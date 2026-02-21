-- Migration 004: comment_embeddings table
-- Stores per-comment vectors separately from the comments table.
-- Keeping them separate means:
--   - The comments table stays lean during bulk inserts
--   - Embedding can be run as a deferred job without locking comments
--   - A missing embedding is simply an absent row (no NULL columns to scan)
-- Idempotent: safe to run multiple times.

CREATE TABLE IF NOT EXISTS comment_embeddings (
  comment_id  TEXT        PRIMARY KEY REFERENCES comments(id) ON DELETE CASCADE,
  embedding   vector(1536) NOT NULL,
  embedded_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- HNSW index for cosine similarity search on individual comments
-- (used for lead-level search: surface the specific person/comment)
CREATE INDEX IF NOT EXISTS comment_embeddings_hnsw
  ON comment_embeddings USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
