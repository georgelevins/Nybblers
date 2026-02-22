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
    key = (os.environ.get("ANTHROPIC_API_KEY") or "").strip()
    return {"configured": bool(key), "key_length": len(key)}


@router.get("/ping")
def agent_ping() -> dict:
    """
    Send one minimal request to Claude to verify basic connectivity.
    Returns {"ok": true, "message": "Claude is reachable"} on success.
    Use this to confirm the API key works and the app can talk to Claude.
    """
    from agent.claude_client import complete
    try:
        reply = complete(
            system="You are a connectivity test. Reply with exactly: OK",
            user="Say OK.",
            max_tokens=10,
        )
        return {"ok": True, "message": "Claude is reachable", "reply": (reply or "").strip()[:50]}
    except RuntimeError as e:
        if "API key" in str(e) or "ANTHROPIC_API_KEY" in str(e):
            raise HTTPException(status_code=503, detail="Claude API not configured (missing ANTHROPIC_API_KEY)")
        raise HTTPException(status_code=502, detail=f"Claude API error: {e}")
    except Exception as e:
        # Catch SDK/network errors so we return 502 with JSON (and CORS) instead of 500
        raise HTTPException(status_code=502, detail=f"Claude API error: {e!s}")


@router.post("/run", response_model=AgentResponse)
def agent_run(request: AgentRequest) -> AgentResponse:
    """
    Run the agent for one action. Input: AgentRequest. Output: AgentResponse.
    Actions: enhance_idea (AI Enhance).
    """
    try:
        return run(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        if "API key" in str(e) or "ANTHROPIC_API_KEY" in str(e):
            raise HTTPException(status_code=503, detail="Agent not configured (missing API key)")
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Agent error: {e!s}")
