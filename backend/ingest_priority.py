#!/usr/bin/env python3
"""
Priority-based overnight ingestion script — posts only.

Works through a tiered list of subreddits, streaming N posts at a time
(no full-file load), embedding via OpenAI, and saving progress to a JSON
state file so a crash or Ctrl-C is fully resumable.

Comments are intentionally skipped — posts (title + body) provide all the
semantic search signal needed.  Run a separate comments pass later if desired.

Usage
-----
  # Dry-run — no DB writes, no OpenAI calls:
  python3 ingest_priority.py --dry-run --posts-per-sub 10

  # Single pass (each subreddit gets one batch, then stop):
  python3 ingest_priority.py

  # Loop overnight (keeps going round after round until files are exhausted):
  python3 ingest_priority.py --loop

  # Bigger batches:
  python3 ingest_priority.py --loop --posts-per-sub 1000

  # Reset progress and start from scratch:
  python3 ingest_priority.py --reset

State file
----------
  backend/ingest_state.json  — written atomically after every subreddit.
  Delete it or use --reset to restart from the beginning.

Logs
----
  logs/ingest_priority.log  — combined log (appended across runs)
  logs/<subreddit>_r<N>.log — per-subreddit per-round detail log
"""

import argparse
import asyncio
import json
import logging
import signal
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# ─── Environment ──────────────────────────────────────────────────────────────

_here = Path(__file__).resolve().parent
load_dotenv(_here / ".env")
load_dotenv()

# ─── Paths ────────────────────────────────────────────────────────────────────

ZST_DIR    = _here.parent / "zst" / "reddit" / "subreddits25"
LOG_DIR    = _here.parent / "logs"
STATE_FILE = _here / "ingest_state.json"

LOG_DIR.mkdir(parents=True, exist_ok=True)

# ─── Logging ──────────────────────────────────────────────────────────────────

_fmt    = "%(asctime)s  %(levelname)-8s  %(message)s"
_datefmt = "%H:%M:%S"

logging.basicConfig(level=logging.INFO, format=_fmt, datefmt=_datefmt)
log = logging.getLogger("ingest_priority")
_file_handler = logging.FileHandler(LOG_DIR / "ingest_priority.log")
_file_handler.setFormatter(logging.Formatter(_fmt, datefmt=_datefmt))
log.addHandler(_file_handler)

# ─── Priority subreddit list ──────────────────────────────────────────────────
#
# Ordered by relevance — processed top-to-bottom each round.
# Add, remove, or reorder freely.

PRIORITY_SUBREDDITS: list[str] = [
    # Tier 1 — core startup / business (the only tier run overnight)
    "Entrepreneur",
    "SaaS",
    "startups",
    "smallbusiness",
    "indiehackers",
    "digitalnomad",
    "freelance",
    "freelanceWriters",
]

# ─── State helpers ────────────────────────────────────────────────────────────


def load_state() -> dict:
    """Load progress from disk. Returns defaults if file is missing."""
    if STATE_FILE.exists():
        try:
            s = json.loads(STATE_FILE.read_text())
            idx = s.get("subreddit_index", 0)
            sub = PRIORITY_SUBREDDITS[idx] if idx < len(PRIORITY_SUBREDDITS) else "done"
            log.info("Resuming: round=%d  next=%s (index %d)", s.get("round", 1), sub, idx)
            return s
        except (json.JSONDecodeError, KeyError):
            log.warning("State file corrupt — starting fresh.")
    return {"round": 1, "subreddit_index": 0, "offsets": {}}


def save_state(state: dict) -> None:
    """Atomically write state to disk (write-then-rename)."""
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(STATE_FILE)


# ─── Per-subreddit ingestion ──────────────────────────────────────────────────


async def ingest_subreddit(
    sub: str,
    pool,
    posts_per_sub: int,
    offset: int,
    round_num: int,
    dry_run: bool,
) -> int:
    """
    Stream the next `posts_per_sub` valid posts from the submissions ZST file,
    starting at `offset` (count of valid records already processed).

    Inserts them into the DB, then embeds any unembedded posts via OpenAI.
    Returns the new offset.  Returns the same offset if the file is exhausted.
    """
    from ingest import (  # noqa: PLC0415
        EMBED_BATCH_SIZE,
        EMBED_CONCURRENCY,
        DB_INSERT_BATCH,
        _check_embedding_backend,
        embed_posts,
        extract_post,
        insert_posts,
        iter_zst,
    )

    submissions_file = ZST_DIR / f"{sub}_submissions.zst"

    if not submissions_file.exists():
        log.warning("r/%s — %s not found, skipping.", sub, submissions_file.name)
        return offset

    # Per-subreddit detail log
    sub_log = LOG_DIR / f"{sub}_r{round_num}.log"
    sub_handler = logging.FileHandler(sub_log, mode="a")
    sub_handler.setFormatter(logging.Formatter(_fmt, datefmt=_datefmt))
    sub_logger = logging.getLogger(f"ingest.{sub}")
    sub_logger.handlers.clear()
    sub_logger.addHandler(sub_handler)
    sub_logger.setLevel(logging.INFO)

    t0 = time.monotonic()
    log.info("── r/%s  round=%d  offset=%d ──", sub, round_num, offset)

    # Stream: skip `offset` valid records, collect the next `posts_per_sub`
    posts: list[dict] = []
    seen = 0
    for obj in iter_zst(str(submissions_file)):
        p = extract_post(obj)
        if p is None:
            continue
        if seen < offset:
            seen += 1
            continue
        posts.append(p)
        seen += 1
        if len(posts) >= posts_per_sub:
            break

    if not posts:
        sub_logger.info("File exhausted at offset %d — nothing new.", offset)
        log.info("r/%s — exhausted at offset %d, skipping.", sub, offset)
        sub_handler.close()
        return offset  # unchanged — signals caller to skip next round too

    new_offset = offset + len(posts)
    sub_logger.info("Got %d posts (offset %d → %d).", len(posts), offset, new_offset)

    # Insert in chunks to keep memory flat
    inserted = 0
    for i in range(0, len(posts), DB_INSERT_BATCH):
        inserted += await insert_posts(pool, posts[i : i + DB_INSERT_BATCH], dry_run)
    sub_logger.info("Inserted: %d posts.", inserted)

    # Embed any unembedded posts.
    # Concurrency=1 keeps us well under the 1M TPM rate limit.
    _check_embedding_backend()
    await embed_posts(pool, EMBED_BATCH_SIZE, 1, dry_run)

    elapsed = time.monotonic() - t0
    log.info("r/%s done in %.0fs — inserted=%d  new_offset=%d", sub, elapsed, inserted, new_offset)

    sub_handler.close()
    return new_offset


# ─── Main loop ────────────────────────────────────────────────────────────────


async def run(args: argparse.Namespace) -> None:
    from ingest import connect_db, ensure_schema  # noqa: PLC0415

    pool = await connect_db()
    async with pool.acquire() as conn:
        await ensure_schema(conn)

    state = load_state()

    _shutdown = asyncio.Event()

    def _handle_signal(sig, frame):  # noqa: ANN001
        log.info("Signal %s — finishing current subreddit then stopping.", sig)
        _shutdown.set()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    total_processed = 0

    try:
        while True:
            round_num = state["round"]
            start_idx = state["subreddit_index"]
            offsets: dict[str, int] = state.get("offsets", {})

            log.info("═══ Round %d — starting at index %d / %d ═══",
                     round_num, start_idx, len(PRIORITY_SUBREDDITS))

            made_progress = False

            for idx in range(start_idx, len(PRIORITY_SUBREDDITS)):
                if _shutdown.is_set():
                    log.info("Shutdown — saving state.")
                    state["subreddit_index"] = idx
                    save_state(state)
                    return

                sub = PRIORITY_SUBREDDITS[idx]
                prev_offset = offsets.get(sub, 0)

                try:
                    new_offset = await ingest_subreddit(
                        sub=sub,
                        pool=pool,
                        posts_per_sub=args.posts_per_sub,
                        offset=prev_offset,
                        round_num=round_num,
                        dry_run=args.dry_run,
                    )
                except Exception as exc:
                    log.error("r/%s FAILED: %s — will retry next run.", sub, exc, exc_info=True)
                    # Save state pointing AT this subreddit so the next run retries it
                    state["subreddit_index"] = idx
                    save_state(state)
                    new_offset = prev_offset
                    continue

                if new_offset > prev_offset:
                    made_progress = True
                    total_processed += 1

                offsets[sub] = new_offset
                state["offsets"] = offsets
                state["subreddit_index"] = idx + 1
                save_state(state)


            log.info("═══ Round %d complete (%d subreddits advanced this session) ═══",
                     round_num, total_processed)

            if not args.loop:
                log.info("Single-pass mode — done.")
                break

            if not made_progress:
                log.info("All files exhausted — stopping.")
                break

            state["round"] = round_num + 1
            state["subreddit_index"] = 0
            save_state(state)

    finally:
        await pool.close()
        log.info("Session finished. Total subreddit-batches processed: %d", total_processed)


# ─── Entry point ─────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Priority overnight ingestion — posts only, fully resumable.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--posts-per-sub", type=int, default=500, metavar="N",
        help="Posts to stream per subreddit per round (default: 500)",
    )
    p.add_argument(
        "--loop", action="store_true",
        help="Keep looping round after round until all files are exhausted",
    )
    p.add_argument(
        "--dry-run", action="store_true",
        help="Parse and log but do not write to DB or call OpenAI",
    )
    p.add_argument(
        "--reset", action="store_true",
        help="Delete the state file and start from scratch",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.reset:
        if STATE_FILE.exists():
            STATE_FILE.unlink()
            log.info("State file deleted — starting fresh.")

    if args.dry_run:
        log.info("DRY RUN — no DB writes or OpenAI calls.")

    log.info("Nybblers overnight ingestion — %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    log.info("ZST_DIR        : %s", ZST_DIR)
    log.info("State file     : %s", STATE_FILE)
    log.info("Posts/sub/round: %d", args.posts_per_sub)
    log.info("Loop mode      : %s", args.loop)
    log.info("Subreddits     : %d", len(PRIORITY_SUBREDDITS))

    asyncio.run(run(args))
