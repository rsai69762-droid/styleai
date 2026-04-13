"""Agent tools: functions the LangGraph nodes call to fetch data."""

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.models import FashionTrend, UserProfile
from src.services.product import get_similar_products as _get_similar, search_products as _search

# Country -> capital city coordinates for Open-Meteo
COUNTRY_COORDS: dict[str, tuple[float, float]] = {
    "FR": (48.86, 2.35),
    "DE": (52.52, 13.41),
    "ES": (40.42, -3.70),
    "IT": (41.90, 12.50),
    "GB": (51.51, -0.13),
    "NL": (52.37, 4.90),
    "BE": (50.85, 4.35),
    "AT": (48.21, 16.37),
    "CH": (46.95, 7.45),
    "PT": (38.72, -9.14),
}

# Temperature -> season mapping
def _temp_to_season(temp_c: float) -> str:
    if temp_c < 10:
        return "hiver"
    elif temp_c < 18:
        return "mi-saison"
    elif temp_c < 28:
        return "ete"
    else:
        return "canicule"


async def fetch_user_profile(db: AsyncSession, user_id: str) -> dict:
    """Get user style profile from DB."""
    profile = (await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )).scalar_one_or_none()

    if not profile:
        return {"gender": "women", "style_tags": [], "favorite_colors": [], "favorite_brands": []}

    return {
        "gender": profile.gender or "women",
        "age_range": profile.age_range,
        "body_type": profile.body_type,
        "style_tags": profile.style_tags or [],
        "favorite_brands": profile.favorite_brands or [],
        "favorite_colors": profile.favorite_colors or [],
        "budget_min_cents": profile.budget_min_cents,
        "budget_max_cents": profile.budget_max_cents,
        "preferred_sizes": profile.preferred_sizes or {},
    }


async def fetch_weather(country: str | None) -> dict | None:
    """Get current weather from Open-Meteo (free, no API key)."""
    coords = COUNTRY_COORDS.get(country or "FR", COUNTRY_COORDS["FR"])
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{settings.open_meteo_base_url}/forecast",
                params={
                    "latitude": coords[0],
                    "longitude": coords[1],
                    "current": "temperature_2m,weathercode",
                    "timezone": "auto",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            current = data.get("current", {})
            temp = current.get("temperature_2m", 20)
            weather_code = current.get("weathercode", 0)

            # Simplified weather description
            is_rainy = weather_code in (51, 53, 55, 61, 63, 65, 71, 73, 75, 80, 81, 82, 95, 96, 99)

            return {
                "temperature_c": temp,
                "is_rainy": is_rainy,
                "season": _temp_to_season(temp),
                "country": country or "FR",
            }
    except Exception:
        return None


async def fetch_trends(db: AsyncSession, season: str | None, gender: str | None) -> list[str]:
    """Get trending style tags for current season."""
    stmt = select(FashionTrend)
    if season:
        stmt = stmt.where(FashionTrend.season == season)
    if gender:
        stmt = stmt.where(FashionTrend.gender == gender)
    stmt = stmt.limit(10)

    rows = (await db.execute(stmt)).scalars().all()
    tags: list[str] = []
    for trend in rows:
        tags.extend(trend.trend_tags or [])
    return list(set(tags))


async def vector_search(
    db: AsyncSession,
    query: str,
    *,
    gender: str | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    tags: list[str] | None = None,
    limit: int = 15,
) -> list[dict]:
    """Semantic search wrapper for the agent."""
    rows = await _search(
        db,
        query,
        gender=gender,
        min_price=min_price,
        max_price=max_price,
        tags=tags,
        limit=limit,
    )
    results = []
    for row in rows:
        product = row[0]
        score = row[2]
        results.append({
            "product_id": str(product.id),
            "title": product.title,
            "brand": product.brand,
            "price_cents": product.price_cents,
            "tags": product.tags or [],
            "image_url": (product.image_urls or [None])[0],
            "score": float(score),
        })
    return results


async def similar_products(db: AsyncSession, product_id: str, limit: int = 5) -> list[dict]:
    """Get similar products wrapper."""
    import uuid
    rows = await _get_similar(db, uuid.UUID(product_id), limit=limit)
    results = []
    for row in rows:
        product = row[0]
        score = row[2]
        results.append({
            "product_id": str(product.id),
            "title": product.title,
            "brand": product.brand,
            "price_cents": product.price_cents,
            "tags": product.tags or [],
            "image_url": (product.image_urls or [None])[0],
            "score": float(score),
        })
    return results
