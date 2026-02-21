-- Migration 001: pgvector extension + base schema + B-tree indexes
-- Idempotent: safe to run multiple times.

CREATE EXTENSION IF NOT EXISTS vector;

-- ---------------------------------------------------------------------------
-- posts
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS posts (
  id                   TEXT PRIMARY KEY,
  subreddit            TEXT NOT NULL,
  title                TEXT NOT NULL,
  body                 TEXT,
  author               TEXT,
  created_utc          TIMESTAMPTZ NOT NULL,
  score                INTEGER,
  url                  TEXT,
  num_comments         INTEGER,
  -- Computed by ingest pipeline (step 3)
  last_comment_utc     TIMESTAMPTZ,
  recent_comment_count INTEGER,
  -- Computed by ingest pipeline (step 4)
  activity_ratio       FLOAT,
  -- Populated by embed.py
  embedding            vector(1536),
  embedded_at          TIMESTAMPTZ,
  -- Built by ingest pipeline (step 5), used as embedding input
  reconstructed_text   TEXT
);

-- ---------------------------------------------------------------------------
-- comments
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS comments (
  id               TEXT PRIMARY KEY,
  post_id          TEXT REFERENCES posts(id),
  parent_id        TEXT,      -- raw Reddit parent_id e.g. "t1_abc" or "t3_xyz"
  parent_type      TEXT,      -- "t1" (comment) or "t3" (post)
  author           TEXT,
  body             TEXT NOT NULL,
  created_utc      TIMESTAMPTZ NOT NULL,
  score            INTEGER,
  controversiality INTEGER
);

-- ---------------------------------------------------------------------------
-- alerts
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS alerts (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_email       TEXT NOT NULL,
  query            TEXT NOT NULL,
  query_embedding  vector(1536),
  created_at       TIMESTAMPTZ DEFAULT NOW(),
  last_notified_at TIMESTAMPTZ
);

-- ---------------------------------------------------------------------------
-- B-tree indexes (fast for filtering / sorting)
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS comments_post_id_idx
  ON comments (post_id);

CREATE INDEX IF NOT EXISTS posts_subreddit_idx
  ON posts (subreddit);

CREATE INDEX IF NOT EXISTS posts_created_utc_idx
  ON posts (created_utc);

CREATE INDEX IF NOT EXISTS posts_activity_ratio_idx
  ON posts (activity_ratio DESC NULLS LAST);

CREATE INDEX IF NOT EXISTS posts_embedded_at_idx
  ON posts (embedded_at)
  WHERE embedded_at IS NULL;   -- partial index: speeds up embed.py batch reads
