# LME-Testing

Document-driven AI test design prototype for governed rule extraction, scenario generation, review, and reporting.

## What This Project Is

LME-Testing is a document-driven AI testing prototype that transforms source documents into structured testing artifacts.

Current workflow:

`source docs -> extraction -> atomic rules -> semantic rules -> maker -> checker -> human review -> rewrite -> report`

The repo is currently optimized for:

- extracting structured rules from documents,
- normalizing those rules into governed artifacts,
- generating BDD-style test scenarios,
- assessing scenario quality and coverage,
- supporting human review and targeted rewrite,
- producing structured reports.

## What This Project Is Not Yet

This repository is **not yet**:

- a full test execution framework,
- a runtime orchestration platform,
- a hosted multi-user review product,
- a complete step-definition-aware BDD execution engine.

Those are later-phase possibilities, not current baseline capabilities.

---

## Current Working Model

This repo is governed by a few core operating assumptions:

- LLM outputs are probabilistic and must be governed, not trusted.
- Artifacts and contracts are first-class.
- Deterministic validation should take priority wherever possible.
- Prompt and model behavior must be versioned and benchmarked.
- Human review is a control layer, not an optional extra.
- Durable behavior must be reconstructable from repo-readable assets.

This means the project is not trying to become a bigger prompt workflow first.
It is trying to become a more stable, governed, and traceable system for document-derived testing artifacts.

---

## Current Priorities

The current near-term priority is to harden the existing design pipeline so it can safely evolve across different LLM APIs.

The current execution order is:

1. govern upstream rule artifacts,
2. make baseline runs reproducible in CI,
3. make model and prompt behavior traceable,
4. expose checker instability on a small baseline set,
5. only then expand upstream ingestion and downstream BDD normalization.

See `docs/roadmap.md` for the full phased direction.

---

## Documentation Entry Points

If you are new to the repo, start here:

1. `docs/roadmap.md`
2. `docs/implementation_plan.md`
3. `docs/acceptance.md`
4. `docs/architecture.md`
5. `docs/model_governance.md`
6. `docs/agent_guidelines.md`

If you are an AI coding agent, read:

1. `../AGENTS.md`
2. `docs/roadmap.md`
3. `docs/implementation_plan.md`
4. `docs/acceptance.md`
5. `docs/architecture.md`

If you are working on model or prompt changes, also read:

- `docs/model_governance.md`
- `docs/prompt_lifecycle.md`

If you need the documentation map, read:

- `docs/index.md`

---

## Core Documents

- `docs/roadmap.md`
  Strategic execution contract and phase boundaries.

- `docs/implementation_plan.md`
  Task-oriented execution plan with prerequisites, contracts, and validation expectations.

- `docs/acceptance.md`
  Phase gates, release readiness, and evidence requirements.

- `docs/architecture.md`
  System boundaries, artifact contracts, traceability, and deterministic vs LLM-assisted responsibilities.

- `docs/model_governance.md`
  Rules for model APIs, prompt versioning, baseline regression, rollout, and rollback.

- `docs/agent_guidelines.md`
  Operating rules for AI coding agents contributing to this repo.

---

## Phased Direction

### Phase 1

Harden the current document-to-rule-to-BDD pipeline with:

- schema validation,
- upstream validation gates,
- baseline CI,
- source-anchor groundwork,
- prompt and artifact metadata,
- baseline checker stability visibility,
- governance docs.

### Phase 2

Expand into a governed planning and normalized BDD platform with:

- multi-document ingestion,
- source-aware rule path,
- planning layer,
- normalized BDD contract,
- BDD style learning,
- step visibility,
- stronger reporting and traceability.

### Phase 3

Move toward execution readiness with:

- step registry and mapping,
- execution-ready scenario contracts,
- deterministic oracle layers for high-value rule classes,
- selective governance signals,
- release governance.

---

## Quick Start

> This section should be updated with exact repo-specific commands as implementation stabilizes.

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

## Summary

LME-Testing is currently a governed AI test design prototype.
Its immediate focus is to stabilize rule artifacts, traceability, model behavior, and validation discipline before expanding into broader planning, normalized BDD, and execution-ready integration.
