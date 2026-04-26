# Model Governance

## Purpose

This document defines the governance rules for using LLM APIs in this repository.

It exists to ensure that the framework can evolve safely even when:
- providers change,
- model versions change,
- prompts change,
- output quality drifts,
- or multiple model APIs are used in parallel.

This document applies to all model-driven modules, including:
- extraction assistants if added,
- semantic normalization,
- maker,
- checker,
- rewrite,
- planning when introduced under a governed contract,
- future step-mapping suggestions,
- and any AI-assisted code generation workflow used in the repo.

This document should be read together with:
- `docs/planning/roadmap.md`
- `docs/planning/implementation_plan.md`
- `docs/governance/acceptance.md`
- `docs/architecture/architecture.md`
- `docs/governance/agent_guidelines.md`
- `docs/governance/testing_governance.md`
- `docs/governance/prompt_lifecycle.md`

---

## Governance Goals

Model governance in this repo has five goals:

1. keep model changes observable,
2. keep prompt changes traceable,
3. prevent silent quality regressions,
4. allow controlled adoption of new providers or models,
5. preserve rollback safety.

The framework must never depend on an undocumented model behavior as if it were a stable contract.

---

## Core Principles

### 1. Models are replaceable, contracts are not

Business logic must not be coupled to a specific provider or model.

Stable behavior must be defined through:
- schemas,
- acceptance gates,
- benchmark thresholds,
- and module interfaces.

### 2. Every model-driven output is probabilistic

All model outputs are treated as probabilistic and must be governed through:
- structured outputs,
- validation,
- benchmark comparison,
- and failure handling.

No model-driven stage should be treated as governed baseline behavior unless its output contract, validation path, and traceability expectations are defined in repo-readable form.

### 3. Prompts are versioned artifacts

Prompts are not inline implementation details.  
They are governed inputs and must be versioned the same way schemas and test fixtures are versioned.

### 4. Adoption requires evidence

A new provider, model, or prompt version must not be adopted based only on subjective inspection.  
Adoption requires benchmark evidence.

### 5. Rollback must always be possible

No model rollout is complete unless it can be reversed without requiring downstream artifact redesign.

### 6. Durable model behavior must be repo-readable

If model behavior is expected to be repeatable across runs or operators, the governing assets must be stored in repo-readable form, such as:
- prompts,
- config files,
- schemas,
- benchmark sets,
- policy docs,
- implementation task definitions.

Chat-only context or undocumented operational memory is not sufficient.

---

## Scope

This governance policy applies to:

- provider configuration,
- model selection,
- prompt management,
- generation metadata,
- benchmark baselines,
- drift detection,
- rollout policy,
- rollback policy.

It does not define business roadmap priorities; those are covered in `docs/planning/roadmap.md`.

It also does not require every future model-driven stage to exist immediately.
Governance must scale with the active roadmap phase and actual system maturity.

---

## Model Strategy Contract

Every model-driven module must resolve its execution through a stable model strategy contract.

At minimum, the strategy contract must define:

- `provider_name`
- `model_name`
- `model_version` if available
- `prompt_id`
- `prompt_version`
- `temperature`
- `top_p` if used
- `max_tokens` if applicable
- `timeout_seconds`
- `retry_policy`
- `structured_output_mode`
- `fallback_strategy` if defined

No model-facing module should embed undocumented provider-specific behavior directly in business logic.

---

## Required Artifact Metadata

Every generated artifact produced by a model-driven stage must include metadata describing how it was created.

### Required fields

At minimum, generated artifacts must record:

- provider name
- model name
- model version if available
- prompt ID
- prompt version
- run timestamp
- source artifact hash
- pipeline version
- module name
- execution mode
- retry count if retries occurred

### Applies to

This metadata should be recorded for:
- maker outputs,
- checker outputs,
- rewrite outputs,
- planner outputs when introduced,
- any future normalized BDD generation outputs when model-driven,
- any future step-binding suggestion outputs.

### Rationale

This allows the team to answer:
- which model produced this artifact,
- which prompt version was used,
- whether a behavior change correlates with a rollout,
- whether rollback is needed.

---

## Prompt Governance Integration

Model governance depends on prompt governance being explicit.

At minimum, governed prompt use should preserve:
- prompt identity,
- prompt version,
- prompt collection completeness where applicable,
- prompt dependency awareness,
- prompt change impact notes.

Model governance does not replace `docs/governance/prompt_lifecycle.md`, but it depends on it.

---

## Prompt Governance

## Prompt identity

Every production prompt must have:
- a stable prompt ID,
- semantic version,
- owner,
- change summary,
- linked benchmark set.

### Prompt storage

Prompts should be stored in a governed location in the repo, such as:
- `prompts/`
- or another dedicated versioned directory.

Do not rely on ad hoc inline prompt strings for production paths.

### Prompt changes

Any prompt change that may affect output behavior must include:
- prompt version bump,
- change note,
- linked benchmark run,
- acceptance impact review if output contracts are affected.

If the prompt belongs to a newly introduced or future stage, that stage must already have a governed contract before the prompt can be promoted into baseline use.

### Prompt review questions

Before promoting a prompt change, review:
- Did output structure change?
- Did behavior change on benchmark cases?
- Did checker stability change?
- Did failure mode distribution change?
- Is rollback straightforward?
- Did prompt dependencies or governed prompt collections change?

---

## Supported Model Tiers

To reduce accidental sprawl, the repo should classify models into usage tiers.

### Tier 1: Approved default models
These are models approved for normal production workflows.

Requirements:
- benchmark-passed,
- stability-checked,
- documented in provider list,
- rollback-ready.

### Tier 2: Experimental candidate models
These are models allowed only in controlled experiments.

Requirements:
- isolated config,
- explicit experiment label,
- no default production use,
- artifact tagging as experimental.

### Tier 3: Disallowed models
These are models that:
- fail benchmark thresholds,
- fail structured output requirements,
- show unacceptable instability,
- or lack rollback-safe behavior.

Disallowed models must not be used in mainline workflows.

---

## Provider Compatibility Policy

A provider may be integrated only if the repo can control and observe its behavior.

### Minimum provider requirements

A provider must support or be wrapped to support:
- deterministic enough configuration for repeated testing,
- structured output handling,
- timeout control,
- retry policy,
- observable error handling,
- metadata capture.

### Provider-specific behavior

Provider quirks must be isolated behind provider adapters.

Examples:
- JSON mode differences,
- schema enforcement differences,
- retryable error patterns,
- token limits,
- truncation handling.

Business logic must not branch directly on provider quirks unless that branching is centralized and documented.

---

## Benchmark Policy

Benchmarks are mandatory for model governance.

### Benchmark categories

At minimum, benchmark coverage should include:

1. extraction sanity
2. semantic normalization sanity
3. maker structural validity
4. checker consistency
5. report generation
6. end-to-end smoke

The active baseline should begin with a small practical benchmark set, such as the existing `poc_two_rules` style flow, before broader benchmark coverage is required.

As the system evolves, benchmark categories should expand to include:
- planning quality,
- BDD normalization,
- BDD style profile consistency where relevant,
- step binding suggestions,
- execution readiness export.

### Benchmark dataset policy

Benchmark data should include:
- representative happy paths,
- edge cases,
- ambiguous rules,
- malformed or incomplete inputs,
- structured rule categories,
- document-class diversity over time.

### Benchmark outputs

Each benchmark run should capture:
- pass/fail status,
- schema validity,
- artifact diffs,
- checker instability signals,
- run metadata,
- summary score or threshold results.

Checker instability checks should default to a small governed baseline set rather than implicitly requiring double-runs of the full corpus.

---

## Model Adoption Workflow

A new model or provider must follow this workflow.

### Step 1: Register candidate
Document:
- provider,
- model name,
- intended usage,
- expected benefit,
- known risks.

### Step 2: Run benchmark
The candidate must run the required benchmark set.

### Step 3: Compare against baseline
Review:
- schema conformance,
- artifact diffs,
- checker stability,
- output completeness,
- failure distribution.

### Step 4: Decide rollout class
Outcome must be one of:
- approved default,
- experimental only,
- rejected.

### Step 5: Document rollback path
Before production adoption, define how to revert to prior default behavior.

No model is considered production-ready until this workflow is complete.

---

## Prompt Adoption Workflow

A prompt change must follow a lighter but still governed workflow.

### Step 1: Create prompt version
Assign:
- prompt ID,
- new semantic version,
- change summary.

### Step 2: Run linked benchmark set
Use the benchmark set defined for that prompt's module.

### Step 3: Compare outputs
Review:
- schema validity,
- benchmark diffs,
- unexpected behavior changes,
- checker stability changes.

### Step 4: Approve or revert
If thresholds are not met, do not promote the prompt.

---

## Stability and Drift Monitoring

The repo must actively watch for silent degradation.

### Drift signals to track

Track at least:
- schema failure rate,
- duplicate rule candidate rate,
- checker instability rate,
- incomplete artifact rate,
- benchmark trend changes,
- report generation failure rate,
- model-specific failure patterns.

The exact metric set should remain selective and phase-appropriate.
Governance should not assume a heavy enterprise observability program before the repo actually needs one.

### Trigger conditions

A governance review should be triggered when:
- benchmark score drops below threshold,
- checker instability exceeds threshold,
- schema failure rate rises materially,
- structured output failure becomes non-trivial,
- provider-specific regressions appear.

---

### Checker Instability Analysis（2026-04-19）

**Measurement:** `runs/checker-stability/20260418T231915+0800-v3/stability_report.json`  
**Data source:** real_api (MiniMax-M2.7)  
**Comparable cases:** 63（run A: 63 reviews, run B: 10 reviews; 53 cases missing due to API disconnect）

| Metric | Value |
|--------|-------|
| stable_count | 4 |
| unstable_count | 6 |
| **instability_rate** | **9.5%** |
| threshold | 5% |
| status | **EXCEEDS THRESHOLD** |

**Unstable case patterns:**
- Score differences of 1-2 points on `requirement_coverage` and `test_design_quality` (expected at low score range)
- `coverage_assessment.status` flipping between `partial` and `covered` across runs
- Missing cases in run B: API disconnected mid-run, retry logic recovered for run A but run B could not resume

**Root cause assessment:**
1. **API reliability is the primary factor** — 53/63 cases missing from run B due to mid-run disconnection. This is not checker instability per se but API availability failure.
2. **Score variance is secondary** — 6 cases showed score differences across runs, all within 1-2 points on subjective quality dimensions. This is within expected variance for LLM-based evaluation.
3. **Coverage status flip** — `partial` ↔ `covered` flip in 2 cases indicates borderline scenarios where small score changes shift coverage determination.

**Implications for model governance:**
- The 9.5% instability rate **exceeds the 5% warning threshold** defined in `config/benchmark_thresholds.json`.
- The majority of observed "instability" is attributable to **API reliability** rather than intrinsic model inconsistency.
- Before flagging this as a model quality problem, API reliability must be addressed (see S2-T02 iterations: retry logic added in v4).
- A clean measurement on a stable API would require retry-with-resume capability for the stability script itself.

**Recommended action:**
- Re-run checker stability measurement after confirming API reliability improvements.
- Consider a separate API reliability metric (e.g., % of batches completed without disconnection) alongside instability rate.
- The `coverage_assessment.status` flip pattern suggests some scenarios are genuinely borderline — these should be reviewed for potential prompt clarification.

---

## Rollout Policy

Rollouts must be controlled.

### Allowed rollout modes

- local experiment
- CI benchmark only
- limited default rollout
- full default rollout

### Rollout requirements

A rollout must define:
- target modules,
- target environments,
- benchmark evidence,
- owner,
- rollback path,
- monitoring expectations.

Do not promote a model or prompt directly from experiment to full default without evidence.
Do not promote a model or prompt into a stage whose contract and acceptance path are still undefined.

---

## Rollback Policy

Rollback must be simple and documented.

### Rollback requirements

For every production model or prompt:
- prior default must remain known,
- config switch path must be documented,
- artifact schema must remain valid after rollback,
- benchmark reference must remain available.

### Rollback triggers

Rollback should be considered when:
- benchmark thresholds fail,
- checker instability rises significantly,
- structured output fails more often,
- users report material degradation,
- report quality or traceability degrades.

---

## Structured Output Policy

Whenever structured JSON output is part of the contract, it must remain part of the contract.

### Requirements

- prefer schema-constrained generation where possible,
- validate all structured outputs,
- hard-fail invalid contract outputs in governed paths,
- do not silently coerce malformed outputs into accepted artifacts.

### Exception handling

If recovery logic is introduced, it must be:
- documented,
- tested,
- bounded,
- and observable in logs and metadata.

---

## Minimum Governance Artifacts

Model governance should produce or preserve a minimum set of reviewable governance artifacts, such as:

- benchmark summaries,
- artifact diff summaries,
- checker instability summaries,
- model adoption records,
- prompt change records,
- rollback notes,
- audit-style run logs where relevant.

The exact directory layout may vary, but the artifacts must remain repo-readable and discoverable.

---

## Governance Thresholds

The exact numeric thresholds may evolve, but the repo should define thresholds for:

- schema pass rate
- benchmark pass rate
- checker instability rate
- structured output validity
- report generation success rate

These thresholds should be maintained in a dedicated config or benchmark policy file where possible.

Do not rely on informal human judgment alone for promotion decisions.
Do not require threshold programs that are heavier than the current roadmap phase justifies.

---

## Required Documentation for Any Model Change

Any production-relevant model or prompt change must include:

- change summary
- reason for change
- affected modules
- benchmark evidence
- known behavior differences
- rollback notes
- owner

This information may live in PR descriptions, release notes, or a dedicated governance log.

---

## AI Agent Rules for Model Changes

Any AI coding agent working with model-facing code must follow these rules.

### 1. Do not switch defaults silently
A model default must not be changed without updating:
- config,
- docs,
- benchmark evidence,
- rollback notes.

### 2. Do not hardcode provider behavior into business modules
Provider-specific logic belongs in adapters or strategy layers.

### 3. Do not change prompts without versioning
Prompt edits must update prompt metadata and benchmark references.

### 4. Do not bypass benchmark gates
A passing local sample is not enough to justify adoption.

### 5. Prefer deterministic validation when possible
If a validation can be made deterministic, do not rely only on model judgment.

### 6. Preserve repo-readable context
If a behavior depends on prompt/config/schema choices, those choices must be stored in repo-readable form rather than only in ephemeral context.

---

## Suggested Repo Structure

Recommended locations for governed model assets:

- `docs/governance/model_governance.md`
- `prompts/`
- `benchmarks/`
- `schemas/`
- `configs/models/`
- `artifacts/benchmarks/`

This exact structure may vary, but model assets must be discoverable and version-controlled.

---

## Review Checklist

Use this checklist before approving any model or prompt change.

### Required
- Is the model or prompt change documented?
- Is the prompt version updated?
- Is benchmark evidence attached?
- Are artifact schemas unchanged or intentionally migrated?
- Is rollback documented?
- Are affected modules listed?
- Are provider quirks isolated?
- Are prompt dependencies and governed prompt collections still valid where applicable?

### Recommended
- Was artifact diff review performed?
- Was checker stability compared?
- Were failure cases reviewed?
- Was the change tested across at least one baseline flow?

---

## Summary

Model governance in this repo is not optional infrastructure.  
It is a core control system that makes multi-model development safe.

The framework may use different LLM APIs over time, but model changes must always be constrained by:
- stable contracts,
- repo-readable durable context,
- versioned prompts,
- benchmark evidence,
- structured outputs,
- and rollback-safe rollout rules.

Without these controls, the repo risks silent regressions, unstable outputs, and unreliable development velocity.
