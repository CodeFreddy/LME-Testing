# Enterprise AI Testing Upgrade Roadmap

## Purpose

This document defines the phased upgrade plan for this repository.

The goal is to evolve the current document-driven test design prototype into an enterprise AI testing framework that can:

- learn and normalize rules from different categories of documents,
- plan test strategy and test intent,
- generate structured BDD scenarios,
- and eventually integrate with existing step definitions and execution layers.

This roadmap is intended to serve two purposes:

1. a practical implementation plan for developers,
2. an execution contract for AI coding agents contributing to the repo.

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
- review remains local and single-user oriented,
- the repository still appears early-stage and requires stronger engineering controls.

---

## Upgrade Principles

These principles apply to all phases of the roadmap.

### 1. Model outputs must be governed, not trusted

All LLM-driven stages are probabilistic and must be controlled through:

- explicit schemas,
- versioned prompts,
- artifact metadata,
- regression baselines,
- rollbackable model configuration.

### 2. Upstream rule quality determines downstream value

No downstream maker, checker, review, or report logic can compensate for invalid `atomic_rule` or `semantic_rule` inputs.

Upstream validation is mandatory before expanding downstream scope.

### 3. Separate deterministic responsibilities from LLM-assisted responsibilities

LLMs may continue to assist with:

- rule normalization,
- ambiguity detection,
- test planning drafts,
- BDD generation suggestions.

Deterministic modules must own:

- schema validation,
- enum validation,
- coverage accounting,
- traceability checks,
- duplicate detection thresholds,
- execution result assertions where possible.

### 4. Each phase must define scope and non-scope

Every phase must clearly define what is included and what is intentionally deferred.

### 5. AI agents must work against contracts

AI coding agents must operate against:

- versioned docs,
- schema contracts,
- acceptance criteria,
- benchmark gates,
- and explicit module boundaries.

No undocumented structural change should be introduced by an agent.

---

## Cross-Model Governance Requirements

These requirements apply regardless of which LLM API is used.

### 1. Provider abstraction

The provider layer must expose a stable model strategy contract including:

- provider name,
- model name,
- model version if available,
- prompt version,
- temperature / decoding settings,
- timeout / retry settings.

All artifacts produced by maker, checker, rewrite, and future planner modules must record this metadata.

### 2. Prompt versioning

Every production prompt must have:

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

A new model API may only be adopted if it passes:

- schema conformance,
- benchmark threshold,
- checker stability threshold,
- artifact diff review.

### 5. Rollback policy

A new model or prompt version must be reversible without changing business logic or artifact schemas.

### 6. Repo-readable execution context

Durable workflow behavior must be reconstructable from repo-readable prompts, configs, schemas, benchmark sets, and implementation task definitions rather than chat state alone.

---

## Short-Term Plan (0–3 Months)

### Stage Goal

Stabilize the current design pipeline so that different model APIs can be used without silently degrading artifact quality.

### In Scope

- extraction validation,
- schema formalization,
- rule type governance,
- stable source-anchor traceability,
- baseline CI,
- prompt and artifact versioning,
- checker stability visibility,
- repo docs for AI agent execution.

### Out of Scope

- multi-user hosted review platform,
- execution engine,
- step definition integration,
- advanced planning intelligence,
- full enterprise workflow orchestration.

### Key Deliverables

#### A. Formal schema layer

Add versioned JSON Schemas for:

- `atomic_rule`,
- `semantic_rule`,
- maker output,
- checker output,
- human review output.

#### B. Rule validation pipeline

Insert a formal validation stage:

`docs -> extraction scripts -> atomic_rules.json -> schema validation -> duplicate candidate detection -> rule_type enum validation -> semantic_rules.json`

#### C. Stable source-anchor traceability

Introduce and propagate a stable source anchor such as `paragraph_id` or equivalent from source segmentation into rule artifacts and downstream governed outputs where applicable.

#### D. Minimal rule quality gates

Implement:

- required fields validation,
- `rule_type` enum enforcement,
- duplicate candidate detection,
- invalid trace reference detection,
- schema failure as hard-stop.

#### E. Prompt and artifact metadata

Every generated artifact must include:

- prompt version,
- model ID,
- provider,
- run timestamp,
- source artifact hash,
- pipeline version.

#### F. Baseline CI

Add CI to run:

- end-to-end smoke on a minimal baseline,
- schema validation tests,
- reporting smoke test,
- core unit tests for pipeline and review session bootstrapping.

#### G. Checker stability signal

Run checker twice on the same small baseline and flag inconsistent conclusions.

#### H. Repo docs for AI agents

Add:

- `docs/roadmap.md`
- `docs/implementation_plan.md`
- `docs/acceptance.md`
- `docs/model_governance.md`
- `docs/agent_guidelines.md`

### Acceptance Criteria

Short-term phase is accepted only if:

- all core artifacts are schema-validated in CI,
- invalid `rule_type` values fail the pipeline,
- baseline smoke run is reproducible in CI,
- every maker/checker artifact records model and prompt metadata,
- checker instability can be surfaced on the baseline set,
- stable source anchors are preserved where applicable,
- roadmap and governance docs are present in the repo.

### Success Metric

The system becomes trustworthy enough for repeated internal development, even if it is not yet enterprise-ready.

---

## Mid-Term Plan (3–9 Months)

### Stage Goal

Upgrade from a stable design prototype into an AI-assisted test planning and BDD generation platform that can handle multiple document categories and produce reusable test design outputs.

### In Scope

- document-type aware ingestion,
- planning layer above maker/checker,
- richer traceability,
- improved review collaboration,
- normalized BDD contract,
- BDD style learning,
- export interfaces for downstream execution teams.

### Out of Scope

- full runtime execution of all generated scenarios,
- autonomous end-to-end execution against all systems,
- full enterprise RBAC and production multi-tenant platform.

### Key Deliverables

#### A. Multi-document ingestion framework

Support defined source classes, for example:

- rulebooks,
- product specs,
- API docs,
- business workflow docs,
- compliance / policy docs,
- release notes / change documents.

Each document class must define:

- parsing strategy,
- extraction constraints,
- expected rule patterns,
- known failure modes.

#### B. Test planning layer

Introduce a planner stage between `semantic_rule` and BDD generation.

New flow:

`semantic_rules -> planning -> test objectives -> scenario families -> BDD generation`

The planner should produce:

- priority,
- risk level,
- coverage intent,
- scenario family,
- dependency notes,
- recommended validation strategy.

#### C. Traceability model

Each final BDD scenario must trace back to:

- source document,
- source clause or section,
- stable source anchor where applicable,
- atomic rule,
- semantic rule,
- planning decision,
- checker verdict,
- human review outcome.

#### D. BDD contract layer

Define a normalized BDD representation independent of final output syntax.

This becomes the stable handoff artifact before step integration.

#### E. BDD style learning

Learn and version team BDD style conventions from existing assets so generated BDD aligns with reusable project practice.

#### F. Review collaboration v1

Add file-based or bundle-based review exchange:

- export review package,
- import review package,
- merge review decisions,
- conflict surfacing.

#### G. Quality dashboards

Enhance reports with:

- rule type coverage heatmap,
- unstable checker decisions,
- baseline drift versus previous runs,
- document class breakdown,
- traceability drill-down,
- JSON / CSV export.

### Acceptance Criteria

Mid-term phase is accepted only if:

- at least 3 document classes are supported with explicit parsing rules,
- planner outputs are versioned and schema-validated,
- generated BDD artifacts are normalized and traceable,
- review packages can be exported and merged,
- reports can show historical diffs and unstable judgments,
- model change regression is enforced before adoption.

### Success Metric

The system becomes usable for controlled team pilots in document-driven test planning and BDD generation.

---

## Long-Term Plan (9–18 Months)

### Stage Goal

Evolve the framework into an enterprise AI testing platform that connects document learning, planning, BDD generation, and execution integration with existing step definitions.

### In Scope

- step definition registry,
- step mapping and gap analysis,
- execution abstraction,
- deterministic assertion layer,
- hosted collaborative review service,
- enterprise governance and observability,
- controlled rollout across model providers.

### Out of Scope

- unrestricted autonomous test execution without approval gates,
- fully free-form agentic code generation without schema and review controls.

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

Move execution truth away from LLM judgment wherever possible.

Deterministic modules should own:

- field validation,
- state validation,
- calculation validation,
- deadline and window checks,
- event sequence verification,
- pass/fail accounting.

#### D. Hosted review and governance service

Upgrade review-session from local HTTP service to a deployable web service with:

- user accounts,
- reviewer roles,
- audit trail,
- conflict resolution,
- comment threads,
- assignment workflow.

#### E. Enterprise observability

Track:

- ingestion failure rate,
- extraction drift,
- duplicate / conflict rule rate,
- planner change rate,
- maker validity rate,
- checker instability rate,
- BDD reuse rate,
- step binding success rate,
- execution pass/fail distribution.

#### F. Release governance

Formalize:

- release tags,
- compatibility matrix,
- benchmark gates,
- migration notes,
- approved provider list.

### Acceptance Criteria

Long-term phase is accepted only if:

- normalized BDD can be bound to existing step definitions with measurable reuse,
- unmatched steps are surfaced automatically,
- execution-ready scenarios can be exported consistently,
- hosted review supports multi-user auditability,
- deterministic assertions exist for at least the core structured rule categories,
- provider rollout requires benchmark pass and rollback path,
- enterprise-level metrics are available for audit and platform operation.

### Success Metric

The system becomes enterprise-usable as an AI-assisted testing platform, not just a design prototype.

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

Short-term work must not add mid-term or long-term scope unless explicitly approved.

### 5. Every feature must ship with an acceptance test

No roadmap item is complete without a testable acceptance condition.

---

## Recommended Repo Document Structure

### `README.md`

Keep concise:

- what the project is,
- current workflow,
- current scope,
- quick start,
- links to roadmap and governance docs.

### `docs/roadmap.md`

Contains this phased upgrade plan.

### `docs/implementation_plan.md`

Contains execution-oriented task breakdowns with input/output contracts and validation expectations.

### `docs/architecture.md`

Defines:

- pipeline stages,
- artifact contracts,
- module boundaries,
- deterministic vs LLM-owned responsibilities.

### `docs/acceptance.md`

Lists phase-based acceptance criteria and benchmark gates.

### `docs/model_governance.md`

Defines:

- provider abstraction,
- model onboarding rules,
- prompt versioning,
- baseline regression,
- rollback policy.

### `docs/agent_guidelines.md`

Defines how AI coding agents are allowed to modify the repo.

### `docs/testing_governance.md`

Defines review, validation, confidence, failure analysis, and operational quality governance.

### `docs/prompt_lifecycle.md`

Defines governed prompt inventory, dependency, versioning, deprecation, and rollback rules.

### `docs/step_integration_plan.md`

Defines the bridge between normalized BDD artifacts and step-definition-aware execution integration.

---

## Repo Summary Paragraph

This project should evolve in three controlled stages. Short-term, it must stabilize the current document-to-rule-to-BDD design pipeline with schemas, CI, stable source-anchor traceability, and model governance. Mid-term, it should add document-aware planning, normalized BDD, style learning, traceability, and collaborative review so teams can pilot it safely. Long-term, it should integrate with existing step definitions, add execution-ready contracts and deterministic assertions, and grow into a governed enterprise AI testing platform. Because multiple LLM APIs may be used, every stage requires schema contracts, versioned prompts, benchmark gates, repo-readable execution context, and rollback-safe model governance.
