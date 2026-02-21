"""Run flesh_out + rank + extract_evidence and return one combined overview response."""

from ..schemas import AgentRequest, AgentResponse
from .flesh_out_idea import flesh_out_idea_skill
from .rank_idea import rank_idea_skill
from .extract_evidence import extract_evidence_skill


def overview_skill(request: AgentRequest) -> AgentResponse:
    """Run flesh_out_idea, rank_idea, extract_evidence; merge into one response."""
    req_flesh = request.model_copy(update={"action": "flesh_out_idea"})
    req_rank = request.model_copy(update={"action": "rank_idea"})
    req_extract = request.model_copy(update={"action": "extract_evidence"})

    r1 = flesh_out_idea_skill(req_flesh)
    r2 = rank_idea_skill(req_rank)
    r3 = extract_evidence_skill(req_extract)

    # Merge: idea_card from flesh_out; outputs from rank + note; evidence from extract
    outputs = dict(r2.outputs)
    outputs["overview_ran"] = ["flesh_out_idea", "rank_idea", "extract_evidence"]

    return AgentResponse(
        action="overview",
        idea_card=r1.idea_card,
        outputs=outputs,
        assumptions=r1.assumptions,
        risks=r1.risks,
        next_steps=r1.next_steps,
        evidence=r3.evidence,
    )
