"""
Embed posts and their comments together in thread-sized batches.

Processes a batch of threads at a time: for each thread (post), embeds the post
and all its comments in one go, then writes to posts.embedding and
comment_embeddings. Use this when you want to process "a bunch of threads and
their comments at once" instead of running embed.py and embed_comments.py
separately.

Run AFTER ingest.py.

Usage:
  python embed_threads.py                      # all un-embedded threads
  python embed_threads.py --limit 100         # stop after 100 threads
  python embed_threads.py --subreddit microsaas
  python embed_threads.py --thread-batch 20   # 20 threads per round (default)
  python embed_threads.py --text-batch 100    # max 100 texts per OpenAI call (comments)

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
DEFAULT_THREAD_BATCH = 20   # threads (posts) per round
DEFAULT_TEXT_BATCH = 100   # max texts per OpenAI call (for comment batches)
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


async def run_embed_threads(
    limit: int | None,
    subreddit: str | None,
    thread_batch: int,
    text_batch: int,
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

    # Check if comment_embeddings exists (migration 004); if not, only embed posts
    comment_embeddings_exists = await conn.fetchval(
        """
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'comment_embeddings'
        )
        """
    )
    if not comment_embeddings_exists:
        print("  Note: comment_embeddings table not found (run migration 004). Embedding posts only.\n")

    total_threads = 0
    total_comments = 0

    try:
        while True:
            # 1) Fetch next batch of threads (posts) that need embedding
            rows = await conn.fetch(
                """
                SELECT id, reconstructed_text
                FROM posts
                WHERE reconstructed_text IS NOT NULL
                  AND embedded_at IS NULL
                  AND ($1::text IS NULL OR subreddit = $1)
                LIMIT $2
                """,
                subreddit,
                thread_batch,
            )
            if not rows:
                break

            post_ids = [r["id"] for r in rows]
            post_texts = [r["reconstructed_text"] for r in rows]

            # 2) Fetch all comments for these threads (id, body) - only those not yet embedded
            if comment_embeddings_exists:
                comment_rows = await conn.fetch(
                    """
                    SELECT c.id, c.body, c.post_id
                    FROM comments c
                    JOIN posts p ON p.id = c.post_id
                    LEFT JOIN comment_embeddings ce ON ce.comment_id = c.id
                    WHERE c.post_id = ANY($1::text[])
                      AND ce.comment_id IS NULL
                      AND c.body IS NOT NULL
                      AND TRIM(c.body) != ''
                    """,
                    post_ids,
                )
            else:
                comment_rows = []

            # 3) Embed posts (one API call for this batch of threads)
            print(f"  Embedding {len(rows)} posts...")
            post_vectors = _embed_with_retry(client, post_texts)

            for post_id, vec in zip(post_ids, post_vectors):
                await conn.execute(
                    "UPDATE posts SET embedding = $1::vector, embedded_at = NOW() WHERE id = $2",
                    _vec_to_str(vec),
                    post_id,
                )

            # 4) Embed comments in chunks
            if comment_rows:
                comment_ids = [r["id"] for r in comment_rows]
                comment_bodies = [r["body"] for r in comment_rows]
                for i in range(0, len(comment_ids), text_batch):
                    chunk_ids = comment_ids[i : i + text_batch]
                    chunk_bodies = comment_bodies[i : i + text_batch]
                    vecs = _embed_with_retry(client, chunk_bodies)
                    for cid, vec in zip(chunk_ids, vecs):
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
                print(f"  Embedded {len(comment_rows)} comments from these threads.")
            else:
                print(f"  No new comments to embed for these threads.")

            total_threads += len(rows)
            total_comments += len(comment_rows)
            print(f"  Running total: {total_threads:,} threads, {total_comments:,} comments embedded.")

            if limit and total_threads >= limit:
                break

    finally:
        await conn.close()

    print(f"\nDone. {total_threads:,} threads and {total_comments:,} comments embedded.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Embed Reddit threads (post + comments) together in batches."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Stop after embedding N threads (posts).",
    )
    parser.add_argument(
        "--subreddit",
        default=None,
        metavar="NAME",
        help="Only process threads from this subreddit.",
    )
    parser.add_argument(
        "--thread-batch",
        type=int,
        default=DEFAULT_THREAD_BATCH,
        metavar="N",
        help=f"Number of threads to process per round (default {DEFAULT_THREAD_BATCH}).",
    )
    parser.add_argument(
        "--text-batch",
        type=int,
        default=DEFAULT_TEXT_BATCH,
        metavar="N",
        help=f"Max comment texts per OpenAI call (default {DEFAULT_TEXT_BATCH}).",
    )
    args = parser.parse_args()

    asyncio.run(run_embed_threads(
        limit=args.limit,
        subreddit=args.subreddit,
        thread_batch=args.thread_batch,
        text_batch=args.text_batch,
    ))


if __name__ == "__main__":
    main()
