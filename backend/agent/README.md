# Remand AI Agent

Action-based orchestration layer for the Remand product. **The agent always decides based on the Reddit/demand data (retrieval matches) provided**—it does not invent or assume demand beyond that data. Built as a **standalone template** so it can drop in when the rest of the system (vector search, Reddit ingestion, DB) is implemented.

## Contract

- **Single endpoint:** `POST /agent/run`
- **Input:** `AgentRequest` (action + idea_text + optional constraints, context, retrieval.matches)
- **Output:** `AgentResponse` (idea_card, outputs, assumptions, risks, next_steps, evidence)

## Actions

| Action | Description |
|--------|-------------|
| `normalize_idea` | Turn raw idea text into a structured idea card |
| `flesh_out_idea` | Expand a raw idea into a full idea card (problem, customer, solution, etc.); use evidence when provided |
| `refine_idea` | Sharpen and improve an existing idea using evidence (clearer problem, better differentiation)—not just expansion |
| `rank_idea` | Rate the idea 1–10 against the data; outputs strengths, weaknesses, rationale |
| `overview` | Run flesh_out + rank + extract_evidence in one call; returns idea_card, rating, evidence for a full overview |
| `generate_variants` | Generate alternative angles/variants for the idea |
| `rerank_matches` | Score and sort retrieval matches by relevance |
| `extract_evidence` | Pick best quotes from matches as evidence (sorted best/most accurate first) |

## Layout

- `schemas.py` — AgentRequest, AgentResponse, IdeaCard, RetrievalMatch (frozen contract)
- `router.py` — Dispatches `action` → corresponding skill
- `claude_client.py` — LLM wrapper (OpenAI GPT; JSON-only, token limit, low temperature)
- `skills/*.py` — One workflow per action (prompt + Claude + normalize to AgentResponse)
- `prompts/*.txt` — Versioned prompt library (v1)
- `interfaces.py` — Placeholder Retriever, Store, RedditSource (stub now; implement later)
- `mock_retrieval.py` — Mock Reddit-style matches when no DB; used by refine_idea, rank_idea, extract_evidence

## Env

Set `OPENAI_API_KEY` in backend `.env`. Without it, `POST /agent/run` returns 503.

## Testing without other infra

Send `POST /agent/run` with:

- `action`: one of the five actions
- `idea_text`: e.g. "Tool for freelancers to track time"
- `retrieval.matches`: optional array of `{ id, title, text, source }` (can be 5–10 fake matches)

The agent returns stable JSON; no vector DB or Reddit pipeline required for development.
