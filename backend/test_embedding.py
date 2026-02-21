"""
Test embedding pipeline: embed one post + its comments, store in DB, then run
similarity queries to check quality.

Usage:
  # Use sample post+comments (inserts into DB if needed), then embed and test
  python test_embedding.py

  # Load from a folder that has *_submissions.zst and *_comments.zst (one pair)
  python test_embedding.py --zst-dir path/to/zst

  # Or point at the two files explicitly
  python test_embedding.py --posts path/to/submissions.zst --comments path/to/comments.zst
  python test_embedding.py --posts sub.zst --comments com.zst --ingest-limit 200

  # Use an existing post from DB by id
  python test_embedding.py --post-id abc123

Requires: DATABASE_URL, OPENAI_API_KEY
Expects Reddit JSONL format (e.g. pushshift): id, subreddit, title, selftext, link_id, body, etc.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

# Backend root for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
load_dotenv()

from openai_utils import embed_text

# For --posts/--comments: minimal loader (no ingest_log). Reuses ingest for stats + reconstruct.
try:
    from ingest import (
        open_jsonl,
        update_comment_stats,
        update_activity_ratio,
        reconstruct_threads,
    )
except ImportError:
    open_jsonl = update_comment_stats = update_activity_ratio = reconstruct_threads = None

EMBEDDING_DIM = 1536
TOP_COMMENTS_FOR_RECONSTRUCT = 10


def _vec_to_str(vec: list[float]) -> str:
    return "[" + ",".join(str(x) for x in vec) + "]"


def _build_reconstructed_text(title: str, body: str | None, comment_bodies: list[str]) -> str:
    """Same format as ingest.py for post-level embedding."""
    parts = [f"[TITLE]\n{title}"]
    if body:
        parts.append(f"[BODY]\n{body}")
    top = comment_bodies[:TOP_COMMENTS_FOR_RECONSTRUCT]
    if top:
        parts.append("[TOP COMMENTS]\n" + "\n\n".join(c for c in top if c))
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Load from .zst / JSONL (Reddit dump format, same as ingest.py)
# ---------------------------------------------------------------------------

DELETED = {"[deleted]", "[removed]"}


def _utc(ts) -> datetime | None:
    if ts is None:
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc)
    except (ValueError, OSError, OverflowError):
        return None


def _naive_utc(dt: datetime | None) -> datetime | None:
    """Return None or a naive datetime in UTC (asyncpg-friendly for TIMESTAMPTZ)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def _clean(text: str | None) -> str | None:
    if text is None:
        return None
    return None if text.strip() in DELETED else text


async def load_from_zst(
    conn: asyncpg.Connection,
    posts_path: Path,
    comments_path: Path,
    posts_limit: int,
    comments_limit: int,
) -> int:
    """
    Load a limited number of posts and comments from Reddit JSONL/.zst files.
    Does not use ingest_log (safe to run multiple times; ON CONFLICT DO NOTHING).
    Then runs comment stats, activity_ratio, and thread reconstruction.
    Returns number of posts inserted.
    """
    if open_jsonl is None or update_comment_stats is None:
        print("ERROR: ingest module not available. Run from backend/ with ingest.py present.", file=sys.stderr)
        raise RuntimeError("ingest not available")

    await conn.execute("SET timezone = 'UTC'")

    sql_post = """
        INSERT INTO posts (id, subreddit, title, body, author, created_utc, score, url, num_comments)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (id) DO NOTHING
    """
    post_count = 0
    batch = []
    batch_size = 100
    for line in open_jsonl(posts_path):
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
        batch.append((
            post_id,
            obj.get("subreddit", ""),
            obj.get("title", ""),
            _clean(obj.get("selftext")),
            obj.get("author"),
            _naive_utc(_utc(obj.get("created_utc"))),
            obj.get("score"),
            obj.get("url"),
            obj.get("num_comments"),
        ))
        if len(batch) >= batch_size:
            await conn.executemany(sql_post, batch)
            post_count += len(batch)
            batch = []
            if post_count >= posts_limit:
                break
    if batch:
        await conn.executemany(sql_post, batch)
        post_count += len(batch)
    print(f"  Loaded {post_count} posts from {posts_path.name}")

    post_ids = {r["id"] for r in await conn.fetch("SELECT id FROM posts")}
    sql_comment = """
        INSERT INTO comments (id, post_id, parent_id, parent_type, author, body, created_utc, score, controversiality)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (id) DO NOTHING
    """
    comment_count = 0
    batch = []
    for line in open_jsonl(comments_path):
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
            continue
        link_id = obj.get("link_id", "")
        post_id = link_id[3:] if link_id.startswith("t3_") else link_id
        if post_id not in post_ids:
            continue
        parent_id_raw = obj.get("parent_id", "")
        parent_type = parent_id_raw[:2] if parent_id_raw else None
        batch.append((
            comment_id,
            post_id,
            parent_id_raw or None,
            parent_type,
            obj.get("author"),
            body,
            _naive_utc(_utc(obj.get("created_utc"))),
            obj.get("score"),
            obj.get("controversiality", 0),
        ))
        if len(batch) >= batch_size:
            await conn.executemany(sql_comment, batch)
            comment_count += len(batch)
            batch = []
            if comment_count >= comments_limit:
                break
    if batch:
        await conn.executemany(sql_comment, batch)
        comment_count += len(batch)
    print(f"  Loaded {comment_count} comments from {comments_path.name}")

    print("  Computing comment stats and activity_ratio...")
    await update_comment_stats(conn)
    await update_activity_ratio(conn)
    print("  Reconstructing threads...")
    await reconstruct_threads(conn)
    return post_count


def _find_zst_pair(directory: Path) -> tuple[Path, Path] | None:
    """Find a single *_submissions.zst / *_comments.zst pair in directory. Returns (submissions, comments) or None."""
    submissions = {p.name.replace("_submissions.zst", ""): p for p in directory.glob("*_submissions.zst")}
    comments = {p.name.replace("_comments.zst", ""): p for p in directory.glob("*_comments.zst")}
    matched = sorted(set(submissions) & set(comments))
    if not matched:
        return None
    name = matched[0]
    return (submissions[name], comments[name])


async def pick_post_with_comments(conn: asyncpg.Connection) -> str | None:
    """Return a post id that has at least one comment and reconstructed_text, or None."""
    row = await conn.fetchrow(
        """
        SELECT p.id
        FROM posts p
        JOIN comments c ON c.post_id = p.id
        WHERE p.reconstructed_text IS NOT NULL
        GROUP BY p.id
        ORDER BY COUNT(*) DESC
        LIMIT 1
        """
    )
    return row["id"] if row else None


# ---------------------------------------------------------------------------
# Sample data (used when DB has no post or --post-id not given)
# ---------------------------------------------------------------------------

SAMPLE_POST = {
    "id": "test_embed_post_1",
    "subreddit": "freelance",
    "title": "Client hasn't paid in 90 days — what do I do?",
    "body": "I've sent three invoices and two reminder emails. They keep saying the check is in the mail. At this point I've done $4k of work and I'm seriously considering small claims court. Has anyone actually had success with that?",
    "author": "test_user",
    "created_utc": datetime(2023, 5, 12, 14, 22, 0, tzinfo=timezone.utc),
    "score": 42,
    "url": "https://reddit.com/r/freelance/comments/test",
    "num_comments": 3,
}

SAMPLE_COMMENTS = [
    {
        "id": "test_embed_c1",
        "post_id": SAMPLE_POST["id"],
        "parent_id": "t3_xxx",
        "parent_type": "t3",
        "author": "user2",
        "body": "Small claims is totally worth it. I did it once and got a default judgment when they didn't show. Took 3 months but I got paid.",
        "created_utc": datetime(2023, 5, 13, 10, 0, 0, tzinfo=timezone.utc),
        "score": 15,
        "controversiality": 0,
    },
    {
        "id": "test_embed_c2",
        "post_id": SAMPLE_POST["id"],
        "parent_id": "t3_xxx",
        "parent_type": "t3",
        "author": "user3",
        "body": "Send a formal demand letter first — certified mail. Often that's enough to get them to pay before you have to file.",
        "created_utc": datetime(2023, 5, 13, 11, 30, 0, tzinfo=timezone.utc),
        "score": 22,
        "controversiality": 0,
    },
    {
        "id": "test_embed_c3",
        "post_id": SAMPLE_POST["id"],
        "parent_id": "t3_xxx",
        "parent_type": "t3",
        "author": "user4",
        "body": "Net 60 and Net 90 are the worst. I now require 50% upfront for any client that insists on long payment terms.",
        "created_utc": datetime(2023, 5, 14, 9, 0, 0, tzinfo=timezone.utc),
        "score": 8,
        "controversiality": 0,
    },
]


async def ensure_sample_post_and_comments(conn: asyncpg.Connection) -> str:
    """Insert sample post + comments if not present; return post id."""
    post_id = SAMPLE_POST["id"]
    await conn.execute(
        """
        INSERT INTO posts (id, subreddit, title, body, author, created_utc, score, url, num_comments)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (id) DO UPDATE SET
            title = EXCLUDED.title,
            body  = EXCLUDED.body
        """,
        post_id,
        SAMPLE_POST["subreddit"],
        SAMPLE_POST["title"],
        SAMPLE_POST["body"],
        SAMPLE_POST["author"],
        SAMPLE_POST["created_utc"],
        SAMPLE_POST["score"],
        SAMPLE_POST["url"],
        SAMPLE_POST["num_comments"],
    )
    for c in SAMPLE_COMMENTS:
        await conn.execute(
            """
            INSERT INTO comments (id, post_id, parent_id, parent_type, author, body, created_utc, score, controversiality)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (id) DO UPDATE SET body = EXCLUDED.body
            """,
            c["id"],
            c["post_id"],
            c["parent_id"],
            c["parent_type"],
            c["author"],
            c["body"],
            c["created_utc"],
            c["score"],
            c["controversiality"],
        )
    # Set reconstructed_text so we have a single blob to embed (same as ingest)
    reconstructed = _build_reconstructed_text(
        SAMPLE_POST["title"],
        SAMPLE_POST["body"],
        [c["body"] for c in SAMPLE_COMMENTS],
    )
    await conn.execute(
        "UPDATE posts SET reconstructed_text = $1 WHERE id = $2",
        reconstructed,
        post_id,
    )
    return post_id


async def fetch_post_and_comments(conn: asyncpg.Connection, post_id: str) -> tuple[dict, list[dict]] | None:
    """Return (post row, list of comment rows) or None if post not found."""
    post = await conn.fetchrow("SELECT * FROM posts WHERE id = $1", post_id)
    if post is None:
        return None
    comments = await conn.fetch(
        "SELECT * FROM comments WHERE post_id = $1 ORDER BY score DESC NULLS LAST",
        post_id,
    )
    return dict(post), [dict(c) for c in comments]


async def embed_and_store(
    conn: asyncpg.Connection,
    post_id: str,
    post_text: str,
    comments: list[dict],
) -> None:
    """Embed post and each comment; write to posts and comment_embeddings."""
    print("Embedding post text...")
    post_vec = await embed_text(post_text)
    vec_str = _vec_to_str(post_vec)
    await conn.execute(
        "UPDATE posts SET embedding = $1::vector, embedded_at = NOW() WHERE id = $2",
        vec_str,
        post_id,
    )
    print("  Post embedding stored.")

    if not comments:
        return
    print(f"Embedding {len(comments)} comments...")
    for i, c in enumerate(comments):
        body = (c.get("body") or "").strip()
        if not body:
            continue
        vec = await embed_text(body)
        vec_str = _vec_to_str(vec)
        await conn.execute(
            """
            INSERT INTO comment_embeddings (comment_id, embedding)
            VALUES ($1, $2::vector)
            ON CONFLICT (comment_id) DO UPDATE SET embedding = EXCLUDED.embedding, embedded_at = NOW()
            """,
            c["id"],
            vec_str,
        )
        print(f"  Comment {i+1}/{len(comments)} stored.")
    print("Comment embeddings stored.")


async def run_similarity_tests(conn: asyncpg.Connection, post_id: str) -> None:
    """Run a few query embeddings and show similarity scores (post-level and comment-level)."""
    test_queries = [
        "client won't pay invoice late payment",
        "small claims court get paid",
        "timesheet tracking hours",
    ]
    print("\n--- Similarity tests (how well do queries match this post/comments?) ---\n")

    for q in test_queries:
        print(f"Query: \"{q}\"")
        query_vec = await embed_text(q)
        vec_str = _vec_to_str(query_vec)

        # Post-level: similarity of query to our post
        row = await conn.fetchrow(
            """
            SELECT id, title, 1 - (embedding <=> $1::vector) AS similarity
            FROM posts WHERE id = $2 AND embedding IS NOT NULL
            """,
            vec_str,
            post_id,
        )
        if row:
            print(f"  Post similarity: {row['similarity']:.4f} — {row['title'][:60]}...")
        else:
            print("  Post: no embedding")

        # Comment-level: top matching comment from this thread
        rows = await conn.fetch(
            """
            SELECT c.id, LEFT(c.body, 80) AS snippet, 1 - (e.embedding <=> $1::vector) AS similarity
            FROM comment_embeddings e
            JOIN comments c ON c.id = e.comment_id
            WHERE c.post_id = $2
            ORDER BY e.embedding <=> $1::vector
            LIMIT 1
            """,
            vec_str,
            post_id,
        )
        if rows:
            r = rows[0]
            print(f"  Best comment: {r['similarity']:.4f} — \"{r['snippet']}...\"")
        else:
            print("  No comment embeddings")
        print()

    # Sanity: embedding the post's title and comparing to post embedding should be high
    print("--- Sanity: post embedding vs same post's title ---")
    title_row = await conn.fetchrow("SELECT title FROM posts WHERE id = $1", post_id)
    if title_row and title_row["title"]:
        title_vec = await embed_text(title_row["title"])
        title_vec_str = _vec_to_str(title_vec)
        row = await conn.fetchrow(
            "SELECT 1 - (embedding <=> $1::vector) AS sim FROM posts WHERE id = $2",
            title_vec_str,
            post_id,
        )
        if row:
            print(f"  Post vs its own title: {row['sim']:.4f} (expect high, e.g. > 0.8)")
    print()


async def main_async(
    post_id_arg: str | None,
    posts_path: Path | None,
    comments_path: Path | None,
    ingest_limit: int,
) -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set.", file=sys.stderr)
        sys.exit(1)
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    conn = await asyncpg.connect(database_url)

    try:
        if posts_path is not None and comments_path is not None:
            if not posts_path.exists():
                print(f"ERROR: File not found: {posts_path}", file=sys.stderr)
                sys.exit(1)
            if not comments_path.exists():
                print(f"ERROR: File not found: {comments_path}", file=sys.stderr)
                sys.exit(1)
            print(f"Loading from {posts_path.name} / {comments_path.name} (limit: {ingest_limit} posts)...")
            await load_from_zst(
                conn,
                posts_path,
                comments_path,
                posts_limit=ingest_limit,
                comments_limit=ingest_limit * 20,
            )
            post_id = await pick_post_with_comments(conn)
            if post_id is None:
                print("ERROR: No post with comments found after load. Try a higher --ingest-limit.", file=sys.stderr)
                sys.exit(1)
            pair = await fetch_post_and_comments(conn, post_id)
            assert pair is not None
            post_row, comments = pair
            post_text = post_row.get("reconstructed_text") or _build_reconstructed_text(
                post_row["title"],
                post_row.get("body"),
                [c.get("body") or "" for c in comments],
            )
            print(f"Selected post: {post_id} ({len(comments)} comments)")
            print(f"Title: {post_row['title'][:70]}...")
        elif post_id_arg:
            pair = await fetch_post_and_comments(conn, post_id_arg)
            if pair is None:
                print(f"Post {post_id_arg} not found.", file=sys.stderr)
                sys.exit(1)
            post_row, comments = pair
            post_id = post_row["id"]
            post_text = post_row.get("reconstructed_text")
            if not post_text:
                post_text = _build_reconstructed_text(
                    post_row["title"],
                    post_row.get("body"),
                    [c.get("body") or "" for c in comments],
                )
            print(f"Using existing post: {post_id} ({len(comments)} comments)")
        else:
            post_id = await ensure_sample_post_and_comments(conn)
            post_row, comments = await fetch_post_and_comments(conn, post_id)
            assert post_row is not None
            post_text = post_row["reconstructed_text"] or _build_reconstructed_text(
                post_row["title"],
                post_row.get("body"),
                [c.get("body") or "" for c in comments],
            )
            print(f"Using sample post: {post_id} ({len(comments)} comments)")
            print(f"Reconstructed length: {len(post_text)} chars")

        await embed_and_store(conn, post_id, post_text, comments)
        await run_similarity_tests(conn, post_id)
        print("Done. Check similarity scores above to judge embedding quality.")
    finally:
        await conn.close()


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Test embedding on one post + comments and run similarity checks.")
    parser.add_argument("--post-id", default=None, help="Use this post from DB instead of sample data.")
    parser.add_argument(
        "--zst-dir",
        type=Path,
        default=None,
        help="Folder containing *_submissions.zst and *_comments.zst (one pair).",
    )
    parser.add_argument("--posts", type=Path, default=None, help="Reddit submissions JSONL or .zst file.")
    parser.add_argument("--comments", type=Path, default=None, help="Reddit comments JSONL or .zst file.")
    parser.add_argument(
        "--ingest-limit",
        type=int,
        default=200,
        metavar="N",
        help="Max posts (and ~20x comments) to load from .zst (default 200).",
    )
    args = parser.parse_args()

    posts_path = args.posts
    comments_path = args.comments
    if args.zst_dir is not None:
        if posts_path is not None or comments_path is not None:
            parser.error("Use either --zst-dir or --posts/--comments, not both.")
        if not args.zst_dir.is_dir():
            parser.error(f"Not a directory: {args.zst_dir}")
        pair = _find_zst_pair(args.zst_dir)
        if pair is None:
            parser.error(
                f"No *_submissions.zst / *_comments.zst pair found in {args.zst_dir}"
            )
        posts_path, comments_path = pair
    elif (posts_path is None) != (comments_path is None):
        parser.error("--posts and --comments must be given together.")

    asyncio.run(main_async(
        post_id_arg=args.post_id,
        posts_path=posts_path,
        comments_path=comments_path,
        ingest_limit=args.ingest_limit,
    ))


if __name__ == "__main__":
    main()
