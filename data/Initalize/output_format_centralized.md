# Output-Format: Centralized Architektur

> Was in einer Run-JSON steht und wo die "Konversation" zwischen den Agenten zu finden ist.
> Stand: 2026-06-05 · gilt für `judgex/architectures/centralized.py`

---

## Wo liegen die Outputs?

Pro CLI-Aufruf wird ein neues Verzeichnis angelegt:

```
runs/<timestamp>_<architecture>_<mechanism>_<provider>_<contest>/
├── 1333002.json
├── 1333885.json
├── 1333894.json
└── summary.csv
```

- **Eine JSON pro Proposal** mit dem vollständigen Endzustand (Input + alle Zwischenschritte + Final + Trace).
- **Ein `summary.csv`** mit den finalen MAS-Scores neben den Jury-Scores.

---

## Top-Level-Struktur der Proposal-JSON

```jsonc
{
  "proposal_id":             "1333885",
  "proposal_text":           "Proposal number: 1333885 ...",   // 1. Input
  "judgments":               { "A1": {...}, ..., "A6": {...} }, // 2. Einzelurteile (Phase 2)
  "conflicts":               [ ... ],                          // 3a. C0's Konflikt-Befund (Phase 3)
  "clarification_requests":  [ ... ],                          // 3b. C0 -> Persona (Phase 3)
  "clarification_responses": [ ... ],                          // 3c. Persona -> C0 (Phase 4)
  "final":                   { ... },                          // 4. Endurteil (Phase 5)
  "trace":                   [ ... ]                           // 5. Phasen-Log
}
```

Die fünf Blöcke entsprechen direkt den 5 Phasen der Centralized-Architektur (siehe Spec §4.1).

---

## 1. `proposal_text` — der Input

Der unveränderte Original-Text aus `data/C{n}-{Contest}/{proposal_id}.txt`. Macht den Run für sich allein lesbar — du musst nicht in den Datensatz springen, um zu wissen, worauf sich die Urteile beziehen.

---

## 2. `judgments` — die sechs Einzelurteile (Phase 2)

Dict mit einem Eintrag pro Persona (`A1`…`A6`). Jeder Eintrag ist ein `AgentJudgment` (Pydantic, `judgex/schemas.py`):

```jsonc
"A1": {
  "persona_id":  "A1",
  "proposal_id": "1333885",
  "feasibility":  { "score": 3, "rationale": "The core mechanics — a one-day walk/cycle event ..." },
  "novelty":      { "score": 2, "rationale": "World Car-Free Day has existed since 2000 ..." },
  "impact":       { "score": 2, "rationale": "The short-term direct emissions savings are honestly modest ..." },
  "presentation": { "score": 2, "rationale": "Multiple typographical errors ('alogorithm') ..." },
  "perspective_summary": "From a scientific and systems perspective, the proposal describes a technically plausible short-term intervention ...",
  "key_concerns": [
    "The causal pathway from a one-day walk event to long-term policy outcomes ... is asserted without empirical evidence",
    "The 5% participation rate assumption is ungrounded ...",
    "Global extrapolation by simple population ratio ignores urban density ..."
  ],
  "confidence": 0.82
}
```

Felder:

| Feld | Typ | Bedeutung |
|---|---|---|
| `persona_id` | enum A1–A6 | Welche Persona dieses Urteil abgegeben hat. Vom Code erzwungen (überschreibt eventuellen LLM-Output). |
| `proposal_id` | str | Welches Proposal bewertet wurde. Vom Code erzwungen. |
| `feasibility` / `novelty` / `impact` / `presentation` | `{score: 1-5, rationale: str}` | Die vier Jury-Dimensionen. Integer-Score, Klartext-Rationale. |
| `perspective_summary` | str | 2–4 Sätze: wie die Persona das Proposal aus ihrer Linse zusammenfasst. |
| `key_concerns` | list[str] | Konkrete Punkte, die die Persona flaggen will — oft mit Hinweis, welche andere Persona dazu noch gefragt werden müsste. |
| `confidence` | float 0–1 | Selbsteinschätzung der Persona. |

**Wichtig:** Identisches Schema in allen 6 Konditionen. Genau das macht den Architektur-/Mechanismus-Vergleich möglich.

---

## 3. Die "Konversation" zwischen den Agenten (Phasen 3 + 4)

In **Centralized reden die Agenten nicht direkt miteinander** — C0 vermittelt. Was als "Konversation" sichtbar wird, sind die drei Listen `conflicts`, `clarification_requests`, `clarification_responses`.

### 3a. `conflicts` — C0 erkennt Divergenzen (Phase 3)

```jsonc
"conflicts": [
  {
    "dimension": "impact",
    "score_spread": 1,
    "personas_involved": ["A1","A2","A3","A4","A5","A6"],
    "summary": "Five experts (A1, A2, A3, A4, A5) score impact at 2, while A6 alone scores it at 3. A6's higher score reflects a long-horizon, systems-level view ..."
  }
]
```

| Feld | Bedeutung |
|---|---|
| `dimension` | enum: `feasibility` / `novelty` / `impact` / `presentation` |
| `score_spread` | Spannweite der Scores in dieser Dimension (z.B. 3 − 2 = 1). |
| `personas_involved` | Welche Personas C0 als beteiligt sieht. |
| `summary` | Klartext: worum dreht sich die Divergenz substantiell. |

Das ist C0's **analytischer Blick** auf die sechs Urteile — noch keine Interaktion mit den Personas.

### 3b. `clarification_requests` — C0 fragt einzelne Personas (Phase 3-Output)

```jsonc
"clarification_requests": [
  {
    "persona_id": "A6",
    "question": "You are the only expert to score impact at 3, citing the long-horizon potential of a replicable blueprint and rewilding integration. You also acknowledge the causal chain is 'asserted rather than evidenced'. Given this self-acknowledged weakness, how do you defend the higher score?"
  }
]
```

Das ist die echte Mehrebenen-Interaktion: **C0 stellt eine pointierte Rückfrage an genau eine Persona**. Mehrere Requests pro Run möglich, jeder an genau eine Persona adressiert.

### 3c. `clarification_responses` — die Persona antwortet (Phase 4)

```jsonc
"clarification_responses": [
  {
    "persona_id": "A6",
    "question": "You are the only expert to score impact at 3 ...",      // wiederholt für Selbständigkeit
    "answer": "The score reflects probability-weighted long-horizon potential, not certainty ...",
    "revised_scores": { "impact": 3 }   // optional; nur wenn die Persona ihren Score ändert
  }
]
```

- `answer`: Antwort der angefragten Persona im Klartext.
- `revised_scores`: optional. Wenn die Persona ihre Position aufgrund der Rückfrage substantiell ändert, kommt hier ein Dict mit den geänderten Dimensions-Scores. **Code wendet die Revision direkt auf `judgments[<persona>]` an**, damit Phase 5 die aktualisierten Scores synthetisiert.

> **Wenn du also "siehst den Dialog" sehen willst:** Paar dir `clarification_requests` mit `clarification_responses` an — das ist die *einzige* Stelle in Centralized, an der gerichtete 1:1-Kommunikation zwischen C0 und einer einzelnen Persona stattfindet.

---

## 4. `final` — das Endurteil (Phase 5)

C0 synthetisiert aus allen Inputs ein einzelnes `FinalJudgment`:

```jsonc
"final": {
  "proposal_id": "1333885",
  "feasibility":  { "score": 3, "rationale": "After clarification, the panel converges on feasibility = 3 ..." },
  "novelty":      { "score": 2, "rationale": "All six experts identify the proposal as well-trodden ..." },
  "impact":       { "score": 2, "rationale": "Five of six experts score impact at 2; A6's revised position ..." },
  "presentation": { "score": 3, "rationale": "Structured but with notable language quality issues ..." },
  "average": 2.5,
  "synthesis": "The six expert perspectives — scientific (A1), governance (A2), implementation (A3), community (A4), ethics (A5), and sustainability (A6) — converge on a modest but real proposal ...",
  "uncertainty": "Two areas of remaining uncertainty: (1) the empirical basis for the long-term policy spillover claims ...",
  "contributing_agents": ["A1","A2","A3","A4","A5","A6"]
}
```

| Feld | Bedeutung |
|---|---|
| `feasibility` / `novelty` / `impact` / `presentation` | Die finalen vier Dimensions-Scores plus Synthese-Begründung. |
| `average` | **Code-recomputed** als Mittel der vier Scores — *nicht* vom LLM gesetzt. So bleibt Konsistenz garantiert. |
| `synthesis` | Erzähltext: wie C0 die heterogenen Perspektiven integriert hat. |
| `uncertainty` | Wo das Endurteil am schwächsten ist; welche Disagreements ungelöst blieben. |
| `contributing_agents` | Liste der beteiligten Personas. Vom Code erzwungen. |

**Das ist die Spalte, die in `summary.csv` neben die Jury-Scores gestellt wird.**

---

## 5. `trace` — der Phasen-Log

```jsonc
"trace": [
  { "event": "phase1_distribute",            "persona_count":   6 },
  { "event": "phase2_specialist_judgments",  "judgment_count":  6 },
  { "event": "phase3_conflict_detection",    "n_conflicts": 3, "n_clarifications": 5 },
  { "event": "phase4_targeted_clarification","n_responses":     5 },
  { "event": "phase5_final_synthesis",       "average":       2.5 }
]
```

Kompakte Event-Liste, nützlich für:

- **Debugging:** ist eine Phase übersprungen worden?
- **Prozess-Analyse:** wie viele Konflikte und Rückfragen pro Proposal? (→ Vergleichsmetrik zwischen Konditionen)
- **Token/Cost-Schätzung:** Anzahl LLM-Calls pro Proposal lässt sich aus den Counts ableiten (Phase 2: 6 Calls; Phase 3: 1 Call; Phase 4: `n_clarifications` Calls; Phase 5: 1 Call).

---

## Beispiel-Größenordnung pro Proposal (Centralized)

| Phase | LLM-Calls | Notiz |
|---|---|---|
| 2 — Specialist Judgments | 6 (A1…A6) | parallelisierbar, aktuell sequenziell |
| 3 — Conflict Detection | 1 (C0) | |
| 4 — Targeted Clarification | k = Anzahl Requests von Phase 3 | typisch 2–6 |
| 5 — Final Synthesis | 1 (C0) | |
| **Total** | **8 + k** | bei live-Smoke beobachtet: 13 pro Proposal |

---

## Zusammenhang mit dem `summary.csv`

`scripts/run_smoke.py` zieht aus jeder Proposal-JSON nur den `final`-Block plus die Jury-Werte und schreibt eine Zeile pro Proposal:

```
proposal_id, contest,
mas_feasibility, mas_novelty, mas_impact, mas_presentation, mas_average,
jury_feasibility, jury_novelty, jury_impact, jury_presentation, jury_average,
title
```

Das ist die schnelle Vergleichssicht; die volle Konversation bleibt in den JSONs.

---

## Was bei den anderen zwei Architekturen anders heißt

Damit du dich nicht verlierst, wenn du eine Shared-Pool- oder Direct-Comm-JSON öffnest:

| Centralized | Shared Message Pool | Direct Communication |
|---|---|---|
| `judgments` (Phase 2) | `pool_round1` + `pool_round2` | `initial_judgments` + `revised_judgments` |
| `conflicts` + `clarification_*` | `clusters` + `open_questions` (Curator) | — (Peer-Austausch ist in `revised_judgments` codiert) |
| `final` | `final` | `cluster_summaries` (S1, S2) + `final` (E) |
| `trace`-Events: `phase1_distribute` … `phase5_final_synthesis` | `shared_round1`, `shared_round2`, `shared_curator`, `shared_judge` | `direct_initial`, `direct_peer_exchange`, `direct_summarizers`, `direct_decisioner` |

Der `final`-Block hat in allen drei Architekturen exakt dieselbe Form (`FinalJudgment`), damit `summary.csv` und die spätere Analyse einheitlich funktionieren.
