# Document Library and Capability Workflow Implementation Plan

**Status:** Proposed implementation plan
**Created:** 2026-04-26
**Source proposal:** `docs/planning/document_library_and_capability_workflow_proposal.md`
**Related architecture proposal:** `docs/architecture/Executable_Engineering_Knowledge_Contract.md`
**Current baseline impact:** None until tasks are implemented. This plan does not by itself change schemas, prompts, model defaults, pipeline behavior, or acceptance status.

---

## Scope

This plan turns the document library and capability workflow proposal into a small, governed implementation path for the current repository.

The broader architecture proposal defines the general MVP as:

```text
Spec Change -> Test Impact -> Automation Backlog
```

For this repository, the near-term implementation slice is:

```text
Initial Margin HKv13 -> HKv14 -> Governed Diff -> Impact Assessment -> Downstream Bridge Decision
```

This is intentionally smaller than a full document platform. It uses the HKv13/HKv14 Initial Margin guide pair to prove the core loop: versioned document intake, deterministic validation, governed diff, impact summary, and human decision before downstream implementation.

---

## Current State

| Area | Current state |
| --- | --- |
| HKv13 source | `docs/materials/Initial Margin Calculation Guide HKv13.pdf` exists. |
| HKv13 governed artifacts | `artifacts/im_hk_v13/` has metadata, pages, clauses, atomic rules, semantic rules, source markdown, and validation report. |
| HKv13 execution bridge | `deliverables/im_hk_v13_mock_api/` exists and is documented as S2-C2. |
| HKv14 source | `docs/materials/Initial Margin Calculation Guide HKv14.pdf` exists. |
| HKv14 artifacts | `artifacts/im_hk_v14/` currently only has page files; governed artifact set is incomplete. |
| Platform workflow docs | Proposal package and planning proposal exist, both marked as non-baseline future direction. |

---

## Non-Goals

The following are out of scope for this implementation plan:

- generic document upload GUI,
- multi-user document repository,
- full knowledge graph database,
- role-based access control,
- workflow composer UI,
- prompt-backed capability registry as production behavior,
- new LLM-driven stage,
- changes to maker/checker/BDD prompts,
- changes to default model or provider configuration,
- automatic creation of an HKv14 mock API bridge before the governed diff justifies it.

---

## Task Overview

```text
S2-C3.1  Complete HKv14 governed intake
S2-C3.2  Validate HKv14 artifacts and baseline governance
S2-C3.3  Create deterministic HKv13/HKv14 diff tooling
S2-C3.4  Produce governed diff and impact report
S2-C3.5  Human review decision for downstream work
S2-C3.6  Optional downstream bridge update task, only if justified
S2-C4    Future role-friendly decision UI for BA/QA/Automation review
```

---

## S2-C3.1 Complete HKv14 Governed Intake

### Goal

Produce the same governed artifact baseline for HKv14 that already exists for HKv13.

### Inputs

- `docs/materials/Initial Margin Calculation Guide HKv14.pdf`
- existing extraction script: `scripts/extract_matching_rules.py`
- existing semantic generation script: `scripts/generate_semantic_rules.py`

### Expected Outputs

- `artifacts/im_hk_v14/metadata.json`
- `artifacts/im_hk_v14/pages.json`
- `artifacts/im_hk_v14/clauses.json`
- `artifacts/im_hk_v14/atomic_rules.json`
- `artifacts/im_hk_v14/semantic_rules.json`
- `artifacts/im_hk_v14/source_from_pdf.md`
- refreshed `artifacts/im_hk_v14/pages/`

### Proposed Commands

```powershell
python scripts/extract_matching_rules.py --document-class calculation_guide --input "docs/materials/Initial Margin Calculation Guide HKv14.pdf" --input-format pdf --output-dir artifacts/im_hk_v14 --doc-id im_hk_v14 --doc-title "Initial Margin Calculation Guide HKv14" --doc-version HKv14 --write-page-text

python scripts/generate_semantic_rules.py --input artifacts/im_hk_v14/atomic_rules.json --output artifacts/im_hk_v14/semantic_rules.json --metadata artifacts/im_hk_v14/metadata.json
```

### Acceptance

- HKv14 artifact directory contains the same artifact classes as HKv13.
- Metadata identifies `doc_id: im_hk_v14`, `doc_version: HKv14`, and `document_class: calculation_guide`.
- HKv13 artifacts remain unchanged.

### Self-Evaluation Target

PASS only if all expected HKv14 artifacts exist and HKv13 baseline artifacts are preserved.

---

## S2-C3.2 Validate HKv14 Artifacts and Baseline Governance

### Goal

Prove HKv14 artifacts are structurally valid before any downstream comparison or generation.

### Inputs

- `artifacts/im_hk_v14/atomic_rules.json`
- `artifacts/im_hk_v14/semantic_rules.json`
- existing validation script: `scripts/validate_rules.py`

### Expected Outputs

- `artifacts/im_hk_v14/validation_report.json`
- passing governance baseline checks

### Proposed Commands

```powershell
python scripts/validate_rules.py --input artifacts/im_hk_v14/atomic_rules.json --semantic-rules artifacts/im_hk_v14/semantic_rules.json --output artifacts/im_hk_v14/validation_report.json --fail-on-error

python scripts/check_docs_governance.py
python scripts/check_artifact_governance.py
```

### Acceptance

- Validation report exists and indicates no blocking schema or rule-type failures.
- Docs governance passes.
- Artifact governance passes.
- Any validation failure is fixed or documented as a blocker; failures must not be hidden.

### Self-Evaluation Target

PASS only if validation and baseline governance pass.

---

## S2-C3.3 Create Deterministic HKv13/HKv14 Diff Tooling

### Goal

Create a deterministic comparison script for Initial Margin governed artifacts.

### Proposed File

- `scripts/compare_initial_margin_versions.py`

### Inputs

- previous artifact directory, such as `artifacts/im_hk_v13/`
- current artifact directory, such as `artifacts/im_hk_v14/`
- optional output path

### Expected Outputs

The script should write a structured JSON report and a human-readable Markdown report.

Suggested files:

- `docs/planning/im_hk_v14_diff_report.md`
- `evidence/im_hk_v14_diff/im_hk_v13_to_v14_diff.json`

### Minimum JSON Sections

```text
metadata
source_versions
artifact_inventory
rule_count_delta
rule_type_distribution_delta
clause_delta
paragraph_id_delta
changed_rule_candidates
added_rule_candidates
removed_rule_candidates
source_anchor_warnings
downstream_impact_candidates
limitations
```

### Implementation Notes

- Prefer deterministic comparison of normalized governed artifacts.
- Do not use LLM analysis for the first version of the diff.
- Compare by stable keys where available: `rule_id`, `paragraph_id`, `clause_id`, and normalized `raw_text`.
- Preserve source anchors and show when anchors changed or disappeared.
- Treat unmatched or changed anchors as review candidates, not automatic business conclusions.

### Acceptance

- Script can compare HKv13 and HKv14 artifact directories.
- Script emits valid JSON and Markdown.
- Script does not mutate input artifacts.
- Unit tests cover at least added, removed, changed, and unchanged rule candidates.

### Self-Evaluation Target

PASS only if deterministic diff output and focused tests exist.

---

## S2-C3.4 Produce Governed Diff and Impact Report

### Goal

Generate a reviewable HKv13/HKv14 report that separates evidence from interpretation.

### Inputs

- completed HKv13 artifacts,
- completed HKv14 artifacts,
- `scripts/compare_initial_margin_versions.py`

### Expected Outputs

- `docs/planning/im_hk_v14_diff_report.md`
- `evidence/im_hk_v14_diff/im_hk_v13_to_v14_diff.json`

### Report Sections

The Markdown report should include:

- source documents compared,
- artifact inventories,
- validation status,
- rule count and rule-type changes,
- added/removed/changed candidate rules,
- source-anchor changes,
- likely downstream impact areas,
- explicit unknowns and review needs,
- recommendation on whether downstream maker/checker/BDD/mock API work is needed.

### Acceptance

- Report is generated from deterministic artifacts.
- Report avoids claiming semantic/business meaning where deterministic evidence is insufficient.
- Report clearly marks review-needed items.
- Report recommends one of:
  - no downstream bridge changes needed,
  - update existing HKv13 bridge documentation only,
  - create `deliverables/im_hk_v14_mock_api/`,
  - defer pending human review.

### Self-Evaluation Target

PASS only if the report is reviewable and source-evidence grounded.

---

## S2-C3.5 Human Review Decision for Downstream Work

### Goal

Require a human decision before treating HKv14 as a new execution bridge task.

### Inputs

- `docs/planning/im_hk_v14_diff_report.md`
- `evidence/im_hk_v14_diff/im_hk_v13_to_v14_diff.json`

### Expected Output

One planning record or review note documenting the decision.

Suggested file:

- `docs/planning/im_hk_v14_downstream_decision.md`

### Decision Options

```text
Option A: HKv14 has no material downstream behavior change.
Option B: HKv14 requires documentation and artifact updates only.
Option C: HKv14 requires maker/checker/BDD rerun.
Option D: HKv14 requires a new mock API bridge.
Option E: HKv14 requires human domain clarification before downstream work.
```

### Acceptance

- Decision is repo-readable.
- Decision references the diff report.
- Decision names known limitations.
- Decision does not silently redefine HKv13 bridge scope.

### Self-Evaluation Target

PASS only if downstream work is explicitly approved or deferred with reasons.

---

## S2-C3.6 Optional Downstream Bridge Update

### Goal

Implement HKv14 downstream execution bridge work only if S2-C3.5 justifies it.

### Possible Outputs

If approved:

- `deliverables/im_hk_v14_mock_api/`
- `deliverables/im_hk_v14_mock_api.zip`
- `docs/planning/im_hk_v14_mock_api_validation_plan.md`
- tests for the HKv14 bridge

### Constraints

- Do not overwrite `deliverables/im_hk_v13_mock_api/`.
- Do not claim real VaR Platform, HKSCC, HKEX, or production Initial Margin readiness.
- Do not change schemas, prompts, or model defaults unless a separate governed task approves it.

### Acceptance

Acceptance must be defined after the HKv13/HKv14 diff is known. It should include compile checks, HTTP-backed BDD runner checks, unit tests, and explicit mock/stub boundary documentation.

### Self-Evaluation Target

PARTIAL until human review approves this optional task and acceptance criteria are finalized.

---

## S2-C4 Future Role-Friendly Decision UI

### Goal

Provide a friendly local UI for BA, QA Lead, Automation Lead and similar role owners to record review decisions without editing Markdown directly.

This task is intentionally future scope. The current HKv14 POC may use Markdown decision notes, but the incoming larger plan should treat role-friendly decision capture as a first-class requirement.

### Inputs

- governed diff reports,
- checker reports when available,
- candidate artifacts,
- source evidence links,
- role and reviewer metadata.

### Expected Outputs

- structured human review records,
- exported Markdown decision notes if needed,
- audit metadata containing reviewer role, reviewer name, timestamp, decision, rationale and linked evidence,
- visible decision status for each candidate item.

### Minimum UI Capabilities

The UI should let reviewers:

- filter by role, artifact, changed candidate and decision status,
- view evidence and candidate output side by side,
- classify each candidate as accepted, rejected, deferred or rework required,
- add comments and rationale,
- approve or reject downstream progression,
- export or persist the decision in repo-readable form.

### Non-Goals

- no hosted multi-user workflow in the first version,
- no enterprise permission model in the first version,
- no automatic approval by LLM,
- no replacement of governed JSON/Markdown artifacts as the durable record.

### Acceptance Direction

PASS when a local reviewer can record and persist decisions for a governed diff or candidate artifact, and the resulting decision record can be reviewed from the repo without relying on hidden UI state.

---

## Testing Strategy

Minimum tests and checks by task:

| Task | Required checks |
| --- | --- |
| S2-C3.1 | Artifact existence and metadata spot check. |
| S2-C3.2 | `validate_rules.py`, `check_docs_governance.py`, `check_artifact_governance.py`. |
| S2-C3.3 | Unit tests for deterministic diff categories. |
| S2-C3.4 | Generated JSON and Markdown report review. |
| S2-C3.5 | Review note exists and references diff evidence. |
| S2-C3.6 | Compile, unit, and HTTP-backed BDD tests if bridge is created. |
| S2-C4 | UI/form save tests plus generated review record validation when implemented. |

---

## Schema, Prompt, and Model Impact

Expected near-term impact:

- **Schema impact:** None for S2-C3.1 through S2-C3.5.
- **Prompt impact:** None for S2-C3.1 through S2-C3.5.
- **Model impact:** None for S2-C3.1 through S2-C3.5.
- **Pipeline impact:** New deterministic comparison script only.

If later tasks add LLM-backed capability definitions, they must be handled as separate governed work with schemas, prompt versions, benchmark evidence, traceability, and rollback notes.

---

## Rollback Considerations

Rollback should be simple for the near-term tasks:

- Remove generated HKv14 artifacts if intake must be redone.
- Remove deterministic diff script and reports if the approach is rejected.
- Keep HKv13 artifacts and HKv13 mock API bridge unchanged.
- Do not remove HKv14 source PDF unless explicitly requested.

---

## Open Questions

1. Should HKv14 artifact generation preserve the current partially generated `artifacts/im_hk_v14/pages/`, or should the intake command refresh it fully?
2. Should diff evidence live under `evidence/im_hk_v14_diff/` or a date-stamped evidence directory?
3. Should the downstream decision be a standalone planning note or added to the diff report as an approval section?
4. Are there HKv14 domain-specific examples that must be manually checked before deciding whether a new mock API bridge is needed?

---

## Required Closeout Format

Any implementation PR or handoff for this plan should include:

- change summary,
- roadmap mapping,
- acceptance items addressed,
- files changed,
- tests run or added,
- schema or prompt impact,
- known limitations,
- rollback considerations,
- PASS / PARTIAL / FAIL self-evaluation.
