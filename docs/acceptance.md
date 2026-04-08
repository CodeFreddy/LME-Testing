# Acceptance Criteria and Delivery Gates

## Purpose

This document defines the acceptance criteria, delivery gates, and required evidence for the upgrade roadmap.

It is intended for:

1. developers implementing roadmap items,
2. reviewers validating delivery quality,
3. AI coding agents making changes under controlled contracts.

This document should be read together with:

- `docs/roadmap.md`
- `docs/architecture.md`
- `docs/model_governance.md`
- `docs/agent_guidelines.md`

---

## Acceptance Philosophy

A roadmap item is **not complete** because code exists.

A roadmap item is considered complete only when:

- the intended behavior is defined,
- the implementation is merged,
- the artifact contract is respected,
- tests or validation gates pass,
- required documentation is updated,
- and acceptance evidence is available.

Every acceptance section below includes:

- **required outcomes**
- **required evidence**
- **hard gates**
- **non-goals**

---

## Global Delivery Gates

These gates apply to all phases.

### G1. Schema integrity gate

No artifact-producing module may be accepted unless:

- its schema is defined or updated,
- schema validation is automated,
- failure cases are covered by tests.

### G2. Reproducibility gate

No LLM-driven workflow change may be accepted unless:

- model and prompt metadata are recorded,
- the relevant baseline suite can be rerun,
- outputs can be compared against prior known-good runs.

### G3. Documentation gate

No new capability may be accepted unless:

- repo docs are updated,
- module boundaries are explained where relevant,
- acceptance criteria are updated if behavior changed.

### G4. CI gate

No roadmap item is accepted unless:

- required CI jobs pass,
- no existing acceptance test regresses,
- new behavior is covered by at least one test or validation check.

### G5. Scope gate

A delivery fails acceptance if it introduces major phase creep.

Short-term work must not quietly introduce unfinished mid-term or long-term design into production paths.

---

# Phase 1 Acceptance: Short-Term (0–3 Months)

## Phase Goal

Stabilize the current design pipeline so different model APIs can be used without silently degrading artifact quality.

## Required Outcomes

The short-term phase is complete only if the repo can reliably enforce artifact quality and make model-driven changes visible.

### ST-1. Versioned schema contracts exist

The repo must define versioned schemas for:

- `atomic_rule`
- `semantic_rule`
- maker output
- checker output
- human review output

#### Required evidence
- schema files committed to the repo
- validation code or command-line validation path
- unit tests for valid and invalid examples

#### Hard gate
- invalid schema instances fail validation in CI

#### Non-goal
- full execution integration is not required in this phase

---

### ST-2. Rule validation pipeline exists

A formal validation stage must exist between extraction and downstream semantic usage.

Minimum required checks:

- required fields validation
- `rule_type` enum enforcement
- duplicate candidate detection
- invalid trace reference detection

#### Required evidence
- pipeline step documented in code or docs
- sample failing inputs demonstrating validation failure
- CI coverage for validation behavior

#### Hard gate
- invalid `rule_type` or malformed extracted rules must stop the pipeline

#### Non-goal
- advanced semantic contradiction resolution is not required in this phase

---

### ST-3. Artifact metadata is recorded

Every maker/checker/rewrite artifact must record:

- provider
- model ID
- prompt version
- run timestamp
- source artifact hash
- pipeline version

#### Required evidence
- metadata schema or contract definition
- sample artifact checked into examples or produced in tests
- automated assertion in test suite

#### Hard gate
- artifacts missing required metadata fail acceptance

#### Non-goal
- full experiment platform or dashboard is not required yet

---

### ST-4. Baseline CI exists

CI must run the minimum baseline quality gates.

Minimum required CI jobs:

- minimal end-to-end smoke run
- schema validation tests
- report generation smoke test
- core unit tests for pipeline and review-session bootstrap

#### Required evidence
- CI configuration in repo
- passing CI run on main branch
- documented command to reproduce locally

#### Hard gate
- pull requests cannot be considered accepted if baseline CI fails

#### Non-goal
- comprehensive benchmark coverage is not required yet

---

### ST-5. Checker instability can be surfaced

Checker output must be evaluated for basic stability on a small baseline.

Minimum required behavior:

- same baseline input can be checked twice
- inconsistent conclusions are surfaced or flagged
- result can be inspected in logs or report output

#### Required evidence
- stability check implementation
- at least one regression test or smoke check
- report or console example showing instability signal

#### Hard gate
- checker stability mechanism must exist before expanding checker usage claims

#### Non-goal
- perfect confidence estimation is not required yet

---

### ST-6. Repo governance docs exist

The repo must include baseline governance documents:

- `docs/roadmap.md`
- `docs/acceptance.md`
- `docs/model_governance.md`
- `docs/agent_guidelines.md`

#### Required evidence
- files committed to repo
- linked from README or docs index

#### Hard gate
- roadmap phase is not complete if governance docs are missing

#### Non-goal
- exhaustive enterprise policy docs are not required yet

---

## Phase 1 Acceptance Summary

Short-term phase is accepted only if all of the following are true:

- core artifacts are schema-validated,
- malformed extracted rules fail fast,
- minimal CI is active,
- artifact metadata is captured,
- checker instability can be surfaced,
- baseline governance docs exist.

---

# Phase 2 Acceptance: Mid-Term (3–9 Months)

## Phase Goal

Upgrade from stable test design to a reusable AI-assisted test planning and BDD generation platform.

## Required Outcomes

### MT-1. Multi-document ingestion is formalized

At least 3 document classes must be supported with explicit ingestion rules.

Each supported class must define:

- parsing strategy
- extraction constraints
- expected rule patterns
- known failure modes

#### Required evidence
- document class registry or equivalent config
- example inputs for each supported class
- docs describing ingestion behavior

#### Hard gate
- new document class support cannot be claimed without explicit parsing rules

#### Non-goal
- support for all document classes is not required

---

### MT-2. Planning layer exists

A planner stage must exist between semantic rules and BDD generation.

Planner output must include at least:

- priority
- risk level
- coverage intent
- scenario family
- dependency notes

#### Required evidence
- planner artifact schema
- planner generation path in pipeline
- examples for at least one baseline flow

#### Hard gate
- planner output must be schema-validated

#### Non-goal
- autonomous release-level planning is not required

---

### MT-3. Traceability is end-to-end

BDD artifacts must be traceable back to:

- source document
- source clause or section
- atomic rule
- semantic rule
- planning decision
- checker verdict
- human review outcome

#### Required evidence
- trace fields in artifact contracts
- rendered traceability in report or exported artifacts
- test validating trace linkage presence

#### Hard gate
- BDD artifacts without traceability cannot pass acceptance

#### Non-goal
- fully graphical trace explorer is optional

---

### MT-4. Normalized BDD contract exists

BDD must be represented in a normalized intermediate structure independent of final formatting.

#### Required evidence
- BDD contract schema
- converter or generator for normalized BDD
- example artifact or fixture

#### Hard gate
- generated BDD must be exportable in normalized form

#### Non-goal
- direct execution readiness is not required in this phase

---

### MT-5. Review collaboration v1 exists

The system must support asynchronous review exchange.

Minimum required capabilities:

- export review package
- import review package
- merge review decisions
- surface merge conflicts

#### Required evidence
- review package format
- example review exchange flow
- test or scripted validation for import/export/merge behavior

#### Hard gate
- review collaboration cannot be claimed without merge conflict surfacing

#### Non-goal
- hosted multi-user web platform is not required yet

---

### MT-6. Quality dashboards are useful

Reports must surface at least:

- rule type coverage heatmap
- unstable checker judgments
- baseline drift versus previous run
- document class breakdown
- traceability drill-down
- JSON or CSV export

#### Required evidence
- sample generated report
- exported JSON/CSV example
- visual or textual proof of the required sections

#### Hard gate
- dashboards must reflect real artifact data, not placeholders

#### Non-goal
- enterprise BI integration is not required yet

---

## Phase 2 Acceptance Summary

Mid-term phase is accepted only if all of the following are true:

- at least 3 document classes are explicitly supported,
- a planner stage exists and is schema-validated,
- BDD is normalized and traceable,
- review package exchange works,
- reports show trend and instability information,
- model regression checks are enforced before rollout.

---

# Phase 3 Acceptance: Long-Term (9–18 Months)

## Phase Goal

Evolve the framework into an enterprise AI testing platform with step definition integration, execution readiness, deterministic assertions, and governed collaboration.

## Required Outcomes

### LT-1. Step definition integration exists

Normalized BDD must be mappable to existing step definitions.

Minimum required support:

- exact step match
- parameterized step match
- candidate step suggestion
- unmatched step reporting
- reuse scoring

#### Required evidence
- step mapping artifact or service contract
- example mappings against real or representative step libraries
- tests for matched and unmatched scenarios

#### Hard gate
- step integration cannot be claimed without unmatched-step visibility

#### Non-goal
- full automated execution coverage across all domains is not required immediately

---

### LT-2. Execution-ready scenario contract exists

A stable `ExecutableScenario` or equivalent contract must extend normalized BDD with:

- environment requirements
- input data requirements
- setup hooks
- expected deterministic assertions
- cleanup hooks
- linked step definitions

#### Required evidence
- executable contract schema
- example artifact
- validation tests

#### Hard gate
- execution-ready scenarios must be serializable and validated

#### Non-goal
- unrestricted autonomous execution is not required

---

### LT-3. Deterministic oracle framework exists

Structured rule categories must be checked by deterministic logic wherever feasible.

Minimum expected deterministic coverage areas:

- field validation
- state validation
- calculation validation
- deadline/window checks
- event sequence verification
- pass/fail accounting

#### Required evidence
- oracle modules or equivalent deterministic validators
- test cases showing deterministic pass/fail behavior
- docs defining which rule categories are deterministic

#### Hard gate
- enterprise-readiness cannot be claimed if structured categories still rely entirely on LLM judgment

#### Non-goal
- all rule categories must not become deterministic at once

---

### LT-4. Hosted review service exists

Review must move beyond local single-user mode.

Minimum required hosted capabilities:

- user accounts
- reviewer roles
- audit trail
- conflict resolution
- comment threads
- assignment workflow

#### Required evidence
- deployed or deployable service definition
- example usage flow
- audit evidence for review actions

#### Hard gate
- enterprise review claims require auditable multi-user support

#### Non-goal
- full enterprise SSO can be deferred if role-based auditability exists

---

### LT-5. Enterprise observability exists

The platform must expose operational metrics including:

- ingestion failure rate
- extraction drift
- duplicate/conflict rule rate
- planner change rate
- maker validity rate
- checker instability rate
- BDD reuse rate
- step binding success rate
- execution pass/fail distribution

#### Required evidence
- metrics definitions
- reporting or dashboard output
- docs explaining the metric source and meaning

#### Hard gate
- enterprise operation cannot be claimed without observable platform health metrics

#### Non-goal
- every metric need not be externally exported on day one

---

### LT-6. Release governance exists

Release management must include:

- release tags
- compatibility matrix
- benchmark gates
- migration notes
- approved provider list

#### Required evidence
- release process documentation
- tagged release examples
- benchmark gate evidence for release approval

#### Hard gate
- no enterprise release should proceed without benchmark pass and rollback path

#### Non-goal
- full compliance certification is not required in this roadmap

---

## Phase 3 Acceptance Summary

Long-term phase is accepted only if all of the following are true:

- normalized BDD can map to existing step definitions,
- execution-ready scenario contracts exist,
- deterministic assertions cover core structured categories,
- review is multi-user and auditable,
- enterprise observability is in place,
- release governance is formalized.

---

# Required Evidence Matrix

## For any accepted roadmap item, at least one of the following must exist:

- schema file
- test file
- CI job
- example artifact
- report screenshot or generated output
- benchmark result
- doc update
- migration note where applicable

A feature with code but without evidence is not accepted.

---

# AI Agent Delivery Rules

Any AI agent making roadmap changes must comply with the following:

## A1. Always update contracts first when changing artifact structure
If output shape changes, update:
- schema
- acceptance docs
- tests
- examples

## A2. Never silently swap deterministic checks for model-based checks
Deterministic ownership must not be weakened without explicit approval.

## A3. Never claim support without evidence
A capability is not considered implemented unless acceptance evidence exists.

## A4. Keep phase boundaries intact
Do not mix long-term platform ambitions into short-term stabilization work unless explicitly instructed.

## A5. Prefer reversible change
Any model-specific or provider-specific addition should be easy to rollback.

---

# Suggested Review Checklist

Use this checklist before accepting any roadmap milestone.

- Is the scope aligned to the correct phase?
- Are schemas defined or updated?
- Are tests present?
- Does CI cover the new behavior?
- Is required artifact metadata captured?
- Is documentation updated?
- Is there acceptance evidence?
- Is there any silent failure risk left unaddressed?
- Does the change preserve model-provider portability?
- Can the change be rolled back safely?

If any answer is "no", the milestone should not be considered complete.
