# Acceptance Criteria and Release Gates

## Purpose

This document defines the acceptance criteria, release gates, and evidence requirements for each roadmap phase.

It is intended to be used by:

- developers implementing roadmap items,
- reviewers validating readiness,
- AI coding agents making changes under roadmap constraints.

This document should be read together with:

- `docs/roadmap.md`
- `docs/architecture.md`
- `docs/model_governance.md`
- `docs/agent_guidelines.md`

---

## General Acceptance Rules

These rules apply to all phases.

### 1. No acceptance without evidence
A phase item is not complete unless there is clear evidence of completion.

Accepted evidence types include:

- passing CI jobs,
- schema validation results,
- benchmark output,
- generated artifacts,
- screenshots or exported reports,
- test logs,
- change notes in the repo.

### 2. No artifact contract change without coordinated updates
Any change to an artifact format requires all of the following:

- schema update,
- migration note,
- test update,
- documentation update,
- acceptance checklist update if the change affects phase gates.

### 3. No model change without regression check
A new model API, model version, or prompt version must not be adopted unless benchmark and stability checks have passed.

### 4. No phase crossover without approval
Work from a later phase must not be merged into an earlier phase unless explicitly approved and documented.

### 5. Structured outputs remain structured
Any module that currently emits structured JSON must continue to emit structured JSON unless the contract is intentionally revised.

### 6. Phase gate sign-off is required for cross-phase execution
If work from a later phase is requested, the relevant earlier phase gate must already be signed off, or the missing sign-off must be explicitly flagged.

Examples:
- Phase 2 work should not be treated as normal implementation if the equivalent Phase 1 gate has not been completed.
- Phase 3 work should not be treated as normal implementation if the required earlier phase gates are missing.

Where a repo uses explicit gate files or equivalent gate records, those records should be checked before cross-phase implementation is considered complete.

---

## Evidence Template

Each completed roadmap item should provide evidence in this form:

- **Change summary**
- **Files changed**
- **Acceptance items addressed**
- **Tests run**
- **Artifacts generated**
- **Known limitations**
- **Rollback impact**

---

# Phase 1 Acceptance: Short-Term Stabilization (0–3 Months)

## Phase Goal

Stabilize the current document-to-rule-to-BDD design pipeline so that different model APIs can be used without silently degrading artifact quality.

## Phase Gate

Phase 1 is complete only if all required acceptance sections below pass.

---

## 1. Artifact Schema Gate

### Required
Versioned schemas must exist for:

- `atomic_rule`
- `semantic_rule`
- maker output
- checker output
- human review output

### Acceptance Criteria
- each schema is stored in the repo,
- schema version is declared,
- example artifacts validate successfully,
- invalid sample artifacts fail validation.

### Evidence
- schema files committed,
- validation test output,
- example valid and invalid fixtures.

---

## 2. Rule Validation Pipeline Gate

### Required
A formal validation stage must exist between extraction and downstream generation.

Expected flow:

`docs -> extraction scripts -> atomic_rules.json -> schema validation -> duplicate candidate detection -> rule_type enum validation -> semantic_rules.json`

### Acceptance Criteria
- invalid `atomic_rule` artifacts fail the pipeline,
- invalid `rule_type` values fail the pipeline,
- duplicate candidate detection produces a machine-readable result,
- invalid trace references are surfaced as validation findings,
- the validation stage can produce a structured validation report,
- the report includes total rules, valid count, invalid count, and per-rule error details,
- validation failure prevents downstream maker execution.

### Evidence
- pipeline implementation,
- test fixtures that intentionally fail,
- CI logs showing enforcement,
- sample structured validation report.

---

## 3. Model and Prompt Metadata Gate

### Required
All maker and checker artifacts must record metadata about how they were generated.

### Acceptance Criteria
Each generated artifact must include:
- provider,
- model identifier,
- prompt version,
- run timestamp,
- source artifact hash,
- pipeline version.

### Evidence
- generated sample artifacts,
- schema support for metadata,
- tests confirming metadata presence.

---

## 4. Baseline CI Gate

### Required
A baseline CI workflow must run automatically.

### Acceptance Criteria
CI must run at least:
- end-to-end smoke on a minimal baseline dataset,
- schema validation tests,
- reporting smoke test,
- core unit tests for pipeline bootstrapping,
- an end-to-end smoke path that can run without real LLM API calls by using a deterministic stub provider or equivalent governed test double.

### Evidence
- CI workflow files,
- CI run logs,
- pass/fail status on example PRs or commits.

---

## 5. Checker Stability Gate

### Required
Checker output instability must be detectable on a baseline set.

### Acceptance Criteria
- the same baseline input can be evaluated twice,
- differences are captured in a machine-readable way,
- unstable findings are surfaced in output or logs,
- the process is documented.

### Evidence
- benchmark or comparison script,
- sample diff output,
- documentation of interpretation rules.

---

## 6. Stable Source Anchor Gate

### Required
The pipeline must support a stable source-level traceability anchor for downstream artifacts.

### Acceptance Criteria
- the rule layer supports a stable source anchor such as a paragraph-level identifier or equivalent governed source key,
- uniqueness within the governed scope is checked,
- downstream artifacts can retain this anchor,
- reports or machine-readable exports can surface the anchor.

### Evidence
- artifact samples with source anchor fields,
- uniqueness validation output,
- report or export examples showing the anchor.

---

## 7. Documentation Gate

### Required
Repository docs must exist to guide both humans and AI agents.

### Acceptance Criteria
The repo contains, at minimum:
- `docs/roadmap.md`
- `docs/acceptance.md`
- `docs/model_governance.md`
- `docs/agent_guidelines.md`

### Evidence
- committed docs,
- links from `README.md`,
- doc review checklist.

---

## 8. Phase 1 Exit Criteria

Phase 1 is accepted only if:
- all core artifacts are schema-validated in CI,
- invalid `rule_type` values hard-fail the pipeline,
- a structured validation report can be produced and used to stop downstream execution,
- a reproducible minimal smoke run exists in CI,
- the smoke path can run without making real LLM API calls by using a deterministic stub provider or equivalent governed test double,
- all maker/checker artifacts record model and prompt metadata,
- checker instability can be surfaced on the baseline set,
- a stable source anchor such as a paragraph-level identifier or equivalent is retained through governed downstream artifacts,
- required governance docs exist in the repo.

---

# Phase 2 Acceptance: Mid-Term Planning and BDD Platform (3–9 Months)

## Phase Goal

Upgrade from a stable prototype into an AI-assisted test planning and BDD generation platform that can support multiple document categories and team pilot usage.

## Phase Gate

Phase 2 is complete only if all required acceptance sections below pass.

---

## 1. Multi-Document Ingestion Gate

### Required
The system must support multiple defined document classes.

### Acceptance Criteria
At least 3 document classes are supported, each with:
- parsing strategy,
- extraction constraints,
- expected rule patterns,
- documented failure modes.

### Evidence
- parser configuration or code,
- sample documents,
- extraction outputs,
- class-specific documentation.

---

## 2. Planning Layer Gate

### Required
A planner stage must exist between semantic rules and BDD generation.

Expected flow:

`semantic_rules -> planning -> test objectives -> scenario families -> BDD generation`

### Acceptance Criteria
Planner outputs are:
- schema-validated,
- versioned,
- reproducible on a benchmark set,
- linked to downstream BDD generation.

### Evidence
- planner schema,
- planner artifact samples,
- tests showing trace into BDD outputs.

---

## 3. Traceability Gate

### Required
Generated BDD scenarios must be traceable through the pipeline.

### Acceptance Criteria
Each final BDD scenario can be traced to:
- source document,
- source clause or section,
- atomic rule,
- semantic rule,
- planning decision,
- checker verdict,
- human review outcome.

### Evidence
- traceability fields in artifacts,
- report examples,
- traceability validation tests.

---

## 4. BDD Contract Gate

### Required
A normalized BDD representation must exist independent of final syntax output.

### Acceptance Criteria
- normalized BDD schema exists,
- generated BDD artifacts validate against it,
- at least one output renderer can consume it,
- the contract is documented.

### Evidence
- BDD schema,
- valid and invalid fixtures,
- renderer tests,
- architecture documentation.

---

## 5. Review Collaboration Gate

### Required
Review data must be exchangeable and mergeable outside a single local session.

### Acceptance Criteria
The system supports:
- export of review packages,
- import of review packages,
- merge of review decisions,
- conflict surfacing.

### Evidence
- export/import format,
- merge logic tests,
- conflict examples,
- usage documentation.

---

## 6. Quality Dashboard Gate

### Required
Reports must support pilot-grade visibility into quality and drift.

### Acceptance Criteria
Reports can show:
- rule type coverage heatmap,
- unstable checker decisions,
- baseline drift versus previous runs,
- document class breakdown,
- traceability drill-down,
- JSON and/or CSV export.

### Evidence
- report artifacts,
- screenshots,
- export samples,
- tests for report generation.

---

## 7. Model Governance Enforcement Gate

### Required
Model changes must be gated before adoption.

### Acceptance Criteria
- benchmark checks run before new model adoption,
- checker stability threshold is enforced,
- artifact diff review is documented,
- rollback path is defined.

### Evidence
- governance doc updates,
- benchmark output,
- model adoption checklist.

---

## 8. Phase 2 Exit Criteria

Phase 2 is accepted only if:
- at least 3 document classes are supported with explicit extraction rules,
- at least one non-initial document class can be processed successfully end-to-end,
- planner outputs are versioned and schema-validated,
- normalized BDD artifacts are traceable end-to-end,
- review packages can be exported, imported, and merged,
- reports show drift and unstable judgments,
- generated BDD or `.feature` outputs can pass a governed syntax or dry-run check in the target BDD framework,
- governance or audit history contains multiple recorded runs sufficient to demonstrate change tracking,
- model change regression is enforced before adoption.

---

# Phase 3 Acceptance: Enterprise AI Testing Platform (9–18 Months)

## Phase Goal

Evolve the framework into an enterprise AI testing platform that connects document learning, planning, BDD generation, step definition integration, and execution-ready handoff.

## Phase Gate

Phase 3 is complete only if all required acceptance sections below pass.

---

## 1. Step Definition Integration Gate

### Required
Normalized BDD steps must be connectable to existing step definitions.

### Acceptance Criteria
The system supports:
- exact step match,
- parameterized step match,
- candidate step suggestion,
- unmatched step reporting,
- reuse score,
- ownership mapping for step libraries.

### Evidence
- matching engine or mapping logic,
- sample bindings,
- unmatched step reports,
- integration tests.

---

## 2. Execution Readiness Gate

### Required
An execution-ready scenario contract must exist.

### Acceptance Criteria
An `ExecutableScenario` representation includes:
- environment requirements,
- input data requirements,
- setup hooks,
- deterministic assertion references,
- cleanup hooks,
- linked step definitions.

### Evidence
- schema or contract docs,
- sample executable artifacts,
- contract validation tests.

---

## 3. Deterministic Oracle Gate

### Required
Core structured rule categories must use deterministic assertions where possible.

### Acceptance Criteria
Deterministic checks exist for at least the core structured categories, such as:
- field validation,
- state validation,
- calculation validation,
- deadline or window checks,
- event sequence verification,
- pass/fail accounting.

### Evidence
- oracle modules,
- unit tests,
- scenario outputs using deterministic checks.

---

## 4. Hosted Review Service Gate

### Required
Review capability must move beyond local single-user operation.

### Acceptance Criteria
A deployable review service supports:
- user accounts,
- reviewer roles,
- audit trail,
- conflict resolution,
- comment threads,
- assignment workflow.

### Evidence
- deployment docs,
- screenshots,
- API or UI tests,
- audit log examples.

---

## 5. Enterprise Observability Gate

### Required
Operational metrics must be available for platform governance.

### Acceptance Criteria
The platform can track:
- ingestion failure rate,
- extraction drift,
- duplicate / conflict rule rate,
- planner change rate,
- maker validity rate,
- checker instability rate,
- BDD reuse rate,
- step binding success rate,
- execution pass/fail distribution.

### Evidence
- dashboards,
- metric definitions,
- telemetry docs,
- monitoring test output.

---

## 6. Release Governance Gate

### Required
Formal release controls must exist.

### Acceptance Criteria
The repo or release process defines:
- release tags,
- compatibility matrix,
- benchmark gates,
- migration notes,
- approved provider list.

### Evidence
- release docs,
- tagged releases,
- compatibility records,
- migration templates.

---

## 7. Phase 3 Exit Criteria

Phase 3 is accepted only if:
- normalized BDD can be mapped to existing step definitions with measurable reuse,
- unmatched steps are automatically surfaced,
- execution-ready scenarios can be exported consistently,
- hosted review supports multi-user auditability,
- deterministic assertions cover the core structured rule classes,
- provider rollout requires benchmark pass and rollback path,
- enterprise metrics are available for audit and operations,
- at least two materially different business domains have been processed through the governed platform path,
- regression reporting covers a meaningful multi-run history rather than a single-run snapshot,
- the quality gate has demonstrated that it can block promotion when thresholds fail.

---

# Release Readiness Checklist

This checklist applies before any release that changes core pipeline behavior.

## Required
- schemas validated,
- CI passing,
- benchmark passing,
- model metadata present,
- prompt version updated if behavior changed,
- migration notes written if contracts changed,
- rollback plan documented,
- acceptance evidence attached.

## Optional but Recommended
- artifact diff review,
- report screenshots,
- benchmark trend comparison,
- reviewer signoff,
- AI agent change summary.

---

# AI Agent Acceptance Rules

Any AI coding agent modifying the repo must satisfy the following:

## 1. Do not declare work complete without acceptance evidence
A code change is incomplete until linked to a passing acceptance item.

## 2. Do not change schemas silently
Any artifact contract change must update:
- schema,
- docs,
- tests,
- acceptance references.

## 3. Do not switch models without benchmark evidence
Model changes must include:
- benchmark results,
- stability results,
- compatibility notes.

## 4. Do not merge cross-phase work by accident
If a change belongs to a later phase, it must be labeled and approved as such.

## 5. Prefer deterministic checks when available
If a validation can be implemented deterministically, do not rely solely on LLM judgment.

---

# Maintenance Notes

This document should be updated whenever:
- a roadmap phase changes,
- a new artifact contract is introduced,
- a new model provider is adopted,
- acceptance gates are tightened or relaxed,
- execution integration scope changes.

The owner of each phase should be documented separately in project planning materials if needed.
