# MVP Document Readiness Registry Plan

**Status:** Implemented deterministic S2-F2 slice
**Created:** 2026-04-27
**Implemented:** 2026-04-29
**Task ID:** S2-F2
**Source proposal:** `docs/architecture/Executable_Engineering_Knowledge_Contract.md` section "03 MVP Scope and Delivery Plan"
**Baseline impact:** This slice adds deterministic registry generation only. It does not change schemas, prompts, default models, pipeline behavior, review-session behavior, or Stage 3 readiness claims.

---

## Purpose

Promote the next small MVP slice from the broader Executable Engineering Knowledge Contract proposal into governed roadmap scope.

S2-F1 proved the role-friendly review and structured decision-record part of the MVP using the HKv13 -> HKv14 Initial Margin POC.

S2-F2 should establish the deterministic input contract for future MVP work:

```text
Register MVP documents -> validate metadata/readiness -> produce document_readiness.json
```

This maps to MVP scope items 1-5:

```text
1. Upload or register Function Spec old version.
2. Upload or register Function Spec new version.
3. Upload or register Test Plan.
4. Upload or register Regression Pack Index.
5. Validate document metadata and readiness.
```

For this repository, the first implementation should remain HKv13/HKv14-focused and deterministic.

---

## In Scope

- Define a small document readiness registry artifact for one MVP workflow instance.
- Register the existing HKv13 and HKv14 Initial Margin guide documents as the old/new version pair.
- Allow placeholder records for Test Plan and Regression Pack Index without pretending they exist.
- Capture deterministic metadata:
  - document id,
  - title,
  - version,
  - document class,
  - source path,
  - source exists,
  - owner role,
  - status,
  - supersedes relationship,
  - checksum or content hash when source exists,
  - readiness state,
  - missing fields or blockers.
- Add deterministic validation and focused tests.
- Preserve generated evidence under `evidence/`.

---

## Out Of Scope

- Generic document upload UI.
- Document storage platform.
- OCR or new parser work.
- LLM extraction, LLM summarization, or maker/checker changes.
- Requirement-to-test mapping.
- Regression-pack mapping.
- Automation backlog generation.
- Role-based permissions.
- JIRA, Zephyr, Git, CI, Confluence, or SharePoint integration.
- Stage 3 real execution readiness claims.

---

## Proposed Artifact Contract

Suggested output:

```text
evidence/mvp_document_readiness/<timestamp>/
  document_readiness.json
  document_readiness_summary.md
```

Minimum top-level fields:

```text
metadata
workflow_instance
documents
relationships
readiness_summary
blockers
limitations
```

Each document record should include:

```text
document_id
title
version
document_class
document_role
source_path
source_exists
owner_role
status
checksum
supersedes
readiness_state
missing_required_fields
notes
```

Allowed `document_role` values for the first version:

```text
function_spec_previous
function_spec_current
test_plan
regression_pack_index
automation_feature_index
```

Allowed `readiness_state` values:

```text
ready
placeholder
blocked
```

---

## Initial HKv14 POC Registry

The first S2-F2 implementation should register:

| Document role | Initial document |
| --- | --- |
| `function_spec_previous` | `docs/materials/Initial Margin Calculation Guide HKv13.pdf` |
| `function_spec_current` | `docs/materials/Initial Margin Calculation Guide HKv14.pdf` |
| `test_plan` | placeholder, not available |
| `regression_pack_index` | placeholder, not available |

The plan intentionally uses Initial Margin calculation guides as the repository-specific stand-in for the broader proposal's "Function Spec" concept.

---

## Acceptance Gates

S2-F2 is PASS only if:

- `document_readiness.json` is generated deterministically.
- HKv13 and HKv14 source files are registered with existing-source checks and hashes.
- Placeholder Test Plan and Regression Pack Index records are explicit and marked `placeholder` or `blocked`.
- Missing inputs are visible in `blockers`; they are not silently ignored.
- The HKv13 -> HKv14 supersedes relationship is represented.
- Deterministic validation rejects unsupported roles, unsupported readiness states, missing required metadata, and missing sources marked as ready.
- Focused tests cover valid registry generation, missing source handling, placeholder handling, and validation failure.
- Docs and artifact governance checks pass.

---

## Rollback Considerations

The slice should be rollback-safe:

- Remove the S2-F2 registry generator and tests.
- Remove generated `evidence/mvp_document_readiness/<timestamp>/` artifacts.
- Preserve S2-F1 evidence and all HKv13/HKv14 governed artifacts.
- Preserve the broader proposal as proposal material.

---

## Implementation Evidence

- Generator: `src/lme_testing/mvp_document_readiness.py`
- CLI: `python main.py mvp-document-readiness`
- Evidence: `evidence/mvp_document_readiness/20260429T075702Z/`
- Tests: `tests/test_mvp_document_readiness.py`

## Self-Evaluation Target

Current implementation status: PASS.

Workflow readiness remains blocked because Test Plan and Regression Pack Index are explicit placeholders.
