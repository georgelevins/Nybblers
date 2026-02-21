-- Migration 002: HNSW vector similarity indexes
-- Run AFTER bulk data load — building HNSW on an empty table is instant,
-- but building it after loading data is much faster than inserting with the
-- index already present (avoids incremental index updates on every row).
--
-- Requires pgvector >= 0.5.0.
-- Idempotent: safe to run multiple times.

-- Cosine similarity index for semantic post search
CREATE INDEX IF NOT EXISTS posts_embedding_hnsw
  ON posts USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- Cosine similarity index for alert query matching
CREATE INDEX IF NOT EXISTS alerts_query_embedding_hnsw
  ON alerts USING hnsw (query_embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
