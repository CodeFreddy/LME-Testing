# Initial Margin HKv14 Role-Friendly Impact Decision Review Plan

**Status:** Implemented local review package generator
**Created:** 2026-04-27
**Task ID:** S2-F1
**Source proposal:** `docs/architecture/Executable_Engineering_Knowledge_Contract.md` section "03 MVP Scope and Delivery Plan"
**Baseline impact:** Adds a deterministic S2-F1 CLI package generator. This document does not change schemas, prompts, default models, maker/checker pipeline behavior, review-session behavior, or Stage 3 readiness claims.

---

## Purpose

Promote a small, governed MVP slice from the broader Executable Engineering Knowledge Contract proposal into the active roadmap.

The broad proposal defines the MVP spine as:

```text
Spec Change -> Test Impact -> Automation Backlog
```

For this repository, the approved near-term slice is narrower:

```text
Initial Margin HKv13 -> HKv14 -> Deterministic Diff -> Role Review -> Structured Decision Record
```

The goal is to replace Markdown-only HKv14 downstream decision handling with a local, single-user, role-friendly review surface that persists structured decision records. This proves the proposal's human-control and transparency requirement without introducing a generic workflow platform.

---

## In Scope

- Use existing HKv13 -> HKv14 deterministic diff evidence.
- Show changed candidates, ID drift candidates, source anchors, and downstream treatment mapping.
- Let role owners record decisions for BA, QA Lead, Automation Lead, and PM / Release Owner perspectives.
- Support decision values: `approve`, `reject`, `defer`, and `request_rework`.
- Capture reviewer role, reviewer name, timestamp, rationale, and comments.
- Persist decisions as governed JSON.
- Export a human-readable Markdown decision summary derived from the structured JSON record.
- Add focused validation and tests.
- Keep the UI local and single-user.

---

## Out Of Scope

- Generic document upload.
- Full document library or workflow engine.
- Role-based permissions or hosted collaboration.
- New maker/checker prompts.
- New model defaults.
- New LLM-driven stages.
- Automatic test case updates.
- Automatic code generation.
- Real LME API execution or Stage 3 readiness claims.
- Moving mock API bridge sources out of `deliverables/`.

---

## Input Contract

The implementation must consume existing governed evidence, not infer from chat-only context.

Required inputs:

- `evidence/im_hk_v14_diff/im_hk_v13_to_v14_diff.json`
- `docs/planning/im_hk_v14_downstream_treatment_mapping.md`
- `artifacts/im_hk_v13/`
- `artifacts/im_hk_v14/`

Optional supporting inputs:

- `docs/planning/im_hk_v14_diff_report.md`
- `docs/planning/im_hk_v14_promotion_scope.md`
- `docs/planning/im_hk_v14_downstream_decision.md`

---

## Output Contract

The structured decision record is canonical. Markdown is an export.

Suggested output layout:

```text
runs/im_hk_v14/review_decisions/<timestamp>/
  decision_record.json
  decision_summary.md
```

Minimum JSON fields:

```text
metadata
source_evidence
review_scope
candidate_decisions
open_items
summary
```

Implemented command:

```powershell
python main.py im-hk-v14-role-review
```

Default output layout:

```text
runs/im_hk_v14/review_decisions/<timestamp>/
  decision_record.json
  decision_summary.md
  review.html
```

Each candidate decision should include at least:

```text
candidate_id
candidate_type
source_rule_id
target_rule_id
source_anchor
treatment_category
reviewer_role
reviewer_name
decision
rationale
comments
review_timestamp
status
```

Allowed `reviewer_role` values:

```text
BA
QA Lead
Automation Lead
PM / Release Owner
```

Allowed `decision` values:

```text
approve
reject
defer
request_rework
```

---

## Implementation Notes

- Prefer extending existing local review-session patterns where practical.
- Keep deterministic evidence visible in the UI and output artifacts.
- Use atomic writes for decision records.
- Markdown summaries must be generated from `decision_record.json`; they must not become the source of truth.
- Validation should fail visibly if a decision references an unknown candidate or unsupported role/decision value.
- The implementation must not mutate `deliverables/im_hk_v13_mock_api/`.
- The implementation must not alter schemas, prompts, default models, or roadmap phase boundaries.

---

## Acceptance Gates

S2-F1 is PASS only if:

- Existing HKv13 baseline artifacts and deliverables are untouched.
- HKv14 remains scoped as POC/mock/stub downstream baseline candidate work.
- Every candidate decision links back to deterministic diff evidence or a documented downstream treatment row.
- `decision_record.json` is validated deterministically.
- `decision_summary.md` is derived from the structured decision record.
- The UI or review surface records reviewer role, reviewer name, decision, rationale, comments, and timestamp.
- Focused tests cover load, save, validation failure, and Markdown export.
- Docs governance and artifact governance checks pass.
- No new LLM stage, prompt change, default model change, schema change, or production-readiness claim is introduced.

---

## Rollback Considerations

The slice should be rollback-safe:

- Remove the review UI entry point and S2-F1 decision outputs.
- Preserve existing HKv14 diff evidence and downstream treatment mapping.
- Preserve HKv13 mock API deliverable as the baseline.
- Leave prior Markdown decision notes intact.

---

## Self-Evaluation Target

Current plan promotion status: PASS.

Implementation status: PASS for local deterministic review package generation. The implementation creates canonical JSON, derived Markdown, and a local HTML review surface. It does not add hosted collaboration, role-based permissions, a generic document platform, or a new LLM stage.
