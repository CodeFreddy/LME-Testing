# Implementation Plan

## Purpose

This document translates the phased roadmap into an execution-oriented implementation plan.

It is intended to serve as:

1. a developer-facing task breakdown,
2. a controlled execution guide for AI coding agents,
3. a practical bridge between roadmap goals and acceptance gates.

This document does **not** replace:

- `docs/roadmap.md` for strategic direction,
- `docs/architecture.md` for system boundaries,
- `docs/acceptance.md` for formal phase gates,
- `docs/model_governance.md` for model and prompt control,
- `docs/testing_governance.md` for test asset and review operations.

Instead, this file explains **how to execute roadmap work in governed tasks**.

---

## How to Use This Document

Each implementation task should be treated as a governed work unit.

For every task:

- identify the task ID and active phase,
- read the task goal,
- confirm prerequisites,
- check whether earlier phase gates or equivalent prerequisites are satisfied,
- honor the input contract,
- produce the expected output contract,
- run the required validation,
- record acceptance evidence,
- end with a structured self-evaluation against the acceptance criteria,
- do not expand scope beyond the task unless explicitly approved.

This document is especially important when different LLM APIs or AI coding agents are used, because it defines stable execution expectations that do not depend on chat context.

---

## Task Contract Template

Every implementation task in this file follows the same structure.

### Required fields

- **Task ID**
- **Goal**
- **Why it matters**
- **Prerequisites**
- **Input contract**
- **Output contract**
- **Implementation notes**
- **Validation**
- **Acceptance evidence**
- **Self-evaluation**
- **Out of scope**

### Governance rule

If a prerequisite is missing, do not fabricate it.
Stop, mark the dependency, and resolve the missing input first.

Durable task behavior must be represented in repo-readable files:

- prompts should live in governed prompt files,
- config should live in config files,
- schemas should live in schema files,
- acceptance requirements should live in docs or governed policy files.

Do not rely on hidden chat context as a substitute for repository contracts.

## Self-Evaluation Format

At the end of every substantial task implementation, produce a short self-evaluation that lists each relevant acceptance criterion and marks it as:

- PASS
- PARTIAL
- FAIL

If any criterion is FAIL, the task should not be treated as complete.

---

# Phase 1 - Baseline Control and Pipeline Hardening

## Objective

Stabilize the current document-to-rule-to-BDD design pipeline so that model changes, prompt changes, and repo evolution do not silently degrade output quality.

## Execution priority

Phase 1 work should generally proceed in this order:

1. governed rule validation,
2. baseline CI and smoke reproducibility,
3. source-anchor groundwork,
4. prompt and model provenance,
5. checker instability visibility.

This ordering reflects the current repo state.
It favors control and reproducibility before adding more workflow breadth.

---

## Task 1.1 - Rule Schema Validation

### Goal

Introduce governed schema validation for rule-layer artifacts.

### Why it matters

The upstream rule layer determines downstream quality.
Invalid `atomic_rule` or `semantic_rule` inputs can silently poison maker, checker, review, and reporting.

### Prerequisites

- current artifact examples exist,
- artifact fields are known,
- baseline schema directory or equivalent location is available.

### Input contract

- representative `atomic_rule` examples,
- representative `semantic_rule` examples,
- known required fields,
- known `rule_type` values.

### Output contract

- governed schema definitions for `atomic_rule` and `semantic_rule`,
- validation utility or validation workflow,
- a structured validation report format,
- valid and invalid fixtures,
- documentation of rule validation behavior.

### Implementation notes

Focus on:

- required fields,
- field types,
- traceability fields,
- `rule_type` enum constraints,
- version support.

Do not overfit schemas to a single temporary sample.

### Validation

- valid fixture passes,
- invalid fixture fails,
- invalid `rule_type` fails,
- missing required field fails,
- a structured validation report can be produced,
- downstream maker execution is blocked when validation fails.

### Acceptance evidence

- schema files committed,
- fixtures committed,
- validation logs or tests committed,
- sample structured validation report committed or demonstrated,
- references added to docs.

### Self-evaluation

Confirm each validation requirement as PASS / PARTIAL / FAIL.

### Out of scope

- advanced conflict reasoning,
- full semantic contradiction analysis,
- execution integration.

---

## Task 1.2 - Baseline CI and Smoke Flow

### Goal

Create a reliable baseline CI path for the current core workflow.

### Why it matters

Without CI, roadmap work has no durable safety net.

### Prerequisites

- minimal reproducible sample flow,
- Task 1.1 validation commands or equivalent scripts available.

### Input contract

- smallest baseline dataset or artifact set,
- schema validation tasks,
- reporting generation task.

### Output contract

CI workflow that runs at least:

- schema validation,
- minimal end-to-end smoke,
- report generation smoke,
- core unit tests for pipeline bootstrapping,
- and can execute the end-to-end smoke path without calling a real LLM API by using a deterministic stub provider or equivalent governed test double.

### Implementation notes

Prefer stable fixture-based smoke coverage over large expensive runs.

### Validation

- CI fails on broken schema,
- CI fails on broken smoke path,
- CI fails on broken report generation,
- smoke runs can be executed without making real LLM API calls.

### Acceptance evidence

- workflow files,
- passing CI logs,
- failing-case proof where useful.

### Self-evaluation

Confirm each CI requirement as PASS / PARTIAL / FAIL.

### Out of scope

- expensive full-dataset CI,
- production deployment pipeline.

---

## Task 1.3 - Structured Source Anchor Groundwork

### Goal

Introduce a stable source-level traceability key, such as a paragraph-level identifier or equivalent governed source anchor, that can flow through upstream and downstream artifacts.

### Why it matters

Traceability becomes actionable when artifacts can point to a stable source anchor rather than only broad source references.

### Prerequisites

- source parsing supports section or paragraph segmentation, or can be extended incrementally,
- trace fields exist or can be extended safely.

### Input contract

- source document segmentation output,
- existing traceability model,
- current rule artifact shape.

### Output contract

A traceability mechanism that carries a stable source anchor into:

- rule artifacts,
- maker outputs where applicable,
- checker outputs where applicable,
- reports,
- future BDD or step-related outputs.

### Implementation notes

For Phase 1, prefer additive metadata over disruptive redesign.
The exact field name may evolve, but the concept must remain stable and documented.

### Validation

- IDs are unique within governed scope,
- upstream artifacts retain the ID,
- downstream artifacts that already consume trace data preserve or surface the ID where practical,
- reports or machine-readable exports can surface or sort by it.

### Acceptance evidence

- artifact examples,
- uniqueness checks,
- docs updated.

### Self-evaluation

Confirm each traceability requirement as PASS / PARTIAL / FAIL.

### Out of scope

- full graph-based provenance service,
- strict enforcement across every downstream artifact before migration support exists.

---

## Task 1.4 - Prompt and Model Version Metadata

### Goal

Ensure generated artifacts record model and prompt provenance.

### Why it matters

Without provenance, behavior drift becomes difficult to diagnose and controlled rollback becomes weak.

### Prerequisites

- provider abstraction exists or is identifiable,
- governed prompt version policy exists or can be introduced.

### Input contract

- model configuration source,
- prompt ID and version source,
- pipeline version source.

### Output contract

Maker, checker, and rewrite artifacts include:

- provider name,
- model name,
- model version if available,
- prompt ID,
- prompt version,
- run timestamp,
- source artifact hash where applicable,
- pipeline version.

### Implementation notes

Do not scatter metadata logic across business modules.
Keep metadata generation centralized where possible.

### Validation

- generated artifacts contain required metadata,
- metadata is stable across repeated runs when inputs are unchanged except timestamp,
- tests confirm metadata presence,
- unknown or unsupported configured model names fail clearly before a live LLM call.

### Acceptance evidence

- sample generated artifacts,
- metadata tests,
- docs updated.

### Self-evaluation

Confirm each acceptance condition as PASS / PARTIAL / FAIL.

### Out of scope

- full model benchmarking,
- rollout automation.

---

## Task 1.5 - Checker Stability Visibility

### Goal

Make checker instability visible instead of implicit.

### Why it matters

Checker results may appear authoritative even when they are unstable.

### Prerequisites

- baseline sample set exists,
- checker can be invoked repeatedly with controlled inputs,
- baseline execution cost is small enough for repeated sampling.

### Input contract

- stable baseline input set,
- checker output comparison method,
- reporting or logging path that can surface instability.

### Output contract

A repeatable workflow that:

- runs checker multiple times on the same baseline set,
- compares results,
- marks unstable outcomes,
- exposes this signal in logs or reports.

### Implementation notes

Start with a small controlled baseline before expanding to broader statistical measurement.
Do not require double-running the full corpus by default.

### Validation

- repeated runs produce comparison data,
- differences are visible,
- unstable cases can be identified,
- the workflow remains practical for the chosen baseline set.

### Acceptance evidence

- comparison output examples,
- task documentation,
- report or log samples.

### Self-evaluation

Confirm each stability requirement as PASS / PARTIAL / FAIL.

### Out of scope

- full confidence engine,
- automated adjudication of instability.

---

# Phase 2 - Planned Test Design and Normalized BDD Platform

## Objective

Expand from stable design artifacts into reusable planning, normalized BDD generation, and controlled team-pilot workflows.

## Execution rule

Phase 2 must not introduce a new LLM-driven stage unless the stage has:

- a defined artifact contract,
- schema or equivalent validation logic,
- traceability expectations,
- reviewable outputs.

This rule is especially important for planner outputs and normalized BDD artifacts.

---

## Task 2.1 - Multi-Document Ingestion and Source-Aware Rule Path

### Goal

Support multiple document classes with explicit ingestion expectations and preserve a governed path from source documents into rule-layer artifacts.

### Why it matters

Enterprise testing cannot depend on a single document shape, and Phase 2 expansion is only useful if traceability survives the transition from documents into `atomic_rule` and `semantic_rule` artifacts.

### Prerequisites

- Phase 1 validation and traceability foundations,
- document classes chosen for initial support.

### Input contract

For each chosen document class:

- representative samples,
- parsing assumptions,
- rule extraction expectations,
- known failure modes.

### Output contract

Document-class-aware ingestion support with:

- documented parsing strategy,
- documented extraction constraints,
- sample source segmentation outputs,
- source-aware rule extraction outputs,
- validation notes.

### Implementation notes

Start with a small number of classes.
Do not claim generality too early.

### Validation

- multiple document classes process successfully,
- each class has documented failure modes,
- outputs remain traceable and schema-valid,
- source anchors survive into governed rule artifacts where applicable.

### Acceptance evidence

- sample documents,
- sample outputs,
- class-specific notes,
- tests or fixtures.

### Self-evaluation

Confirm each ingestion requirement as PASS / PARTIAL / FAIL.

### Out of scope

- unlimited file-type support,
- OCR-heavy universal ingestion.

---

## Task 2.2 - Planning Layer

### Goal

Add a planner stage between semantic rules and scenario generation.

### Why it matters

Planning introduces explicit test intent rather than generating scenarios directly from rules without intermediate reasoning structure.

### Prerequisites

- semantic rules are stable,
- planner output schema can be defined before planner rollout,
- traceability from planner outputs to semantic rules is modelled.

### Input contract

- semantic rules,
- rule metadata,
- risk and priority heuristics where available.

### Output contract

Versioned planner artifacts describing:

- test objective,
- risk level,
- coverage intent,
- scenario family,
- dependency notes,
- recommended validation strategy.

### Implementation notes

Planner outputs should remain structured and reviewable.
Do not let planner become a free-form narrative layer.

### Validation

- planner artifacts validate,
- planner artifacts trace to semantic rules,
- planner outputs can be reviewed independently,
- downstream generation can consume them.

### Acceptance evidence

- planner schema,
- planner samples,
- integration tests to downstream generation.

### Self-evaluation

Confirm each planning requirement as PASS / PARTIAL / FAIL.

### Out of scope

- full autonomous test management,
- execution orchestration.

---

## Task 2.3 - Normalized BDD Contract

### Goal

Introduce a stable BDD representation independent of final output syntax.

### Why it matters

BDD must become a governed artifact, not only a presentation format.
Without a normalized contract, `.feature` output becomes a fragile syntax-level dependency.

### Prerequisites

- planning outputs or stable generation inputs exist,
- BDD output patterns are understood,
- schema for normalized BDD can be defined before it becomes the default path.

### Input contract

- planner or semantic inputs,
- current BDD output examples,
- style expectations.

### Output contract

A normalized BDD artifact contract with:

- schema,
- traceability,
- scenario structure,
- style metadata where needed.

### Implementation notes

The normalized BDD artifact should be reusable across future renderers and step-integration logic.
Do not treat raw Gherkin text as the only governed representation once this task is introduced.

### Validation

- valid BDD artifacts pass schema,
- invalid ones fail,
- at least one renderer or exporter consumes the normalized representation.

### Acceptance evidence

- schema,
- fixtures,
- renderer or export proof,
- docs updated.

### Self-evaluation

Confirm each BDD contract requirement as PASS / PARTIAL / FAIL.

### Out of scope

- full execution binding,
- automatic step generation as a required baseline.

---

## Task 2.4 - BDD Style Learning

### Goal

Learn reusable style patterns from existing BDD assets without hardcoding everything manually.

### Why it matters

Teams often already have conventions that should be preserved.

### Prerequisites

- existing `.feature` examples or equivalent BDD assets,
- normalized BDD contract direction established.

### Input contract

- representative feature files,
- style attributes to observe,
- extraction procedure for style features.

### Output contract

A governed style artifact, such as a style profile or style guide, that can inform generation without becoming an opaque hidden dependency.

### Implementation notes

Style-learning outputs should be inspectable and versioned.
They should not be hidden inside prompts only.

### Validation

- extracted style patterns are reviewable,
- generation can reference them,
- results remain within normalized BDD contract.

### Acceptance evidence

- style profile artifacts,
- review notes,
- examples before and after style adoption.

### Self-evaluation

Confirm each style-learning requirement as PASS / PARTIAL / FAIL.

### Out of scope

- unrestricted stylistic self-optimization.

---

## Task 2.5 - Step Registry Visibility

### Goal

Introduce early visibility into step-definition reuse needs without treating full execution binding as a Phase 2 requirement.

### Why it matters

Teams need to know whether generated BDD is likely to reuse existing execution assets before Phase 3 mapping and execution-readiness work begins.

### Prerequisites

- normalized BDD artifacts exist,
- representative step assets or step conventions are available.

### Input contract

- normalized BDD scenarios,
- sample step assets or step definitions,
- early matching assumptions.

### Output contract

Lightweight step-visibility outputs showing:

- candidate reusable steps,
- obvious gaps,
- implementation-needed markers,
- early mapping notes for later Phase 3 work.

### Implementation notes

Keep this phase lightweight and reviewable.
Do not claim full exact-match or parameterized-match coverage yet.

### Validation

- step visibility outputs are reproducible,
- gaps are visible,
- downstream teams can inspect the results.

### Acceptance evidence

- sample visibility artifacts,
- matching notes,
- docs updated.

### Self-evaluation

Confirm each step-visibility requirement as PASS / PARTIAL / FAIL.

### Out of scope

- full step registry,
- full binding engine,
- automatic step implementation.

---

## Task 2.6 - Quality Dashboards and Drift Views

### Goal

Enhance reporting so teams can see stability, drift, and traceability patterns.

### Why it matters

Governed workflows need visibility, not just final pass or fail summaries.

### Prerequisites

- stable reporting layer,
- traceability data,
- checker stability signal.

### Input contract

- current reports,
- benchmark history or repeated run history,
- traceability fields.

### Output contract

Reporting extensions that can show, at minimum:

- rule-type coverage view,
- unstable checker decisions,
- run-to-run drift,
- traceability drill-down,
- machine-readable export.

### Implementation notes

Prefer traceability and governance value over decorative visualization.

### Validation

- reports render correctly,
- exports are usable,
- drift signals are visible.

### Acceptance evidence

- report samples,
- export samples,
- screenshots if needed,
- generation tests.

### Self-evaluation

Confirm each reporting requirement as PASS / PARTIAL / FAIL.

### Out of scope

- heavy BI platform integration.

---

# Phase 3 - Execution Readiness and Selective Enterprise Controls

## Objective

Extend from design and planning artifacts into execution integration, deterministic validation for high-value rule classes, and release-grade governance controls.

---

## Task 3.1 - Step Definition Registry

### Goal

Build a governed registry of existing step definitions for reuse and integration.

### Why it matters

Enterprise adoption depends on connecting generated BDD to real executable assets.

### Prerequisites

- normalized BDD contract exists,
- representative step definition libraries are available.

### Input contract

- step definition source set,
- parsing assumptions,
- output registry schema.

### Output contract

A governed step registry that supports:

- step signature inventory,
- ownership or source mapping,
- parameter awareness where possible,
- reuse-oriented lookup.

### Implementation notes

The registry should help identify reuse opportunities before generating new steps.

### Validation

- registry is generated reproducibly,
- representative steps are captured,
- lookup works for sample BDD outputs.

### Acceptance evidence

- registry artifact,
- parser tests,
- integration examples.

### Self-evaluation

Confirm each registry requirement as PASS / PARTIAL / FAIL.

### Out of scope

- automatic execution of all step bindings.

---

## Task 3.2 - Step Mapping and Gap Analysis

### Goal

Map normalized BDD steps to existing step definitions and expose gaps.

### Why it matters

Teams need to know what is reusable and what still needs implementation.

### Prerequisites

- Task 3.1 complete,
- normalized BDD artifacts available.

### Input contract

- normalized BDD scenarios,
- step registry,
- matching rules.

### Output contract

Mapping results showing:

- exact matches,
- parameterized matches where supported,
- unmatched steps,
- candidate suggestions,
- gap summary.

### Implementation notes

Unmatched steps should be explicit and reviewable.
Do not bury them in free-form logs.

### Validation

- mapping results are reproducible,
- unmatched steps are visible,
- reuse is measurable.

### Acceptance evidence

- mapping samples,
- diff or gap reports,
- matching tests.

### Self-evaluation

Confirm each mapping requirement as PASS / PARTIAL / FAIL.

### Out of scope

- automatic step implementation.

---

## Task 3.3 - Executable Scenario Contract

### Goal

Introduce an execution-ready artifact that extends normalized BDD into a runtime integration contract.

### Why it matters

Design artifacts and executable artifacts should not be conflated.

### Prerequisites

- normalized BDD exists,
- step mapping exists,
- execution concerns have been modeled.

### Input contract

- normalized BDD artifacts,
- step mappings,
- environment and setup expectations,
- assertion references.

### Output contract

An execution-ready scenario artifact that may include:

- environment requirements,
- input data requirements,
- setup hooks,
- cleanup hooks,
- deterministic assertion references,
- step bindings.

### Implementation notes

Keep this contract explicit and bounded.
Do not let it become a vague future execution bucket.

### Validation

- contract validates,
- required execution metadata exists,
- export is consistent.

### Acceptance evidence

- schema or contract definition,
- sample artifacts,
- validation tests.

### Self-evaluation

Confirm each execution-contract requirement as PASS / PARTIAL / FAIL.

### Out of scope

- full distributed execution engine.

---

## Task 3.4 - Deterministic Oracle Layer

### Goal

Move core runtime truth into deterministic assertions wherever possible for high-value structured rule classes.

### Why it matters

Execution correctness should not depend purely on LLM judgment.

### Prerequisites

- execution-ready contract exists,
- structured rule categories identified.

### Input contract

- rule categories,
- expected observable behaviors,
- assertion scope.

### Output contract

Deterministic validation modules for core structured categories, such as:

- field validation,
- state validation,
- deadline and window checks,
- calculation checks,
- sequence checks,
- pass or fail accounting.

### Implementation notes

Start with the most structured and highest-value categories first.
Do not build a generic framework before domain-critical cases justify it.

### Validation

- assertions are test-covered,
- deterministic outputs are reproducible,
- integration with execution-ready artifacts is clear.

### Acceptance evidence

- oracle modules,
- tests,
- sample scenario validations.

### Self-evaluation

Confirm each deterministic-oracle requirement as PASS / PARTIAL / FAIL.

### Out of scope

- full autonomous judgment of ambiguous cases.

---

## Task 3.5 - Selective Governance Signals

### Goal

Track the minimum operational signals needed for governed release and platform review.

### Why it matters

The platform needs enough observability for controlled operation, but not every enterprise-style metric is justified immediately.

### Prerequisites

- traceability and reporting exist,
- checker stability visibility exists,
- release review workflow exists.

### Input contract

- benchmark history,
- artifact quality metrics,
- checker stability metrics,
- mapping or reuse metrics where applicable.

### Output contract

A governed metrics and review package that can surface signals such as:

- schema failure rate,
- checker instability rate,
- coverage trend,
- step binding success rate where applicable.

### Implementation notes

Keep metrics explicit, reviewable, and tied to real decisions.
Avoid introducing a heavy observability program before the platform needs it.

### Validation

- metrics can be produced reproducibly,
- reports remain reviewable,
- release discussions can rely on the signals.

### Acceptance evidence

- metric definitions,
- report samples,
- docs updated.

### Self-evaluation

Confirm each governance-signal requirement as PASS / PARTIAL / FAIL.

### Out of scope

- full enterprise observability stack,
- product-scale operations dashboards by default.

---

## Task 3.6 - Quality Gate and Regression Governance

### Goal

Formalize release-ready gating for model behavior, artifact quality, and integration stability.

### Why it matters

As the platform grows, changes must be promoted through governed quality signals rather than intuition.

### Prerequisites

- benchmark infrastructure exists,
- traceability and reporting exist,
- model governance is enforced.

### Input contract

- benchmark history,
- artifact quality metrics,
- checker stability metrics,
- mapping and reuse metrics where applicable.

### Output contract

A governed quality-gate process that can block promotion when:

- schema validity drops,
- checker instability rises,
- benchmark thresholds fail,
- regression patterns appear,
- integration quality degrades.

### Implementation notes

Keep thresholds explicit and reviewable.

### Validation

- failing thresholds block promotion,
- successful runs produce reviewable evidence,
- rollback path remains documented.

### Acceptance evidence

- gate configuration,
- blocked-run examples,
- promotion examples,
- docs updated.

### Self-evaluation

Confirm each quality-gate requirement as PASS / PARTIAL / FAIL.

### Out of scope

- fully autonomous release approval.

---

## Optional Exploration Tasks (Do Not Treat as Core Path)

These tasks may be useful later, but they are not core requirements for the main platform path.

### Optional A - Review Package Exchange

Possible future direction once local review workflows are stable enough that cross-session and cross-reviewer exchange solves a real problem.

### Optional B - Hosted Review and Audit Service

Possible future direction if the repo eventually justifies deployable multi-user review and audit workflows.

### Optional C - Auto Step Definition Generation

Possible future direction once step registry and gap analysis are mature.

### Optional D - Prompt Optimization Assistant

Possible future direction once enough benchmark history exists to justify governed optimization.

### Optional E - Domain Packages and Specialization Layers

Possible future direction once the base platform is stable and multiple target domains require specialization.

These optional tasks should not displace core governance, traceability, and execution-readiness work.

# Phase Gate Awareness

Implementation work should respect formal phase gates where they exist.

Before starting work in a later phase:

- check whether the prior phase gate has been signed off,
- if a required gate record is missing, flag it,
- do not quietly treat later-phase work as normal completion when earlier phase criteria are still open.

This does not forbid exploratory work, but it does forbid presenting governed later-phase work as fully complete when prerequisite phase gates remain unsigned.

# Implementation Review Checklist

Before merging any implementation task, confirm:

- task ID is identified,
- prerequisites were satisfied,
- earlier phase gates or equivalent prerequisites were checked,
- input contract was honored,
- output contract was produced,
- validation was run,
- acceptance evidence exists,
- a structured self-evaluation was produced,
- out-of-scope boundaries were respected,
- docs were updated where required.

If any of these are unclear, the task is not implementation-ready.

---

# AI Agent Execution Rules

Any AI coding agent following this plan must obey the following:

## 1. Never fabricate missing prerequisites

If an input contract depends on a file, schema, benchmark, artifact, or earlier phase gate that does not exist, stop and surface the missing dependency.

## 2. Do not silently widen scope

Stay within the current task and phase unless a human explicitly expands scope.

## 3. Do not replace contracts with chat context

All durable behavior must be captured in repo-readable files, not hidden in conversation state.

## 4. Prefer deterministic validation when available

If a contract can be validated deterministically, do not rely only on model judgment.

## 5. Keep outputs reviewable

Generated outputs, configs, schemas, and summaries must remain understandable by human reviewers.

## 6. End with explicit completion status

For substantial work, provide a short self-evaluation with PASS, PARTIAL, or FAIL per relevant acceptance item.

---

# Summary

This implementation plan turns the strategic roadmap into governed execution tasks.

It preserves the governance-first approach of the repo while adding task-level execution structure that is especially useful for:

- developers,
- reviewers,
- and AI coding agents working across different LLM APIs.

The key principle is simple:

**strategic direction belongs in the roadmap, system boundaries belong in architecture, governance belongs in policy docs, and execution detail belongs here.**
