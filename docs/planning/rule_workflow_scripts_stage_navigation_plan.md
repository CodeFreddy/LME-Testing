# Rule Workflow Scripts and Stage Navigation Plan

**Status:** Proposed S2-F7
**Date:** 2026-05-07
**Scope:** HKv14 rule workflow GUI POC, Scripts view, stage navigation, and mock API step-definition bridge

## Purpose

This plan records three UX and workflow gaps found during the HKv14 end-to-end rule workflow POC:

1. The Scripts view does not show executable API-backed step definitions under BDD steps.
2. The workflow stages cannot be revisited or jumped between without restarting from the beginning.
3. Steps that are not in a usable match state, especially `unmatched`, do not provide a controlled way to generate or attach matching step definitions.

The goal is to make the HKEX AI Assisted Workflow easier to inspect and iterate while keeping governed artifacts, validation gates, and mock/stub boundaries visible.

## Boundaries

This plan is limited to the HKv14 POC/mock/stub bridge and the rule workflow GUI.

It does not:

- claim HKv14 production downstream automation readiness,
- change artifact schemas,
- change prompts,
- change default models,
- introduce a new LLM stage,
- promote generated step definitions as trusted without human review,
- replace the HKv13 mock API preservation baseline,
- hide unmatched, stale, or failed integration states.

## Track 1: Show API-Backed Step Definitions in Scripts View

### Current Gap

The Scripts view shows step matching status and step registry information, but it does not show the executable definition behind a matched or candidate step. Users cannot see which Python function, API endpoint, payload setup, or assertion makes a BDD step executable.

### Target Behavior

Each Scripts view step should support an expandable definition panel showing:

- BDD step text,
- match state: `exact`, `parameterized`, `candidate`, or `unmatched`,
- matched step pattern,
- Python function name,
- source file path,
- implementation snippet,
- detected API endpoint call such as `POST /margin/aggregate`,
- payload or fixture setup source,
- response assertion details for `Then` steps,
- provenance linking the step to its semantic rule and scenario.

For HKv14, the first executable step library source should include:

- `deliverables/im_hk_v14_mock_api/features/step_definitions/initial_margin_steps.py`
- `deliverables/im_hk_mock_api_common/im_hk_mock_api_common/steps.py`
- `deliverables/im_hk_mock_api_common/im_hk_mock_api_common/client.py`

### Implementation Notes

- Extend step registry processing to resolve implementation metadata from Python step definition files.
- Parse decorators and function bodies using Python's `ast` module where possible.
- Detect mock API calls through `context.client.post(...)` and `context.client.get(...)`.
- Preserve the current step match result rather than replacing it with implementation metadata.
- Update `/api/scripts` to return implementation details when available.
- Update the Scripts tab to render the expandable definition panel.

### Acceptance Criteria

- A matched step such as `the margin is aggregated` shows that it calls `POST /margin/aggregate`.
- The UI shows the source function and file path.
- The UI shows assertion-relevant implementation for `Then` steps.
- Missing definitions remain visible as gaps.
- Existing step registry output remains backward compatible or has an explicitly governed migration path.

## Track 2: Generate Matching Step Definitions for Non-Candidate Gaps

### Current Gap

Steps outside a usable match state, especially `unmatched`, have no direct path forward from the Scripts view. Users can see that a step does not bind, but cannot generate, attach, or review a matching implementation.

### Target Behavior

For every step that is not currently executable, the Scripts view should offer controlled actions:

- `Generate step definition`
- `Attach to existing API endpoint`
- `Create stub only`
- `Mark as intentionally manual / out of scope`

Generated step definitions must be draft artifacts first. They must not silently become canonical executable code.

### Generated Artifact Shape

Draft generation should produce reviewable files such as:

- `generated_step_definitions/draft_steps.py`
- `generated_step_definitions/step_generation_manifest.json`

The manifest should record:

- source BDD step text,
- step type: `given`, `when`, or `then`,
- scenario ID,
- semantic rule ID,
- selected API endpoint if any,
- source artifacts used,
- generation timestamp,
- human approval status,
- reviewer notes,
- promotion target if approved.

### Implementation Notes

- Add a Scripts view action for `unmatched`, low-confidence, or otherwise unusable steps.
- Let the user select or confirm:
  - target API endpoint,
  - payload fixture or setup source,
  - expected response assertion,
  - whether the output is an executable implementation or a stub.
- Generate code as a proposal.
- Show the generated diff in the GUI before promotion.
- Refresh the step registry after a generated step is approved or attached.

### Acceptance Criteria

- An `unmatched` step has a visible generate action.
- Generated code is shown before promotion.
- The generated manifest records provenance and approval state.
- Generated code is not automatically treated as trusted.
- Refreshing the step registry can move a step from `unmatched` to `exact`, `parameterized`, or `candidate`.
- Binding or execution failures remain visible.

## Track 3: Navigate Between Workflow Stages Without Restarting

### Current Gap

The rule workflow GUI behaves as a mostly linear path. After reaching later stages, users cannot freely revisit Rule Extraction, Scenario Review, BDD Review, Scripts, or Finalize without restarting.

### Target Behavior

The GUI should support stage navigation across:

1. Rule Extraction
2. Scenario Review
3. BDD Review
4. Scripts / Step Integration
5. Finalize

Backward navigation should be allowed freely. Forward navigation should be gated by prerequisite artifacts.

### Artifact Readiness Model

The session should track readiness for:

- uploaded source,
- extracted rules,
- reviewed rules,
- generated cases,
- generated BDD,
- step registry,
- finalized report.

The session should also track stale downstream state when upstream artifacts are edited.

### Stale-State Rules

- Editing extracted or reviewed rules marks generated cases, BDD, Scripts, and Finalize as stale.
- Editing scenarios marks BDD, Scripts, and Finalize as stale.
- Editing BDD marks Scripts and Finalize as stale.
- Editing generated or attached step definitions marks Scripts and Finalize as needing refresh.
- Finalized artifacts remain immutable snapshots.
- Post-finalize edits should create a new iteration or require an explicit reopen/new revision action.

### Implementation Notes

- Add stage navigation controls to the GUI.
- Add or extend `/api/stage` to expose current stage, readiness, stale state, and allowed transitions.
- Add explicit regeneration actions:
  - `Regenerate cases from reviewed rules`
  - `Regenerate BDD from current cases`
  - `Refresh scripts from current BDD`
  - `Finalize current session`
- Keep stale artifacts inspectable, but visibly marked.

### Acceptance Criteria

- A user can return to Stage 1 after reaching Stage 4 without restarting.
- A user can jump to Stage 4 if prerequisite BDD and step registry artifacts already exist.
- Forward navigation is blocked with a visible prerequisite message when required artifacts are missing.
- Stale downstream artifacts are clearly marked.
- Final reports are not silently mutated by later edits.

## Suggested Delivery Order

1. Add Scripts view implementation metadata for existing API-backed step definitions.
2. Add generation and attach actions for unmatched or unusable steps.
3. Add stage navigation and readiness state.
4. Add stale-state invalidation and explicit regeneration controls.
5. Add HTTP and browser-level tests for the complete navigation and Scripts workflow.

## Test Plan

Minimum focused tests:

- manager-level tests for step implementation metadata extraction,
- HTTP tests for `/api/scripts` implementation details,
- HTTP tests for generation draft artifact creation,
- HTTP tests for `/api/stage` readiness and stale-state transitions,
- browser-level tests for Scripts definition expansion and generate action visibility,
- browser-level tests for stage navigation from Rule Extraction through Finalize.

Governance baseline:

```text
python scripts/check_docs_governance.py
python scripts/check_artifact_governance.py
```

## Rollback Considerations

- Scripts view additions should be feature-local and removable without affecting governed artifacts.
- Generated step definitions should remain draft artifacts until explicitly approved.
- Stage navigation should preserve the existing linear path as a valid default.
- Finalized reports and manifests must remain immutable to make rollback auditable.

## Self-Evaluation Template

- Track 1: PASS / PARTIAL / FAIL
- Track 2: PASS / PARTIAL / FAIL
- Track 3: PASS / PARTIAL / FAIL
- Schema impact: expected none unless separately approved
- Prompt impact: expected none unless separately approved
- Model impact: expected none unless separately approved
- Production readiness claim: none
