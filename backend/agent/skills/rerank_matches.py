"""Rerank retrieval matches by relevance to the idea/query."""

from ..claude_client import complete_json, get_prompt
from ..schemas import AgentRequest, AgentResponse
from .._response import normalize_llm_output
from ._build_user import build_user_message


def rerank_matches_skill(request: AgentRequest) -> AgentResponse:
    system = get_prompt("rerank_matches", "v1")
    user = build_user_message(request)
    raw = complete_json(system=system, user=user)
    return normalize_llm_output(request.action, raw)
