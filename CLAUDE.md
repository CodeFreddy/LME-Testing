# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Agent Entry Rules

**Read `AGENTS.md` first** before making non-trivial changes in this repo. This repository is governed by contracts, phase boundaries, and acceptance gates. Agents may implement the roadmap, but must not silently redefine it through code or document changes.

## Project Overview

LME-Testing is a document-driven AI test design prototype. It transforms source documents into structured testing artifacts through a governed pipeline:

`source docs -> extraction -> atomic_rules -> semantic_rules -> maker -> checker -> human review -> rewrite -> report`

The system generates BDD-style test scenarios from rules and evaluates their quality and coverage against semantic rules.

## Running Commands

### Tests
```bash
python -m pytest
python -m unittest
```

### Run a single test
```bash
python -m unittest tests.test_pipelines.PipelineTests.test_maker_pipeline_persists_records
```

### CLI (maker/checker/report)
```bash
# Maker: generate test cases from semantic rules
python main.py maker --input artifacts/lme_rules_v2_2/semantic_rules.json --output-dir runs/maker --config config/llm_profiles.json

# Checker: evaluate scenario quality and coverage
python main.py checker --rules artifacts/lme_rules_v2_2/semantic_rules.json --cases runs/maker/<run_id>/maker_cases.jsonl --output-dir runs/checker --config config/llm_profiles.json

# Report: generate HTML report
python main.py report --maker-cases <path> --checker-reviews <path> --maker-summary <path> --checker-summary <path> --coverage-report <path> --output-html <path>
```

### Pipelines support batching and resume
```bash
python main.py maker --input <path> --output-dir <path> --batch-size 4 --resume-from runs/maker/<run_id>/maker_cases.jsonl
```

### End-to-End POC (2 rules)
When asked to run an "end to end 2 rule poc", run all four stages (maker + checker + BDD + step-registry):
```bash
# 1. Maker
python main.py maker --input artifacts/poc_two_rules/semantic_rules.json --output-dir runs/poc_two_rules_poc --batch-size 4

# 2. Checker
python main.py checker --rules artifacts/poc_two_rules/semantic_rules.json --cases runs/poc_two_rules_poc/<maker_run_id>/maker_cases.jsonl --output-dir runs/poc_two_rules_poc --batch-size 4

# 3. BDD export (for review session BDD tab)
python main.py bdd --cases runs/poc_two_rules_poc/<maker_run_id>/maker_cases.jsonl --output-dir runs/poc_two_rules_poc/bdd

# 4. Step registry (for review session Scripts tab — run after BDD)
python main.py step-registry --bdd runs/poc_two_rules_poc/bdd/<bdd_run_id>/normalized_bdd.jsonl --output-dir runs/poc_two_rules_poc/step-registry

# 5. Report
python main.py report --maker-cases runs/poc_two_rules_poc/<maker_run_id>/maker_cases.jsonl --checker-reviews runs/poc_two_rules_poc/<checker_run_id>/checker_reviews.jsonl --maker-summary runs/poc_two_rules_poc/<maker_run_id>/summary.json --checker-summary runs/poc_two_rules_poc/<checker_run_id>/summary.json --coverage-report runs/poc_two_rules_poc/<checker_run_id>/coverage_report.json --output-html runs/poc_two_rules_poc/report.html
```

For the review session, include both BDD and step-registry:
```bash
python main.py review-session --rules artifacts/poc_two_rules/semantic_rules.json --cases runs/poc_two_rules_poc/<maker_run_id>/maker_cases.jsonl --checker-reviews runs/poc_two_rules_poc/<checker_run_id>/checker_reviews.jsonl --checker-summary runs/poc_two_rules_poc/<checker_run_id>/summary.json --coverage-report runs/poc_two_rules_poc/<checker_run_id>/coverage_report.json --normalized-bdd runs/poc_two_rules_poc/bdd/<bdd_run_id>/normalized_bdd.jsonl --step-registry runs/poc_two_rules_poc/step-registry/<step_reg_run_id>/step_visibility.json --output-dir runs/poc_two_rules_poc/sessions --port 8765
```

## Governance Checks

Before or after substantial repo changes, run baseline governance checks:

```bash
python scripts/check_docs_governance.py   # Enforces relative local links in *.md
python scripts/check_artifact_governance.py # Enforces minimum artifact structure and controlled rule_type values
```

## Git Hooks (Session Handoff)

Enable the post-commit hook to auto-refresh `docs/operations/session_handoff.md`:

```bash
powershell -ExecutionPolicy Bypass -File scripts/setup_git_hooks.ps1
```

If hooks are unavailable, update manually before committing:

```bash
powershell -ExecutionPolicy Bypass -File scripts/update_session_handoff.ps1
```

## Architecture

See `docs/architecture/architecture.md` for the full system architecture, artifact contracts, and module boundaries.

### Pipeline Flow
1. **Extraction** (scripts): Parse source documents into `atomic_rules.json`
2. **Normalization**: Transform atomic rules into `semantic_rules.json`
3. **Maker**: Generate BDD-style scenarios from semantic rules → `maker_cases.jsonl`
4. **Checker**: Evaluate scenario quality/coverage → `checker_reviews.jsonl` + `coverage_report.json`
5. **Review/Rewrite**: Human review decisions trigger regeneration
6. **Report**: HTML output for human review

### Core Modules
| Module | Responsibility |
|--------|---------------|
| `src/lme_testing/pipelines.py` | Orchestrates maker/checker pipelines, coverage calculation |
| `src/lme_testing/schemas.py` | JSON validation for all artifacts; defines CASE_TYPES, COVERAGE_STATUSES |
| `src/lme_testing/config.py` | ProjectConfig/ProviderConfig/RoleDefaults; loads `config/llm_profiles.json` |
| `src/lme_testing/providers.py` | LLM provider abstraction (OpenAI-compatible API) |
| `src/lme_testing/prompts.py` | MAKER_SYSTEM_PROMPT, CHECKER_SYSTEM_PROMPT, and prompt builders |
| `src/lme_testing/reporting.py` | HTML report generation |
| `src/lme_testing/storage.py` | JSON/JSONL read/write utilities; `timestamp_slug()` for run IDs |

### Key Governance Documents

| Document | Purpose |
|----------|---------|
| `docs/planning/roadmap.md` | Phase-based execution contract (Phase 1/2/3), scope boundaries, priorities |
| `docs/architecture/architecture.md` | Pipeline stages, artifact contracts, module boundaries |
| `docs/planning/implementation_plan.md` | Task breakdowns with input/output contracts |
| `docs/governance/acceptance.md` | Formal phase acceptance criteria and release gates |
| `docs/governance/model_governance.md` | Provider abstraction, model onboarding, prompt versioning |
| `docs/governance/agent_guidelines.md` | How AI agents may modify the repo |

### Key Data Structures
- **semantic_rules.json**: List of rule objects with `semantic_rule_id`, `classification.rule_type`, `evidence`, `source.atomic_rule_ids`
- **maker_cases.jsonl**: One JSON record per semantic rule containing `scenarios[]` with `scenario_id`, `case_type`, `given/when/then`, `evidence`
- **checker_reviews.jsonl**: One record per scenario with `case_type_accepted`, `coverage_relevance`, `is_blocking`, `scores`, `coverage_assessment`
- **coverage_report.json**: Aggregated coverage per rule based on `rule_type` and required case types

### Rule Type Case Requirements
Each `rule_type` in `RULE_TYPE_CASE_REQUIREMENTS` (pipelines.py) defines which case types are required/optional:
- `obligation`: positive, negative (required); boundary, exception (optional)
- `prohibition`: negative, positive (required); exception (optional)
- `permission`: positive (required)
- `deadline`: positive, boundary, negative (required)
- `state_transition`: positive, state_transition (required)
- `data_constraint`: positive, negative, data_validation (required)

## Configuration

Provider configuration uses `config/llm_profiles.json`:
- `providers`: Named provider configs (type, model, base_url, api_key, temperature, etc.)
- `roles`: Maps `maker` and `checker` to provider names
- Supports `${ENV_VAR}` template substitution for api_key

## Artifact Governance

- All model outputs must be schema-validated via `validate_maker_payload` / `validate_checker_payload` in `schemas.py`
- Prompts must be versioned; prompt changes require benchmark evidence
- Every artifact must record model ID, prompt version, provider, run timestamp
- Durable behavior must be repo-readable; do not rely on chat context

## Phase Discipline

This repo follows a phased roadmap (short/mid/long). Key boundaries:
- **Short-term**: Schema validation, CI, source-anchor traceability, model governance
- **Mid-term**: Multi-document ingestion, planner stage, normalized BDD contract
- **Long-term**: Step definition registry, execution-ready contracts

Do not expand scope across phases without explicit approval.

## Phase Completion Tracking

**Rule**: After completing any roadmap phase or acceptance gate:
1. Update `docs/governance/acceptance.md` to mark the gate as done with date and evidence
2. Commit the doc change and push before moving to new work

This keeps the doc current and ensures tracking is preserved in git history, not lost in ephemeral context.

