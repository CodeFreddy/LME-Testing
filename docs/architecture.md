# Architecture

## Purpose

This document defines the current and target architecture of the repository.

Its goals are to:

- describe the end-to-end pipeline clearly,
- define artifact contracts and responsibilities,
- separate deterministic modules from LLM-assisted modules,
- establish stable module boundaries,
- and reduce architecture drift as the system evolves.

This document should be read together with:

- `docs/roadmap.md`
- `docs/acceptance.md`
- `docs/model_governance.md`
- `docs/agent_guidelines.md`

---

## 1. System Overview

This repository is a document-driven AI testing framework evolving in stages.

At its current core, the system transforms source documents into structured rule artifacts, then into test design outputs, and finally into human-reviewed reports.

### Current pipeline

`source docs -> extraction scripts -> atomic_rules.json -> semantic_rules.json -> maker -> checker -> review-session -> rewrite -> checker -> report`

### Long-term target pipeline

`source docs -> ingestion -> extraction -> validation -> semantic normalization -> planning -> normalized BDD -> review -> step mapping -> executable scenario -> execution integration -> report / analytics`

The architecture must support the transition from the current pipeline to the target pipeline without breaking artifact traceability or governance.

---

## 2. Architectural Principles

### 2.1 Contracts over conventions

Artifacts must be governed by explicit schemas and interfaces.  
No module should depend on loosely assumed structures.

### 2.2 Traceability is a first-class requirement

Every downstream artifact should be traceable back to its upstream source inputs.

### 2.3 Deterministic where possible, LLM-assisted where useful

LLMs should be used where interpretation, drafting, or semantic compression is valuable.

Deterministic logic should be used where correctness, validation, and repeatability are required.

### 2.4 Phase-safe evolution

Architecture changes must respect roadmap phase boundaries.  
Do not design mid-term and long-term components in ways that destabilize short-term deliverables.

### 2.5 Provider isolation

Model-provider-specific behavior must remain behind provider or strategy interfaces.

---

## 3. Major Pipeline Stages

This section defines the intended role of each stage.

### 3.1 Source Document Ingestion

**Responsibility**  
Accept source materials and prepare them for extraction.

**Input examples**
- rulebooks
- product specifications
- API documentation
- business workflow documents
- compliance and policy documents
- release notes

**Output**  
A normalized document representation suitable for extraction.

**Notes**  
In the short term, ingestion may remain lightweight and script-driven.  
In the mid-term, document-class-aware ingestion should be introduced.

### 3.2 Rule Extraction

**Responsibility**  
Extract raw candidate rules from source materials.

**Input**  
Normalized source document or document text.

**Output**  
`atomic_rules.json`

**Characteristics**  
This stage is one of the most failure-sensitive parts of the system.  
Errors here propagate into all downstream stages.

**Required controls**
- schema validation
- required field checks
- duplicate candidate detection
- rule type validation
- trace reference validation

### 3.3 Semantic Normalization

**Responsibility**  
Transform atomic rules into semantically richer rule objects that can support test design.

**Input**  
`atomic_rules.json`

**Output**  
`semantic_rules.json`

**Characteristics**  
This stage bridges source-oriented rules and test-oriented reasoning.

**Output expectations**  
Semantic rules should encode:
- normalized meaning,
- category / rule type,
- relevant constraints,
- traceability references,
- downstream design guidance,
- execution-oriented hints where appropriate.

### 3.4 Planning

**Responsibility**  
Convert semantic rules into prioritized and grouped test planning units.

**Input**  
`semantic_rules.json`

**Output**  
Planning artifacts such as:
- test objectives
- scenario families
- risk labels
- dependency notes
- recommended validation strategies

**Notes**  
This stage is mid-term roadmap scope.  
It should sit between semantic normalization and BDD generation.

### 3.5 BDD Generation

**Responsibility**  
Generate structured BDD scenarios from rule and planning artifacts.

**Current implementation pattern**  
This responsibility is currently approximated by the maker stage.

**Long-term expectation**  
BDD generation should target a normalized BDD contract rather than raw output formatting only.

**Output**  
Normalized BDD artifact, plus renderable BDD variants as needed.

### 3.6 Checker Review

**Responsibility**  
Assess generated scenarios for structural validity, coverage intent, and review findings.

**Input**  
Maker or BDD generation output plus semantic rule context.

**Output**  
Structured checker artifact with:
- accept / block style judgments,
- coverage-related findings,
- evidence or rationale,
- traceability references,
- stability metadata if supported.

**Important limitation**  
Checker logic may be LLM-assisted, but checker outputs must remain structured and governed.

### 3.7 Human Review

**Responsibility**  
Provide explicit human approval, rejection, or rewrite decisions.

**Current implementation pattern**  
Local review-session service.

**Long-term expectation**  
Hosted multi-user review and audit workflow.

**Output**  
Structured human review decision artifact.

### 3.8 Rewrite

**Responsibility**  
Regenerate selected outputs after human or checker-driven feedback.

**Input**  
Review decisions plus prior artifacts.

**Output**  
Revised design artifacts suitable for re-checking.

### 3.9 Reporting

**Responsibility**  
Expose pipeline results in forms suitable for evaluation and governance.

**Output examples**
- HTML reports
- heatmaps
- JSON exports
- CSV exports
- drift summaries
- traceability views

### 3.10 Step Definition Mapping

**Responsibility**  
Map normalized BDD steps onto existing step definitions.

**Notes**  
This is long-term roadmap scope.

**Output**  
Binding artifact including:
- matched steps
- parameter bindings
- candidate suggestions
- unmatched step list
- reuse signals

### 3.11 Execution Integration

**Responsibility**  
Prepare and hand off execution-ready scenarios to downstream automation layers.

**Notes**  
This architecture does not assume immediate in-repo full execution ownership.

**Output**  
`ExecutableScenario` or equivalent execution-ready artifact.

---

## 4. Artifact Contracts

This section defines the conceptual artifact model.

### 4.1 Source Document Artifact

Represents an ingested source document or normalized source content.

Expected properties:
- source identifier
- document type
- version or timestamp if known
- section references
- normalized text representation

### 4.2 Atomic Rule Artifact

Represents the smallest source-grounded rule unit extracted from documents.

Expected properties:
- stable rule identifier
- source trace reference
- raw or lightly normalized statement
- rule type candidate
- section or clause reference
- extraction metadata

**Architectural role**  
Source-grounded unit for validation and traceability.

### 4.3 Semantic Rule Artifact

Represents a semantically normalized rule suitable for test design reasoning.

Expected properties:
- stable semantic rule identifier
- trace back to atomic rule(s)
- normalized statement
- canonical rule type
- constraints
- semantic qualifiers
- planning hints
- execution-oriented hints where needed

**Architectural role**  
Bridge between document semantics and test design logic.

### 4.4 Planning Artifact

Represents the planning interpretation of semantic rules.

Expected properties:
- planning identifier
- linked semantic rule(s)
- priority
- risk
- coverage intent
- scenario family
- dependency notes
- recommended validation mode

**Architectural role**  
Transforms rule semantics into test planning decisions.

### 4.5 BDD Artifact

Represents normalized BDD scenario structures.

Expected properties:
- scenario identifier
- linked planning item
- linked semantic rule(s)
- scenario title
- preconditions
- actions
- expected outcomes
- traceability references
- rendering metadata if needed

**Architectural role**  
Stable design handoff before step mapping or execution integration.

### 4.6 Checker Artifact

Represents checker findings for generated scenarios.

Expected properties:
- checker run metadata
- linked scenario identifier
- linked semantic rule identifier
- decision or judgment
- coverage finding
- finding evidence
- stability or comparison metadata when available

**Architectural role**  
Governed evaluation output, not free-form narrative.

### 4.7 Human Review Artifact

Represents human decisions on review units.

Expected properties:
- reviewer or review source
- target object identifier
- decision
- comments
- rewrite request details
- timestamp
- merge provenance if collaboration is supported

### 4.8 Step Binding Artifact

Represents the mapping between normalized BDD steps and existing step definitions.

Expected properties:
- scenario identifier
- step identifier
- matched step definition
- binding confidence or mode
- parameter mapping
- unmatched status if applicable

### 4.9 Executable Scenario Artifact

Represents a scenario that is ready to be executed or handed off to an execution layer.

Expected properties:
- executable scenario identifier
- linked normalized BDD scenario
- environment requirements
- input data requirements
- setup hooks
- linked step definitions
- deterministic assertion references
- cleanup hooks

---

## 5. Module Boundaries

This section defines stable architectural boundaries.

### 5.1 Ingestion Module

**Owns**
- document loading
- document-type classification if implemented
- normalized document representation

**Must not own**
- semantic interpretation
- BDD generation
- execution logic

### 5.2 Extraction Module

**Owns**
- source rule extraction
- extraction metadata
- raw rule structuring

**Must not own**
- downstream coverage logic
- final BDD output formatting
- execution mapping decisions beyond extraction hints

### 5.3 Validation Module

**Owns**
- schema validation
- enum validation
- duplicate candidate detection
- trace reference validation
- contract checks

**Must not own**
- semantic rewriting
- planner creativity
- provider-specific inference behavior

### 5.4 Semantic Normalization Module

**Owns**
- rule meaning normalization
- semantic categorization
- downstream design hints
- trace-preserving transformation

**Must not own**
- final report rendering
- execution orchestration
- provider plumbing

### 5.5 Planning Module

**Owns**
- risk and priority framing
- scenario family definition
- coverage intent shaping
- dependency annotation

**Must not own**
- final step binding
- provider adapters
- execution result validation

### 5.6 BDD Generation Module

**Owns**
- normalized scenario generation
- BDD contract population
- test-design-level structure

**Must not own**
- execution platform specifics
- step implementation code
- final pass/fail truth

### 5.7 Checker Module

**Owns**
- structured review findings
- coverage-related structured judgments
- scenario validity signals
- output suitable for reports and human review

**Must not own**
- schema definition
- source extraction
- execution truth for deterministic checks

### 5.8 Human Review Module

**Owns**
- review workflow
- human decisions
- review package exchange or merge
- audit trail in long-term scope

**Must not own**
- model selection
- artifact generation rules
- silent artifact mutation

### 5.9 Reporting Module

**Owns**
- presentation and export
- trend and drift views
- traceability visualization
- decision summaries

**Must not own**
- rule extraction
- semantic inference
- step definition matching logic

### 5.10 Provider / Model Strategy Module

**Owns**
- provider abstraction
- model configuration
- prompt resolution
- retry strategy
- output mode configuration

**Must not own**
- business decision logic
- schema interpretation rules
- roadmap scope decisions

### 5.11 Step Mapping Module

**Owns**
- matching BDD steps to existing step definitions
- candidate suggestion
- unmatched reporting
- reuse scoring

**Must not own**
- document extraction
- semantic rule normalization
- full execution runtime ownership unless explicitly extended

---

## 6. Deterministic vs LLM-Assisted Responsibility Split

This split is critical to the architecture.

### 6.1 Deterministic responsibilities

These should be implemented without relying on model judgment wherever practical:

- schema validation
- required field validation
- enum validation
- traceability linkage checks
- duplicate candidate thresholding
- artifact metadata enforcement
- benchmark result accounting
- report export correctness
- step match exactness when exact mapping is available
- execution-time assertions for structured checks

### 6.2 LLM-assisted responsibilities

These may use LLMs because semantic compression or drafting value is high:

- rule normalization
- ambiguity handling
- scenario drafting
- planning suggestions
- checker reasoning draft generation
- candidate step suggestions where exact mapping is not available

### 6.3 Mixed responsibilities

Some modules may combine deterministic guardrails with LLM assistance:

- semantic normalization with schema-constrained outputs
- maker with required case type constraints
- checker with structured output validation
- step suggestion with deterministic exact match first and LLM-assisted fallback second

---

## 7. Traceability Requirements

Traceability must be preserved across the pipeline.

At minimum, downstream artifacts should support tracing back through:

- source document
- source section or clause
- atomic rule
- semantic rule
- planning artifact if present
- BDD artifact
- checker artifact
- human review artifact
- step binding artifact where applicable
- executable scenario where applicable

Traceability should be machine-readable and reportable.

---

## 8. Error Handling and Failure Visibility

The architecture must prefer visible failure over silent corruption.

### Required behaviors
- invalid structured artifacts fail validation,
- malformed outputs are not silently accepted,
- recovery logic is bounded and observable,
- retries are tracked,
- provider-specific failures are isolated and visible,
- report generation failures are surfaced.

### Non-goals
- hiding invalid outputs just to keep the pipeline green,
- converting major contract failures into warnings without policy support.

---

## 9. Evolution Strategy

Architecture should evolve incrementally.

### Short-term emphasis
- stabilize extraction and validation,
- govern maker and checker outputs,
- strengthen CI and metadata.

### Mid-term emphasis
- add planning,
- add multi-document support,
- normalize BDD,
- add collaborative review and richer dashboards.

### Long-term emphasis
- integrate step definitions,
- introduce executable scenario contracts,
- add deterministic execution assertions,
- support hosted review and enterprise observability.

---

## 10. Suggested Repository Structure

A recommended repo-aligned structure may look like:

- `docs/`
- `schemas/`
- `prompts/`
- `benchmarks/`
- `configs/models/`
- `artifacts/`
- `src/ingestion/`
- `src/extraction/`
- `src/validation/`
- `src/semantic/`
- `src/planning/`
- `src/bdd/`
- `src/checker/`
- `src/review/`
- `src/reporting/`
- `src/providers/`
- `src/step_mapping/`
- `src/execution/`

The exact implementation layout may differ, but module ownership should remain clear.

---

## 11. Architectural Review Questions

Before approving a design change, reviewers should ask:

- Which pipeline stage is being changed?
- Which artifact contracts are affected?
- Does the change preserve traceability?
- Is the logic deterministic where it should be?
- Is LLM use properly governed?
- Does the change cross roadmap phase boundaries?
- Are provider-specific behaviors isolated?
- Are acceptance criteria and docs updated?

If these questions cannot be answered clearly, the architectural change is not ready.

---

## 12. Summary

This architecture is designed to support a controlled evolution from a document-driven test design prototype to an enterprise AI testing platform.

The central architectural commitments are:

- explicit artifact contracts,
- strong traceability,
- deterministic validation where correctness matters,
- LLM assistance where semantic value is high,
- provider isolation,
- and phase-safe evolution.

These boundaries exist to make the system scalable, governable, and resilient as multiple model APIs and more advanced testing capabilities are introduced.
