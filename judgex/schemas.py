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
    questions: list[str] = Field(
        default_factory=list,
        description=(
            "Optional questions the persona raises to the pool (un-addressed; any other expert "
            "may pick them up in the next round). Leave empty if the persona has nothing to ask."
        ),
    )
    revised_scores: dict[str, int] | None = Field(
        default=None,
        description=(
            "Optional revised scores per dimension if the pool reading changes the persona's "
            "judgment. Keys: feasibility, novelty, impact, presentation."
        ),
    )


class PeerQuestion(BaseModel):
    """A single directed question from one cluster-peer to another (Direct Communication)."""

    to_persona: PersonaId = Field(..., description="The cluster-peer this question is addressed to.")
    question: str


class PeerQuestionSet(BaseModel):
    """An agent's optional questions to its cluster-peers in the peer-exchange step.

    At most one question per peer, and entirely optional: an agent that has nothing to
    ask returns an empty list.
    """

    questions: list[PeerQuestion] = Field(default_factory=list)


class PeerAnswerItem(BaseModel):
    question: str = Field(..., description="The peer question being answered (echoed verbatim).")
    answer: str


class PeerAnswerSet(BaseModel):
    """An agent's answers to the questions its cluster-peers directed at it."""

    answers: list[PeerAnswerItem] = Field(default_factory=list)


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
