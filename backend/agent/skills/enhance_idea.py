"""
AI Enhance: brainstorm a better-but-similar idea, test both against Remand search,
and only suggest the enhanced idea if it has greater Reddit traction.
"""

import asyncio
from typing import Any

from ..claude_client import complete_json, get_prompt
from ..schemas import AgentRequest, AgentResponse
from .._response import normalize_llm_output
from ._build_user import build_user_message

# Limit and traction window for fair comparison
TOP_MATCHES_LIMIT = 15


def _traction_score(matches: list[Any]) -> float:
    """Sum of similarity scores; higher = more/better Reddit demand."""
    return sum(getattr(m, "similarity", 0.0) for m in matches)


def enhance_idea_skill(request: AgentRequest) -> AgentResponse:
    """
    1. LLM generates one enhanced idea (stays close to original).
    2. Test both ideas via Remand search (get_top_matches); compare traction.
    3. Only suggest enhanced idea if its traction is strictly greater.
    """
    system = get_prompt("enhance_idea", "v1")
    user = build_user_message(request, use_mock_if_empty=False)
    raw = complete_json(system=system, user=user)
    base_response = normalize_llm_output("enhance_idea", raw)

    enhanced_idea_text: str = ""
    if isinstance(raw.get("outputs"), dict):
        enhanced_idea_text = (raw["outputs"].get("enhanced_idea_text") or "").strip()
    if not enhanced_idea_text:
        base_response.outputs["suggested"] = False
        base_response.outputs["enhance_error"] = "Could not generate an enhanced idea."
        return base_response

    original_traction = 0.0
    enhanced_traction = 0.0
    try:
        from repositories import posts as posts_repo

        async def _fetch_both() -> tuple[list[Any], list[Any]]:
            orig = await posts_repo.get_top_matches(request.idea_text.strip() or "(none)", limit=TOP_MATCHES_LIMIT)
            enh = await posts_repo.get_top_matches(enhanced_idea_text, limit=TOP_MATCHES_LIMIT)
            return orig.matches, enh.matches

        loop = asyncio.new_event_loop()
        try:
            orig_matches, enh_matches = loop.run_until_complete(_fetch_both())
            original_traction = _traction_score(orig_matches)
            enhanced_traction = _traction_score(enh_matches)
        finally:
            loop.close()
    except Exception as e:  # DB unavailable or embed/search failure
        base_response.outputs["suggested"] = False
        base_response.outputs["enhance_error"] = f"Could not test demand: {e!s}"
        base_response.outputs["enhanced_idea_text"] = enhanced_idea_text
        if isinstance(raw.get("outputs"), dict):
            base_response.outputs["rationale"] = raw["outputs"].get("rationale", "")
        return base_response

    # Only suggest enhanced if it has strictly better traction
    suggested = enhanced_traction > original_traction
    base_response.outputs["suggested"] = suggested
    base_response.outputs["enhanced_idea_text"] = enhanced_idea_text
    base_response.outputs["original_traction"] = round(original_traction, 2)
    base_response.outputs["enhanced_traction"] = round(enhanced_traction, 2)
    if isinstance(raw.get("outputs"), dict):
        base_response.outputs["rationale"] = raw["outputs"].get("rationale", "")

    return base_response
