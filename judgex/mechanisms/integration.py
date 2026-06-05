"""Integration-oriented Cooperation mechanism (spec §3.1).

Participants treat other perspectives as complementary inputs and work toward
shared understanding and synthesis. Focus: combining, complementing, integrating.

This module exposes prompt fragments that get composed into the system / user
prompts of the architecture nodes. The mechanism is prompt scaffolding only;
it does NOT change persona definitions or the output schema.
"""
from __future__ import annotations

MECHANISM_NAME = "integration_oriented"


PERSONA_PREAMBLE = (
    "You are participating in a cooperative multi-expert evaluation. "
    "Treat the other experts' perspectives as complementary inputs. "
    "When you see another perspective, look first for what it adds to yours, "
    "not for what you can refute. Aim to enable a later synthesis that integrates "
    "your lens with the others."
)


INDIVIDUAL_JUDGMENT_INSTRUCTION = (
    "Produce your structured judgment of the proposal from your persona's lens. "
    "Where another perspective would be needed to fully evaluate a dimension, name it "
    "in `key_concerns` rather than penalising the score on grounds outside your expertise."
)


CLARIFICATION_AGENT_INSTRUCTION = (
    "Another expert has raised a question relevant to your evaluation. "
    "Respond constructively: clarify, fill gaps, and update your scores if the new "
    "information genuinely changes your judgment. Stay in your persona's lens."
)


SYNTHESIS_INSTRUCTION = (
    "Synthesize the experts' judgments into a single final judgment. "
    "Where perspectives complement each other, integrate them. "
    "Where they diverge, decide on a consolidated score and explain how the divergence "
    "was resolved. Score each dimension on integer 1-5; the `average` is the mean of the four. "
    "Be explicit about remaining uncertainty in the `uncertainty` field."
)


CONFLICT_DETECTION_INSTRUCTION = (
    "Compare the experts' judgments. Identify dimensions where scores diverge by more than "
    "1 point, and surface specific assumptions or evidence gaps behind the divergence. "
    "Under the integration-oriented mechanism, frame these as gaps to fill, not as positions "
    "to defeat."
)
