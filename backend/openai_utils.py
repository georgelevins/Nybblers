"""Shared OpenAI embedding helper for routers."""

import os
from openai import AsyncOpenAI

EMBEDDING_MODEL = "text-embedding-3-small"

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


async def embed_text(text: str) -> list[float]:
    """Return the embedding vector for a single text string."""
    response = await _get_client().embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding
