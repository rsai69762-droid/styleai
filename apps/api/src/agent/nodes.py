"""LangGraph agent nodes: the 5 steps of the recommendation pipeline."""

import asyncio
import json
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.state import AgentState, ProductCandidate, RecommendationResult
from src.agent.tools import (
    fetch_trends,
    fetch_user_profile,
    fetch_weather,
    vector_search,
)
from src.config import settings
from src.db.models import Recommendation


def _build_llm():
    if settings.llm_provider == "ollama":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
            temperature=0.3,
            max_tokens=1024,
        )
    else:
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0.3,
            extra_body={"options": {"num_predict": 1024}},
            think=False,
        )


_llm = _build_llm()


async def gather_context(state: AgentState, *, db: AsyncSession) -> dict:
    """Node 1: Fetch user profile, weather, and trends in parallel."""
    user_id = state["user_id"]

    profile, weather = await asyncio.gather(
        fetch_user_profile(db, user_id),
        fetch_weather(None),  # will use profile country below
    )

    # Re-fetch weather with user's country if available
    country = profile.get("country") or "FR"
    if weather and weather.get("country") != country:
        weather = await fetch_weather(country)

    season = weather["season"] if weather else "ete"
    trends = await fetch_trends(db, season, profile.get("gender"))

    return {
        "user_profile": profile,
        "weather": weather,
        "trends": trends,
    }


async def plan_search(state: AgentState) -> dict:
    """Node 2: LLM generates 2-4 search queries based on context."""
    profile = state["user_profile"]
    weather = state.get("weather") or {}
    trends = state.get("trends", [])
    occasion = state.get("occasion") or ""
    mood = state.get("mood") or ""

    prompt = f"""Tu es un styliste personnel. Genere 2 a 4 requetes de recherche pour trouver des vetements adaptes a cette personne.

PROFIL :
- Genre : {profile.get('gender', 'women')}
- Style prefere : {', '.join(profile.get('style_tags', [])) or 'non precise'}
- Couleurs preferees : {', '.join(profile.get('favorite_colors', [])) or 'non precise'}
- Marques preferees : {', '.join(profile.get('favorite_brands', [])) or 'non precise'}
- Budget : {profile.get('budget_min_cents', 0)//100}€ - {profile.get('budget_max_cents', 10000)//100}€

METEO : {weather.get('temperature_c', '?')}°C, {'pluie' if weather.get('is_rainy') else 'beau temps'}, saison {weather.get('season', '?')}

TENDANCES ACTUELLES : {', '.join(trends) or 'non disponible'}

{'OCCASION : ' + occasion if occasion else ''}
{'STYLE RECHERCHE : ' + mood if mood else ''}

Reponds UNIQUEMENT avec un JSON array de strings, chaque string etant une requete de recherche en francais.
Exemple : ["robe ete fleurie legere", "top blanc casual", "jean slim taille haute"]
"""
    response = await _llm.ainvoke(prompt)
    content = response.content.strip()

    # Parse JSON from response (handle markdown code blocks)
    if "```" in content:
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()

    try:
        queries = json.loads(content)
        if not isinstance(queries, list):
            queries = ["vetements tendance"]
    except json.JSONDecodeError:
        queries = ["vetements tendance"]

    return {"search_queries": queries[:4]}


async def execute_search(state: AgentState, *, db: AsyncSession) -> dict:
    """Node 3: Execute vector searches and collect candidate products."""
    profile = state["user_profile"]
    queries = state.get("search_queries", ["vetements"])

    gender = profile.get("gender")
    min_price = profile.get("budget_min_cents")
    max_price = profile.get("budget_max_cents")

    seen_ids: set[str] = set()
    candidates: list[ProductCandidate] = []

    all_results = await asyncio.gather(*(
        vector_search(db, query, gender=gender, min_price=min_price, max_price=max_price, limit=15)
        for query in queries
    ))

    for results in all_results:
        for r in results:
            if r["product_id"] not in seen_ids:
                seen_ids.add(r["product_id"])
                candidates.append(ProductCandidate(
                    product_id=r["product_id"],
                    title=r["title"],
                    brand=r["brand"],
                    price_cents=r["price_cents"],
                    tags=r["tags"],
                    image_url=r["image_url"],
                    score=r["score"],
                ))

    return {"candidate_products": candidates}


async def rank_and_filter(state: AgentState) -> dict:
    """Node 4: LLM ranks candidates and generates explanations."""
    profile = state["user_profile"]
    weather = state.get("weather") or {}
    trends = state.get("trends", [])
    candidates = state.get("candidate_products", [])
    occasion = state.get("occasion") or ""

    if not candidates:
        return {"recommendations": []}

    # Build product list for LLM
    products_text = "\n".join(
        f"- ID:{c['product_id'][:8]} | {c['title']} | {c['brand'] or '?'} | {c['price_cents']/100:.0f}€ | tags: {', '.join(c['tags'][:5])}"
        for c in candidates[:30]  # limit to 30 for context window
    )

    prompt = f"""Tu es un styliste personnel. Classe ces produits par pertinence pour cette personne et selectionne les 8 meilleurs.

PROFIL :
- Genre : {profile.get('gender', 'women')}
- Style : {', '.join(profile.get('style_tags', [])) or 'eclectique'}
- Couleurs preferees : {', '.join(profile.get('favorite_colors', [])) or 'toutes'}

METEO : {weather.get('temperature_c', '?')}°C, saison {weather.get('season', '?')}
TENDANCES : {', '.join(trends) or 'non disponible'}
{'OCCASION : ' + occasion if occasion else ''}

PRODUITS :
{products_text}

Pour chaque produit selectionne, reponds avec un JSON array :
[{{"id": "ID_8_chars", "score": 0.0-1.0, "reason": "explication courte en francais"}}]

Classe du plus pertinent au moins pertinent. Score 1.0 = parfait match. Reponds UNIQUEMENT avec le JSON.
"""
    response = await _llm.ainvoke(prompt)
    content = response.content.strip()

    if "```" in content:
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()

    try:
        ranked = json.loads(content)
        if not isinstance(ranked, list):
            ranked = []
    except json.JSONDecodeError:
        ranked = []

    # Map back to full product IDs
    id_map = {c["product_id"][:8]: c["product_id"] for c in candidates}

    recommendations: list[RecommendationResult] = []
    for item in ranked[:8]:
        short_id = item.get("id", "")
        full_id = id_map.get(short_id)
        if not full_id:
            continue
        recommendations.append(RecommendationResult(
            product_id=full_id,
            score=min(1.0, max(0.0, float(item.get("score", 0.5)))),
            reason=item.get("reason", ""),
        ))

    return {"recommendations": recommendations}


async def format_output(state: AgentState, *, db: AsyncSession) -> dict:
    """Node 5: Save recommendations to DB and finalize."""
    recommendations = state.get("recommendations", [])
    user_id = state["user_id"]
    run_id = state.get("agent_run_id", str(uuid.uuid4()))

    context = {
        "weather": state.get("weather"),
        "trends": state.get("trends", []),
        "occasion": state.get("occasion"),
        "mood": state.get("mood"),
        "search_queries": state.get("search_queries", []),
    }

    for rec in recommendations:
        db.add(Recommendation(
            user_id=uuid.UUID(user_id),
            product_id=uuid.UUID(rec["product_id"]),
            score=rec["score"],
            reason=rec["reason"],
            context=context,
            agent_run_id=run_id,
        ))

    await db.commit()
    return {"agent_run_id": run_id}
