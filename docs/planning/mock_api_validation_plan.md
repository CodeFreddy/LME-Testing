# Mock API Validation Plan

**Status:** COMPLETE for S2-C1 mock execution bridge  
**Date:** 2026-04-23  
**Scope:** Validate that generated or reviewed BDD-style scripts can call a deterministic API under test before real LME API access is available.

---

## Purpose

The real LME API remains blocked by internal VM access. This plan defines a bounded mock execution bridge so the project can validate the path:

`LME_Matching_Rules_Aug_2022.md -> maker/checker -> BDD -> script -> API under test`

This is not a replacement for Stage 3. It is a controlled mock target for script executability and integration shape.

---

## Deliverable

The mock package is stored at:

- `deliverables/lme_mock_api/`
- `deliverables/lme_mock_api.zip`

Key files:

- `deliverables/lme_mock_api/mock_lme_api/server.py` — HTTP mock API service
- `deliverables/lme_mock_api/mock_lme_api/domain.py` — deterministic rule checks
- `deliverables/lme_mock_api/mock_lme_api/client.py` — HTTP client used by scripts
- `deliverables/lme_mock_api/features/matching_rules/core_matching_rules.feature` — executable sample feature
- `deliverables/lme_mock_api/features/step_definitions/matching_rules_steps.py` — step definitions that call the mock API over HTTP
- `deliverables/lme_mock_api/run_bdd.py` — lightweight Gherkin runner
- `deliverables/lme_mock_api/data/normalized_bdd_sample.json` — normalized BDD sample aligned to existing schema shape
- `deliverables/lme_mock_api/tests/test_mock_api.py` — end-to-end tests

---

## Mock Rule Scope

The mock API implements representative executable checks from `docs/materials/LME_Matching_Rules_Aug_2022.md`.

| Rule | Source area | Endpoint |
|------|-------------|----------|
| MR-001 | Capitalised terms use LME Rulebook meaning | `POST /terminology/validate` |
| MR-002 | Exchange business is subject to price validation | `POST /trades/validate-price` |
| MR-003 | Contact Exchange after price validation failure | `POST /trades/contact-exchange` |
| MR-004 | Extension requests no later than 15 minutes before deadline | `POST /deadlines/validate` |
| MR-007 | Asian-hours Client Contracts submitted by 08:30 | `POST /trades/submit` |
| MR-008 | Full audit trail retained | `POST /audit/validate` |
| MR-046 | Give-Up Inter-office venue and UNA process | `POST /giveups/submit` |
| MR-064 | OTC Bring-On prior OTC transaction evidence | `POST /otc-bring-ons/validate` |
| MR-071 | Auction bid rejection conditions | `POST /auctions/bids` |
| MR-075 | OTC Bring-On cannot be misused to avoid PTT | `POST /ptt/validate` |

---

## Validation Commands

Run the service:

```powershell
cd deliverables\lme_mock_api
python -m mock_lme_api.server --port 8766
```

Run the BDD sample in a second shell:

```powershell
cd deliverables\lme_mock_api
python run_bdd.py
```

Run tests:

```powershell
cd deliverables\lme_mock_api
python -m unittest tests.test_mock_api
```

Expected result:

```text
Summary: 33 passed, 0 failed
Ran 2 tests
OK
```

---

## Acceptance

S2-C1 is PASS when:

- the mock API starts locally without third-party dependencies,
- BDD step definitions issue HTTP calls to the mock API,
- positive and negative scenarios assert API responses,
- a small feature suite runs end-to-end with zero failures,
- the package includes README and source code,
- the package is downloadable as a zip artifact,
- docs explicitly state that this is mock verification, not real LME API readiness.

Current result: PASS.

---

## Known Limits

- The mock is deterministic and selective; it does not simulate a full matching engine.
- The mock does not replace Stage 3 real LME VM/API integration.
- The sample BDD is a curated bridge sample, not a full regenerated 180-rule BDD execution suite.
- Current repo does not retain a usable full `normalized_bdd.jsonl` run artifact, so the bridge includes `data/normalized_bdd_sample.json` for repeatable validation.

---

## Rollback

The mock bridge is isolated under `deliverables/lme_mock_api/`. Removing that directory and `deliverables/lme_mock_api.zip` reverts the deliverable without changing main pipeline schemas, prompts, models, or artifact contracts.
