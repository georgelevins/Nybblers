"""Build user message payload from AgentRequest for prompt injection."""

import json
from ..schemas import AgentRequest, RetrievalMatch


def get_effective_matches(req: AgentRequest, use_mock_if_empty: bool = False) -> list[RetrievalMatch]:
    """Return request's retrieval matches, or mock matches when empty if use_mock_if_empty."""
    if req.retrieval.matches:
        return req.retrieval.matches
    if use_mock_if_empty:
        from ..mock_retrieval import get_mock_matches
        return get_mock_matches()
    return []


def _matches_json(matches: list[RetrievalMatch]) -> str:
    if not matches:
        return "No retrieval matches provided."
    parts = []
    for m in matches:
        parts.append({"id": m.id, "title": m.title, "text": m.text[:2000], "source": m.source})
    return json.dumps(parts, indent=2)


def build_user_message(req: AgentRequest, use_mock_if_empty: bool = False) -> str:
    """Single place to build the user message from request fields. Set use_mock_if_empty=True to inject mock matches when none provided."""
    matches = get_effective_matches(req, use_mock_if_empty=use_mock_if_empty)
    sections = [
        f"Idea text:\n{req.idea_text or '(none)'}",
        f"Constraints: target_customer={req.constraints.target_customer}, b2b_or_b2c={req.constraints.b2b_or_b2c}, budget={req.constraints.budget}, timeline={req.constraints.timeline}, geography={req.constraints.geography}, avoid={req.constraints.avoid}",
        f"Context: founder_background={req.context.founder_background or '(none)'}, assets={req.context.assets}, preferences={req.context.preferences}",
        f"Retrieval matches:\n{_matches_json(matches)}",
    ]
    return "\n\n".join(sections)
