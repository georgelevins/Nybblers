"""
Agent request/response schemas for the Remand AI agent.
Frozen contract: frontend and downstream services depend on this shape.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field


# --- Action type (supported actions) ---
AgentAction = Literal[
    "normalize_idea",
    "refine_idea",
    "generate_variants",
    "rerank_matches",
    "extract_evidence",
]

MatchSource = Literal["reddit", "internal", "web", "other"]


# --- Retrieval (optional now; populated from vector DB / Reddit later) ---
class RetrievalMatch(BaseModel):
    id: str
    title: str
    text: str
    source: MatchSource
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalContext(BaseModel):
    matches: list[RetrievalMatch] = Field(default_factory=list)


# --- Request constraints and context ---
class AgentConstraints(BaseModel):
    target_customer: str | None = None
    b2b_or_b2c: Literal["b2b", "b2c", "unknown"] = "unknown"
    budget: str | None = None
    timeline: str | None = None
    geography: str | None = None
    avoid: list[str] = Field(default_factory=list)


class AgentRequestContext(BaseModel):
    founder_background: str | None = None
    assets: list[str] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)


# --- Full agent request ---
class AgentRequest(BaseModel):
    action: AgentAction
    idea_text: str = ""
    constraints: AgentConstraints = Field(default_factory=AgentConstraints)
    context: AgentRequestContext = Field(default_factory=AgentRequestContext)
    retrieval: RetrievalContext = Field(default_factory=RetrievalContext)


# --- Idea card (output shape for refine/normalize) ---
class IdeaCard(BaseModel):
    problem: str | None = None
    customer: str | None = None
    when: str | None = None
    current_workaround: str | None = None
    solution: str | None = None
    differentiator: str | None = None
    monetization: str | None = None
    distribution: str | None = None


# --- Evidence item (quote + why it matters) ---
class EvidenceItem(BaseModel):
    match_id: str
    quote: str
    why_it_matters: str


# --- Consistent agent response (all actions) ---
class AgentResponse(BaseModel):
    action: AgentAction
    idea_card: IdeaCard = Field(default_factory=IdeaCard)
    outputs: dict[str, Any] = Field(default_factory=dict)
    assumptions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
