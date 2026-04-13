"""Wishlist endpoints."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.deps import get_current_user
from src.db.engine import get_db
from src.db.models import Product, Source, User, Wishlist
from src.schemas.products import ProductOut

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


@router.get("/users/me/wishlist", response_model=list[ProductOut])
async def get_wishlist(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    stmt = (
        select(Product, Source.name.label("source_name"))
        .join(Wishlist, Wishlist.product_id == Product.id)
        .join(Source, Product.source_id == Source.id)
        .where(Wishlist.user_id == user.id)
        .order_by(Wishlist.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = (await db.execute(stmt)).all()
    return [_product_to_out(r[0], r[1]) for r in rows]


@router.post("/users/me/wishlist/{product_id}", status_code=201)
async def add_to_wishlist(
    product_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Check product exists
    exists = (await db.execute(select(func.count()).where(Product.id == product_id))).scalar()
    if not exists:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check not already in wishlist
    already = (await db.execute(
        select(func.count()).where(Wishlist.user_id == user.id, Wishlist.product_id == product_id)
    )).scalar()
    if already:
        return {"status": "already_exists"}

    db.add(Wishlist(user_id=user.id, product_id=product_id))
    await db.commit()
    return {"status": "added"}


@router.delete("/users/me/wishlist/{product_id}", status_code=200)
async def remove_from_wishlist(
    product_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        delete(Wishlist).where(Wishlist.user_id == user.id, Wishlist.product_id == product_id)
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Product not in wishlist")
    await db.commit()
    return {"status": "removed"}
