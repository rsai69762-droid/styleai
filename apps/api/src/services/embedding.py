"""Embedding service using Ollama nomic-embed-text."""

import httpx

from src.config import settings

MODEL = "nomic-embed-text"


async def get_embedding(text: str) -> list[float]:
    """Generate a 768-dim embedding for a text query via Ollama."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{settings.ollama_base_url}/api/embed",
            json={"model": MODEL, "input": text},
        )
        resp.raise_for_status()
        data = resp.json()
        return data["embeddings"][0]
