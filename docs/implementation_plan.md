# Implementation Plan

## Purpose

This document translates the high-level roadmap into a task-oriented execution plan.

It is intended to serve as:

1. an implementation guide for developers,
2. a task contract reference for AI coding agents,
3. a review aid for acceptance and phase-gate validation.

This document does **not** replace:
- `docs/roadmap.md`
- `docs/architecture.md`
- `docs/acceptance.md`
- `docs/model_governance.md`
- `docs/testing_governance.md`
- `docs/prompt_lifecycle.md`
- `docs/agent_guidelines.md`

Instead, it provides the **execution layer** that sits beneath them.

---

## How to Use This Document

For any non-trivial change:

1. identify the roadmap phase,
2. identify the task ID,
3. read the task input contract,
4. implement only within declared scope,
5. produce the required outputs,
6. run the defined checks,
7. attach acceptance evidence.

If a task depends on missing upstream artifacts, do not invent them silently.  
Stop and explicitly identify the missing prerequisite.

---

## Global Execution Rules

These rules apply to all tasks in this file.

### 1. Every task must define contracts
Each task must define:
- input contract,
- output contract,
- implementation notes,
- acceptance criteria,
- evidence expectations.

### 2. No task may silently expand scope
A task may not absorb future-phase work just because it seems convenient.

### 3. Structured artifacts remain governed
Any artifact introduced by a task must be:
- named,
- documented,
- versionable where needed,
- and linked back to the appropriate schema or contract layer.

### 4. Traceability must improve, not weaken
Every material change should either preserve or strengthen traceability.

### 5. Model-facing work must remain benchmark-governed
Any task that changes model behavior, prompt behavior, or structured output assumptions must also satisfy model governance requirements.

---

## Phase Overview

### Phase 1 — Stabilization
Focus:
- rule validation,
- schema enforcement,
- metadata,
- CI,
- traceability hardening,
- model/prompt stability controls.

### Phase 2 — Planning and BDD Platform
Focus:
- multi-document ingestion,
- planning layer,
- normalized BDD,
- collaborative review exchange,
- style learning,
- step registry,
- checker stability visibility,
- richer reporting.

### Phase 3 — Enterprise Integration
Focus:
- domain packaging,
- step-definition integration,
- execution-ready contracts,
- deterministic oracle growth,
- quality gates,
- regression analysis.

---

# Phase 1 Tasks

## Task P1.1 — Artifact Schema Validation

### Goal
Introduce formal schema validation for all core structured artifacts.

### Input Contract
- existing core artifact definitions,
- current generated samples if available,
- repo governance docs.

### Output Contract
- versioned schema files for:
  - atomic rule
  - semantic rule
  - maker output
  - checker output
  - review output
- validation entry points,
- valid and invalid fixtures,
- schema validation tests.

### Implementation Notes
- prefer backward-tolerant evolution where possible,
- do not weaken contracts silently,
- ensure invalid fixtures fail clearly.

### Acceptance Criteria
- all core artifact schemas exist,
- valid samples pass validation,
- invalid samples fail validation,
- CI can run schema validation.

### Evidence
- schema files,
- fixtures,
- test logs,
- CI output.

---

## Task P1.2 — Rule Validation Pipeline

### Goal
Insert a governed validation layer between extraction outputs and downstream semantic use.

### Input Contract
- extraction outputs,
- current rule normalization flow,
- schema definitions from Task P1.1.

### Output Contract
A formal pipeline step that performs:
- schema validation,
- rule_type enum validation,
- duplicate candidate detection,
- trace reference validation.

### Implementation Notes
- validation failures must be visible,
- do not auto-heal malformed artifacts silently,
- duplicate detection may be heuristic but must be observable.

### Acceptance Criteria
- invalid rule artifacts hard-fail the validation step,
- invalid enum values hard-fail the validation step,
- duplicate candidates are surfaced in machine-readable output,
- broken trace references are surfaced.

### Evidence
- validation output samples,
- failing fixtures,
- pipeline test logs.

---

## Task P1.3 — Model and Prompt Metadata

### Goal
Ensure all model-driven outputs record sufficient metadata for auditability.

### Input Contract
- current maker/checker/rewrite paths,
- provider abstraction behavior,
- model governance requirements.

### Output Contract
All governed generated artifacts contain:
- provider,
- model name,
- model version if available,
- prompt ID,
- prompt version,
- run timestamp,
- source artifact hash,
- pipeline version,
- module name.

### Implementation Notes
- metadata presence must be testable,
- avoid provider-specific leakage into business logic.

### Acceptance Criteria
- maker and checker outputs include metadata,
- rewrite outputs include metadata when applicable,
- metadata is validated in tests,
- missing metadata fails governed validation.

### Evidence
- generated artifacts,
- tests,
- validation output.

---

## Task P1.4 — Baseline CI and Smoke Flow

### Goal
Create a reproducible baseline CI path for the minimal supported workflow.

### Input Contract
- minimal baseline artifacts or fixture set,
- current pipeline entrypoints,
- testing and acceptance docs.

### Output Contract
CI jobs covering:
- schema validation,
- minimal end-to-end smoke,
- reporting smoke,
- core unit tests.

### Implementation Notes
- keep the baseline small and reproducible,
- use fixtures where possible,
- network-dependent model calls should be stubbed or controlled for CI reliability.

### Acceptance Criteria
- CI runs on every relevant change,
- minimal smoke flow is reproducible,
- failures are attributable to stage,
- reporting path is covered.

### Evidence
- workflow files,
- CI logs,
- smoke artifacts.

---

## Task P1.5 — Structured Traceability Key

### Goal
Strengthen traceability with a stable, explicit source-level identifier strategy.

### Input Contract
- source segmentation logic,
- rule normalization pipeline,
- reporting requirements.

### Output Contract
A traceability strategy that propagates a stable source-level identifier through:
- source parsing,
- atomic rule,
- semantic rule,
- maker output,
- checker output,
- report output.

### Implementation Notes
- identifiers must remain unique within intended scope,
- sortability and audit usability are preferred,
- downstream artifacts must preserve the key rather than recompute ad hoc variants.

### Acceptance Criteria
- traceability key appears in core downstream artifacts,
- traceability is testable end-to-end,
- duplicate or broken identifiers are detectable.

### Evidence
- artifact samples,
- validation tests,
- report examples.

---

## Task P1.6 — Checker Stability Visibility

### Goal
Make checker instability observable on a controlled baseline.

### Input Contract
- checker module,
- baseline fixture set,
- reporting or benchmark output path.

### Output Contract
A controlled comparison flow that:
- runs checker more than once on the same baseline,
- compares outputs,
- surfaces unstable findings.

### Implementation Notes
- stability is a signal, not a replacement for correctness,
- do not hide instability behind a single final score.

### Acceptance Criteria
- repeated checker runs can be compared,
- unstable results are surfaced in machine-readable output,
- the process is documented.

### Evidence
- comparison outputs,
- benchmark script output,
- docs update.

---

# Phase 2 Tasks

## Task P2.1 — Multi-Document Ingestion

### Goal
Support multiple document classes with explicit ingestion strategies.

### Input Contract
- current source ingestion behavior,
- representative sample documents for at least 3 classes,
- extraction constraints per class.

### Output Contract
Document-class-aware ingestion definitions covering:
- parsing strategy,
- extraction constraints,
- expected rule patterns,
- known failure modes.

### Implementation Notes
- do not assume one extraction policy fits all document classes,
- keep class behavior explicit and reviewable.

### Acceptance Criteria
- at least 3 document classes are supported,
- each class has documented parsing and extraction behavior,
- extraction outputs remain governed.

### Evidence
- configs or code,
- class-specific docs,
- sample outputs.

---

## Task P2.2 — Planning Layer

### Goal
Introduce a planner stage between semantic rules and BDD generation.

### Input Contract
- semantic rules,
- current maker assumptions,
- roadmap phase guidance.

### Output Contract
A planner artifact that includes:
- objective,
- priority,
- risk level,
- coverage intent,
- scenario family,
- dependency notes,
- validation strategy hints.

### Implementation Notes
- planner output is a governed artifact,
- do not collapse planner output into unstructured prompt text.

### Acceptance Criteria
- planner schema exists,
- planner output is traceable,
- planner output is consumed by downstream generation,
- planner behavior is benchmarkable.

### Evidence
- planner schema,
- planner fixtures,
- integration tests.

---

## Task P2.3 — Normalized BDD Contract

### Goal
Define a stable BDD contract independent of final renderer or execution integration.

### Input Contract
- planner output,
- current maker output,
- existing feature-file style references if available.

### Output Contract
A normalized BDD artifact that preserves:
- scenario intent,
- step structure,
- traceability,
- metadata,
- execution-agnostic representation.

### Implementation Notes
- keep it renderer-independent,
- do not bind directly to a single feature syntax assumption if future flexibility is needed.

### Acceptance Criteria
- normalized BDD schema exists,
- generated BDD validates,
- at least one renderer can consume it,
- traceability is preserved.

### Evidence
- schema,
- output samples,
- renderer tests.

---

## Task P2.4 — BDD Style Learning

### Goal
Learn reusable BDD style patterns from existing feature assets.

### Input Contract
- existing `.feature` corpus if available,
- current generated BDD artifacts,
- normalized BDD contract.

### Output Contract
Style-learning outputs such as:
- style profile data,
- template profile summary,
- style guide notes,
- optional renderer preferences.

### Implementation Notes
- learned style should guide rendering, not corrupt semantic intent,
- style artifacts should remain reviewable and replaceable.

### Acceptance Criteria
- style profiles can be generated from sample features,
- rendering can consume learned style preferences,
- semantic content remains stable when style changes.

### Evidence
- style artifacts,
- before/after render comparisons,
- review notes.

---

## Task P2.5 — Step Registry

### Goal
Build a governed view of existing step-definition inventory for future reuse.

### Input Contract
- existing step definition sources if available,
- normalized BDD outputs,
- naming and ownership expectations.

### Output Contract
A step registry artifact capturing:
- step signatures,
- parameter patterns,
- ownership or source path,
- reuse hints,
- match candidates.

### Implementation Notes
- registry is descriptive first, not yet full execution binding,
- unmatched steps must remain visible.

### Acceptance Criteria
- step inventory can be produced,
- step matching categories can be reported,
- unmatched step candidates are surfaced,
- reuse analysis exists.

### Evidence
- registry output,
- diff or match reports,
- integration tests.

---

## Task P2.6 — Review Exchange and Merge

### Goal
Support asynchronous review beyond a single local session.

### Input Contract
- current review artifact model,
- review workflow assumptions,
- conflict-handling needs.

### Output Contract
A review exchange mechanism supporting:
- export,
- import,
- merge,
- conflict surfacing.

### Implementation Notes
- keep review artifacts structured,
- merge behavior must be explicit and testable.

### Acceptance Criteria
- review packages can be exported and imported,
- merge conflicts can be surfaced,
- structured review integrity is preserved.

### Evidence
- package format,
- merge tests,
- conflict examples.

---

## Task P2.7 — Quality Dashboard and Drift Reporting

### Goal
Provide pilot-grade visibility into coverage, drift, and instability.

### Input Contract
- checker output,
- traceability data,
- benchmark comparison data.

### Output Contract
Reports or machine-readable summaries covering:
- rule-type coverage,
- unstable checker findings,
- baseline drift,
- document-class breakdown,
- traceability drill-down,
- JSON/CSV export.

### Implementation Notes
- metrics should remain attributable to artifacts,
- do not hide drift behind aggregated pass/fail alone.

### Acceptance Criteria
- reports surface instability and drift,
- exports are usable downstream,
- traceability remains visible.

### Evidence
- report samples,
- exported files,
- report tests.

---

# Phase 3 Tasks

## Task P3.1 — Domain Packaging

### Goal
Support domain-aware configuration without coupling the whole platform to one domain.

### Input Contract
- current pipeline configuration,
- representative domain differences,
- governance expectations.

### Output Contract
A domain-aware configuration model that can express:
- domain-specific ingestion hints,
- rule interpretation differences,
- BDD rendering preferences,
- review/reporting defaults where appropriate.

### Implementation Notes
- domain customization must remain explicit,
- shared core contracts should not be duplicated unnecessarily.

### Acceptance Criteria
- domain configuration can be introduced without breaking shared flow,
- at least one domain override path is testable,
- core artifacts remain compatible.

### Evidence
- config examples,
- domain tests,
- compatibility notes.

---

## Task P3.2 — Step Binding and Integration Readiness

### Goal
Move from step inventory to actual step binding readiness.

### Input Contract
- normalized BDD outputs,
- step registry,
- ownership expectations,
- current runtime constraints if known.

### Output Contract
A governed binding result indicating:
- exact matches,
- parameterized matches,
- unmatched steps,
- implementation-needed markers,
- reuse score,
- integration-ready summaries.

### Implementation Notes
- do not generate false certainty for unmatched steps,
- binding results should remain auditable.

### Acceptance Criteria
- step binding can be evaluated,
- unmatched steps are clearly reported,
- reuse metrics are available,
- integration summaries are exportable.

### Evidence
- binding reports,
- examples,
- tests.

---

## Task P3.3 — Executable Scenario Contract

### Goal
Introduce an execution-ready handoff artifact without collapsing design and execution layers.

### Input Contract
- normalized BDD,
- step binding outputs,
- environment and assertion requirements,
- long-term architecture guidance.

### Output Contract
An `ExecutableScenario` contract including:
- environment requirements,
- setup hooks,
- data requirements,
- linked step definitions,
- deterministic assertion references,
- cleanup expectations.

### Implementation Notes
- keep execution contract explicit,
- do not make it a raw prompt output without schema and review.

### Acceptance Criteria
- execution contract exists and is schema-validatable,
- sample scenarios can be exported,
- traceability is preserved from source to executable contract.

### Evidence
- schema,
- samples,
- validation tests.

---

## Task P3.4 — Deterministic Oracle Expansion

### Goal
Increase deterministic validation coverage for structured rule classes.

### Input Contract
- structured rule categories,
- existing validation logic,
- execution contract direction.

### Output Contract
Deterministic validation modules for core categories such as:
- field validation,
- state validation,
- calculation validation,
- deadline/window checks,
- event sequence checks,
- pass/fail accounting.

### Implementation Notes
- prioritize deterministic checks where clear structure exists,
- do not delegate deterministic truth to LLMs if avoidable.

### Acceptance Criteria
- at least core structured categories are supported,
- tests exist for deterministic modules,
- execution-facing artifacts can reference deterministic checks.

### Evidence
- modules,
- tests,
- sample usage.

---

## Task P3.5 — Quality Gate

### Goal
Create a governed promotion gate for generated BDD and integration outputs.

### Input Contract
- normalized BDD,
- step binding data,
- checker stability signals,
- benchmark summaries.

### Output Contract
A quality-gate decision framework that can mark outputs as:
- acceptable,
- review-required,
- unstable,
- implementation-incomplete,
- blocked.

### Implementation Notes
- gate logic should remain transparent,
- quality gates complement human review rather than silently replace it.

### Acceptance Criteria
- gate decisions are reproducible,
- decision reasons are visible,
- outputs can be filtered by gate status.

### Evidence
- gate outputs,
- test cases,
- report examples.

---

## Task P3.6 — Cross-Run Regression Analysis

### Goal
Track quality movement across runs rather than only within a single run.

### Input Contract
- benchmark history,
- report outputs,
- checker stability results,
- traceability keys.

### Output Contract
Cross-run analysis artifacts covering:
- drift,
- stability changes,
- reuse changes,
- unmatched-step trend,
- quality-gate trend.

### Implementation Notes
- preserve run metadata,
- comparisons should remain attributable and reviewable.

### Acceptance Criteria
- multiple runs can be compared,
- regression summaries are available,
- trend outputs are exportable.

### Evidence
- history artifacts,
- trend reports,
- comparison tests.

---

## Task P3.7 — Prompt Improvement Loop (Optional / Experimental)

### Goal
Create a controlled, non-default mechanism for proposing prompt improvements from observed failures.

### Input Contract
- failure analyses,
- benchmark regressions,
- prompt lifecycle policy,
- model governance policy.

### Output Contract
A governed candidate-improvement flow that can produce:
- candidate prompt change proposals,
- linked failure evidence,
- validation requirements,
- non-default recommendation records.

### Implementation Notes
- this task is experimental,
- it must not auto-promote prompt changes,
- all proposals remain subject to prompt lifecycle and model governance rules.

### Acceptance Criteria
- prompt-improvement proposals are clearly marked as proposals,
- no automatic production promotion occurs,
- linked validation expectations are present.

### Evidence
- candidate proposal artifacts,
- workflow docs,
- governance references.

---

## Cross-Task Acceptance Rules

These rules apply across all phases.

### 1. Every task needs evidence
No task is done without:
- tests,
- artifacts,
- docs updates where relevant,
- and an acceptance mapping.

### 2. Missing prerequisites must be reported
If a task cannot proceed because an upstream artifact or contract is missing, the gap must be made explicit.

### 3. Contract changes require coordinated updates
If a task changes a schema, prompt contract, registry structure, or output contract, update:
- tests,
- docs,
- acceptance references,
- migration notes where needed.

### 4. Provider-specific behavior must remain isolated
Tasks must not introduce provider-specific coupling into business modules.

### 5. Deterministic logic should grow over time
Where responsibilities can become deterministic, future tasks should move in that direction.

---

## Suggested Tracking Format

Each task implementation should produce a structured summary:

- Task ID
- Title
- Scope
- Files changed
- Inputs used
- Outputs produced
- Tests run
- Acceptance items satisfied
- Known limitations
- Follow-up tasks
- Rollback notes

This can be used in PRs, issue templates, or internal project tracking.

---

## Summary

This document converts the roadmap into an execution-oriented plan.

The roadmap explains **where the system is going**.  
This implementation plan explains **how to move phase by phase without losing contracts, governance, or reviewability**.

It is especially important for AI-assisted development because it:
- reduces ambiguity,
- enforces phase discipline,
- makes dependencies explicit,
- and ties work to testable outcomes.
