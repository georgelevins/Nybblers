# RedditDemand pipeline runbook

How to load a full subreddit into the database and run embeddings so you can test search and the app.

## 1. Schema (match your friend’s code)

Migrations live in `database/migrations/`. Apply them in order (e.g. in Supabase SQL Editor or `psql`):

| Migration | What it does |
|-----------|----------------|
| **001_setup.sql** | `vector` extension, `posts`, `comments`, `alerts`, B-tree indexes |
| **002_hnsw_indexes.sql** | HNSW indexes on `posts.embedding`, `alerts.query_embedding` — run **after** bulk load |
| **003_ingest_log.sql** | `ingest_log` table (ingest.py uses it to skip already-ingested files) |
| **004_comment_embeddings.sql** | `comment_embeddings` table (for per-comment / leads search) |
| **005_ingest_log_year.sql** | `ingest_log.year` — idempotency per (file, year) when using `--year` |

**Important:** Run **002** only after you’ve finished loading and embedding posts (or do it at the end). Creating HNSW on an empty table is fine; building it after bulk insert is faster than updating it on every row.

**Permissions:** The DB user in `DATABASE_URL` needs at least:

- `posts`, `comments`: SELECT, INSERT, UPDATE  
- `ingest_log`: SELECT, INSERT, UPDATE  
- `comment_embeddings`: SELECT, INSERT, UPDATE (if you use comment embedding)

Grant them in Supabase/Postgres if you see “permission denied”.

---

## 2. Pipeline order

```
.zst dumps (submissions + comments)
        ↓
   [1] ingest.py     → posts, comments, ingest_log; then stats + reconstructed_text
        ↓
   [2] embed.py           → posts.embedding, posts.embedded_at
        ↓
   [3] embed_comments.py  → comment_embeddings (for /search/leads)
        ↓
   [4] Migration 002       → HNSW indexes (if not already applied)
```

---

## 3. Step-by-step commands

From the repo root, with `backend/.env` containing `DATABASE_URL` and `OPENAI_API_KEY`.

### 3.1 Ingest one subreddit (full or limited)

**Full subreddit** (e.g. everything in `zst/`):

```bash
cd backend
source venv/bin/activate
python ingest.py --dir /Users/george/Documents/Projects/Nybblers/zst
```

**Single subreddit, explicit files:**

```bash
python ingest.py --posts /path/to/microsaas_submissions.zst --comments /path/to/microsaas_comments.zst
```

**Test run (first 2000 rows per file):**

```bash
python ingest.py --dir /Users/george/Documents/Projects/Nybblers/zst --limit 2000
```

**One calendar year only (e.g. 2024):**

```bash
python ingest.py --dir /path/to/zst --year 2024
```

Idempotency is per (file, year): the same file can be ingested again for a different year without changing the log.

**Dry run (count rows only, no DB writes):**

```bash
python ingest.py --dir /path/to/zst --dry-run
python ingest.py --dir /path/to/zst --year 2024 --limit 5000 --dry-run
```

Ingest will:

1. Insert posts (skips file if already in `ingest_log` as complete).
2. Insert comments.
3. Compute `last_comment_utc`, `recent_comment_count`.
4. Compute `activity_ratio`.
5. Build `reconstructed_text` (title + body + top comments) for each post.

### 3.2 Embed posts

Embeds all posts that have `reconstructed_text` but no `embedded_at`:

```bash
python embed.py
```

**Only one subreddit:**

```bash
python embed.py --subreddit microsaas
```

**Cap for testing:**

```bash
python embed.py --limit 1000
```

**Smaller batches (if you hit rate limits):**

```bash
python embed.py --batch-size 50
```

### 3.3 Comment embeddings (for leads search)

Run after ingest (and optionally after `embed.py`). Fills `comment_embeddings` so the **leads** endpoint can surface comment-level matches.

```bash
python embed_comments.py
```

**Only one subreddit:**

```bash
python embed_comments.py --subreddit microsaas
```

**Cap for testing:**

```bash
python embed_comments.py --limit 500
```

**Smaller batches (if you hit rate limits):**

```bash
python embed_comments.py --batch-size 50
```

You can skip this and still use **post-level** search and **demand count**; only **leads** (comment-level) requires comment embeddings.

### 3.4 HNSW indexes (if not already applied)

After bulk insert + embed, apply migration 002 if you haven’t already:

```sql
-- In Supabase SQL Editor or psql
\i database/migrations/002_hnsw_indexes.sql
```

(or run the contents of that file).

---

## 4. Rough time estimates

| Step | Depends on | Rough time (order of magnitude) |
|------|------------|----------------------------------|
| **Ingest** | Size of .zst (posts + comments) | ~1–5 min per 10k posts + their comments (I/O + batch inserts). 50k posts + 500k comments: ~10–30 min. |
| **Embed (posts)** | Number of posts, OpenAI rate limits | ~1–2 min per 1k posts at default batch size (100). 50k posts: ~1–2 hours if rate-limited; less if you have higher tier. |

So for a **full subreddit** (e.g. 20k–100k posts):

- Ingest: usually under an hour.
- Embed: from tens of minutes to a couple of hours depending on size and API limits.

Start with `--limit 2000` on ingest and `--limit 500` on embed to confirm everything works, then remove the limits for the full run.

---

## 5. API endpoints (search, demand, leads)

| Endpoint | Purpose |
|----------|---------|
| **POST /search** | Semantic search for threads (post-level). Body: `{ "query": "...", "subreddit": null, "limit": 20 }`. |
| **POST /search/demand** | Demand count: matching posts, distinct authors, total comments. Body: `{ "query": "...", "subreddit": null, "min_similarity": 0.5 }`. |
| **POST /search/leads** | Leads: comment-level matches (author + snippet + post link). Body: `{ "query": "...", "subreddit": null, "limit": 20, "min_similarity": 0.5 }`. Requires `embed_comments.py` to have run. |

---

## 6. Check that it worked

- **Ingest:** In DB, `SELECT COUNT(*) FROM posts;` and `FROM comments;`. Check `reconstructed_text IS NOT NULL` for some posts.
- **Embed (posts):** `SELECT COUNT(*) FROM posts WHERE embedded_at IS NOT NULL;` should grow after `embed.py`.
- **Embed (comments):** `SELECT COUNT(*) FROM comment_embeddings;` should grow after `embed_comments.py`.
- **Search:** Use POST /search with a query; you should get back posts by similarity. Use /search/demand for counts, /search/leads for comment-level leads.

---

## 7. Idempotency and re-runs

- **Ingest:** Uses `ingest_log` keyed by `(file_name, year)`. The same file won’t be re-ingested for the same year once marked complete. You can run the same file with a different `--year` to add another year. To re-run the same file+year, delete or update its row in `ingest_log`.
- **Embed (posts):** Only updates rows where `embedded_at IS NULL`; safe to re-run.
- **Embed (comments):** Upserts into `comment_embeddings`; safe to re-run (fills any new or missed comments).

---

## 8. Small test vs full run

**Small test (validate pipeline):**

```bash
python ingest.py --dir /path/to/zst --limit 2000
python embed.py --limit 500
python embed_comments.py --limit 500
```

Then hit POST /search, POST /search/demand, and POST /search/leads with a query.

**Full run (all subreddits in directory):**

```bash
python ingest.py --dir /path/to/zst
python embed.py
python embed_comments.py
```

Apply migration 002 (HNSW) after bulk load if you haven’t already. Use `ANALYZE` after large loads if needed.

Your friend’s code and this runbook are aligned to the schema in `database/migrations/`. Running ingest, embed, and embed_comments with the steps above is enough to use search, demand count, and leads.
