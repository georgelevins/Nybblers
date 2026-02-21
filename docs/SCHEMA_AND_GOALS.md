# Schema vs. product goals

Goals:

1. **Chart interest over time** — How much discussion of this problem per month/year?
2. **Surface people who want the solution** — Who (authors) are talking about the problem so we can reach them?
3. **Highlight Reddit threads** that talk about the problem — Link to threads, show snippet.
4. **See if threads are still active** — How many new comments recently? Still getting engagement years later?

---

## What the schema already supports

| Goal | Status | Where it lives |
|------|--------|----------------|
| **Highlight threads** | ✅ Done | Search returns post id, title, subreddit, snippet; you build `reddit.com/r/{sub}/comments/{id}`. `posts.url` also exists. |
| **Still active?** | ✅ Done | `posts.last_comment_utc`, `posts.recent_comment_count` (comments in last **90 days**), `posts.activity_ratio` (heat: recent comments × ln(1 + age)). Search/API can sort by `activity_ratio` or show “X comments in last 90 days”. |
| **Surface people** | ✅ Data there, not in search response yet | `posts.author` (and `comments.author`) exist. To “surface people” you need author in search results and/or a “matching authors” list. |
| **Interest over time** | ✅ Data there, no chart query yet | `posts.created_utc` exists. To chart: take matching posts (by embedding similarity), then `GROUP BY date_trunc('month', created_utc)` and count. Requires an endpoint or script that runs the embedding + time bucketing. |

So the **database schema is set up** for all of this. What’s missing is mostly **queries and API/UI**: expose author, expose recent_comment_count, and add a “time series” query (counts per month for a problem).

---

## Limitations and details

### 1. “Recent” is fixed at 90 days

- `recent_comment_count` = comments in the **last 90 days** (set in ingest, `RECENT_DAYS = 90`).
- So “still active” is “active in the last 90 days”. For “last 30 days” or “last year” you’d either:
  - Add more columns (e.g. `recent_comment_count_30d`), or
  - Compute on the fly from `comments` (e.g. `COUNT(*) WHERE created_utc > NOW() - interval '30 days'` per post). Slower but flexible.

### 2. Activity ratio

- Formula: `recent_comment_count * ln(1 + age_in_days)`.
- So an old thread with lots of recent comments gets a high score; a new thread with few comments stays lower. Good for “still active over the years”.

### 3. Charting interest over time

- You need “matching” posts for a given problem (embedding similarity ≥ threshold), then bucket by `created_utc` (e.g. by month).
- Schema supports it: `posts.created_utc` is there. You need an endpoint or script that:
  - Embeds the problem query,
  - Selects posts where `1 - (embedding <=> $vec) >= threshold`,
  - Groups by `date_trunc('month', created_utc)` and counts (and optionally sums `num_comments` or distinct authors).
- No new tables required.

### 4. Surfacing “people who want the solution”

- **Post authors:** `posts.author` is in the DB. Add `author` to the search API response so the UI can show “u/username” and link to their profile.
- **Comment authors (more people):** Today we only embed **posts**. To surface “people who commented that they have this problem” you need **comment-level embeddings** (`comment_embeddings` table) and a query that returns matching comments + `comments.author`. Schema exists (migration 004); you need a batch job to fill it and an endpoint that searches comment_embeddings and returns author.

### 5. Reddit links and “still active” in UI

- Thread link: `https://reddit.com/r/{subreddit}/comments/{post_id}` (or use `posts.url` if you store the full URL).
- “Still active” in UI: show `last_comment_utc` (“Last activity: 2 weeks ago”) and `recent_comment_count` (“12 comments in last 90 days”). Both are in the schema; ensure they’re in the API response.

---

## Summary

| Need | Schema | What to add |
|------|--------|-------------|
| Chart interest over time | ✅ `created_utc` | Query/endpoint: embed problem → filter by similarity → GROUP BY month, COUNT. |
| Surface people (post authors) | ✅ `author` | Add `author` (and optionally `recent_comment_count`) to search result model and SQL. |
| Surface people (comment authors) | ✅ `comments.author`, `comment_embeddings` table | Back-fill comment embeddings; endpoint that searches comments by problem and returns author. |
| Highlight threads + “still active” | ✅ `last_comment_utc`, `recent_comment_count`, `activity_ratio` | Ensure search/API returns these; sort by `activity_ratio` for “still active first”. |
| Different “recent” windows (e.g. 30 days) | ⚠️ Only 90 days in schema | Either add columns for 30d/1y or compute from `comments` when needed. |

So: **the schema is set up.** The main gaps are (1) adding author (and recent_comment_count) to search results, (2) a time-series query/endpoint for charts, and (3) optional comment embeddings + endpoint if you want to surface commenters as “people who want the solution.”
