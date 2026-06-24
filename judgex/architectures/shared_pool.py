"""Shared Message Pool architecture (spec §4.2).

Topology: A1-A6 read and write a shared structured working memory (the pool).
Two neutral coordination roles:
  - Pool Curator: filters, bundles, clusters pool contributions.
  - Final Pool Summarizer / Judge: produces the final judgment from clustered contributions.

The agents themselves never address one specific peer; they read the whole pool
and decide what to add.

Flow (Curator moderates from the middle, not just at the end):
  Round 1:        every persona writes an initial structured AgentJudgment into the pool.
  Curator (early): clusters round 1, surfaces conflicts and open questions, posts them
                   back into the pool.
  Round 2 (Q&A):  every persona reads the pool + the curator's open questions, answers
                  what it can, may raise its own questions to the pool, and may revise
                  scores (PoolReaction).
  Round 3:        every persona answers the questions raised in round 2 and settles its
                  position (last exchange before synthesis); may revise scores.
  Curator (final): re-clusters the full pool (rounds 1-3).
  Judge:          produces the final judgment from the clustered pool.
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
    pool_round3: dict[str, dict[str, Any]]  # persona_id -> PoolReaction dump
    pool_questions: list[dict[str, Any]]    # questions raised by experts in round 2
    early_clusters: list[dict[str, Any]]    # Curator's early clustering of round 1
    early_open_questions: list[str]         # open questions posted back into the pool
    judgments: dict[str, dict[str, Any]]    # final per-persona judgment (round1 + round2/3 revisions)
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


def _round2_user(
    proposal_text: str, pool_blob: str, open_questions_blob: str, mechanism: Mechanism
) -> str:
    return (
        f"PROPOSAL:\n{proposal_text}\n\n"
        f"POOL (round 1, all six experts):\n{pool_blob}\n\n"
        f"OPEN QUESTIONS RAISED BY THE CURATOR:\n{open_questions_blob}\n\n"
        "Round 2: read the pool and the curator's open questions, then post a concise "
        "reaction. Address any open question you can speak to from your lens, and say what "
        "other perspectives add or where you qualify your earlier judgment. You may also "
        "raise your own questions to the pool (in `questions`) for the other experts to pick "
        "up next round; leave it empty if you have none. "
        "If reading the pool genuinely changes any of your dimension scores, include them in "
        "`revised_scores`; otherwise leave that field empty.\n\n"
        + mechanism.persona_preamble
    )


def _round3_user(
    proposal_text: str, pool_blob: str, questions_blob: str, mechanism: Mechanism
) -> str:
    return (
        f"PROPOSAL:\n{proposal_text}\n\n"
        f"POOL SO FAR (round 1 judgments + round 2 reactions):\n{pool_blob}\n\n"
        f"OPEN QUESTIONS RAISED BY EXPERTS IN ROUND 2:\n{questions_blob}\n\n"
        "Round 3 (final exchange before synthesis): answer the round-2 questions you can "
        "speak to from your lens and settle your position. You do not need to raise new "
        "questions now. If the discussion genuinely changes any of your dimension scores, "
        "include them in `revised_scores`; otherwise leave that field empty.\n\n"
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


def _node_curator_early(provider: LLMProvider, mechanism: Mechanism):
    """Curator runs early: cluster round 1 and post open questions back into the pool."""

    def node(state: SharedPoolState) -> SharedPoolState:
        pool_blob = json.dumps(state["pool_round1"], indent=2)
        user = (
            f"PROPOSAL (for context):\n{state['proposal_text'][:4000]}...\n\n"
            f"POOL CONTENTS (round 1 initial judgments):\n{pool_blob}\n\n"
            "Cluster the round-1 contributions into a small number of coherent themes "
            "(typically 3-6). For each cluster, give a label, a summary, the contributing "
            "personas, and which evaluation dimensions it touches. Then list the open "
            "questions the experts implicitly left unresolved - these will be posted back "
            "into the pool for the experts to address in the next round.\n\n"
            f"{mechanism.conflict_detection_instruction}"
        )
        report, _ = call_model(
            provider=provider,
            system=_curator_system(mechanism),
            user=user,
            response_model=ClusterReport,
        )
        state["early_clusters"] = [c.model_dump() for c in report.clusters]
        state["early_open_questions"] = list(report.open_questions)
        _log(
            state,
            "shared_curator_early",
            {
                "n_clusters": len(state["early_clusters"]),
                "n_open_questions": len(state["early_open_questions"]),
            },
        )
        return state

    return node


def _node_round2(provider: LLMProvider, mechanism: Mechanism):
    def node(state: SharedPoolState) -> SharedPoolState:
        pool_blob = json.dumps(state["pool_round1"], indent=2)
        open_questions_blob = json.dumps(state.get("early_open_questions", []), indent=2)
        reactions: dict[str, dict[str, Any]] = {}
        pool_questions: list[dict[str, Any]] = []
        # Merge round-1 judgments and apply revisions in round 2.
        merged_judgments: dict[str, dict[str, Any]] = {
            pid: dict(judg) for pid, judg in state["pool_round1"].items()
        }
        for persona in all_personas():
            validated, _ = call_model(
                provider=provider,
                system=_persona_system(persona, mechanism),
                user=_round2_user(
                    state["proposal_text"], pool_blob, open_questions_blob, mechanism
                ),
                response_model=PoolReaction,
                overrides={"persona_id": persona.id},
            )
            reactions[persona.id] = validated.model_dump()
            for q in validated.questions or []:
                pool_questions.append({"from_persona": persona.id, "question": q})
            revised = validated.revised_scores or {}
            for dim, score in revised.items():
                if dim in merged_judgments[persona.id] and isinstance(
                    merged_judgments[persona.id][dim], dict
                ):
                    merged_judgments[persona.id][dim]["score"] = int(score)
        state["pool_round2"] = reactions
        state["pool_questions"] = pool_questions
        state["judgments"] = merged_judgments
        _log(
            state,
            "shared_round2",
            {"n_reactions": len(reactions), "n_questions": len(pool_questions)},
        )
        return state

    return node


def _node_round3(provider: LLMProvider, mechanism: Mechanism):
    def node(state: SharedPoolState) -> SharedPoolState:
        pool_blob = json.dumps(
            {
                "round1_judgments": state["pool_round1"],
                "round2_reactions": state["pool_round2"],
            },
            indent=2,
        )
        questions_blob = json.dumps(state.get("pool_questions", []), indent=2)
        reactions: dict[str, dict[str, Any]] = {}
        # Carry the round-2 merged judgments forward and apply round-3 revisions on top.
        merged_judgments: dict[str, dict[str, Any]] = {
            pid: dict(judg) for pid, judg in state["judgments"].items()
        }
        for persona in all_personas():
            validated, _ = call_model(
                provider=provider,
                system=_persona_system(persona, mechanism),
                user=_round3_user(state["proposal_text"], pool_blob, questions_blob, mechanism),
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
        state["pool_round3"] = reactions
        state["judgments"] = merged_judgments
        _log(state, "shared_round3", {"n_reactions": len(reactions)})
        return state

    return node


def _node_curator_final(provider: LLMProvider, mechanism: Mechanism):
    """Final curator pass: re-cluster the full pool (rounds 1-3) for the judge."""

    def node(state: SharedPoolState) -> SharedPoolState:
        pool_blob = json.dumps(
            {
                "round1_judgments": state["pool_round1"],
                "round2_reactions": state["pool_round2"],
                "round3_reactions": state["pool_round3"],
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
            "shared_curator_final",
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
    g.add_node("curator_early", _node_curator_early(provider, mechanism))
    g.add_node("round2", _node_round2(provider, mechanism))
    g.add_node("round3", _node_round3(provider, mechanism))
    g.add_node("curator_final", _node_curator_final(provider, mechanism))
    g.add_node("judge", _node_judge(provider, mechanism))

    g.set_entry_point("round1")
    g.add_edge("round1", "curator_early")
    g.add_edge("curator_early", "round2")
    g.add_edge("round2", "round3")
    g.add_edge("round3", "curator_final")
    g.add_edge("curator_final", "judge")
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
