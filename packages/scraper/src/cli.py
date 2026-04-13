import asyncio
import json
from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(name="scraper", help="StylAI product scraper CLI")
console = Console()


def get_scraper(source: str, country: str = "FR", language: str = "fr"):
    if source == "zalando":
        from src.scrapers.zalando import ZalandoScraper
        return ZalandoScraper(country=country, language=language)
    else:
        raise typer.BadParameter(f"Unknown source: {source}. Available: zalando, asos, zara, hm")


@app.command()
def scrape(
    source: str = typer.Option("zalando", help="Source site to scrape"),
    country: str = typer.Option("FR", help="Country code (FR, DE, GB, ES, IT)"),
    gender: str = typer.Option("women", help="Gender: men, women"),
    max_products: int = typer.Option(50, help="Maximum products to scrape"),
    output: str = typer.Option("data/products.json", help="Output JSON file"),
):
    """Scrape products from a fashion website."""
    console.print(f"[bold]Scraping {source} ({country}) - {gender} - max {max_products} products[/bold]")

    async def _scrape():
        scraper = get_scraper(source, country=country, language=country.lower()[:2])
        try:
            products = await scraper.scrape_category(gender, max_products=max_products)
            console.print(f"\n[bold green]Scraped {len(products)} products[/bold green]")

            # Save to JSON
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(
                    [p.model_dump(mode="json") for p in products],
                    f,
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                )
            console.print(f"[green]Saved to {output_path}[/green]")
            return products
        finally:
            await scraper.close()

    asyncio.run(_scrape())


@app.command()
def embed(
    input_file: str = typer.Option("data/products.json", help="Input JSON file with products"),
    batch_size: int = typer.Option(50, help="Batch size for embedding generation"),
):
    """Generate embeddings for scraped products."""
    from src.embedder import build_embedding_text, generate_embeddings_batch

    console.print(f"[bold]Generating embeddings from {input_file}[/bold]")

    async def _embed():
        with open(input_file, "r", encoding="utf-8") as f:
            products = json.load(f)

        texts = [build_embedding_text(p) for p in products]
        console.print(f"Generating embeddings for {len(texts)} products...")

        embeddings = await generate_embeddings_batch(texts, batch_size=batch_size)

        # Save embeddings alongside products
        for i, product in enumerate(products):
            product["embedding"] = embeddings[i]

        output_path = input_file.replace(".json", "_embedded.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2, default=str)

        valid = sum(1 for e in embeddings if e is not None)
        console.print(f"[green]Generated {valid}/{len(texts)} embeddings -> {output_path}[/green]")

    asyncio.run(_embed())


@app.command()
def load(
    input_file: str = typer.Option("data/products_embedded.json", help="Input JSON with products and embeddings"),
):
    """Load products (with embeddings) into PostgreSQL."""
    from src.db_loader import load_products, close
    from src.models import ScrapedProduct

    console.print(f"[bold]Loading products from {input_file} into DB[/bold]")

    async def _load():
        with open(input_file, "r", encoding="utf-8") as f:
            raw_products = json.load(f)

        products = []
        embeddings = []
        for p in raw_products:
            emb = p.pop("embedding", None)
            products.append(ScrapedProduct(**p))
            embeddings.append(emb)

        await load_products(products, embeddings)
        await close()

    asyncio.run(_load())


@app.command()
def pipeline(
    source: str = typer.Option("zalando", help="Source site"),
    country: str = typer.Option("FR", help="Country code"),
    gender: str = typer.Option("women", help="Gender: men, women"),
    max_products: int = typer.Option(50, help="Maximum products"),
    batch_size: int = typer.Option(50, help="Embedding batch size"),
):
    """Full pipeline: scrape -> tag -> embed -> load into DB."""
    from src.embedder import build_embedding_text, generate_embeddings_batch
    from src.db_loader import load_products, close
    from src.tagger import generate_tags

    console.print(f"[bold]Full pipeline: {source} ({country}) - {gender}[/bold]\n")

    async def _pipeline():
        # Step 1: Scrape
        console.rule("[bold blue]Step 1: Scraping")
        scraper = get_scraper(source, country=country, language=country.lower()[:2])
        try:
            products = await scraper.scrape_category(gender, max_products=max_products)
        finally:
            await scraper.close()

        if not products:
            console.print("[red]No products scraped. Aborting.[/red]")
            return

        console.print(f"[green]Scraped {len(products)} products[/green]\n")

        # Step 1.5: Tag
        console.rule("[bold blue]Step 1.5: Auto-tagging")
        for p in products:
            if not p.tags:
                p.tags = generate_tags(p.model_dump())
        console.print(f"[green]Tagged {len(products)} products[/green]\n")

        # Step 2: Embed (tags included in embedding text)
        console.rule("[bold blue]Step 2: Generating embeddings")
        texts = [build_embedding_text(p.model_dump()) for p in products]
        embeddings = await generate_embeddings_batch(texts, batch_size=batch_size)
        valid = sum(1 for e in embeddings if e is not None)
        console.print(f"[green]Generated {valid}/{len(texts)} embeddings[/green]\n")

        # Step 3: Load
        console.rule("[bold blue]Step 3: Loading into database")
        loaded = await load_products(products, embeddings)
        await close()

        console.print(f"\n[bold green]Pipeline complete! {loaded} products loaded.[/bold green]")

    asyncio.run(_pipeline())


@app.command()
def import_browser(
    input_file: str = typer.Option(..., help="JSON file exported from browser script"),
    batch_size: int = typer.Option(50, help="Embedding batch size"),
):
    """Import products from browser-extracted JSON, tag them, embed, and load into DB."""
    from src.embedder import build_embedding_text, generate_embeddings_batch
    from src.db_loader import load_products, close
    from src.models import ScrapedProduct
    from src.tagger import generate_tags

    console.print(f"[bold]Importing browser-extracted products from {input_file}[/bold]\n")

    async def _import():
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle both formats: {products: [...]} or [...]
        raw_products = data.get("products", data) if isinstance(data, dict) else data

        # Convert to ScrapedProduct objects with auto-tags
        products = []
        for p in raw_products:
            p.pop("_raw_json_ld", None)
            p.pop("embedding", None)
            # Auto-generate tags before creating the model
            if not p.get("tags"):
                p["tags"] = generate_tags(p)
            try:
                products.append(ScrapedProduct(**p))
            except Exception as e:
                console.print(f"[yellow]Skipping invalid product: {e}[/yellow]")

        if not products:
            console.print("[red]No valid products found. Aborting.[/red]")
            return

        console.print(f"[green]Parsed {len(products)} valid products[/green]")
        # Show tag stats
        all_tags = set()
        for p in products:
            all_tags.update(p.tags)
        console.print(f"[cyan]Auto-tagged with {len(all_tags)} unique tags: {', '.join(sorted(all_tags))}[/cyan]\n")

        # Embed (tags are included in embedding text)
        console.rule("[bold blue]Generating embeddings")
        texts = [build_embedding_text(p.model_dump()) for p in products]
        embeddings = await generate_embeddings_batch(texts, batch_size=batch_size)
        valid = sum(1 for e in embeddings if e is not None)
        console.print(f"[green]Generated {valid}/{len(texts)} embeddings[/green]\n")

        # Load
        console.rule("[bold blue]Loading into database")
        loaded = await load_products(products, embeddings)
        await close()

        console.print(f"\n[bold green]Import complete! {loaded} products loaded with embeddings.[/bold green]")

    asyncio.run(_import())


if __name__ == "__main__":
    app()
