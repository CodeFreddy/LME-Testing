# Documentation Index

## Purpose

This document is the entry point for the repository documentation set.

It explains:

- what each document is for,
- how the documents relate to each other,
- what order new contributors should read them in,
- and how the documentation should be organized in the repo.

This index exists so the documentation set behaves like a system, not just a collection of files.

---

## Documentation Map

### 1. `README.md`
Use this as the project entry point.

It should answer:
- what the project is,
- what it does today,
- what it does not do yet,
- where the documentation lives,
- how a new contributor should get started.

### 2. `docs/roadmap.md`
Use this for strategic direction.

It defines:
- short-term, mid-term, and long-term goals,
- phase scope,
- main platform evolution path,
- what is core versus deferred.

### 3. `docs/implementation_plan.md`
Use this for execution-oriented work planning.

It defines:
- task breakdowns,
- task contracts,
- prerequisites,
- input and output contracts,
- acceptance evidence expectations.

This is the main “how to execute” document for developers and AI coding agents.

### 4. `docs/architecture.md`
Use this for system boundaries and artifact design.

It defines:
- the current and future pipeline,
- artifact contracts,
- deterministic vs LLM-assisted responsibilities,
- module boundaries,
- traceability model,
- validation architecture.

### 5. `docs/acceptance.md`
Use this for phase gates and release readiness.

It defines:
- acceptance criteria per phase,
- required evidence,
- release checklists,
- gate conditions.

### 6. `docs/model_governance.md`
Use this for model, prompt, benchmark, rollout, and rollback governance.

It defines:
- provider abstraction expectations,
- model onboarding rules,
- prompt versioning expectations,
- benchmark requirements,
- rollout and rollback control.

### 7. `docs/agent_guidelines.md`
Use this for AI coding agent operating discipline.

It defines:
- what agents may do,
- what agents must not do,
- pre-implementation checks,
- change summary expectations,
- phase discipline,
- failure-handling expectations.

### 8. `docs/testing_governance.md`
Use this for test-operations governance.

It defines:
- prompt-set governance from a testing perspective,
- review and feedback governance,
- confidence and failure analysis,
- pre-run and post-run validation,
- integration test procedures,
- operational testing quality controls.

### 9. `docs/prompt_lifecycle.md`
Use this for prompt asset lifecycle management.

It defines:
- prompt inventory rules,
- prompt IDs,
- prompt dependencies,
- versioning,
- deprecation,
- retirement,
- rollback expectations.

### 10. `docs/step_integration_plan.md`
Use this for the bridge between generated BDD and existing executable step assets.

It defines:
- BDD style learning,
- step definition registry,
- step mapping,
- gap analysis,
- implementation-needed markers,
- and execution handoff expectations.

---

## Recommended Reading Order

### If you are new to the repo
Read in this order:

1. `README.md`
2. `docs/roadmap.md`
3. `docs/architecture.md`
4. `docs/implementation_plan.md`
5. `docs/acceptance.md`
6. `docs/model_governance.md`
7. `docs/agent_guidelines.md`

Then read:
8. `docs/testing_governance.md`
9. `docs/prompt_lifecycle.md`
10. `docs/step_integration_plan.md`

### If you are implementing a task
Read in this order:

1. `docs/roadmap.md`
2. `docs/implementation_plan.md`
3. `docs/acceptance.md`
4. `docs/architecture.md`
5. any domain-specific or integration-specific document relevant to the task

### If you are reviewing an AI-generated change
Read in this order:

1. `docs/agent_guidelines.md`
2. `docs/acceptance.md`
3. `docs/model_governance.md`
4. `docs/architecture.md`
5. the relevant task in `docs/implementation_plan.md`

### If you are working on model or prompt changes
Read in this order:

1. `docs/model_governance.md`
2. `docs/prompt_lifecycle.md`
3. `docs/testing_governance.md`
4. `docs/acceptance.md`

### If you are working on BDD / step integration
Read in this order:

1. `docs/step_integration_plan.md`
2. `docs/architecture.md`
3. `docs/implementation_plan.md`
4. `docs/acceptance.md`

---

## Recommended Repo Documentation Structure

Suggested documentation structure:

```text
README.md
docs/
  index.md
  roadmap.md
  implementation_plan.md
  architecture.md
  acceptance.md
  model_governance.md
  agent_guidelines.md
  testing_governance.md
  prompt_lifecycle.md
  step_integration_plan.md
```

This layout keeps the project entry point lightweight while keeping all governed operating documents in one discoverable location.

---

## Recommended Document Responsibilities

To avoid overlap and drift:

- **README** should stay concise.
- **roadmap** should remain strategic.
- **implementation_plan** should hold task-level execution detail.
- **architecture** should hold system structure and boundaries.
- **acceptance** should hold phase gates and evidence requirements.
- **model_governance** should hold multi-model and prompt rollout rules.
- **agent_guidelines** should hold AI implementation rules.
- **testing_governance** should hold testing operations governance.
- **prompt_lifecycle** should hold prompt asset lifecycle rules.
- **step_integration_plan** should hold BDD-to-step bridge logic.

If a document starts taking on another document’s responsibility, refactor the boundary instead of letting drift accumulate.

---

## Suggested README Navigation Section

The README can include a short navigation section like this:

### Documentation
- `docs/index.md` — documentation entry point
- `docs/roadmap.md` — strategic roadmap
- `docs/implementation_plan.md` — task execution plan
- `docs/architecture.md` — architecture and artifact model
- `docs/acceptance.md` — acceptance gates
- `docs/model_governance.md` — model and prompt governance
- `docs/agent_guidelines.md` — AI agent rules
- `docs/testing_governance.md` — testing governance
- `docs/prompt_lifecycle.md` — prompt lifecycle rules
- `docs/step_integration_plan.md` — BDD to step integration plan

---

## Suggested First Commit Scope

A clean first documentation commit can include:

- `README.md`
- `docs/index.md`
- `docs/roadmap.md`
- `docs/implementation_plan.md`
- `docs/architecture.md`
- `docs/acceptance.md`
- `docs/model_governance.md`
- `docs/agent_guidelines.md`
- `docs/testing_governance.md`
- `docs/prompt_lifecycle.md`
- `docs/step_integration_plan.md`

### Suggested commit message

`docs: add governed roadmap, architecture, acceptance, model, testing, prompt, and step-integration documentation`

---

## Suggested PR Description Template

A documentation PR introducing this structure can use a summary like:

### Summary
Add the initial governed documentation framework for the repository.

### Includes
- strategic roadmap
- execution-oriented implementation plan
- architecture document
- acceptance and release gates
- model governance
- AI agent guidelines
- testing governance
- prompt lifecycle governance
- BDD to step integration plan
- documentation index

### Why
This creates a repo-readable control layer so the project can evolve safely across:
- multiple LLM APIs,
- AI coding agent contributions,
- growing document coverage,
- and future BDD-to-execution integration.

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

This documentation set is intentionally layered.

- `README.md` introduces the project.
- `roadmap.md` defines where it is going.
- `implementation_plan.md` defines how work is executed.
- `architecture.md` defines how the system is shaped.
- `acceptance.md` defines when work is considered done.
- `model_governance.md`, `testing_governance.md`, and `prompt_lifecycle.md` govern change.
- `agent_guidelines.md` governs AI contributors.
- `step_integration_plan.md` defines the BDD-to-execution bridge.

Use this file as the documentation entry point when contributing to the repo.
