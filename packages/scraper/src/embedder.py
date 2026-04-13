import httpx
from rich.console import Console
from rich.progress import Progress

from src.config import OLLAMA_BASE_URL, EMBEDDING_MODEL

console = Console()


def build_embedding_text(product: dict) -> str:
    """Construct a rich text representation for embedding."""
    parts = [
        product.get("title", ""),
        f"Brand: {product['brand']}" if product.get("brand") else "",
        f"Category: {product.get('category', '')}",
        f"Subcategory: {product.get('subcategory', '')}" if product.get("subcategory") else "",
        f"Gender: {product.get('gender', '')}",
        f"Colors: {', '.join(product['colors'])}" if product.get("colors") else "",
        f"Tags: {', '.join(product['tags'])}" if product.get("tags") else "",
        f"Material: {product['material']}" if product.get("material") else "",
        product.get("description", "") or "",
    ]
    return " | ".join(p for p in parts if p)


async def generate_embeddings_batch(texts: list[str], batch_size: int = 50) -> list[list[float]]:
    """Generate embeddings for a list of texts using Ollama."""
    results = []

    async with httpx.AsyncClient(timeout=120.0) as client:
        with Progress() as progress:
            task = progress.add_task("[cyan]Generating embeddings...", total=len(texts))

            for i in range(0, len(texts), batch_size):
                batch = texts[i : i + batch_size]
                try:
                    response = await client.post(
                        f"{OLLAMA_BASE_URL}/api/embed",
                        json={"model": EMBEDDING_MODEL, "input": batch},
                    )
                    response.raise_for_status()
                    data = response.json()
                    results.extend(data["embeddings"])
                except httpx.HTTPError as e:
                    console.print(f"[red]Embedding error for batch {i}: {e}[/red]")
                    # Fill with None for failed items
                    results.extend([None] * len(batch))

                progress.update(task, advance=len(batch))

    return results


async def generate_embedding(text: str) -> list[float] | None:
    """Generate a single embedding."""
    result = await generate_embeddings_batch([text], batch_size=1)
    return result[0] if result else None
