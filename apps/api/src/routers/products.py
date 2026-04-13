"""Product endpoints: list, detail, search, similar."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.engine import get_db
from src.schemas.products import (
    ProductListOut,
    ProductOut,
    ProductSearchOut,
    ProductSearchResultOut,
)
from src.services.product import (
    get_product_by_id,
    get_product_by_slug,
    get_similar_products,
    list_products,
    search_products,
)

router = APIRouter()


def _row_to_product_out(row) -> ProductOut:
    product = row[0]  # Product ORM object
    source_name = row[1]  # source_name label
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


@router.get("/products", response_model=ProductListOut)
async def list_products_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    gender: str | None = None,
    category: str | None = None,
    brand: str | None = None,
    min_price: int | None = Query(None, ge=0),
    max_price: int | None = Query(None, ge=0),
    tags: list[str] | None = Query(None),
    sort_by: str = Query("created_at", pattern=r"^(created_at|price_cents|brand|title)$"),
    db: AsyncSession = Depends(get_db),
):
    rows, total = await list_products(
        db,
        page=page,
        page_size=page_size,
        gender=gender,
        category=category,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        tags=tags,
        sort_by=sort_by,
    )
    return ProductListOut(
        products=[_row_to_product_out(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/products/search", response_model=ProductSearchOut)
async def search_products_endpoint(
    q: str = Query(..., min_length=1, max_length=500),
    gender: str | None = None,
    category: str | None = None,
    brand: str | None = None,
    min_price: int | None = Query(None, ge=0),
    max_price: int | None = Query(None, ge=0),
    tags: list[str] | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    rows = await search_products(
        db,
        q,
        gender=gender,
        category=category,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        tags=tags,
        limit=limit,
    )
    results = [
        ProductSearchResultOut(product=_row_to_product_out(r), score=r[2])
        for r in rows
    ]
    return ProductSearchOut(results=results, query=q, total=len(results))


@router.get("/products/{slug}", response_model=ProductOut)
async def get_product_endpoint(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    row = await get_product_by_slug(db, slug)
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    return _row_to_product_out(row)


@router.get("/products/{product_id}/similar", response_model=list[ProductSearchResultOut])
async def get_similar_products_endpoint(
    product_id: uuid.UUID,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    rows = await get_similar_products(db, product_id, limit=limit)
    return [
        ProductSearchResultOut(product=_row_to_product_out(r), score=r[2])
        for r in rows
    ]
