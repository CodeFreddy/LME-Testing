# Testing Governance

## Purpose

This document defines the testing-governance layer for this repository.

It complements the architecture, roadmap, model governance, and agent rules by focusing on the testing perspective:

- how test assets are governed,
- how prompt-driven testing workflows are controlled,
- how review and validation are organized,
- how failures and confidence are assessed,
- how changes are introduced safely,
- and how quality is preserved across iterations.

This document should be read together with:

- `docs/roadmap.md`
- `docs/acceptance.md`
- `docs/model_governance.md`
- `docs/agent_guidelines.md`
- `docs/architecture.md`

---

## Why This Document Exists

The repository already has a strong developer-oriented structure:
- architecture,
- artifact contracts,
- phase-based roadmap,
- model governance,
- agent behavior rules.

However, enterprise AI testing also requires a testing-oriented governance layer.

Developer-facing documents answer questions such as:
- What is the system architecture?
- What are the artifact contracts?
- How should model changes be governed?
- What is the roadmap?

Testing governance answers different but equally important questions:
- What counts as a governed test asset?
- How are prompts, reviews, and validation steps maintained over time?
- How do we detect silent degradation?
- How do we assess confidence and failure modes?
- How do we validate changes before and after rollout?
- How do we manage test workflow consistency when multiple model APIs are used?

This document exists to make those testing concerns first-class and explicit.

---

## Role in the Documentation System

This file is intentionally separate from other docs.

### This document should own
- testing asset governance,
- prompt lifecycle expectations from a testing perspective,
- review and feedback discipline,
- pre-run and post-run validation expectations,
- confidence and failure analysis,
- test change management,
- non-functional testing controls such as parallelism, recovery, and incremental updates.

### This document should not replace
- architecture definitions in `docs/architecture.md`,
- model API governance in `docs/model_governance.md`,
- roadmap priorities in `docs/roadmap.md`,
- phase gates in `docs/acceptance.md`,
- repo-wide AI agent rules in `docs/agent_guidelines.md`.

---

## Governance Model

The overall framework should be understood in two complementary layers:

### 1. Architecture-led layer
This is the developer-facing system layer.

It governs:
- pipeline stages,
- module boundaries,
- artifact contracts,
- roadmap phases,
- model strategy,
- provider abstractions,
- execution evolution.

### 2. Test-governed layer
This is the testing-facing quality control layer.

It governs:
- prompt and test asset lifecycle,
- review discipline,
- validation discipline,
- failure classification,
- confidence reporting,
- change safety,
- repeatability of testing workflows.

Both layers are required.  
Architecture alone is not enough for enterprise AI testing.  
Testing discipline alone is not enough for long-term system evolution.

---

## Core Testing Governance Principles

### 1. Test assets are governed assets

The following must be treated as governed testing assets, not disposable helpers:

- prompt sets,
- review templates,
- validation checklists,
- confidence labels,
- failure-analysis templates,
- benchmark datasets,
- sample artifacts,
- expected output patterns,
- integration test procedures.

### 2. Prompt-driven testing behavior must be versioned

If prompts or prompt sequences affect system behavior, they are part of the governed testing surface and must be versioned, reviewed, and traceable.

### 3. Validation must happen both before and after execution

A testing workflow is incomplete unless it defines:
- pre-run validation,
- post-run validation,
- and change impact review.

### 4. Silent degradation is a primary risk

This framework must explicitly watch for situations where:
- the pipeline still runs,
- output still looks plausible,
- but quality or trustworthiness has degraded.

### 5. Failure handling is part of quality, not an afterthought

The repo should classify, surface, analyze, and learn from testing failures.

### 6. Testing governance must remain compatible with multi-model operation

Different LLM APIs may behave differently.  
Testing workflows must remain stable through explicit governance rather than provider-specific habit.

---

## Governed Testing Assets

## 1. Prompt sets

Prompt sets include any prompts or ordered prompt sequences that meaningfully shape:
- rule extraction support,
- semantic interpretation,
- test planning,
- BDD generation,
- review guidance,
- rewrite behavior,
- or future step-mapping suggestions.

Prompt sets must have:
- stable identifiers,
- version history,
- ownership,
- dependency awareness,
- linked benchmark usage.

## 2. Review templates

Review structures, scoring rubrics, review labels, and human decision templates are governed assets.

Examples:
- approve / reject / rewrite labels,
- quality review categories,
- confidence levels,
- issue classification templates.

## 3. Validation checklists

Pre-run and post-run validation checklists must be maintained as governed operational assets.

## 4. Failure-analysis templates

Failure analysis should follow repeatable structures rather than ad hoc notes.

## 5. Benchmark and regression datasets

Benchmark datasets are not only model-governance assets; they are also testing-governance assets because they define expected stability and quality behavior.

---

## Prompt Lifecycle Governance

This section focuses on prompts from a testing-governance perspective.  
Technical model governance remains in `docs/model_governance.md`.

## Prompt lifecycle stages

Each governed prompt or prompt set should move through these stages:

1. proposal
2. draft
3. review
4. baseline validation
5. active use
6. monitored use
7. revision
8. deprecation or rollback

## Minimum prompt metadata

Every governed prompt should have, at minimum:
- prompt ID
- version
- owner
- purpose
- related module
- expected input type
- expected output type
- dependency notes
- linked validation or benchmark set
- change log

## Prompt change expectations

A prompt change should not be treated as a trivial edit.

A valid prompt change should include:
- reason for change,
- expected behavior impact,
- benchmark or validation evidence,
- risk assessment,
- rollback note if behavior worsens.

## Prompt dependency awareness

If multiple prompts are designed to be used together or in sequence, their dependency order must be documented.

This matters because testing workflows often fail not because a single prompt is wrong, but because:
- sequence assumptions change,
- one prompt's output no longer matches another prompt's expected input,
- dependency drift occurs silently.

---

## Review Governance

## Role of review

Review is a testing control mechanism, not only a usability step.

It exists to:
- catch low-confidence outputs,
- detect failure patterns,
- expose ambiguity,
- support selective rewrite,
- preserve accountability.

## Review dimensions

Reviews should be able to cover at least these dimensions:

- structural validity
- source traceability
- scenario relevance
- coverage credibility
- ambiguity level
- rewrite necessity
- reviewer confidence

## Structured review expectations

Where possible, review should use structured forms rather than pure free text.

Structured review should support:
- outcome labels,
- issue categories,
- confidence labels,
- trace references,
- rationale snippets,
- recommended action.

## Review disagreement handling

If multiple reviewers are introduced later, the system should preserve disagreement rather than flattening it immediately.

Disagreement is valuable signal and should be visible.

---

## Confidence Governance

Confidence should be treated as an explicit testing concept.

## Why confidence matters

A result can be:
- structurally valid,
- apparently complete,
- and still not trustworthy enough for action.

Confidence reporting helps distinguish:
- plausible output,
- stable output,
- trusted output.

## Suggested confidence dimensions

Confidence may be expressed across different axes, for example:
- structural confidence
- semantic confidence
- coverage confidence
- review confidence
- stability confidence

## Architectural note

Confidence should not replace pass/fail or coverage decisions.  
It should complement them.

For example:
- fully covered + unstable
- partially covered + high confidence
- structurally valid + low semantic confidence

---

## Failure Analysis Governance

Failure analysis should be systematic.

## Why failure analysis matters

The framework is likely to face failures such as:
- malformed extraction artifacts,
- wrong rule typing,
- duplicate or conflicting rules,
- unstable checker judgments,
- prompt regressions,
- provider-specific behavior changes,
- report inconsistencies,
- review merge conflicts in future collaborative workflows.

Without systematic failure analysis, the same errors repeat without improving the system.

## Failure categories

Testing failures should be classified at minimum by:
- source / ingestion failure
- extraction failure
- normalization failure
- generation failure
- checker inconsistency
- review failure
- reporting failure
- model/provider failure
- regression failure

## Failure record expectations

A useful failure record should include:
- failure category
- affected stage
- artifact identifiers
- model/prompt metadata if relevant
- observed behavior
- expected behavior
- severity
- recovery action
- follow-up action

---

## Pre-Run Validation

Pre-run validation ensures the testing workflow is safe to execute.

## Required pre-run checks

At minimum, pre-run validation should confirm:
- required source inputs exist,
- required schemas exist,
- required prompt versions are available,
- target model/provider configuration is valid,
- benchmark or validation dataset is selected when needed,
- output paths or artifact destinations are valid,
- expected dependencies between stages are satisfied.

## Optional pre-run checks

Depending on phase and maturity:
- duplicate candidate warnings,
- prompt dependency checks,
- configuration diff warnings,
- previous failed run reminders.

---

## Post-Run Validation

Post-run validation ensures results are usable and trustworthy.

## Required post-run checks

At minimum, post-run validation should confirm:
- all required artifacts were produced,
- artifact schemas are valid,
- required metadata is present,
- traceability links are intact,
- checker output can be interpreted,
- report output was generated if expected,
- instability or low-confidence flags are surfaced.

## Recommended post-run checks

- compare against previous baseline,
- summarize drift,
- classify failures,
- identify changed risk areas,
- record known limitations.

---

## Change Management for Testing Assets

Testing changes should be governed explicitly.

## Changes covered by this policy

This includes changes to:
- prompts,
- review labels,
- validation templates,
- benchmark datasets,
- confidence scales,
- failure taxonomy,
- test execution procedures,
- integration checklists.

## Required change questions

Before accepting a testing-asset change, answer:
- What changed?
- Why is it needed?
- Which workflow stage is affected?
- What could regress?
- What validation was run?
- Can the change be rolled back?
- Should the change update docs or acceptance gates?

---

## Integration Testing Governance

Integration testing is especially important for multi-stage AI testing systems.

## Why integration testing matters

A single stage may look correct in isolation while the multi-stage workflow still fails because:
- inputs/outputs no longer align,
- metadata is missing,
- prompt ordering assumptions break,
- downstream validators reject upstream output,
- reports misrepresent results.

## Minimum integration test coverage

Integration tests should cover at least:
- extraction -> normalization
- semantic rules -> maker
- maker -> checker
- checker -> review
- rewrite -> checker -> report
- benchmark baseline flow

As the system evolves, integration tests should expand to include:
- planning -> normalized BDD
- normalized BDD -> step mapping
- step mapping -> executable scenario contract

---

## Non-Functional Testing Governance

Testing governance should also cover operational qualities, not only correctness.

## 1. Incremental update handling

The system should be able to validate what changed without forcing unnecessary revalidation of everything every time.

## 2. Parallel execution awareness

If multiple runs or reviewer operations happen in parallel, the framework should guard against:
- file collisions,
- artifact overwrite,
- inconsistent review state,
- baseline confusion.

## 3. Error recovery

Recovery behavior should be explicit and visible.

Recovery mechanisms should not silently hide structural failures.

## 4. Performance awareness

The framework should eventually observe metrics such as:
- run duration by stage,
- validation time,
- report generation time,
- retry frequency,
- benchmark execution time.

Performance does not replace correctness, but it matters for enterprise use.

---

## Relationship to Existing Repo Docs

## `docs/architecture.md`
This file defines system structure.  
Testing governance adds operational and quality discipline on top of that structure.

## `docs/model_governance.md`
That file governs provider/model/prompt adoption from a platform perspective.  
This file governs how testing workflows remain stable and reviewable when those model choices change.

## `docs/acceptance.md`
That file defines phase gates.  
This file defines the testing discipline needed to pass those gates in a repeatable way.

## `docs/agent_guidelines.md`
That file defines what AI agents may or may not do.  
This file defines which testing assets and review practices those agents must respect.

## `README.md`
The README should remain concise and point readers here rather than duplicating detailed testing governance.

---

## Suggested Future Companion Documents

As the system grows, testing governance may be complemented by:

- `docs/prompt_lifecycle.md`
- `docs/review_framework.md`
- `docs/failure_taxonomy.md`
- `docs/benchmark_policy.md`

These should be created only if the current doc becomes too large or if those topics need deeper operational detail.

---

## Review Questions for Testing Governance

Use these questions when reviewing major workflow or prompt changes:

- Does this change alter a governed testing asset?
- Is the prompt or review structure versioned?
- Are pre-run and post-run validations still sufficient?
- Could this introduce silent degradation?
- Is confidence reporting affected?
- Does failure analysis need new categories?
- Are integration tests still valid?
- Can the change be rolled back safely?

If these questions cannot be answered clearly, the change is not yet governance-ready.

---

## Summary

Testing governance is the quality-control layer that complements the repo's architecture and roadmap.

The developer-facing documents define how the system is built and evolves.  
This document defines how testing assets, review, validation, confidence, and failure handling are governed so that the system remains trustworthy as it grows.

The intended end state is not just an AI-enabled testing pipeline, but a governed enterprise AI testing framework where:
- architecture is explicit,
- artifacts are traceable,
- prompts are controlled,
- reviews are structured,
- validation is repeatable,
- failures are learned from,
- and model changes do not silently erode testing quality.
