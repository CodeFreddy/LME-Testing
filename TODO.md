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

## Scripts Tab Edit Workflow (DONE 2026/04/18)

Scripts tab now supports full edit → save → downstream wiring:

- `saveScriptsEdits` JS function collects step text from textareas (both regular and gap steps) and POSTs to `/api/scripts/save`
- `save_scripts_edits` Python method persists `human_scripts_edits_latest.json` in session snapshot and records the path in session state
- `--human-scripts-edits` flag added to `bdd` and `rewrite` CLI subcommands; rewrite jobs automatically pick up the latest saved edits from state
- `apply_human_step_edits()` updates `step_text`, `step_pattern`, and `code` in normalized BDD results; gap steps are appended as new entries
- `generate_step_definition(human_edited=True)` uses Python `STEP_LIBRARY` for real code; falls back to `_generate_python_implementation()` for Python implementations, not `pending` stubs
- `map_step_to_template` gains multi-strategy matching: exact substring, parameterized prefix, and token-overlap with `require_exact` safety flag

## Python Step Definitions Migration (COMPLETE 2026/04/18)

Switching from Ruby Cucumber to Python step definitions as the global rule:

- `lme_testing/step_library.py` (NEW): centralized Python step registry with `@step` decorator and `STEP_LIBRARY` dict; 50 entries covering all actual MiniMax BDD output patterns plus translated Ruby library entries; uses Python `LME.Client`, `LME.API`, `LME.PostTrade` patterns
- `lme_testing/step_registry.py`: `extract_steps_from_python_step_defs()` reads Python step defs; imports `STEP_LIBRARY` directly from `step_library.py` for `step_library.py` file, regex-parses `@given/@when/@then` decorated files; CLI auto-detects `.py` vs `.rb`
- `lme_testing/bdd_export.py`: `generate_step_definition()` uses `STEP_LIBRARY` for canonical implementations; `render_steps_from_normalized_bdd()` overrides LLM-generated code with library versions when available; `_generate_python_implementation()` emits Python `def` functions; output is `features/step_definitions/steps.py`
- `lme_testing/prompts.py`: `BDD_PROMPT_VERSION` incremented to `"3.0"`; `BDD_SYSTEM_PROMPT` updated to request Python code; example schema shows Python `@when/def` syntax
- `lme_testing/step_library.py`: `_build_decorated_code()` now properly indents function body by 4 spaces (critical bug fix — unindented body caused Python syntax errors)
- Ruby `samples/ruby_cucumber/` preserved as archive (not deleted)

## Governance Signals CI Wiring (DONE 2026/04/18)

`governance-signals` CLI wired into CI:
- `.github/workflows/ci.yml`: added `governance-signals` job (needs: smoke-test) that runs `python main.py governance-signals --output runs/governance_signals.json`
- `release-governance` job now `needs: governance-signals` so it runs after signals are computed
- `check_release_governance.py` now sees a current `governance_signals.json` and passes all 5 checks

## Report UX Improvements (DONE 2026/04/18)

HTML report (`generate_html_report()` in `reporting.py`):

- **Rule ID jump**: clicking a rule ID in "Rule 级覆盖判定" uses native browser anchor navigation to jump to the sub-header row in "场景审核明细" with blue highlight on matching data rows
- **`link.hash` fix**: changed from `getAttribute('href')` (returned full URL) to `link.hash` (returns `#rule-detail-XXX` fragment) for correct rule ID extraction
- **Color-coded case-type pills**: inline chips in sub-header rows and coverage table columns — gray=Required, green=Present, blue=Accepted, red-strikethrough=Missing
- **Clickable coverage metrics**: clicking Fully Covered / Partially Covered / Uncovered / Not Applicable in "运行摘要" filters the "Rule 级覆盖判定" table with active highlight state
- **Rule 级覆盖判定 filters**: Coverage Status + Rule Type dropdowns with "X / Y 条规则" count and clear button
- **`WindowsPath` empty name guard**: `apply_human_step_edits()` and `run_rewrite_pipeline` now guard against empty/invalid `human_scripts_edits_path` values (`Path("")` or `Path(".")`)
