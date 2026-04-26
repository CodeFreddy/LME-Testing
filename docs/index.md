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
- `docs/planning/roadmap.md` defines strategic direction and phase boundaries.
- `docs/planning/implementation_plan.md` defines how roadmap work is executed.
- `docs/governance/acceptance.md` defines when phase work is considered done.
- `docs/architecture/architecture.md` defines system boundaries and artifact contracts.
- `docs/governance/model_governance.md` defines model and prompt change controls.
- `docs/governance/agent_guidelines.md` defines how AI agents are allowed to operate.

Those documents are the core control documents. Supporting documents are grouped by purpose:

- `docs/governance/` for supporting governance policies.
- `docs/planning/` for task plans, validation plans, and stage analysis.
- `docs/architecture/` for the main architecture contract and architecture support references.
- `docs/guides/` for operator and developer guides.
- `docs/operations/` for session handoff and checkpoint state.
- `docs/releases/` for release notes and baseline records.
- `docs/materials/`, `docs/references/`, and `docs/archives/` for source material, historical references, and completed records.

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

### 2. `docs/planning/roadmap.md`

Use this for strategic direction.

It defines:

- the repo's core methodology,
- the current priority order,
- phase scope and non-scope,
- what is core versus deferred.

### 3. `docs/planning/implementation_plan.md`

Use this for execution-oriented work planning.

It defines:

- task breakdowns,
- task contracts,
- prerequisites,
- validation expectations,
- execution order and scope boundaries.

This is the main "how to execute" document for developers and AI coding agents.

### 4. `docs/governance/acceptance.md`

Use this for phase gates and release readiness.

It defines:

- acceptance criteria per phase,
- required evidence,
- release checklists,
- gate conditions,
- what counts as completion.

### 5. `docs/architecture/architecture.md`

Use this for system boundaries and artifact design.

It defines:

- the current and future pipeline,
- artifact contracts,
- deterministic vs LLM-assisted responsibilities,
- module boundaries,
- traceability model,
- validation architecture.

### 6. `docs/governance/model_governance.md`

Use this for model, prompt, benchmark, rollout, and rollback governance.

It defines:

- provider abstraction expectations,
- model onboarding rules,
- prompt versioning expectations,
- baseline benchmark requirements,
- rollout and rollback control.

### 7. `docs/governance/agent_guidelines.md`

Use this for AI coding agent operating discipline.

It defines:

- what agents may do,
- what agents must not do,
- pre-implementation checks,
- phase discipline,
- contract-first change behavior,
- failure-handling expectations.

### 8. `docs/governance/testing_governance.md`

Use this for broader testing-governance topics that go beyond the core execution contract.

### 9. `docs/governance/prompt_lifecycle.md`

Use this for prompt asset lifecycle management.

### 10. `docs/planning/step_integration_plan.md`

Use this for the future bridge between generated BDD and existing executable step assets.

This is not the current execution baseline.
It is a later-phase bridge document.

### 11. `docs/planning/mock_api_validation_plan.md`

Use this for the Stage 3 pre-access mock execution bridge.

It defines:

- the mock API deliverable,
- representative LME rule coverage,
- how BDD scripts call the mock API,
- validation commands and evidence,
- and the boundary between mock execution verification and real LME API readiness.

### 12. `docs/operations/checkpoints.md`

Use this for preserving generated checkpoints and resume prompts across context compaction or fresh sessions.

It records:

- the latest recoverable task state,
- the next single action,
- non-negotiable constraints,
- and a directly reusable resume prompt.

### 13. `docs/planning/ui_test_plan.md`

Use this for the governed UI flow test plan from source artifacts through BDD and Scripts review.

It defines:

- BDD and Scripts tab save/reload expectations,
- artifact refresh expectations,
- manager-level, HTTP-level, and browser-level automation layers,
- current UI test coverage limits,
- and the implemented browser E2E coverage for the primary Review -> BDD -> Scripts path.

### 14. `docs/planning/im_hk_v14_promotion_scope.md`

Use this for the promoted HKv14 downstream implementation slice.

It defines:

- the human promotion decision,
- allowed HKv14 downstream scope,
- contracts and non-outputs,
- acceptance gates,
- rollback boundaries,
- and the next deterministic candidate-mapping action.

### Supporting Guide And Reference Folders

- `docs/guides/maker_checker_usage.md` explains the maker/checker CLI workflow.
- `docs/guides/rule_extraction_script_guide.md` explains rule extraction operations.
- `docs/archives/20260422_ai_test_generation_demo.md` preserves demo-oriented usage notes.
- `docs/architecture/rule_model_and_parsing_design.md` captures rule model and parsing design detail.
- `docs/architecture/run_directory_structure.md` documents run output layout.
- `docs/archives/20260422_script_generation_investigation.md`, `docs/planning/stage2_planned_modules.md`, and `docs/planning/s2t01_coverage_analysis.md` preserve supporting Stage 2 planning and analysis.
- `docs/planning/im_hk_v14_downstream_treatment_mapping.md` preserves the S2-C4 deterministic treatment mapping for HKv14 diff candidates.

---

## Recommended Reading Order

### If you are new to the repo

Read in this order:

1. `README.md`
2. `docs/planning/roadmap.md`
3. `docs/planning/implementation_plan.md`
4. `docs/governance/acceptance.md`
5. `docs/architecture/architecture.md`
6. `docs/governance/model_governance.md`
7. `docs/governance/agent_guidelines.md`

Then read supporting docs only as needed:

8. `docs/governance/testing_governance.md`
9. `docs/governance/prompt_lifecycle.md`
10. `docs/planning/step_integration_plan.md`
11. `docs/planning/mock_api_validation_plan.md`
12. `docs/operations/checkpoints.md`
13. `docs/planning/ui_test_plan.md`
14. `docs/planning/im_hk_v14_promotion_scope.md`

### If you are implementing a task

Read in this order:

1. `docs/planning/roadmap.md`
2. `docs/planning/implementation_plan.md`
3. `docs/governance/acceptance.md`
4. `docs/architecture/architecture.md`
5. any domain-specific or integration-specific document relevant to the task

### If you are reviewing an AI-generated change

Read in this order:

1. `../AGENTS.md`
2. `docs/governance/agent_guidelines.md`
3. `docs/governance/acceptance.md`
4. `docs/governance/model_governance.md`
5. `docs/architecture/architecture.md`
6. the relevant task in `docs/planning/implementation_plan.md`

### If you are working on model or prompt changes

Read in this order:

1. `docs/governance/model_governance.md`
2. `docs/governance/prompt_lifecycle.md`
3. `docs/governance/acceptance.md`
4. `docs/planning/implementation_plan.md`

### If you are working on future BDD / step integration

Read in this order:

1. `docs/architecture/architecture.md`
2. `docs/planning/roadmap.md`
3. `docs/planning/implementation_plan.md`
4. `docs/planning/step_integration_plan.md`
5. `docs/governance/acceptance.md`

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
- **planning docs** should hold future BDD-to-step bridge logic, validation plans, and stage-specific analyses.
- **guides** should hold operational workflows.
- **operations** should hold session continuity files such as handoff and checkpoints.
- **architecture docs** should hold the main system contract plus supporting design detail that is too specific for the main architecture overview.
- **checkpoints** should hold recoverable checkpoints and resume prompts.

If a document starts taking on another document's responsibility, refactor the boundary instead of letting drift accumulate.

---

## Navigation Note

For agent entry, use:

- `../AGENTS.md`

For repo and phase entry, use:

- `README.md`
- `docs/planning/roadmap.md`

For implementation execution, use:

- `docs/planning/implementation_plan.md`
- `docs/governance/acceptance.md`

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
