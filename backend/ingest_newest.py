#!/usr/bin/env python3
"""
Import the N newest posts from a subreddit ZST file + their comments, then embed.
Usage: python3 ingest_newest.py --n 100 --subreddit Entrepreneur
"""
import argparse, asyncio, json, logging, os, sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("ingest_newest")

ZST_DIR = Path(__file__).parent.parent / "zst" / "reddit" / "subreddits25"

# Reuse helpers from ingest.py
sys.path.insert(0, str(Path(__file__).parent))
from ingest import iter_zst, extract_post, extract_comment, connect_db, insert_posts, insert_comments, update_activity_stats, embed_posts, embed_comments, ensure_schema


async def main():
    p = argparse.ArgumentParser()
    p.add_argument("--subreddit", required=True)
    p.add_argument("--n", type=int, default=100, help="Number of newest posts to keep")
    p.add_argument("--mode", choices=["import", "embed", "all"], default="all")
    p.add_argument("--skip-comment-embeddings", action="store_true")
    args = p.parse_args()

    sub = args.subreddit
    submissions_file = ZST_DIR / f"{sub}_submissions.zst"
    comments_file    = ZST_DIR / f"{sub}_comments.zst"

    pool = await connect_db()

    async with pool.acquire() as conn:
        await ensure_schema(conn)

    if args.mode in ("import", "all"):
        # --- Posts: read all, sort by newest, take top N ---
        log.info("Reading all posts from %s...", submissions_file)
        all_posts = []
        for obj in iter_zst(str(submissions_file)):
            post = extract_post(obj)
            if post:
                all_posts.append(post)

        all_posts.sort(key=lambda p: p["created_utc"], reverse=True)
        newest = all_posts[:args.n]
        wanted_ids = {p["id"] for p in newest}

        log.info("Keeping %d newest posts (out of %d total)", len(newest), len(all_posts))
        await insert_posts(pool, newest, dry_run=False)
        log.info("Posts inserted.")

        # --- Comments: only those belonging to the kept posts ---
        log.info("Scanning comments for matching post IDs...")
        matching_comments = []
        for obj in iter_zst(str(comments_file)):
            c = extract_comment(obj)
            if c and c["post_id"] in wanted_ids:
                matching_comments.append(c)

        log.info("Found %d comments for those %d posts", len(matching_comments), len(newest))
        await insert_comments(pool, matching_comments, dry_run=False)
        log.info("Comments inserted.")

        await update_activity_stats(pool, dry_run=False)

    if args.mode in ("embed", "all"):
        from ingest import EMBED_BATCH_SIZE, EMBED_CONCURRENCY, _check_embedding_backend
        _check_embedding_backend()
        await embed_posts(pool, EMBED_BATCH_SIZE, EMBED_CONCURRENCY, dry_run=False)
        if not args.skip_comment_embeddings:
            await embed_comments(pool, EMBED_BATCH_SIZE, EMBED_CONCURRENCY, dry_run=False)

    await pool.close()
    log.info("Done.")


if __name__ == "__main__":
    asyncio.run(main())
