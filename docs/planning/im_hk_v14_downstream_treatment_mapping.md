# Initial Margin HKv14 Downstream Treatment Mapping

**Status:** S2-C4 deterministic treatment mapping complete
**Created:** 2026-04-26
**Promotion scope:** `docs/planning/im_hk_v14_promotion_scope.md`
**Diff evidence:** `evidence/im_hk_v14_diff/im_hk_v13_to_v14_diff.json`

---

## Purpose

Map the accepted HKv13→HKv14 deterministic diff candidates to downstream treatment categories before changing HKv14 mock API behavior.

This is deterministic treatment planning, not final business interpretation.

---

## Treatment Categories

| Category | Meaning |
| --- | --- |
| `already_covered_by_shared_bridge` | Existing shared mock API behavior remains valid for the candidate. |
| `requires_hkv14_validation_data_update` | HKv14 wrapper data/tests/BDD labels must be updated, but shared API logic remains valid. |
| `advisory_reference_only` | Candidate is reference/advisory or ID drift; no executable mock behavior change. |
| `deferred_domain_clarification` | Needs domain review before production or broader automation claims. |

---

## Candidate Mapping

| Candidate | Diff signal | Treatment | Downstream action |
| --- | --- | --- | --- |
| `MR-012-A-1` | Clause 12 sample portfolio changed values; duplicated long clause extraction also reflects table/layout movement. | `requires_hkv14_validation_data_update` | Update HKv14 validation data source anchor and sample portfolio values. No shared API logic change. |
| `MR-012-A-3` | Favorable MTM note now includes footnote 42 definition for aggregated HKD equivalent contract/market value. | `already_covered_by_shared_bridge` | Existing MTM split behavior remains sufficient for mock/stub bridge; record as covered. |
| `MR-012-A-4` | Favorable MTM/MTM requirement sample uses HKv14 portfolio values but same treatment: negative result becomes MTM requirement. | `already_covered_by_shared_bridge` | Existing MTM requirement treatment remains sufficient for mock/stub bridge; no code change. |
| `MR-012-A-5` | Rule type changed from `calculation` to `permission`; text now records assumed position limit add-on of `487,332`. | `already_covered_by_shared_bridge` | Existing position limit add-on mock value already uses `487,332`; no code change. |
| `MR-012-A-9` | Total MTM and margin requirement changes from `67,720,481` to `67,717,332` because position limit add-on changes to `487,332`. | `already_covered_by_shared_bridge` | Existing total margin aggregation behavior remains valid; future full-total test may assert HKv14 value. |
| `MR-012-B-1` | Clause 12 duplicated long extraction reflects the same sample portfolio/table changes. | `requires_hkv14_validation_data_update` | Same HKv14 flat-rate sample update as `MR-012-A-1`. |
| `MR-012-B-2` | Candidate alignment moved from structured product long-position inclusion to portfolio-level LRA excerpt. | `deferred_domain_clarification` | Treat as extraction/table alignment drift; do not change behavior until domain review. |
| `MR-012-B-3` | Candidate alignment moved to structured product long-position inclusion previously under `MR-012-B-2`. | `already_covered_by_shared_bridge` | Existing structured product inclusion behavior remains valid; no HKv14-specific code change. |
| `MR-012-C-1` | Clause 12 duplicated long extraction reflects the same sample portfolio/table changes. | `requires_hkv14_validation_data_update` | Same HKv14 flat-rate sample update as `MR-012-A-1`. |
| `MR-012-D-1` | Clause 12 duplicated long extraction reflects the same sample portfolio/table changes. | `requires_hkv14_validation_data_update` | Same HKv14 flat-rate sample update as `MR-012-A-1`. |
| `MR-012-B-4` → `MR-012-C-2` | Identical notification text moved IDs; similarity 1.0. | `advisory_reference_only` | Preserve as ID drift advisory; no executable mock behavior change. |

---

## Required Implementation From Mapping

The only immediate HKv14 wrapper change required by this mapping is to refresh the flat-rate validation example:

- source anchor must reference HKv14, not HKv13,
- sample portfolio must use HKv14 values:
  - `658`: short market value `-60,000,000`, flat rate `12%`,
  - `3606`: long market value `30,000,000`, flat rate `12%`,
  - `3456`: long market value `750,000`, flat rate `30%`,
  - `3457`: short market value `-300,000`, flat rate `55%`,
- expected pre-multiplier margin remains `7,590,000`,
- expected flat-rate margin remains `15,180,000`.

No shared mock API logic change is required for this mapping.

---

## Validation Required

- HKv14 wrapper unit tests and BDD runner must pass after the validation data update.
- HKv13 mock API validation should still pass to confirm preservation baseline compatibility.
- Docs and artifact governance checks must pass.

---

## Validation Results

Executed after the HKv14 flat-rate validation data update:

- `.venv\Scripts\python.exe -m unittest discover -s deliverables\im_hk_v14_mock_api\tests -t deliverables\im_hk_v14_mock_api -v`: passed, 3 tests OK; BDD summary 37 passed, 0 failed.
- `.venv\Scripts\python.exe deliverables\im_hk_v14_mock_api\poc_flat_rate_margin.py`: passed; pre-multiplier breakdown is `7,200,000 + 225,000 + 165,000 = 7,590,000`, final margin `15,180,000`.
- `.venv\Scripts\python.exe -m unittest discover -s deliverables\im_hk_v13_mock_api\tests -t deliverables\im_hk_v13_mock_api -v`: passed, 4 tests OK; BDD summary 37 passed, 0 failed.
- `.venv\Scripts\python.exe -m unittest tests.test_compare_initial_margin_versions tests.test_extract_matching_rules -v`: passed, 4 tests OK.
- `.venv\Scripts\python.exe scripts/check_docs_governance.py`: passed.
- `.venv\Scripts\python.exe scripts/check_artifact_governance.py`: passed.

---

## Boundaries

- This mapping does not claim production business interpretation.
- This mapping does not promote HKv14 to real execution readiness.
- This mapping does not change schemas, prompts, default models, or roadmap phase boundaries.
- Extraction/table drift candidates remain visible; they are not hidden to make the flow look cleaner.

---

## Self-Evaluation

| Item | Status | Notes |
| --- | --- | --- |
| 10 changed candidates mapped | PASS | All changed candidates have treatment categories. |
| 1 ID drift candidate mapped | PASS | `MR-012-B-4` → `MR-012-C-2` is advisory/reference-only. |
| Required HKv14 update identified | PASS | Flat-rate validation data/test refresh is required. |
| HKv13 preservation protected | PASS | No HKv13 artifact or deliverable change is required. |
| Schema/prompt/model impact explicit | PASS | No impact. |
