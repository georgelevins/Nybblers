#!/usr/bin/env python3
"""
Test script: run a semantic search against the database and print results.

Purpose: Search by PROBLEM — how people actually describe the pain (e.g. "invoices
get paid late", "can't stick to a routine"). You find where real people are talking
about that problem; then you brainstorm solution ideas (even silly ones first).

Usage:
  cd backend && source venv/bin/activate
  python search_test.py "never have time to exercise"
  python search_test.py "forget to track hours then guess at end of week" --limit 5
  python search_test.py "client keeps adding small requests" --subreddit microsaas

  # Count how many people (posts) in the dataset match this problem (for "demand size")
  python search_test.py "need ideas for a micro saas" --count
  python search_test.py "no time for side project" --count --min-similarity 0.6

Requires: DATABASE_URL and OPENAI_API_KEY in backend/.env
"""

import asyncio
import os
import sys
from pathlib import Path

# Backend root for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

import asyncpg
from dotenv import load_dotenv

load_dotenv()

from openai_utils import embed_text


def _vec_to_str(vec: list[float]) -> str:
    return "[" + ",".join(str(x) for x in vec) + "]"


def _reddit_post_url(post_id: str, subreddit: str) -> str:
    sub = (subreddit or "reddit").strip().lstrip("/")
    return f"https://reddit.com/r/{sub}/comments/{post_id}"


async def run_count(
    query: str,
    subreddit: str | None,
    min_similarity: float,
) -> None:
    """Count how many posts (and distinct authors) in the dataset match this problem."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set (check backend/.env)", file=sys.stderr)
        sys.exit(1)
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    print(f"Problem: \"{query}\"")
    if subreddit:
        print(f"Subreddit filter: {subreddit}")
    print(f"Min similarity (threshold): {min_similarity}\n")

    print("Embedding query...")
    query_vec = await embed_text(query)
    vec_str = _vec_to_str(query_vec)

    conn = await asyncpg.connect(database_url)
    try:
        row = await conn.fetchrow(
            """
            SELECT
                COUNT(*) AS matching_posts,
                COUNT(DISTINCT author) FILTER (WHERE author IS NOT NULL AND author != '') AS distinct_authors,
                COALESCE(SUM(num_comments), 0)::bigint AS total_comments_on_matching
            FROM posts
            WHERE embedding IS NOT NULL
              AND ($2::text IS NULL OR subreddit = $2)
              AND (1 - (embedding <=> $1::vector)) >= $3
            """,
            vec_str,
            subreddit,
            min_similarity,
        )
    finally:
        await conn.close()

    print("--- Demand in dataset ---")
    print(f"  Matching threads (posts):  {row['matching_posts']:,}")
    print(f"  Distinct authors (people): {row['distinct_authors']:,}")
    print(f"  Total comments on those:   {row['total_comments_on_matching']:,}")
    print()
    print("(Each matching post = someone raised this problem; distinct_authors avoids double-counting.)")


async def run_search(query: str, subreddit: str | None, limit: int) -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set (check backend/.env)", file=sys.stderr)
        sys.exit(1)
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    print(f"Query: \"{query}\"")
    if subreddit:
        print(f"Subreddit filter: {subreddit}")
    print(f"Limit: {limit}\n")

    print("Embedding query...")
    query_vec = await embed_text(query)
    vec_str = _vec_to_str(query_vec)

    conn = await asyncpg.connect(database_url)
    try:
        rows = await conn.fetch(
            """
            SELECT
                id,
                subreddit,
                title,
                author,
                created_utc,
                COALESCE(num_comments, 0)       AS num_comments,
                COALESCE(recent_comment_count, 0) AS recent_comment_count,
                COALESCE(activity_ratio, 0)     AS activity_ratio,
                last_comment_utc,
                1 - (embedding <=> $1::vector)  AS similarity_score,
                LEFT(reconstructed_text, 400)   AS snippet
            FROM posts
            WHERE embedding IS NOT NULL
              AND ($2::text IS NULL OR subreddit = $2)
            ORDER BY embedding <=> $1::vector
            LIMIT $3
            """,
            vec_str,
            subreddit,
            limit,
        )
    finally:
        await conn.close()

    if not rows:
        print("No results (no embedded posts in DB, or no matches).")
        print("Run: python embed.py  to embed posts first.")
        return

    print(f"Found {len(rows)} result(s):\n")
    for i, r in enumerate(rows, 1):
        link = _reddit_post_url(r["id"], r["subreddit"])
        print(f"--- {i}. {r['title'][:70]}...")
        print(f"    {link}")
        author_str = f"  u/{r['author']}" if r.get("author") else ""
        print(f"    r/{r['subreddit']}{author_str}  similarity={r['similarity_score']:.4f}")
        print(f"    comments: {r['num_comments']} total, {r.get('recent_comment_count') or 0} in last 90 days (still active?)")
        print(f"    snippet: {(r['snippet'] or '')[:200]}...")
        print()


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Test semantic search against the DB.")
    parser.add_argument(
        "query",
        nargs="?",
        default="I don't have time to work on my side project",
        help="Problem to search for — how people describe the pain (default: time/side project)",
    )
    parser.add_argument("--subreddit", default=None, help="Filter by subreddit (e.g. microsaas)")
    parser.add_argument("--limit", type=int, default=10, help="Max results (default 10)")
    parser.add_argument(
        "--count",
        action="store_true",
        help="Count how many posts/people in the dataset match this problem (demand size).",
    )
    parser.add_argument(
        "--min-similarity",
        type=float,
        default=0.5,
        metavar="0.0-1.0",
        help="For --count: only count posts with similarity >= this (default 0.5).",
    )
    args = parser.parse_args()

    if args.count:
        asyncio.run(run_count(args.query, args.subreddit, args.min_similarity))
    else:
        asyncio.run(run_search(args.query, args.subreddit, args.limit))


if __name__ == "__main__":
    main()
