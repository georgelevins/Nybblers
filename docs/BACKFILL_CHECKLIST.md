# Before you back-fill lots of Reddit data

End goal: **see how many people in total have had a given problem in our dataset.**

---

## 1. Demand count (how many people had this problem)

- **Posts:** Each matching post = one thread where the problem was raised. Count them with:
  ```bash
  python search_test.py "your problem phrase" --count
  ```
- **People (distinct authors):** Same script reports `distinct_authors` so one person posting 5 times counts once.
- **Threshold:** Use `--min-similarity 0.6` (or 0.5) so only clear matches count:
  ```bash
  python search_test.py "need ideas for a micro saas" --count --min-similarity 0.6
  ```

So before scaling: **decide your threshold** (e.g. 0.5 = broad, 0.65 = strict) and use `--count` to interpret “how many people” in the dataset.

---

## 2. What to improve or change before big back-fills

| Area | Recommendation |
|------|----------------|
| **Comment-level “people”** | Right now we only embed **posts**. To count “people who had this problem” at the **comment** level (each comment = one voice), you’d need to back-fill **comment embeddings** (table `comment_embeddings`) and add a count over comments. That’s a separate batch job; post-level count is already meaningful (each post = one thread about the problem). |
| **Similarity threshold** | Pick a single threshold (e.g. 0.5 or 0.6) for “this post matches the problem” and use it everywhere: in search, in counts, and in any future analytics. Document it in one place. |
| **Subreddit list** | Ingest one subreddit per pair of files; for “loads of Reddit” run ingest (then embed) per subreddit or use `--dir` with many pairs. Ensure `ingest_log` and `--limit` (for testing) behave as you expect. |
| **Embedding cost & time** | Each post = one embedding call. For 100k posts that’s 100k inputs (batched). Check OpenAI pricing and rate limits; run `embed.py` with `--limit` in chunks if needed. |
| **DB performance** | After huge bulk loads, run `ANALYZE posts;` (and `comments` if used). HNSW index (migration 002) is built once; creating it **after** bulk load is faster than before. |
| **Idempotency** | Ingest skips files already in `ingest_log` as complete. To re-run a file you must fix or remove that row. Embed only updates rows where `embedded_at IS NULL`, so safe to re-run. |
| **Author = “people”** | We use `author` for distinct-authors count. Deleted/removed posts often have `author = NULL` or `[deleted]`; the count script already filters those so “distinct authors” is a lower bound of real people. |

---

## 3. Suggested order for a big back-fill

1. **Apply migrations** (001, 003; 002 after bulk embed; 004 if you add comment embeddings later).
2. **Run ingest** per subreddit (or `--dir` with all pairs). Use `--limit` on a small subset first to confirm schema and permissions.
3. **Run embed** (all at once or in chunks with `--limit` / `--subreddit`). Then apply migration 002 if not already.
4. **Use `--count`** with a few problem phrases and your chosen `--min-similarity` to validate “how many people had this problem” in the dataset.

---

## 4. One-line summary

**Before back-filling:** decide your similarity threshold, use `search_test.py --count` for “how many people in the dataset had this problem,” and add comment embeddings only if you need per-comment (per-person) demand counts.
