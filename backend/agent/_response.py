"""Normalize Claude JSON into AgentResponse. Keeps skills thin and schema-stable."""

from typing import Any

from .schemas import AgentAction, AgentResponse, EvidenceItem, IdeaCard


def _ensure_idea_card(obj: Any) -> IdeaCard:
    if not obj or not isinstance(obj, dict):
        return IdeaCard()
    return IdeaCard(
        problem=obj.get("problem"),
        customer=obj.get("customer"),
        when=obj.get("when"),
        current_workaround=obj.get("current_workaround"),
        solution=obj.get("solution"),
        differentiator=obj.get("differentiator"),
        monetization=obj.get("monetization"),
        distribution=obj.get("distribution"),
    )


def _ensure_evidence(arr: Any) -> list[EvidenceItem]:
    if not isinstance(arr, list):
        return []
    out = []
    for item in arr:
        if isinstance(item, dict) and "match_id" in item and "quote" in item:
            out.append(
                EvidenceItem(
                    match_id=str(item["match_id"]),
                    quote=str(item["quote"]),
                    why_it_matters=str(item.get("why_it_matters", "")),
                )
            )
    return out


def normalize_llm_output(action: AgentAction, raw: dict[str, Any]) -> AgentResponse:
    """Map Claude JSON to AgentResponse. Ensures required keys and types."""
    return AgentResponse(
        action=action,
        idea_card=_ensure_idea_card(raw.get("idea_card")),
        outputs=raw.get("outputs") if isinstance(raw.get("outputs"), dict) else {},
        assumptions=raw.get("assumptions") if isinstance(raw.get("assumptions"), list) else [],
        risks=raw.get("risks") if isinstance(raw.get("risks"), list) else [],
        next_steps=raw.get("next_steps") if isinstance(raw.get("next_steps"), list) else [],
        evidence=_ensure_evidence(raw.get("evidence")),
    )
