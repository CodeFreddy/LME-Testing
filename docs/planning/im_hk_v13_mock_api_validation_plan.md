# Initial Margin HKv13 Mock API Validation Plan

**Status:** COMPLETE for S2-C2 mock execution bridge  
**Date:** 2026-04-26  
**Canonical owner:** `docs/planning/implementation_plan.md` section S2-C2 and `docs/governance/acceptance.md` Gate S2.5
**Related roadmap task:** S2-C2
**Scope:** Validate that generated or reviewed BDD-style scripts can call a deterministic API under test for Initial Margin HKv13 before real execution environment access is available.

---

## Purpose

The real execution environment remains outside this repository. This plan defines a bounded mock execution bridge so the project can validate the path:

`Initial Margin Calculation Guide HKv13 -> governed rules -> BDD -> script -> API under test`

This is not a replacement for Stage 3. It is a controlled mock target for script executability and integration shape.

---

## Deliverable

The mock package is stored at:

- `deliverables/im_hk_v13_mock_api/`
- `deliverables/im_hk_v13_mock_api.zip`

Key files:

- `deliverables/im_hk_v13_mock_api/mock_im_api/server.py` - HTTP mock API service
- `deliverables/im_hk_v13_mock_api/mock_im_api/domain.py` - deterministic rule checks
- `deliverables/im_hk_v13_mock_api/mock_im_api/client.py` - HTTP client used by scripts
- `deliverables/im_hk_v13_mock_api/features/initial_margin/core_initial_margin.feature` - executable sample feature
- `deliverables/im_hk_v13_mock_api/features/initial_margin/flat_rate_margin_poc.feature` - section 3.2.4.2 end-to-end POC
- `deliverables/im_hk_v13_mock_api/features/step_definitions/initial_margin_steps.py` - step definitions that call the mock API over HTTP
- `deliverables/im_hk_v13_mock_api/run_bdd.py` - lightweight Gherkin runner
- `deliverables/im_hk_v13_mock_api/poc_flat_rate_margin.py` - focused Flat Rate Margin POC runner
- `deliverables/im_hk_v13_mock_api/data/normalized_bdd_sample.json` - normalized BDD sample aligned to existing schema shape
- `deliverables/im_hk_v13_mock_api/data/flat_rate_margin_poc.json` - source-anchored Flat Rate Margin fixture
- `deliverables/im_hk_v13_mock_api/tests/test_mock_api.py` - end-to-end tests

---

## Mock Rule Scope

The mock API implements representative executable checks from `docs/materials/Initial Margin Calculation Guide HKv13.pdf` and the derived governed artifacts in `artifacts/im_hk_v13/`.

| Area | Source area | Endpoint |
|------|-------------|----------|
| RPF validation | Section 2.2 | `POST /rpf/validate` |
| Position normalization | Section 3.1.2 | `POST /positions/normalize` |
| Market risk components | Sections 3.2.2-3.2.4 | `POST /margin/market-risk-components` |
| Flat rate margin POC | Section 3.2.4.2 | `POST /margin/flat-rate` |
| MTM split | Sections 3.2.5.2 and 3.2.6.1 | `POST /margin/mtm` |
| Margin aggregation and rounding | Section 3.2.5.1 | `POST /margin/aggregate` |
| Corporate action adjustment | Section 4.4 | `POST /corporate-actions/adjust` |
| Cross-day position netting | Section 4.5 | `POST /positions/cross-day-net` |
| Cross-currency MTM netting | Section 4.6 | `POST /mtm/cross-currency-net` |
| Intraday MTM treatment | Section 4.7 | `POST /mtm/intraday` |

---

## Validation Commands

Run the service:

```powershell
cd deliverables\im_hk_v13_mock_api
python -m mock_im_api.server --port 8767
```

Run the BDD sample in a second shell:

```powershell
cd deliverables\im_hk_v13_mock_api
python run_bdd.py
```

Run tests:

```powershell
python -m unittest discover -s deliverables\im_hk_v13_mock_api\tests -t deliverables\im_hk_v13_mock_api -v
```

Expected result:

```text
Summary: 37 passed, 0 failed
Ran 4 tests
OK
```

The focused Flat Rate Margin POC is anchored to `artifacts/im_hk_v13/source_from_pdf.md` lines 802-880. It validates the guide example:

```text
(1,300,000 x 30% + 60,000,000 x 12%) x 2 = 15,180,000
```

---

## Acceptance

S2-C2 is PASS when:

- the mock API starts locally without third-party dependencies,
- BDD step definitions issue HTTP calls to the mock API,
- positive and negative scenarios assert API responses,
- a small feature suite runs end-to-end with zero failures,
- the package includes README and source code,
- the package is downloadable as a zip artifact,
- docs explicitly state that this is mock verification, not real Initial Margin execution readiness.

Current result: PASS.

---

## Known Limits

- The mock is deterministic and selective; it does not simulate a full VaR Platform or production Initial Margin engine.
- The mock does not replace Stage 3 real execution environment integration.
- The sample BDD is a curated bridge sample, not a full regenerated 164-rule BDD execution suite.
- The formulas are intentionally small and reviewable so script execution remains deterministic.

---

## Rollback

The mock bridge is isolated under `deliverables/im_hk_v13_mock_api/`. Removing that directory, `deliverables/im_hk_v13_mock_api.zip`, and this validation plan reverts the deliverable without changing main pipeline schemas, prompts, models, or artifact contracts.
