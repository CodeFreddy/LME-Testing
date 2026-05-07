# Initial Margin HKv14 Promotion Scope

**Status:** Completed scoped implementation slice
**Decision date:** 2026-04-26
**Promotion basis:** `docs/planning/im_hk_v14_downstream_decision.md`
**POC evidence:** `docs/planning/im_hk_v14_diff_report.md` and `docs/planning/im_hk_v14_mock_api_validation_plan.md`

---

## Decision

HKv14 is promoted from POC-only continuation into a governed Stage 2 implementation slice.

This promotion authorizes the minimum implementation work needed to make HKv14 a reviewable downstream baseline candidate for the Initial Margin mock/stub bridge.

This promotion does not authorize production readiness claims, Stage 3 real execution claims, prompt/model changes, schema changes, or replacement of the HKv13 preservation baseline.

---

## Scope

The promoted slice is limited to:

1. keep `artifacts/im_hk_v14/` as the governed HKv14 source artifact set,
2. preserve deterministic HKv13→HKv14 diff evidence under `evidence/im_hk_v14_diff/`,
3. maintain `deliverables/im_hk_mock_api_common/` as the shared implementation package,
4. maintain `deliverables/im_hk_v14_mock_api/` as the HKv14 wrapper,
5. add or refine HKv14-specific tests only where deterministic diff candidates require visible downstream coverage,
6. keep HKv13 and HKv14 validation runnable side by side,
7. document all validation evidence and residual limitations.

---

## Contracts

### Inputs

- `docs/materials/Initial Margin Calculation Guide HKv14.pdf`
- `artifacts/im_hk_v14/`
- `artifacts/im_hk_v13/`
- `evidence/im_hk_v14_diff/im_hk_v13_to_v14_diff.json`
- `docs/planning/im_hk_v14_downstream_decision.md`
- `deliverables/im_hk_v13_mock_api/`
- `deliverables/im_hk_mock_api_common/`
- `deliverables/im_hk_v14_mock_api/`

### Outputs

- updated HKv14 wrapper tests or BDD samples when required by accepted diff candidates,
- updated validation note in `docs/planning/im_hk_v14_mock_api_validation_plan.md`,
- refreshed handoff/checkpoint documentation when implementation changes are made,
- optional updated zip deliverable if HKv14 wrapper code or data changes.

### Non-Outputs

- no schema changes,
- no prompt changes,
- no default model changes,
- no new LLM-driven stage,
- no production Initial Margin engine,
- no real VaR Platform, HKSCC, HKEX, or Stage 3 execution integration.

---

## Acceptance Gates

The promoted slice reaches PASS only when:

- HKv13 deliverable remains unmodified except for explicitly documented shared compatibility work,
- HKv13 and HKv14 mock API tests both pass,
- HKv14 BDD runner passes all included feature steps,
- at least one validation artifact or note maps accepted HKv13→HKv14 deterministic diff candidates to downstream treatment,
- docs governance and artifact governance checks pass,
- schema/prompt/model impact remains explicitly none, or a separate governed change is opened before any such impact is introduced.

PARTIAL is allowed only if residual diff candidates are explicitly deferred with reason and next action.

FAIL applies if HKv13 is overwritten, contracts are weakened, validation advisories are hidden, or HKv14 readiness is overstated.

---

## Rollback

Rollback is limited to the promoted HKv14 downstream slice:

- revert HKv14 wrapper changes,
- remove or regenerate `deliverables/im_hk_v14_mock_api.zip`,
- preserve `artifacts/im_hk_v14/` and `evidence/im_hk_v14_diff/` as reviewed evidence unless explicitly superseded,
- keep `deliverables/im_hk_v13_mock_api/` as the stable baseline.

---

## Completed S2-C4 Action

Map the 10 accepted HKv13→HKv14 changed candidates and 1 ID drift candidate to downstream treatment categories:

- already covered by shared mock bridge,
- requires HKv14-specific BDD/data/test update,
- advisory/reference-only with no executable downstream change,
- deferred pending domain clarification.

Completed in `docs/planning/im_hk_v14_downstream_treatment_mapping.md`.

The mapping found one required HKv14 wrapper update: refresh the flat-rate validation data from the HKv13 two-term example to the HKv14 three-term example while keeping the same expected margin of `15,180,000`.

---

## Self-Evaluation

| Item | Status | Notes |
| --- | --- | --- |
| Human promotion captured | PASS | User explicitly approved promotion on 2026-04-26. |
| Scope bounded | PASS | Stage 2 downstream candidate only; no production or Stage 3 claim. |
| Contracts named | PASS | Inputs, outputs, non-outputs, gates, and rollback are listed. |
| HKv13 preservation protected | PASS | HKv13 deliverable remains the stable baseline. |
| Next implementation action deterministic | PASS | Diff candidate mapping was completed before mock behavior changes. |
| HKv14 validation updated | PASS | HKv14 flat-rate validation data now uses the HKv14 three-term example. |
