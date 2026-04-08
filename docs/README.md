# LME-Testing

A document-driven AI testing framework for extracting rules from source documents, generating structured BDD-style test scenarios, reviewing coverage, and evolving toward enterprise-grade AI-assisted testing.

## Status

This repository is currently a **document-driven test design system**, not yet a full execution platform.

Current pipeline:

`source documents -> extraction -> atomic rules -> semantic rules -> maker -> checker -> review-session -> rewrite -> checker -> report`

Today, the project is focused on:

- extracting structured rules from source documents,
- normalizing rules into governed artifacts,
- generating BDD-style test scenarios,
- checking scenario quality and coverage,
- supporting human review and rewrite,
- producing readable reports.

Planned future layers include:

- multi-document ingestion,
- test planning,
- normalized BDD contracts,
- step definition integration,
- execution-ready scenario contracts,
- deterministic runtime assertions,
- hosted collaborative review.

See [`docs/roadmap.md`](./roadmap.md) for the phased plan.

---

## What This Project Is

LME-Testing is intended to help teams move from document-based requirements to structured, reviewable test design artifacts.

The architecture is built around governed transformations:

- source documents
- extracted rule artifacts
- semantic rule artifacts
- generated scenario artifacts
- review artifacts
- reports

This project is especially suited for workflows where:

- rules originate in specifications, rulebooks, compliance docs, API docs, or business workflow documents,
- teams want traceable AI-assisted test design,
- BDD-style outputs are useful,
- model-driven generation must still be governed by schemas, validation, and review.

---

## What This Project Is Not Yet

This repository is **not yet**:

- a general-purpose runtime execution framework,
- a fully hosted multi-user review system,
- a complete step-definition-aware BDD execution engine,
- an autonomous enterprise testing platform.

Those are part of the longer-term roadmap, not current functionality.

---

## Current Core Workflow

The current system is organized around this design loop:

1. extract source rules from documents,
2. normalize into `atomic_rule`,
3. normalize into `semantic_rule`,
4. generate scenarios through `maker`,
5. evaluate scenario quality and coverage through `checker`,
6. review outputs through human review session,
7. rewrite targeted results,
8. generate reports.

This separation is intentional.  
The project treats artifacts as governed contracts rather than ad hoc prompt outputs.

---

## Repository Documentation

The repository is governed through the documents in `docs/`:

- [`docs/roadmap.md`](./roadmap.md) — phased short-term, mid-term, and long-term upgrade plan
- [`docs/acceptance.md`](./acceptance.md) — acceptance criteria, release gates, and evidence requirements
- [`docs/model_governance.md`](./model_governance.md) — model API governance, prompt versioning, benchmark and rollout rules
- [`docs/agent_guidelines.md`](./agent_guidelines.md) — rules for AI coding agents working in the repo
- [`docs/architecture.md`](./architecture.md) — system architecture, module boundaries, artifact contracts, deterministic vs LLM-assisted responsibilities

These docs are intended to help both:
- human developers,
- AI coding agents working under controlled constraints.

---

## Architecture Overview

At a high level, the repository is a **document-to-test-design transformation system**.

Current artifact flow:

`source documents -> extraction -> atomic rules -> semantic rules -> maker output -> checker output -> human review -> report`

Architectural principles:

- artifacts are first-class contracts,
- upstream rule quality matters more than downstream cleverness,
- structured outputs remain structured,
- deterministic validation must constrain LLM-assisted steps,
- traceability must be preserved through the pipeline.

See [`docs/architecture.md`](./architecture.md) for the full architecture description.

---

## Model Governance

This repository is designed to work with evolving LLM APIs, but model usage must remain governed.

Core governance expectations:

- prompts are versioned artifacts,
- model outputs are treated as probabilistic,
- generated artifacts must record metadata,
- benchmark evidence is required for model or prompt changes,
- rollback must remain possible,
- provider-specific behavior must stay isolated behind adapters or strategy layers.

See [`docs/model_governance.md`](./model_governance.md) for details.

---

## Acceptance and Phase Gates

The roadmap is phase-based and every phase has explicit acceptance criteria.

No major feature is considered complete unless it includes:

- clear acceptance evidence,
- tests or benchmark support,
- contract alignment,
- documentation updates where needed.

See [`docs/acceptance.md`](./acceptance.md) for the full release and acceptance rules.

---

## AI Agent Contribution Policy

AI coding agents are welcome in this repository, but must work under repo contracts.

Key expectations:

- do not silently change schemas,
- do not silently switch default models,
- do not bypass acceptance criteria,
- do not replace deterministic checks with LLM-only behavior,
- do not expand roadmap scope implicitly,
- do not hide failures to keep flows passing.

See [`docs/agent_guidelines.md`](./agent_guidelines.md).

---

## Suggested Near-Term Priorities

The near-term focus of the repo is to stabilize the current design pipeline before expanding architectural scope.

Priority areas include:

- schema-governed rule validation,
- rule type enforcement,
- benchmarkable maker/checker behavior,
- CI protection for the pipeline,
- model and prompt metadata,
- checker stability visibility,
- controlled governance docs and contracts.

These priorities are described in the short-term phase of [`docs/roadmap.md`](./roadmap.md).

---

## Working Philosophy

This project assumes that AI-assisted testing is only valuable when it is:

- traceable,
- reviewable,
- contract-governed,
- benchmarked,
- and incrementally extensible.

The goal is not just to generate test artifacts with LLMs.  
The goal is to build a trustworthy system that can evolve from document-driven test design into enterprise AI testing over time.

---

## Contributing

Before making major changes, review:

1. [`docs/roadmap.md`](./roadmap.md)
2. [`docs/acceptance.md`](./acceptance.md)
3. [`docs/model_governance.md`](./model_governance.md)
4. [`docs/agent_guidelines.md`](./agent_guidelines.md)
5. [`docs/architecture.md`](./architecture.md)

When contributing:

- keep changes scoped,
- preserve artifact contracts,
- update docs if behavior changes,
- add or update tests,
- keep provider logic isolated,
- prefer deterministic validation whenever possible.

---

## Recommended Next Docs to Add

As the repository evolves, the following docs are recommended:

- `docs/step_integration_plan.md`
- `docs/benchmark_policy.md`
- `docs/schema_evolution.md`
- `docs/review_collaboration.md`

---

## Summary

LME-Testing is a governed AI-assisted test design framework that starts from documents and moves toward structured BDD generation, review, and eventually enterprise test integration.

It is currently strongest as a document-to-test-design system.  
Its evolution toward enterprise AI testing depends on strong contracts, phase discipline, benchmark-governed model changes, and clear architectural boundaries.
