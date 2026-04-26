# Step Integration Plan

## Purpose

This document defines the future bridge from governed BDD artifacts to executable, step-definition-aware workflows.

It exists because the repository is expected to evolve from:

- document-driven rule extraction,
- planning and BDD generation,
- into step-aware, execution-ready testing assets when the roadmap reaches that phase.

This document does **not** assume that the repository is already a full execution platform.
Instead, it defines the staged integration path between:

- normalized BDD artifacts,
- existing step definition libraries,
- gap analysis,
- execution-ready scenario contracts,
- and future execution integration.

This document is a future bridge, not a shortcut around the current roadmap baseline.
It becomes actionable only after normalized BDD artifacts, traceability, and review contracts are stable enough to support it.

This document should be read together with:

- `docs/planning/roadmap.md`
- `docs/planning/implementation_plan.md`
- `docs/architecture/architecture.md`
- `docs/governance/acceptance.md`
- `docs/governance/testing_governance.md`
- `docs/governance/prompt_lifecycle.md`

---

## Why Step Integration Needs Its Own Document

BDD generation and step execution are related, but they are not the same thing.

The repository already has or plans to have:
- source document learning,
- rule normalization,
- planning,
- normalized BDD generation,
- coverage and review workflows.

Step integration adds a new layer of responsibility:

- identifying what can already execute,
- identifying what still needs implementation,
- preserving team style and step reuse,
- translating generated scenarios into execution-aware handoff artifacts.

This deserves a dedicated plan because it introduces:
- reuse constraints,
- executable asset ownership,
- compatibility expectations,
- gap analysis,
- and long-term execution integration.

It should remain a later-phase design concern until the upstream governed artifacts are mature enough to make execution-facing work reliable.

---

## Scope

This document covers:

- BDD style learning,
- normalized BDD to step bridge,
- step registry,
- step mapping,
- gap analysis,
- unmatched-step review,
- step stub generation strategy,
- execution-ready handoff planning.

It does **not** define:
- a full execution engine,
- runtime environment orchestration,
- distributed test execution infrastructure,
- full CI/CD execution deployment details,
- the current repo baseline for Phase 1 or early Phase 2 work.

---

## Core Principles

### 1. Reuse before generation

If an existing step definition can satisfy a generated BDD step, the framework should prefer reuse over new generation.

### 2. Step awareness starts after normalized BDD

Generated raw text is not enough.
Step-aware integration should begin from a governed normalized BDD contract.

### 3. No step bridge without governed intermediate artifacts

Step integration should not begin from direct syntax rendering alone.
The bridge depends on governed normalized BDD outputs, stable traceability, and explicit mapping artifacts.

### 4. Team style is a governed input

Existing BDD conventions are part of execution compatibility, not just stylistic preference.

### 5. Gap visibility is mandatory

The framework must make it obvious which generated steps:
- map cleanly to existing implementations,
- might map with parameterization,
- or require new implementation.

### 6. Execution readiness is a separate contract

BDD is not the same as executable integration.
Execution readiness must be represented explicitly.

### 7. Stable traceability must survive the bridge

Source traceability, including stable source anchors such as paragraph-level identity where applicable, must remain available through BDD and step-integration outputs.

---

## High-Level Bridge Model

The intended bridge is:

`source documents -> rule artifacts -> planning -> normalized BDD -> step registry lookup -> mapping / gap analysis -> executable scenario contract -> execution integration`

This bridge introduces four major layers:

1. style learning
2. step inventory / registry
3. mapping and gap analysis
4. execution-ready handoff

Each layer depends on the previous one being governed well enough to support reviewable downstream decisions.

---

## Step Integration Stages

## Stage 1 - BDD Style Learning

### Goal
Learn reusable BDD conventions from existing assets so generated BDD aligns with team practice.

### Inputs
- existing `.feature` files or equivalent BDD assets,
- project-specific naming and structuring conventions,
- tag usage patterns,
- scenario phrasing patterns,
- shared Given/When/Then conventions.

### Outputs
Governed style artifacts such as:
- BDD style guide,
- style profile,
- reusable formatting patterns,
- tag usage rules,
- scenario naming conventions.

### Governance expectations
- style artifacts must be inspectable,
- style artifacts must be versioned,
- style artifacts must not remain hidden inside prompts only,
- style-learning results must be reviewable by humans.

### Non-goal
This stage does not create execution bindings.

---

## Stage 2 - Step Definition Registry

### Goal
Create a governed registry of existing step definitions so reuse can be measured and planned.

### Inputs
- existing step definition code,
- parser or indexing logic,
- ownership metadata if available,
- parameter pattern information if available.

### Outputs
A step registry capable of capturing:
- step signature inventory,
- source file or library reference,
- ownership or package reference,
- parameter awareness where feasible,
- step category or domain tags if used.

### Governance expectations
- the registry must be reproducible,
- the registry must be reviewable,
- parsing assumptions must be documented,
- missing or ambiguous entries must be visible.

### Non-goal
This stage does not automatically create new steps.

---

## Stage 3 - Mapping and Gap Analysis

### Goal
Map normalized BDD steps to existing step definitions and expose what is missing.

### Inputs
- normalized BDD artifacts,
- step registry,
- matching logic,
- style artifacts where relevant.

### Outputs
Mapping results showing:
- exact matches,
- parameterized matches where supported,
- candidate matches,
- unmatched steps,
- gap reports,
- reuse metrics.

### Governance expectations
- mapping must be reproducible,
- unmatched steps must be explicit,
- candidate matches must not be silently treated as exact matches,
- gap reports should be exportable.

### Recommended statuses
Use explicit mapping statuses such as:
- `matched`
- `matched_parameterized`
- `candidate`
- `unmatched`
- `needs_review`
- `needs_implementation`

### Non-goal
This stage does not yet guarantee runtime executability.

---

## Stage 4 - Review of Unmatched or Weakly Matched Steps

### Goal
Add human control over step gaps and ambiguous mappings.

### Inputs
- mapping results,
- gap reports,
- candidate matches,
- normalized BDD traceability,
- existing ownership metadata.

### Outputs
Structured review decisions such as:
- accept existing mapping,
- prefer alternate candidate,
- require new step implementation,
- mark as deferred,
- mark as domain-specific exception.

### Governance expectations
- decisions must be structured,
- decisions must be traceable to BDD artifacts,
- decisions should be exportable if review workflows require handoff or auditability.

### Non-goal
This stage does not execute the scenario.

---

## Stage 5 - Step Stub Generation Strategy (Optional)

### Goal
Provide a governed path for creating implementation-ready stubs for steps that do not exist.

### Inputs
- unmatched-step review results,
- normalized BDD steps,
- style constraints,
- ownership or package selection rules.

### Outputs
Potential future outputs:
- stub step definitions,
- placeholder implementation files,
- implementation tickets,
- ownership-ready handoff summaries.

### Governance expectations
- stub generation must not silently enter production step libraries,
- generated stubs must be labeled as generated or pending,
- generated stubs should preserve traceability and gap context.

### Non-goal
This stage is not required for the current roadmap baseline and should remain optional until registry and mapping are mature.

---

## Stage 6 - Execution-Ready Handoff

### Goal
Represent the execution-facing contract after BDD and step integration are sufficiently mature.

### Inputs
- normalized BDD artifacts,
- mapping results,
- unmatched-step decisions,
- step bindings,
- deterministic assertion references,
- environment/setup requirements.

### Outputs
An execution-ready scenario artifact that may include:
- normalized BDD references,
- bound step references,
- unresolved gap markers,
- setup requirements,
- cleanup expectations,
- deterministic assertion references,
- input data requirements,
- ownership or execution package hints.

### Governance expectations
- execution-ready artifacts must remain explicit,
- unresolved gaps must remain visible,
- execution assumptions must not be hidden in free-form text,
- traceability to source and BDD artifacts must be preserved.

### Non-goal
This document does not define the runtime engine itself.

---

## BDD Style Learning Details

## What to learn

Style learning should examine at least:
- scenario naming patterns,
- tag usage,
- Given/When/Then balance,
- phrasing consistency,
- step granularity,
- examples or scenario outline patterns,
- domain vocabulary usage.

## What style learning should not do

Style learning should not:
- override schema contracts,
- invent hidden execution assumptions,
- silently rewrite core business intent,
- become an opaque unreviewable heuristic,
- bypass normalized BDD contracts with style-only `.feature` generation.

## Output recommendations

Useful style artifacts may include:
- style profile JSON or equivalent,
- human-readable style guide,
- examples of preferred step forms,
- anti-pattern list.

---

## Step Registry Details

## Minimum registry fields

A governed step registry should ideally contain:
- stable registry entry ID,
- step text or canonical signature,
- parameter markers or pattern shape,
- source location,
- ownership or package reference,
- step status,
- last indexed timestamp.

## Registry quality expectations

The registry should support:
- reproducible regeneration,
- duplicate detection or duplicate surfacing,
- explicit unknowns,
- compatibility with diff or gap analysis.

## Registry non-goals

The registry is not:
- a guarantee of correct behavior,
- a substitute for runtime validation,
- a substitute for code ownership processes.

It is also not required for the current baseline before the roadmap reaches execution-readiness work.

---

## Mapping Strategy

## Matching levels

Suggested matching levels:
1. exact textual match
2. parameterized match
3. candidate semantic match
4. unmatched

## Matching rules

The system should:
- prefer exact and parameterized matches,
- preserve candidate ambiguity explicitly,
- require review when confidence is weak,
- avoid silently collapsing candidate matches into executable truth.

Matching logic should be introduced only after the upstream normalized BDD artifact is stable enough to make mappings reviewable and repeatable.

## Mapping outputs

Useful outputs include:
- mapping JSON or equivalent machine-readable artifact,
- human-readable diff report,
- unmatched-step summary,
- reuse rate metrics,
- per-scenario mapping status.

---

## Gap Analysis

Gap analysis should answer:

- Which BDD steps already map to reusable implementations?
- Which steps are only weakly matched?
- Which steps require new implementation?
- Which gaps are repeated and should be prioritized?
- Which gaps are domain-specific versus framework-generic?

## Recommended gap outputs

Useful artifacts:
- unmatched-step list,
- grouped gap report,
- frequency summary,
- ownership suggestions where available,
- review queue candidates.

---

## Suggested Step Status Labels

The following labels are recommended for step-level governance:

- `matched`
- `matched_parameterized`
- `candidate`
- `needs_review`
- `needs_implementation`
- `deferred`
- `generated_stub`
- `rejected`

Teams may adapt names, but the lifecycle should remain explicit.

---

## Traceability Across the Bridge

The following traceability chain should remain available:

`source document -> source section / clause -> stable source anchor -> atomic rule -> semantic rule -> planning artifact -> normalized BDD -> step mapping -> execution-ready scenario`

This matters because:
- test teams need to understand why a step exists,
- reviewers need to resolve mapping ambiguity,
- execution gaps should be explainable to engineering teams,
- regression analysis depends on stable referential context.

---

## Governance Artifacts for Step Integration

A minimum recommended artifact set for governed step integration includes:

- style-learning artifact,
- step registry artifact,
- mapping artifact,
- gap report,
- review decisions for ambiguous or unmatched steps,
- execution-ready handoff artifact when available.

These should be discoverable and exportable when this bridge is active.
They do not need to exist before the roadmap reaches the relevant phase.

---

## Validation Expectations

## Validation for style learning
- style artifacts are generated reproducibly,
- style artifacts are reviewable,
- style artifacts can be referenced by downstream BDD generation.

## Validation for step registry
- registry regeneration is reproducible,
- representative step definitions are captured,
- parser assumptions are documented.

## Validation for mapping
- exact matches are stable,
- unmatched steps remain explicit,
- gap reports are generated consistently.

## Validation for execution-ready handoff
- contract fields validate,
- unresolved steps remain visible,
- deterministic assertion references are present where required,
- traceability survives the bridge.

Validation depth should remain proportional to the active phase.
The repo should not build a heavy execution-governance program before the bridge itself becomes part of active scope.

---

## Acceptance-Oriented Milestones

## Milestone A - Style-aware normalized BDD
Complete when:
- normalized BDD exists,
- style-learning artifacts exist,
- generated BDD can reference style guidance.

## Milestone B - Step registry and mapping visibility
Complete when:
- a step registry exists,
- normalized BDD can be mapped,
- unmatched steps are visible,
- reuse metrics can be reported.

## Milestone C - Reviewable gap governance
Complete when:
- ambiguous and unmatched steps can be reviewed,
- step gap decisions are structured,
- gap reports are exportable.

## Milestone D - Execution-ready handoff
Complete when:
- step-aware execution artifacts can be produced,
- unresolved implementation gaps remain visible,
- deterministic assertion references are attached where required.

These milestones should be treated as later-phase objectives.
They are not evidence that Phase 1 or early Phase 2 baseline work is complete.

---

## AI Agent Rules for Step Integration

Any AI coding agent working in this layer must follow these rules.

### 1. Reuse before generation
Do not generate or propose new steps without checking for existing reusable steps.

### 2. Do not silently mark candidate matches as exact
Ambiguity must remain visible.

### 3. Do not hide unmatched steps
If a step has no valid mapping, it must remain explicit.

### 4. Preserve traceability
Do not drop source-level traceability when generating BDD, mapping steps, or creating execution-ready handoff artifacts.

### 5. Keep execution readiness explicit
Do not imply that a scenario is executable unless step mapping and required execution metadata are actually present.

### 6. Treat stub generation as governed output
If stubs are generated, they must be labeled and kept separate from trusted manually maintained libraries unless explicitly approved.

### 7. Do not pull step integration forward across phases
If normalized BDD contracts, traceability, or review gates are not yet stable, do not present step integration as current baseline work.

---

## Recommended Future Repo Structure (Conceptual)

The exact structure may evolve, but conceptually the repo should have discoverable places for:

- style artifacts
- step registry artifacts
- mapping outputs
- gap reports
- step-review records
- execution-ready handoff artifacts

Directory names may vary.
The governance requirement is discoverability and traceability, not one hardcoded folder tree.

---

## Review Questions

Use these questions before approving step-integration changes:

- Does this preserve normalized BDD as a governed contract?
- Are style assumptions visible and reviewable?
- Is the step registry reproducible?
- Are candidate matches distinguished from exact matches?
- Are unmatched steps explicit?
- Are gaps exportable and reviewable?
- Does traceability survive the bridge?
- Is execution readiness explicit rather than implied?
- Is this being introduced at the roadmap phase where it actually belongs?

---

## Summary

Step integration is the bridge between AI-generated test design and executable testing assets.

In this repository, that bridge should evolve in stages:

1. learn team BDD style
2. build a governed step registry
3. map normalized BDD to existing steps
4. expose gaps clearly
5. optionally generate governed stubs
6. produce explicit execution-ready handoff artifacts

This staged approach preserves reuse, traceability, and reviewability without pretending that BDD generation alone equals executable automation.

In the current repo phase, the practical implication is narrower: keep step integration clearly positioned as a later bridge, and avoid designing execution-facing machinery before the normalized BDD and governance foundations are ready.
