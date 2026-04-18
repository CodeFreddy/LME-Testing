# Roadmap TODO — All Phases Complete

## Phase 1 Completion (2026/04/13)

- [x] Artifact Schema Gate
- [x] Upstream Validation Pipeline Gate
- [x] Baseline CI Gate
- [x] Model and Prompt Metadata Gate
- [x] Stable Source Anchor Gate
- [x] Checker Stability Gate
- [x] Documentation Gate

## Phase 2 Gates (COMPLETE 2026/04/13)

- [x] **Gate 1: Multi-Document Ingestion** — Support multiple document classes with source-aware extraction
- [x] **Gate 2: Planning Layer** — Planner stage between semantic_rules and BDD generation
- [x] **Gate 3: Normalized BDD Contract** — Schema-validated intermediate BDD representation
- [x] **Gate 4: Traceability Gate** — Full source-to-BDD traceability in artifacts and reports
- [x] **Gate 5: Step Visibility Gate** — Surface reusable steps and gaps without execution binding
- [x] **Gate 6: Quality and Drift Reporting** — Reports showing baseline drift, unstable judgments
- [x] **Gate 7: Model Governance Enforcement Gate** — Benchmark checks before model/prompt adoption

## Phase 3 Post-Completion Items (ALL DONE 2026/04/17)

- [x] **Web Portal BDD Stage** — BDD tab displays normalized BDD per approved scenario with editable Given/When/Then steps; saves to `human_bdd_edits_latest.json` in session snapshot
- [x] **Web Portal Scripts Stage** — Scripts tab displays step registry visibility with match quality badges (exact/parameterized/candidate/unmatched); saves edits to session snapshot
- [x] **Stage Progression UI** — 4-stage progress bar (Scenario Review → BDD Edit → Scripts → Finalize) with gate logic enforcing tab unlock order

## Phase 3 Gates (COMPLETE 2026/04/14)

- [x] **Gate 1: Step Definition Integration** — 3-tier matching, reuse scores, ownership
- [x] **Gate 2: Execution Readiness** — ExecutableScenario schema with environment/input/hooks/assertions
- [x] **Gate 3: Deterministic Oracle** — Oracle modules for structured rule categories
- [x] **Gate 4: Governance Signals** — Schema failure rate, instability, binding success
- [x] **Gate 5: Release Governance** — Release tags, compatibility matrix, benchmark gates
- [x] **Gate 6: Phase 3 Exit** — All above

## End-to-End POC Verification (2026/04/17)

Successfully ran full 2-rule end-to-end POC:

1. **Maker** → 2 rules → 5 scenarios (qwen3.5-plus, ~2 min)
2. **Checker** → 5 reviews (MiniMax-M2.5, ~1 min)
3. **Report** → `runs/report.html`, `maker_readable.html`, `checker_readable.html`, `report.csv`
4. **BDD** → `normalized_bdd.jsonl` + `.feature` files + Ruby step definitions
5. **BDD Export** → template-based `.feature` files and step definitions (no LLM)
6. **Step Registry** → gap analysis linking normalized BDD to step visibility
7. **Review Session** → web UI at `http://127.0.0.1:8765` with Scenario Review, BDD, Scripts, Finalize tabs

**Bugs Fixed During POC:**
- `review_session.py` line ~1130: `issueOptionMap` function definition corrupted into orphan statement — restored as proper function
- `review_session.py` line ~1129: `saveScriptsEdits` async function missing closing `}` — added brace
- `step_registry.py`: `StepEntry` dataclass lacked match metadata fields; `compute_step_matches` never annotated inventory entries; `render_step_visibility_report` never wrote per-step details — all fixed to surface step-level data in Scripts tab

## Formal Schema Validation Wired (DONE 2026/04/18)

Extraction scripts and CI now enforce JSON Schema validation by default:

- `extract_matching_rules.py`: `--skip-validate` flag added (validation is now default); renamed from `--validate`
- `generate_semantic_rules.py`: same `--skip-validate` inversion
- `validate_rules.py`: now accepts `--semantic-rules` to validate `semantic_rules.json` alongside `atomic_rules.json`; `upstream-validation` CI job passes both
- `schemas/fixtures/atomic_rule_invalid.json`: expanded to 8 cases (added rule_id pattern, start_page/end_page type errors)
- `schemas/fixtures/semantic_rule_invalid.json`: expanded to 10 cases (added semantic_rule_id pattern, pages type, atomic_rule_ids empty, priority enum, empty evidence quote)
- `tests/test_schemas.py`: added targeted tests for edge cases

## Known Issues / Open Questions

- **Scripts tab is read-only display**: The `saveScriptsEdits` button and save mechanism are scaffolded but not wired to a real edit workflow. Step definitions are managed locally in `bdd_export.py` `TEMPLATE_REGISTRY` and Ruby step definition files, not via GUI.
