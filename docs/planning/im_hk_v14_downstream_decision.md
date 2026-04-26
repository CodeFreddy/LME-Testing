# Initial Margin HKv14 Downstream Decision

**Status:** Human accepted for POC  
**Date:** 2026-04-26  
**Reviewer:** Human project owner  
**Related diff report:** `docs/planning/im_hk_v14_diff_report.md`  
**Evidence JSON:** `evidence/im_hk_v14_diff/im_hk_v13_to_v14_diff.json`

---

## Reviewed Inputs

- `docs/materials/Initial Margin Calculation Guide HKv13.pdf`
- `docs/materials/Initial Margin Calculation Guide HKv14.pdf`
- `artifacts/im_hk_v13/`
- `artifacts/im_hk_v14/`
- `docs/planning/im_hk_v14_diff_report.md`
- `evidence/im_hk_v14_diff/im_hk_v13_to_v14_diff.json`

---

## Deterministic Diff Summary

| Metric | Value |
| --- | --- |
| HKv13 atomic rules | 164 |
| HKv14 atomic rules | 164 |
| Rule count delta | 0 |
| Changed rule candidates | 10 |
| Added rule candidates | 0 |
| Removed rule candidates | 0 |
| ID drift candidates | 1 |
| Source anchor warnings | 0 |

Rule type distribution changed:

| Rule type | HKv13 | HKv14 | Delta |
| --- | ---: | ---: | ---: |
| calculation | 122 | 120 | -2 |
| data_constraint | 13 | 13 | 0 |
| obligation | 8 | 8 | 0 |
| permission | 0 | 1 | +1 |
| reference_only | 21 | 22 | +1 |

---

## Human Review Assessment

This review is for proof-of-concept progression, not production approval.

The deterministic diff identifies 10 changed rule candidates and 1 ID-drift candidate. For POC purposes, the project owner accepts these candidate differences as sufficient evidence to proceed with downstream HKv14 impact work.

This acceptance does not mean:

- the deterministic diff is a final business interpretation,
- HKv14 calculation behavior is production-validated,
- the mock API represents a real VaR Platform, HKSCC, HKEX, or production Initial Margin engine,
- HKv13 artifacts or `deliverables/im_hk_v13_mock_api/` should be overwritten.

---

## Decision

**Decision:** Accept all HKv13/HKv14 deterministic diff candidates for POC purposes and proceed to downstream HKv14 impact work.

Approved next step:

```text
Create a governed HKv14 downstream POC task to decide and implement the minimum required BDD/mock API updates for HKv14.
```

Allowed:

- use `artifacts/im_hk_v14/` as the HKv14 governed source artifact set for POC,
- use the deterministic diff report as POC evidence,
- create HKv14-specific downstream deliverables if needed,
- preserve HKv13 as the existing baseline.

Not allowed:

- do not overwrite `artifacts/im_hk_v13/`,
- do not overwrite `deliverables/im_hk_v13_mock_api/`,
- do not claim real Initial Margin execution readiness,
- do not change schemas, prompts, or model defaults without a separate governed task,
- do not treat this POC acceptance as production business signoff.

---

## Downstream Classification

| Option | Decision |
| --- | --- |
| Option A: No material downstream behavior change | Not selected for POC. |
| Option B: Documentation/artifact update only | Not selected for POC. |
| Option C: Maker/checker/BDD rerun required | Allowed if scoped as POC. |
| Option D: New HKv14 mock API bridge required | Allowed if scoped as POC. |
| Option E: Domain clarification required | Deferred for POC; required before production claims. |

---

## Required Follow-Up

1. Define the minimum HKv14 downstream POC scope.
2. Decide whether the POC requires:
   - HKv14 BDD updates only,
   - `deliverables/im_hk_v14_mock_api/`,
   - or both.
3. Keep HKv13 bridge and HKv14 bridge separate.
4. Add tests and validation evidence for any HKv14 downstream deliverable.
5. Document mock/stub boundaries clearly.

---

## Schema, Prompt, and Model Impact

- Schema impact: none from this decision note.
- Prompt impact: none from this decision note.
- Model impact: none from this decision note.
- Artifact contract impact: none from this decision note.

Any later maker/checker/BDD or mock API implementation must document its own schema, prompt, model, and rollback impact.

---

## Rollback Considerations

This decision note is documentation-only. It can be revised or superseded after deeper domain review.

Rollback path:

- keep HKv13 artifacts and bridge as the stable baseline,
- remove or archive HKv14 POC downstream deliverables if rejected,
- keep the deterministic diff report as evidence of what was reviewed.

---

## Self-Evaluation

| Item | Status | Notes |
| --- | --- | --- |
| Diff evidence reviewed | PASS | Deterministic JSON and Markdown diff were used as inputs. |
| Downstream decision made | PASS | All candidates are accepted for POC progression. |
| HKv13 baseline preserved | PASS | Decision explicitly forbids overwriting HKv13 artifacts or bridge. |
| Schema/prompt/model impact explicit | PASS | No impact from this decision note. |
| Production boundary clear | PASS | POC acceptance is not production business signoff. |
