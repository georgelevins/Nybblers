# RedditDemand Backend

FastAPI backend for RedditDemand — a demand intelligence platform that lets founders and startups search through Reddit to find evidence that real people want the problem their business solves.

## Prerequisites

- Python 3.10+
- Supabase Postgres with pgvector enabled (for future real data)

## Setup

1. Copy the example env file and fill in your values:

   ```bash
   cp .env.example .env
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the server:

   ```bash
   cd backend
   source venv/bin/activate   # if using a venv
   python -m uvicorn main:app --reload
   ```

   Using `python -m uvicorn` ensures the venv's Python (and its installed packages) is used, avoiding conflicts with system or conda Python.

The API will be available at `http://localhost:8000`. Docs at `http://localhost:8000/docs`.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check — returns status and timestamp |
| POST | `/search` | Semantic search — `{ "query": "...", "subreddit": "optional", "limit": 20 }` |
| GET | `/threads/opportunities` | Opportunity view — posts by activity_ratio. Params: `subreddit`, `limit`, `min_activity_ratio` |
| GET | `/threads/{id}` | Single thread with comments |
| POST | `/alerts` | Create alert — `{ "user_email": "...", "query": "..." }` |

## Current State

**Mock data only.** All endpoints return hardcoded data. Real database integration (OpenAI embeddings, pgvector search) will be added when the schema is finalized.

## Schema

See `schema.sql` for the database schema. Requires pgvector extension.
