-- RedditDemand database schema
-- Requires pgvector extension: CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE posts (
  id TEXT PRIMARY KEY,
  subreddit TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT,
  author TEXT,
  created_utc TIMESTAMP NOT NULL,
  score INTEGER,
  url TEXT,
  num_comments INTEGER,
  last_comment_utc TIMESTAMP,
  recent_comment_count INTEGER,
  activity_ratio FLOAT,
  embedding vector(1536),
  embedded_at TIMESTAMP,
  reconstructed_text TEXT
);

CREATE TABLE comments (
  id TEXT PRIMARY KEY,
  post_id TEXT REFERENCES posts(id),
  parent_id TEXT,
  parent_type TEXT,
  author TEXT,
  body TEXT NOT NULL,
  created_utc TIMESTAMP NOT NULL,
  score INTEGER,
  controversiality INTEGER
);

CREATE TABLE alerts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_email TEXT NOT NULL,
  query TEXT NOT NULL,
  query_embedding vector(1536),
  created_at TIMESTAMP DEFAULT NOW(),
  last_notified_at TIMESTAMP
);

-- Indexes for query performance
CREATE INDEX IF NOT EXISTS comments_post_id_idx ON comments (post_id);
CREATE INDEX IF NOT EXISTS posts_activity_ratio_idx ON posts (activity_ratio DESC NULLS LAST);
