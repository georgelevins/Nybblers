#!/usr/bin/env python3
"""
Nybblers data ingestion pipeline.

Loads Reddit data from Pushshift ZST dumps into PostgreSQL, then generates
OpenAI embeddings for semantic search.

Stages
------
  import  – Parse ZST files, insert raw posts + comments, compute activity stats.
  embed   – Batch-embed posts and/or comments via OpenAI; resumes automatically
            (skips records that already have embeddings).
  all     – Run import then embed.

Usage
-----
  # Full pipeline from scratch:
  python ingest.py \\
      --submissions ../zst/submissions.zst \\
      --comments    ../zst/comments.zst \\
      --mode all

  # Import only (no OpenAI calls):
  python ingest.py \\
      --submissions ../zst/submissions.zst \\
      --comments    ../zst/comments.zst \\
      --mode import

  # Resume embedding after an interruption (no ZST files needed):
  python ingest.py --mode embed

  # Embed posts only (skip comments):
  python ingest.py --mode embed --skip-comment-embeddings

  # Test on a small slice:
  python ingest.py \\
      --submissions ../zst/submissions.zst \\
      --comments    ../zst/comments.zst \\
      --mode all --limit 2000

Rate limits & cost
------------------
  OpenAI text-embedding-3-small (as of 2025):
    - $0.02 / 1M tokens
    - Tier 1 paid: 3,000 RPM  /  1,000,000 TPM
    - Tier 2:      5,000 RPM  /  2,000,000 TPM

  Estimate for a 100 MB compressed submissions file (~165,000 posts):
    - ~33M tokens  →  $0.66  →  ~33 min (TPM-limited at Tier 1)

  Estimate for a 100 MB compressed comments file (~760,000 raw, ~400,000 after filter):
    - ~30M tokens  →  $0.60  →  ~30 min (TPM-limited at Tier 1)

  DB storage: each 1536-dim vector ≈ 6 KB; 165,000 posts ≈ 1 GB for embeddings alone.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import asyncpg
import zstandard as zstd
from dotenv import load_dotenv

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("ingest")

# ─── Config ───────────────────────────────────────────────────────────────────

# Load .env from the backend directory
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=_env_path)
load_dotenv()

EMBED_BATCH_SIZE = 200          # texts per embedding call
EMBED_CONCURRENCY = 4           # concurrent embedding calls
DB_INSERT_BATCH = 500           # rows per INSERT statement
MIN_COMMENT_BODY_LEN = 50       # characters; shorter comments aren't worth embedding

_DELETED = frozenset({"[deleted]", "[removed]", ""})
_BOT_AUTHORS = frozenset({"AutoModerator", "[deleted]", "reddit", "BotDefense"})

# ─── ZST helpers ──────────────────────────────────────────────────────────────


def iter_zst(path: str, limit: int | None = None) -> Iterator[dict]:
    """Stream JSON objects from a Zstandard-compressed NDJSON file."""
    dctx = zstd.ZstdDecompressor(max_window_size=2**31)
    count = 0
    buf = b""
    with open(path, "rb") as fh:
        with dctx.stream_reader(fh) as reader:
            while True:
                chunk = reader.read(131_072)
                if not chunk:
                    break
                buf += chunk
                lines = buf.split(b"\n")
                buf = lines[-1]
                for line in lines[:-1]:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    count += 1
                    if limit and count >= limit:
                        return
    # Handle any remaining bytes after the loop
    if buf.strip():
        try:
            yield json.loads(buf)
        except json.JSONDecodeError:
            pass


def _ts(val) -> datetime | None:
    """Convert a Unix timestamp (int/float/str) to a UTC datetime."""
    try:
        return datetime.fromtimestamp(int(val), tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return None


# ─── Post extraction ──────────────────────────────────────────────────────────


def extract_post(obj: dict) -> dict | None:
    """Return a clean post dict or None if the record should be skipped."""
    pid = obj.get("id", "").strip()
    title = (obj.get("title") or "").strip()
    author = (obj.get("author") or "").strip()

    if not pid or not title or title.lower() in _DELETED:
        return None
    if author in _BOT_AUTHORS:
        return None

    body = (obj.get("selftext") or "").strip()
    if body.lower() in _DELETED:
        body = ""

    created = _ts(obj.get("created_utc"))
    if not created:
        return None

    # Build the text we will embed: title + body (used for reconstructed_text)
    parts = [f"Title: {title}"]
    if body:
        parts.append(body)
    reconstructed = "\n\n".join(parts)

    permalink = (obj.get("permalink") or "").strip()
    url = obj.get("url") or (f"https://www.reddit.com{permalink}" if permalink else None)

    return {
        "id": pid,
        "subreddit": (obj.get("subreddit") or "").strip(),
        "title": title,
        "body": body or None,
        "author": author or None,
        "created_utc": created,
        "score": _int(obj.get("score")),
        "url": url,
        "num_comments": _int(obj.get("num_comments")),
        "reconstructed_text": reconstructed,
    }


def _int(val) -> int | None:
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


# ─── Comment extraction ───────────────────────────────────────────────────────


def extract_comment(obj: dict) -> dict | None:
    """Return a clean comment dict or None if the record should be skipped."""
    cid = obj.get("id", "").strip()
    body = (obj.get("body") or "").strip()
    author = (obj.get("author") or "").strip()

    if not cid or not body or body.lower() in _DELETED:
        return None
    if author in _BOT_AUTHORS:
        return None

    link_id = (obj.get("link_id") or "").strip()  # e.g. "t3_abc123"
    if not link_id.startswith("t3_"):
        return None
    post_id = link_id[3:]  # strip "t3_" prefix

    parent_id_raw = (obj.get("parent_id") or "").strip()
    parent_type = "comment" if parent_id_raw.startswith("t1_") else "post"

    created = _ts(obj.get("created_utc"))
    if not created:
        return None

    return {
        "id": cid,
        "post_id": post_id,
        "parent_id": parent_id_raw or None,
        "parent_type": parent_type,
        "author": author or None,
        "body": body,
        "created_utc": created,
        "score": _int(obj.get("score")),
        "controversiality": _int(obj.get("controversiality")),
    }


# ─── Database helpers ─────────────────────────────────────────────────────────


async def connect_db() -> asyncpg.Pool:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        log.error("DATABASE_URL is not set — cannot connect.")
        sys.exit(1)
    log.info("Connecting to database…")
    pool = await asyncpg.create_pool(url, min_size=2, max_size=10, command_timeout=120)
    log.info("Connected.")
    return pool


async def ensure_schema(conn: asyncpg.Connection) -> None:
    """Create missing tables and indexes without touching existing ones."""
    # Import here so EMBEDDING_BACKEND env var is already loaded from .env
    from repositories.embeddings import EMBEDDING_DIM  # noqa: PLC0415

    await conn.execute(f"""
        CREATE TABLE IF NOT EXISTS comment_embeddings (
            comment_id  TEXT PRIMARY KEY REFERENCES comments(id) ON DELETE CASCADE,
            embedding   vector({EMBEDDING_DIM}) NOT NULL,
            embedded_at TIMESTAMP NOT NULL DEFAULT NOW()
        );
    """)

    # pgvector HNSW indexes for fast approximate nearest-neighbour search.
    # Build AFTER bulk data load for speed; these commands are idempotent.
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS posts_embedding_hnsw
            ON posts USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
    """)
    await conn.execute("""
        CREATE INDEX IF NOT EXISTS comment_embeddings_hnsw
            ON comment_embeddings USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
    """)
    log.info("Schema ensured (comment_embeddings table + HNSW indexes).")


async def insert_posts(pool: asyncpg.Pool, posts: list[dict], dry_run: bool) -> int:
    if not posts or dry_run:
        return 0
    async with pool.acquire() as conn:
        await conn.executemany(
            """
            INSERT INTO posts
                (id, subreddit, title, body, author, created_utc, score, url,
                 num_comments, reconstructed_text)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
            ON CONFLICT (id) DO NOTHING
            """,
            [
                (
                    p["id"], p["subreddit"], p["title"], p["body"], p["author"],
                    p["created_utc"], p["score"], p["url"],
                    p["num_comments"], p["reconstructed_text"],
                )
                for p in posts
            ],
        )
    return len(posts)


async def insert_comments(pool: asyncpg.Pool, comments: list[dict], dry_run: bool) -> int:
    if not comments or dry_run:
        return 0
    async with pool.acquire() as conn:
        await conn.executemany(
            """
            INSERT INTO comments
                (id, post_id, parent_id, parent_type, author, body,
                 created_utc, score, controversiality)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
            ON CONFLICT (id) DO NOTHING
            """,
            [
                (
                    c["id"], c["post_id"], c["parent_id"], c["parent_type"],
                    c["author"], c["body"], c["created_utc"],
                    c["score"], c["controversiality"],
                )
                for c in comments
            ],
        )
    return len(comments)


async def update_activity_stats(pool: asyncpg.Pool, dry_run: bool) -> None:
    """
    Compute last_comment_utc, recent_comment_count, and activity_ratio for all posts
    that have comments. activity_ratio = comments per month since post creation.
    """
    if dry_run:
        return
    log.info("Updating activity stats (last_comment_utc, recent_comment_count, activity_ratio)…")
    async with pool.acquire() as conn:
        updated = await conn.fetchval("""
            WITH agg AS (
                SELECT
                    post_id,
                    COUNT(*)            AS cnt,
                    MAX(created_utc)    AS last_ts
                FROM comments
                GROUP BY post_id
            )
            UPDATE posts p
            SET
                last_comment_utc      = agg.last_ts,
                recent_comment_count  = agg.cnt,
                activity_ratio        = agg.cnt::float /
                    GREATEST(
                        1.0,
                        EXTRACT(EPOCH FROM (NOW() - p.created_utc)) / 86400.0 / 30.0
                    )
            FROM agg
            WHERE p.id = agg.post_id
            RETURNING p.id
        """)
    log.info("Activity stats updated for %s posts.", updated if updated else "0")


# ─── Embedding helpers ────────────────────────────────────────────────────────


def _check_embedding_backend() -> None:
    """Log which backend will be used so there are no surprises."""
    from repositories.embeddings import EMBEDDING_DIM, _BACKEND, _LOCAL_MODEL_NAME  # noqa: PLC0415

    if _BACKEND == "local":
        log.info(
            "Embedding backend: LOCAL  model=%s  dim=%d  (set EMBEDDING_BACKEND=openai to use OpenAI)",
            _LOCAL_MODEL_NAME, EMBEDDING_DIM,
        )
    else:
        log.info("Embedding backend: OPENAI  model=text-embedding-3-small  dim=%d", EMBEDDING_DIM)


def _to_pg_vector(embedding: list[float]) -> str:
    return "[" + ",".join(map(str, embedding)) + "]"


# ─── Generic embed-and-store helper ──────────────────────────────────────────


async def _embed_and_store(
    pool: asyncpg.Pool,
    label: str,
    fetch_sql: str,
    fetch_params: list,
    text_field: str,
    id_field: str,
    store_fn,           # async callable(pool, ids, vecs)
    total: int,
    batch_size: int,
    concurrency: int,
    dry_run: bool,
) -> None:
    from repositories.embeddings import embed_texts  # noqa: PLC0415

    sem = asyncio.Semaphore(concurrency)
    embedded = 0
    t0 = time.monotonic()

    async def process_batch(rows: list) -> None:
        nonlocal embedded
        ids = [r[id_field] for r in rows]
        texts = [r[text_field] or "" for r in rows]
        async with sem:
            if dry_run:
                await asyncio.sleep(0.02)
                vecs = [[0.0] * 4 for _ in texts]  # placeholder in dry-run
            else:
                vecs = await embed_texts(texts)
        if not dry_run:
            await store_fn(pool, ids, vecs)
        embedded += len(ids)
        elapsed = time.monotonic() - t0
        rate = embedded / elapsed if elapsed > 0 else 0
        eta = (total - embedded) / rate if rate > 0 else float("inf")
        log.info("%s embedded: %d / %d  (%.0f/s, ETA %.0fm)", label, embedded, total, rate, eta / 60)

    offset = 0
    tasks: list[asyncio.Task] = []
    while offset < total:
        async with pool.acquire() as conn:
            rows = await conn.fetch(fetch_sql, *fetch_params, batch_size, offset)
        if not rows:
            break
        tasks.append(asyncio.create_task(process_batch(list(rows))))
        offset += batch_size

        if len(tasks) >= concurrency * 4:
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for t in done:
                await t
            tasks = list(pending)

    if tasks:
        await asyncio.gather(*tasks)

    log.info("Done. %s embedded total: %d", label, embedded)


# ─── Embed posts ──────────────────────────────────────────────────────────────


async def _store_post_embeddings(pool: asyncpg.Pool, ids: list, vecs: list) -> None:
    async with pool.acquire() as conn:
        await conn.executemany(
            "UPDATE posts SET embedding = $2::vector, embedded_at = NOW() WHERE id = $1",
            [(_id, _to_pg_vector(v)) for _id, v in zip(ids, vecs)],
        )


async def embed_posts(pool: asyncpg.Pool, batch_size: int, concurrency: int, dry_run: bool) -> None:
    """Fetch unembedded posts, generate embeddings, store in posts.embedding."""
    async with pool.acquire() as conn:
        total = await conn.fetchval("SELECT COUNT(*) FROM posts WHERE embedding IS NULL")
    if total == 0:
        log.info("All posts are already embedded — nothing to do.")
        return
    log.info("Embedding %d posts (batch=%d, concurrency=%d)…", total, batch_size, concurrency)
    await _embed_and_store(
        pool=pool,
        label="Posts",
        fetch_sql="""
            SELECT id, COALESCE(reconstructed_text, title) AS reconstructed_text
            FROM posts WHERE embedding IS NULL ORDER BY id LIMIT $1 OFFSET $2
        """,
        fetch_params=[],
        text_field="reconstructed_text",
        id_field="id",
        store_fn=_store_post_embeddings,
        total=total,
        batch_size=batch_size,
        concurrency=concurrency,
        dry_run=dry_run,
    )


# ─── Embed comments ───────────────────────────────────────────────────────────


async def _store_comment_embeddings(pool: asyncpg.Pool, ids: list, vecs: list) -> None:
    async with pool.acquire() as conn:
        await conn.executemany(
            """
            INSERT INTO comment_embeddings (comment_id, embedding, embedded_at)
            VALUES ($1, $2::vector, NOW())
            ON CONFLICT (comment_id) DO NOTHING
            """,
            [(_id, _to_pg_vector(v)) for _id, v in zip(ids, vecs)],
        )


async def embed_comments(pool: asyncpg.Pool, batch_size: int, concurrency: int, dry_run: bool) -> None:
    """Embed substantive comments and store in comment_embeddings."""
    async with pool.acquire() as conn:
        total = await conn.fetchval(
            """
            SELECT COUNT(*) FROM comments c
            WHERE LENGTH(c.body) >= $1
              AND c.body NOT IN ('[deleted]', '[removed]')
              AND NOT EXISTS (SELECT 1 FROM comment_embeddings ce WHERE ce.comment_id = c.id)
            """,
            MIN_COMMENT_BODY_LEN,
        )
    if total == 0:
        log.info("All qualifying comments are already embedded — nothing to do.")
        return
    log.info(
        "Embedding %d comments (body >= %d chars, batch=%d, concurrency=%d)…",
        total, MIN_COMMENT_BODY_LEN, batch_size, concurrency,
    )
    await _embed_and_store(
        pool=pool,
        label="Comments",
        fetch_sql="""
            SELECT c.id, c.body
            FROM comments c
            WHERE LENGTH(c.body) >= $1
              AND c.body NOT IN ('[deleted]', '[removed]')
              AND NOT EXISTS (SELECT 1 FROM comment_embeddings ce WHERE ce.comment_id = c.id)
            ORDER BY c.id LIMIT $2 OFFSET $3
        """,
        fetch_params=[MIN_COMMENT_BODY_LEN],
        text_field="body",
        id_field="id",
        store_fn=_store_comment_embeddings,
        total=total,
        batch_size=batch_size,
        concurrency=concurrency,
        dry_run=dry_run,
    )


# ─── Import stage ─────────────────────────────────────────────────────────────


async def run_import(args: argparse.Namespace, pool: asyncpg.Pool) -> None:
    if not args.submissions and not args.comments:
        log.error("--mode import requires at least one of --submissions or --comments.")
        sys.exit(1)

    if args.submissions:
        log.info("Importing posts from %s…", args.submissions)
        batch: list[dict] = []
        total_inserted = 0
        total_skipped = 0
        t0 = time.monotonic()

        for obj in iter_zst(args.submissions, limit=args.limit):
            post = extract_post(obj)
            if post is None:
                total_skipped += 1
                continue
            batch.append(post)
            if len(batch) >= DB_INSERT_BATCH:
                total_inserted += await insert_posts(pool, batch, args.dry_run)
                batch.clear()
                elapsed = time.monotonic() - t0
                log.info("Posts inserted: %d  (skipped: %d, %.0fs)", total_inserted, total_skipped, elapsed)

        if batch:
            total_inserted += await insert_posts(pool, batch, args.dry_run)
        log.info(
            "Posts import complete: %d inserted, %d skipped (dry_run=%s).",
            total_inserted, total_skipped, args.dry_run,
        )

    if args.comments:
        log.info("Importing comments from %s…", args.comments)
        batch = []
        total_inserted = 0
        total_skipped = 0
        t0 = time.monotonic()

        for obj in iter_zst(args.comments, limit=args.limit):
            comment = extract_comment(obj)
            if comment is None:
                total_skipped += 1
                continue
            batch.append(comment)
            if len(batch) >= DB_INSERT_BATCH:
                total_inserted += await insert_comments(pool, batch, args.dry_run)
                batch.clear()
                elapsed = time.monotonic() - t0
                log.info("Comments inserted: %d  (skipped: %d, %.0fs)", total_inserted, total_skipped, elapsed)

        if batch:
            total_inserted += await insert_comments(pool, batch, args.dry_run)
        log.info(
            "Comments import complete: %d inserted, %d skipped (dry_run=%s).",
            total_inserted, total_skipped, args.dry_run,
        )

    # Recompute activity stats after loading comments
    if args.comments:
        await update_activity_stats(pool, args.dry_run)


# ─── Embed stage ──────────────────────────────────────────────────────────────


async def run_embed(args: argparse.Namespace, pool: asyncpg.Pool) -> None:
    _check_embedding_backend()
    if not args.skip_post_embeddings:
        await embed_posts(pool, args.embed_batch_size, args.embed_concurrency, args.dry_run)
    if not args.skip_comment_embeddings:
        await embed_comments(pool, args.embed_batch_size, args.embed_concurrency, args.dry_run)


# ─── Entry point ──────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Nybblers ingestion pipeline — load Reddit ZST data and generate embeddings.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--submissions", metavar="PATH", help="Path to submissions .zst file")
    p.add_argument("--comments", metavar="PATH", help="Path to comments .zst file")
    p.add_argument(
        "--mode",
        choices=["import", "embed", "all"],
        default="all",
        help="Pipeline stage to run (default: all)",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Stop after N records per file (for testing)",
    )
    p.add_argument(
        "--embed-batch-size",
        type=int,
        default=EMBED_BATCH_SIZE,
        metavar="N",
        help=f"Texts per OpenAI embedding call (default: {EMBED_BATCH_SIZE})",
    )
    p.add_argument(
        "--embed-concurrency",
        type=int,
        default=EMBED_CONCURRENCY,
        metavar="N",
        help=f"Concurrent OpenAI embedding calls (default: {EMBED_CONCURRENCY})",
    )
    p.add_argument(
        "--skip-post-embeddings",
        action="store_true",
        help="Skip embedding posts (embed stage only)",
    )
    p.add_argument(
        "--skip-comment-embeddings",
        action="store_true",
        help="Skip embedding comments (embed stage only)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and validate data but do not write to DB or call OpenAI",
    )
    return p.parse_args()


async def main() -> None:
    args = parse_args()

    if args.dry_run:
        log.info("DRY RUN — no DB writes or OpenAI calls.")

    pool = await connect_db()

    try:
        async with pool.acquire() as conn:
            await ensure_schema(conn)

        if args.mode in ("import", "all"):
            await run_import(args, pool)

        if args.mode in ("embed", "all"):
            await run_embed(args, pool)
    finally:
        await pool.close()

    log.info("Ingestion complete.")


if __name__ == "__main__":
    asyncio.run(main())
