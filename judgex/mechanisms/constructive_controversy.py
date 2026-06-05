"""Constructive Controversy mechanism (spec §3.2).

Established form of structured intellectual conflict: incompatible ideas, information,
or conclusions are deliberately confronted, while participants stay oriented toward a
reasoned synthesis (Johnson & Johnson, 2009). Systematic challenge, critical scrutiny,
and perspective differentiation come *before* integration.

Same shared-goal cooperative frame as integration-oriented; the difference is in the
mode of communication, not the goal structure.

Same scaffolding shape as integration.py - this module exposes prompt fragments only;
it does NOT change personas or the output schema.
"""
from __future__ import annotations

MECHANISM_NAME = "constructive_controversy"


PERSONA_PREAMBLE = (
    "You are participating in a multi-expert evaluation organised as constructive controversy. "
    "The shared goal is a reasoned synthesis, but the path runs through systematic challenge. "
    "When you see another perspective, your first job is to surface inconsistencies, contest "
    "weak assumptions, and sharpen the disagreement before integrating. Stay rigorous, not "
    "agreeable. The synthesis only counts after the disagreement has been worked through."
)


INDIVIDUAL_JUDGMENT_INSTRUCTION = (
    "Produce your structured judgment of the proposal from your persona's lens. "
    "Sharpen, do not soften: where the proposal makes claims that would not survive your "
    "lens's standards, mark them down and say why. Where other expert lenses would likely "
    "reach a different conclusion than you, flag the expected disagreement in `key_concerns` "
    "rather than pre-emptively splitting the difference."
)


CLARIFICATION_AGENT_INSTRUCTION = (
    "Another expert has challenged a part of your evaluation. Respond rigorously: defend "
    "your position where it holds, concede where the challenge actually exposes a weakness, "
    "and only revise your scores if the challenge changes the substance, not the social "
    "pressure. Stay in your persona's lens; do not drift toward consensus for its own sake."
)


SYNTHESIS_INSTRUCTION = (
    "Synthesize the experts' judgments into a single final judgment - but only after "
    "explicitly working through the substantive disagreements. Where perspectives diverge, "
    "do not split the difference: weigh the evidence and arguments and decide. Score each "
    "dimension on integer 1-5; `average` is the mean. In `synthesis`, name the key "
    "disagreements and how each was resolved. In `uncertainty`, name disagreements that "
    "remain unresolved even after deliberation."
)


CONFLICT_DETECTION_INSTRUCTION = (
    "Compare the experts' judgments. Identify dimensions where scores diverge by more than "
    "1 point, and the substantive disagreement behind each divergence. Under the constructive "
    "controversy mechanism, do not paper over conflicts: name them sharply and route a "
    "challenging question to the expert most responsible for the divergence, so the position "
    "is tested before any synthesis."
)
