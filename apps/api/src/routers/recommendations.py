"""Recommendation endpoints: generate, list, feedback."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.agent.graph import run_agent
from src.auth.deps import get_current_user
from src.db.engine import get_db
from src.db.models import Product, Recommendation, Source, User
from src.schemas.products import ProductOut
from src.schemas.recommendations import (
    RecommendationFeedbackIn,
    RecommendationGenerateIn,
    RecommendationGenerateOut,
    RecommendationItemOut,
)

router = APIRouter()


def _product_to_out(product: Product, source_name: str) -> ProductOut:
    return ProductOut(
        id=product.id,
        source=source_name,
        slug=product.slug,
        title=product.title,
        description=product.description,
        brand=product.brand,
        price_cents=product.price_cents,
        currency=product.currency,
        original_url=product.original_url,
        affiliate_url=product.affiliate_url,
        image_urls=product.image_urls or [],
        category=product.category,
        subcategory=product.subcategory,
        gender=product.gender,
        sizes=product.sizes or [],
        colors=product.colors or [],
        material=product.material,
        tags=product.tags or [],
        language=product.language,
        scraped_at=product.scraped_at,
        is_available=product.is_available,
    )


@router.post("/recommendations/generate", response_model=RecommendationGenerateOut)
async def generate_recommendations(
    body: RecommendationGenerateIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run the AI agent to generate personalized recommendations."""
    result = await run_agent(
        db,
        str(user.id),
        occasion=body.occasion,
        mood=body.mood,
    )

    # Fetch full products for the response
    rec_items: list[RecommendationItemOut] = []
    for rec in result.get("recommendations", []):
        stmt = (
            select(Recommendation, Product, Source.name.label("source_name"))
            .join(Product, Recommendation.product_id == Product.id)
            .join(Source, Product.source_id == Source.id)
            .where(Recommendation.agent_run_id == result["agent_run_id"])
            .where(Recommendation.product_id == uuid.UUID(rec["product_id"]))
            .where(Recommendation.user_id == user.id)
        )
        row = (await db.execute(stmt)).first()
        if row:
            rec_obj, product, source_name = row
            rec_items.append(RecommendationItemOut(
                id=rec_obj.id,
                product=_product_to_out(product, source_name),
                score=rec_obj.score,
                reason=rec_obj.reason,
                agent_run_id=rec_obj.agent_run_id,
                created_at=rec_obj.created_at,
            ))

    return RecommendationGenerateOut(
        agent_run_id=result["agent_run_id"],
        recommendations=rec_items,
        context={
            "weather": result.get("weather"),
            "trends": result.get("trends", []),
            "search_queries": result.get("search_queries", []),
        },
    )


@router.get("/recommendations", response_model=list[RecommendationItemOut])
async def list_recommendations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
):
    """Get saved recommendations for current user."""
    stmt = (
        select(Recommendation, Product, Source.name.label("source_name"))
        .join(Product, Recommendation.product_id == Product.id)
        .join(Source, Product.source_id == Source.id)
        .where(Recommendation.user_id == user.id)
        .where(Recommendation.is_dismissed.is_(False))
        .order_by(Recommendation.created_at.desc())
        .limit(limit)
    )
    rows = (await db.execute(stmt)).all()

    return [
        RecommendationItemOut(
            id=rec.id,
            product=_product_to_out(product, source_name),
            score=rec.score,
            reason=rec.reason,
            agent_run_id=rec.agent_run_id,
            created_at=rec.created_at,
        )
        for rec, product, source_name in rows
    ]


@router.post("/recommendations/{rec_id}/feedback")
async def recommendation_feedback(
    rec_id: uuid.UUID,
    body: RecommendationFeedbackIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Like/dislike a recommendation."""
    result = await db.execute(
        update(Recommendation)
        .where(Recommendation.id == rec_id, Recommendation.user_id == user.id)
        .values(is_dismissed=body.is_dismissed)
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    await db.commit()
    return {"status": "updated"}
