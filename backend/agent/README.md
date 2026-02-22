# Remand AI Agent

Action-based orchestration layer for the Remand product. **The agent always decides based on the Reddit/demand data (retrieval matches) provided**—it does not invent or assume demand beyond that data. Built as a **standalone template** so it can drop in when the rest of the system (vector search, Reddit ingestion, DB) is implemented.

## Contract

- **Single endpoint:** `POST /agent/run`
- **Input:** `AgentRequest` (action + idea_text + optional constraints, context, retrieval.matches)
- **Output:** `AgentResponse` (idea_card, outputs, assumptions, risks, next_steps, evidence)

## Actions

| Action | Description |
|--------|-------------|
| `enhance_idea` | AI Enhance: brainstorm a better-but-similar idea, test both against Remand search (Reddit), and only suggest the enhanced idea if it has greater traction. |

## Layout

- `schemas.py` — AgentRequest, AgentResponse, IdeaCard, RetrievalMatch (frozen contract)
- `router.py` — Dispatches `action` → corresponding skill
- `claude_client.py` — LLM wrapper (OpenAI GPT; JSON-only, token limit, low temperature)
- `skills/enhance_idea.py` — Enhance workflow (prompt + LLM + search traction comparison)
- `prompts/enhance_idea_v1.txt` — Prompt for the enhance step
- `interfaces.py` — Placeholder Retriever, Store, RedditSource (stub now; implement later)
- `mock_retrieval.py` — Optional mock Reddit-style matches (not used by enhance_idea; enhance uses live search)

## Env

Set `ANTHROPIC_API_KEY` in backend `.env`. Without it, `POST /agent/run` returns 503.

## Testing without other infra

Send `POST /agent/run` with:

- `action`: `enhance_idea`
- `idea_text`: e.g. "Tool for freelancers to track time"
- `retrieval.matches`: optional array of `{ id, title, text, source }` (can be 5–10 fake matches)

The agent returns stable JSON; no vector DB or Reddit pipeline required for development.
