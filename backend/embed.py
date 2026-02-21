"""
Embedding pipeline for RedditDemand.

Reads posts where reconstructed_text is ready but embedding is missing,
calls the OpenAI embeddings API in batches, and writes the vectors back.

Run AFTER ingest.py (and BEFORE applying the HNSW index for bulk loads).

Usage:
  python embed.py                          # embed all un-embedded posts
  python embed.py --limit 1000            # stop after 1000 posts (for testing)
  python embed.py --subreddit entrepreneur # only embed one subreddit
  python embed.py --batch-size 50         # smaller batches (default 100)

Requires:
  DATABASE_URL   - Postgres connection string
  OPENAI_API_KEY - OpenAI API key (read automatically by the openai library)
"""

import argparse
import asyncio
import os
import sys
import time

import asyncpg
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_BATCH_SIZE = 100
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0  # seconds, doubles on each retry


def _vec_to_str(vec: list[float]) -> str:
    """Format a float list as a pgvector literal string."""
    return "[" + ",".join(str(x) for x in vec) + "]"


def _embed_with_retry(client: OpenAI, texts: list[str]) -> list[list[float]]:
    """Call the OpenAI embeddings API with simple exponential backoff."""
    for attempt in range(MAX_RETRIES):
        try:
            response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
            return [e.embedding for e in response.data]
        except Exception as exc:
            if attempt == MAX_RETRIES - 1:
                raise
            delay = RETRY_BASE_DELAY * (2 ** attempt)
            print(f"  OpenAI error (attempt {attempt + 1}/{MAX_RETRIES}): {exc}. Retrying in {delay}s...")
            time.sleep(delay)
    raise RuntimeError("Unreachable")


async def run_embed(
    limit: int | None,
    subreddit: str | None,
    batch_size: int,
) -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set.", file=sys.stderr)
        sys.exit(1)

    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("ERROR: OPENAI_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=openai_key)

    print("Connecting to database...")
    conn = await asyncpg.connect(database_url)
    total = 0

    try:
        while True:
            rows = await conn.fetch(
                """
                SELECT id, reconstructed_text
                FROM posts
                WHERE embedded_at IS NULL
                  AND reconstructed_text IS NOT NULL
                  AND ($1::text IS NULL OR subreddit = $1)
                LIMIT $2
                """,
                subreddit,
                batch_size,
            )

            if not rows:
                break

            ids = [r["id"] for r in rows]
            texts = [r["reconstructed_text"] for r in rows]

            print(f"  Embedding batch of {len(rows)} posts...")
            vectors = _embed_with_retry(client, texts)

            updates = [(_vec_to_str(vec), pid) for vec, pid in zip(vectors, ids)]
            await conn.executemany(
                "UPDATE posts SET embedding = $1::vector, embedded_at = NOW() WHERE id = $2",
                updates,
            )

            total += len(rows)
            print(f"  Total embedded: {total:,}")

            if limit and total >= limit:
                break

    finally:
        await conn.close()

    print(f"\nDone. {total:,} posts embedded.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Embed Reddit post threads into Postgres via OpenAI."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Stop after embedding N posts. Useful for test runs.",
    )
    parser.add_argument(
        "--subreddit",
        default=None,
        metavar="NAME",
        help="Only embed posts from this subreddit.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        metavar="N",
        help=f"Number of posts per OpenAI API call (default {DEFAULT_BATCH_SIZE}).",
    )
    args = parser.parse_args()

    asyncio.run(run_embed(
        limit=args.limit,
        subreddit=args.subreddit,
        batch_size=args.batch_size,
    ))


if __name__ == "__main__":
    main()
