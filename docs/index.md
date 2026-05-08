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
- `docs/governance/docs_housekeeping.md` defines how documentation may be labeled, summarized, archived, or deleted without losing governance history.

Those documents are the core control documents. Supporting documents are grouped by purpose:

- `docs/governance/` for supporting governance policies.
- `docs/governance/README.md` for the local governance-folder map.
- `docs/planning/` for task plans, validation plans, and stage analysis.
- `docs/planning/README.md` for the local planning-folder map.
- `docs/architecture/` for the main architecture contract and architecture support references.
- `docs/architecture/README.md` for the local architecture-folder map.
- `docs/guides/` for operator and developer guides.
- `docs/guides/README.md` for the local guides-folder map.
- `docs/operations/` for session handoff and checkpoint state.
- `docs/operations/README.md` for the local operations-folder map.
- `docs/releases/` for release notes and baseline records.
- `docs/releases/README.md` for the local releases-folder map.
- `docs/materials/`, `docs/references/`, and `docs/archives/` for source material, historical references, and completed records.
- `docs/materials/README.md` for the local source-materials map.
- `docs/references/README.md` for the local references-folder map.
- `docs/archives/README.md` indexes archived records and explains how to use them safely.

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

For the local planning-folder map, use `docs/planning/README.md`.

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

For the local governance-folder map, use `docs/governance/README.md`.

### 5. `docs/architecture/architecture.md`

Use this for system boundaries and artifact design.

It defines:

- the current and future pipeline,
- artifact contracts,
- deterministic vs LLM-assisted responsibilities,
- module boundaries,
- traceability model,
- validation architecture.

For the local architecture-folder map, use `docs/architecture/README.md`.

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

### 10A. `docs/governance/docs_housekeeping.md`

Use this before cleaning, pruning, or moving documentation.

It defines:

- document classes,
- required status metadata for planning docs,
- safe archiving rules,
- safe deletion rules,
- line-level cleanup expectations,
- and the recommended housekeeping workflow.

Its core principle is curation before deletion: label, summarize, cross-link, archive, and delete only when explicitly safe.

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

### 15. `docs/planning/im_hk_v14_role_review_plan.md`

Use this for the implemented S2-F1 slice promoted from the broader Executable Engineering Knowledge Contract MVP proposal.

It defines:

- the HKv13 -> HKv14 role-friendly impact decision review scope,
- structured decision record inputs and outputs,
- BA / QA Lead / Automation Lead / PM review boundaries,
- acceptance gates,
- implementation boundaries,
- and explicit non-goals.

### 16. `docs/planning/mvp_document_readiness_plan.md`

Use this for the implemented S2-F2 planning slice promoted from the broader Executable Engineering Knowledge Contract MVP proposal.

It defines:

- the MVP document readiness registry scope,
- document readiness inputs and outputs,
- HKv13/HKv14 old/new document registration boundaries,
- placeholder handling for Test Plan and Regression Pack Index,
- acceptance gates,
- implementation evidence,
- and explicit non-goals.

### 17. `docs/planning/mvp_input_document_contract_plan.md`

Use this for the implemented S2-F3 input contract slice.

It defines:

- the minimum Test Plan input contract,
- the minimum Regression Pack Index input contract,
- deterministic readiness/blocking rules,
- optional-input validation boundaries,
- and explicit non-goals for mapping, LLM stages, and external integrations.

### 18. `docs/planning/implementation_plan.md` section `S2-F4`

Use this for the implemented CodeFreddy rule extraction review workflow slice.

It defines:

- the controlled merge boundary,
- the `rule-workflow-session` GUI scope,
- HKv14 PDF extraction and GUI smoke validation,
- follow-up startup/PDF extraction fixes,
- and the broader CodeFreddy prompt/schema/concurrency changes that remain out of scope.

### 19. `docs/planning/implementation_plan.md` section `S2-F5`

Use this for the implemented governed pipeline concurrency slice.

It defines:

- bounded maker/checker batch concurrency,
- deterministic output ordering,
- checker partial failure visibility,
- serial rollback behavior,
- and the prompt/schema/default-model boundaries that remain unchanged.

### 20. `docs/planning/implementation_plan.md` section `S2-F6`

Use this for the partially implemented rewrite prompt governance slice.

It records what exists in code (`REWRITE_SYSTEM_PROMPT`, `build_rewrite_user_prompt()`, and `run_rewrite_pipeline()` usage) and what remains open before the slice can be accepted: dedicated rewrite prompt versioning, metadata tests, acceptance evidence, and governance checks.

### 21. `docs/planning/rule_workflow_scripts_stage_navigation_plan.md`

Use this for the partially implemented HKv14 rule workflow GUI follow-up covering Scripts view implementation visibility, controlled generation of missing step definitions, and stage navigation without restarting.

It defines:

- how Scripts view should show API-backed step definitions under BDD steps,
- how unmatched or unusable steps can generate reviewable draft definitions,
- how Rule Extraction through Finalize navigation should work,
- stale-artifact behavior,
- and the POC/mock/stub boundaries that must remain visible.

### 22. `docs/planning/next_phase_plan.md`

Use this for the consolidated next-phase execution order.

It defines:

- S2-F6A rewrite prompt governance completion,
- S2-F7A/B/C Scripts metadata, draft-step governance, and stage navigation,
- S2-F8 enterprise POC response planning,
- later enterprise slices E1-E7.

### 23. `docs/planning/enterprise_target_architecture_plan.md`

Use this for long-range enterprise architecture discussion.

It includes a pros/cons comparison of Spring AI / Java service, Python micro-services, modular monolith, workflow orchestrator plus service workers, and extension of an existing enterprise platform.

### 24. `docs/planning/assets/tabbed_review_gui_mockups/`

Use this folder as the future visual target reference for the tabbed local workflow.

It contains:

- `01-documents-tab.png`
- `02-rules-bdd-workflow.png`
- `03-bdd-review-tab.png`
- `04-scripts-review-tab.png`
- `05-evidence-traceability-tab.png`

These mockups are not canonical workflow state and do not approve new schemas, permissions, or enterprise features by themselves.

### 25. `docs/planning/mvp_input_document_contract_plan.md`

Use this for the implemented S2-F3 slice that defines the minimum Test Plan and Regression Pack Index input contracts.

It defines:

- required readiness registry metadata,
- minimum human-readable content expectations,
- deterministic readiness and blocking rules,
- implementation expectations and evidence,
- and explicit non-goals.

### Supporting Guide And Reference Folders

- `docs/governance/README.md` explains the governance folder's core policies, supporting policies, and quick routing by task type.
- `docs/planning/README.md` explains the planning folder's current, active, complete, future-support, and archived document buckets.
- `docs/architecture/README.md` explains the architecture folder's current contract and supporting design references.
- `docs/guides/README.md` explains operator and developer guide placement rules.
- `docs/guides/maker_checker_usage.md` explains the maker/checker CLI workflow.
- `docs/guides/rule_extraction_script_guide.md` explains rule extraction operations.
- `docs/archives/20260422_ai_test_generation_demo.md` preserves demo-oriented usage notes.
- `docs/archives/README.md` explains archive scope, preservation reasons, and current archived records.
- `docs/architecture/rule_model_and_parsing_design.md` captures rule model and parsing design detail.
- `docs/architecture/run_directory_structure.md` documents run output layout.
- `docs/operations/README.md` explains session handoff and checkpoint preservation rules.
- `docs/references/README.md` explains how to use historical and external reference materials without treating them as current governance.
- `docs/releases/README.md` explains release-note and baseline-record placement rules.
- `docs/materials/README.md` explains source material lineage and preservation rules.
- `docs/archives/20260422_script_generation_investigation.md`, `docs/archives/stage2_planned_modules.md`, and `docs/archives/s2t01_coverage_analysis.md` preserve supporting Stage 2 planning and analysis.
- `docs/planning/im_hk_v14_downstream_treatment_mapping.md` preserves the S2-C4 deterministic treatment mapping for HKv14 diff candidates.
- `docs/planning/im_hk_v14_role_review_plan.md` preserves the implemented S2-F1 role-friendly impact decision review plan and package boundaries.
- `docs/planning/mvp_document_readiness_plan.md` preserves the implemented S2-F2 MVP document readiness registry plan and package boundaries.
- `docs/planning/mvp_input_document_contract_plan.md` preserves the implemented S2-F3 Test Plan and Regression Pack Index input contract slice.
- `docs/planning/implementation_plan.md` section `S2-F5` preserves the implemented governed pipeline concurrency slice.
- `docs/planning/implementation_plan.md` section `S2-F6` preserves the partial rewrite prompt governance status and remaining completion work.
- `docs/planning/rule_workflow_scripts_stage_navigation_plan.md` preserves the S2-F7 rule workflow GUI Scripts and stage navigation plan; review-session Scripts generation exists, while API-backed metadata and full rule-workflow navigation remain open.
- `docs/planning/next_phase_plan.md` preserves the recommended next-phase order and S2-F8 planning scope.
- `docs/planning/enterprise_target_architecture_plan.md` preserves enterprise architecture option tradeoffs.
- `docs/planning/assets/tabbed_review_gui_mockups/` preserves the target GUI look-and-feel reference for future tabbed workflow discussion.

---

## Housekeeping Snapshot

Use this snapshot as the starting inventory for the next cleanup pass. It is intentionally conservative: no deletion is implied by these labels.

| Area | Current Role | Suggested Action |
|------|--------------|------------------|
| `docs/planning/roadmap.md` | Current control doc for phase direction | Keep current |
| `docs/planning/implementation_plan.md` | Current control doc for task contracts | Keep current; summarize repeated history only after acceptance evidence remains linked |
| `docs/planning/README.md` | Local planning-folder index | Keep current when planning docs are added, archived, or reclassified |
| `docs/governance/acceptance.md` | Current control doc for gates and evidence | Keep current |
| `docs/governance/README.md` | Local governance-folder index | Keep current when governance docs are added or reclassified |
| `docs/architecture/architecture.md` | Current control doc for boundaries and module map | Keep current |
| `docs/architecture/README.md` | Local architecture-folder index | Keep current when architecture docs are added, superseded, or reclassified |
| `docs/guides/README.md` | Local guides-folder index | Keep current when guides are added, deprecated, or archived |
| `docs/operations/README.md` | Local operations-folder index | Keep current when operations files or handoff rules change |
| `docs/references/README.md` | Local references-folder index | Keep current when reference files are added, promoted, archived, or pruned |
| `docs/releases/README.md` | Local releases-folder index | Keep current when release records or baselines are added |
| `docs/materials/README.md` | Local materials-folder index | Keep current when source materials or source-derived inputs are added |
| `docs/planning/next_phase_plan.md` | Active planning and sequencing | Keep active; use as canonical near-term order |
| `docs/planning/rule_workflow_scripts_stage_navigation_plan.md` | Active S2-F7 planning | Keep active until S2-F7 is accepted or superseded |
| `docs/planning/enterprise_poc_feedback_summary.md` | Input summary for S2-F8 | Keep active as planning input; archive after S2-F8 response package captures the outcome |
| `docs/planning/enterprise_target_architecture_plan.md` | Long-range enterprise support planning | Keep as planning support; do not treat as approved implementation scope |
| `docs/planning/tabbed_review_gui_development_plan.md` | Future GUI direction and mockup reference | Keep as planning support for S2-F7 and later E1 |
| `docs/archives/s2t01_coverage_analysis.md` | Complete S2-T01 evidence summary | Archived; current status is owned by implementation/acceptance docs |
| `docs/archives/stage2_planned_modules.md` | Complete historical planning record for S2-B1/B2 | Archived; S2-B1/B2 are implemented and owned by implementation/acceptance docs |
| `docs/planning/mock_api_validation_plan.md` | Complete S2-C1 validation plan | Keep until mock API bridge docs are consolidated; later archive candidate |
| `docs/planning/im_hk_v13_mock_api_validation_plan.md` | Complete S2-C2 validation plan | Keep until Initial Margin bridge docs are consolidated; later archive candidate |
| `docs/planning/im_hk_v14_diff_report.md` | Deterministic HKv13-to-HKv14 diff evidence summary | Preserve as evidence-linked planning record |
| `docs/planning/im_hk_v14_downstream_decision.md` | Human POC downstream decision record | Preserve as decision record |
| `docs/planning/im_hk_v14_downstream_treatment_mapping.md` | Complete S2-C4 deterministic treatment mapping | Preserve as treatment evidence; archive only after acceptance links remain stable |
| `docs/planning/document_library_and_capability_workflow_proposal.md` | Future document/capability workflow proposal | Keep as future planning support; do not implement from this alone |
| `docs/planning/document_library_and_capability_workflow_implementation_plan.md` | Future implementation proposal | Keep as future planning support; may be superseded by later enterprise slices |
| `docs/planning/step_integration_plan.md` | Future Stage 3 execution-readiness bridge | Keep as future planning support |
| `docs/planning/ui_test_plan.md` | Complete S2-D1 UI test plan | Keep while browser test scope remains current; later archive candidate if replaced by acceptance evidence |
| `docs/archives/` | Historical completed or superseded records | Preserve and link when useful |
| `docs/references/` | Historical prompts and external comparison notes | Preserve unless a human approves pruning |
| `docs/operations/checkpoints.md` | Recoverable session history | Preserve; do not prune without explicit human request |

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
10. `docs/governance/docs_housekeeping.md`
11. `docs/planning/step_integration_plan.md`
12. `docs/planning/mock_api_validation_plan.md`
13. `docs/operations/checkpoints.md`
14. `docs/planning/ui_test_plan.md`
15. `docs/planning/mvp_input_document_contract_plan.md`
16. `docs/planning/im_hk_v14_promotion_scope.md`
17. `docs/planning/im_hk_v14_role_review_plan.md`
18. `docs/planning/mvp_document_readiness_plan.md`
19. `docs/planning/rule_workflow_scripts_stage_navigation_plan.md`
20. `docs/planning/next_phase_plan.md`
21. `docs/planning/enterprise_target_architecture_plan.md`
22. `docs/planning/tabbed_review_gui_development_plan.md`

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
- **docs_housekeeping** should hold cleanup, archiving, and deletion rules for the documentation set.
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

For documentation housekeeping, follow `docs/governance/docs_housekeeping.md`:

1. classify files before changing them,
2. add status metadata to active planning docs,
3. summarize or cross-link repeated status instead of deleting it first,
4. archive completed or superseded work only after canonical status is preserved,
5. delete only when the safe deletion rule is satisfied,
6. run `python scripts/check_docs_governance.py` after structural changes.

---

## Summary

Use this file as the documentation entry point when contributing to the repo.
The core path is simple: understand the current phase in `roadmap.md`, execute through `implementation_plan.md`, validate against `acceptance.md`, and stay within the system boundaries defined in `architecture.md`.
