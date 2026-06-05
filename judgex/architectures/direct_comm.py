"""Direct Communication architecture (spec §4.3).

Three layers:
  Layer 1: A1-A6 (cluster 1 = {A1, A2, A3}, cluster 2 = {A4, A5, A6}).
           Within a cluster, agents communicate directly. Spec marks A4's cluster
           assignment as an open ANNAHME; we follow the documented routing.
  Layer 2: Two Summarizers S1, S2. S1 aggregates A1-A3, S2 aggregates A4-A6.
  Layer 3: Decisioner E synthesizes S1 + S2 into the FinalJudgment.

Baseline flow:
  Phase 1a: each agent posts an initial AgentJudgment (no peer info).
  Phase 1b: each agent reads its two cluster-peers' initial judgments and posts
            a revised AgentJudgment.
  Phase 2:  S1 and S2 produce cluster summaries (using the FinalJudgment schema,
            with contributing_agents scoped to the cluster).
  Phase 3:  E produces the overall FinalJudgment from S1 + S2.
"""
from __future__ import annotations

import json
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from judgex.architectures.centralized import INTEGRATION_ORIENTED, Mechanism
from judgex.llm import LLMProvider
from judgex.personas import PERSONAS, Persona
from judgex.runtime import call_model
from judgex.schemas import AgentJudgment, FinalJudgment, PersonaId

CLUSTER_1: tuple[PersonaId, ...] = ("A1", "A2", "A3")
CLUSTER_2: tuple[PersonaId, ...] = ("A4", "A5", "A6")


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


class DirectCommState(TypedDict, total=False):
    proposal_id: str
    proposal_text: str
    initial_judgments: dict[str, dict[str, Any]]   # persona_id -> AgentJudgment dump
    revised_judgments: dict[str, dict[str, Any]]   # persona_id -> AgentJudgment dump (post peer)
    cluster_summaries: dict[str, dict[str, Any]]   # "S1" / "S2" -> FinalJudgment dump
    final: dict[str, Any]
    trace: list[dict[str, Any]]


def _log(state: DirectCommState, event: str, payload: dict[str, Any]) -> None:
    state.setdefault("trace", []).append({"event": event, **payload})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _persona_system_initial(persona: Persona, mechanism: Mechanism) -> str:
    cluster = "cluster 1 (A1, A2, A3)" if persona.id in CLUSTER_1 else "cluster 2 (A4, A5, A6)"
    return (
        persona.system_prompt()
        + f"\n\nYou are in {cluster}. After this initial pass you will see your two cluster-peers' "
        "judgments and may revise yours.\n"
        + mechanism.persona_preamble
    )


def _persona_system_revised(persona: Persona, mechanism: Mechanism) -> str:
    return (
        persona.system_prompt()
        + "\n\nYou have just read your two cluster-peers' initial judgments. "
        "Update your judgment if the peer information genuinely changes it; otherwise restate.\n"
        + mechanism.persona_preamble
    )


def _initial_user(proposal_text: str, mechanism: Mechanism) -> str:
    return (
        f"PROPOSAL:\n{proposal_text}\n\n"
        f"{mechanism.individual_judgment_instruction}\n\n"
        "Return your initial AgentJudgment from your persona's lens."
    )


def _revised_user(proposal_text: str, peer_blob: str, mechanism: Mechanism) -> str:
    return (
        f"PROPOSAL:\n{proposal_text}\n\n"
        f"YOUR CLUSTER PEERS' INITIAL JUDGMENTS:\n{peer_blob}\n\n"
        f"{mechanism.clarification_agent_instruction}\n\n"
        "Return your revised AgentJudgment. Keep your persona's lens; update scores only "
        "where the peer information actually warrants it."
    )


def _summarizer_system(summarizer_id: str, cluster: tuple[PersonaId, ...], mechanism: Mechanism) -> str:
    cluster_str = ", ".join(cluster)
    return (
        f"You are {summarizer_id}, a neutral Summarizer for cluster ({cluster_str}). "
        "You have no domain perspective of your own. Aggregate the cluster's revised "
        "judgments into a single summary judgment for the cluster.\n\n"
        + mechanism.persona_preamble
    )


def _summarizer_user(
    summarizer_id: str,
    cluster: tuple[PersonaId, ...],
    proposal_text: str,
    revised: dict[str, dict[str, Any]],
    mechanism: Mechanism,
) -> str:
    judgments_blob = json.dumps({pid: revised[pid] for pid in cluster}, indent=2)
    return (
        f"PROPOSAL:\n{proposal_text}\n\n"
        f"REVISED JUDGMENTS FROM {summarizer_id}'s CLUSTER ({', '.join(cluster)}):\n"
        f"{judgments_blob}\n\n"
        f"{mechanism.synthesis_instruction}\n\n"
        "Return a FinalJudgment object representing the cluster's aggregated view. "
        "`contributing_agents` will be set automatically; focus on rationale and uncertainty."
    )


def _decisioner_system(mechanism: Mechanism) -> str:
    return (
        "You are E, the Decisioner. You have no domain perspective of your own. "
        "You receive cluster summaries from S1 (A1-A3) and S2 (A4-A6) and produce the "
        "single overall final judgment of the proposal.\n\n"
        + mechanism.persona_preamble
    )


def _decisioner_user(
    proposal_text: str,
    s1: dict[str, Any],
    s2: dict[str, Any],
    mechanism: Mechanism,
) -> str:
    blob = json.dumps({"S1_cluster_summary": s1, "S2_cluster_summary": s2}, indent=2)
    return (
        f"PROPOSAL:\n{proposal_text}\n\n"
        f"CLUSTER SUMMARIES:\n{blob}\n\n"
        f"{mechanism.synthesis_instruction}\n\n"
        "Return the final FinalJudgment object. Where the two clusters diverge, decide and "
        "name the trade-off you made in the `uncertainty` field."
    )


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


def _node_initial(provider: LLMProvider, mechanism: Mechanism):
    def node(state: DirectCommState) -> DirectCommState:
        initial: dict[str, dict[str, Any]] = {}
        for pid in CLUSTER_1 + CLUSTER_2:
            persona = PERSONAS[pid]
            validated, _ = call_model(
                provider=provider,
                system=_persona_system_initial(persona, mechanism),
                user=_initial_user(state["proposal_text"], mechanism),
                response_model=AgentJudgment,
                overrides={
                    "persona_id": persona.id,
                    "proposal_id": state["proposal_id"],
                },
            )
            initial[pid] = validated.model_dump()
        state["initial_judgments"] = initial
        _log(state, "direct_initial", {"n_initial": len(initial)})
        return state

    return node


def _node_peer_exchange(provider: LLMProvider, mechanism: Mechanism):
    def node(state: DirectCommState) -> DirectCommState:
        revised: dict[str, dict[str, Any]] = {}
        for cluster in (CLUSTER_1, CLUSTER_2):
            for pid in cluster:
                persona = PERSONAS[pid]
                peers = [p for p in cluster if p != pid]
                peer_blob = json.dumps(
                    {p: state["initial_judgments"][p] for p in peers}, indent=2
                )
                validated, _ = call_model(
                    provider=provider,
                    system=_persona_system_revised(persona, mechanism),
                    user=_revised_user(state["proposal_text"], peer_blob, mechanism),
                    response_model=AgentJudgment,
                    overrides={
                        "persona_id": persona.id,
                        "proposal_id": state["proposal_id"],
                    },
                )
                revised[pid] = validated.model_dump()
        state["revised_judgments"] = revised
        _log(state, "direct_peer_exchange", {"n_revised": len(revised)})
        return state

    return node


def _node_summarizers(provider: LLMProvider, mechanism: Mechanism):
    def node(state: DirectCommState) -> DirectCommState:
        summaries: dict[str, dict[str, Any]] = {}
        for summarizer_id, cluster in (("S1", CLUSTER_1), ("S2", CLUSTER_2)):
            validated, _ = call_model(
                provider=provider,
                system=_summarizer_system(summarizer_id, cluster, mechanism),
                user=_summarizer_user(
                    summarizer_id,
                    cluster,
                    state["proposal_text"],
                    state["revised_judgments"],
                    mechanism,
                ),
                response_model=FinalJudgment,
                overrides={
                    "proposal_id": state["proposal_id"],
                    "contributing_agents": list(cluster),
                },
            )
            dims = [
                validated.feasibility.score,
                validated.novelty.score,
                validated.impact.score,
                validated.presentation.score,
            ]
            out = validated.model_dump()
            out["average"] = round(sum(dims) / 4.0, 3)
            summaries[summarizer_id] = out
        state["cluster_summaries"] = summaries
        _log(state, "direct_summarizers", {"summaries": list(summaries.keys())})
        return state

    return node


def _node_decisioner(provider: LLMProvider, mechanism: Mechanism):
    def node(state: DirectCommState) -> DirectCommState:
        s1 = state["cluster_summaries"]["S1"]
        s2 = state["cluster_summaries"]["S2"]
        validated, _ = call_model(
            provider=provider,
            system=_decisioner_system(mechanism),
            user=_decisioner_user(state["proposal_text"], s1, s2, mechanism),
            response_model=FinalJudgment,
            overrides={
                "proposal_id": state["proposal_id"],
                "contributing_agents": list(CLUSTER_1 + CLUSTER_2),
            },
        )
        dims = [
            validated.feasibility.score,
            validated.novelty.score,
            validated.impact.score,
            validated.presentation.score,
        ]
        out = validated.model_dump()
        out["average"] = round(sum(dims) / 4.0, 3)
        state["final"] = out
        _log(state, "direct_decisioner", {"average": out["average"]})
        return state

    return node


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_direct_comm_graph(provider: LLMProvider, mechanism: Mechanism = INTEGRATION_ORIENTED):
    g = StateGraph(DirectCommState)
    g.add_node("initial", _node_initial(provider, mechanism))
    g.add_node("peer_exchange", _node_peer_exchange(provider, mechanism))
    g.add_node("summarizers", _node_summarizers(provider, mechanism))
    g.add_node("decisioner", _node_decisioner(provider, mechanism))

    g.set_entry_point("initial")
    g.add_edge("initial", "peer_exchange")
    g.add_edge("peer_exchange", "summarizers")
    g.add_edge("summarizers", "decisioner")
    g.add_edge("decisioner", END)
    return g.compile()


def run_direct_comm(
    provider: LLMProvider,
    proposal_id: str,
    proposal_text: str,
    mechanism: Mechanism = INTEGRATION_ORIENTED,
) -> DirectCommState:
    graph = build_direct_comm_graph(provider, mechanism)
    initial: DirectCommState = {
        "proposal_id": proposal_id,
        "proposal_text": proposal_text,
        "trace": [],
    }
    result = graph.invoke(initial)
    return result  # type: ignore[return-value]
