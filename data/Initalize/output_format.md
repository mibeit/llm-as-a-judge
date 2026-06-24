# Output-Format: alle Architekturen (kompakt)

> Welche Keys in einer Run-JSON vorkommen — pro Architektur. Stand: 2026-06-24.
> Detail-Doku Centralized: siehe `output_format_centralized.md`. Schemas: `judgex/schemas.py`.

## Ablage

```
runs/<timestamp>_<arch>_<mech>_<provider>_<contest>/
├── <proposal_id>.json   # voller Endzustand pro Proposal (Input + Zwischenschritte + final + trace)
└── summary.csv          # finale MAS-Scores neben Jury-Scores
```

Gemeinsam in **jeder** JSON: `proposal_id` (str), `proposal_text` (str, Original-Input), `final` (`FinalJudgment`), `trace` (Event-Liste).
Der `final`-Block hat in allen drei Architekturen exakt dieselbe Form → `summary.csv` zieht nur daraus.

---

## Top-Level-Keys pro Architektur

### Centralized (`judgex/architectures/centralized.py`)
```jsonc
{
  "proposal_id", "proposal_text",
  "judgments":               { "A1": AgentJudgment, … "A6": … },  // Einzelurteile (Phase 2)
  "conflicts":               [ Conflict, … ],                     // C0-Befund (Phase 3)
  "clarification_requests":  [ ClarificationRequestItem, … ],     // C0 → Persona (Phase 3)
  "clarification_responses": [ {persona_id, question, …ClarificationResponse} ], // Persona → C0 (Phase 4)
  "final": FinalJudgment,                                         // Synthese (Phase 5)
  "trace": [ … ]
}
```
trace-Events: `phase1_distribute` · `phase2_specialist_judgments` · `phase3_conflict_detection` · `phase4_targeted_clarification` · `phase5_final_synthesis`

### Shared Message Pool (`judgex/architectures/shared_pool.py`)
```jsonc
{
  "proposal_id", "proposal_text",
  "pool_round1":          { "A1": AgentJudgment, … },     // R1 Initialurteile
  "early_clusters":       [ Cluster, … ],                 // Curator (früh)
  "early_open_questions": [ str, … ],                     // zurück in den Pool gepostet
  "pool_round2":          { "A1": PoolReaction, … },      // R2 Q&A (mit questions[])
  "pool_questions":       [ {from_persona, question} ],   // in R2 gestellte Fragen
  "pool_round3":          { "A1": PoolReaction, … },      // R3 Antworten/Settle
  "judgments":            { "A1": AgentJudgment, … },     // R1 + R2/R3-Score-Revisionen gemerged
  "clusters":             [ Cluster, … ],                 // Curator (final)
  "open_questions":       [ str, … ],
  "final": FinalJudgment,
  "trace": [ … ]
}
```
trace-Events: `shared_round1` · `shared_curator_early` · `shared_round2` · `shared_round3` · `shared_curator_final` · `shared_judge`

### Direct Communication (`judgex/architectures/direct_comm.py`)
```jsonc
{
  "proposal_id", "proposal_text",
  "initial_judgments": { "A1": AgentJudgment, … },        // 1a (ohne Peer-Info)
  "peer_questions":    [ {from_persona, to_persona, question} ],  // 1b-i (optional, max 1/Peer)
  "peer_answers":      [ {from_persona, to_persona, question, answer} ], // 1b-ii
  "revised_judgments": { "A1": AgentJudgment, … },        // 1b-iii (post Q&A)
  "cluster_summaries": { "S1": FinalJudgment, "S2": FinalJudgment }, // Cluster-Aggregat
  "final": FinalJudgment,                                 // Decisioner E
  "trace": [ … ]
}
```
trace-Events: `direct_initial` · `direct_peer_questions` · `direct_peer_answers` · `direct_peer_revision` · `direct_summarizers` · `direct_decisioner`

---

## Wiederverwendete Objekt-Schemas (`judgex/schemas.py`)

**DimensionScore** `{ score: int 1–5, rationale: str }`

**AgentJudgment** (pro Persona)
```jsonc
{ persona_id: "A1"–"A6", proposal_id, feasibility, novelty, impact, presentation,  // 4× DimensionScore
  perspective_summary: str, key_concerns: [str], confidence: float 0–1 }
```

**FinalJudgment** (terminaler Block jeder Architektur; auch S1/S2)
```jsonc
{ proposal_id, feasibility, novelty, impact, presentation,  // 4× DimensionScore
  average: float,        // Code-recomputed = Mittel der 4 Scores (nicht vom LLM)
  synthesis: str, uncertainty: str, contributing_agents: ["A1"…] }
```

**PoolReaction** (Shared Pool R2/R3) `{ persona_id, text: str, questions: [str], revised_scores: {dim:int}|null }`

**Conflict** (Centralized) `{ dimension, score_spread: int 0–4, personas_involved: [id], summary }`
**ClarificationRequestItem** `{ persona_id, question }` · **ClarificationResponse** `{ answer, revised_scores: {dim:int}|null }`

**Cluster** (Curator) `{ label, summary, contributing_personas: [id], dimensions_touched: [dim] }`
**ClusterReport** = `{ clusters: [Cluster], open_questions: [str] }`

**PeerQuestion** `{ to_persona, question }` (Set: `{questions:[…]}`, optional, max 1/Peer)
**PeerAnswerItem** `{ question, answer }` (Set: `{answers:[…]}`)

> `score`/`revised_scores`-Dimensionen sind immer: `feasibility`, `novelty`, `impact`, `presentation`.
> `persona_id`, `proposal_id`, `contributing_agents`, `average` werden vom Code erzwungen/neu berechnet — nicht dem LLM vertraut.

---

## summary.csv
Eine Zeile pro Proposal, nur aus `final` + Jury:
```
proposal_id, contest,
mas_feasibility, mas_novelty, mas_impact, mas_presentation, mas_average,
jury_feasibility, jury_novelty, jury_impact, jury_presentation, jury_average, title
```
