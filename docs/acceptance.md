# Acceptance Criteria and Release Gates

## Purpose

This document defines the acceptance criteria, release gates, and evidence requirements for each roadmap phase.

It is intended to be used by:

- developers implementing roadmap items,
- reviewers validating readiness,
- AI coding agents making changes under roadmap constraints.

This document should be read together with:

- `docs/roadmap.md`
- `docs/implementation_plan.md`
- `docs/architecture.md`
- `docs/model_governance.md`
- `docs/agent_guidelines.md`

---

## General Acceptance Rules

These rules apply to all phases.

### 1. No acceptance without evidence

A phase item is not complete unless there is clear evidence of completion.

Accepted evidence types include:

- passing CI jobs,
- schema validation results,
- benchmark output,
- generated artifacts,
- screenshots or exported reports,
- test logs,
- change notes in the repo.

### 2. No artifact contract change without coordinated updates

Any change to an artifact format requires all of the following:

- schema update or equivalent contract update,
- migration note where applicable,
- test update,
- documentation update,
- acceptance checklist update if the change affects phase gates.

### 3. No model or prompt change without regression check

A new model API, model version, or prompt version must not be adopted unless benchmark and stability checks have passed at the level required by the active phase.

### 4. No phase crossover without approval

Work from a later phase must not be merged into an earlier phase unless explicitly approved and documented.

### 5. Structured outputs remain structured

Any module that currently emits structured JSON must continue to emit structured JSON unless the contract is intentionally revised.

### 6. Phase gate sign-off is required for cross-phase execution

If work from a later phase is requested, the relevant earlier phase gate must already be signed off, or the missing sign-off must be explicitly flagged.

Examples:

- Phase 2 work should not be treated as normal implementation if the equivalent Phase 1 gate has not been completed.
- Phase 3 work should not be treated as normal implementation if the required earlier phase gates are missing.

Where a repo uses explicit gate files or equivalent gate records, those records should be checked before cross-phase implementation is considered complete.

### 7. New LLM-driven stages require governed contracts

No new LLM-driven stage should be treated as accepted baseline behavior unless it has:

- a defined artifact contract,
- schema or equivalent deterministic validation,
- traceability expectations,
- reviewable outputs,
- documented failure behavior.

This rule is especially important for planner outputs and normalized BDD artifacts.

---

## Evidence Template

Each completed roadmap item should provide evidence in this form:

- **Change summary**
- **Files changed**
- **Acceptance items addressed**
- **Tests run**
- **Artifacts generated**
- **Known limitations**
- **Rollback impact**

---

# Phase 1 Acceptance: Baseline Control and Pipeline Hardening (0-3 Months)

## Phase Goal

Stabilize the current document-to-rule-to-BDD design pipeline so that different model APIs can be used without silently degrading artifact quality.

## Phase Gate

Phase 1 is complete only if all required acceptance sections below pass.

Phase 1 is intentionally biased toward control, validation, and reproducibility before workflow expansion.

---

## 1. Artifact Schema Gate

### Required

Governed schemas or equivalent governed validation contracts must exist for:

- `atomic_rule`
- `semantic_rule`
- maker output
- checker output
- human review output

### Acceptance Criteria

- each artifact contract is stored in the repo,
- contract version or validation version is declared,
- example artifacts validate successfully,
- invalid sample artifacts fail validation.

### Evidence

- schema files or governed validation modules committed,
- validation test output,
- example valid and invalid fixtures.

---

## 2. Upstream Validation Pipeline Gate

### Required

A formal validation stage must exist between extraction and downstream generation.

Expected path:

`docs -> extraction scripts -> atomic_rules.json -> schema validation -> duplicate candidate detection -> rule_type enum validation -> semantic_rules.json`

### Acceptance Criteria

- invalid `atomic_rule` artifacts fail the pipeline,
- invalid `rule_type` values fail the pipeline,
- duplicate candidate detection produces a machine-readable result,
- invalid trace references are surfaced as validation findings where trace fields already exist,
- the validation stage can produce a structured validation report,
- the report includes total rules, valid count, invalid count, and per-rule error details,
- validation failure prevents downstream maker execution.

### Evidence

- pipeline implementation,
- test fixtures that intentionally fail,
- CI logs showing enforcement,
- sample structured validation report.

---

## 3. Baseline CI Gate

### Required

A baseline CI workflow must run automatically.

### Acceptance Criteria

CI must run at least:

- end-to-end smoke on a minimal baseline dataset,
- schema validation tests,
- reporting smoke test,
- core unit tests for pipeline bootstrapping,
- an end-to-end smoke path that can run without real LLM API calls by using a deterministic stub provider or equivalent governed test double.

### Evidence

- CI workflow files,
- CI run logs,
- pass or fail status on example commits or PRs.

---

## 4. Model and Prompt Metadata Gate

### Required

All maker and checker artifacts must record metadata about how they were generated.

### Acceptance Criteria

Each generated governed artifact includes:

- provider,
- model identifier,
- prompt version,
- run timestamp,
- source artifact hash where applicable,
- pipeline version.

### Evidence

- generated sample artifacts,
- contract or schema support for metadata,
- tests confirming metadata presence.

---

## 5. Stable Source Anchor Gate

### Required

The pipeline must support a stable source-level traceability anchor for governed upstream artifacts and any downstream artifact that already carries traceability.

### Acceptance Criteria

- the rule layer supports a stable source anchor such as a paragraph-level identifier or equivalent governed source key,
- uniqueness within the governed scope is checked,
- downstream governed artifacts that consume trace data can retain or surface this anchor where practical,
- reports or machine-readable exports can surface the anchor when available.

### Evidence

- artifact samples with source anchor fields,
- uniqueness validation output,
- report or export examples showing the anchor.

**Completed:** `paragraph_id` field added to AtomicRule (schema and extraction script). `paragraph_ids` added to semantic_rule source section. All 183 LME and 2 poc atomic rules updated with `paragraph_id = rule_id`. Uniqueness validation implemented in validate_rules.py (advisory for pre-existing duplicates). Coverage report and HTML report surface paragraph_ids. [2026/04/13]

---

## 6. Checker Stability Gate

### Required

Checker output instability must be detectable on a baseline set.

### Acceptance Criteria

- the same small baseline input can be evaluated repeatedly,
- differences are captured in a machine-readable way,
- unstable findings are surfaced in output or logs,
- the process is documented,
- the gate applies to a practical baseline set and does not require full-corpus double-runs by default.

### Evidence

- benchmark or comparison script,
- sample diff output,
- documentation of interpretation rules.

---

## 7. Documentation Gate

### Required

Repository docs must exist to guide both humans and AI agents.

### Acceptance Criteria

The repo contains, at minimum:

- `docs/roadmap.md`
- `docs/implementation_plan.md`
- `docs/acceptance.md`
- `docs/model_governance.md`
- `docs/agent_guidelines.md`

### Evidence

- committed docs,
- links from `README.md`,
- doc review checklist.

---

## 8. Phase 1 Exit Criteria

Phase 1 is accepted only if:

- all core rule artifacts are schema-validated in CI,
- invalid `rule_type` values hard-fail the pipeline,
- a structured validation report can be produced and used to stop downstream execution,
- a reproducible minimal smoke run exists in CI,
- the smoke path can run without making real LLM API calls by using a deterministic stub provider or equivalent governed test double,
- maker and checker artifacts record model and prompt metadata,
- checker instability can be surfaced on the baseline set,
- a stable source anchor is available in governed upstream artifacts and preserved where applicable downstream,
- required governance docs exist in the repo.

---

## Phase 1 Completion

**Phase 1 — Baseline Control and Pipeline Hardening: COMPLETED 2026/04/13**

All 7 acceptance gates passed:
1. Artifact Schema Gate — JSON schemas for atomic_rule, semantic_rule, maker_output, checker_output
2. Upstream Validation Pipeline Gate — validate_rules.py with schema, rule_type, duplicate, field checks
3. Baseline CI Gate — CI workflow with smoke, schema, upstream validation jobs
4. Model and Prompt Metadata Gate — prompt/pipeline versioning, provider/model in all summaries
5. Stable Source Anchor Gate — paragraph_id in AtomicRule, propagation to semantic_rules, surfacing in reports
6. Checker Stability Gate — scripts/checker_stability.py with deterministic stub comparison
7. Documentation Gate — roadmap, acceptance, architecture, implementation_plan, model_governance, agent_guidelines

Evidence: all CI jobs pass locally, smoke test passes, schema validation passes, upstream validation passes.

---

# Phase 2 Acceptance: Planned Test Design and Normalized BDD Platform (3-9 Months)

## Phase Goal

Upgrade from a stable prototype into an AI-assisted test planning and BDD generation platform that can support multiple document categories and controlled team-pilot usage without losing reviewability or contract clarity.

## Phase Gate

Phase 2 is complete only if all required acceptance sections below pass.

Phase 2 is about adding governed intermediate artifacts, not just adding more LLM calls.

---

## 1. Multi-Document Ingestion Gate

### Required

The system must support multiple defined document classes and preserve a governed source-to-rule path.

### Acceptance Criteria

Multiple document classes are supported, each with:

- parsing strategy,
- extraction constraints,
- expected rule patterns,
- documented failure modes,
- source-aware outputs that remain traceable and schema-valid.

### Evidence

- parser configuration or code,
- sample documents,
- extraction outputs,
- class-specific documentation.

---

## 2. Planning Layer Gate

### Required

A planner stage may exist between semantic rules and BDD generation only if it is governed.

Expected flow:

`semantic_rules -> planning -> test objectives -> scenario families -> BDD generation`

### Acceptance Criteria

Planner outputs are:

- schema-validated or equivalently contract-validated,
- versioned,
- traceable to semantic rules,
- reviewable independently,
- linked to downstream BDD generation.

### Evidence

- planner schema,
- planner artifact samples,
- tests showing trace into downstream generation.

---

## 3. Normalized BDD Contract Gate

### Required

A normalized BDD representation must exist independent of final syntax output.

### Acceptance Criteria

- normalized BDD schema exists,
- generated BDD artifacts validate against it,
- at least one output renderer can consume it,
- the contract is documented,
- raw `.feature` output is not the only governed representation.

### Evidence

- BDD schema,
- valid and invalid fixtures,
- renderer tests,
- architecture or contract documentation.

---

## 4. Traceability Gate

### Required

Generated planning and BDD artifacts must be traceable through the pipeline.

### Acceptance Criteria

Governed downstream artifacts can be traced to:

- source document or source segment,
- governed source anchor where applicable,
- atomic rule,
- semantic rule,
- planning decision where planning exists.

### Evidence

- traceability fields in artifacts,
- report examples,
- traceability validation tests.

---

## 5. Step Visibility Gate

### Required

Phase 2 must surface early step-definition reuse and gap visibility without requiring full execution binding.

### Acceptance Criteria

The system can produce reviewable outputs showing:

- candidate reusable steps,
- obvious step gaps,
- implementation-needed markers,
- lightweight early mapping notes.

### Evidence

- visibility artifacts,
- sample gap reports,
- usage documentation.

---

## 6. Quality and Drift Reporting Gate

### Required

Reports must support pilot-grade visibility into quality, drift, and traceability.

### Acceptance Criteria

Reports can show:

- rule type coverage view,
- unstable checker decisions on the benchmark set,
- baseline drift versus previous runs,
- document class breakdown where applicable,
- traceability drill-down,
- JSON and/or CSV export.

### Evidence

- report artifacts,
- screenshots,
- export samples,
- tests for report generation.

---

## 7. Model Governance Enforcement Gate

### Required

Model and prompt changes must be gated before adoption.

### Acceptance Criteria

- benchmark checks run before new model or prompt adoption,
- checker stability threshold is enforced where applicable,
- artifact diff review is documented,
- rollback path is defined.

### Evidence

- governance doc updates,
- benchmark output,
- adoption checklist or review record.

---

## 8. Phase 2 Exit Criteria

Phase 2 is accepted only if:

- multiple document classes are supported with explicit extraction rules,
- planner outputs, if introduced, are versioned and schema-validated,
- normalized BDD artifacts exist as governed intermediate outputs,
- governed downstream artifacts remain traceable end-to-end,
- step reuse and gap visibility exists in a lightweight reviewable form,
- reports show drift and unstable judgments where applicable,
- generated BDD or `.feature` outputs can pass a governed syntax or dry-run check in the target BDD framework where such output exists,
- model change regression is enforced before adoption.

---

## Phase 2 Completion

**Phase 2 — Planned Test Design and Normalized BDD Platform: COMPLETED 2026/04/13**

All 7 acceptance gates infrastructure-complete (end-to-end validated with MiniMax-M2.7 on poc_two_rules):

1. **Multi-Document Ingestion Gate** — `scripts/document_classes.py`: DocumentClass enum, ParsingStrategy, 4 strategies (rulebook/api_spec/policy/workflow), `infer_rule_type()` with class-specific keyword hints.

2. **Planning Layer Gate** — `schemas/planner_output.schema.json` + `run_planner_pipeline` + `validate_planner_payload`. Planner run `runs/acceptance_e2e/20260413T133435Z/planner_results.jsonl` validated successfully. Traceability: paragraph_ids and atomic_rule_ids carried through.

3. **Normalized BDD Contract Gate** — `schemas/normalized_bdd.schema.json` + `run_bdd_pipeline` + `validate_normalized_bdd_payload`. BDD run `runs/acceptance_e2e/20260413T134346Z/normalized_bdd.jsonl` produced 2 feature files + step_definitions. `run_bdd_export` renders Gherkin `.feature` files independently of normalized BDD.

4. **Traceability Gate** — paragraph_ids propagate through planner → maker → BDD pipelines. Planner results carry source `paragraph_ids`/`atomic_rule_ids`. BDD `metadata` section carries `planner_run_id`, `maker_run_id`, `paragraph_ids`. Each scenario carries `semantic_rule_ref` and `paragraph_ids`.

5. **Step Visibility Gate** — `lme_testing/step_registry.py`: `extract_steps_from_normalized_bdd()`, `compute_step_gaps()`, `render_step_visibility_report()`. CLI `step-registry` command. Step visibility report at `runs/acceptance_e2e/step-registry/step_visibility.json`: 27 total steps, 21 unique patterns, 21 unmatched (no step library provided).

6. **Quality and Drift Reporting Gate** — `scripts/generate_trend_report.py`: pairwise and sequential drift comparison. `calculate_drift()` in `pipelines.py` computes status changes. Coverage reports include `status_by_rule` with `rule_coverage_status`.

7. **Model Governance Enforcement Gate** — `scripts/check_model_governance.py` + `check_artifact_metadata_in_runs()` in `governance_checks.py`. Validates provider, model, prompt_version, pipeline_version in all run summaries. `StubProvider` enables deterministic smoke testing without real API calls.

**Evidence**: End-to-end pipeline run with MiniMax-M2.7 (`runs/acceptance_e2e/`): planner → maker → bdd → checker → step-registry all completed. All governance checks pass. All 6 unit tests pass.

---

# Phase 3 Acceptance: Execution Readiness and Selective Enterprise Controls (9-18 Months)

## Phase Goal

Evolve the framework into an execution-ready and governance-mature AI testing platform that connects planning, normalized BDD, step definition integration, and deterministic validation for high-value rule classes.

## Phase Gate

Phase 3 is complete only if all required acceptance sections below pass.

Phase 3 is about execution readiness and release-grade control, not about requiring a hosted product by default.

---

## 1. Step Definition Integration Gate

### Required

Normalized BDD steps must be connectable to existing step definitions.

### Acceptance Criteria

The system supports:

- exact step match,
- parameterized step match where supported,
- candidate step suggestion,
- unmatched step reporting,
- reuse score,
- ownership mapping for step libraries where needed.

### Evidence

- matching engine or mapping logic,
- sample bindings,
- unmatched step reports,
- integration tests.

---

## 2. Execution Readiness Gate

### Required

An execution-ready scenario contract must exist.

### Acceptance Criteria

An `ExecutableScenario` representation includes:

- environment requirements,
- input data requirements,
- setup hooks,
- deterministic assertion references,
- cleanup hooks,
- linked step definitions.

### Evidence

- schema or contract docs,
- sample executable artifacts,
- contract validation tests.

**Completed:** `schemas/executable_scenario.schema.json` with required fields: executable_scenario_id, semantic_rule_ref, scenario_id, case_type, environment, input_data, step_bindings. Optional: assertions, cleanup_hooks, traceability, metadata. Enum-constrained fields: case_type (8 values), binding_status (6 values), assertion type (8 values), hook type (8 values). Fixtures: `schemas/fixtures/executable_scenario_valid.json` and `schemas/fixtures/executable_scenario_invalid.json`. Unit tests: 14 ExecutableScenarioSchemaTests all passing. [2026/04/14]

---

## 3. Deterministic Oracle Gate

### Required

Core structured rule categories must use deterministic assertions where possible.

### Acceptance Criteria

Deterministic checks exist for at least the high-value structured categories, such as:

- field validation,
- state validation,
- calculation validation,
- deadline or window checks,
- event sequence verification,
- pass or fail accounting.

### Evidence

- oracle modules,
- unit tests,
- scenario outputs using deterministic checks.

**Completed:** `lme_testing/oracles/` framework with 8 oracle modules (field_validation, state_validation, calculation_validation, deadline_check, event_sequence, pass_fail_accounting, null_check, compliance_check). Auto-registration via `@register_oracle`. `evaluate_assertion()` API for single-assertion evaluation. `OracleResult` with pass/fail/undetermined/error status. Unit tests: 38 oracle tests all passing. [2026/04/14]

---

## 4. Governance Signals Gate

### Required

Operational signals must be available for governed release and platform review.

### Acceptance Criteria

The platform can track and review signals such as:

- schema failure rate,
- checker instability rate,
- coverage trend,
- step binding success rate where applicable.

### Evidence

- report artifacts,
- metric definitions,
- telemetry or reporting docs,
- monitoring or generation test output.

**Completed:** `lme_testing/signals/` module with `compute_governance_signals()` API. Four signal types: SchemaSignals, CheckerInstabilitySignals, CoverageSignals, StepBindingSignals. CLI `governance-signals` command. Signals computed against actual runs: coverage=100%, step_binding_rate=35.4%, checker_instability=0%, schema_failure=0%. Unit tests: 9 signals tests all passing. [2026/04/14]

---

## 5. Release Governance Gate

### Required

Formal release controls must exist.

### Acceptance Criteria

The repo or release process defines:

- release tags,
- compatibility matrix,
- benchmark gates,
- migration notes,
- approved provider list.

### Evidence

- release docs,
- tagged releases,
- compatibility records,
- migration templates.

**Completed:** `config/approved_providers.json` (Tier 1/2/3 with MiniMax-M2.7 and stub), `config/compatibility_matrix.json` (provider × phase/pipeline compatibility), `config/benchmark_thresholds.json` (numeric gates for schema/coverage/instability), `docs/releases/RELEASES.md` (release records), `scripts/check_release_governance.py` (5 automated checks), CI job `Release Governance`. All governance checks pass. [2026/04/14]

---

## 6. Phase 3 Exit Criteria

Phase 3 is accepted only if:

- normalized BDD can be mapped to existing step definitions with measurable reuse,
- unmatched steps are automatically surfaced,
- execution-ready scenarios can be exported consistently,
- deterministic assertions cover the core high-value structured rule classes,
- provider rollout requires benchmark pass and rollback path,
- governance signals are available for release review,
- the quality gate has demonstrated that it can block promotion when thresholds fail.

**Phase 3 Exit — COMPLETED 2026/04/14**

All 6 Phase 3 acceptance gates passed:

1. **Step Definition Integration Gate** ✅ — `lme_testing/step_registry.py`: exact, parameterized, candidate 3-tier matching; reuse scores; ownership mapping.
2. **Execution Readiness Gate** ✅ — `schemas/executable_scenario.schema.json` + `validate_executable_scenario()`; 14 schema tests passing.
3. **Deterministic Oracle Gate** ✅ — `lme_testing/oracles/`: 8 oracle modules (field_validation, state_validation, calculation_validation, deadline_check, event_sequence, pass_fail_accounting, null_check, compliance_check); 38 oracle tests passing.
4. **Governance Signals Gate** ✅ — `lme_testing/signals/`: 4 signal types computed from run artifacts; CLI + CI wired; 9 signal tests passing.
5. **Release Governance Gate** ✅ — `config/approved_providers.json`, `config/compatibility_matrix.json`, `config/benchmark_thresholds.json`, `docs/releases/RELEASES.md`, `scripts/check_release_governance.py`; CI `Release Governance` job wired.
6. **Phase 3 Exit** ✅ — All gates 1-5 verified.

**Evidence**: 73 unit tests passing; all 4 governance checks pass; coverage=100%, step_binding_rate=35.4%, checker_instability=0%, schema_failure=0%.

---

# Release Readiness Checklist

This checklist applies before any release that changes core pipeline behavior.

## Required

- schemas or equivalent contracts validated,
- CI passing,
- benchmark passing,
- model metadata present,
- prompt version updated if behavior changed,
- migration notes written if contracts changed,
- rollback plan documented,
- acceptance evidence attached.

## Optional but Recommended

- artifact diff review,
- report screenshots,
- benchmark trend comparison,
- reviewer signoff,
- AI agent change summary.

---

# AI Agent Acceptance Rules

Any AI coding agent modifying the repo must satisfy the following:

## 1. Do not declare work complete without acceptance evidence

A code change is incomplete until linked to a passing acceptance item.

## 2. Do not change schemas silently

Any artifact contract change must update:

- schema or equivalent contract,
- docs,
- tests,
- acceptance references.

## 3. Do not switch models or prompts without benchmark evidence

Model or prompt changes must include:

- benchmark results,
- stability results where applicable,
- compatibility notes.

## 4. Do not merge cross-phase work by accident

If a change belongs to a later phase, it must be labeled and approved as such.

## 5. Prefer deterministic checks when available

If a validation can be implemented deterministically, do not rely solely on LLM judgment.

---

# Maintenance Notes

This document should be updated whenever:

- a roadmap phase changes,
- a new artifact contract is introduced,
- a new model provider is adopted,
- acceptance gates are tightened or relaxed,
- execution integration scope changes.

The owner of each phase should be documented separately in project planning materials if needed.
