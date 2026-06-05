"""Shared Message Pool architecture (spec §4.2).

Topology: A1-A6 read and write a shared structured working memory (the pool).
Two neutral coordination roles:
  - Pool Curator: filters, bundles, clusters pool contributions.
  - Final Pool Summarizer / Judge: produces the final judgment from clustered contributions.

The agents themselves never address one specific peer; they read the whole pool
and decide what to add.

Two-round baseline:
  Round 1: every persona writes an initial structured AgentJudgment into the pool.
  Round 2: every persona reads the pool and posts a PoolReaction (text + optional
           revised scores). Peer-aware refinement.
Then Curator -> Judge.
"""
from __future__ import annotations

import json
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from judgex.architectures.centralized import (
    INTEGRATION_ORIENTED,
    Mechanism,
)
from judgex.llm import LLMProvider
from judgex.personas import Persona, all_personas
from judgex.runtime import call_model
from judgex.schemas import AgentJudgment, ClusterReport, FinalJudgment, PoolReaction


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


class SharedPoolState(TypedDict, total=False):
    proposal_id: str
    proposal_text: str
    pool_round1: dict[str, dict[str, Any]]  # persona_id -> AgentJudgment dump
    pool_round2: dict[str, dict[str, Any]]  # persona_id -> PoolReaction dump
    judgments: dict[str, dict[str, Any]]    # final per-persona judgment (round1 + round2 revisions)
    clusters: list[dict[str, Any]]
    open_questions: list[str]
    final: dict[str, Any]
    trace: list[dict[str, Any]]


def _log(state: SharedPoolState, event: str, payload: dict[str, Any]) -> None:
    state.setdefault("trace", []).append({"event": event, **payload})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _persona_system(persona: Persona, mechanism: Mechanism) -> str:
    return (
        persona.system_prompt()
        + "\n\nYou are working in a shared message pool: every other expert can read what you write.\n"
        + mechanism.persona_preamble
    )


def _round1_user(proposal_text: str, mechanism: Mechanism) -> str:
    return (
        f"PROPOSAL:\n{proposal_text}\n\n"
        "Round 1: post your initial structured judgment to the shared pool. "
        "Nothing is in the pool yet; this is your unmediated take from your persona's lens.\n\n"
        f"{mechanism.individual_judgment_instruction}"
    )


def _round2_user(proposal_text: str, pool_blob: str, mechanism: Mechanism) -> str:
    return (
        f"PROPOSAL:\n{proposal_text}\n\n"
        f"POOL (round 1, all six experts):\n{pool_blob}\n\n"
        "Round 2: read the pool and post a concise reaction. "
        "What do other perspectives add, or where do you qualify your earlier judgment? "
        "If reading the pool genuinely changes any of your dimension scores, include them in "
        "`revised_scores`; otherwise leave that field empty.\n\n"
        + mechanism.persona_preamble
    )


def _curator_system(mechanism: Mechanism) -> str:
    return (
        "You are the Pool Curator: a neutral coordination role with no domain perspective of "
        "your own. Your job is to filter, bundle, and cluster the experts' pool contributions "
        "so the final judge can synthesize efficiently.\n\n"
        + mechanism.persona_preamble
    )


def _judge_system(mechanism: Mechanism) -> str:
    return (
        "You are the Final Pool Summarizer / Judge: a neutral synthesis role with no domain "
        "perspective of your own. You produce the single final judgment of the proposal from "
        "the clustered pool contents.\n\n"
        + mechanism.persona_preamble
    )


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------


def _node_round1(provider: LLMProvider, mechanism: Mechanism):
    def node(state: SharedPoolState) -> SharedPoolState:
        contributions: dict[str, dict[str, Any]] = {}
        for persona in all_personas():
            validated, _ = call_model(
                provider=provider,
                system=_persona_system(persona, mechanism),
                user=_round1_user(state["proposal_text"], mechanism),
                response_model=AgentJudgment,
                overrides={
                    "persona_id": persona.id,
                    "proposal_id": state["proposal_id"],
                },
            )
            contributions[persona.id] = validated.model_dump()
        state["pool_round1"] = contributions
        _log(state, "shared_round1", {"n_contributions": len(contributions)})
        return state

    return node


def _node_round2(provider: LLMProvider, mechanism: Mechanism):
    def node(state: SharedPoolState) -> SharedPoolState:
        pool_blob = json.dumps(state["pool_round1"], indent=2)
        reactions: dict[str, dict[str, Any]] = {}
        # Merge round-1 judgments and apply revisions in round 2.
        merged_judgments: dict[str, dict[str, Any]] = {
            pid: dict(judg) for pid, judg in state["pool_round1"].items()
        }
        for persona in all_personas():
            validated, _ = call_model(
                provider=provider,
                system=_persona_system(persona, mechanism),
                user=_round2_user(state["proposal_text"], pool_blob, mechanism),
                response_model=PoolReaction,
                overrides={"persona_id": persona.id},
            )
            reactions[persona.id] = validated.model_dump()
            revised = validated.revised_scores or {}
            for dim, score in revised.items():
                if dim in merged_judgments[persona.id] and isinstance(
                    merged_judgments[persona.id][dim], dict
                ):
                    merged_judgments[persona.id][dim]["score"] = int(score)
        state["pool_round2"] = reactions
        state["judgments"] = merged_judgments
        _log(state, "shared_round2", {"n_reactions": len(reactions)})
        return state

    return node


def _node_curator(provider: LLMProvider, mechanism: Mechanism):
    def node(state: SharedPoolState) -> SharedPoolState:
        pool_blob = json.dumps(
            {
                "round1_judgments": state["pool_round1"],
                "round2_reactions": state["pool_round2"],
            },
            indent=2,
        )
        user = (
            f"PROPOSAL (for context):\n{state['proposal_text'][:4000]}...\n\n"
            f"POOL CONTENTS:\n{pool_blob}\n\n"
            "Cluster the pool contributions into a small number of coherent themes "
            "(typically 3-6). For each cluster, give a label, a summary, the contributing "
            "personas, and which evaluation dimensions it touches. Also list open questions "
            "the experts implicitly left unresolved.\n\n"
            f"{mechanism.conflict_detection_instruction}"
        )
        report, _ = call_model(
            provider=provider,
            system=_curator_system(mechanism),
            user=user,
            response_model=ClusterReport,
        )
        state["clusters"] = [c.model_dump() for c in report.clusters]
        state["open_questions"] = list(report.open_questions)
        _log(
            state,
            "shared_curator",
            {
                "n_clusters": len(state["clusters"]),
                "n_open_questions": len(state["open_questions"]),
            },
        )
        return state

    return node


def _node_judge(provider: LLMProvider, mechanism: Mechanism):
    def node(state: SharedPoolState) -> SharedPoolState:
        body = json.dumps(
            {
                "merged_judgments": state["judgments"],
                "clusters": state["clusters"],
                "open_questions": state["open_questions"],
            },
            indent=2,
        )
        user = (
            f"PROPOSAL:\n{state['proposal_text']}\n\n"
            f"POOL ANALYSIS:\n{body}\n\n"
            f"{mechanism.synthesis_instruction}\n\n"
            "Return a FinalJudgment object."
        )
        contributing = list(state["judgments"].keys())
        validated, _ = call_model(
            provider=provider,
            system=_judge_system(mechanism),
            user=user,
            response_model=FinalJudgment,
            overrides={
                "proposal_id": state["proposal_id"],
                "contributing_agents": contributing,
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
        _log(state, "shared_judge", {"average": out["average"]})
        return state

    return node


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_shared_pool_graph(provider: LLMProvider, mechanism: Mechanism = INTEGRATION_ORIENTED):
    g = StateGraph(SharedPoolState)
    g.add_node("round1", _node_round1(provider, mechanism))
    g.add_node("round2", _node_round2(provider, mechanism))
    g.add_node("curator", _node_curator(provider, mechanism))
    g.add_node("judge", _node_judge(provider, mechanism))

    g.set_entry_point("round1")
    g.add_edge("round1", "round2")
    g.add_edge("round2", "curator")
    g.add_edge("curator", "judge")
    g.add_edge("judge", END)
    return g.compile()


def run_shared_pool(
    provider: LLMProvider,
    proposal_id: str,
    proposal_text: str,
    mechanism: Mechanism = INTEGRATION_ORIENTED,
) -> SharedPoolState:
    graph = build_shared_pool_graph(provider, mechanism)
    initial: SharedPoolState = {
        "proposal_id": proposal_id,
        "proposal_text": proposal_text,
        "trace": [],
    }
    result = graph.invoke(initial)
    return result  # type: ignore[return-value]
