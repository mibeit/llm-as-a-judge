"""Smoke-test runner.

Dumps per-proposal JSON traces and a summary CSV (MAS scores vs. jury averages).

Usage:
    python -m scripts.run_smoke --provider mock
    python -m scripts.run_smoke --provider anthropic --architecture shared_pool --mechanism constructive_controversy
    python -m scripts.run_smoke --provider openai_compatible   # uses JUDGEX_BASE_URL + JUDGEX_MODEL
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from judgex.architectures.centralized import MECHANISMS, run_centralized
from judgex.architectures.direct_comm import run_direct_comm
from judgex.architectures.shared_pool import run_shared_pool
from judgex.data import ContestName, load_jury, proposals_for_contest
from judgex.llm import get_provider

ARCHITECTURES = {
    "centralized": run_centralized,
    "shared_pool": run_shared_pool,
    "direct_comm": run_direct_comm,
}

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNS_ROOT = REPO_ROOT / "runs"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--provider",
        choices=["mock", "anthropic", "openai_compatible"],
        default="mock",
        help=(
            "anthropic: Claude via Anthropic SDK. "
            "openai_compatible: OpenAI proper or any OpenAI-compatible endpoint "
            "(vLLM, Ollama, university cluster) - configured via JUDGEX_BASE_URL + "
            "JUDGEX_API_KEY + JUDGEX_MODEL in .env."
        ),
    )
    parser.add_argument(
        "--contest",
        choices=["Behavior", "Adaptation", "LandUse", "Energy"],
        default="Behavior",
    )
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument(
        "--architecture",
        choices=list(ARCHITECTURES.keys()),
        default="centralized",
    )
    parser.add_argument(
        "--mechanism",
        choices=list(MECHANISMS.keys()),
        default="integration_oriented",
    )
    args = parser.parse_args()

    load_dotenv()
    provider = get_provider(args.provider)
    contest: ContestName = args.contest  # type: ignore[assignment]
    print(f"[provider] {provider.name}  model={provider.model}", flush=True)

    proposals = proposals_for_contest(contest, limit=args.limit)
    jury = load_jury()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = RUNS_ROOT / f"{timestamp}_{args.architecture}_{args.mechanism}_{args.provider}_{contest}"
    run_dir.mkdir(parents=True, exist_ok=True)

    run_fn = ARCHITECTURES[args.architecture]
    mechanism = MECHANISMS[args.mechanism]
    summary_rows: list[dict[str, object]] = []
    for p in proposals:
        print(
            f"[run] {p.proposal_id} ({contest})  arch={args.architecture}  "
            f"mech={args.mechanism}  provider={args.provider}",
            flush=True,
        )
        state = run_fn(
            provider,
            proposal_id=p.proposal_id,
            proposal_text=p.text,
            mechanism=mechanism,
        )
        out_path = run_dir / f"{p.proposal_id}.json"
        out_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

        final = state["final"]
        j = jury.get(p.proposal_id)
        summary_rows.append(
            {
                "proposal_id": p.proposal_id,
                "contest": contest,
                "mas_feasibility": final["feasibility"]["score"],
                "mas_novelty": final["novelty"]["score"],
                "mas_impact": final["impact"]["score"],
                "mas_presentation": final["presentation"]["score"],
                "mas_average": final["average"],
                "jury_feasibility": j.feasibility if j else None,
                "jury_novelty": j.novelty if j else None,
                "jury_impact": j.impact if j else None,
                "jury_presentation": j.presentation if j else None,
                "jury_average": j.average if j else None,
                "title": j.title if j else None,
            }
        )

    summary_path = run_dir / "summary.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    print(f"[done] {len(summary_rows)} proposals  ->  {run_dir}")


if __name__ == "__main__":
    main()
