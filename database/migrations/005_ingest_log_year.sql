-- Migration 005: ingest_log per-year idempotency (Option B)
-- Adds year column so the same file can be ingested once per year.
-- Idempotency key: (file_name, year). year NULL = full-file ingest.
-- Idempotent: safe to run multiple times.

ALTER TABLE ingest_log
  ADD COLUMN IF NOT EXISTS year INT NULL;

-- Index for "already done?" check: (file_name, year) and status = 'complete'
CREATE INDEX IF NOT EXISTS ingest_log_file_year_status_idx
  ON ingest_log (file_name, year, status);
