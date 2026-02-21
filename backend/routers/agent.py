"""
Agent API: single endpoint for the Remand AI agent.
Separate from search, threads, alerts — agent-only surface.
"""

from fastapi import APIRouter, HTTPException

from agent import run
from agent.schemas import AgentRequest, AgentResponse

router = APIRouter()


@router.get("/status")
def agent_status() -> dict:
    """Check if the agent has an API key configured (does not expose the key)."""
    import os
    from pathlib import Path
    from dotenv import load_dotenv
    # Force-load .env from backend folder (routers/agent.py -> backend/.env)
    _backend_dir = Path(__file__).resolve().parent.parent
    load_dotenv(dotenv_path=_backend_dir / ".env")
    key = (os.environ.get("OPENAI_API_KEY") or "").strip()
    return {"configured": bool(key), "key_length": len(key)}


@router.post("/run", response_model=AgentResponse)
def agent_run(request: AgentRequest) -> AgentResponse:
    """
    Run the agent for one action. Input: AgentRequest. Output: AgentResponse.
    Actions: normalize_idea, flesh_out_idea, refine_idea, generate_variants, rerank_matches, extract_evidence, rank_idea, overview.
    """
    try:
        return run(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        if "API key" in str(e) or "OPENAI_API_KEY" in str(e):
            raise HTTPException(status_code=503, detail="Agent not configured (missing API key)")
        raise HTTPException(status_code=502, detail=str(e))
