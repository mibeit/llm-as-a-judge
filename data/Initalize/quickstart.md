# Quickstart: Wie starte ich selbst einen Run?

> Setup-Anleitung und CLI-Referenz für `scripts/run_smoke.py`.
> Stand: 2026-06-05

---

## 1. Einmalige Vorbereitung

### Python + Dependencies
Python ≥ 3.11. Im Projekt-Root:

```powershell
pip install -e .
```

(installiert `judgex` als editierbares Package mit allen Dependencies aus `pyproject.toml`: `langgraph`, `anthropic`, `pydantic`, `openpyxl`, `python-dotenv`)

### API-Key (nur für Live-Runs gegen Claude)
`.env` im Projekt-Root anlegen — Template ist `.env.example`:

```
ANTHROPIC_API_KEY=sk-ant-...
JUDGEX_MODEL=claude-sonnet-4-6
```

- `ANTHROPIC_API_KEY` — dein Anthropic-API-Key.
- `JUDGEX_MODEL` — welches Claude-Modell die Agenten benutzen. Default ist `claude-sonnet-4-6`. Setz das, wenn du z.B. mal mit Opus 4.7 testen willst.

`.env` ist gitignored — kommt nicht ins Repo.

**Für Mock-Runs brauchst du *nichts* von dem.** Mock läuft auch ohne API-Key.

---

## 2. Den Runner aufrufen

```powershell
python -m scripts.run_smoke [OPTIONS]
```

### Flags

| Flag | Werte | Default | Bedeutung |
|---|---|---|---|
| `--provider` | `mock` / `anthropic` | `mock` | Mock = deterministische Fake-Antworten, kein API-Call. Anthropic = echte Claude-Calls (kostet). |
| `--contest` | `Behavior` / `Adaptation` / `LandUse` / `Energy` | `Behavior` | Welcher der vier Wicked-Problem-Datensätze. |
| `--limit` | int | `3` | Wie viele Proposals aus dem Contest (sortiert nach ID, von oben). |
| `--architecture` | `centralized` / `shared_pool` / `direct_comm` | `centralized` | Die MAS-Topologie. |
| `--mechanism` | `integration_oriented` / `constructive_controversy` | `integration_oriented` | Der Kommunikationsmodus. |

Die zwei letzten Flags spannen die 3×2-Matrix auf — 6 Konditionen insgesamt.

---

## 3. Typische Aufrufe

### Erstmal verstehen, was rauskommt — ohne Kosten
```powershell
python -m scripts.run_smoke
```
→ Mock-Run, Centralized + Integration, 3 Proposals aus Behavior. Macht keine API-Calls, prüft nur die Pipeline-Mechanik.

### Echte Bewertung an drei Proposals testen
```powershell
python -m scripts.run_smoke --provider anthropic --limit 3
```
→ Live gegen Claude. Centralized + Integration. **Kostet etwa 13 LLM-Calls pro Proposal** (= 39 Calls insgesamt) — bei Sonnet 4.6 typisch wenige Cent.

### Eine andere Kondition fahren
```powershell
python -m scripts.run_smoke --provider anthropic --architecture shared_pool --mechanism constructive_controversy --limit 3
```
→ Shared Message Pool mit Constructive Controversy.

### Ein anderer Contest, mehr Proposals
```powershell
python -m scripts.run_smoke --provider anthropic --contest Energy --limit 5
```

### Alle 6 Konditionen auf demselben Sample (heute noch von Hand)
Aktuell musst du sie nacheinander aufrufen. Ein `run_matrix.py` ist auf der Roadmap, sodass das ein Befehl wird.

```powershell
foreach ($a in "centralized","shared_pool","direct_comm") {
  foreach ($m in "integration_oriented","constructive_controversy") {
    python -m scripts.run_smoke --provider anthropic --architecture $a --mechanism $m --limit 3
  }
}
```

---

## 4. Wo landen die Outputs?

```
runs/<timestamp>_<architecture>_<mechanism>_<provider>_<contest>/
├── <proposal_id>.json   # voller Endzustand pro Proposal
├── ...
└── summary.csv          # eine Zeile pro Proposal: MAS-Scores neben Jury-Scores
```

Beispiel:
```
runs/20260605_161431_centralized_integration_oriented_anthropic_Behavior/
├── 1333002.json
├── 1333885.json
├── 1333894.json
└── summary.csv
```

Was genau in den JSONs steht, beschreibt **`Initalize/output_format_centralized.md`**.

Das ganze `runs/`-Verzeichnis ist gitignored — du kannst es jederzeit löschen, alte Runs bleiben so lange erhalten, wie du sie behältst.

---

## 5. Kostengröße einschätzen (Live-Runs)

Calls pro Proposal nach Architektur:

| Architektur | LLM-Calls pro Proposal (typisch) |
|---|---|
| Centralized | 8 + k ≈ 13 (k = Anzahl Clarification-Rückfragen, meist 2–6) |
| Shared Message Pool | 6 + 6 + 1 + 1 = 14 |
| Direct Communication | 6 + 6 + 2 + 1 = 15 |

Multipliziert mit `--limit` und (später) mit der Anzahl Wiederholungs-Runs. Sonnet 4.6 ist preislich der Sweet Spot; Opus 4.7 ist ~5× teurer.

---

## 6. Troubleshooting

### "ANTHROPIC_API_KEY not set"
`.env` im Projekt-Root vergessen oder leer. `cat .env` (bzw. `Get-Content .env`) prüfen. Du kannst stattdessen auch die Env-Var direkt setzen:
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
python -m scripts.run_smoke --provider anthropic --limit 1
```

### "Structured call for AgentJudgment failed validation after 3 attempts"
Claude hat dreimal hintereinander ein Output erzeugt, das das Schema verletzt. Sehr selten. Wenn das passiert, einfach neu starten — die Stochastik des Modells fängt sich meist beim nächsten Versuch. Wenn es bei einem bestimmten Proposal *reproduzierbar* scheitert, sag bescheid; dann schau ich mir das Schema oder die Prompt-Strenge an.

### "ModuleNotFoundError: judgex"
Du hast nicht aus dem Projekt-Root gestartet, oder `pip install -e .` nicht gemacht. `cd S:\dev\LLMASAJUDGE\llm-as-a-judge` und nochmal probieren.

### Run hängt scheinbar fest
Python's stdout ist gebuffert; die `[run] …`-Zeilen erscheinen ggf. verzögert. Du kannst während der Run läuft in das frisch erstellte `runs/<…>/`-Verzeichnis schauen — sobald eine Proposal-JSON dort liegt, ist der Run aktiv und produktiv. Bei 13 Calls × ~3s pro Call ist ein Proposal in 30–60 Sekunden durch.

### "Permission denied" beim Schreiben in `runs/`
Verzeichnis-Berechtigungen prüfen. Workaround: `runs/` einmal manuell anlegen.

---

## 7. Was checken nach einem Live-Run?

1. **`summary.csv`** öffnen — passt der MAS-Average grob zum Jury-Average?
2. **Eine Proposal-JSON** öffnen und durch die Phasen lesen (siehe `output_format_centralized.md` für die Struktur). Spannend ist meistens:
   - `judgments.A?.key_concerns` — was hat jede Linse wirklich gesehen?
   - `clarification_requests` + `clarification_responses` — die einzige gerichtete Konversation in Centralized.
   - `final.synthesis` und `final.uncertainty` — wie ist das Endurteil zustande gekommen?
3. **`trace`** — wenn dir eine Phase fehlt oder die Counts seltsam aussehen, ist da was schiefgelaufen.
