"""Normalize a raw idea into a structured idea card."""

from ..claude_client import complete_json, get_prompt
from ..schemas import AgentRequest, AgentResponse
from .._response import normalize_llm_output
from ._build_user import build_user_message


def normalize_idea_skill(request: AgentRequest) -> AgentResponse:
    system = get_prompt("normalize_idea", "v1")
    user = build_user_message(request)
    raw = complete_json(system=system, user=user)
    return normalize_llm_output(request.action, raw)
