"""
AI Enhance: brainstorm up to 5 better-but-similar ideas, test each against Remand search.
Only suggest one if it has greater Reddit traction; otherwise report "your idea is well optimised".
When the Remand DB is unavailable, we still run Claude once and return the enhanced idea (no traction comparison).
"""

import asyncio
from typing import Any

from ..claude_client import complete_json, get_prompt
from ..schemas import AgentRequest, AgentResponse
from .._response import normalize_llm_output
from ._build_user import build_user_message

# Limit and traction window for fair comparison
TOP_MATCHES_LIMIT = 15
MAX_BRAINSTORM_ATTEMPTS = 5


def _traction_score(matches: list[Any]) -> float:
    """Sum of similarity scores; higher = more/better Reddit demand."""
    return sum(getattr(m, "similarity", 0.0) for m in matches)


def _run_with_db(request: AgentRequest) -> AgentResponse | None:
    """
    Run full pipeline using Remand DB for traction. Returns None if DB is unavailable.
    """
    system = get_prompt("enhance_idea", "v1")
    base_user = build_user_message(request, use_mock_if_empty=False)

    # Get original traction once (required to compare)
    try:
        from repositories import posts as posts_repo

        async def _fetch_original() -> list[Any]:
            r = await posts_repo.get_top_matches(
                request.idea_text.strip() or "(none)", limit=TOP_MATCHES_LIMIT
            )
            return r.matches

        loop = asyncio.new_event_loop()
        try:
            orig_matches = loop.run_until_complete(_fetch_original())
            original_traction = _traction_score(orig_matches)
        finally:
            loop.close()
    except Exception:
        return None

    # Brainstorm -> back_idea up to 5 times; stop when one beats original
    winner_idea: str | None = None
    winner_traction: float = 0.0
    winner_rationale: str = ""
    last_raw: dict[str, Any] = {}

    for attempt in range(1, MAX_BRAINSTORM_ATTEMPTS + 1):
        user = base_user
        if attempt > 1:
            user += f"\n\nAttempt {attempt} of {MAX_BRAINSTORM_ATTEMPTS}. Previous variant(s) did not beat the original traction; try a different refinement (same idea, different wording or angle)."
        raw = complete_json(system=system, user=user)
        last_raw = raw

        enhanced_idea_text = ""
        if isinstance(raw.get("outputs"), dict):
            enhanced_idea_text = (raw["outputs"].get("enhanced_idea_text") or "").strip()
        if not enhanced_idea_text:
            continue

        try:
            from repositories import posts as posts_repo

            async def _fetch_enhanced(text: str) -> list[Any]:
                r = await posts_repo.get_top_matches(text, limit=TOP_MATCHES_LIMIT)
                return r.matches

            loop = asyncio.new_event_loop()
            try:
                enh_matches = loop.run_until_complete(_fetch_enhanced(enhanced_idea_text))
                enhanced_traction = _traction_score(enh_matches)
            finally:
                loop.close()
        except Exception:
            continue

        if enhanced_traction > original_traction:
            winner_idea = enhanced_idea_text
            winner_traction = enhanced_traction
            winner_rationale = (raw.get("outputs") or {}).get("rationale") or ""
            break

    base_response = normalize_llm_output("enhance_idea", last_raw)
    base_response.outputs["original_traction"] = round(original_traction, 2)
    base_response.outputs["db_used"] = True

    if winner_idea is not None:
        base_response.outputs["suggested"] = True
        base_response.outputs["enhanced_idea_text"] = winner_idea
        base_response.outputs["enhanced_traction"] = round(winner_traction, 2)
        base_response.outputs["rationale"] = winner_rationale
    else:
        base_response.outputs["suggested"] = False
        base_response.outputs["well_optimised_message"] = (
            "We couldn't enhance your idea—after five attempts, no refinement had better traction than your original."
        )
        base_response.outputs["enhanced_idea_text"] = None
        base_response.outputs["enhanced_traction"] = None
        base_response.outputs["rationale"] = ""

    return base_response


def _run_without_db(request: AgentRequest) -> AgentResponse:
    """
    DB unavailable: run Claude once with request context (and optional mock retrieval),
    return the enhanced idea without traction comparison.
    """
    system = get_prompt("enhance_idea", "v1")
    base_user = build_user_message(request, use_mock_if_empty=True)
    raw = complete_json(system=system, user=base_user)
    base_response = normalize_llm_output("enhance_idea", raw)
    base_response.outputs["db_used"] = False
    base_response.outputs["original_traction"] = None
    base_response.outputs["enhanced_traction"] = None

    enhanced_idea_text = ""
    if isinstance(raw.get("outputs"), dict):
        enhanced_idea_text = (raw["outputs"].get("enhanced_idea_text") or "").strip()
    rationale = (raw.get("outputs") or {}).get("rationale") or ""

    if enhanced_idea_text:
        base_response.outputs["suggested"] = True
        base_response.outputs["enhanced_idea_text"] = enhanced_idea_text
        base_response.outputs["rationale"] = rationale
    else:
        base_response.outputs["suggested"] = False
        base_response.outputs["enhanced_idea_text"] = None
        base_response.outputs["rationale"] = ""
        base_response.outputs["well_optimised_message"] = (
            "We couldn't generate an enhanced variant this time. Try rephrasing your idea."
        )

    return base_response


def enhance_idea_skill(request: AgentRequest) -> AgentResponse:
    """
    Pipeline: when Remand DB is available, brainstorm and compare traction; otherwise
    run Claude once and return the enhanced idea (referencing request/retrieval context).
    """
    response = _run_with_db(request)
    if response is not None:
        return response
    return _run_without_db(request)
