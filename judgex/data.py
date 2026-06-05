"""Loaders for proposals and the human jury ground truth."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import openpyxl

ContestName = Literal["Behavior", "Adaptation", "LandUse", "Energy"]

# Excel "Contest" column -> data subdirectory name
CONTEST_DIRS: dict[ContestName, str] = {
    "Behavior": "C1-Behavior",
    "Adaptation": "C2-Adaptation",
    "LandUse": "C3-LandUse",
    "Energy": "C4-Energy",
}

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = REPO_ROOT / "data"
JURY_XLSX = DATA_ROOT / "Jury Bewertungen.xlsx"


@dataclass(frozen=True)
class Proposal:
    proposal_id: str
    contest: ContestName
    text: str
    path: Path


@dataclass(frozen=True)
class JuryScore:
    proposal_id: str
    contest: ContestName
    title: str
    author: str
    average: float
    feasibility: float
    novelty: float
    impact: float
    presentation: float


def load_proposal(contest: ContestName, proposal_id: str | int) -> Proposal:
    pid = str(proposal_id)
    path = DATA_ROOT / CONTEST_DIRS[contest] / f"{pid}.txt"
    text = path.read_text(encoding="utf-8")
    return Proposal(proposal_id=pid, contest=contest, text=text, path=path)


def list_proposals(contest: ContestName) -> list[str]:
    folder = DATA_ROOT / CONTEST_DIRS[contest]
    return sorted(p.stem for p in folder.glob("*.txt"))


def load_jury() -> dict[str, JuryScore]:
    """Read the jury workbook, keyed by proposal_id (string)."""
    wb = openpyxl.load_workbook(JURY_XLSX, data_only=True)
    ws = wb["Tabelle1"]
    rows = list(ws.iter_rows(values_only=True))
    header = rows[0]
    # Sanity: expected layout per inspection
    expected = ("Contest", "Proposal title", "Author/Team name", None, "Proposal URL")
    if header[: len(expected)] != expected:
        raise RuntimeError(f"Unexpected jury sheet header: {header[:6]}")

    out: dict[str, JuryScore] = {}
    for r in rows[1:]:
        contest, title, author, _, pid_raw, _url, _phase, _judge, avg, feas, nov, imp, pres = r
        if pid_raw is None:
            continue
        pid = str(pid_raw)
        out[pid] = JuryScore(
            proposal_id=pid,
            contest=contest,
            title=title,
            author=author,
            average=float(avg),
            feasibility=float(feas),
            novelty=float(nov),
            impact=float(imp),
            presentation=float(pres),
        )
    return out


def proposals_for_contest(contest: ContestName, limit: int | None = None) -> list[Proposal]:
    ids = list_proposals(contest)
    if limit is not None:
        ids = ids[:limit]
    return [load_proposal(contest, pid) for pid in ids]
