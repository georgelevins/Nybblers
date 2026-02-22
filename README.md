# Remand
HACKEUROPE PROJECT
Where Ideas Meet Discussion

Track market buzz, measure demand momentum, and discover conversations where your next customers are already talking.

Live app: https://nybblers.vercel.app/

---

## From Discussion to Direction

Remand turns online noise into your next winning move. Our AI cuts through scattered threads, comments, and discussions to reveal high-intent opportunities so you know what to build, launch, or fix before your competitors do.

Build smarter. Grow faster.

---

## Features

### Growth Momentum

Most opportunities don't announce themselves. They show up in small, scattered conversations that slowly cluster. Growth Momentum maps that evolution in real time: when interest shifts from isolated curiosity to collective momentum. By identifying acceleration early, you gain something most teams never have: Timing.

You're not reacting to trends. You're entering before they peak.

### Embedded AI Agent

The agent powers your search and brainstorming, turning raw Reddit discussions into clear positioning, feature ideas, and outreach angles.

- Finds the strongest demand signals in noisy threads
- Summarizes recurring pain points in seconds
- Suggests practical go-to-market responses

Built to move from buzz to decisions faster.

---

## Tech Stack

**Frontend**
- Next.js 16, React 19, TypeScript, Tailwind CSS

**Backend**
- FastAPI, Python 3.10+, Uvicorn

**Data**
- Supabase Postgres (pgvector for semantic search)

**AI**
- OpenAI, Anthropic (embeddings and agent)

---

## Getting Started

### Prerequisites

- Node.js 18+ (for frontend)
- Python 3.10+ (for backend)
- Supabase Postgres with pgvector (for real data)

### Frontend

cd frontend
npm install
npm run dev

Open http://localhost:3000. Set NEXT_PUBLIC_API_URL in .env.local (e.g. http://localhost:8000) to point at the backend.

### Backend

cd backend
cp .env.example .env
pip install -r requirements.txt
python -m uvicorn main:app --reload

API: http://localhost:8000
Docs: http://localhost:8000/docs

### Root scripts

From the repo root: npm run dev (frontend), npm run build, npm run start.

---

## API Overview

- GET /health - Health check
- POST /agent/run - AI agent (validate, refine, rank ideas)
- POST /search - Semantic search over discussions
- GET /threads/opportunities - Opportunity view by activity
- GET /threads/{id} - Single thread with comments
- POST /alerts - Create alert (email and query)

---

## License

Private. All rights reserved.
