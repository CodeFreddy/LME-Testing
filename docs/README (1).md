# LME-Testing

Document-driven AI test design prototype for rule extraction, scenario generation, review, and reporting.

## What This Project Is

LME-Testing is a document-driven AI testing prototype that transforms source documents into structured testing artifacts.

Current workflow:

`source docs -> extraction -> atomic rules -> semantic rules -> maker -> checker -> human review -> rewrite -> report`

The system is currently optimized for:

- extracting structured rules from documents,
- normalizing those rules into governed artifacts,
- generating BDD-style test scenarios,
- assessing scenario quality and coverage,
- supporting human review and rewrite,
- producing structured reports.

## What This Project Is Not Yet

This repository is **not yet**:

- a full test execution framework,
- a runtime orchestration platform,
- a hosted multi-user review product,
- a complete step-definition-aware BDD execution engine.

Those are part of the longer-term roadmap, not current baseline capabilities.

---

## Current Architecture at a Glance

The current design loop is:

1. ingest source documents,
2. extract `atomic_rule` artifacts,
3. normalize into `semantic_rule` artifacts,
4. generate candidate scenarios with `maker`,
5. evaluate scenario quality and coverage with `checker`,
6. collect human review decisions,
7. regenerate targeted outputs through `rewrite`,
8. produce final reports.

This repo is centered on governed artifacts and phased validation rather than free-form prompt chaining.

---

## Current Priorities

The current near-term priority is to stabilize the existing design pipeline so it can safely evolve across different LLM APIs.

That means focusing on:

- schema governance,
- rule validation,
- stable source-anchor traceability,
- prompt and model governance,
- CI and benchmark gates,
- checker stability visibility,
- reviewable artifact contracts.

See the roadmap for phased details.

---

## Repository Documentation

Project documentation is organized under `docs/`.

### Core documents

- `docs/roadmap.md`  
  Phased short-term, mid-term, and long-term upgrade plan.

- `docs/implementation_plan.md`  
  Task-oriented execution plan with input/output contracts, validation expectations, and task boundaries.

- `docs/acceptance.md`  
  Acceptance criteria and release gates for each roadmap phase.

- `docs/model_governance.md`  
  Rules for model APIs, prompt versioning, regression baselines, rollout, and rollback.

- `docs/agent_guidelines.md`  
  Operating rules for AI coding agents contributing to this repo.

- `docs/architecture.md`  
  System-level architecture, artifact contracts, module boundaries, traceability, and deterministic vs LLM-assisted responsibilities.

- `docs/testing_governance.md`  
  Review, confidence, failure analysis, validation, operational metrics, and test-governance rules.

- `docs/prompt_lifecycle.md`  
  Prompt inventory, dependency, versioning, deprecation, and rollback rules.

- `docs/step_integration_plan.md`  
  BDD style learning, step registry, step mapping, gap analysis, and execution-ready handoff planning.

---

## Roadmap Summary

### Short-term
Stabilize the current document-to-rule-to-BDD pipeline with:
- schema validation,
- rule validation,
- stable source-anchor traceability,
- baseline CI,
- prompt and artifact metadata,
- checker stability visibility,
- governance docs.

### Mid-term
Expand into a reusable AI-assisted planning and BDD generation platform with:
- multi-document ingestion,
- planning layer,
- normalized BDD contract,
- BDD style learning,
- stronger traceability,
- collaborative review exchange,
- richer reporting.

### Long-term
Evolve into an enterprise AI testing platform with:
- step-definition registry and mapping,
- execution-ready scenario contracts,
- deterministic assertion layers,
- hosted review workflows,
- enterprise observability.

See `docs/roadmap.md` for the full plan.

---

## Governance Principles

This repository follows a few core rules:

- model outputs are probabilistic and must be governed,
- schemas and contracts are first-class,
- deterministic validation takes priority where possible,
- prompts must be versioned,
- model changes require benchmark evidence,
- architecture changes must respect roadmap phases,
- durable behavior must be reconstructable from repo-readable assets.

See:
- `docs/model_governance.md`
- `docs/agent_guidelines.md`
- `docs/acceptance.md`

---

## Quick Start

> Note: This section should be updated with exact repo-specific commands if the CLI or setup steps change.

Typical high-level flow:

1. prepare source documents,
2. run extraction to produce rule artifacts,
3. validate generated artifacts,
4. run maker to generate scenarios,
5. run checker to assess quality and coverage,
6. review results through the review workflow,
7. run rewrite if required,
8. generate final reports.

If you are new to the repo, start with the smallest reproducible baseline flow before attempting larger datasets.

---

## Working Model

### Artifact-first development
All meaningful outputs in the pipeline should be represented as governed artifacts.

### Benchmark-governed evolution
Any meaningful model or prompt change should be benchmarked before adoption.

### Human review remains a control layer
Human review is part of the current system design, not an optional extra.

### Step integration is a future bridge, not a current shortcut
BDD generation and executable step integration are connected by a governed bridge layer.  
See `docs/step_integration_plan.md`.

---

## Recommended Next Steps for Contributors

If you are contributing to this repo, start by reading:

1. `docs/roadmap.md`
2. `docs/implementation_plan.md`
3. `docs/architecture.md`
4. `docs/model_governance.md`
5. `docs/acceptance.md`
6. `docs/agent_guidelines.md`

Then identify:
- the current roadmap phase,
- the relevant implementation task,
- the acceptance criteria,
- the artifact contracts affected by your change.

---

## Suggested README Follow-Ups

As implementation progresses, this README should be extended with:

- exact installation steps,
- concrete CLI examples,
- example artifact paths,
- sample reports,
- benchmark usage instructions,
- contribution workflow notes.

---

## Summary

LME-Testing is currently a document-driven AI test design prototype.  
Its immediate focus is not to become a bigger prompt workflow, but to become a more stable, governed, traceable system for document-derived testing artifacts. Over time, it is intended to evolve toward enterprise AI testing through planning, normalized BDD generation, step-definition integration, execution-ready contracts, and governed step-aware automation.
