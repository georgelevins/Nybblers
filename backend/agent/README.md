# Remand AI Agent

Action-based orchestration layer for the Remand product. Built as a **standalone template** so it can drop in when the rest of the system (vector search, Reddit ingestion, DB) is implemented.

## Contract

- **Single endpoint:** `POST /agent/run`
- **Input:** `AgentRequest` (action + idea_text + optional constraints, context, retrieval.matches)
- **Output:** `AgentResponse` (idea_card, outputs, assumptions, risks, next_steps, evidence)

## Actions

| Action | Description |
|--------|-------------|
| `normalize_idea` | Turn raw idea text into a structured idea card |
| `refine_idea` | Refine and differentiate; returns 3 options + rank + rationale |
| `generate_variants` | Generate alternative angles/variants for the idea |
| `rerank_matches` | Score and sort retrieval matches by relevance |
| `extract_evidence` | Pick 2–3 best quotes from matches as evidence |

## Layout

- `schemas.py` — AgentRequest, AgentResponse, IdeaCard, RetrievalMatch (frozen contract)
- `router.py` — Dispatches `action` → corresponding skill
- `claude_client.py` — Single Claude wrapper (JSON-only, token limit, low temperature)
- `skills/*.py` — One workflow per action (prompt + Claude + normalize to AgentResponse)
- `prompts/*.txt` — Versioned prompt library (v1)
- `interfaces.py` — Placeholder Retriever, Store, RedditSource (stub now; implement later)

## Env

Set `ANTHROPIC_API_KEY` (see backend `.env.example`). Without it, `POST /agent/run` returns 503.

## Testing without other infra

Send `POST /agent/run` with:

- `action`: one of the five actions
- `idea_text`: e.g. "Tool for freelancers to track time"
- `retrieval.matches`: optional array of `{ id, title, text, source }` (can be 5–10 fake matches)

The agent returns stable JSON; no vector DB or Reddit pipeline required for development.
