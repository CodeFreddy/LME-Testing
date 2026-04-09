# Rule Model and Parsing Design

## Purpose

This document explains the current upstream rule-model design in the repository:

- why the repo separates `atomic_rule` from `semantic_rule`
- what each layer is responsible for
- what fields belong to each artifact
- how deterministic extraction and first-pass semantic normalization should interact
- and how this model fits into the current governed roadmap

This is the primary implementation-side design document for extraction and rule modeling.

Read it together with:

- `docs/roadmap.md`
- `docs/implementation_plan.md`
- `docs/architecture.md`
- `docs/acceptance.md`
- `docs/rule_extraction_script_guide.md`

---

## Current Processing Path

For the current repo phase, the intended upstream path is:

`source document -> pages -> clauses -> atomic_rule -> semantic_rule`

These artifacts then support:

- validation
- review
- maker/checker inputs
- reporting
- and later planning / normalized BDD work

This document intentionally stops before normalized BDD, step integration, and execution-ready contracts.
Those belong to later phases and are governed elsewhere.

---

## Why the Repo Uses Two Rule Layers

The repo does not jump directly from source documents to test cases because that would make it harder to:

- keep the coverage denominator stable
- preserve traceability
- separate extraction errors from semantic interpretation errors
- review upstream quality before downstream generation
- and support multiple later consumers from the same governed source artifacts

The two-layer rule model exists to create a stable intermediate truth boundary:

- `atomic_rule` captures document-grounded rule units
- `semantic_rule` captures first-pass normalized interpretation of those units

---

## Layer 1: `atomic_rule`

`atomic_rule` is the smallest governed document-level rule unit used by this repo.

### Responsibilities

- provide a stable coverage denominator candidate
- preserve document-grounded traceability
- support human inspection of extraction quality
- serve as the direct source for `semantic_rule` generation

### Design principles

- prefer deterministic extraction over model interpretation
- stay conservative when splitting
- preserve recoverability to the source text
- allow coarse first-pass categorization, but avoid overclaiming semantic certainty

### What `atomic_rule` is not

`atomic_rule` is not:

- a full semantic interpretation
- a test case
- a normalized BDD artifact
- an execution-ready contract

---

## Layer 2: `semantic_rule`

`semantic_rule` is the first-pass normalized semantic artifact built from one or more `atomic_rule` records.

### Responsibilities

- normalize rule meaning into a governed structured form
- preserve source traceability and evidence
- support downstream maker/checker flows
- support later planning and normalized BDD stages
- carry review-relevant uncertainty signals such as ambiguity and inferred fields

### Design principles

- every `semantic_rule` must trace back to source `atomic_rule` records
- normalization is allowed, but inferred content must remain visible
- evidence is mandatory
- the artifact should be useful to later stages without pretending to be those later stages

### What `semantic_rule` is not

`semantic_rule` is not:

- the final business truth
- a direct substitute for planner outputs
- the canonical normalized BDD artifact
- a syntax-specific `.feature` rendering
- an execution-ready scenario contract

---

## Parsing Design

## Parsing layers

The upstream parsing stack currently uses four levels:

1. `document`
2. `section`
3. `clause`
4. `atomic_rule`

### Meaning of each layer

- `document` holds source-level metadata
- `section` captures the major heading context
- `clause` captures explicit numbered rule sections such as `46.`
- `atomic_rule` captures the smallest reviewable rule unit needed for governed downstream use

## Clause splitting

Clause boundaries should be determined by deterministic parsing logic, not by LLM judgment.

Why:

- clause boundaries must be reproducible
- the same source should yield the same clause structure across runs
- later coverage and traceability depend on stable upstream boundaries

## Atomic-rule splitting

One `atomic_rule` should express one reviewable normative proposition.

Typical cases that should split:

- multiple independent modal requirements in one clause such as `must`, `must not`, `may`, `shall`, `will`
- mixed obligation and prohibition content
- multiple independent timing requirements
- semantically independent subclauses such as `(a)(b)(c)`
- semantically independent roman-numeral lists such as `(i)(ii)(iii)`
- multiple distinct enum definitions in the same clause

Typical cases that should not split further:

- pure background context
- explanatory fragments that do not stand alone as rules
- examples that do not define a separate normative proposition

---

## `atomic_rule` Fields

The current extraction stage uses the following key `atomic_rule` fields.

### `rule_id`

Stable rule identifier.

Examples:

- `MR-046-01`
- `MR-052-A-1`

### `clause_id`

Stable parent clause identifier.

Example:

- `MR-046`

### `clause_number`

Original clause number from the source document.

### `section`

Parent section heading when available.

Example:

- `Give-Ups`

### `start_page` / `end_page`

Source page range for the extracted rule.

### `rule_type`

First-pass deterministic or heuristic category guess from the extraction layer.

Important:

- this is an initial classification hint
- it is not the final semantic judgment

### `testability`

First-pass extraction-layer judgment about whether the rule appears testable.

### `split_basis`

Explains how the rule was split from the clause.

Examples:

- `sentence`
- `subclause:A`
- `subclause:B`

### `raw_text`

The source text fragment for this rule.

This field is a critical basis for:

- evidence generation
- review
- semantic normalization
- and traceability

---

## `semantic_rule` Core Fields

The fields below are the core repo-readable structure for first-pass semantic normalization.

### `semantic_rule_id`

Primary key for the semantic artifact.

Recommended style:

- `SR-MR-046-03`
- `SR-MR-052-AB`

### `version`

Schema version for the semantic artifact.

Current first-pass examples commonly use:

- `1.0`

### `source`

Traceability payload that should at minimum preserve:

- `doc_id`
- `doc_title`
- `doc_version`
- `section`
- `clause_refs`
- `atomic_rule_ids`
- `pages`

This field exists to support:

- source traceability
- review
- coverage reasoning
- and downstream artifact linkage

### `classification`

Rule metadata and downstream coverage context.

Typical fields:

- `rule_type`
- `rule_tags`
- `testability`
- `priority`
- `coverage_eligible`

### `statement`

Normalized semantic statement of the rule.

Typical fields:

- `actor`
- `action`
- `object`
- `conditions`
- `constraints`
- `outcome`
- `exceptions`

Interpretation guideline:

- `conditions` describe when the rule applies
- `constraints` describe field/value restrictions
- `outcome` describes the expected effect or state

### `execution_mapping`

Bridging hints for later downstream design, not an execution contract.

Typical fields:

- `business_inputs`
- `observable_outputs`
- `system_events`
- `preconditions_for_execution`
- `postconditions_for_execution`
- `dsl_assertions`

Important:

- this field may help later planning or normalized BDD work
- it must not be treated as proof that execution integration is already governed
- it should remain subordinate to later canonical intermediate artifacts

### `evidence`

Source-backed evidence list.

Each evidence item should at minimum preserve:

- `target`
- `quote`
- `page`
- `atomic_rule_id`

### `review`

Review-oriented metadata such as:

- `confidence`
- `inference_flags`
- `ambiguities`

### `test_design_hints`

Optional first-pass hints that may help later test design.

Typical fields:

- `gherkin_intent`
- `positive_scenarios`
- `negative_scenarios`
- `boundary_scenarios`
- `data_requirements`
- `oracle_notes`

These are hints, not final planning outputs.

---

## Key Enums

### `rule_type`

Current governed values:

- `obligation`
- `prohibition`
- `permission`
- `deadline`
- `state_transition`
- `data_constraint`
- `enum_definition`
- `workflow`
- `calculation`
- `reference_only`

### `testability`

- `testable`
- `partially_testable`
- `ambiguous`
- `non_testable`

### `priority`

- `critical`
- `high`
- `medium`
- `low`

### `source_type`

- `explicit`
- `normalized`
- `inferred`

`source_type` is especially important because it distinguishes:

- direct source facts
- normalized restatements
- inferred content that must not be mistaken for explicit source truth

---

## Type-Specific Payloads

The current semantic model supports type-specific payloads under `type_payload`.

### `obligation`

Meaning:

- the document requires an actor to perform an action

Fields:

- `type_payload.obligation.mode`
- `type_payload.obligation.fulfillment`

### `prohibition`

Meaning:

- the document forbids a behavior

Fields:

- `type_payload.prohibition.mode`
- `type_payload.prohibition.scope`

### `permission`

Meaning:

- the document allows a behavior, but does not require it

Fields:

- `type_payload.permission.mode`
- `type_payload.permission.optional`

### `deadline`

Meaning:

- the document defines a timing constraint or deadline

Fields:

- `type_payload.deadline.deadline_kind`
- `type_payload.deadline.reference_event`
- `type_payload.deadline.offset_iso8601`
- `type_payload.deadline.absolute_time_local`
- `type_payload.deadline.timezone`
- `type_payload.deadline.business_day_offset`
- `type_payload.deadline.breach_outcome`

### `state_transition`

Meaning:

- the document describes a required or expected state change

Fields:

- `type_payload.state_transition.trigger_event`
- `type_payload.state_transition.from_state`
- `type_payload.state_transition.to_state`
- `type_payload.state_transition.automatic`

### `data_constraint`

Meaning:

- the document constrains field values, formats, or allowed ranges

Fields:

- `type_payload.data_constraint.field`
- `type_payload.data_constraint.constraint_kind`
- `type_payload.data_constraint.format`
- `type_payload.data_constraint.allowed_values`
- `type_payload.data_constraint.applies_when`

### `enum_definition`

Meaning:

- the document defines a governed code value or enumerated meaning

Fields:

- `type_payload.enum_definition.field`
- `type_payload.enum_definition.value`
- `type_payload.enum_definition.meaning`
- `type_payload.enum_definition.applies_to`

### `workflow`

Meaning:

- the document defines a multi-branch or multi-step process

Fields:

- `type_payload.workflow.trigger`
- `type_payload.workflow.branches`
- `branch_id`
- `branch_condition`
- `steps`

### `calculation`

Meaning:

- the document defines a formula, substitution, derivation, or arithmetic rule

Fields:

- `type_payload.calculation.calculation_kind`
- `type_payload.calculation.inputs`
- `type_payload.calculation.formula_description`
- `type_payload.calculation.rounding_rule`

### `reference_only`

Meaning:

- contextual or explanatory content retained for traceability, but not counted as coverage-eligible test scope

Fields:

- `type_payload.reference_only.reason`

This type should normally imply:

- `testability = non_testable`
- `coverage_eligible = false`

---

## Relationship to Later Test Design

`semantic_rule` should help later test design, but it must not collapse into later-phase artifacts.

### What later stages may use

Later stages may draw from:

- `statement`
- `execution_mapping`
- `test_design_hints`
- `evidence`

### What this document does not authorize

This document does not authorize:

- direct syntax-first Gherkin generation as the canonical contract
- skipping planner or normalized BDD artifacts when those phases are introduced
- treating `execution_mapping` as an execution-ready handoff

The correct downstream order remains:

- governed semantic artifacts first
- later planner and normalized BDD contracts next
- syntax-specific export after that
- execution bridge only in later phases

---

## Design Guidance

- Do not let the LLM decide document boundaries that should be deterministic.
- Do not remove or weaken `evidence`.
- Do not treat `source_type = inferred` as high-confidence source truth.
- Do not include `reference_only` in coverage-eligible rule denominators.
- Stabilize `atomic_rule` quality before expanding `semantic_rule` sophistication.
- Prefer upstream traceability and reviewability over aggressive semantic compression.

---

## Related Files

- [extract_matching_rules.py](../scripts/extract_matching_rules.py)
- [generate_semantic_rules.py](../scripts/generate_semantic_rules.py)
- [rule_extraction_script_guide.md](./rule_extraction_script_guide.md)
