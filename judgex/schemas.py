from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, conint

PersonaId = Literal["A1", "A2", "A3", "A4", "A5", "A6"]
Dimension = Literal["feasibility", "novelty", "impact", "presentation"]

DIMENSIONS = ("feasibility", "novelty", "impact", "presentation")


Score = conint(ge=1, le=5)


class DimensionScore(BaseModel):
    score: Score = Field(..., description="Integer 1-5, where 1 = very weak, 5 = excellent.")
    rationale: str = Field(..., description="Concise justification grounded in the proposal text.")


class AgentJudgment(BaseModel):
    """Structured single-agent judgment of a proposal."""

    persona_id: PersonaId
    proposal_id: str
    feasibility: DimensionScore
    novelty: DimensionScore
    impact: DimensionScore
    presentation: DimensionScore
    perspective_summary: str = Field(
        ...,
        description="2-4 sentences summarizing the proposal from this persona's evaluation lens.",
    )
    key_concerns: list[str] = Field(
        default_factory=list,
        description="Concrete concerns or open assumptions the persona wants flagged.",
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Self-reported confidence in the overall judgment.",
    )


class ClarificationRequestItem(BaseModel):
    persona_id: PersonaId
    question: str


class Conflict(BaseModel):
    dimension: Dimension
    score_spread: int = Field(..., ge=0, le=4)
    personas_involved: list[PersonaId]
    summary: str


class ConflictReport(BaseModel):
    """Output of C0's conflict-detection pass in the Centralized architecture (phase 3)."""

    conflicts: list[Conflict]
    clarification_requests: list[ClarificationRequestItem]


class ClarificationResponse(BaseModel):
    """A persona's response to a targeted clarification question (Centralized phase 4)."""

    answer: str
    revised_scores: dict[str, int] | None = Field(
        default=None,
        description=(
            "Optional revised scores per dimension if the answer changes the persona's earlier "
            "judgment. Keys: feasibility, novelty, impact, presentation."
        ),
    )


class PoolReaction(BaseModel):
    """A persona's reaction to the shared pool after reading peers' contributions."""

    persona_id: PersonaId
    text: str = Field(
        ...,
        description="Concise reaction: what the persona adds, agrees with, or qualifies after seeing peers.",
    )
    revised_scores: dict[str, int] | None = Field(
        default=None,
        description=(
            "Optional revised scores per dimension if the pool reading changes the persona's "
            "judgment. Keys: feasibility, novelty, impact, presentation."
        ),
    )


class Cluster(BaseModel):
    label: str
    summary: str
    contributing_personas: list[PersonaId]
    dimensions_touched: list[Dimension]


class ClusterReport(BaseModel):
    """Output of the Pool Curator in the Shared Message Pool architecture."""

    clusters: list[Cluster]
    open_questions: list[str]


class FinalJudgment(BaseModel):
    """Synthesized final judgment produced by the architecture-specific terminal node."""

    proposal_id: str
    feasibility: DimensionScore
    novelty: DimensionScore
    impact: DimensionScore
    presentation: DimensionScore
    average: float = Field(..., description="Mean of the four dimension scores.")
    synthesis: str = Field(
        ...,
        description="Narrative synthesis: how heterogeneous perspectives were integrated.",
    )
    uncertainty: str = Field(
        ...,
        description="Where the final judgment is least robust; remaining disagreements or open questions.",
    )
    contributing_agents: list[PersonaId] = Field(default_factory=list)
