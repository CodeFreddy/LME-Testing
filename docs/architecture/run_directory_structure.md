# Run Directory Structure

**Created:** 2026-04-18
**Status:** Based on actual `runs/` inspection

---

## Standard Structure

```
runs/
  <run_type>/              # maker | checker | bdd | step-registry | review_sessions
    <run_id>/             # Timestamp-based ID (e.g. 20260418T161845+0800)
      <artifact files>
```

### Run Types and Their Artifacts

#### `runs/maker/<run_id>/`
| File | Description |
|------|-------------|
| `maker_cases.jsonl` | One JSON record per semantic rule with generated scenarios |
| `summary.json` | Aggregate stats: total rules, total scenarios, case type breakdown |
| `maker_raw_responses.jsonl` | Raw LLM responses (if `log_raw_responses: true` in config) |

#### `runs/checker/<run_id>/`
| File | Description |
|------|-------------|
| `checker_reviews.jsonl` | One JSON record per scenario with checker assessment |
| `coverage_report.json` | Aggregated coverage per semantic rule (required for governance signals) |
| `summary.json` | Aggregate stats: coverage %, case type acceptance rates |
| `checker_raw_responses.jsonl` | Raw LLM responses |

#### `runs/bdd/<run_id>/`
| File | Description |
|------|-------------|
| `normalized_bdd.jsonl` | Normalized BDD scenarios with given/when/then steps |
| `summary.json` | Aggregate stats |

#### `runs/bdd-export/<run_id>/`
| File | Description |
|------|-------------|
| `*.feature` | Gherkin feature files |
| `step_definitions.py` | Python step definitions (or `.rb` for Ruby) |

#### `runs/step-registry/<run_id>/`
| File | Description |
|------|-------------|
| `step_visibility.json` | Match report: exact/parameterized/candidate/unmatched counts |

#### `runs/schema_validation_latest.json` (top-level, not in a run directory)
| File | Description |
|------|-------------|
| `schema_validation_latest.json` | CI schema validation summary; written by `validate_schemas.py --output-json` |

#### `runs/review_sessions/<session_id>/`
| File | Description |
|------|-------------|
| `session_state.json` | Review session state |
| `human_bdd_edits_latest.json` | Latest human BDD edits |
| `human_scripts_edits_latest.json` | Latest human step edits |
| `iterations/<iter>/` | Per-iteration snapshots |

---

## Current Local State (2026-04-19)

Governance signals analysis (computed `runs_analyzed=21`, `total_rules=180`):

| Run Type | Count | Rule Count | Coverage % |
|----------|-------|------------|------------|
| maker | ~30 | 183 | — |
| checker | ~20 | 183 | 72.78% |
| bdd | ~5 | 183 | — |
| review_sessions | multiple | 183 | — |

Full 183-rule runs are present in `runs/maker_v1.1_full/` and `runs/baseline_full/`.

---

## Using `--runs-dir` with Governance Signals

To analyze runs from a different location:

```bash
python main.py governance-signals \
  --repo-root . \
  --runs-dir /path/to/external/runs \
  --output governance_signals.json
```

When `--runs-dir` is specified, governance signals will scan that directory instead of the default `./runs/`.

---

## Governance Signals Scanning Logic

| Signal | Scans |
|--------|-------|
| `schema_signals` | `<runs_dir>/schema_validation_latest.json` (top-level) |
| `checker_instability_signals` | `<runs_dir>/<any>/stability_report.json` |
| `coverage_signals` | `<runs_dir>/checker/<run_id>/coverage_report.json` (picks latest by timestamp) |
| `step_binding_signals` | `<runs_dir>/<any>/step_visibility.json` |
| `runs_analyzed` | Count of top-level subdirs in `<runs_dir>` |
