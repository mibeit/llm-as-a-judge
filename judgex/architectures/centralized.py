"""Centralized architecture (spec §4.1).

Topology: star. C0 orchestrates; A1-A6 never talk to each other directly.

Five phases:
  1. Task Distribution      - C0 fans the proposal out to all six personas.
  2. Specialist Judgments   - A1..A6 each return a structured AgentJudgment.
  3. Conflict Detection     - C0 inspects all judgments, surfaces divergences.
  4. Targeted Clarification - C0 routes pointed questions to relevant personas; they revise.
  5. Final Synthesis        - C0 produces the final FinalJudgment.

The mechanism (integration-oriented / constructive controversy) is injected as
prompt scaffolding; the graph topology stays identical.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from judgex.llm import LLMProvider
from judgex.mechanisms import constructive_controversy as cc_mech
from judgex.mechanisms import integration as integration_mech
from judgex.personas import PERSONAS, Persona, all_personas
from judgex.runtime import call_model
from judgex.schemas import (
    AgentJudgment,
    ClarificationResponse,
    ConflictReport,
    FinalJudgment,
    PersonaId,
)


# ---------------------------------------------------------------------------
# Mechanism binding
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Mechanism:
    name: str
    persona_preamble: str
    individual_judgment_instruction: str
    clarification_agent_instruction: str
    synthesis_instruction: str
    conflict_detection_instruction: str


INTEGRATION_ORIENTED = Mechanism(
    name=integration_mech.MECHANISM_NAME,
    persona_preamble=integration_mech.PERSONA_PREAMBLE,
    individual_judgment_instruction=integration_mech.INDIVIDUAL_JUDGMENT_INSTRUCTION,
    clarification_agent_instruction=integration_mech.CLARIFICATION_AGENT_INSTRUCTION,
    synthesis_instruction=integration_mech.SYNTHESIS_INSTRUCTION,
    conflict_detection_instruction=integration_mech.CONFLICT_DETECTION_INSTRUCTION,
)

CONSTRUCTIVE_CONTROVERSY = Mechanism(
    name=cc_mech.MECHANISM_NAME,
    persona_preamble=cc_mech.PERSONA_PREAMBLE,
    individual_judgment_instruction=cc_mech.INDIVIDUAL_JUDGMENT_INSTRUCTION,
    clarification_agent_instruction=cc_mech.CLARIFICATION_AGENT_INSTRUCTION,
    synthesis_instruction=cc_mech.SYNTHESIS_INSTRUCTION,
    conflict_detection_instruction=cc_mech.CONFLICT_DETECTION_INSTRUCTION,
)


MECHANISMS: dict[str, Mechanism] = {
    INTEGRATION_ORIENTED.name: INTEGRATION_ORIENTED,
    CONSTRUCTIVE_CONTROVERSY.name: CONSTRUCTIVE_CONTROVERSY,
}


# ---------------------------------------------------------------------------
# Graph state
# ---------------------------------------------------------------------------


class CentralizedState(TypedDict, total=False):
    proposal_id: str
    proposal_text: str
    judgments: dict[str, dict[str, Any]]  # persona_id -> AgentJudgment dump
    conflicts: list[dict[str, Any]]
    clarification_requests: list[dict[str, Any]]
    clarification_responses: list[dict[str, Any]]
    final: dict[str, Any]
    trace: list[dict[str, Any]]


def _log(state: CentralizedState, event: str, payload: dict[str, Any]) -> None:
    state.setdefault("trace", []).append({"event": event, **payload})


# ---------------------------------------------------------------------------
# Node implementations
# ---------------------------------------------------------------------------


def _persona_system(persona: Persona, mechanism: Mechanism) -> str:
    return (
        persona.system_prompt()
        + "\n\n"
        + mechanism.persona_preamble
    )


def _persona_judgment_user_msg(proposal_text: str, mechanism: Mechanism) -> str:
    return (
        f"PROPOSAL:\n{proposal_text}\n\n"
        f"{mechanism.individual_judgment_instruction}\n\n"
        "Return your judgment as a structured AgentJudgment object."
    )


def _make_phase1_distribute() -> Any:
    def node(state: CentralizedState) -> CentralizedState:
        _log(state, "phase1_distribute", {"persona_count": 6})
        return state

    return node


def _make_phase2_specialist(provider: LLMProvider, mechanism: Mechanism) -> Any:
    def node(state: CentralizedState) -> CentralizedState:
        judgments: dict[str, dict[str, Any]] = {}
        for persona in all_personas():
            system = _persona_system(persona, mechanism)
            user = _persona_judgment_user_msg(state["proposal_text"], mechanism)
            validated, _ = call_model(
                provider=provider,
                system=system,
                user=user,
                response_model=AgentJudgment,
                overrides={
                    "persona_id": persona.id,
                    "proposal_id": state["proposal_id"],
                },
            )
            judgments[persona.id] = validated.model_dump()
        state["judgments"] = judgments
        _log(state, "phase2_specialist_judgments", {"judgment_count": len(judgments)})
        return state

    return node


def _make_phase3_conflict(provider: LLMProvider, mechanism: Mechanism) -> Any:
    def node(state: CentralizedState) -> CentralizedState:
        judgments_blob = json.dumps(state["judgments"], indent=2)
        system = (
            "You are C0, the neutral central orchestrator. You do not have a domain "
            "perspective of your own; you coordinate the six specialist experts.\n\n"
            + mechanism.persona_preamble
        )
        user = (
            f"The six experts have produced these structured judgments:\n\n{judgments_blob}\n\n"
            f"{mechanism.conflict_detection_instruction}\n\n"
            "Return a ConflictReport object. Include only conflicts where you would "
            "actually benefit from a clarifying question to a specific expert. Each "
            "clarification_request must name exactly one persona."
        )
        report, _ = call_model(
            provider=provider,
            system=system,
            user=user,
            response_model=ConflictReport,
        )
        state["conflicts"] = [c.model_dump() for c in report.conflicts]
        state["clarification_requests"] = [r.model_dump() for r in report.clarification_requests]
        _log(
            state,
            "phase3_conflict_detection",
            {
                "n_conflicts": len(state["conflicts"]),
                "n_clarifications": len(state["clarification_requests"]),
            },
        )
        return state

    return node


def _make_phase4_clarify(provider: LLMProvider, mechanism: Mechanism) -> Any:
    def node(state: CentralizedState) -> CentralizedState:
        responses: list[dict[str, Any]] = []
        for req in state.get("clarification_requests", []):
            pid: PersonaId = req["persona_id"]  # type: ignore[assignment]
            persona = PERSONAS[pid]
            system = _persona_system(persona, mechanism)
            user = (
                f"Original proposal:\n{state['proposal_text']}\n\n"
                f"Your earlier judgment:\n{json.dumps(state['judgments'][pid], indent=2)}\n\n"
                f"Clarification question from the orchestrator:\n{req['question']}\n\n"
                f"{mechanism.clarification_agent_instruction}\n\n"
                "Return a ClarificationResponse. Only include `revised_scores` if your "
                "answer actually changes your earlier scores."
            )
            resp, _ = call_model(
                provider=provider,
                system=system,
                user=user,
                response_model=ClarificationResponse,
            )
            resp_dump = resp.model_dump()
            responses.append({"persona_id": pid, "question": req["question"], **resp_dump})
            # Apply revisions in-place so synthesis sees the updated scores.
            revised = resp_dump.get("revised_scores") or {}
            if revised:
                judg = state["judgments"][pid]
                for dim, score in revised.items():
                    if dim in judg and isinstance(judg[dim], dict):
                        judg[dim]["score"] = int(score)
        state["clarification_responses"] = responses
        _log(state, "phase4_targeted_clarification", {"n_responses": len(responses)})
        return state

    return node


def _make_phase5_synthesis(provider: LLMProvider, mechanism: Mechanism) -> Any:
    def node(state: CentralizedState) -> CentralizedState:
        judgments_blob = json.dumps(state["judgments"], indent=2)
        clarifications_blob = json.dumps(state.get("clarification_responses", []), indent=2)
        system = (
            "You are C0, the neutral central orchestrator. You synthesize the experts' "
            "judgments into a single final judgment. You have no domain perspective of your "
            "own.\n\n"
            + mechanism.persona_preamble
        )
        user = (
            f"PROPOSAL:\n{state['proposal_text']}\n\n"
            f"EXPERT JUDGMENTS (post-clarification):\n{judgments_blob}\n\n"
            f"CLARIFICATION EXCHANGES:\n{clarifications_blob}\n\n"
            f"{mechanism.synthesis_instruction}\n\n"
            "Return a FinalJudgment object. Set proposal_id and contributing_agents correctly."
        )
        contributing = list(state["judgments"].keys())
        validated, _ = call_model(
            provider=provider,
            system=system,
            user=user,
            response_model=FinalJudgment,
            overrides={
                "proposal_id": state["proposal_id"],
                "contributing_agents": contributing,
            },
        )
        # Recompute the average to keep it consistent with the four dimension scores.
        dims = [
            validated.feasibility.score,
            validated.novelty.score,
            validated.impact.score,
            validated.presentation.score,
        ]
        out = validated.model_dump()
        out["average"] = round(sum(dims) / 4.0, 3)
        state["final"] = out
        _log(state, "phase5_final_synthesis", {"average": out["average"]})
        return state

    return node


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_centralized_graph(provider: LLMProvider, mechanism: Mechanism = INTEGRATION_ORIENTED):
    g = StateGraph(CentralizedState)
    g.add_node("phase1_distribute", _make_phase1_distribute())
    g.add_node("phase2_specialist", _make_phase2_specialist(provider, mechanism))
    g.add_node("phase3_conflict", _make_phase3_conflict(provider, mechanism))
    g.add_node("phase4_clarify", _make_phase4_clarify(provider, mechanism))
    g.add_node("phase5_synthesis", _make_phase5_synthesis(provider, mechanism))

    g.set_entry_point("phase1_distribute")
    g.add_edge("phase1_distribute", "phase2_specialist")
    g.add_edge("phase2_specialist", "phase3_conflict")
    g.add_edge("phase3_conflict", "phase4_clarify")
    g.add_edge("phase4_clarify", "phase5_synthesis")
    g.add_edge("phase5_synthesis", END)
    return g.compile()


def run_centralized(
    provider: LLMProvider,
    proposal_id: str,
    proposal_text: str,
    mechanism: Mechanism = INTEGRATION_ORIENTED,
) -> CentralizedState:
    graph = build_centralized_graph(provider, mechanism)
    initial: CentralizedState = {
        "proposal_id": proposal_id,
        "proposal_text": proposal_text,
        "trace": [],
    }
    result = graph.invoke(initial)
    return result  # type: ignore[return-value]
