"""
Agent router: single entrypoint that accepts an action and returns structured AgentResponse.
Only action: enhance_idea (AI Enhance).
"""

from .schemas import AgentRequest, AgentResponse
from .skills import enhance_idea_skill


def run(request: AgentRequest) -> AgentResponse:
    """Dispatch by action to the corresponding skill; return AgentResponse."""
    if request.action == "enhance_idea":
        return enhance_idea_skill(request)
    raise ValueError(f"Unknown action: {request.action}")
