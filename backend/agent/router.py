"""
Agent router: single entrypoint that accepts an action and returns structured AgentResponse.
"""

from .schemas import AgentRequest, AgentResponse
from .skills import (
    normalize_idea_skill,
    flesh_out_idea_skill,
    refine_idea_skill,
    generate_variants_skill,
    rerank_matches_skill,
    extract_evidence_skill,
    rank_idea_skill,
    overview_skill,
)


def run(request: AgentRequest) -> AgentResponse:
    """Dispatch by action to the corresponding skill; return AgentResponse."""
    action = request.action
    if action == "normalize_idea":
        return normalize_idea_skill(request)
    if action == "flesh_out_idea":
        return flesh_out_idea_skill(request)
    if action == "refine_idea":
        return refine_idea_skill(request)
    if action == "generate_variants":
        return generate_variants_skill(request)
    if action == "rerank_matches":
        return rerank_matches_skill(request)
    if action == "extract_evidence":
        return extract_evidence_skill(request)
    if action == "rank_idea":
        return rank_idea_skill(request)
    if action == "overview":
        return overview_skill(request)
    raise ValueError(f"Unknown action: {action}")
