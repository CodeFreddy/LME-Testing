# Testing Governance

## Purpose

This document defines the testing-governance layer for the repository.

It complements the roadmap, implementation plan, acceptance, architecture, and model governance documents by defining how governed workflows should be validated, reviewed, and evidenced as testing assets.

This document exists to ensure that:

- governed workflows are testable and reviewable,
- validation is structured and repeatable,
- failure analysis is preserved,
- quality signals remain visible,
- integration behavior does not drift silently,
- and testing discipline stays aligned with the current roadmap phase.

This document should be read together with:

- `docs/planning/roadmap.md`
- `docs/planning/implementation_plan.md`
- `docs/governance/acceptance.md`
- `docs/governance/model_governance.md`
- `docs/governance/agent_guidelines.md`
- `docs/architecture/architecture.md`

---

## Why This Document Exists

The repo already defines:

- strategic direction in `roadmap.md`,
- execution tasks in `implementation_plan.md`,
- phase gates in `acceptance.md`,
- system boundaries in `architecture.md`,
- model and prompt controls in `model_governance.md`.

This document adds the testing-governance view:

- how governed workflows are validated,
- what evidence should be preserved,
- how instability and failures should be surfaced,
- how review quality should remain explicit,
- how integration behavior should be kept testable.

It is not a replacement for those other documents.
It is the operational testing layer that helps keep the governed system trustworthy.

---

## Scope

This document governs:

- pre-run and post-run validation,
- review and feedback discipline,
- confidence and instability visibility where useful,
- failure analysis,
- integration test expectations,
- incremental and parallel execution checks,
- recovery visibility,
- phase-appropriate quality signals,
- minimum testing-governance artifacts.

It does **not** define:

- roadmap priorities,
- artifact contracts,
- model rollout policy,
- schema design,
- or hosted product requirements.

---

## Core Testing Governance Principles

### 1. Validation must exist before and after execution

A governed workflow is not sufficiently tested if it validates only the final artifact.

Testing governance should cover:

- pre-run assumptions,
- in-run failures,
- post-run artifact validity,
- evidence quality.

### 2. Upstream test quality matters most

Testing effort should first protect the upstream path that most strongly affects downstream quality.

For this repo's current phase, the most important testing-governance focus is:

- rule artifact validity,
- baseline reproducibility,
- source-anchor preservation,
- model and prompt provenance,
- checker instability visibility.

### 3. Review is a governed control layer

Review outputs are not casual notes.
Where a workflow requires review, review outputs are part of the governed testing record.

### 4. Failure must remain analyzable

If a governed workflow fails materially, the testing layer should preserve enough evidence to understand:

- what failed,
- where it failed,
- what downstream artifacts were affected,
- and whether rollback or follow-up action is required.

### 5. Testing signals must be phase-appropriate

The repo should collect the quality signals needed for the current phase.
It should not assume a heavy enterprise observability program before the platform actually needs one.

### 6. Governed testing behavior must be repo-readable

If a testing rule is intended to be repeatable, it should live in repo-readable assets such as:

- benchmark sets,
- validation scripts,
- review templates where applicable,
- evidence checklists,
- acceptance rules,
- testing-governance documentation.

---

## Governed Testing Assets

The following are considered governed testing assets in this repo, where applicable:

- benchmark cases,
- validation checklists,
- integration test procedures,
- test doubles and stub providers,
- failure-analysis notes,
- instability comparison outputs,
- review templates,
- run summaries used as evidence,
- machine-readable exports used for drift or traceability review.

Every governed testing asset should have, where relevant:

- a stable identifier or discoverable name,
- version or revision trace,
- scope,
- dependencies,
- validation expectations,
- update notes if materially changed.

---

## Pre-Run and Post-Run Validation

## 1. Pre-run validation

Before a governed workflow executes, validate:

- source availability,
- source readability,
- required directories and paths,
- permission assumptions,
- risk of accidental overwrite,
- required dependencies,
- source-anchor generation expectations where relevant,
- benchmark or fixture availability where required.

## 2. Post-run validation

After execution, validate:

- required artifacts exist,
- naming conventions are respected,
- schema or contract checks pass,
- traceability references resolve,
- source anchors are preserved where applicable,
- review outputs exist where required,
- logs and metadata are present,
- reports or summaries are updated where required.

## 3. Governance rule

Pre-run and post-run validation are part of testing governance, not optional convenience scripts.

---

## Review and Feedback Governance

## 1. Review is required when the workflow requires it

If a governed workflow includes a human review step, the testing layer should treat review evidence as part of completion.

## 2. Minimum review deliverables

For significant governed workflows, review output should preserve where applicable:

- review result,
- feedback or rationale,
- reviewed artifact reference,
- reviewer role or identity,
- timestamp.

## 3. Feedback structure

Feedback should not be completely ad hoc for governed flows.

Useful categories include:

- correctness issues,
- coverage gaps,
- traceability issues,
- contract or format issues,
- instability concerns,
- failure root causes.

## 4. Phase rule

The current roadmap does not require heavy multi-user hosted review or merge-heavy collaboration as baseline testing behavior.
Testing governance should not assume those capabilities before the roadmap phase justifies them.

---

## Confidence and Instability Governance

## 1. Confidence is separate from pass/fail

A generated artifact may be acceptable yet still deserve low confidence.

Confidence, where used, should remain a secondary signal, not a substitute for actual validation.

## 2. Useful confidence inputs

Confidence may be informed by:

- schema validity,
- traceability completeness,
- source-anchor completeness where applicable,
- checker stability,
- known ambiguity level,
- quality of review evidence.

## 3. Current-phase emphasis

In the current repo stage, checker instability visibility on a small governed baseline is more important than building a broad confidence-scoring framework.

---

## Failure Analysis Governance

## 1. Failure analysis is required for material failures

When a governed workflow fails materially, the failure should produce a structured analysis or equivalent reviewable record.

## 2. Failure analysis should capture

At minimum:

- what failed,
- where it failed,
- likely root cause,
- affected downstream artifacts,
- whether recovery was attempted,
- whether rollback is needed,
- recommended next action.

## 3. Failure categories

Suggested categories:

- source or input failure,
- extraction failure,
- schema or contract failure,
- prompt or model behavior failure,
- review workflow failure,
- reporting failure,
- integration failure.

## 4. Retention

Material failure analyses should be retained as learning artifacts, not discarded after the immediate issue is closed.

---

## Integration Test Governance

## 1. Integration tests are required for governed workflow chains

If a workflow depends on sequence, dependency, or output handoff between stages, there should be integration tests or integration test procedures.

## 2. Integration focus areas

For this framework, integration governance should especially protect:

- extraction to rule artifacts,
- rule artifacts to maker output,
- maker output to checker output,
- checker output to review workflow,
- review decisions to rewrite flow,
- report generation from final artifacts.

## 3. Procedure quality

Integration procedures should define:

- scenario name,
- purpose,
- prerequisites,
- steps,
- expected outputs,
- expected review artifacts where applicable,
- expected validation checks.

## 4. Phase rule

Integration governance should prioritize the currently active governed chain.
It should not assume future execution-stage integrations before the roadmap reaches that phase.

---

## Incremental and Parallel Execution Governance

## 1. Incremental update support is a quality claim

If a workflow claims to support partial updates, that claim must be testable and governed.

Incremental-update governance should cover:

- change detection,
- changed-scope tracking,
- update logging,
- validation of updated subsets,
- traceability preservation.

## 2. Parallel execution must preserve correctness

If tasks are processed in parallel, governance must ensure that:

- identifiers remain unique,
- outputs do not overwrite each other,
- logging remains attributable,
- traceability remains intact,
- source anchors remain attributable,
- failure isolation works as expected.

## 3. Current-phase emphasis

These concerns matter, but they should be tested in proportion to actual workflow usage rather than assumed at enterprise scale by default.

---

## Error Recovery Governance

## 1. Recovery must be bounded and observable

Automatic recovery is allowed only if:

- recovery logic is documented,
- recovery attempts are logged,
- recovered outputs remain traceable,
- unrecoverable cases fail visibly.

## 2. Recovery records

Recovery logs should capture:

- error type,
- stage,
- recovery action,
- success or failure,
- time spent,
- impact on final outputs.

## 3. Governance rule

Recovery should never hide that an error occurred.

---

## Phase-Appropriate Quality Signals

Testing governance should include quality signals beyond correctness, but the signal set should remain appropriate to the current phase.

## Current minimum recommended signals

### Baseline execution signals

- start and end time,
- total duration,
- per-stage duration where practical.

### Quality signals

- artifact generation success,
- schema pass rate,
- traceability completeness,
- source-anchor completeness where applicable,
- checker instability rate on the governed baseline set,
- report generation success.

### Failure signals

- error count,
- error category distribution,
- recovery attempt count where recovery exists.

### Drift signals

- run-to-run artifact differences where governed baselines exist,
- regression versus previous benchmark or baseline outputs,
- visible changes in checker instability.

## Long-term signal expansion

More extensive metrics may be added later, but they should be introduced only when the roadmap phase and actual platform usage justify them.

---

## Minimum Testing-Governance Artifacts

A governed testing workflow should be able to produce or preserve, where relevant:

- run summaries,
- validation summaries,
- review summaries,
- failure analyses,
- drift comparison outputs,
- checker instability summaries,
- integration test evidence,
- rollback notes,
- audit-style execution records.

The exact repo structure may evolve, but these artifacts should remain repo-readable and reviewable.

---

## Relationship to Other Docs

This document should strengthen, not replace, the other governed docs.

### With `docs/architecture/architecture.md`

Preserve emphasis on:

- pre-run and post-run validation,
- source-anchor handling,
- integration boundaries,
- incremental and parallel execution as governed concerns.

### With `docs/governance/acceptance.md`

Preserve emphasis on:

- evidence quality,
- instability visibility,
- failure-analysis evidence,
- integration-test evidence,
- rollback verification where relevant.

### With `docs/governance/model_governance.md`

Preserve emphasis on:

- benchmark evidence,
- prompt change impact,
- instability visibility,
- phase-appropriate rollout controls.

### With `docs/governance/agent_guidelines.md`

Preserve emphasis on:

- no silent prompt or template deletion where governed assets exist,
- no silent dependency breakage,
- mandatory update records for governed testing assets,
- visible failure handling.

---

## AI Agent Rules for Testing Governance

Any AI coding agent working with test-governed assets must follow these rules.

### 1. Do not silently delete governed testing assets

If a benchmark case, validation template, review template, or other governed testing asset is removed, the change must be explicit, justified, and documented.

### 2. Do not weaken evidence quality silently

An agent must not remove instability reporting, validation evidence, or reviewable outputs just to simplify a workflow.

### 3. Do not present future-phase testing capabilities as baseline

If a testing feature belongs to a later phase, label it clearly instead of presenting it as the current default workflow.

### 4. Do not treat failure analysis as optional when the workflow materially failed

If a governed workflow failed in a meaningful way, preserve reviewable failure evidence.

### 5. Prefer practical baseline controls over heavy premature governance

Testing governance should first strengthen the baseline path that the repo actually relies on.

---

## Review Questions

Use these questions when reviewing testing-governance changes:

- Does this change improve or weaken baseline validation?
- Does it preserve reviewable evidence?
- Does it keep checker instability visible where required?
- Does it preserve traceability and source-anchor handling where applicable?
- Does it weaken failure-analysis capability?
- Does it affect integration-sequence integrity?
- Does it assume heavier future-phase operations than the roadmap currently justifies?

---

## Summary

Testing governance adds the operational validation layer that architecture and acceptance alone do not provide.

In this repository:

- roadmap defines priorities,
- implementation plan defines execution,
- acceptance defines gates,
- architecture defines boundaries,
- model governance controls probabilistic dependencies,
- and testing governance keeps validation, evidence, instability visibility, failure analysis, and integration quality disciplined.

This is what helps turn a promising AI testing prototype into a governed system that contributors can trust and operate.
