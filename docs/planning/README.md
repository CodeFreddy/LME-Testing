# Planning Documents

**Status:** Active planning index
**Date:** 2026-05-08
**Canonical owner:** `docs/index.md` and `docs/governance/docs_housekeeping.md`
**Scope:** Local index for roadmap, implementation plans, active planning docs, validation plans, and future planning support.

---

## Purpose

This folder contains planning records for current, completed, and future work.

Use this README to decide where to start, which documents are current control surfaces, and which documents are supporting plans or evidence summaries.

For cleanup rules, follow `docs/governance/docs_housekeeping.md`.

---

## Current Control Documents

These documents define current direction and execution contracts. Keep them current rather than archiving them.

| File | Role |
|------|------|
| `roadmap.md` | Strategic direction, phase boundaries, current status, and non-goals. |
| `implementation_plan.md` | Task contracts, prerequisites, output expectations, and self-evaluation records. |
| `next_phase_plan.md` | Current near-term sequencing for S2-F6, S2-F7, S2-F8, and later enterprise slices. |

---

## Active Or Partial Planning

| File | Status | Role |
|------|--------|------|
| `rule_workflow_scripts_stage_navigation_plan.md` | Proposed / partial S2-F7 | Scripts implementation visibility, draft step generation, and workflow navigation. |
| `enterprise_poc_feedback_summary.md` | Planning input | Captures stakeholder POC feedback for S2-F8. |
| `enterprise_target_architecture_plan.md` | Draft support | Long-range enterprise architecture options; not implementation approval. |
| `tabbed_review_gui_development_plan.md` | Draft direction | Future tabbed workflow direction and visual mockup references. |

---

## Completed Planning And Evidence Records

These records remain in planning because they are still frequently linked or useful to active context. Archive them only after the current-control documents preserve the needed status and evidence.

| File | Status | Role |
|------|--------|------|
| `mock_api_validation_plan.md` | Complete S2-C1 | LME mock API validation plan. |
| `im_hk_v13_mock_api_validation_plan.md` | Complete S2-C2 | Initial Margin HKv13 mock API validation plan. |
| `im_hk_v14_mock_api_validation_plan.md` | Complete S2-C4 | Initial Margin HKv14 promoted mock API validation plan. |
| `im_hk_v14_diff_report.md` | Evidence summary | HKv13-to-HKv14 deterministic diff summary. |
| `im_hk_v14_downstream_decision.md` | Decision record | Human POC downstream decision record. |
| `im_hk_v14_downstream_treatment_mapping.md` | Complete S2-C4 | Deterministic treatment mapping. |
| `im_hk_v14_promotion_scope.md` | Complete S2-C4 | Promotion scope and boundaries. |
| `im_hk_v14_role_review_plan.md` | Complete S2-F1 | Role-friendly impact decision review plan. |
| `mvp_document_readiness_plan.md` | Complete S2-F2 | MVP document readiness registry plan. |
| `mvp_input_document_contract_plan.md` | Complete S2-F3 | Test Plan and Regression Pack Index input contract plan. |
| `mock_api_deliverables_policy.md` | Current policy | Stage 2 deliverables location policy. |
| `ui_test_plan.md` | Complete S2-D1 | Browser-level review-session test plan and limits. |

---

## Future Planning Support

These documents are not current implementation approval. They preserve future direction or design options.

| File | Role |
|------|------|
| `step_integration_plan.md` | Future Stage 3 BDD-to-step integration bridge. |
| `document_library_and_capability_workflow_proposal.md` | Future document/capability workflow proposal. |
| `document_library_and_capability_workflow_implementation_plan.md` | Future implementation proposal for document/capability workflow. |
| `assets/tabbed_review_gui_mockups/` | Visual target references for future tabbed workflow discussion. |

---

## Archived Planning Records

Completed historical records that no longer need to remain in this folder live under `docs/archives/`.

Examples:

- `docs/archives/s2t01_coverage_analysis.md`
- `docs/archives/stage2_planned_modules.md`

See `docs/archives/README.md` for the archive index and preservation reasons.

---

## Placement Rules

Add a new planning document here only when it is one of:

- active roadmap/task planning,
- validation planning,
- decision planning,
- future planning support that is clearly marked as non-implementation,
- evidence summary that is still directly useful to current work.

Move a completed planning document to `docs/archives/` when the current status is preserved in `roadmap.md`, `implementation_plan.md`, `acceptance.md`, or another current control document.

Do not place source materials, generated evidence artifacts, checkpoints, or release records here.
