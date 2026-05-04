"""Embedding service using Ollama nomic-embed-text."""

from functools import lru_cache

import httpx

from src.config import settings

MODEL = "nomic-embed-text"

_cache: dict[str, list[float]] = {}
MAX_CACHE_SIZE = 500


async def get_embedding(text: str) -> list[float]:
    normalized = text.strip().lower()
    if normalized in _cache:
        return _cache[normalized]

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{settings.ollama_base_url}/api/embed",
            json={"model": MODEL, "input": normalized},
        )
        resp.raise_for_status()
        data = resp.json()
        embedding = data["embeddings"][0]

    if len(_cache) < MAX_CACHE_SIZE:
        _cache[normalized] = embedding

    return embedding
