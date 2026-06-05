# Multi-Agenten-System zur Wicked-Problem-Evaluation — Spezifikation

> Bündelung der vorbereiteten Inhalte als Kontext-/Build-Spezifikation (z. B. für Claude Code).
> Stand: Entwurf zur Abstimmung. Offene Punkte sind am Ende gesammelt und im Text mit **[ANNAHME]** markiert.

---

## 1. Zielsetzung

Das System bewertet **Wicked Problems** durch das Zusammenführen heterogener Fachperspektiven (Collective-Intelligence-Ansatz). Sechs spezialisierte Agenten (A1–A6) liefern strukturierte Einzelurteile, die je nach Konfiguration über unterschiedliche Kollaborations-Architekturen und Kommunikationsmechanismen zu einem finalen Urteil mit Begründung und Unsicherheitsangabe integriert werden.

Es gibt **zwei unabhängige Design-Dimensionen**:

1. **Kommunikationsmechanismus** — *wie* Perspektiven verarbeitet werden (kooperativ-integrativ vs. konstruktive Kontroverse).
2. **Kollaborations-Architektur** — *über welche Topologie* Agenten verbunden sind (Centralized / Shared Message Pool / Direct Communication).

**[ANNAHME]** Beide Dimensionen sind orthogonal → 3 Architekturen × 2 Mechanismen = **6 Konditionen**.

---

## 2. Agenten-Personas (A1–A6)

| Agent | Persona | Evaluationsperspektive |
|-------|---------|------------------------|
| **A1** | Scientific / Systems Expert | Bewertet Evidenz, kausale Mechanismen, System-Interdependenzen, Unsicherheit und technische Plausibilität. |
| **A2** | Policy / Governance Expert | Bewertet regulatorische Machbarkeit, institutionelle Passung, öffentliche Rechenschaftspflicht, Governance-Kapazität und politische Restriktionen. |
| **A3** | Industry / Implementation Expert | Bewertet operative Machbarkeit, benötigte Ressourcen, Skalierbarkeit, Anreize, Adoptionsbarrieren und Umsetzungsrisiken. |
| **A4** | Affected Community Representative | Bewertet gelebte Erfahrung, lokale Konsequenzen, Zugänglichkeit, soziale Akzeptanz, praktische Nützlichkeit und mögliche unbeabsichtigte Effekte. |
| **A5** | Ethics / Justice Expert | Bewertet Fairness, Verteilungsfolgen, Inklusion, Wertekonflikte, Exklusionsrisiken und normative Trade-offs. |
| **A6** | Sustainability / Long-term Impact Expert | Bewertet ökologische Konsequenzen, Resilienz, langfristige gesellschaftliche Effekte, intergenerationale Wirkungen und systemische Nachhaltigkeit. |

---

## 3. Kommunikationsmechanismen (theoretischer Rahmen)

Kommunikationsarchitekturen lassen sich zunächst über ihre **Zielstruktur** unterscheiden. In der Social-Interdependence-Theorie beruhen kooperative Ansätze auf geteilten oder positiv verknüpften Zielen, kompetitive Ansätze auf getrennten oder negativ verknüpften Zielen, bei denen der Erfolg einer Partei den Erfolg einer anderen behindert (Deutsch, 1949; Tjosvold, 1998).

Für die Wicked-Problem-Evaluation ist eine **strikt kompetitive** Zielstruktur schwer mit Collective-Intelligence-Ansätzen vereinbar, da diese auf Einbindung, Aggregation und Synthese heterogener Perspektiven beruhen statt auf der Dominanz einer Position (Gimpel et al., 2023). Beide hier genutzten Mechanismen werden daher **innerhalb einer kooperativen Zielstruktur** verortet:

### 3.1 Integration-oriented Cooperation
Teilnehmer behandeln andere Perspektiven primär als **komplementäre Inputs** und arbeiten auf gemeinsames Verständnis und Synthese hin. Fokus: Zusammenführen, ergänzen, integrieren.

### 3.2 Constructive Controversy
Etablierte Form **strukturierten intellektuellen Konflikts**: Inkompatible Ideen, Informationen oder Schlussfolgerungen werden bewusst konfrontiert, während die Teilnehmer auf eine begründete Synthese orientiert bleiben (Johnson & Johnson, 2009). Vor der Integration steht systematische Herausforderung, kritische Prüfung und Perspektivendifferenzierung.

> Hintergrund: Kollaboration ist kein einzelner Mechanismus, sondern hängt von Interaktionsmustern wie Erklärung, Aushandlung, Widerspruch und gegenseitiger Regulation ab (Dillenbourg, 1999). Constructive Controversy bewahrt die Shared-Goal-Logik kollektiven Lernens, ergänzt sie aber um einen stärker kontroversbasierten Kommunikationsmodus. Beide Mechanismen sind daher als **theoretisch eigenständige Kollaborationsmechanismen** innerhalb einer kooperativen Zielstruktur zu behandeln.

---

## 4. Kollaborations-Architekturen

### 4.1 Centralized (Orchestrator)

**Komponenten:** 6 Agenten (A1–A6) + **C0 — Central Orchestrator**

**Topologie:** Sternförmig. Jede Kommunikation läuft über C0; die Agenten kommunizieren **nicht** direkt miteinander. (Im Diagramm: ausgehend C0 → Agenten, rücklaufend Agenten → C0.)

**Ablauf (5 Phasen):**

| Phase | Name | Inhalt |
|-------|------|--------|
| 1 | **Task Distribution** | C0 gibt die komplette Aufgabe (Wicked Problem) an alle Agenten und fordert eine Lösung aus deren jeweiliger Sicht an. |
| 2 | **Specialist Judgments** | Alle Agenten bewerten **unabhängig** und liefern strukturierte Einzelurteile. |
| 3 | **Conflict Detection** | C0 vergleicht alle Urteile, identifiziert Widersprüche und offene Annahmen. |
| 4 | **Targeted Clarification** | C0 stellt gezielte Rückfragen **nur an relevante Agenten**. Diese überarbeiten und antworten. |
| 5 | **Final Synthesis** | C0 integriert alle Informationen und erstellt das finale Urteil mit Begründung und Unsicherheit. |

---

### 4.2 Shared Message Pool

**Komponenten:**
- 6 Agenten (A1–A6)
- **Shared Message Pool** — gemeinsames strukturiertes Arbeitsgedächtnis (alle Agenten lesen und schreiben, bidirektional)
- **Pool Curator / Clustering Agent** (neutral) — filtert, bündelt und clustert Pool-Beiträge
- **Final Pool Summarizer / Judge** (neutral) — erstellt das finale Urteil auf Basis der geclusterten Beiträge

**Topologie / Ablauf:**
1. A1–A6 schreiben Beiträge in den Shared Message Pool und lesen daraus (gemeinsames Arbeitsgedächtnis statt direkter 1:1-Verbindungen).
2. Der **Pool Curator** verarbeitet die Pool-Inhalte: filtern, bündeln, clustern.
3. Der **Final Pool Summarizer / Judge** erstellt das finale Urteil auf Basis der geclusterten Beiträge.

Beide Verarbeitungsrollen (Curator, Summarizer/Judge) sind **neutral**, d. h. ohne eigene Fachperspektive.

---

### 4.3 Direct Communication

**Komponenten:** 6 Agenten (A1–A6) + 2 **Summarizer** (S1, S2) + 1 **Decisioner** (E)

**Schichtstruktur:**

| Layer | Rolle | Knoten |
|-------|-------|--------|
| **Layer 1** | Fachagenten | A1, A2, A3, A4, A5, A6 |
| **Layer 2** | Summarizer | S1, S2 |
| **Layer 3** | Decisioner | E |

**Routing zwischen den Layern:**
- A1, A2, A3 → **S1**
- A4, A5, A6 → **S2**
- S1, S2 → **E** (finale Entscheidung)

**Peer-Kommunikation (Layer 1):**
**[ANNAHME]** Zusätzlich zur Weiterleitung an die Summarizer kommunizieren die Agenten **innerhalb ihres Clusters direkt untereinander** — Cluster {A1, A2, A3} und Cluster {A4, A5, A6}. Die genaue Zuordnung von A4 ist noch zu bestätigen (siehe offene Punkte).

---

## 5. Architektur-Vergleich (Übersicht)

| Merkmal | Centralized | Shared Message Pool | Direct Communication |
|---------|-------------|---------------------|----------------------|
| Koordinationsrolle(n) | C0 (1) | Pool Curator + Summarizer/Judge (2, neutral) | S1, S2 (Summarizer) + E (Decisioner) |
| Agent-zu-Agent | nein (nur über C0) | indirekt über Pool | ja (Intra-Cluster) |
| Gemeinsamer Speicher | nein | ja (Pool) | nein |
| Finale Synthese durch | C0 | Final Pool Summarizer/Judge | E (Decisioner) |
| Iteration / Rückfragen | ja (Phase 4) | über Pool-Updates | über Peer-Austausch |

