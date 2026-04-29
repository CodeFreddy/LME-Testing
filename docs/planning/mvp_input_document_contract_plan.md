# MVP Input Document Contract Plan

**Status:** Implemented deterministic S2-F3 slice  
**Created:** 2026-04-29  
**Implemented:** 2026-04-29  
**Task ID:** S2-F3  
**Source:** Follow-on from `docs/planning/mvp_document_readiness_plan.md` and the S2-F2 readiness blockers  
**Baseline impact:** This slice extends deterministic document readiness generation to accept optional real Test Plan and Regression Pack Index inputs. It does not change schemas, prompts, default models, maker/checker pipeline behavior, review-session behavior, or Stage 3 readiness claims.

---

## Purpose

S2-F2 implemented a deterministic document readiness registry for the MVP workflow. The registry is intentionally blocked because two required MVP inputs are placeholders:

- Test Plan
- Regression Pack Index

S2-F3 should define the minimum acceptable input contract for those two document classes before any implementation claims they are ready.

This is a contract-definition slice, not a document-ingestion or mapping implementation.

---

## In Scope

- Define what counts as a minimally valid Test Plan input for this MVP.
- Define what counts as a minimally valid Regression Pack Index input for this MVP.
- Define required metadata that the readiness registry should expect when real files are provided.
- Define deterministic validation expectations for future implementation.
- Define fixture expectations for valid and invalid examples.
- Keep the contract compatible with the existing S2-F2 `document_readiness.json` shape.

---

## Out Of Scope

- Creating real Test Plan or Regression Pack Index documents.
- Auto-generating Test Plan or Regression Pack Index contents.
- Generic upload UI or document storage platform.
- OCR, parser, or LLM extraction work.
- Requirement-to-test mapping.
- Regression impact mapping.
- Automation backlog generation.
- JIRA, Zephyr, Git, CI, Confluence, or SharePoint integration.
- Prompt, model, schema, or maker/checker behavior changes.
- Stage 3 real execution readiness claims.

---

## Minimum Test Plan Contract

A real Test Plan document can be marked `ready` only if its registry record and source content support the following metadata and operator review expectations.

### Required Registry Metadata

```text
document_id
title
version
document_class = Test Plan
document_role = test_plan
source_path
source_exists = true
owner_role = QA Lead
status = registered
checksum
readiness_state = ready
missing_required_fields = []
notes
```

### Minimum Content Expectations

The source document should identify, in human-readable form:

- test objective or scope,
- target system or domain,
- applicable function/specification version,
- in-scope test levels or types,
- out-of-scope items or exclusions,
- responsible QA owner or approving role,
- revision/version marker.

### Readiness Rules

- Missing source path blocks readiness.
- Missing source file blocks readiness.
- Missing checksum blocks readiness.
- Missing title, version, owner role, or document role blocks readiness.
- A Test Plan may be marked `ready` without requirement-to-test mapping; mapping is later scope.
- Ambiguous or incomplete content should be recorded as `blocked`, not silently coerced to ready.

---

## Minimum Regression Pack Index Contract

A real Regression Pack Index document can be marked `ready` only if its registry record and source content support the following metadata and operator review expectations.

### Required Registry Metadata

```text
document_id
title
version
document_class = Regression Pack Index
document_role = regression_pack_index
source_path
source_exists = true
owner_role = Automation Lead
status = registered
checksum
readiness_state = ready
missing_required_fields = []
notes
```

### Minimum Content Expectations

The source document should identify, in human-readable form:

- regression pack name or identifier,
- target system or domain,
- applicable function/specification version or release baseline,
- list of regression suites, scenarios, scripts, or cases,
- owner or maintaining role,
- revision/version marker,
- explicit note when automation coverage is partial or unknown.

### Readiness Rules

- Missing source path blocks readiness.
- Missing source file blocks readiness.
- Missing checksum blocks readiness.
- Missing title, version, owner role, or document role blocks readiness.
- A Regression Pack Index may be marked `ready` without impact analysis; impact analysis is later scope.
- Partial automation coverage is allowed only if visible in notes or source content.

---

## Future Implementation Expectations

The implementation slice remains deterministic and does:

- allow real Test Plan and Regression Pack Index paths to be passed into the S2-F2 readiness generator,
- validate role, state, source existence, and hash deterministically,
- preserve placeholder behavior when the files are not provided,
- reject `ready` records that lack required metadata or existing sources,
- add focused tests for valid real document inputs, missing source failure, and placeholder fallback.

It should not parse detailed test mappings or infer regression impact.

---

## Acceptance Gates

S2-F3 is PASS only if:

- [x] the minimum Test Plan input contract is documented,
- [x] the minimum Regression Pack Index input contract is documented,
- [x] readiness and blocking rules are explicit,
- [x] implementation preserves S2-F2 boundaries,
- [x] `mvp-document-readiness` accepts optional real Test Plan and Regression Pack Index paths,
- [x] placeholder behavior is preserved when those files are not provided,
- [x] focused tests cover valid real document inputs, missing source failure, incomplete content blocking, and placeholder fallback,
- [x] non-goals exclude mapping, generation, LLM stages, integrations, and Stage 3 readiness claims,
- [x] docs and artifact governance pass.

---

## Rollback Considerations

This slice is rollback-safe:

- remove the S2-F3 optional-input changes from `src/lme_testing/mvp_document_readiness.py`, `src/lme_testing/cli.py`, and `tests/test_mvp_document_readiness.py`,
- remove generated S2-F3 evidence under `evidence/mvp_document_readiness/20260429T083211Z/`,
- remove S2-F3 references from roadmap, implementation plan, TODO, index, handoff, and checkpoints,
- preserve S2-F2 implementation and evidence.

---

## Implementation Evidence

- Generator: `src/lme_testing/mvp_document_readiness.py`
- CLI: `python main.py mvp-document-readiness --test-plan <path> --regression-pack-index <path>`
- Default evidence preserving placeholder blockers: `evidence/mvp_document_readiness/20260429T083211Z/`
- Tests: `tests/test_mvp_document_readiness.py`

## Self-Evaluation Target

Current implementation status: PASS.

Default workflow readiness remains blocked until real Test Plan and Regression Pack Index sources are provided.
