"""
Reddit JSONL ingestion pipeline for RedditDemand.

Supports plain JSONL files and Zstandard-compressed (.zst) files.

Usage:
  # Single subreddit pair
  python ingest.py --posts Entrepreneur_submissions.zst --comments Entrepreneur_comments.zst

  # Single pair, first 1000 rows only (for testing)
  python ingest.py --posts Entrepreneur_submissions.zst --comments Entrepreneur_comments.zst --limit 1000

  # Only ingest posts from 2024
  python ingest.py --posts Entrepreneur_submissions.zst --comments Entrepreneur_comments.zst --year 2024

  # Skip stats/reconstruction (pure ingest test)
  python ingest.py --posts ... --comments ... --limit 500 --skip-stats

  # Whole subreddits directory (ingests all matched pairs)
  python ingest.py --dir /path/to/subreddits/

Requires DATABASE_URL in environment (same as the API).
Runs all steps in order:
  1. Insert posts
  2. Insert comments
  3. Compute last_comment_utc + recent_comment_count
  4. Compute activity_ratio (heat score)
  5. Reconstruct threads into text blobs for embedding
"""

import argparse
import asyncio
import io
import json
import os
import sys
from calendar import timegm
from datetime import datetime, timezone
from pathlib import Path

import asyncpg
import zstandard as zstd
from dotenv import load_dotenv

load_dotenv()

BATCH_SIZE = 500
LOG_EVERY = 10_000
RECENT_DAYS = 90
TOP_COMMENTS_PER_THREAD = 10
RECONSTRUCT_BATCH = 200

DELETED = {"[deleted]", "[removed]"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utc(ts) -> datetime | None:
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc)
    except (ValueError, OSError, OverflowError):
        return None


def _clean(text: str | None) -> str | None:
    if text is None:
        return None
    return None if text.strip() in DELETED else text


def _year_bounds(year: int) -> tuple[int, int]:
    """Return Unix timestamps for the start and end of the given calendar year."""
    start = timegm((year, 1, 1, 0, 0, 0, 0, 0, 0))
    end = timegm((year + 1, 1, 1, 0, 0, 0, 0, 0, 0))
    return start, end


def open_jsonl(path: Path):
    """
    Yield lines from a plain JSONL or .zst-compressed JSONL file.
    Streams .zst without writing a decompressed copy to disk.
    """
    if path.suffix == ".zst":
        dctx = zstd.ZstdDecompressor()
        with path.open("rb") as fh:
            with dctx.stream_reader(fh) as reader:
                text_stream = io.TextIOWrapper(reader, encoding="utf-8", errors="replace")
                yield from text_stream
    else:
        with path.open("r", encoding="utf-8", errors="replace") as fh:
            yield from fh


# ---------------------------------------------------------------------------
# Ingest log helpers
# ---------------------------------------------------------------------------


async def _log_start(conn: asyncpg.Connection, file_name: str, file_type: str) -> int:
    """Insert a 'running' row into ingest_log and return its id."""
    return await conn.fetchval(
        """
        INSERT INTO ingest_log (file_name, file_type, status)
        VALUES ($1, $2, 'running')
        RETURNING id
        """,
        file_name,
        file_type,
    )


async def _log_complete(conn: asyncpg.Connection, log_id: int, rows_inserted: int) -> None:
    await conn.execute(
        """
        UPDATE ingest_log
        SET status = 'complete', rows_inserted = $2, completed_at = NOW()
        WHERE id = $1
        """,
        log_id,
        rows_inserted,
    )


async def _log_failed(conn: asyncpg.Connection, log_id: int, error: str) -> None:
    await conn.execute(
        """
        UPDATE ingest_log
        SET status = 'failed', error_text = $2, completed_at = NOW()
        WHERE id = $1
        """,
        log_id,
        error,
    )


async def _already_done(conn: asyncpg.Connection, file_name: str) -> bool:
    """Return True if this file has already been successfully ingested."""
    result = await conn.fetchval(
        "SELECT 1 FROM ingest_log WHERE file_name = $1 AND status = 'complete' LIMIT 1",
        file_name,
    )
    return result is not None


# ---------------------------------------------------------------------------
# Step 1 — Insert posts
# ---------------------------------------------------------------------------


async def insert_posts(
    conn: asyncpg.Connection,
    path: Path,
    limit: int | None = None,
    year: int | None = None,
) -> int:
    if await _already_done(conn, path.name):
        print(f"  Skipping {path.name} (already ingested)")
        return 0

    year_start, year_end = _year_bounds(year) if year else (None, None)

    sql = """
        INSERT INTO posts (id, subreddit, title, body, author, created_utc,
                           score, url, num_comments)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (id) DO NOTHING
    """
    batch = []
    total = 0
    log_id = await _log_start(conn, path.name, "submissions")

    try:
        for line in open_jsonl(path):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            post_id = obj.get("id", "")
            if not post_id:
                continue

            # Year filter
            if year is not None:
                ts = obj.get("created_utc")
                try:
                    ts_int = int(ts)
                except (TypeError, ValueError):
                    continue
                if not (year_start <= ts_int < year_end):
                    continue

            batch.append((
                post_id,
                obj.get("subreddit", ""),
                obj.get("title", ""),
                _clean(obj.get("selftext")),
                obj.get("author"),
                _utc(obj.get("created_utc")),
                obj.get("score"),
                obj.get("url"),
                obj.get("num_comments"),
            ))

            if len(batch) >= BATCH_SIZE:
                await conn.executemany(sql, batch)
                total += len(batch)
                batch = []
                if total % LOG_EVERY == 0:
                    print(f"  posts: {total:,} rows inserted")
                if limit and total >= limit:
                    break

        if batch:
            await conn.executemany(sql, batch)
            total += len(batch)

    except Exception as exc:
        await _log_failed(conn, log_id, str(exc))
        raise

    await _log_complete(conn, log_id, total)
    print(f"  posts: {total:,} rows inserted (done)")
    return total


# ---------------------------------------------------------------------------
# Step 2 — Insert comments
# ---------------------------------------------------------------------------


async def _load_post_ids(conn: asyncpg.Connection) -> set[str]:
    rows = await conn.fetch("SELECT id FROM posts")
    return {r["id"] for r in rows}


async def insert_comments(
    conn: asyncpg.Connection,
    path: Path,
    limit: int | None = None,
    year: int | None = None,
) -> int:
    if await _already_done(conn, path.name):
        print(f"  Skipping {path.name} (already ingested)")
        return 0

    year_start, year_end = _year_bounds(year) if year else (None, None)

    print("  Loading post IDs for FK filtering...")
    post_ids = await _load_post_ids(conn)
    print(f"  {len(post_ids):,} posts in DB")

    sql = """
        INSERT INTO comments (id, post_id, parent_id, parent_type, author,
                              body, created_utc, score, controversiality)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (id) DO NOTHING
    """
    batch = []
    total = 0
    skipped = 0
    log_id = await _log_start(conn, path.name, "comments")

    try:
        for line in open_jsonl(path):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            comment_id = obj.get("id", "")
            body = _clean(obj.get("body"))
            if not comment_id or body is None:
                skipped += 1
                continue

            # Year filter
            if year is not None:
                ts = obj.get("created_utc")
                try:
                    ts_int = int(ts)
                except (TypeError, ValueError):
                    skipped += 1
                    continue
                if not (year_start <= ts_int < year_end):
                    skipped += 1
                    continue

            link_id = obj.get("link_id", "")
            post_id = link_id[3:] if link_id.startswith("t3_") else link_id

            if post_id not in post_ids:
                skipped += 1
                continue

            parent_id_raw = obj.get("parent_id", "")
            parent_type = parent_id_raw[:2] if parent_id_raw else None  # "t1" or "t3"

            batch.append((
                comment_id,
                post_id,
                parent_id_raw or None,
                parent_type,
                obj.get("author"),
                body,
                _utc(obj.get("created_utc")),
                obj.get("score"),
                obj.get("controversiality", 0),
            ))

            if len(batch) >= BATCH_SIZE:
                await conn.executemany(sql, batch)
                total += len(batch)
                batch = []
                if total % LOG_EVERY == 0:
                    print(f"  comments: {total:,} rows inserted")
                if limit and total >= limit:
                    break

        if batch:
            await conn.executemany(sql, batch)
            total += len(batch)

    except Exception as exc:
        await _log_failed(conn, log_id, str(exc))
        raise

    await _log_complete(conn, log_id, total)
    print(f"  comments: {total:,} inserted, {skipped:,} skipped (done)")
    return total


# ---------------------------------------------------------------------------
# Step 3 — Compute last_comment_utc + recent_comment_count
# ---------------------------------------------------------------------------


async def update_comment_stats(conn: asyncpg.Connection) -> None:
    print("  Computing last_comment_utc and recent_comment_count...")
    await conn.execute(f"""
        UPDATE posts p
        SET
            last_comment_utc     = agg.last_comment_utc,
            recent_comment_count = agg.recent_count
        FROM (
            SELECT
                post_id,
                MAX(created_utc) AS last_comment_utc,
                COUNT(*) FILTER (
                    WHERE created_utc > NOW() - INTERVAL '{RECENT_DAYS} days'
                ) AS recent_count
            FROM comments
            GROUP BY post_id
        ) agg
        WHERE p.id = agg.post_id
    """)
    print("  Done.")


# ---------------------------------------------------------------------------
# Step 4 — Compute activity_ratio (heat score)
# ---------------------------------------------------------------------------


async def update_activity_ratio(conn: asyncpg.Connection) -> None:
    print("  Computing activity_ratio...")
    await conn.execute("""
        UPDATE posts
        SET activity_ratio =
            COALESCE(recent_comment_count, 0)
            * ln(1 + GREATEST(
                EXTRACT(EPOCH FROM (NOW() - created_utc)) / 86400.0,
                1
            ))
    """)
    print("  Done.")


# ---------------------------------------------------------------------------
# Step 5 — Reconstruct threads
# ---------------------------------------------------------------------------


def _build_blob(title: str, body: str | None, comments: list[str]) -> str:
    parts = [f"[TITLE]\n{title}"]
    if body:
        parts.append(f"[BODY]\n{body}")
    if comments:
        comment_text = "\n\n".join(c for c in comments if c)
        parts.append(f"[TOP COMMENTS]\n{comment_text}")
    return "\n\n".join(parts)


async def reconstruct_threads(conn: asyncpg.Connection) -> int:
    total = 0

    while True:
        rows = await conn.fetch(f"""
            SELECT
                p.id,
                p.title,
                p.body,
                array_agg(c.body ORDER BY c.score DESC NULLS LAST)
                    FILTER (WHERE c.body IS NOT NULL) AS top_comments
            FROM posts p
            LEFT JOIN (
                SELECT post_id, body, score
                FROM comments
                WHERE body IS NOT NULL
                ORDER BY score DESC NULLS LAST
            ) c ON c.post_id = p.id
            WHERE p.reconstructed_text IS NULL
            GROUP BY p.id, p.title, p.body
            LIMIT {RECONSTRUCT_BATCH}
        """)

        if not rows:
            break

        updates = []
        for row in rows:
            top = (row["top_comments"] or [])[:TOP_COMMENTS_PER_THREAD]
            blob = _build_blob(row["title"], row["body"], top)
            updates.append((blob, row["id"]))

        await conn.executemany(
            "UPDATE posts SET reconstructed_text = $1 WHERE id = $2",
            updates,
        )
        total += len(rows)
        print(f"  reconstructed_text: {total:,} threads done")

    print(f"  Thread reconstruction complete ({total:,} threads)")
    return total


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------


async def _ingest_pair(
    conn: asyncpg.Connection,
    posts_path: Path,
    comments_path: Path,
    limit: int | None,
    year: int | None,
) -> None:
    print(f"\n  Posts:    {posts_path.name}")
    print(f"  Comments: {comments_path.name}")
    if limit:
        print(f"  Limit:    {limit:,} rows per file")
    if year:
        print(f"  Year:     {year}")
    await insert_posts(conn, posts_path, limit=limit, year=year)
    await insert_comments(conn, comments_path, limit=limit, year=year)


def _find_pairs(directory: Path) -> list[tuple[Path, Path]]:
    """Find matching submissions+comments pairs in a directory."""
    submissions = {p.name.replace("_submissions.zst", ""): p
                   for p in directory.glob("*_submissions.zst")}
    comments = {p.name.replace("_comments.zst", ""): p
                for p in directory.glob("*_comments.zst")}
    matched = sorted(set(submissions) & set(comments))
    return [(submissions[n], comments[n]) for n in matched]


async def main_async(
    posts_path: Path | None,
    comments_path: Path | None,
    subreddits_dir: Path | None,
    limit: int | None = None,
    year: int | None = None,
    skip_stats: bool = False,
) -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set.", file=sys.stderr)
        sys.exit(1)

    print("Connecting to database...")
    conn = await asyncpg.connect(database_url)

    try:
        if subreddits_dir:
            pairs = _find_pairs(subreddits_dir)
            if not pairs:
                print(f"ERROR: No matched submission/comment pairs found in {subreddits_dir}", file=sys.stderr)
                sys.exit(1)
            names = [p.name.replace("_submissions.zst", "") for p, _ in pairs]
            print(f"Found {len(pairs)} subreddit(s): {', '.join(names)}")
            for sub_posts, sub_comments in pairs:
                print(f"\n=== {sub_posts.name.replace('_submissions.zst', '')} ===")
                await _ingest_pair(conn, sub_posts, sub_comments, limit=limit, year=year)
        else:
            await _ingest_pair(conn, posts_path, comments_path, limit=limit, year=year)

        if skip_stats:
            print("\n[--skip-stats] Skipping steps 3–5.")
        else:
            print("\n[3/5] Computing comment stats...")
            await update_comment_stats(conn)

            print("\n[4/5] Computing activity_ratio...")
            await update_activity_ratio(conn)

            print("\n[5/5] Reconstructing threads...")
            await reconstruct_threads(conn)

        print("\nIngestion complete.")

    finally:
        await conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest Reddit JSONL/.zst dumps into Postgres for RedditDemand."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dir", help="Directory of *_submissions.zst / *_comments.zst pairs")
    group.add_argument("--posts", help="Single submissions JSONL or .zst file")
    parser.add_argument("--comments", help="Comments file (required with --posts)")
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Stop after inserting N rows per file. Useful for test runs.",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=None,
        metavar="YYYY",
        help="Only ingest records from this calendar year (filters on created_utc).",
    )
    parser.add_argument(
        "--skip-stats",
        action="store_true",
        help="Skip steps 3–5 (comment stats, activity_ratio, thread reconstruction).",
    )
    args = parser.parse_args()

    if args.posts and not args.comments:
        parser.error("--comments is required when using --posts")

    posts_path = Path(args.posts) if args.posts else None
    comments_path = Path(args.comments) if args.comments else None
    subreddits_dir = Path(args.dir) if args.dir else None

    if posts_path:
        for p in (posts_path, comments_path):
            if not p.exists():
                print(f"ERROR: file not found: {p}", file=sys.stderr)
                sys.exit(1)
    if subreddits_dir and not subreddits_dir.is_dir():
        print(f"ERROR: not a directory: {subreddits_dir}", file=sys.stderr)
        sys.exit(1)

    asyncio.run(main_async(
        posts_path,
        comments_path,
        subreddits_dir,
        limit=args.limit,
        year=args.year,
        skip_stats=args.skip_stats,
    ))


if __name__ == "__main__":
    main()
