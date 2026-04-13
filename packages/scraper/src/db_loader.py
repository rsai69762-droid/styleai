import json

from slugify import slugify
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from rich.console import Console
from rich.progress import Progress

from src.config import DATABASE_URL
from src.models import ScrapedProduct

console = Console()

SOURCE_IDS = {"zalando": 1, "asos": 2, "zara": 3, "hm": 4}

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def generate_slug(product: ScrapedProduct) -> str:
    """Generate a unique SEO-friendly slug."""
    base = f"{product.brand} {product.title}"
    slug = slugify(base, max_length=400)
    # Append source and external_id for uniqueness
    return f"{slug}-{product.source}-{slugify(product.external_id)}"


async def load_products(
    products: list[ScrapedProduct],
    embeddings: list[list[float] | None] | None = None,
) -> int:
    """Upsert products into PostgreSQL with optional embeddings."""
    loaded = 0

    async with async_session() as session:
        with Progress() as progress:
            task = progress.add_task("[cyan]Loading products into DB...", total=len(products))

            for i, product in enumerate(products):
                embedding = embeddings[i] if embeddings and i < len(embeddings) else None
                slug = generate_slug(product)

                # Build sizes JSON
                sizes_json = [{"size": s.size, "available": s.available} for s in product.sizes]

                # Upsert using raw SQL for ON CONFLICT
                embedding_clause = ""
                params = {
                    "source_id": SOURCE_IDS[product.source],
                    "external_id": product.external_id,
                    "slug": slug,
                    "title": product.title,
                    "description": product.description,
                    "brand": product.brand,
                    "price_cents": product.price_cents,
                    "currency": product.currency,
                    "original_url": product.original_url,
                    "image_urls": product.image_urls,
                    "category": product.category,
                    "subcategory": product.subcategory,
                    "gender": product.gender,
                    "sizes": json.dumps(sizes_json),
                    "colors": product.colors,
                    "material": product.material,
                    "tags": product.tags,
                    "country_availability": [product.country],
                    "language": product.language,
                }

                if embedding:
                    embedding_clause = ", embedding = CAST(:embedding AS vector)"
                    params["embedding"] = str(embedding)

                sql = text(f"""
                    INSERT INTO products (
                        source_id, external_id, slug, title, description, brand,
                        price_cents, currency, original_url, image_urls, category,
                        subcategory, gender, sizes, colors, tags, material,
                        country_availability, language
                        {', embedding' if embedding else ''}
                    ) VALUES (
                        :source_id, :external_id, :slug, :title, :description, :brand,
                        :price_cents, :currency, :original_url, :image_urls, :category,
                        :subcategory, :gender, CAST(:sizes AS jsonb), :colors, :tags, :material,
                        :country_availability, :language
                        {', CAST(:embedding AS vector)' if embedding else ''}
                    )
                    ON CONFLICT (slug) DO UPDATE SET
                        price_cents = EXCLUDED.price_cents,
                        tags = EXCLUDED.tags,
                        is_available = true,
                        last_checked_at = now()
                        {embedding_clause}
                """)

                try:
                    await session.execute(sql, params)
                    loaded += 1
                except Exception as e:
                    console.print(f"[red]DB error for {product.title[:40]}: {e}[/red]")

                progress.update(task, advance=1)

        await session.commit()

    console.print(f"[green]Loaded {loaded}/{len(products)} products into DB[/green]")
    return loaded


async def close():
    await engine.dispose()
