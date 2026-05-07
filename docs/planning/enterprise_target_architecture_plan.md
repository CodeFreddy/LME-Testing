# Enterprise Target Architecture Plan

**Date:** 2026-05-06
**Scope:** Long-range product and platform planning
**Status:** Draft

---

## Purpose

This document describes the long-term target architecture for evolving the current local, single-user LME testing workflow into an enterprise-level governed test design platform.

It is intentionally a planning document. It does not approve implementation of multi-user features, new schemas, new LLM stages, new approval contracts, or deployment infrastructure. Those changes require separate scoped tasks, contracts, validation, and acceptance evidence.

---

## Current Baseline

The current system is a local document-driven test design workflow with:

- governed source/rule artifacts,
- maker/checker/BDD/script generation,
- deterministic validation gates,
- local review-session GUI,
- rule-workflow-session GUI,
- static HTML reporting and audit views,
- model and prompt governance documentation.

The current architecture is suitable for local POC and controlled Stage 2 workflow validation. It is not yet an enterprise multi-user platform.

---

## Enterprise Direction

The long-term system should support:

- large source document sets,
- repeatable document-version comparison,
- role-based review workflows,
- traceability from document source to evidence,
- immutable artifact versioning,
- auditable approval records,
- deterministic governance dashboards,
- batch operations,
- review queues,
- controlled model/prompt rollout,
- enterprise deployment and access controls.

The guiding principle is:

```text
Enterprise trust comes from traceable, reviewable, reproducible artifacts.
```

---

## Target Product Layers

### 1. Workspace Layer

Add a first-class workspace/project layer above documents.

Example hierarchy:

```text
Workspace
  -> Document Set
    -> Source Document Version
      -> Extracted Rules
        -> Reviewed Rules
          -> BDD Scenarios
            -> Test Scripts
              -> Evidence
```

Possible workspace types:

- regulation pack,
- market or product line,
- test release,
- client delivery package,
- internal validation campaign.

Enterprise value:

- users can organize work by business context instead of individual files,
- artifact lineage can be scoped to a meaningful project boundary,
- review and evidence packs can be exported per workspace.

MVP implication:

- The tabbed GUI should not hardcode assumptions that only one document exists forever.
- A local session can behave like a lightweight workspace until a formal workspace model is approved.

### 2. Documents And Versioning

Documents should become versioned enterprise inputs.

Target capabilities:

- document upload/import registry,
- source file hash,
- document class/type,
- effective date/version label,
- extraction attempts,
- source-to-artifact lineage,
- document-to-document diff,
- changed-section detection,
- history snapshots.

Enterprise value:

- users can answer which document version produced which rules,
- changes between document versions can invalidate downstream approvals,
- repeatability does not rely on filename memory.

### 3. Review Queues

Large document sets need queue-based review in addition to tabs.

Target queues:

- My pending reviews,
- Changed since previous version,
- Blocked items,
- Needs business review,
- Needs QA/BDD review,
- Needs automation review,
- Ready for evidence pack,
- Recently invalidated approvals.

Enterprise value:

- reviewers can work by responsibility and priority,
- large documents do not become one long review page,
- pending work remains visible.

### 4. Role-Based Review

Future roles may include:

- business reviewer,
- rule/governance reviewer,
- QA/BDD reviewer,
- automation engineer,
- approver,
- auditor,
- administrator.

Role design should eventually control:

- visible queues,
- allowed edits,
- approval authority,
- export authority,
- model/prompt rollout permissions,
- governance override permissions.

MVP implication:

- Do not implement permissions in the tabbed GUI MVP.
- Design UI status labels and review metadata so role ownership can be added later.

### 5. Traceability Matrix

The enterprise system should provide a traceability matrix across the full chain:

```text
Source document paragraph
  -> Atomic rule
  -> Semantic rule
  -> BDD scenario
  -> Test script / step
  -> Validation evidence / result
```

Target capabilities:

- filter by document, rule, scenario, script, or evidence status,
- show missing links,
- show changed upstream anchors,
- show impacted downstream artifacts,
- export traceability evidence.

Enterprise value:

- auditors can verify coverage,
- business users can inspect where a rule came from,
- QA can understand which tests are impacted by a document change.

### 6. Change Impact Review

When a new source document version arrives, the system should show:

- unchanged sections,
- changed sections,
- deleted sections,
- newly added sections,
- rules impacted by source changes,
- BDD impacted by changed rules,
- scripts impacted by changed BDD,
- approvals invalidated by upstream changes,
- recommended regeneration scope.

Enterprise value:

- reviewers focus on what changed,
- unchanged approved work can be preserved,
- downstream work can be regenerated selectively.

---

## Target Platform Layers

### 1. Canonical Approval Records

Approvals should eventually become governed artifacts.

Target approval record fields:

- artifact type,
- artifact id,
- artifact version/hash,
- decision,
- reviewer,
- role,
- timestamp,
- rationale/notes,
- source context,
- invalidation status,
- invalidation reason,
- previous approval reference.

Important constraint:

- This is not part of the tabbed GUI MVP.
- A canonical approval schema must be separately designed, validated, tested, and documented before implementation.

### 2. Immutable Artifact Versioning

Enterprise workflows should avoid silently mutating approved artifacts.

Target versioning:

- source document hash/version,
- extraction run id,
- atomic/semantic rule version,
- rule review version,
- BDD version,
- script version,
- evidence pack version.

Enterprise value:

- exact approved states can be reproduced,
- audit trails can identify what changed and when,
- rollback is possible without reconstructing history from logs.

### 3. Audit-First Event Log

Every meaningful action should be recorded.

Target events:

- document uploaded/imported,
- extraction run started/completed/failed,
- rule edited,
- review decision made,
- BDD generated,
- BDD edited,
- script generated,
- script edited,
- validation run completed,
- artifact exported,
- approval invalidated.

Event metadata:

- actor,
- timestamp,
- workspace,
- document context,
- artifact id/version,
- source hash,
- model/prompt/config metadata where applicable,
- before/after references.

### 4. Validation Dashboard

Enterprise users need a visible validation control panel.

Target dashboard signals:

- schema validation,
- artifact governance,
- source anchor completeness,
- duplicate/advisory warnings,
- missing review decisions,
- blocked approvals,
- BDD generation status,
- step matching gaps,
- coverage status,
- checker stability,
- model/prompt provenance completeness.

Dashboard rule:

- warnings and failures must remain visible.
- the UI must not hide broken contracts to make the workflow look cleaner.

### 5. Batch Operations

Large document workflows require bulk actions.

Target operations:

- approve unchanged items,
- assign review owner,
- bulk mark non-testable,
- regenerate impacted BDD only,
- regenerate impacted scripts only,
- export selected evidence pack,
- compare selected document versions,
- filter and bulk-save reviewer notes.

Safety requirement:

- batch approvals must record precise artifact versions and reviewed scope.

### 6. Model And Prompt Release Control

Enterprise use requires controlled rollout of model/prompt changes.

Target capabilities:

- model strategy registry,
- prompt version registry,
- benchmark comparison before adoption,
- rollback notes,
- side-by-side run comparison,
- release gate for default model/prompt changes,
- provenance display in evidence views.

Constraint:

- No default model or prompt changes should be made without benchmark evidence and rollback notes.

---

## Deployment Direction

The current system is local and single-user. Enterprise deployment should be introduced in stages.

Possible staged deployment:

1. Local single-user tabbed workflow.
2. Local workspace registry with immutable artifact versions.
3. Team-shared artifact store.
4. Authenticated web app.
5. Role-based review and approval workflow.
6. Centralized audit/event store.
7. Enterprise integrations.

Potential enterprise integrations:

- SSO,
- document management system,
- issue tracker,
- CI/CD,
- test management platform,
- evidence archive,
- model gateway/provider control plane.

Deployment constraints:

- Do not introduce server/database infrastructure before artifact contracts and approval records are defined.
- Do not turn local POC behavior into enterprise claims without acceptance evidence.

---

## Suggested Roadmap Slices

### Slice E1: Tabbed Local Workflow

Build the tabbed GUI shell:

```text
Documents -> Rules -> BDD -> Scripts -> Evidence
```

Goal:

- make large-document review usable,
- preserve existing artifacts,
- keep single-user/local scope.

### Slice E2: Workspace And Document Registry

Define a lightweight workspace/document registry.

Goal:

- preserve document identity, version, hash, and artifact lineage.

Requires:

- contract proposal,
- validation,
- tests,
- migration notes.

### Slice E3: Traceability Matrix

Build derived traceability view from existing artifacts.

Goal:

- show source-to-evidence lineage without changing source artifacts.

### Slice E4: Canonical Approval Records

Define and implement governed approval records.

Goal:

- make review decisions auditable and version-bound.

Requires:

- schema,
- acceptance criteria,
- invalidation rules,
- tests,
- rollback plan.

### Slice E5: Change Impact Review

Build document-version diff and downstream impact review.

Goal:

- focus reviewers on changed/impacted items.

### Slice E6: Role-Friendly Queues

Add review queues and optional role ownership.

Goal:

- make enterprise-scale review work manageable.

Requires:

- role model planning,
- permissions boundary,
- review responsibility contract.

### Slice E7: Enterprise Deployment

Introduce authenticated shared deployment only after artifact versioning and approval records are stable.

Goal:

- support team usage with auditability.

---

## Near-Term Recommendation

Proceed in this order:

1. Implement the tabbed local workflow MVP.
2. Add a lightweight workspace/document registry contract.
3. Add traceability matrix as a derived view.
4. Design canonical approval records.
5. Add change-impact review.
6. Add role-friendly queues and permissions.
7. Consider shared enterprise deployment.

This order keeps the current POC honest while moving toward an enterprise architecture.

---

## Non-Goals For Immediate MVP

- multi-user permissions,
- SSO,
- database-backed deployment,
- canonical approval schema,
- new LLM-driven stages,
- default model or prompt changes,
- production HKv14 downstream automation claims,
- replacing governed JSON/JSONL artifacts with HTML state.

---

## Governance Notes

Any future implementation must report:

- roadmap phase/task mapping,
- contracts touched,
- schema impact,
- prompt/model impact,
- validation added,
- acceptance criteria,
- rollback considerations,
- PASS/PARTIAL/FAIL self-evaluation.

Stop and escalate if:

- a new approval schema is needed,
- a new LLM-driven stage is proposed,
- a model/prompt/default config change is implied,
- a database or multi-user deployment changes artifact ownership,
- downstream artifact contracts would be affected.
