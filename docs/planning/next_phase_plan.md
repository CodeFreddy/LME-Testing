# Next Phase Plan

**Date:** 2026-05-08  
**Status:** Draft for review  
**Canonical owner:** `docs/planning/implementation_plan.md` and `docs/governance/acceptance.md`
**Related roadmap task:** S2-F6, S2-F7, S2-F8, later enterprise slices
**Scope:** Planning only. This document does not approve schema changes, prompt changes, default model changes, new LLM stages, enterprise deployment, HKEX integration, or production readiness claims.

---

## Purpose

This plan consolidates the recent planning threads into a clear execution order:

- S2-F6 rewrite prompt governance completion,
- S2-F7 rule workflow Scripts and navigation completion,
- S2-F8 enterprise POC response planning,
- later enterprise architecture slices.

The goal is to keep the next work useful without letting enterprise ambition blur current contracts.

The visual north star for future tabbed GUI work is the mockup set in `docs/planning/assets/tabbed_review_gui_mockups/`, as described in `docs/planning/tabbed_review_gui_development_plan.md`.

---

## Current Verified State

### Complete

- S2-F4 rule extraction review GUI is implemented and smoke-reviewed with HKv14.
- S2-F5 governed maker/checker batch concurrency is implemented and stub-verified.
- S2-F1 through S2-F3 deterministic HKv14 role review and document readiness slices are implemented.
- S2-D1 browser-level review-session BDD/Scripts path is implemented.

### Partial

- S2-F6 rewrite prompt governance:
  - dedicated rewrite prompt path exists,
  - `run_rewrite_pipeline()` uses it,
  - rewrite metadata still uses maker prompt version,
  - no dedicated S2-F6 acceptance gate exists yet.

- S2-F7 Scripts and stage navigation:
  - review-session can generate editable Scripts code for unmatched steps,
  - deterministic fallback exists for invalid Scripts model payloads,
  - basic review-session stage gates exist,
  - API-backed implementation metadata, governed draft-step approval manifests, stale-state handling, and full rule-workflow-session navigation remain open.

### Blocked

- Stage 3 real execution remains blocked by real LME/HKEX environment access.
- Enterprise deployment remains planning only until artifact versioning, approval records, access assumptions, and operational ownership are approved.

---

## Next Phase Order

### S2-F6A — Rewrite Prompt Governance Completion

**Goal:** Make the existing rewrite prompt path governed and correctly versioned.

**Why first:** The code has already moved past planning. Governance should catch up before more UI and workflow behavior depends on rewrite outputs.

**Inputs:**

- `src/lme_testing/prompts.py`
- `src/lme_testing/pipelines.py`
- `tests/test_pipelines.py`
- `docs/governance/acceptance.md`

**Outputs:**

- `REWRITE_PROMPT_VERSION`
- rewrite summary metadata using rewrite-specific prompt version,
- focused tests for rewrite prompt metadata,
- focused tests for rewrite concurrency ordering/failure behavior if concurrency remains exposed,
- S2-F6 acceptance gate and evidence,
- governance baseline checks.

**Acceptance:**

- Rewrite summaries no longer report `MAKER_PROMPT_VERSION` as the rewrite prompt version.
- Tests prove rewrite metadata is present and accurate.
- Any accepted rewrite concurrency behavior has deterministic ordering and visible failure behavior.
- No schema, default model, or review-decision contract changes.

**Self-evaluation target:** PASS.

---

### S2-F7A — Scripts Implementation Metadata

**Goal:** Make the Scripts view show what a matched or candidate step actually executes.

**Why next:** This is the smallest useful S2-F7 track and directly addresses tester/automation-lead feedback without adding a new contract.

**Inputs:**

- `src/lme_testing/review_session.py`
- `src/lme_testing/rule_workflow_session.py`
- `src/lme_testing/step_registry.py`
- `deliverables/im_hk_v14_mock_api/`
- `deliverables/im_hk_mock_api_common/`

**Outputs:**

- deterministic parser for Python step definition metadata,
- Scripts payload fields for source file, function name, decorator pattern, code snippet, and detected endpoint call,
- read-only UI panel for implementation details, visually aligned with `04-scripts-review-tab.png`,
- focused unit/HTTP tests.

**Acceptance:**

- A matched step can show its source implementation.
- The UI shows source file and function name.
- Mock API endpoint calls are detected where available.
- Missing implementation metadata remains visible as a gap.
- No generated code is trusted or promoted by this track.

**Self-evaluation target:** PASS for Track 1, S2-F7 remains PARTIAL.

---

### S2-F7B — Governed Draft Step Generation

**Goal:** Convert existing Scripts AI generation into a governed draft-step workflow.

**Inputs:**

- existing `/api/scripts/create-by-ai`,
- generated scripts artifacts,
- step registry outputs,
- API catalog.

**Outputs:**

- `generated_step_definitions/step_generation_manifest.json`,
- draft code artifacts with provenance,
- approval state and reviewer notes,
- explicit promotion target,
- attach/stub/manual actions for unmatched steps.

**Acceptance:**

- Generated code is reviewable before promotion.
- Provenance records source BDD step, semantic rule, scenario, endpoint, timestamp, reviewer status, and promotion target.
- Step registry refresh can move a step from `unmatched` to matched/candidate only after explicit review.
- Binding failures remain visible.

**Self-evaluation target:** PASS for Track 2, S2-F7 remains PARTIAL until navigation is complete.

---

### S2-F7C — Rule Workflow Stage Navigation And Stale State

**Goal:** Let users revisit workflow stages without restarting while preserving artifact correctness.

**Inputs:**

- `rule-workflow-session` state,
- review-session stage gates,
- generated cases, BDD, Scripts, and final artifacts.

**Outputs:**

- stage readiness payload,
- backward/forward navigation gates,
- stale downstream artifact markers,
- explicit regeneration controls,
- immutable final snapshots,
- browser-level happy-path and stale-state tests,
- tabbed shell direction aligned with the Documents/Rules/BDD/Scripts/Evidence mockups.

**Acceptance:**

- User can go backward without restarting.
- Forward navigation is blocked with prerequisite messages.
- Upstream edits mark downstream artifacts stale.
- Finalized outputs are not silently mutated.

**Self-evaluation target:** PASS for S2-F7.

---

### S2-F8 — Enterprise POC Response Planning

**Goal:** Produce a bounded response package for enterprise stakeholders without implementing enterprise infrastructure.

**Inputs:**

- `docs/planning/enterprise_poc_feedback_summary.md`
- `docs/planning/enterprise_target_architecture_plan.md`
- `docs/planning/tabbed_review_gui_development_plan.md`
- current S2-F4 through S2-F7 status.

**Outputs:**

- enterprise deployment assumptions,
- HKEX/source-code access checklist,
- role-based MVP workflow map,
- maker/checker benchmark and sampling proposal,
- prompt/RAG governance boundaries,
- non-goals and approval requirements.

**Acceptance:**

- Enterprise architecture options are compared with pros/cons.
- HKEX/source-code execution prerequisites are explicit.
- Maker/checker `Pass` is treated as advisory unless supported by deterministic validation, benchmark evidence, or human review policy.
- RAG/knowledge-base use remains planning only unless separately approved.
- No implementation is started under this slice.

**Self-evaluation target:** PASS as planning package.

---

## Later Enterprise Slices

| Slice | Purpose | Precondition |
|------|---------|--------------|
| E1 Local tabbed workflow | Convert local flow into Documents -> Rules -> BDD -> Scripts -> Evidence using the mockups as visual target | S2-F7 direction agreed |
| E2 Workspace/document registry | Preserve document identity, hash, version, and lineage | Contract proposal approved |
| E3 Traceability matrix | Derived source-to-evidence lineage view | Workspace/document lineage available or simulated locally |
| E4 Canonical approval records | Version-bound review decisions | Approval schema approved |
| E5 Change impact review | Diff document versions and downstream impacts | Versioned documents and approval invalidation rules |
| E6 Role-friendly queues | Pending/blocked/changed review queues | Role ownership model agreed |
| E7 Enterprise deployment | Shared authenticated deployment | Artifact versioning, approval records, audit events, and access model stable |

---

## Enterprise Discussion Guardrails

- Local POC success does not imply production readiness.
- Enterprise deployment should follow artifact/version/approval contracts, not precede them.
- Spring AI, micro-services, or another architecture should be selected only after access, security, audit, model-provider, and ownership assumptions are known.
- New LLM stages require contracts, validation, traceability, reviewable outputs, benchmark evidence, and rollback notes.
- Generated scripts remain draft until reviewed and promoted through a governed process.

---

## Recommended Immediate Action

Start with S2-F6A.

It is the smallest corrective slice, closes a real governance gap, and gives later S2-F7/enterprise work a cleaner base.
