# Vergleich von Multi-Agenten-Systemen für die Bewertung nachhaltiger Innovationskonzepte

> **Status:** 🟢 Working Document · **Letztes Update:** 2026-06-24
> **Semester:** Baseline-Phase
> **Autor:innen:** *TBD*

---

## 1. Projektüberblick

### 1.1 Forschungsfrage (Working)
> *Wie beeinflussen unterschiedliche Kollaborations-Architekturen und Kommunikations-Mechanismen in Multi-Agenten-Systemen (MAS) die Qualität evaluierter nachhaltiger Innovationskonzepte ("Wicked Problems")?*

### 1.2 Kernbeitrag
Systematischer Vergleich von **6 MAS-Konditionen** (3 Architekturen × 2 Mechanismen) bei der Bewertung nachhaltiger Innovationskonzepte. Die LLM-basierten Outputs werden gegen menschliche Jury-Bewertungen validiert.

### 1.3 Scope dieses Semesters
- **Baseline-Implementierung** aller 6 Konditionen mit der vollen Persona-Population (6 Personas A1–A6)
- Ziel: Proof-of-Concept — produziert die jeweilige (Architektur, Mechanismus)-Kombination einen erkennbaren Effekt gegenüber den anderen?
- Späteres Semester: Skalierung, weitere Mechanismen, Persona-Variation.

---

## 2. Theoretischer Hintergrund

### 2.1 Multi-Agenten-Systeme
- LLM-basierte MAS als emergente Klasse für komplexe, schlecht-strukturierte Aufgaben
- *TBD: Kernreferenzen einfügen (Park et al. Generative Agents, AutoGen, CAMEL, ChatDev, MetaGPT, …)*

### 2.2 Wicked Problems & nachhaltige Innovation
- Wicked Problems nach Rittel & Webber: keine eindeutige Problemformulierung, keine "richtige" Lösung, hohe Stakeholder-Diversität
- Nachhaltigkeit als paradigmatisches Wicked-Problem-Feld (ökologisch / ökonomisch / sozial — Zielkonflikte intrinsisch)
- *TBD: Refs ergänzen*

### 2.3 Kollaboration: Zielstruktur vs. Kommunikationsmechanismus

**Entwicklung gegenüber der ursprünglichen Konzeption:** Das ursprünglich geplante 2×3-Design (Cooperative vs. Competitive × 3 Architekturen) wurde verworfen, weil eine strikt **kompetitive Zielstruktur** schwer mit Collective-Intelligence-Ansätzen vereinbar ist — diese beruhen auf Einbindung, Aggregation und Synthese heterogener Perspektiven, nicht auf der Dominanz einer Position (Gimpel et al., 2023). Stattdessen werden **zwei kooperative Mechanismen** kontrastiert, die innerhalb einer Shared-Goal-Logik unterschiedliche Kommunikationsmuster operationalisieren:

- **Cooperative (Zielstruktur):** geteilte / positiv verknüpfte Ziele (Deutsch, 1949; Tjosvold, 1998).
- **Competitive (Zielstruktur):** getrennte / negativ verknüpfte Ziele — *für das Forschungsdesign verworfen.*

Innerhalb der kooperativen Zielstruktur:

- **Integration-oriented Cooperation:** Andere Perspektiven werden primär als komplementäre Inputs behandelt; Fokus auf Zusammenführen, ergänzen, integrieren.
- **Constructive Controversy (Johnson & Johnson, 2009):** Strukturierter intellektueller Konflikt — inkompatible Ideen werden bewusst konfrontiert, während die Teilnehmer auf eine begründete Synthese orientiert bleiben. Vor der Integration steht systematische Herausforderung, kritische Prüfung und Perspektivendifferenzierung.

Hintergrund: Kollaboration ist kein einzelner Mechanismus, sondern hängt von Interaktionsmustern wie Erklärung, Aushandlung, Widerspruch und gegenseitiger Regulation ab (Dillenbourg, 1999). Beide Mechanismen sind daher als **theoretisch eigenständige Kollaborationsmechanismen innerhalb einer kooperativen Zielstruktur** zu behandeln.

---

## 3. Setup-Matrix (3 × 2 Design)

|  | **Integration-oriented** | **Constructive Controversy** |
|---|---|---|
| **Centralized** | Kondition 1 | Kondition 2 |
| **Shared Message Pool** | Kondition 3 | Kondition 4 |
| **Direct Communication** | Kondition 5 | Kondition 6 |

Die beiden Dimensionen sind als orthogonal angenommen. Die Architektur bestimmt die **Topologie** (wer mit wem über welchen Pfad), der Mechanismus bestimmt den **Kommunikationsmodus** (integrieren vs. konfrontieren). Personas, Output-Schema und Foundation-LLM sind über alle Konditionen identisch — der Vergleich liegt ausschließlich an Architektur und Mechanismus.

### 3.1 Architekturen (Topologie)

Siehe §4 für die vollständigen Definitionen.

### 3.2 Mechanismen (Kommunikationsmodus)

Implementiert als reines **Prompt-Scaffolding**, das in jede Architektur eingehängt wird (sechs Snippets: Persona-Preamble, Individual-Judgment-Instruction, Clarification-Instruction, Synthesis-Instruction, Conflict-Detection-Instruction). Personas und Output-Schema bleiben unverändert — der Mechanismus modifiziert ausschließlich den Kommunikationsstil.

---

## 4. Architekturen im Detail

### 4.1 Centralized (Orchestrator)
**Komponenten:** A1–A6 + **C0 — Central Orchestrator** (neutral).
**Topologie:** Sternförmig. Jede Kommunikation läuft über C0; A1–A6 kommunizieren *nicht* direkt.
**Ablauf (5 Phasen):**
1. **Task Distribution** — C0 verteilt die Aufgabe an alle Agenten.
2. **Specialist Judgments** — A1–A6 bewerten unabhängig und liefern strukturierte Einzelurteile.
3. **Conflict Detection** — C0 vergleicht die Urteile, identifiziert Widersprüche.
4. **Targeted Clarification** — C0 stellt gezielte Rückfragen an relevante Agenten; diese überarbeiten und antworten.
5. **Final Synthesis** — C0 integriert alle Informationen zum finalen Urteil.

### 4.2 Shared Message Pool
**Komponenten:** A1–A6 + **Pool Curator** (neutral, filtert/clustert) + **Final Pool Summarizer / Judge** (neutral, synthetisiert).
**Topologie:** Alle Agenten lesen und schreiben in ein gemeinsames strukturiertes Arbeitsgedächtnis (Blackboard-Pattern). Keine direkte Adressierung; Agenten entscheiden selbst, wann und worauf sie reagieren. Fragen gehen daher *an den Pool* (un-adressiert) — jeder Experte kann sie aufgreifen.
**Ablauf:** Der Curator moderiert aus der Mitte heraus, nicht erst am Ende.
1. **Round 1** — A1–A6 posten initiale strukturierte Urteile in den Pool.
2. **Curator (früh)** — clustert Round 1, benennt Konflikte und offene Fragen und postet diese zurück in den Pool.
3. **Round 2 (Q&A)** — A1–A6 lesen den Pool inkl. der Curator-Fragen, beantworten was sie aus ihrer Perspektive können, dürfen eigene Fragen an den Pool stellen und ggf. Scores revidieren.
4. **Round 3** — A1–A6 beantworten die in Round 2 aufgeworfenen Fragen und legen ihre Position fest (letzter Austausch vor der Synthese); optional mit revidierten Scores.
5. **Curator (final)** — re-clustert den vollständigen Pool (Round 1–3).
6. **Final Judge** — synthetisiert aus dem geclusterten Pool das finale Urteil.

### 4.3 Direct Communication
**Komponenten:** A1–A6 + 2 **Summarizer** (S1, S2) + 1 **Decisioner** (E).
**Schichtstruktur:**
| Layer | Rolle | Knoten |
|-------|-------|--------|
| 1 | Fachagenten | A1, A2, A3, A4, A5, A6 |
| 2 | Summarizer | S1 (für Cluster {A1,A2,A3}), S2 (für Cluster {A4,A5,A6}) |
| 3 | Decisioner | E |

**Peer-Kommunikation in Layer 1:** Agenten kommunizieren innerhalb ihres Clusters direkt untereinander (Cluster {A1,A2,A3} und Cluster {A4,A5,A6}). Die A4-Zuordnung folgt der Spec; sie ist als bewusste Annahme markiert und kann in einem späteren Schritt revidiert werden, ohne Code-Änderung.

**Ablauf:**
1. **Initial Judgments** — jeder Agent postet ein initiales Urteil (ohne Peer-Information).
2. **Peer Exchange** — eine einzelne, *optionale* Q&A-Runde innerhalb des Clusters:
   - **Fragen:** Jeder Agent liest die Urteile seiner beiden Cluster-Peers und *darf* je Peer **maximal eine** gezielte Frage / Anregung stellen — muss aber nicht. Wer nichts zu fragen hat, fragt nicht.
   - **Antworten:** Jeder adressierte Agent beantwortet die an ihn gerichteten Fragen.
   - **Revision:** Jeder Agent postet ein revidiertes Urteil auf Basis der Peer-Urteile und der Cluster-internen Q&A.
   Genau eine Frage-Runde (bewusst nicht iterativ, um die Komplexität gering zu halten).
3. **Cluster-Summarizer** — S1 aggregiert A1–A3, S2 aggregiert A4–A6 (jeweils als FinalJudgment für den Cluster).
4. **Decisioner E** — synthetisiert aus S1 + S2 das overall FinalJudgment.

### 4.4 Architektur-Vergleich (Übersicht)

| Merkmal | Centralized | Shared Message Pool | Direct Communication |
|---------|-------------|---------------------|----------------------|
| Koordinationsrolle(n) | C0 (1) | Pool Curator (früh + final) + Summarizer/Judge (neutral) | S1, S2 (Summarizer) + E (Decisioner) |
| Agent-zu-Agent direkt | nein | indirekt über Pool (Fragen un-adressiert) | ja (Intra-Cluster, gerichtete Fragen) |
| Gemeinsamer Speicher | nein | ja (Pool) | nein |
| Finale Synthese durch | C0 | Final Pool Summarizer/Judge | E (Decisioner) |
| Iteration / Feedback | gezielte Rückfragen (Phase 4) | Curator-Fragen + Pool-Q&A (Round 2 + 3) | optionale Q&A-Runde im Peer-Austausch |

---

## 5. Personas (A1–A6)

### 5.1 Prinzip: Konsistenz über Konditionen
Dieselben Personas in allen 6 Konditionen → der Unterschied liegt ausschließlich in der Architektur und im Mechanismus, nicht in den Agenten selbst.

### 5.2 Persona-Set
| ID | Persona | Evaluationsperspektive |
|----|---------|------------------------|
| **A1** | Scientific / Systems Expert | Evidenz, Kausalmechanismen, System-Interdependenzen, Unsicherheit, technische Plausibilität. |
| **A2** | Policy / Governance Expert | Regulatorische Machbarkeit, institutionelle Passung, öffentliche Rechenschaftspflicht, Governance-Kapazität, politische Restriktionen. |
| **A3** | Industry / Implementation Expert | Operative Machbarkeit, Ressourcen, Skalierbarkeit, Anreize, Adoptionsbarrieren, Umsetzungsrisiken. |
| **A4** | Affected Community Representative | Gelebte Erfahrung, lokale Konsequenzen, Zugänglichkeit, soziale Akzeptanz, unbeabsichtigte Effekte. |
| **A5** | Ethics / Justice Expert | Fairness, Verteilungsfolgen, Inklusion, Wertekonflikte, Exklusionsrisiken, normative Trade-offs. |
| **A6** | Sustainability / Long-term Impact Expert | Ökologische Konsequenzen, Resilienz, langfristige gesellschaftliche Effekte, intergenerationale Wirkungen, systemische Nachhaltigkeit. |

### 5.3 Persona-Schema (im Code)
Jede Persona ist über Name, Expertise, Evaluation-Focus und Kommunikationsstil definiert (`judgex/personas.py`). Identisch über alle Konditionen.

---

## 6. Wicked-Problem-Cases (Daten)

Die Cases sind als realer Datensatz vorhanden (`data/`):

- **4 Contests** mit jeweils 26 Proposals = **104 Proposals total**
  - C1-Behavior (Verhaltensänderung)
  - C2-Adaptation (Klimaanpassung)
  - C3-LandUse (Landnutzung)
  - C4-Energy (Energie)
- Pro Proposal: roher `.txt`-Text + identische normalisierte Variante in `C{n}.json`
- Quelle: Climate CoLab "Semi-Finalist selection"-Phase

---

## 7. Evaluations-Framework

### 7.1 Ground Truth: Menschliche Jury-Bewertungen
- Datei: `data/Jury Bewertungen.xlsx`
- 104 Proposals × 1 Zeile pro Proposal
- Bewertete Dimensionen: **Feasibility, Novelty, Impact, Presentation** (jeweils Skala ~1–5, beobachteter Bereich 1.0–4.0) plus Average
- **Wichtige Einschränkung:** nur die *aggregierte* Average-Spalte pro Judge liegt vor — keine einzelnen Judge-Scores, daher **keine Inter-Rater-Reliability berechenbar**

### 7.2 Vergleichsmetriken
- Direkter Vergleich: die 6 MAS-Konditionen liefern Scores auf **exakt denselben 4 Dimensionen** wie die Jury → unmittelbar vergleichbar.
- Geplante Metriken pro Kondition:
  - **MAE / RMSE** pro Dimension (MAS vs. Jury-Average)
  - **Pearson / Spearman-Korrelation** über alle Proposals
  - **Rank-Agreement** innerhalb eines Contests (Top-N-Übereinstimmung)
- Prozess-Eigenschaften (explorativ, aus dem `trace`-Block der Runs):
  - Anzahl Rückfragen / Pool-Beiträge / Peer-Revisionen
  - Token-/Kosten-Effizienz pro Kondition

### 7.3 Statistisches Design
- *TBD:* Anzahl Wiederholungs-Runs pro Proposal (Foundation-LLMs sind stochastisch; mindestens 3 Runs empfohlen, um Streuung zu erfassen).
- *TBD:* Korrektur für multiples Testen bei 6-Konditionen-Vergleich.

---

## 8. Technische Implementierung

### 8.1 Framework: LangGraph + Python
- **LangGraph** als Graph-Runtime. Jede Architektur ist ein eigener `StateGraph` (`judgex/architectures/`).
- Begründung: Graph-basierte Modellierung erlaubt es, alle 3 Topologien sauber abzubilden — bei identischem Agent-Code darunter.
- Verworfen: AutoGen (Shared Message Pool und strikt zentralisierte Topologien wären Workarounds), CrewAI (opinionated hierarchisch/sequenziell).

### 8.2 LLM-Layer
- **Pluggable Provider** (`judgex/llm.py`): `MockProvider` (deterministisch, schema-konform, für Pipeline-Tests ohne API-Key) und `AnthropicProvider` (Claude via Anthropic SDK).
- **Strukturierter Output** über `tool_use`: das gewünschte JSON-Schema wird als Tool deklariert; das Modell wird gezwungen, exakt dieses Tool aufzurufen.
- **Retry-mit-Validation-Feedback** (`judgex/runtime.py`): Bei Pydantic-Validation-Errors wird der Fehler dem Modell zurückgegeben und der Call bis zu 3× wiederholt — fängt seltene Schema-Verstöße ab.
- **Foundation-LLM:** *TBD finalisieren.* Aktuell als Konfigurations-Flag (`JUDGEX_MODEL`), Default `claude-sonnet-4-6`. Wichtig für Fairness: identisches Modell, identische Parameter über alle 6 Konditionen.

### 8.3 Output-Schemas (Pydantic)
- `AgentJudgment`: pro Persona, 4 Dimensionen mit Score (1–5) und Rationale, `perspective_summary`, `key_concerns`, `confidence`.
- `FinalJudgment`: 4 Dimensionen, recomputed `average`, `synthesis`, `uncertainty`, `contributing_agents`.
- `PoolReaction` (Shared Pool, Round 2/3): kompakte Reaktion mit optionalen Fragen an den Pool (`questions`) und optional revidierten Scores.
- `PeerQuestionSet` / `PeerAnswerSet` (Direct Comm, Peer-Exchange): gerichtete Fragen an Cluster-Peers (max. 1 je Peer, optional) und die zugehörigen Antworten.
- Inline-Schemas: `ConflictReport`, `ClarificationResponse`, `ClusterReport`.

### 8.4 Mechanismus-Implementierung
- Reines Prompt-Scaffolding (`judgex/mechanisms/`).
- `integration.py` und `constructive_controversy.py` exportieren je sechs Prompt-Snippets in identischer Struktur. Die Architektur-Nodes binden den jeweiligen Mechanismus über eine `Mechanism`-Dataclass ein. Mechanismus-Wechsel = anderer Import, keine Logik-Änderung.

### 8.5 Reproduzierbarkeit
- Pro Run wird ein eigenes Verzeichnis angelegt: `runs/<timestamp>_<architecture>_<mechanism>_<provider>_<contest>/`
- Pro Proposal: ein JSON mit dem vollständigen Endzustand (Proposal-Text, alle Zwischen-Outputs, Final, Trace).
- Pro Run-Verzeichnis: ein `summary.csv` (MAS-Scores neben Jury-Scores).
- *Noch fehlend:* zentrale `meta.json` pro Run mit Modell, Parametern, Git-Commit (geplant).
- *Noch fehlend:* Token/Cost-Logging aus den Anthropic-Responses (geplant).

### 8.6 Repo-Struktur (aktuell)
```
llm-as-a-judge/
├── data/                          # Proposals + Jury-Datei (gitignored)
├── Initalize/                     # Konzept-Dokumente (dieses File + multi-agent-spec.md)
├── judgex/
│   ├── personas.py                # A1–A6
│   ├── schemas.py                 # Pydantic AgentJudgment, FinalJudgment, PoolReaction
│   ├── data.py                    # Proposal- und Jury-Loader
│   ├── llm.py                     # Mock + Anthropic Provider
│   ├── runtime.py                 # call_validated_model + Retry-Logik
│   ├── mechanisms/
│   │   ├── integration.py
│   │   └── constructive_controversy.py
│   └── architectures/
│       ├── centralized.py
│       ├── shared_pool.py
│       └── direct_comm.py
├── scripts/
│   └── run_smoke.py               # CLI: --provider, --architecture, --mechanism, --contest, --limit
├── runs/                          # Output-Verzeichnisse (gitignored)
└── pyproject.toml
```

### 8.7 Stand der Implementierung (2026-06-05)

| Komponente | Status |
|---|---|
| Personas A1–A6 | ✅ |
| Output-Schemas | ✅ |
| Data-Loader (Proposals + Jury) | ✅ |
| LLM-Provider (Mock + Anthropic) | ✅ |
| Retry-on-Validation-Error | ✅ |
| Mechanismus: Integration-oriented | ✅ |
| Mechanismus: Constructive Controversy | ✅ |
| Architektur: Centralized | ✅ (mock + live getestet) |
| Architektur: Shared Message Pool | ✅ (mock getestet, live ausstehend) |
| Architektur: Direct Communication | ✅ (mock getestet, live ausstehend) |
| Smoke-Runner | ✅ |
| **Noch zu bauen:** | |
| Analyse-Modul (MAE/Korrelation/Rank-Agreement) | 🔴 |
| Batch-Runner (alle 6 Konditionen × N Proposals) | 🔴 |
| Run-Metadata `meta.json` | 🔴 |
| Token/Cost-Logging | 🔴 |

---

## 9. Roadmap / Meilensteine

| Phase | Inhalt | Status |
|---|---|---|
| 1. Konzeption | Personas, Mechanismen, Architekturen finalisieren | ✅ Abgeschlossen |
| 2. Setup | Repo, Framework, Logging | ✅ Abgeschlossen |
| 3. Implementierung | Alle 6 Konditionen baubar | ✅ Abgeschlossen |
| 4. Pilot-Runs | Smoke-Test pro Kondition (3 Proposals) | 🟡 Centralized + Integration live getestet; 5 Konditionen ausstehend |
| 5. Hauptdurchlauf | Vollständige Baseline (alle Konditionen × alle 104 Proposals × Wiederholungen) | 🔴 Offen |
| 6. Analyse | MAE / Korrelation / Rank-Agreement pro Kondition; statistischer Vergleich | 🔴 Offen |
| 7. Doku & Schreiben | Ergebnisse, Reflexion | 🔴 Offen |

---

## 10. Offene Fragen / Diskussionspunkte

### Geklärt seit der ursprünglichen Version
- ~~Cooperative vs. Competitive~~ → durch zwei kooperative Mechanismen (Integration / Constructive Controversy) ersetzt; siehe §2.3
- ~~Agent-Zahl Baseline~~ → 6 Personas (A1–A6) in allen Konditionen; strukturbedingte Zusatzknoten (C0, Curator, Judge, S1, S2, E) je nach Architektur
- ~~Operationalisierung Competitive~~ → entfällt
- ~~Persona-Set Finalisierung~~ → A1–A6 stehen (§5.2)
- ~~Eval-Modalität~~ → identische 4 Dimensionen wie die Jury; direkter Vergleich möglich
- ~~Framework-Wahl~~ → LangGraph + Python

### Noch offen
1. **Foundation-LLM final wählen.** Aktuell Default `claude-sonnet-4-6`, pluggable. Vor Hauptdurchlauf festziehen.
2. **Anzahl Wiederholungs-Runs pro Proposal** (Stochastik des LLMs). Vorschlag: 3.
3. **A4-Cluster-Annahme in Direct Communication.** Aktuell A4 → S2 (gemäß Spec). Revidierbar ohne Code-Änderung.
4. **Termination Criterion pro Setup.** Aktuell fix: Centralized 5 Phasen, Shared Pool 3 Runden (R1 + Q&A-Runden R2/R3, gerahmt von frühem und finalem Curator-Pass), Direct Comm 1 optionale Q&A-Runde im Peer-Austausch. Für Baseline ausreichend; für spätere Iterationen evtl. konvergenzbasiert.
5. **Statistisches Design.** Welche Tests für den 6-Konditionen-Vergleich? Korrektur für multiples Testen?
6. **Inter-Rater-Reliability nicht berechenbar.** Die Jury-Datei enthält nur Average-Werte über alle Judges, keine Einzel-Scores. Konsequenz für die Validität der Ground Truth dokumentieren.
7. **Kosten-Budget für Hauptdurchlauf.** 104 Proposals × 6 Konditionen × 3 Wiederholungen × ~15 LLM-Calls = ~28k Calls. Modellwahl beeinflusst das deutlich.

---

## 11. Changelog
- **2026-06-24** — Interaktion in zwei Architekturen vertieft. **Shared Message Pool:** Curator vom End-Filter zum Moderator in der Mitte (früher Cluster-/Fragen-Pass nach Round 1), neue fixe Round 3, in der Experten die in Round 2 gestellten Fragen beantworten; `PoolReaction` um `questions` (Fragen an den Pool) erweitert. **Direct Communication:** Peer-Exchange um eine optionale, einzelne Q&A-Runde erweitert (je Peer max. 1 Frage, kein Zwang → Frage → Antwort → Revision); neue Schemas `PeerQuestionSet`/`PeerAnswerSet`.
- **2026-06-05** — Re-Design: Cooperative/Competitive → Integration-oriented / Constructive Controversy. Personas A1–A6 festgelegt. Daten eingepflegt (4 Contests × 26 Proposals, Jury-Datei). Baseline-Implementierung aller 6 Konditionen abgeschlossen. Live-Smoke (Centralized + Integration) erfolgreich.
- **2026-05-26** — Initiale Version erstellt (Struktur + offene Fragen).
