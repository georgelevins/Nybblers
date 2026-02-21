"""
Batch job: embed comments that don't yet have a row in comment_embeddings.

Reads comments (optionally filtered by subreddit), calls OpenAI embeddings API
in batches, and upserts into comment_embeddings. Run after ingest and optionally
after embed.py (post embedding). Used by the leads search endpoint.

Usage:
  python embed_comments.py                    # embed all un-embedded comments
  python embed_comments.py --limit 500       # stop after 500 (for testing)
  python embed_comments.py --subreddit microsaas
  python embed_comments.py --batch-size 100

Requires:
  DATABASE_URL   - Postgres connection string
  OPENAI_API_KEY - OpenAI API key
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
RETRY_BASE_DELAY = 2.0


def _vec_to_str(vec: list[float]) -> str:
    return "[" + ",".join(str(x) for x in vec) + "]"


def _embed_with_retry(client: OpenAI, texts: list[str]) -> list[list[float]]:
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


async def run_embed_comments(
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
                SELECT c.id, c.body
                FROM comments c
                LEFT JOIN comment_embeddings ce ON ce.comment_id = c.id
                WHERE ce.comment_id IS NULL
                  AND c.body IS NOT NULL
                  AND TRIM(c.body) != ''
                  AND ($1::text IS NULL OR c.post_id IN (SELECT id FROM posts WHERE subreddit = $1))
                LIMIT $2
                """,
                subreddit,
                batch_size,
            )

            if not rows:
                break

            ids = [r["id"] for r in rows]
            texts = [r["body"] for r in rows]

            print(f"  Embedding batch of {len(rows)} comments...")
            vectors = _embed_with_retry(client, texts)

            for cid, vec in zip(ids, vectors):
                await conn.execute(
                    """
                    INSERT INTO comment_embeddings (comment_id, embedding)
                    VALUES ($1, $2::vector)
                    ON CONFLICT (comment_id) DO UPDATE SET
                        embedding = EXCLUDED.embedding,
                        embedded_at = NOW()
                    """,
                    cid,
                    _vec_to_str(vec),
                )

            total += len(rows)
            print(f"  Total embedded: {total:,}")

            if limit and total >= limit:
                break

    finally:
        await conn.close()

    print(f"\nDone. {total:,} comments embedded.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Embed Reddit comments into comment_embeddings via OpenAI."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Stop after embedding N comments. Useful for test runs.",
    )
    parser.add_argument(
        "--subreddit",
        default=None,
        metavar="NAME",
        help="Only embed comments from this subreddit (via post_id).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        metavar="N",
        help=f"Number of comments per OpenAI API call (default {DEFAULT_BATCH_SIZE}).",
    )
    args = parser.parse_args()

    asyncio.run(run_embed_comments(
        limit=args.limit,
        subreddit=args.subreddit,
        batch_size=args.batch_size,
    ))


if __name__ == "__main__":
    main()
