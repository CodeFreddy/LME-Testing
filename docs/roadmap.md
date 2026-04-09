# Enterprise AI Testing Upgrade Roadmap

## Purpose

This document defines the phased upgrade plan for this repository.

It is not a feature wish list and it is not a product vision deck.
It is a governed execution contract for how this repo should evolve under probabilistic LLM behavior.

The roadmap is written primarily for:

1. AI coding agents modifying the repo,
2. tech leads and reviewers governing repo evolution,
3. developers implementing roadmap tasks.

It is written secondarily for testers and other contributors who need to understand the platform direction.

---

## Current Starting Point

The current system is a document-driven test design prototype with a usable design loop:

`source docs -> extraction scripts -> atomic_rules.json -> semantic_rules.json -> maker -> checker -> review-session -> rewrite -> checker -> report`

Today, the framework already supports:

- rule extraction into `atomic_rule` and `semantic_rule` artifacts,
- BDD-style scenario generation through `maker`,
- scenario quality and coverage assessment through `checker`,
- human approval / rewrite / reject decisions through a local review session,
- final HTML reporting.

Current weaknesses that must be addressed before expansion:

- upstream rule extraction governance is not yet a first-class validation layer,
- model and prompt stability governance are not explicit enough,
- stable source-anchor traceability is not yet consistently enforced,
- review remains local and single-user oriented,
- the repository still appears early-stage and requires stronger engineering controls.

The immediate risk is not lack of downstream intelligence.
The immediate risk is uncontrolled upstream quality, weak reproducibility, and insufficiently governed model-driven behavior.

---

## What This Roadmap Is and Is Not

This roadmap is:

- a phase-based execution contract,
- a prioritization tool for controlled repo evolution,
- a boundary document for AI agent work,
- a guide for what should be stabilized before scope expands.

This roadmap is not:

- a commitment to build every attractive future capability now,
- a hosted product plan,
- a requirement to introduce enterprise workflow layers before the repo is ready,
- a replacement for `docs/implementation_plan.md`, `docs/architecture.md`, or `docs/acceptance.md`.

Exploratory work may happen outside the current phase.
It must not be presented as completed governed capability until the relevant phase contracts and acceptance gates are satisfied.

---

## Core Methodology

These principles apply to all phases of the roadmap.

### 1. Governance-contract-first

LLM outputs must be governed, not trusted.

All meaningful LLM-driven artifacts should be controlled through:

- explicit schemas,
- versioned prompts,
- artifact metadata,
- benchmark baselines,
- reviewable change records,
- rollback-safe configuration.

### 2. Deterministic responsibilities before agentic expansion

The repo should first strengthen deterministic control layers before expanding LLM-driven workflow stages.

Deterministic modules should own:

- schema validation,
- enum and field validation,
- duplicate detection thresholds,
- traceability checks,
- coverage accounting,
- release gates,
- execution assertions where possible.

LLMs may assist with:

- rule normalization,
- ambiguity detection,
- planning drafts,
- BDD generation suggestions,
- rewrite proposals.

### 3. Upstream quality dominates downstream value

No downstream maker, checker, review, or reporting logic can compensate for invalid or weak upstream rule artifacts.

For the current repo stage, the first priority is to make rule-layer artifacts more valid, traceable, and reproducible before adding heavier downstream capabilities.

### 4. Repo-readable execution context

Durable workflow behavior must be reconstructable from repo-readable assets rather than chat state.

That means the repo should contain enough stable context in:

- docs,
- schemas,
- prompts,
- configs,
- benchmark sets,
- task contracts,
- acceptance criteria.

### 5. Phase discipline over scope creep

Each phase must define scope and non-scope.

Later-phase ideas may be explored, but they must not quietly enter the repo as if they were already part of the current governed baseline.

### 6. Human review remains a control layer

Human review is part of the current architecture, not an optional UX enhancement.

Automation may accelerate generation and validation, but it must not bypass required human decision points where governance still depends on reviewer judgment.

---

## Cross-Model Governance Requirements

These requirements apply regardless of which LLM API is used.

### 1. Provider abstraction

The provider layer must expose a stable model strategy contract including:

- provider name,
- model name,
- model version if available,
- prompt version,
- temperature or decoding settings,
- timeout and retry settings.

All governed artifacts produced by maker, checker, rewrite, and future planner modules should record this metadata.

### 2. Prompt versioning

Every production prompt should have:

- a stable prompt ID,
- semantic version,
- owner,
- change log,
- linked benchmark set.

### 3. Regression baseline

The repo should formalize a small baseline suite, starting from the existing `poc_two_rules` style sample flow.

Baseline categories should include:

- extraction sanity,
- maker structural validity,
- checker consistency,
- report generation,
- end-to-end smoke.

### 4. Model compatibility policy

A new model or provider should only be adopted if it passes:

- schema conformance,
- benchmark threshold,
- baseline checker stability threshold where applicable,
- artifact diff review.

### 5. Rollback policy

A new model or prompt version must be reversible without changing business logic or artifact schemas.

### 6. Repo-readable execution context

Durable workflow behavior must be reconstructable from repo-readable prompts, configs, schemas, benchmark sets, and implementation task definitions rather than chat state alone.

---

## Current Priority Order

The current recommended execution order for the repo is:

1. govern upstream rule artifacts,
2. make baseline runs reproducible in CI,
3. make model and prompt behavior traceable,
4. expose checker instability on a small baseline set,
5. only then expand upstream ingestion and downstream BDD normalization.

This ordering reflects the current maturity of the repo.
It is intentionally biased toward control, validation, and reproducibility before workflow expansion.

---

## Phase 1 - Baseline Control and Pipeline Hardening (0-3 Months)

### Stage Goal

Stabilize the current design pipeline so that different model APIs can be used without silently degrading artifact quality.

### Why this phase matches the current repo

The repo already has a working maker-checker-review-report loop.
What it lacks is stronger control over upstream rule quality, traceability, and reproducible validation.

This phase therefore focuses on control surfaces, not new workflow breadth.

### In Scope

- rule-layer schema formalization,
- upstream validation and quality gates,
- baseline CI and smoke reproducibility,
- stable source-anchor groundwork,
- prompt and artifact metadata,
- checker stability visibility on a small baseline set,
- repo docs and rules for AI agent execution.

### Out of Scope

- multi-user hosted review platform,
- execution engine,
- step definition integration,
- advanced planning intelligence,
- full enterprise workflow orchestration,
- persona-specific output modes as a roadmap priority.

### Key Deliverables

#### A. Formal schema layer

Add versioned JSON Schemas for:

- `atomic_rule`,
- `semantic_rule`,
- maker output,
- checker output,
- human review output.

#### B. Upstream validation pipeline

Insert a formal validation stage so the rule path becomes:

`docs -> extraction scripts -> atomic_rules.json -> schema validation -> duplicate candidate detection -> rule_type enum validation -> semantic_rules.json`

This should be introduced incrementally where necessary so existing working paths are not broken without migration support.

#### C. Baseline CI and reproducible smoke flow

Add CI to run:

- end-to-end smoke on a minimal baseline,
- schema validation tests,
- reporting smoke test,
- core unit tests for pipeline and review session bootstrapping.

#### D. Stable source-anchor groundwork

Introduce and propagate a stable source anchor such as `paragraph_id` or equivalent.

For the current phase, this may begin as additive metadata in extraction and rule artifacts before becoming a stricter downstream requirement everywhere.

#### E. Prompt and artifact metadata

Every generated governed artifact should include:

- prompt version,
- model ID,
- provider,
- run timestamp,
- source artifact hash where applicable,
- pipeline version.

#### F. Checker stability signal on baseline set

Run checker twice on the same small baseline set and flag inconsistent conclusions.

This is a baseline sampling control, not a requirement to double-run the full corpus by default.

#### G. Repo docs and agent operating rules

Ensure the repo has and uses the minimum governance documents needed for controlled implementation:

- `docs/roadmap.md`,
- `docs/implementation_plan.md`,
- `docs/acceptance.md`,
- `docs/model_governance.md`,
- `docs/agent_guidelines.md`.

### Acceptance Criteria

Phase 1 is accepted only if:

- all core rule artifacts are schema-validated in CI,
- invalid `rule_type` values fail the pipeline,
- baseline smoke runs are reproducible in CI,
- every maker and checker artifact records model and prompt metadata,
- checker instability can be surfaced on the baseline set,
- stable source anchors exist where applicable in governed upstream artifacts,
- roadmap and governance docs are present and usable in the repo.

### Success Metric

The system becomes trustworthy enough for repeated internal development and controlled model change, even if it is not yet enterprise-ready.

---

## Phase 2 - Planned Test Design and Normalized BDD Artifacts (3-9 Months)

### Stage Goal

Upgrade from a stable design prototype into an AI-assisted test planning and BDD generation platform that can handle multiple document categories while keeping intermediate artifacts governed and reviewable.

### Why this phase matches the current repo

After Phase 1, the repo should have stronger schema control, metadata, and baseline validation.
That is the minimum foundation needed before introducing new LLM-assisted stages such as planning and normalized BDD generation.

This phase should add stable intermediate contracts, not just more generation steps.

### In Scope

- multi-document ingestion,
- stronger traceability from source to generated artifacts,
- test planning as a governed intermediate stage,
- normalized BDD contract,
- BDD style learning,
- export interfaces for downstream execution teams,
- limited review collaboration only if it remains lightweight and file-based.

### Out of Scope

- full runtime execution of all generated scenarios,
- autonomous end-to-end execution against all systems,
- hosted multi-user governance platform,
- full enterprise RBAC,
- broad product-style collaboration features as default roadmap commitments.

### Key Deliverables

#### A. Multi-document ingestion framework

Support defined source classes, for example:

- rulebooks,
- product specs,
- API docs,
- business workflow docs,
- compliance or policy docs,
- release notes and change documents.

Each document class must define:

- parsing strategy,
- extraction constraints,
- expected rule patterns,
- known failure modes.

#### B. Source-aware rule extraction and synthesis

Expand the governed path from source documents into:

- source-aware `atomic_rule` artifacts,
- source-aware `semantic_rule` artifacts,
- preserved source anchors and source references.

This phase should strengthen the path from raw document structure into existing rule-layer artifacts without weakening current schema discipline.

#### C. Test planning layer

Introduce a planner stage between `semantic_rule` and BDD generation.

New flow:

`semantic_rules -> planning -> test_objectives -> scenario families -> BDD generation`

The planner should produce:

- priority,
- risk level,
- coverage intent,
- scenario family,
- dependency notes,
- recommended validation strategy.

Planner outputs must be versioned, schema-defined, and reviewable before planner-driven generation is treated as governed baseline behavior.

#### D. Normalized BDD contract layer

Define a normalized BDD representation independent of final output syntax.

This becomes the canonical intermediate artifact before Gherkin export or later step integration.

Normalized BDD should be introduced only with an explicit schema and validation approach.

#### E. BDD style learning

Learn and version team BDD style conventions from existing assets so generated BDD aligns with reusable project practice.

#### F. Gherkin export and downstream handoff

Export normalized BDD into `.feature` files or equivalent downstream artifacts without making raw syntax the only governed representation.

#### G. Step registry visibility

Introduce early visibility into step-definition reuse needs through:

- step inventory awareness,
- mapping preparation,
- gap surfacing,
- implementation-needed markers.

This should stop short of full execution binding logic in this phase.

#### H. Quality and traceability reporting

Enhance reports with:

- rule type coverage heatmap,
- unstable checker decisions on the benchmark set,
- baseline drift versus previous runs,
- document class breakdown,
- traceability drill-down,
- JSON or CSV export where useful.

### Acceptance Criteria

Phase 2 is accepted only if:

- multiple document classes are supported with explicit parsing rules,
- planner outputs are versioned and schema-validated,
- normalized BDD artifacts exist as governed intermediate outputs,
- generated BDD artifacts are traceable to governed upstream artifacts,
- reporting can show baseline diffs and unstable judgments where applicable,
- model change regression remains enforced before adoption.

### Success Metric

The system becomes usable for controlled team pilots in document-driven test planning and BDD generation without losing reviewability or contract clarity.

---

## Phase 3 - Execution Readiness and Selective Enterprise Controls (9-18 Months)

### Stage Goal

Extend from design and planning artifacts into execution integration, deterministic assertions for high-value rule classes, and selective enterprise-grade governance controls that are justified by actual platform maturity.

### Why this phase matches the current repo

Execution integration only becomes valuable once rule artifacts, planning outputs, normalized BDD, and traceability are stable enough to bind to execution assets.

This phase should focus on execution readiness and high-value controls, not on turning the repo into a hosted product by default.

### In Scope

- step definition registry and mapping,
- execution-ready scenario contract,
- deterministic oracle layer for domain-critical assertions,
- release governance,
- selective operational metrics that support governed operation,
- controlled rollout across model providers.

### Out of Scope

- unrestricted autonomous test execution without approval gates,
- fully free-form agentic code generation without schema and review controls,
- full hosted review product as a required roadmap outcome,
- broad multi-tenant platform commitments that are not yet justified by repo maturity.

### Key Deliverables

#### A. Step definition integration layer

Create a mapping layer between normalized BDD steps and existing step definitions.

This should support:

- exact step match,
- parameterized step match,
- candidate step suggestion,
- unmatched step reporting,
- reuse score,
- ownership per step library.

#### B. Execution readiness contract

Introduce an `ExecutableScenario` representation that extends BDD with:

- environment requirements,
- input data requirements,
- setup hooks,
- expected deterministic assertions,
- cleanup hooks,
- linked step definitions.

#### C. Deterministic oracle framework

Move execution truth away from LLM judgment wherever possible for high-value structured rule categories.

Deterministic modules should own:

- field validation,
- state validation,
- calculation validation,
- deadline and window checks,
- event sequence verification,
- pass or fail accounting.

This should be scoped to domain-critical rule classes rather than treated as an abstract universal framework first.

#### D. Selective governance and observability

Track the minimum operational signals needed for governed operation, such as:

- schema failure rate,
- checker instability rate,
- coverage trend,
- step binding success rate where applicable.

Additional enterprise observability should be introduced only when justified by actual platform usage.

#### E. Release governance

Formalize:

- release tags,
- compatibility matrix,
- benchmark gates,
- migration notes,
- approved provider list.

### Acceptance Criteria

Phase 3 is accepted only if:

- normalized BDD can be bound to existing step definitions with measurable reuse,
- unmatched steps are surfaced automatically,
- execution-ready scenarios can be exported consistently,
- deterministic assertions exist for at least the core structured rule categories that matter most,
- provider rollout requires benchmark pass and rollback path,
- operational metrics are available for governed release and platform review.

### Success Metric

The system becomes execution-ready and governance-mature enough to support enterprise-style usage without depending on uncontrolled LLM judgment.

---

## AI Agent Contribution Rules

Any AI coding agent working on this roadmap must follow these repository-level rules.

### 1. Do not bypass schemas

No artifact format change is allowed without:

- schema update,
- migration note,
- acceptance update,
- test update.

### 2. Do not couple business logic to a specific model

All provider-specific behavior must remain behind provider or strategy interfaces.

### 3. Do not replace structured outputs with free-form text

If a module currently emits JSON, it must remain structured unless the contract is formally changed.

### 4. Do not expand scope across phases

Phase 1 work must not quietly add Phase 2 or Phase 3 scope unless explicitly approved.

### 5. Every meaningful feature must ship with a testable acceptance outcome

No roadmap item is complete without a testable acceptance condition.

---

## Documentation Operating Model

To reduce overlap and drift, documents in this repo should keep stable responsibilities.

### `docs/roadmap.md`

Contains phase goals, scope boundaries, non-scope, deliverable classes, and phase gates.

### `docs/implementation_plan.md`

Contains execution-oriented task breakdowns with input and output contracts, prerequisites, and validation expectations.

### `docs/architecture.md`

Defines:

- pipeline stages,
- artifact contracts,
- module boundaries,
- deterministic versus LLM-assisted responsibilities.

### `docs/acceptance.md`

Lists formal phase-based acceptance criteria, required evidence, and release gates.

### `docs/model_governance.md`

Defines:

- provider abstraction,
- model onboarding rules,
- prompt versioning,
- baseline regression,
- rollout and rollback policy.

### `docs/agent_guidelines.md`

Defines how AI coding agents are allowed to modify the repo.

### Document addition rule

New docs should only be added when a concern has a stable lifecycle and cannot be kept clear within the existing governance boundaries.

---

## Repo Summary Paragraph

This project should evolve in three controlled stages. Phase 1 should harden the current document-to-rule-to-BDD design pipeline with schemas, CI, source-anchor groundwork, model metadata, and baseline checker stability visibility. Phase 2 should add source-aware ingestion, governed planning outputs, normalized BDD artifacts, and stronger traceability so teams can pilot document-driven test design safely. Phase 3 should connect governed design artifacts to step-definition-aware execution readiness, deterministic assertions for high-value rule classes, and selective enterprise-grade release controls. Because multiple LLM APIs may be used, every stage requires schema contracts, versioned prompts, benchmark gates, repo-readable execution context, and rollback-safe model governance.
