"""
Agent API: single endpoint for the Remand AI agent.
Separate from search, threads, alerts — agent-only surface.
"""

from fastapi import APIRouter, HTTPException

from agent import run
from agent.schemas import AgentRequest, AgentResponse

router = APIRouter()


@router.post("/run", response_model=AgentResponse)
def agent_run(request: AgentRequest) -> AgentResponse:
    """
    Run the agent for one action. Input: AgentRequest. Output: AgentResponse.
    Actions: normalize_idea, refine_idea, generate_variants, rerank_matches, extract_evidence.
    """
    try:
        return run(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        if "ANTHROPIC_API_KEY" in str(e):
            raise HTTPException(status_code=503, detail="Agent not configured (missing API key)")
        raise HTTPException(status_code=502, detail=str(e))
