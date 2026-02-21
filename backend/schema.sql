-- RedditDemand database schema
-- Run once on a fresh database:
--   psql $DATABASE_URL -f schema.sql
--
-- For existing databases use migrate.sql instead (safe, idempotent).
--
-- Requires pgvector extension:
CREATE EXTENSION IF NOT EXISTS vector;

-- ── Core tables ───────────────────────────────────────────────────────────────

-- Vector dimension:
--   768  for local sentence-transformers (EMBEDDING_BACKEND=local, default)
--   1536 for OpenAI text-embedding-3-small (EMBEDDING_BACKEND=openai)
-- Pick one before first ingest and never change it without re-embedding everything.
CREATE TABLE IF NOT EXISTS posts (
  id                   TEXT PRIMARY KEY,
  subreddit            TEXT NOT NULL,
  title                TEXT NOT NULL,
  body                 TEXT,
  author               TEXT,
  created_utc          TIMESTAMP NOT NULL,
  score                INTEGER,
  url                  TEXT,
  num_comments         INTEGER,
  last_comment_utc     TIMESTAMP,
  recent_comment_count INTEGER,
  activity_ratio       FLOAT,
  embedding            vector(768),
  embedded_at          TIMESTAMP,
  reconstructed_text   TEXT
);

CREATE TABLE IF NOT EXISTS comments (
  id               TEXT PRIMARY KEY,
  post_id          TEXT REFERENCES posts(id) ON DELETE CASCADE,
  parent_id        TEXT,
  parent_type      TEXT,
  author           TEXT,
  body             TEXT NOT NULL,
  created_utc      TIMESTAMP NOT NULL,
  score            INTEGER,
  controversiality INTEGER
);

-- Embeddings for comments are stored in a separate table so the comments table
-- stays lean and we can embed incrementally without locking the main table.
CREATE TABLE IF NOT EXISTS comment_embeddings (
  comment_id  TEXT PRIMARY KEY REFERENCES comments(id) ON DELETE CASCADE,
  embedding   vector(768) NOT NULL,
  embedded_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS alerts (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_email       TEXT NOT NULL,
  query            TEXT NOT NULL,
  query_embedding  vector(768),
  created_at       TIMESTAMP DEFAULT NOW(),
  last_notified_at TIMESTAMP
);

-- ── Indexes ───────────────────────────────────────────────────────────────────

-- HNSW indexes for fast approximate nearest-neighbour search (pgvector >= 0.5).
-- Build these AFTER bulk data load for best performance.
-- m=16 and ef_construction=64 are solid defaults for up to a few million rows.
CREATE INDEX IF NOT EXISTS posts_embedding_hnsw
    ON posts USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS comment_embeddings_hnsw
    ON comment_embeddings USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Supporting indexes for common filter patterns
CREATE INDEX IF NOT EXISTS posts_subreddit_idx ON posts (subreddit);
CREATE INDEX IF NOT EXISTS posts_created_utc_idx ON posts (created_utc);
CREATE INDEX IF NOT EXISTS posts_activity_ratio_idx ON posts (activity_ratio DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS comments_post_id_idx ON comments (post_id);
CREATE INDEX IF NOT EXISTS comments_created_utc_idx ON comments (created_utc);
