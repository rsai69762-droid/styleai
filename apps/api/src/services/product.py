"""Product service: DB queries for listing, filtering, vector search."""

import uuid

from sqlalchemy import Select, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Product, Source
from src.services.embedding import get_embedding


def _base_query() -> Select:
    return (
        select(Product, Source.name.label("source_name"))
        .join(Source, Product.source_id == Source.id)
        .where(Product.is_available.is_(True))
    )


def _apply_filters(
    stmt: Select,
    *,
    gender: str | None = None,
    category: str | None = None,
    brand: str | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    tags: list[str] | None = None,
) -> Select:
    if gender:
        stmt = stmt.where(Product.gender == gender)
    if category:
        stmt = stmt.where(Product.category == category)
    if brand:
        stmt = stmt.where(func.lower(Product.brand) == brand.lower())
    if min_price is not None:
        stmt = stmt.where(Product.price_cents >= min_price)
    if max_price is not None:
        stmt = stmt.where(Product.price_cents <= max_price)
    if tags:
        stmt = stmt.where(Product.tags.overlap(tags))
    return stmt


async def list_products(
    db: AsyncSession,
    *,
    page: int = 1,
    page_size: int = 20,
    gender: str | None = None,
    category: str | None = None,
    brand: str | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    tags: list[str] | None = None,
    sort_by: str = "created_at",
) -> tuple[list[tuple], int]:
    stmt = _base_query()
    stmt = _apply_filters(stmt, gender=gender, category=category, brand=brand, min_price=min_price, max_price=max_price, tags=tags)

    # Count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Sort
    order_col = getattr(Product, sort_by, Product.created_at)
    stmt = stmt.order_by(order_col.desc())

    # Paginate
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(stmt)).all()
    return rows, total


async def get_product_by_slug(db: AsyncSession, slug: str) -> tuple | None:
    stmt = _base_query().where(Product.slug == slug)
    row = (await db.execute(stmt)).first()
    return row


async def get_product_by_id(db: AsyncSession, product_id: uuid.UUID) -> tuple | None:
    stmt = _base_query().where(Product.id == product_id)
    row = (await db.execute(stmt)).first()
    return row


async def search_products(
    db: AsyncSession,
    query: str,
    *,
    gender: str | None = None,
    category: str | None = None,
    brand: str | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    tags: list[str] | None = None,
    limit: int = 20,
) -> list[tuple]:
    """Semantic search using pgvector cosine distance."""
    query_embedding = await get_embedding(query)

    stmt = (
        select(
            Product,
            Source.name.label("source_name"),
            (1 - Product.embedding.cosine_distance(query_embedding)).label("score"),
        )
        .join(Source, Product.source_id == Source.id)
        .where(Product.is_available.is_(True))
        .where(Product.embedding.isnot(None))
    )
    stmt = _apply_filters(stmt, gender=gender, category=category, brand=brand, min_price=min_price, max_price=max_price, tags=tags)
    stmt = stmt.order_by(text("score DESC")).limit(limit)

    rows = (await db.execute(stmt)).all()
    return rows


async def get_similar_products(
    db: AsyncSession,
    product_id: uuid.UUID,
    *,
    limit: int = 10,
) -> list[tuple]:
    """Find similar products by vector similarity."""
    # Get the source product embedding
    prod = (await db.execute(select(Product).where(Product.id == product_id))).scalar_one_or_none()
    if not prod or prod.embedding is None:
        return []

    stmt = (
        select(
            Product,
            Source.name.label("source_name"),
            (1 - Product.embedding.cosine_distance(prod.embedding)).label("score"),
        )
        .join(Source, Product.source_id == Source.id)
        .where(Product.is_available.is_(True))
        .where(Product.id != product_id)
        .where(Product.embedding.isnot(None))
        .order_by(text("score DESC"))
        .limit(limit)
    )
    rows = (await db.execute(stmt)).all()
    return rows
