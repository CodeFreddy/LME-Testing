# Tabbed Review GUI Development Plan

**Date:** 2026-05-06
**Scope:** S2-F4 continuation planning slice
**Status:** Draft, human-approved direction

---

## Goal

Evolve the current `rule-workflow-session` GUI into a human-friendly tabbed review workflow for large source documents, while preserving existing governed artifact contracts.

The current GUI can become too long when a large raw document produces many extracted rules, BDD scenarios, and script review items. The MVP should let a reviewer move through a clear workflow instead of reviewing every stage on one shared page.

Primary happy path:

```text
Documents -> Rules -> BDD -> Scripts -> Evidence
```

Each tab should preserve the active document context and make the next action obvious.

---

## Roadmap Mapping

- **Roadmap area:** Stage 2, S2-F4 rule extraction review workflow continuation
- **Task type:** UI/workflow usability planning
- **Contract impact:** None in MVP
- **Prompt impact:** None
- **Model/default config impact:** None
- **Schema impact:** None

This plan is a review-surface restructuring. Canonical source-of-truth artifacts remain the governed JSON/JSONL files already produced by the pipeline.

---

## Design Principles

1. **Documents own context**
   - Uploaded/imported documents should be visible as first-class session items.
   - Selecting a document sets the active context for downstream tabs.
   - Context should be preserved when jumping between tabs.

2. **Tabs represent workflow stages**
   - Each stage should have a clear purpose, status, blockers, and next action.
   - Reviewers should not need to scroll through all workflow stages on one page.

3. **Governed artifacts remain canonical**
   - Tabs display and edit governed artifacts.
   - The UI must not make rendered HTML the source of truth.

4. **Large-document review must be filterable**
   - Rule, BDD, and script review surfaces should support filtering by status, document, rule, and changed/pending items.

5. **Failures stay visible**
   - Validation failures, advisory warnings, missing approvals, and generation errors should appear as blockers or warnings, not disappear to keep the flow moving.

---

## Proposed Tabs

### 1. Documents

Purpose: session context owner.

MVP behavior:

- List uploaded/imported documents.
- Show active document selection.
- Show document metadata:
  - filename,
  - source type,
  - extraction status,
  - artifact directory,
  - latest extraction attempt,
  - downstream stage status.
- On document click, show:
  - extraction history,
  - diff/history summary,
  - latest generated artifacts,
  - warnings or blockers.
- Maintain active document context across Rules, BDD, Scripts, and Evidence tabs.

Output impact:

- None for MVP. This tab reads existing session state, source paths, artifact dirs, and history snapshots.

### 2. Rules

Purpose: extract, review, edit, and approve extracted rules.

MVP behavior:

- Extract or import rules for the active document.
- Review atomic and semantic rules grouped by document and rule group.
- Show source anchors and extracted text context.
- Show reviewed-change badges and diffs.
- Provide filters:
  - all,
  - pending,
  - edited,
  - approved,
  - rejected,
  - changed since previous extraction.
- Save reviewed rules using existing reviewed artifact paths:
  - `rule_review/reviewed_atomic_rules.json`
  - `rule_review/reviewed_semantic_rules.json`

Output impact:

- Reuse existing reviewed rule artifacts.
- Do not change rule schemas in MVP.

### 3. BDD

Purpose: generate, review, edit, and approve BDD scenarios from approved rules.

MVP behavior:

- Enable BDD generation only after the relevant rules are approved or explicitly allowed.
- Generate BDD for the active document or selected approved rule set.
- Display normalized BDD grouped by:
  - document,
  - semantic rule,
  - scenario.
- Review and edit Given/When/Then steps.
- Provide scenario-level approval/rejection status.
- Persist reviewed BDD through the existing review-session mechanics, including:
  - `reviewed_normalized_bdd_latest.jsonl`
  - human BDD/script edit snapshots.

Output impact:

- Reuse existing normalized BDD review/edit behavior.
- Do not make Gherkin output canonical where normalized BDD owns the contract.

### 4. Scripts

Purpose: generate, review, edit, and approve test scripts from approved BDD.

MVP behavior:

- Show step visibility metrics:
  - total steps,
  - exact matches,
  - parameterized matches,
  - candidates,
  - unmatched gaps.
- List step matches and gaps by active document/rule/scenario context.
- Allow review/edit of unmatched or generated step text/code.
- Generate/export scripts from approved BDD.
- Preserve existing Scripts tab behavior from `review_session.py`, but mount it inside the tabbed shell.

Output impact:

- Reuse existing step registry and BDD export artifacts.
- Keep deterministic step matching visible.

### 5. Evidence

Purpose: show completion status, generated artifacts, validation outputs, and blockers.

MVP behavior:

- Show artifact links:
  - reviewed rules,
  - normalized/reviewed BDD,
  - step visibility report,
  - generated feature files/scripts,
  - HTML reports,
  - CSV outputs where available.
- Show latest validation/governance status if available.
- Show coverage/checker summary if available.
- Show warnings and blockers for the active document/workflow.
- Provide a concise "happy path complete" summary when all required review stages are approved.

Output impact:

- Derived display only.

### Optional Later Tab: History

Purpose: cross-workflow timeline and snapshot recovery.

This can stay inside Documents for MVP. If history becomes crowded, promote it to a dedicated tab later.

---

## Navigation Requirements

Add a persistent top navigation bar:

```text
Documents | Rules | BDD | Scripts | Evidence
```

Each tab should show a status badge:

- `Not started`
- `Ready`
- `Needs review`
- `Approved`
- `Blocked`

Each tab should expose one clear happy-path action:

- Documents: `Select Document` or `Upload Document`
- Rules: `Extract Rules` or `Approve Rules`
- BDD: `Generate BDD` or `Approve BDD`
- Scripts: `Generate Scripts` or `Approve Scripts`
- Evidence: `Review Evidence`

The UI should allow direct jumping between tabs while preserving context. If a future tab is blocked, show the reason and the required previous action.

---

## Implementation Phases

### Phase A: Shell and Context

- Refactor `rule_workflow_session.py` frontend state into a tabbed shell.
- Add top navigation and tab status badges.
- Add active document/session context.
- Keep existing `/scenario-review` route as a compatibility fallback.
- Avoid schema, prompt, and model changes.

Acceptance:

- User can switch between tabs without losing active document context.
- Existing rule workflow startup still works.

### Phase B: Documents Tab

- Add document list/history payload.
- Add active document selection API.
- Display upload/import history and latest artifacts.
- Display extraction diffs/history when a document is clicked.

Acceptance:

- Multiple uploaded/imported docs can be listed.
- Active document drives downstream tab context.

### Phase C: Rules Tab

- Move existing rule review UI into the Rules tab.
- Add filters and approval status.
- Keep reviewed artifact writes unchanged.
- Keep source anchors visible.

Acceptance:

- Reviewer can extract, edit, save, and approve rules without using a long shared page.

### Phase D: BDD and Scripts Tabs

- Mount the existing Review Session BDD/Scripts logic inside the tabbed shell.
- Reuse `bdd_payload`, `save_bdd_edits`, `scripts_payload`, and `save_scripts_edits` behavior.
- Preserve `/scenario-review` as fallback for compatibility.

Acceptance:

- Reviewer can generate/review BDD and scripts from approved rules inside the same tabbed workflow.

### Phase E: Evidence Tab

- Surface artifact links, summaries, blockers, and validation status.
- Show happy-path completion status.

Acceptance:

- Reviewer can see what was produced, what passed, and what remains blocked.

### Phase F: Tests

- Add unit tests for tab/status/context payloads.
- Add browser smoke coverage for:
  - upload/import document,
  - extract rules,
  - approve rules,
  - generate BDD,
  - review/save BDD,
  - review/save scripts,
  - inspect Evidence.
- Run governance baseline checks:
  - `python scripts/check_docs_governance.py`
  - `python scripts/check_artifact_governance.py`

---

## MVP Acceptance Criteria

The MVP is PASS when:

- Large document review no longer requires one long shared page.
- The reviewer can move through `Documents -> Rules -> BDD -> Scripts -> Evidence`.
- Active document context is preserved between tabs.
- BDD and Scripts review are integrated into the tabbed workflow.
- Existing `review-session` behavior remains available or has a documented compatibility path.
- Existing governed artifacts remain the source of truth.
- No schemas, prompts, default models, or roadmap phase boundaries are changed.
- Browser smoke covers the MVP happy path.
- Governance checks pass.

---

## Known Limitations

- MVP remains local and single-user.
- Multi-user review, permissions, role-specific queues, concurrent editing, and new artifact schemas are out of scope.
- The initial implementation should not claim production readiness for HKv14 downstream automation.
- New approval contracts should not be introduced silently. If approval states become canonical, they require a separate governed contract update.

---

## Rollback Considerations

- Keep existing `/scenario-review` route and current review-session behavior during the MVP.
- Implement the tabbed shell as a UI restructuring over existing managers and artifacts.
- Avoid changing canonical artifact formats so rollback can remove the tabbed UI without migrating data.

---

## Self-Evaluation Format

Future implementation closeout should report:

- **Change summary**
- **Roadmap phase/task mapping**
- **Acceptance items addressed**
- **Files changed**
- **Tests run or added**
- **Schema or prompt impact**
- **Known limitations**
- **Rollback considerations**
- **Self-evaluation:** PASS / PARTIAL / FAIL
