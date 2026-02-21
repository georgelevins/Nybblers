"""Build user message payload from AgentRequest for prompt injection."""

import json
from ..schemas import AgentRequest


def _matches_json(req: AgentRequest) -> str:
    if not req.retrieval.matches:
        return "No retrieval matches provided."
    parts = []
    for m in req.retrieval.matches:
        parts.append({"id": m.id, "title": m.title, "text": m.text[:2000], "source": m.source})
    return json.dumps(parts, indent=2)


def build_user_message(req: AgentRequest) -> str:
    """Single place to build the user message from request fields."""
    sections = [
        f"Idea text:\n{req.idea_text or '(none)'}",
        f"Constraints: target_customer={req.constraints.target_customer}, b2b_or_b2c={req.constraints.b2b_or_b2c}, budget={req.constraints.budget}, timeline={req.constraints.timeline}, geography={req.constraints.geography}, avoid={req.constraints.avoid}",
        f"Context: founder_background={req.context.founder_background or '(none)'}, assets={req.context.assets}, preferences={req.context.preferences}",
        f"Retrieval matches:\n{_matches_json(req)}",
    ]
    return "\n\n".join(sections)
