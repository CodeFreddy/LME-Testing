# UI Test Plan

## Purpose

This plan verifies the governed review UI flow from source-derived artifacts to BDD and script review artifacts.

It is limited to the existing documented pipeline and UI behavior. It does not introduce new product scope or new LLM stages.

## Flow Under Test

The UI flow is:

1. PDF or Markdown source is transformed into governed JSON artifacts.
2. Semantic JSON feeds maker and checker outputs.
3. Review UI loads maker/checker results for human review.
4. BDD tab loads normalized BDD and saves human BDD edits.
5. Scripts tab loads step visibility and saves human step review edits.
6. Save operations refresh reviewed BDD and step visibility artifacts.
7. Submit uses the latest human review artifacts for the next rewrite/checker iteration.

The canonical editable outputs are governed artifacts, not rendered UI text.

## Required UI Logic Assertions

### Source To Review

- The session payload exposes the initial maker, checker, coverage, BDD, and step visibility artifact paths when present.
- Missing optional BDD or step visibility artifacts must produce explicit `has_bdd=false` or `has_registry=false` payloads rather than silent empty success.
- Stage gates must remain visible and deterministic.

### BDD Tab

- `/api/bdd` must load normalized BDD from the current session state.
- Saving BDD edits must write:
  - `human_bdd_edits_latest.json` as the BDD-tab audit artifact,
  - `human_scripts_edits_latest.json` as the pipeline-compatible flattened edit artifact,
  - `reviewed_normalized_bdd_latest.jsonl` as the reviewed BDD artifact.
- After a BDD edit, the session state must point BDD reads at the reviewed BDD artifact while preserving the original source normalized BDD path.
- BDD edits must not delete existing Scripts-tab edits.

### Scripts Tab

- `/api/scripts` must load the current step visibility artifact from session state.
- Saving Scripts edits must write `human_scripts_edits_latest.json`.
- Saving Scripts edits must preserve prior BDD-tab flattened scenario edits.
- Gap edits must include or be enriched with:
  - `step_type`,
  - `source_scenario_ids`,
  - original step text or pattern.
- Saving Scripts edits must refresh:
  - `reviewed_normalized_bdd_latest.jsonl`,
  - `step_visibility_latest.json`.
- Matching counters such as exact, parameterized, candidate, and unmatched counts must update after the save.

### Submit And Iteration

- Submit must use the latest human review and step edit artifacts.
- A new iteration must carry forward explicit artifact paths in the session manifest.
- Finalized sessions must reject further edit saves unless the workflow explicitly reopens for a new iteration.

## Automated Coverage

### Manager-Level Tests

Implemented in `tests/test_review_session.py`.

Required cases:

- saving review decisions writes snapshot and latest review artifacts;
- submitting reviews advances iteration and generates report links;
- finalizing locks the session against edits;
- saving BDD edits materializes reviewed BDD and refreshes step visibility;
- saving a Scripts gap edit updates reviewed BDD and refreshes matching metrics;
- saving Scripts edits preserves prior BDD-tab flattened edits.

These tests exercise the UI backend contract without a browser.

### HTTP Contract Tests

The next automation layer should start the review server with temporary fixtures and call:

- `GET /api/session`,
- `GET /api/bdd`,
- `POST /api/bdd/save`,
- `GET /api/scripts`,
- `POST /api/scripts/save`,
- `GET /api/stage`.

Assertions should compare HTTP payloads with the artifacts written to disk.

### Browser E2E Tests

Implemented in `tests/test_review_session_browser.py`.

The suite uses a real local review-session HTTP server and drives an installed Chromium-family browser through the Chrome DevTools Protocol. It uses deterministic fixture artifacts and does not call a live LLM provider.

Current browser assertions:

- opens the review UI,
- moves from Review to BDD to Scripts,
- edits one BDD step,
- saves BDD edits,
- verifies the Scripts tab reloads refreshed match metrics,
- edits one step text,
- saves Scripts edits,
- verifies unmatched or exact counts update in the visible UI,
- verifies no textareas lose unsaved data during tab navigation.

## Acceptance

The UI flow is acceptable when:

- all manager-level tests pass;
- HTTP contract tests cover save and reload behavior for BDD and Scripts artifacts;
- browser E2E tests cover the primary human path when a browser runner is available;
- governance checks pass:
  - `python scripts/check_docs_governance.py`
  - `python scripts/check_artifact_governance.py`

## Known Limits

- Browser E2E coverage requires an installed Chrome or Edge executable. The test is skipped when no browser is available.
- Scripts-tab edits are step text and mapping review edits, not direct Python implementation editing.
- The original normalized BDD artifact remains the source artifact; reviewed BDD is an iteration-local reviewed artifact produced from human edits.
