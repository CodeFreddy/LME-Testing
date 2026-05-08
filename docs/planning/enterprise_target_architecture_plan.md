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

## Enterprise Architecture Options

These options are candidates for future discussion. No option is approved for implementation by this document.

### Option A: Spring AI / Java Enterprise Service

Use a Spring Boot / Spring AI service layer as the enterprise orchestration backend, with Python components either wrapped as services or migrated selectively.

**Pros:**

- Fits many enterprise Java estates and existing Spring operational practices.
- Strong integration path for SSO, RBAC, audit logging, service discovery, config management, and internal platform standards.
- Good fit if HKEX/source-code systems already expose Java-friendly APIs or sit behind existing Java service layers.
- Easier for enterprise architecture boards to review if Spring is already the approved backend pattern.

**Cons:**

- Current governed pipeline is Python-native; wrapping or migrating it introduces integration and parity risk.
- Python artifact generation, PDF extraction, BDD rendering, and current tests would need a stable service boundary or gradual migration.
- Spring AI adoption still requires prompt/model governance; it does not remove benchmark, rollback, or traceability requirements.
- Higher upfront architecture cost before the local artifact contracts and approval records are fully stabilized.

**Best fit when:**

- the enterprise already mandates Spring services,
- Java teams will own long-term operations,
- SSO/RBAC/audit integration is more important than preserving local Python simplicity.

### Option B: Python Micro-Service Platform

Keep core pipeline logic in Python and expose bounded services for document intake, rule extraction, generation, review, traceability, and evidence export.

**Pros:**

- Preserves current codebase, tests, and governed artifact behavior with less migration risk.
- Natural fit for PDF/document processing, Python BDD tooling, and current deterministic validators.
- Enables incremental service boundaries: start with local APIs, then split only where scaling or ownership requires it.
- Faster path from current POC to a team-shared service.

**Cons:**

- Enterprise operations may require additional work for auth, RBAC, audit, deployment, observability, and support standards.
- Micro-service boundaries can multiply artifact/version consistency problems if introduced too early.
- Without strict contracts, services can drift into hidden state instead of preserving repo-readable artifacts.
- Some enterprises prefer Java/.NET for long-lived governed systems.

**Best fit when:**

- the priority is preserving current governed behavior,
- Python ownership and deployment support are available,
- the first shared version is a controlled internal platform rather than a broad enterprise product.

### Option C: Modular Monolith Web Application

Build a single deployable application with internal modules for workspace, documents, rules, BDD, Scripts, traceability, and evidence.

**Pros:**

- Lower operational complexity than micro-services.
- Easier to preserve transaction boundaries and artifact consistency.
- Good intermediate step from local POC to shared team usage.
- Allows later extraction into services when boundaries are proven by real usage.

**Cons:**

- Scaling and team ownership boundaries are less flexible.
- A poorly structured monolith can become hard to split later.
- Enterprise teams may still require platform integration work for auth, audit, and deployment.
- Does not by itself solve model governance, prompt governance, or approval records.

**Best fit when:**

- the next target is team-shared MVP rather than full enterprise platform,
- artifact consistency matters more than independent service scaling,
- the team wants to defer micro-service complexity until contracts are stable.

### Option D: Workflow Orchestrator Plus Service Workers

Use a workflow engine or orchestration platform for long-running review/generation jobs, with Python or Java workers for specialized tasks.

**Pros:**

- Strong fit for long-running jobs, retries, audit trails, and review checkpoints.
- Makes explicit states such as pending, blocked, stale, approved, regenerated, and finalized.
- Can support review queues and role ownership once approval records exist.
- Separates orchestration from specialized document/LLM/script workers.

**Cons:**

- Requires a clear canonical artifact and approval model before workflow state can be trusted.
- Adds platform complexity and operational dependency.
- Badly designed workflow state can compete with governed JSON artifacts as the source of truth.
- Needs careful rollback and migration planning.

**Best fit when:**

- approval records and artifact versioning are already designed,
- the workflow has many long-running or human-in-the-loop steps,
- audit/event history is a primary enterprise requirement.

### Option E: Existing Enterprise Test Management / DevOps Platform Extension

Integrate the AI-assisted workflow into an existing system such as a test management platform, internal developer portal, CI/CD system, or document-management workflow.

**Pros:**

- Reuses existing access control, audit, ownership, and user adoption paths.
- Can reduce new-platform governance burden.
- May fit testers and automation leads better if they already work in a test management system.
- Good path for importing existing test cases, regression packs, and execution evidence.

**Cons:**

- Existing platforms may not model source-to-rule-to-BDD-to-script lineage cleanly.
- Plugin/extension constraints may limit artifact governance and review UX.
- Integration can hide critical state in third-party systems unless contracts are explicit.
- Vendor/platform constraints can slow iteration.

**Best fit when:**

- the enterprise already has a mandated QA/test management platform,
- import/export of existing assets is the highest priority,
- the AI workflow should augment rather than replace current QA operations.

### Option Comparison

| Option | Main Strength | Main Risk | Near-Term Suitability |
|--------|---------------|-----------|-----------------------|
| Spring AI / Java service | Enterprise alignment and integration | Python parity/migration risk | Medium, if enterprise Java ownership is confirmed |
| Python micro-services | Preserves current pipeline behavior | Operational maturity burden | High for controlled internal MVP |
| Modular monolith | Simple deployable team MVP | Later scaling/splitting risk | High as an intermediate step |
| Workflow orchestrator + workers | Human-in-loop audit and long-running jobs | Premature workflow state complexity | Medium after approval records exist |
| Existing enterprise platform extension | User adoption and existing controls | Hidden state and platform constraints | Medium, depends on platform fit |

### Recommended Discussion Position

For the next enterprise review, compare **Python modular monolith**, **Python micro-services**, and **Spring AI / Java service** as the primary candidates.

Recommended default path unless enterprise constraints override it:

1. Keep the local Python workflow as the governed reference implementation.
2. Build a modular monolith or thin Python service wrapper for team-shared MVP.
3. Define artifact versioning, approval records, audit events, and access assumptions.
4. Revisit Spring AI or broader micro-services after ownership, integration, and deployment constraints are known.

This avoids a premature platform rewrite while keeping Spring AI and enterprise micro-services on the table for the right reasons.

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
