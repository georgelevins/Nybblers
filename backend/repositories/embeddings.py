"""
Embedding backend for Nybblers.

Controlled by two environment variables:

  EMBEDDING_BACKEND   "local" (default) | "openai"
  LOCAL_EMBEDDING_MODEL  sentence-transformers model name
                         default: BAAI/bge-base-en-v1.5  (768 dims, ~440 MB)
                         lighter:  BAAI/bge-small-en-v1.5 (384 dims, ~90 MB)

Local backend
  - Zero API cost; runs entirely on the server CPU (or GPU if available).
  - First call downloads the model weights (~440 MB for bge-base) to
    ~/.cache/huggingface/hub — cached forever after that.
  - Speed: ~100–400 texts/sec on a modern CPU with batch_size=64;
    much faster on GPU.
  - Uses cosine similarity (vectors are L2-normalised).
  - EMBEDDING_DIM = 768

OpenAI backend
  - Requires OPENAI_API_KEY.
  - text-embedding-3-small: $0.02 / 1 M tokens; Tier-1 limit 1 M TPM.
  - EMBEDDING_DIM = 1536

IMPORTANT: The vector dimension written here must match the vector(N)
in your database schema.  Pick one backend before running ingest and
don't change it mid-way through (mixing dims breaks search).
"""

import asyncio
import os

# ── Backend detection ─────────────────────────────────────────────────────────

_BACKEND = os.environ.get("EMBEDDING_BACKEND", "local").strip().lower()

# Dimensions for each backend — used by schema creation and callers.
_DIM_LOCAL = int(os.environ.get("EMBEDDING_DIM", "768"))
_DIM_OPENAI = 1536

EMBEDDING_DIM: int = _DIM_LOCAL if _BACKEND == "local" else _DIM_OPENAI

# ── Local (sentence-transformers) ─────────────────────────────────────────────

_LOCAL_MODEL_NAME = os.environ.get(
    "LOCAL_EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5"
)
_local_model = None  # lazy-loaded on first use


def _get_local_model():
    global _local_model
    if _local_model is None:
        try:
            from sentence_transformers import SentenceTransformer  # noqa: PLC0415
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is not installed. "
                "Run: pip install sentence-transformers"
            ) from exc
        _local_model = SentenceTransformer(_LOCAL_MODEL_NAME)
    return _local_model


def _encode_local(texts: list[str]) -> list[list[float]]:
    """Synchronous local encode — run this in a thread via asyncio.to_thread."""
    model = _get_local_model()
    vecs = model.encode(
        texts,
        normalize_embeddings=True,  # L2-normalise → cosine sim = dot product
        batch_size=64,
        show_progress_bar=False,
    )
    return vecs.tolist()


# ── OpenAI ────────────────────────────────────────────────────────────────────

_OPENAI_MODEL = "text-embedding-3-small"
_MAX_CHARS = 24_000  # ~6 000 tokens; safe limit for both models

_openai_client = None


def _get_openai():
    global _openai_client
    if _openai_client is None:
        from openai import AsyncOpenAI  # noqa: PLC0415

        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set — cannot use OpenAI backend.")
        _openai_client = AsyncOpenAI(api_key=api_key)
    return _openai_client


async def _encode_openai(texts: list[str]) -> list[list[float]]:
    client = _get_openai()
    truncated = [t[:_MAX_CHARS] for t in texts]
    resp = await client.embeddings.create(model=_OPENAI_MODEL, input=truncated)
    return [item.embedding for item in sorted(resp.data, key=lambda x: x.index)]


# ── Public API ────────────────────────────────────────────────────────────────


async def embed_text(text: str) -> list[float]:
    """Embed a single string and return a float vector."""
    results = await embed_texts([text.strip()])
    return results[0]


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of strings in one shot and return a list of float vectors
    in the same order.  Prefer this over looping embed_text() — the local
    backend batches internally for much better throughput.
    """
    if not texts:
        return []
    cleaned = [t.strip()[:_MAX_CHARS] for t in texts]
    if _BACKEND == "local":
        return await asyncio.to_thread(_encode_local, cleaned)
    return await _encode_openai(cleaned)


def to_pg_vector(embedding: list[float]) -> str:
    """
    Convert a float list to the pgvector wire format '[x,y,z,...]'.
    asyncpg passes this as a text literal; Postgres casts it via ::vector.
    """
    return "[" + ",".join(map(str, embedding)) + "]"
