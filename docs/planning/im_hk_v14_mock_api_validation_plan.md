# Initial Margin HKv14 Mock API Validation Plan

**Status:** Promoted S2-C4 validation plan
**Created:** 2026-04-26
**Canonical owner:** `docs/planning/implementation_plan.md` section S2-C4 and `docs/governance/acceptance.md` Gate S2.7
**Related roadmap task:** S2-C4
**Related decision:** `docs/planning/im_hk_v14_downstream_decision.md`
**Related diff:** `docs/planning/im_hk_v14_diff_report.md`
**Related treatment mapping:** `docs/planning/im_hk_v14_downstream_treatment_mapping.md`

---

## Goal

Validate the promoted HKv14 mock/stub execution bridge without rebuilding a second independent mock API implementation.

The HKv14 bridge uses:

- shared deterministic implementation in `deliverables/im_hk_mock_api_common/`,
- thin HKv14 wrapper in `deliverables/im_hk_v14_mock_api/`,
- HKv14-specific service name, rule catalog labels, BDD labels and README,
- HKv14-specific flat-rate validation data mapped from the accepted deterministic diff candidates.

---

## Boundary

This is a proof-of-concept mock API. It does not represent:

- real VaR Platform behavior,
- HKSCC/HKEX production Initial Margin readiness,
- production-calibrated HKv14 calculation validation,
- Stage 3 real execution integration.

HKv13 remains preserved as `deliverables/im_hk_v13_mock_api/`.

---

## Validation Commands

From repository root:

```powershell
.venv\Scripts\python.exe -m compileall deliverables\im_hk_mock_api_common deliverables\im_hk_v14_mock_api
.venv\Scripts\python.exe -m unittest discover -s deliverables\im_hk_v14_mock_api\tests -t deliverables\im_hk_v14_mock_api -v
```

From the HKv14 deliverable directory:

```powershell
python poc_flat_rate_margin.py
python run_bdd.py
```

Expected BDD result:

```text
Summary: 37 passed, 0 failed
```

---

## Acceptance

- HKv14 API health endpoint reports `mock-im-hk-v14-api`.
- HKv14 rules endpoint returns `IM-HK14-*` rule IDs.
- Flat rate margin validation uses the HKv14 three-term example:
  `(60,000,000 x 12% + 750,000 x 30% + 300,000 x 55%) x 2 = 15,180,000`.
- BDD runner passes all included feature steps.
- Shared common package compiles.
- HKv13 deliverable remains unmodified.

---

## S2-C4 Treatment Mapping Result

`docs/planning/im_hk_v14_downstream_treatment_mapping.md` maps the 10 changed candidates and 1 ID drift candidate.

Immediate implementation required by that mapping:

- update HKv14 flat-rate validation source anchor to `artifacts/im_hk_v14/source_from_pdf.md`,
- update HKv14 flat-rate validation data from the HKv13 two-term example to the HKv14 three-term example,
- keep shared mock API logic unchanged,
- preserve HKv13 deliverable as the baseline.

---

## Schema, Prompt, and Model Impact

- Schema impact: none.
- Prompt impact: none.
- Model impact: none.
- Main pipeline impact: none.

---

## Rollback

Rollback is limited to removing:

- `deliverables/im_hk_mock_api_common/`,
- `deliverables/im_hk_v14_mock_api/`,
- `docs/planning/im_hk_v14_downstream_treatment_mapping.md`,
- this validation plan.

HKv13 artifacts and HKv13 mock API deliverables remain the stable baseline.
