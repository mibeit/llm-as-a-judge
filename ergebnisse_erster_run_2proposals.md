# Ergebnisse — Erster Run (2 Proposals, alle 6 Kombinationen)
**Datum:** 2026-06-17, Mittag (10:59 – 12:11 Uhr)
**Modell:** alias-large (Qwen3.5-122B) via Blablador / Forschungszentrum Jülich
**Setup:** 2 Proposals × 3 Architekturen × 2 Mechanismen = **12 Runs**

---

## Die zwei getesteten Proposals

| ID | Titel | Typ |
|---|---|---|
| **1333002** | Global Civic Center & Capital — the road to a sustainable planet | Hochfliegende Vision: eine Weltbürger-Stadt als Klima-Katalysator |
| **1333885** | LET'S WALK! — climate change awareness day event | Kleine Aktion: ein Aktionstag fürs Zufußgehen |

Bewusst zwei sehr unterschiedliche Proposal-Typen: einmal *„zu groß/visionär"*, einmal *„zu klein/symbolisch"*.

---

## Gesamtübersicht — Alle 12 Ergebnisse vs. Jury

### Proposal 1333002 — „Global Civic Center"  ·  Jury-Referenz: **Ø 3.12** (F2 N4 I3.5 P3)

| Architektur | Mechanismus | F | N | I | P | **MAS Ø** | Δ zur Jury |
|---|---|---|---|---|---|---|---|
| Centralized | Integration | 2 | 3 | 3 | 3 | **2.75** | −0.37 |
| Centralized | Controversy | 1 | 2 | 1 | 1 | **1.25** | −1.87 |
| Shared Pool | Integration | 2 | 4 | 3 | 3 | **3.00** | **−0.12** ✅ |
| Shared Pool | Controversy | 1 | 2 | 1 | 3 | **1.75** | −1.37 |
| Direct Comm | Integration | 2 | 3 | 3 | 2 | **2.50** | −0.62 |
| Direct Comm | Controversy | 1 | 2 | 1 | 2 | **1.50** | −1.62 |

### Proposal 1333885 — „Let's Walk!"  ·  Jury-Referenz: **Ø 2.75** (F3 N2 I3 P3)

| Architektur | Mechanismus | F | N | I | P | **MAS Ø** | Δ zur Jury |
|---|---|---|---|---|---|---|---|
| Centralized | Integration | 2 | 2 | 3 | 2 | **2.25** | **−0.50** ✅ |
| Centralized | Controversy | 2 | 2 | 2 | 2 | **2.00** | −0.75 |
| Shared Pool | Integration | 2 | 2 | 2 | 2 | **2.00** | −0.75 |
| Shared Pool | Controversy | 2 | 2 | 1 | 2 | **1.75** | −1.00 |
| Direct Comm | Integration | 2 | 2 | 2 | 2 | **2.00** | −0.75 |
| Direct Comm | Controversy | 1 | 2 | 1 | 2 | **1.50** | −1.25 |

---

## Zentrale Erkenntnisse

### 1 · Das System bewertet **systematisch strenger** als die menschliche Jury
In **allen 12 Runs** liegt der MAS-Score unter der Jury-Referenz — kein einziges Mal darüber. Der Multi-Agent-Judge ist durchgängig kritischer als die menschlichen Gutachter. Das ist der stärkste übergreifende Befund.

### 2 · Integration Oriented liegt **immer näher an der Jury** als Constructive Controversy
| Proposal | Bester Integration-Run | Bester Controversy-Run |
|---|---|---|
| 1333002 | Shared Pool: Ø3.00 (Δ −0.12) | Shared Pool: Ø1.75 (Δ −1.37) |
| 1333885 | Centralized: Ø2.25 (Δ −0.50) | Centralized: Ø2.00 (Δ −0.75) |

Constructive Controversy zieht die Scores massiv nach unten — bei 1333002 um bis zu **1.5 Punkte**. Es eignet sich daher eher zum *Aufdecken von Schwächen* als zur *kalibrierten Bewertung*.

### 3 · Der **beste Einzeltreffer**: Shared Pool + Integration bei 1333002 (Δ −0.12)
Dieser Lauf trifft die Jury fast exakt — und ist der **einzige**, der die hohe Novelty der Jury (4) korrekt reproduziert (N=4). In allen anderen Läufen wird die Originalität des Proposals unterschätzt.

### 4 · Der Mechanismus-Effekt ist beim visionären Proposal viel größer
| Proposal | Spanne Integration ↔ Controversy |
|---|---|
| 1333002 (visionär) | bis zu **1.50 Punkte** Unterschied |
| 1333885 (bescheiden) | nur **0.25 – 0.50 Punkte** Unterschied |

Bei einem grandiosen, angreifbaren Proposal (1333002) reibt sich der Controversy-Mechanismus regelrecht auf — die Agenten finden viele Angriffsflächen. Beim bescheidenen Aktionstag-Proposal (1333885) sind sich beide Mechanismen weitgehend einig, weil es schlicht weniger zu „bekämpfen" gibt.

### 5 · Die Architektur ist der schwächere Hebel
Innerhalb desselben Mechanismus liegen die drei Architekturen nah beieinander (max. 0.5 Punkte Unterschied). **Der Mechanismus (Integration vs. Controversy) bestimmt das Ergebnis weit stärker als die Architektur** (Centralized vs. Shared Pool vs. Direct Comm).

---

## Wie die Diskussionen inhaltlich abliefen

### Proposal 1333002 — „Global Civic Center"
- **Integration:** Agent A6 (Long-term Sustainability) verteidigt einen hohen Impact (5) über einen „Demonstrationseffekt"; die anderen Agenten erkennen das als legitimen Gegenpol an. Sprache: *„visionary but unfeasible", „complementary perspectives"*.
- **Controversy:** Alle Agenten konvergieren auf scharfe Ablehnung. A3 wird für seine positivere Presentation-Note (3) konfrontiert und revidiert auf 1 (*„dangerous obfuscation"*). Wortfeld: *„fantasy", „non-starter", „techno-utopian", „climate apartheid"*.

### Proposal 1333885 — „Let's Walk!"
- **Beide Mechanismen** diagnostizieren denselben Kernfehler: einen **„causal fallacy"** — ein eintägiges Event wird unrealistisch mit langfristigem politischem Wandel verknüpft.
- **Integration:** *„low-novelty, high-risk awareness campaign"* — einig, aber nüchtern-konstruktiv.
- **Controversy:** *„fundamentally flawed in its theory of change"* — schärfer, aber wegen des kleinen Anspruchs des Proposals nur geringfügig niedrigere Scores.
- Interessant: Bei 1333885 startete in Centralized/Controversy zunächst **A6** mit einer abweichenden Meinung, gab aber im Konsens nach.

---

## Bewertung der Dimensionen (wo liegt das System richtig/falsch?)

| Dimension | Befund |
|---|---|
| **Feasibility** | Gut kalibriert in Integration (meist F=2). In Controversy oft auf F=1 gedrückt. |
| **Novelty** | Wird **systematisch unterschätzt**, außer in Shared Pool/Integration (1333002: N=4 = Jury). |
| **Impact** | Größter Hebel des Mechanismus: Integration I≈3, Controversy I=1. |
| **Presentation** | Am stärksten umkämpft — in Controversy wird emotionale Rhetorik abgestraft (1333002: P 3→1). |

---

## Fazit für das Projekt

1. **Constructive Controversy** ist als reines Bewertungsverfahren zu streng — es unterbietet die Jury deutlich. Wert hat es als **Stresstest** zum Aufdecken von Schwächen.
2. **Integration Oriented**, insbesondere mit **Shared Message Pool**, kommt der menschlichen Jury am nächsten und reproduziert als einziges Setup die Novelty-Einschätzung korrekt.
3. Das System hat eine **generelle Negativ-Tendenz** gegenüber der Jury — ein Kalibrierungs-Offset, der bei der Interpretation der Scores berücksichtigt werden sollte.
4. Die Wahl des **Mechanismus** ist für das Endergebnis wichtiger als die Wahl der **Architektur**.
