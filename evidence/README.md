# Evidence Archive

Preserved run artifacts that document key results. These are snapshots of evidence referenced in governance documents and session handoffs.

> **Note:** These files are manually preserved. The `runs/` and `reports/` directories are gitignored — this directory tracks key evidence that should not be lost.

---

## evidence/20260419_stability_v4/

**Purpose:** S2-T02 checker stability measurement — MiniMax API reliability investigation

**Contents:**
- `run_a/` — checker run A: `checker_reviews.jsonl`, `coverage_report.json`, `summary.json`
- `run_b/` — checker run B: `checker_reviews.jsonl` (process hung at batch 98/322)
- `stability_report_v3.json` — v3 stability report (v4 process hung; v3 is last complete measurement)

**Key findings (v3):** 9.5% instability rate (6/63 comparable cases) — exceeds 5% threshold. Full 322-case measurement blocked by API random disconnects.

**Source:** `runs/checker-stability/20260418T231915+0800-v4/` (run_a/run_b) and `...-v3/` (stability_report)

---

## evidence/20260419_baseline_full/

**Purpose:** S1-T04 full 183-rule quality baseline

**Contents:**
- `maker_summary.json` — maker run summary (322 scenarios generated)
- `checker_summary.json` — checker run summary
- `coverage_report.json` — 72.78% coverage (131/180 fully covered)
- `baseline_full_20260418.html` — full HTML report (1.2MB, human-verified)

**Key findings:** 72.78% coverage on 180 rules (131 fully covered). 12 rules randomly sampled and human-verified. Full results in `docs/releases/BASELINE-183-RULES.md`.

**Source:** `runs/maker_v1.1_full/20260419T090524+0800/` and `runs/checker_v1.1_full/20260419T092854+0800/`

---

## evidence/governance_signals.json

**Purpose:** Latest governance signal values

**Source:** `runs/governance_signals.json` (computed from 21 runs, 180 rules)

---

## evidence/schema_validation_latest.json

**Purpose:** Latest CI schema validation result

**Key value:** `failure_rate = 0.0` (370 fixtures, 0 failures) — `schema_signal_source: "real_validation"`

**Source:** `runs/schema_validation_latest.json`

---

## evidence/20260420_s2t01_v1p1_checker_run/

**Purpose:** S2-T01 v1.1 checker re-run — verify coverage improvement from checker prompt calibration

**Contents:**
- `coverage_report.json` — v1.1 coverage results (75.0% coverage)
- `summary.json` — v1.1 run metadata (prompt_version: 1.1)

**Key findings:** Coverage 72.22% -> 75.0% (+2.78%). 9 rules improved (partial->full), 4 rules regressed (full->partial). Net +5 fully covered rules.

**Source:** `runs/checker/20260420T062527Z/`
