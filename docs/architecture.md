# Architecture

## Purpose

This document defines the architecture of the repository at the system level.

It serves four goals:

1. describe the current pipeline clearly,
2. define artifact contracts and module boundaries,
3. separate deterministic responsibilities from LLM-assisted responsibilities,
4. guide future evolution without allowing implicit architecture drift.

This document should be read together with:

- `docs/roadmap.md`
- `docs/implementation_plan.md`
- `docs/acceptance.md`
- `docs/model_governance.md`
- `docs/agent_guidelines.md`
- `docs/testing_governance.md`

---

## Architectural Summary

The repository is currently a **document-driven test design system**.

Its current architecture is centered on a structured transformation pipeline:

`source documents -> extraction -> atomic rules -> semantic rules -> maker -> checker -> human review -> rewrite -> report`

This architecture is optimized for:
- rule extraction,
- test scenario generation,
- coverage analysis,
- human review,
- structured reporting.

It is **not yet** a full execution platform.

Execution integration, step definition mapping, deterministic runtime assertions, and heavy hosted collaboration are future architectural layers, not current core layers.

---

## Current System Boundary

### What the system currently is

The current system is a pipeline that transforms source documents into structured test design artifacts and reviewable outputs.

### What the system currently is not

The current system is not yet:

- a general-purpose test execution framework,
- a runtime orchestration system,
- a multi-user enterprise review platform,
- a step-definition-aware BDD execution engine.

This distinction matters because architecture decisions should be aligned with the actual system stage, not an assumed end-state.

---

## Architectural Principles

### 1. Artifacts are first-class contracts

The system is built around governed artifacts, not around ad hoc prompt outputs.

Artifacts must be:
- structured,
- versionable,
- traceable,
- schema-validatable,
- reviewable.

### 2. Upstream correctness matters more than downstream cleverness

If upstream rule extraction is invalid, downstream maker/checker quality becomes unreliable.

### 3. LLMs assist judgment and generation, but contracts remain deterministic

LLM-assisted stages may propose or interpret, but the overall architecture must remain controlled by:
- schemas,
- deterministic validation,
- explicit pipeline stages,
- benchmark gates,
- and acceptance rules.

No new LLM-driven stage should become part of the governed baseline unless its outputs are contract-defined, reviewable, and traceable.

### 4. Module boundaries must remain explicit

Business logic, provider logic, schema logic, review logic, and reporting logic should not be mixed casually.

### 5. Traceability is part of the architecture

The architecture must preserve the ability to trace downstream artifacts back to upstream sources.

### 6. Durable execution context must be repo-readable

If behavior is expected to be repeatable across humans, models, providers, or sessions, its governing inputs must live in repo-readable assets such as:
- schemas,
- prompts,
- configs,
- benchmark data,
- acceptance rules,
- implementation tasks.

Durable system behavior must not depend only on transient conversation context.

### 7. New LLM-driven stages require contract-first introduction

Future planner, normalized BDD, or similar stages must not be introduced as free-form pipeline expansions.

Before a new LLM-assisted stage becomes part of the governed baseline, the architecture should define:
- the artifact contract,
- validation rules,
- traceability expectations,
- reviewability requirements,
- failure behavior.

This is especially important for planner outputs and normalized BDD artifacts.

---

## High-Level Pipeline

## Current pipeline

The current architecture can be represented as:

1. **Source documents**
2. **Extraction**
3. **Atomic rule normalization**
4. **Semantic rule normalization**
5. **Scenario generation (maker)**
6. **Scenario assessment (checker)**
7. **Human review**
8. **Rewrite**
9. **Reporting**

### Stage overview

#### 1. Source documents
Input source materials such as:
- specifications,
- rulebooks,
- product behavior docs,
- API docs,
- policy / compliance docs,
- or other structured business documents.

#### 2. Extraction
Transforms source material into intermediate structured rule candidates.

#### 3. Atomic rule normalization
Represents document-level rule statements in a granular, source-grounded form.

#### 4. Semantic rule normalization
Transforms atomic rules into semantically richer structures used by downstream generation and coverage logic.

#### 5. Scenario generation (maker)
Generates structured BDD-style or scenario-style test design artifacts from semantic rules.

#### 6. Scenario assessment (checker)
Evaluates generated scenarios for quality and coverage against semantic rules.

#### 7. Human review
Allows human reviewers to approve, reject, or request rewrite for generated results.

#### 8. Rewrite
Regenerates targeted outputs after human review decisions.

#### 9. Reporting
Produces human-readable and machine-usable outputs summarizing the pipeline results.

---

## Target Future Pipeline

The longer-term target architecture extends the current pipeline rather than replacing it.

Target future pipeline:

`source documents -> extraction -> atomic rules -> semantic rules -> planning -> normalized BDD -> step mapping -> executable scenario contract -> execution integration -> deterministic oracle -> report and analytics`

This target architecture adds:
- planning layer,
- normalized BDD contract,
- BDD style-learning support,
- step definition registry and mapping,
- execution-ready handoff,
- deterministic runtime validation,
- selective governance signals.

These are future extensions, not current assumptions.

The ordering is intentional:
- planning should follow governed semantic rules,
- normalized BDD should exist before syntax-specific outputs become the canonical handoff,
- execution integration should follow normalized BDD and step mapping,
- deterministic oracle layers should be introduced where business value justifies them.

---

## Artifact Model

Artifacts are the backbone of this architecture.

## Artifact categories

### 1. Source-level artifacts
Represent original or parsed content from documents.

Examples:
- raw source file metadata,
- parsed sections,
- clauses,
- extraction traces,
- stable source anchors such as paragraph-level identity where applicable.

### 2. Rule-level artifacts
Represent normalized rule structures.

Examples:
- `atomic_rule`
- `semantic_rule`

### 3. Generation artifacts
Represent outputs produced from rules.

Examples:
- maker outputs,
- checker outputs,
- rewrite outputs,
- planner outputs in future phases,
- normalized BDD outputs in future phases,
- syntax-specific BDD renderings such as `.feature` exports in future phases.

### 4. Review artifacts
Represent human review state and decisions.

Examples:
- review draft,
- review decision records,
- conflict markers in future collaboration flows.

### 5. Reporting artifacts
Represent summarized results for humans or external systems.

Examples:
- HTML reports,
- JSON exports,
- CSV exports,
- quality summaries,
- benchmark summaries,
- audit-style run summaries.

---

## Core Artifact Contracts

## 1. Atomic Rule

### Role
The atomic rule is the source-grounded normalized unit extracted from document content.

### Architectural responsibility
It preserves:
- source intent at low semantic abstraction,
- traceability back to source sections or clauses,
- stable source anchors where available,
- input granularity for downstream semantic normalization.

### Must remain
- source-linked,
- schema-governed,
- minimally opinionated,
- reviewable.

### Must not become
- overloaded with downstream generation assumptions,
- a substitute for semantic planning,
- free-form text blobs without structure.

---

## 2. Semantic Rule

### Role
The semantic rule is the normalized rule object used for downstream coverage logic and scenario generation.

### Architectural responsibility
It bridges:
- source-grounded rule meaning,
- downstream scenario generation,
- rule-type-aware coverage expectations.

### Must remain
- schema-governed,
- traceable to atomic rules,
- traceable to stable source anchors where applicable,
- semantically clear,
- fit for maker/checker consumption.

### May contain
- rule type,
- execution-oriented hints,
- observables,
- constraints,
- scenario-relevant metadata.

### Must not be treated as
- a directly executable test script,
- a substitute for a future execution contract.

---

## 3. Maker Output

### Role
Represents generated test scenarios or BDD-style design outputs from semantic rules.

### Architectural responsibility
It is a design artifact, not runtime truth.

### Must remain
- structured,
- schema-validatable,
- traceable to semantic rules,
- traceable to stable source anchors when available,
- reviewable by checker and humans.

### Must not be treated as
- execution proof,
- final oracle,
- provider-specific raw output.

---

## 4. Checker Output

### Role
Represents assessment of maker outputs for quality and coverage.

### Architectural responsibility
It acts as a governed evaluation artifact for design-stage quality.

### Must remain
- structured,
- schema-validatable,
- explainable at artifact level,
- traceable to governed source anchors when applicable,
- distinguishable from deterministic runtime assertions.

### Must not be treated as
- infallible truth,
- a substitute for future deterministic execution oracle,
- purely free-form narrative.

---

## 5. Human Review Artifact

### Role
Represents human decisions over generated results.

### Architectural responsibility
It is the controlled human override and governance layer for the design loop.

### Must remain
- structured where possible,
- decision-oriented,
- traceable to reviewed artifacts,
- auditable.

---

## 6. Normalized BDD Artifact (future)

### Role
Represents a stable BDD contract independent of final rendering or execution bindings.

### Architectural responsibility
It becomes the handoff artifact between test design and execution integration.

### Must remain
- execution-agnostic,
- traceable,
- schema-validatable,
- reusable across output formats.

### Must be introduced only when
- its contract is defined explicitly,
- at least one validator exists,
- at least one renderer or downstream consumer exists,
- raw syntax output is no longer the only governed representation.

### Must not become
- a vague synonym for rendered Gherkin text,
- an unvalidated middle layer between planner and execution work.

---

## 7. Executable Scenario Artifact (future)

### Role
Represents execution-ready scenarios enriched with environment, setup, data, assertions, and step bindings.

### Architectural responsibility
It bridges design artifacts to runtime integration.

### Must remain
- explicit,
- deterministic where possible,
- test-environment aware,
- independent from undocumented model behavior.

### Must not become
- a bucket for unresolved design ambiguity,
- a substitute for step mapping evidence,
- a substitute for deterministic oracle ownership.

---

## Module Boundary Model

The repo should maintain explicit boundaries between modules.

## 1. Ingestion / extraction modules
Own:
- document reading,
- parsing,
- extraction support,
- source segmentation,
- stable source-anchor generation where applicable,
- extraction trace metadata.

Do not own:
- downstream scenario generation policy,
- provider-specific model logic,
- report rendering.

## 2. Rule normalization modules
Own:
- atomic rule shaping,
- semantic rule shaping,
- trace linkage,
- schema alignment,
- rule-type interpretation.

Do not own:
- review UI,
- reporting,
- provider transport details.

## 3. Generation modules
Own:
- maker,
- rewrite,
- future planner,
- future normalized BDD generation,
- future BDD style-learning outputs,
- future syntax-specific exporters built on normalized BDD.

Do not own:
- provider adapter internals,
- schema registry policy,
- long-term analytics logic,
- canonical execution truth.

## 4. Evaluation modules
Own:
- checker,
- future benchmark evaluation,
- future stability comparison.

Do not own:
- human decision workflow,
- runtime execution pass/fail truth,
- provider transport.

## 5. Review modules
Own:
- review state,
- decision storage,
- human workflow control.

Do not own:
- rule extraction,
- provider logic,
- deterministic execution assertions.

## 6. Reporting modules
Own:
- human-readable output,
- machine-readable summaries,
- metrics aggregation,
- traceability views,
- audit-style run summaries.

Do not own:
- business rules for generation,
- provider selection,
- schema migration policy.

## 7. Provider / model strategy modules
Own:
- provider-specific API interaction,
- retry handling,
- structured output mode,
- metadata capture,
- model selection abstraction.

Do not own:
- scenario generation business logic,
- report rendering,
- review workflows.

## 8. Schema and contract modules
Own:
- artifact structure definitions,
- schema validation,
- contract evolution policy support.

Do not own:
- provider invocation,
- document parsing,
- UI workflows.

---

## Deterministic vs LLM-Assisted Responsibilities

This is one of the most important architectural boundaries in the repo.

## LLM-assisted responsibilities

LLMs may assist with:
- extraction support where explicitly permitted,
- semantic normalization support,
- ambiguity detection,
- maker generation,
- checker evaluation,
- rewrite suggestions,
- future planning suggestions,
- future BDD style-pattern suggestion,
- future step candidate suggestions.

These stages are useful because they involve interpretation, synthesis, or language-rich generation.

## Deterministic responsibilities

Deterministic modules must own:
- schema validation,
- enum validation,
- stable source-anchor integrity checks,
- traceability checks,
- duplicate candidate logic thresholds,
- contract enforcement,
- artifact metadata enforcement,
- benchmark pass/fail accounting,
- CI gates,
- report assembly rules,
- audit/run-record generation rules,
- future execution assertions wherever feasible.

## Architectural rule

If a responsibility can be made deterministic without losing essential value, it should not remain purely LLM-governed.

---

## Traceability Model

Traceability should exist across the pipeline.

## Stable source-anchor strategy

Where source segmentation permits it, the architecture should introduce a stable source anchor such as `paragraph_id` or equivalent.

This anchor should:
- be unique within governed source scope,
- survive downstream transformations,
- appear in rule artifacts where applicable,
- remain available to maker/checker/reporting layers,
- and extend into future BDD and step-integration layers.

The exact field name may evolve, but the architectural requirement should remain stable.

## Minimum traceability path

`source document -> source section / clause -> stable source anchor (if applicable) -> atomic rule -> semantic rule -> maker output -> checker output -> human review -> report`

## Future traceability path

`... -> planning decision -> normalized BDD -> style profile reference -> step mapping -> executable scenario -> execution result`

Traceability must support:
- auditability,
- debugging,
- coverage reasoning,
- regression analysis,
- human review confidence.

---

## Validation Architecture

Validation should not be a single step; it should exist across layers.

## Validation layers

### 1. Source ingestion validation
Checks:
- source readability,
- format compatibility,
- section extraction sanity,
- stable source-anchor uniqueness where applicable.

### 2. Rule artifact validation
Checks:
- schema validity,
- enum validity,
- required field presence,
- trace references,
- duplicate candidate detection.

### 3. Generation artifact validation
Checks:
- structured output validity,
- semantic rule references,
- stable source-anchor propagation where applicable,
- expected field completeness,
- metadata presence.

For future planner and normalized BDD stages, generation validation should also check:
- stage-specific contract conformance,
- traceability continuity,
- reviewability of outputs,
- renderer or downstream-consumer compatibility where relevant.

### 4. Review validation
Checks:
- decision format,
- reviewed target identity,
- allowed action values,
- merge integrity in future collaboration flows.

### 5. Reporting validation
Checks:
- artifact completeness,
- traceability availability,
- metrics consistency,
- export validity,
- governance/audit summary completeness where applicable.

Validation failures should remain visible.  
The architecture should not silently absorb broken contracts.

---

## Benchmark Architecture

Benchmarks are part of architecture, not an optional add-on.

## Benchmark roles

Benchmarks should validate:
- extraction sanity,
- semantic normalization quality,
- maker structural validity,
- checker consistency,
- report generation,
- end-to-end smoke behavior.

Future benchmark roles should include:
- planning quality,
- normalized BDD quality,
- BDD style-learning consistency,
- step binding quality,
- execution contract readiness.

## Benchmark ownership

Benchmarks belong to governed system quality, not to individual providers.

This means benchmarks should be reusable even when the underlying model changes.

---

## Configuration Architecture

Configuration should remain layered and explicit.

## Configuration layers

### 1. Pipeline configuration
Defines:
- stage enablement,
- artifact paths,
- validation behavior,
- environment mode.

### 2. Model strategy configuration
Defines:
- provider,
- model,
- prompt version,
- retries,
- structured output settings.

### 3. Benchmark configuration
Defines:
- datasets,
- thresholds,
- comparison policy.

### 4. Reporting configuration
Defines:
- output formats,
- summaries,
- export behavior,
- governance/audit summary behavior where relevant.

Configuration should not be scattered across undocumented inline constants.

---

## Minimum Governance Artifacts

In addition to business artifacts, the architecture should support a minimal set of governance artifacts.

Examples include:
- benchmark outputs,
- drift comparison outputs,
- checker instability summaries,
- run summaries,
- change-impact notes,
- audit-style execution records.

The architecture does not require a full enterprise observability stack before those artifacts are justified by actual platform usage.

The exact directory structure may evolve, but the architecture assumes these artifacts are repo-readable and reviewable.

---

## Failure Model

The architecture should assume failure will occur.

## Failure classes

### 1. Source failure
Examples:
- unreadable document,
- malformed source,
- unsupported format.

### 2. Contract failure
Examples:
- invalid schema,
- invalid enum,
- broken trace reference,
- broken source-anchor propagation.

### 3. Model failure
Examples:
- timeout,
- malformed structured output,
- unstable output,
- incomplete result.

### 4. Review failure
Examples:
- incomplete review state,
- conflicting review state in any future collaboration flow.

### 5. Reporting failure
Examples:
- missing required artifacts,
- broken summary generation,
- export failure.

## Architectural rule for failures

Failures should be:
- visible,
- classifiable,
- attributable to a stage,
- recoverable where appropriate,
- never hidden as if they were successful outputs.

---

## Evolution Rules

The architecture may evolve, but evolution must be governed.

## Allowed architectural evolution

The repo may evolve by:
- adding new artifact versions,
- adding new validation layers,
- introducing planning artifacts,
- introducing normalized BDD,
- introducing BDD style-learning assets,
- introducing step registry and mapping,
- introducing execution contracts,
- improving collaboration where justified,
- improving selective governance signals and observability where justified.

## Disallowed architectural drift

The repo should not drift into:
- undocumented provider coupling,
- free-form artifact formats,
- unclear module ownership,
- silent contract weakening,
- later-phase features hidden inside early-phase work,
- syntax-first BDD pipelines that skip normalized governed artifacts once the normalized layer is introduced,
- heavy hosted collaboration assumptions becoming implicit architecture before the repo actually needs them.

---

## Recommended Directory Responsibilities

This section is intentionally abstract so it remains valid even if the exact repo layout evolves.

### `docs/`
Owns:
- architecture,
- roadmap,
- governance,
- acceptance rules,
- agent rules.

### `schemas/` or equivalent
Owns:
- artifact schemas,
- schema fixtures,
- schema evolution helpers.

### `prompts/` or equivalent
Owns:
- governed prompts,
- prompt metadata,
- versioned prompt assets.

### `benchmarks/` or equivalent
Owns:
- benchmark datasets,
- comparison logic,
- benchmark configs,
- evaluation summaries.

### `artifacts/` or equivalent
Owns:
- generated sample outputs,
- benchmark outputs,
- reproducible reference flows,
- governance/audit outputs.

### `src/` or equivalent code directories
Own:
- pipeline logic,
- providers,
- validators,
- reporting,
- review flows,
- generation logic.

---

## Architectural Review Questions

Use these questions before approving major changes:

- Does this change preserve artifact contracts?
- Does it improve or weaken traceability?
- Does it preserve stable source-anchor propagation where applicable?
- Does it keep provider logic isolated?
- Does it blur module boundaries?
- Does it move deterministic responsibilities into LLM-only logic?
- Does it introduce a new LLM-driven stage without a defined contract?
- Does it treat syntax output as canonical where a normalized artifact should own the contract?
- Does it silently introduce later-phase capabilities?
- Does it preserve rollback clarity?
- Does it align with the current roadmap phase?

If these questions cannot be answered clearly, the architecture impact is not yet review-ready.

---

## Summary

The architecture of this repository is centered on governed transformation of documents into structured test design artifacts.

The system should continue evolving through:
- explicit artifacts,
- clear module boundaries,
- deterministic validation,
- stable source-anchor traceability,
- repo-readable durable context,
- LLM-assisted generation where appropriate,
- strong traceability,
- and phased expansion toward planning, BDD normalization, step integration, and execution readiness.

Architecture clarity is essential because this repo may use multiple LLM APIs over time.  
Without stable boundaries and contracts, model flexibility would become system instability.
