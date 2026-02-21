"""Flesh out a raw idea into a full idea card (expand into problem, customer, solution, etc.)."""

from ..claude_client import complete_json, get_prompt
from ..schemas import AgentRequest, AgentResponse
from .._response import normalize_llm_output
from ._build_user import build_user_message


def flesh_out_idea_skill(request: AgentRequest) -> AgentResponse:
    system = get_prompt("flesh_out_idea", "v1")
    user = build_user_message(request, use_mock_if_empty=True)
    raw = complete_json(system=system, user=user)
    return normalize_llm_output(request.action, raw)
