# Documentation Index

## Purpose

This document is the entry point for the repository documentation set.

It explains:

- what each document is for,
- how the documents relate to each other,
- what order contributors and agents should read them in,
- and how to keep documentation boundaries clear.

This index exists so the documentation set behaves like a system, not just a collection of files.

---

## Documentation Model

The documentation set is intentionally layered.

- `README.md` explains what the project is and what matters now.
- `roadmap.md` defines strategic direction and phase boundaries.
- `implementation_plan.md` defines how roadmap work is executed.
- `acceptance.md` defines when phase work is considered done.
- `architecture.md` defines system boundaries and artifact contracts.
- `model_governance.md` defines model and prompt change controls.
- `agent_guidelines.md` defines how AI agents are allowed to operate.

Other docs may exist, but these are the core control documents.

---

## Documentation Map

### 1. `README.md`

Use this as the project entry point.

It should answer:

- what the project is,
- what it does today,
- what it does not do yet,
- what the current priorities are,
- where the governed documentation lives.

### 2. `docs/roadmap.md`

Use this for strategic direction.

It defines:

- the repo's core methodology,
- the current priority order,
- phase scope and non-scope,
- what is core versus deferred.

### 3. `docs/implementation_plan.md`

Use this for execution-oriented work planning.

It defines:

- task breakdowns,
- task contracts,
- prerequisites,
- validation expectations,
- execution order and scope boundaries.

This is the main "how to execute" document for developers and AI coding agents.

### 4. `docs/acceptance.md`

Use this for phase gates and release readiness.

It defines:

- acceptance criteria per phase,
- required evidence,
- release checklists,
- gate conditions,
- what counts as completion.

### 5. `docs/architecture.md`

Use this for system boundaries and artifact design.

It defines:

- the current and future pipeline,
- artifact contracts,
- deterministic vs LLM-assisted responsibilities,
- module boundaries,
- traceability model,
- validation architecture.

### 6. `docs/model_governance.md`

Use this for model, prompt, benchmark, rollout, and rollback governance.

It defines:

- provider abstraction expectations,
- model onboarding rules,
- prompt versioning expectations,
- baseline benchmark requirements,
- rollout and rollback control.

### 7. `docs/agent_guidelines.md`

Use this for AI coding agent operating discipline.

It defines:

- what agents may do,
- what agents must not do,
- pre-implementation checks,
- phase discipline,
- contract-first change behavior,
- failure-handling expectations.

### 8. `docs/testing_governance.md`

Use this for broader testing-governance topics that go beyond the core execution contract.

### 9. `docs/prompt_lifecycle.md`

Use this for prompt asset lifecycle management.

### 10. `docs/step_integration_plan.md`

Use this for the future bridge between generated BDD and existing executable step assets.

This is not the current execution baseline.
It is a later-phase bridge document.

### 11. `docs/mock_api_validation_plan.md`

Use this for the Stage 3 pre-access mock execution bridge.

It defines:

- the mock API deliverable,
- representative LME rule coverage,
- how BDD scripts call the mock API,
- validation commands and evidence,
- and the boundary between mock execution verification and real LME API readiness.

### 12. `docs/checkpoints.md`

Use this for preserving generated checkpoints and resume prompts across context compaction or fresh sessions.

It records:

- the latest recoverable task state,
- the next single action,
- non-negotiable constraints,
- and a directly reusable resume prompt.

### 13. `docs/ui_test_plan.md`

Use this for the governed UI flow test plan from source artifacts through BDD and Scripts review.

It defines:

- BDD and Scripts tab save/reload expectations,
- artifact refresh expectations,
- manager-level, HTTP-level, and browser-level automation layers,
- current UI test coverage limits,
- and the implemented browser E2E coverage for the primary Review -> BDD -> Scripts path.

---

## Recommended Reading Order

### If you are new to the repo

Read in this order:

1. `README.md`
2. `docs/roadmap.md`
3. `docs/implementation_plan.md`
4. `docs/acceptance.md`
5. `docs/architecture.md`
6. `docs/model_governance.md`
7. `docs/agent_guidelines.md`

Then read supporting docs only as needed:

8. `docs/testing_governance.md`
9. `docs/prompt_lifecycle.md`
10. `docs/step_integration_plan.md`
11. `docs/mock_api_validation_plan.md`
12. `docs/checkpoints.md`
13. `docs/ui_test_plan.md`

### If you are implementing a task

Read in this order:

1. `docs/roadmap.md`
2. `docs/implementation_plan.md`
3. `docs/acceptance.md`
4. `docs/architecture.md`
5. any domain-specific or integration-specific document relevant to the task

### If you are reviewing an AI-generated change

Read in this order:

1. `../AGENTS.md`
2. `docs/agent_guidelines.md`
3. `docs/acceptance.md`
4. `docs/model_governance.md`
5. `docs/architecture.md`
6. the relevant task in `docs/implementation_plan.md`

### If you are working on model or prompt changes

Read in this order:

1. `docs/model_governance.md`
2. `docs/prompt_lifecycle.md`
3. `docs/acceptance.md`
4. `docs/implementation_plan.md`

### If you are working on future BDD / step integration

Read in this order:

1. `docs/architecture.md`
2. `docs/roadmap.md`
3. `docs/implementation_plan.md`
4. `docs/step_integration_plan.md`
5. `docs/acceptance.md`

---

## Recommended Document Responsibilities

To avoid overlap and drift:

- **README** should stay concise and current-state-oriented.
- **roadmap** should remain strategic and phase-based.
- **implementation_plan** should hold task-level execution detail.
- **acceptance** should hold gates and evidence expectations.
- **architecture** should hold system structure and artifact boundaries.
- **model_governance** should hold model, prompt, rollout, and rollback rules.
- **agent_guidelines** should hold AI implementation rules.
- **testing_governance** should hold broader testing operations governance.
- **prompt_lifecycle** should hold prompt lifecycle rules.
- **step_integration_plan** should hold future BDD-to-step bridge logic.
- **checkpoints** should hold recoverable checkpoints and resume prompts.
- **ui_test_plan** should hold UI flow testing expectations and automation layers.

If a document starts taking on another document's responsibility, refactor the boundary instead of letting drift accumulate.

---

## Navigation Note

For agent entry, use:

- `../AGENTS.md`

For repo and phase entry, use:

- `README.md`
- `docs/roadmap.md`

For implementation execution, use:

- `docs/implementation_plan.md`
- `docs/acceptance.md`

---

## Maintenance Expectations

This index should be updated whenever:

- a new major documentation file is added,
- the reading order materially changes,
- the repo documentation structure changes,
- responsibilities shift between documents.

The goal is to keep the documentation set easy to navigate for both humans and AI agents.

---

## Summary

Use this file as the documentation entry point when contributing to the repo.
The core path is simple: understand the current phase in `roadmap.md`, execute through `implementation_plan.md`, validate against `acceptance.md`, and stay within the system boundaries defined in `architecture.md`.
