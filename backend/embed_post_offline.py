"""
Embed a single post and its comment thread from .zst files — no database.

Use this to test embedding quality before running the full pipeline or writing to DB.

Usage:
  # Pick a post id from your dump, then:
  python embed_post_offline.py --post-id <REDDIT_POST_ID> --zst-dir /path/to/zst

  # Or point at the two files directly
  python embed_post_offline.py --post-id abc123 --posts sub.zst --comments com.zst

  # Optional: run custom similarity queries (default runs a few built-in ones)
  python embed_post_offline.py --post-id abc123 --zst-dir ./zst --query "your search phrase"

  # List first N post IDs, or N most recent; use --with-comments to only show posts that have comments
  python embed_post_offline.py --zst-dir ./zst --list-posts 10
  python embed_post_offline.py --zst-dir ./zst --list-posts 10 --recent
  python embed_post_offline.py --zst-dir ./zst --list-posts 10 --recent --with-comments

Requires: OPENAI_API_KEY only (no DATABASE_URL).
Expects Reddit JSONL format: id, subreddit, title, selftext, link_id, body, etc.
"""

import asyncio
import heapq
import json
import os
import sys
from pathlib import Path

# Backend root for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv()

from openai_utils import embed_text

try:
    from ingest import open_jsonl
except ImportError:
    open_jsonl = None

TOP_COMMENTS_FOR_RECONSTRUCT = 10
DELETED = {"[deleted]", "[removed]"}


def _clean(text: str | None) -> str | None:
    if text is None:
        return None
    return None if text.strip() in DELETED else text


def _build_reconstructed_text(title: str, body: str | None, comment_bodies: list[str]) -> str:
    parts = [f"[TITLE]\n{title}"]
    if body:
        parts.append(f"[BODY]\n{body}")
    top = comment_bodies[:TOP_COMMENTS_FOR_RECONSTRUCT]
    if top:
        parts.append("[TOP COMMENTS]\n" + "\n\n".join(c for c in top if c))
    return "\n\n".join(parts)


def _cosine_sim(a: list[float], b: list[float]) -> float:
    """Cosine similarity (OpenAI embeddings are normalized, so dot product = cos sim)."""
    return sum(x * y for x, y in zip(a, b))


def _reddit_post_url(post_id: str, subreddit: str) -> str:
    """Build the Reddit URL for a post (view in browser)."""
    sub = (subreddit or "reddit").strip().lstrip("/")
    return f"https://reddit.com/r/{sub}/comments/{post_id}"




def _find_zst_pair(directory: Path) -> tuple[Path, Path] | None:
    submissions = {p.name.replace("_submissions.zst", ""): p for p in directory.glob("*_submissions.zst")}
    comments = {p.name.replace("_comments.zst", ""): p for p in directory.glob("*_comments.zst")}
    matched = sorted(set(submissions) & set(comments))
    if not matched:
        return None
    name = matched[0]
    return (submissions[name], comments[name])


def find_post_in_submissions(submissions_path: Path, post_id: str) -> dict | None:
    """Stream submissions file until we find the post with this id. Return raw dict or None."""
    for line in open_jsonl(submissions_path):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if obj.get("id") == post_id:
            return obj
    return None


def list_post_ids(submissions_path: Path, limit: int) -> list[tuple[str, str]]:
    """Return [(id, title), ...] for the first `limit` posts (no OPENAI needed)."""
    if open_jsonl is None:
        return []
    out = []
    for line in open_jsonl(submissions_path):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        pid = obj.get("id")
        if not pid:
            continue
        title = (obj.get("title") or "")[:60]
        out.append((pid, title))
        if len(out) >= limit:
            break
    return out


def list_recent_post_ids(submissions_path: Path, limit: int) -> list[tuple[str, str]]:
    """Return [(id, title), ...] for the `limit` most recent posts by created_utc (newest first)."""
    if open_jsonl is None:
        return []
    # Min-heap of (created_utc, id, title) — keep only the N largest timestamps
    heap: list[tuple[int, str, str]] = []
    for line in open_jsonl(submissions_path):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        pid = obj.get("id")
        if not pid:
            continue
        try:
            ts = int(obj.get("created_utc") or 0)
        except (TypeError, ValueError):
            continue
        title = (obj.get("title") or "")[:60]
        if len(heap) < limit:
            heapq.heappush(heap, (ts, pid, title))
        elif ts > heap[0][0]:
            heapq.heapreplace(heap, (ts, pid, title))
    # Return newest first (descending by time)
    out = [(pid, title) for _, pid, title in sorted(heap, key=lambda x: -x[0])]
    return out


def _post_ids_with_comments(comments_path: Path) -> set[str]:
    """Return set of post_ids that have at least one comment in the comments file."""
    out: set[str] = set()
    for line in open_jsonl(comments_path):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        link_id = obj.get("link_id", "")
        pid = link_id[3:] if link_id.startswith("t3_") else link_id
        if pid:
            out.add(pid)
    return out


def list_recent_post_ids_with_comments(
    submissions_path: Path,
    comments_path: Path,
    limit: int,
) -> list[tuple[str, str]]:
    """Return [(id, title), ...] for the `limit` most recent posts that have at least one comment."""
    if open_jsonl is None:
        return []
    post_ids_with_comments = _post_ids_with_comments(comments_path)
    heap: list[tuple[int, str, str]] = []
    for line in open_jsonl(submissions_path):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        pid = obj.get("id")
        if not pid or pid not in post_ids_with_comments:
            continue
        try:
            ts = int(obj.get("created_utc") or 0)
        except (TypeError, ValueError):
            continue
        title = (obj.get("title") or "")[:60]
        if len(heap) < limit:
            heapq.heappush(heap, (ts, pid, title))
        elif ts > heap[0][0]:
            heapq.heapreplace(heap, (ts, pid, title))
    out = [(pid, title) for _, pid, title in sorted(heap, key=lambda x: -x[0])]
    return out


def find_comments_for_post(comments_path: Path, post_id: str) -> list[dict]:
    """Stream comments file; return all comments whose link_id is t3_<post_id> or post_id, sorted by score desc."""
    comments = []
    for line in open_jsonl(comments_path):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        link_id = obj.get("link_id", "")
        pid = link_id[3:] if link_id.startswith("t3_") else link_id
        if pid != post_id:
            continue
        body = _clean(obj.get("body"))
        if body is None:
            continue
        comments.append({
            "id": obj.get("id"),
            "body": body,
            "score": obj.get("score") or 0,
            "author": obj.get("author"),
        })
    comments.sort(key=lambda c: c["score"], reverse=True)
    return comments


async def run_offline(
    post_id: str,
    submissions_path: Path,
    comments_path: Path,
    extra_queries: list[str],
) -> None:
    if open_jsonl is None:
        print("ERROR: ingest module not available (need open_jsonl). Run from backend/.", file=sys.stderr)
        sys.exit(1)
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    print(f"Looking for post id = {post_id} in {submissions_path.name}...")
    post = find_post_in_submissions(submissions_path, post_id)
    if post is None:
        print(f"Post {post_id} not found in submissions file.", file=sys.stderr)
        sys.exit(1)

    title = post.get("title") or ""
    body = _clean(post.get("selftext"))
    subreddit = post.get("subreddit") or ""
    post_url = _reddit_post_url(post_id, subreddit)
    print(f"  Title: {title[:80]}...")
    print(f"  Link:  {post_url}")
    print(f"  Body length: {len(body or '')} chars")

    print(f"Loading comments for this post from {comments_path.name}...")
    comments = find_comments_for_post(comments_path, post_id)
    print(f"  Found {len(comments)} comments")

    comment_bodies = [c["body"] for c in comments]
    reconstructed = _build_reconstructed_text(title, body, comment_bodies)
    print(f"  Reconstructed thread length: {len(reconstructed)} chars\n")

    # Embed post (full thread)
    print("Embedding post (full thread)...")
    post_vec = await embed_text(reconstructed)
    print("  Done.")

    # Embed each comment
    comment_vecs: list[tuple[dict, list[float]]] = []
    for i, c in enumerate(comments):
        vec = await embed_text(c["body"])
        comment_vecs.append((c, vec))
    print(f"Embedded {len(comment_vecs)} comments.\n")

    # Similarity tests
    test_queries = [
        "client won't pay invoice late payment",
        "small claims court get paid",
        "timesheet tracking hours",
    ]
    test_queries.extend(extra_queries)

    print("--- Similarity (query vs post thread) ---\n")
    for q in test_queries:
        query_vec = await embed_text(q)
        sim = _cosine_sim(query_vec, post_vec)
        print(f"  \"{q}\"  →  post: {sim:.4f}")

    if comment_vecs:
        print("\n--- Similarity (query vs best-matching comment in thread) ---\n")
        for q in test_queries:
            query_vec = await embed_text(q)
            best = max(comment_vecs, key=lambda cv: _cosine_sim(query_vec, cv[1]))
            sim = _cosine_sim(query_vec, best[1])
            snippet = (best[0]["body"] or "")[:70]
            print(f"  \"{q}\"  →  {sim:.4f}  \"{snippet}...\"")
    else:
        print("\n--- Similarity (query vs best-matching comment) ---\n  (no comments in thread, skipped)")

    print("\n--- Sanity: post vs its own title ---")
    title_vec = await embed_text(title)
    sim = _cosine_sim(title_vec, post_vec)
    print(f"  Post vs title: {sim:.4f} (expect high, e.g. > 0.7)\n")
    print("Done. No database writes; all embeddings were computed in memory.")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description="Embed one post + its comments from .zst files (no DB)."
    )
    parser.add_argument("--post-id", default=None, help="Reddit post ID to embed.")
    parser.add_argument(
        "--zst-dir",
        type=Path,
        default=None,
        help="Folder containing *_submissions.zst and *_comments.zst.",
    )
    parser.add_argument("--posts", type=Path, default=None, help="Submissions .zst or JSONL file.")
    parser.add_argument("--comments", type=Path, default=None, help="Comments .zst or JSONL file.")
    parser.add_argument(
        "--list-posts",
        type=int,
        metavar="N",
        default=None,
        help="Just list N post IDs and titles (no embedding). No OPENAI_API_KEY needed.",
    )
    parser.add_argument(
        "--recent",
        action="store_true",
        help="With --list-posts: show N most recent posts by created_utc (default: first N in file).",
    )
    parser.add_argument(
        "--with-comments",
        action="store_true",
        help="With --list-posts: only show posts that have at least one comment (needs comments file).",
    )
    parser.add_argument(
        "--query",
        action="append",
        default=[],
        dest="queries",
        help="Extra similarity query to run (can be repeated).",
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
            parser.error(f"No *_submissions.zst / *_comments.zst pair in {args.zst_dir}")
        posts_path, comments_path = pair
    elif posts_path is None or comments_path is None:
        if args.list_posts is not None:
            if posts_path is None:
                parser.error("For --list-posts provide --zst-dir or --posts.")
        else:
            parser.error("Provide --zst-dir or both --posts and --comments.")

    if posts_path is not None and not posts_path.exists():
        parser.error(f"File not found: {posts_path}")
    if comments_path is not None and not comments_path.exists():
        parser.error(f"File not found: {comments_path}")

    if args.list_posts is not None:
        if open_jsonl is None:
            print("ERROR: ingest module not available.", file=sys.stderr)
            sys.exit(1)
        if posts_path is None:
            parser.error("--list-posts needs --zst-dir or --posts (submissions file).")
        if args.with_comments:
            if comments_path is None:
                parser.error("--with-comments needs the comments file (use --zst-dir or --comments).")
            if args.recent:
                print(f"{args.list_posts} most recent posts that have comments ({posts_path.name}):\n")
                items = list_recent_post_ids_with_comments(posts_path, comments_path, args.list_posts)
            else:
                # First N in file that have comments
                post_ids_ok = _post_ids_with_comments(comments_path)
                items = []
                for line in open_jsonl(posts_path):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    pid = obj.get("id")
                    if not pid or pid not in post_ids_ok:
                        continue
                    title = (obj.get("title") or "")[:60]
                    items.append((pid, title))
                    if len(items) >= args.list_posts:
                        break
                print(f"First {args.list_posts} posts that have comments in {posts_path.name}:\n")
        elif args.recent:
            print(f"{args.list_posts} most recent post IDs in {posts_path.name}:\n")
            items = list_recent_post_ids(posts_path, args.list_posts)
        else:
            print(f"First {args.list_posts} post IDs in {posts_path.name}:\n")
            items = list_post_ids(posts_path, args.list_posts)
        for i, (pid, title) in enumerate(items, 1):
            print(f"  {i}. {pid}  {title}...")
        print("\nRun with:  python embed_post_offline.py --post-id <ID> --zst-dir ...")
        return

    if args.post_id is None:
        parser.error("--post-id is required (or use --list-posts to discover IDs).")

    asyncio.run(run_offline(
        post_id=args.post_id,
        submissions_path=posts_path,
        comments_path=comments_path,
        extra_queries=args.queries,
    ))


if __name__ == "__main__":
    main()
