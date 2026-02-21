-- Migration 003: ingest_log table
-- Tracks every file processed by ingest.py so we can:
--   - Skip files already successfully ingested (idempotent re-runs)
--   - Resume after a crash (status='failed' rows can be retried)
--   - Audit how much data came from each file
-- Idempotent: safe to run multiple times.

CREATE TABLE IF NOT EXISTS ingest_log (
  id            SERIAL PRIMARY KEY,
  file_name     TEXT        NOT NULL,
  file_type     TEXT        NOT NULL,  -- 'submissions' or 'comments'
  started_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  completed_at  TIMESTAMPTZ,
  rows_inserted INTEGER,
  status        TEXT        NOT NULL DEFAULT 'running',
  -- status values: 'running' | 'complete' | 'failed'
  error_text    TEXT
);

-- Speeds up the "already done?" check at the start of each ingest run
CREATE INDEX IF NOT EXISTS ingest_log_file_status_idx
  ON ingest_log (file_name, status);
