-- migrate.sql — safe, idempotent migrations for an existing Nybblers database.
-- Run this against your live database to bring it up to the current schema
-- without losing any data.
--
--   psql $DATABASE_URL -f migrate.sql
--
-- All statements use IF NOT EXISTS / IF EXISTS so the file can be re-run safely.
--
-- ── Vector dimension note ─────────────────────────────────────────────────────
-- The default embedding backend is now local (sentence-transformers, 768 dims).
-- If your DB already has vector(1536) columns from OpenAI embeddings you have
-- two options:
--
--   A) Keep using OpenAI: set EMBEDDING_BACKEND=openai in .env, skip the
--      ALTER TABLE statements in the "dimension migration" section below.
--
--   B) Switch to local (free): drop the existing embedding columns, recreate
--      them at 768 dims, then re-run `python ingest.py --mode embed`.
--      The commented-out ALTER TABLE statements below do this for you.
-- ─────────────────────────────────────────────────────────────────────────────

-- ── Extensions ────────────────────────────────────────────────────────────────

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- needed for gen_random_uuid()

-- ── comment_embeddings table ──────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS comment_embeddings (
    comment_id  TEXT PRIMARY KEY REFERENCES comments(id) ON DELETE CASCADE,
    embedding   vector(768) NOT NULL,   -- 768 for local backend; 1536 for OpenAI
    embedded_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ── Dimension migration (only needed if switching from 1536 → 768) ─────────
-- Uncomment these if you previously ran with EMBEDDING_BACKEND=openai and are
-- switching to the free local backend.  All embeddings will need to be
-- regenerated afterwards with: python ingest.py --mode embed
--
-- ALTER TABLE posts DROP COLUMN IF EXISTS embedding;
-- ALTER TABLE posts ADD COLUMN embedding vector(768);
-- ALTER TABLE posts DROP COLUMN IF EXISTS embedded_at;
-- ALTER TABLE posts ADD COLUMN embedded_at TIMESTAMP;
--
-- ALTER TABLE alerts DROP COLUMN IF EXISTS query_embedding;
-- ALTER TABLE alerts ADD COLUMN query_embedding vector(768);
--
-- DROP TABLE IF EXISTS comment_embeddings;
-- CREATE TABLE comment_embeddings (
--     comment_id  TEXT PRIMARY KEY REFERENCES comments(id) ON DELETE CASCADE,
--     embedding   vector(768) NOT NULL,
--     embedded_at TIMESTAMP NOT NULL DEFAULT NOW()
-- );

-- ── Add missing columns to posts ──────────────────────────────────────────────
-- Each ALTER is wrapped in a DO block so it's a no-op if the column exists.

DO $$ BEGIN
    ALTER TABLE posts ADD COLUMN IF NOT EXISTS last_comment_utc TIMESTAMP;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE posts ADD COLUMN IF NOT EXISTS recent_comment_count INTEGER;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE posts ADD COLUMN IF NOT EXISTS activity_ratio FLOAT;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE posts ADD COLUMN IF NOT EXISTS reconstructed_text TEXT;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE posts ADD COLUMN IF NOT EXISTS embedded_at TIMESTAMP;
EXCEPTION WHEN duplicate_column THEN NULL; END $$;

-- ── Add ON DELETE CASCADE to comments.post_id if missing ─────────────────────
-- This is a constraint change; skip if the FK already has cascade.
-- Uncomment and adapt if needed:
-- ALTER TABLE comments DROP CONSTRAINT IF EXISTS comments_post_id_fkey;
-- ALTER TABLE comments ADD CONSTRAINT comments_post_id_fkey
--     FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE;

-- ── HNSW vector indexes ───────────────────────────────────────────────────────
-- Requires pgvector >= 0.5. These build in the background on Supabase/RDS.
-- Note: building a HNSW index on a large existing table can take several minutes.

CREATE INDEX IF NOT EXISTS posts_embedding_hnsw
    ON posts USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS comment_embeddings_hnsw
    ON comment_embeddings USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- ── Supporting indexes ────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS posts_subreddit_idx ON posts (subreddit);
CREATE INDEX IF NOT EXISTS posts_created_utc_idx ON posts (created_utc);
CREATE INDEX IF NOT EXISTS posts_activity_ratio_idx ON posts (activity_ratio DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS comments_post_id_idx ON comments (post_id);
CREATE INDEX IF NOT EXISTS comments_created_utc_idx ON comments (created_utc);

-- ── Rebuild reconstructed_text for any posts that are missing it ──────────────
-- This is a one-time fix; safe to re-run.

UPDATE posts
SET reconstructed_text = CASE
    WHEN body IS NOT NULL AND body <> ''
        THEN 'Title: ' || title || E'\n\n' || body
    ELSE
        'Title: ' || title
    END
WHERE reconstructed_text IS NULL;
