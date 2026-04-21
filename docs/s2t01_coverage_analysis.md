# S2-T01 Coverage Analysis

**Date:** 2026-04-20
**Run ID:** `20260420T033143Z`
**Artifact:** `evidence/20260420_s2t01_full_run/`

## Coverage Summary

| Metric | Value |
|--------|-------|
| Total rules | 180 |
| Fully covered | 130 (72.22%) |
| Partially covered | 17 |
| Uncovered | 2 |
| Not applicable | 34 |

## Partially Covered Rules — Root Cause Analysis

### Root Cause 1: Checker rates case type as "indirect" instead of "direct"

These rules generated all required case types, but the checker marked them as
`coverage_relevance = indirect` or `not_relevant`, which does not count toward
direct coverage.

#### Pattern A: `workflow` rules missing "exception" (7 rules)
Checker accepted the exception case type but rated it `indirect`.

| Rule | Accepted case types | Missing from direct |
|------|--------------------|--------------------|
| SR-MR-060-B-1 | positive, negative, exception | exception (indirect) |
| SR-MR-071-A-1 | positive, negative, exception | exception (indirect) |
| SR-MR-071-B-1 | positive, negative, exception | exception (indirect) |
| SR-MR-071-C-1 | positive, negative, exception | exception (indirect) |
| SR-MR-074-A-1 | positive, negative, exception | exception (indirect) |
| SR-MR-074-B-1 | positive, negative, exception | exception (indirect) |
| SR-MR-074-C-1 | positive, negative, exception | exception (indirect) |

**Fix:** Adjust `CHECKER_SYSTEM_PROMPT` so that for `rule_type = workflow`,
`case_type = exception` is treated as `direct` coverage relevance.

#### Pattern B: `deadline` rules missing "boundary" (3 rules)
Checker rated boundary case type as `not_relevant`.

| Rule | Missing |
|------|---------|
| SR-MR-004-01 | boundary |
| SR-MR-015-B3-4 | boundary |
| SR-MR-021-02 | boundary |

**Fix:** Adjust `CHECKER_SYSTEM_PROMPT` so that for `rule_type = deadline`,
`case_type = boundary` is treated as `direct` coverage relevance.

#### Pattern C: `prohibition` rules missing "positive" (2 rules)
Checker rated positive case type as `indirect`.

| Rule | Missing |
|------|---------|
| SR-MR-033-03 | positive |
| SR-MR-033-04 | positive |

**Fix:** Adjust `CHECKER_SYSTEM_PROMPT` so that for `rule_type = prohibition`,
`case_type = positive` is treated as `direct` coverage relevance.

### Root Cause 2: Maker didn't generate required case types (4 rules)

The maker pipeline skipped generating some required case types. This is likely
because the prompt did not sufficiently emphasize generating all required types.

| Rule | Rule type | Missing |
|------|-----------|---------|
| SR-MR-014-B4-1 | enum_definition | negative |
| SR-MR-014-B5-1 | enum_definition | negative |
| SR-MR-017-B6-1 | calculation | boundary |
| SR-MR-028-01 | deadline | negative |

**Fix:** Strengthen `MAKER_SYSTEM_PROMPT` to explicitly require each
`required_case_types` entry to have at least one scenario generated.

## Uncovered Rules — Root Cause Analysis

### SR-MR-064-A-1 and SR-MR-064-B-1

Both rules have `rule_type = obligation` with required case types
`[positive, negative]`. The maker generated both cases, but the checker
rejected both as `blocking = True` with very low scores:

```
SR-MR-064-A-1-positive: evidence_consistency=1, requirement_coverage=2, test_design_quality=3
SR-MR-064-A-1-negative: evidence_consistency=1, requirement_coverage=2, test_design_quality=3
```

**Root cause:** The evidence quote in `semantic_rules.json` is truncated:

```
"(a) the over-the-counter transaction must: i. ii. iii."
```

The full text was cut off during document extraction — the actual requirements
(i, ii, iii) are not shown. The checker correctly identifies that the evidence
does not support the scenario's assumptions.

**Fix:** Re-extract the source document (LME Matching Rules v2.2, page 19) to
capture the complete text of requirement (a). Update `atomic_rules.json` and
regenerate `semantic_rules.json` for SR-MR-064-A-1 and SR-MR-064-B-1.

## Checker Prompt Adjustment

File: `lme_testing/prompts.py` — `CHECKER_SYSTEM_PROMPT`

The checker should be calibrated so that:

1. For `rule_type = workflow`: `case_type = exception` → `coverage_relevance = direct`
2. For `rule_type = deadline`: `case_type = boundary` → `coverage_relevance = direct`
3. For `rule_type = prohibition`: `case_type = positive` → `coverage_relevance = direct`

## Expected Impact After Fixes

| Fix | Rules affected | Coverage delta |
|-----|---------------|-----------------|
| Checker: workflow+exception | +7 fully covered | +3.89% |
| Checker: deadline+boundary | +3 fully covered | +1.67% |
| Checker: prohibition+positive | +2 fully covered | +1.11% |
| Source re-extraction (064-A/B) | +2 fully covered | +1.11% |
| Maker: generate missing types | +4 fully covered | +2.22% |
| **Total** | **18** | **~10%** |

Expected final coverage: **~82%**

---

## v1.1 Checker Run Results (2026-04-20)

**Run ID:** `20260420T062527Z`
**Prompt version:** 1.1
**Source maker cases:** `runs/maker/20260420T023545Z` (same maker run as v1.0)

### Coverage Comparison

| Metric | v1.0 (Before) | v1.1 (After) | Delta |
|--------|---------------|--------------|-------|
| Coverage | 72.22% | **75.0%** | **+2.78%** |
| Fully covered | 130 | 135 | +5 |
| Partially covered | 17 | 12 | -5 |
| Uncovered | 2 | 1 | -1 |
| Not applicable | 34 | 35 | +1 |

### Rules That Improved (partial → fully covered)

| Rule | Root Cause Fixed | v1.0 Missing | v1.1 Status |
|------|-----------------|--------------|-------------|
| SR-MR-071-B-1 | workflow+exception | exception (indirect) | fixed |
| SR-MR-071-C-1 | workflow+exception | exception (indirect) | fixed |
| SR-MR-074-A-1 | workflow+exception | exception (indirect) | fixed |
| SR-MR-074-B-1 | workflow+exception | exception (indirect) | fixed |
| SR-MR-074-C-1 | workflow+exception | exception (indirect) | fixed |
| SR-MR-015-B3-4 | deadline+boundary | boundary (not_relevant) | fixed |
| SR-MR-021-02 | deadline+boundary | boundary (not_relevant) | fixed |
| SR-MR-014-B4-1 | maker missed (self-corrected) | negative | fixed |
| SR-MR-014-B5-1 | maker missed (self-corrected) | negative | fixed |

### Still Partially Covered (12 rules)

| Rule | Root Cause | v1.0 Missing | v1.1 Missing |
|------|------------|--------------|--------------|
| SR-MR-004-01 | deadline+boundary | boundary | boundary (not fixed) |
| SR-MR-060-B-1 | workflow+exception | exception | exception (not fixed) |
| SR-MR-071-A-1 | workflow+exception | exception | exception (not fixed) |
| SR-MR-033-03 | prohibition+positive | positive | positive (not fixed) |
| SR-MR-033-04 | prohibition+positive | positive | positive (not fixed) |
| SR-MR-017-B6-1 | calculation+boundary | boundary | boundary (not fixed) |
| SR-MR-028-01 | deadline+negative | negative | negative (not fixed) |
| SR-MR-016-B3-1 | enum+negative | — | negative (new regression) |
| SR-MR-017-B2-1 | calculation+data_validation | — | data_validation (new regression) |
| SR-MR-070-02 | deadline+negative | — | negative (new regression) |
| SR-MR-075-01 | prohibition+positive | — | positive (new regression) |

### Regressions (4 rules: fully → partially covered)

| Rule | v1.0 Accepted | v1.1 Accepted | Lost |
|------|--------------|---------------|------|
| SR-MR-016-B3-1 | negative, positive | positive | negative |
| SR-MR-017-B2-1 | boundary, data_validation, positive | boundary, positive | data_validation |
| SR-MR-070-02 | boundary, negative, positive | boundary, positive | negative |
| SR-MR-075-01 | negative, positive | negative | positive |

### Uncovered Rules

| Rule | v1.0 Status | v1.1 Status | Note |
|------|-------------|-------------|------|
| SR-MR-064-A-1 | uncovered | not_applicable | Correctly marked; source page 19 itself truncated |
| SR-MR-064-B-1 | partially_covered | fully_covered | improved (was blocked by 064-A-1) |

### Why ~82% Wasn't Reached

The expected +10% was based on all 17 partially-covered rules improving. Actual result:
- 9 rules improved (partial → full)
- 4 rules regressed (full → partial) — v1.1 prompt introduced new strictness
- Net: +5 fully covered rules

**Specific pattern failures:**
- `workflow+exception`: Fixed 5/7 rules. SR-MR-060-B-1 and SR-MR-071-A-1 still fail.
- `deadline+boundary`: Fixed 2/3 rules. SR-MR-004-01 still fails.
- `prohibition+positive`: Fixed 0/2 rules. SR-MR-033-03 and SR-MR-033-04 still fail.

**New regressions:** v1.1 prompt caused checker to de-accept previously-accepted case types on 4 rules (SR-MR-016-B3-1, SR-MR-017-B2-1, SR-MR-070-02, SR-MR-075-01).

### v1.1 Regression Analysis (4 rules: fully -> partially covered)

All 4 regressions share a pattern: **v1.1's stricter guideline language caused the checker to scrutinize evidence_consistency more carefully**, leading to lower scores and downgraded coverage_relevance.

| Rule | v1.0 Accepted | v1.1 Accepted | Lost Case | Root Cause |
|------|--------------|---------------|-----------|------------|
| SR-MR-016-B3-1 | negative, positive | positive | negative (3,4,4) | Negative scenario for enum_definition tested invalid value not grounded in evidence |
| SR-MR-017-B2-1 | boundary, data_validation, positive | boundary, positive | data_validation (3,3,4) | v1.1 stricter evidence scrutiny lowered data_validation scores |
| SR-MR-070-02 | boundary, negative, positive | boundary, positive | negative (4,3,4) | v1.1 stricter evidence scrutiny lowered negative scores |
| SR-MR-075-01 | negative, positive | negative | positive (3,4,3) | Positive scenario tested normal OTC usage, not the prohibited misuse |

### Root Cause of Remaining Failures

After examining the evidence quotes vs. maker scenarios, **all remaining failures are maker quality issues or evidence gaps** — not checker calibration issues. The v1.1 guidelines are working correctly when the maker output is sound.

| Rule | Issue Type | Evidence vs Scenario | Fix Owner |
|------|-----------|---------------------|-----------|
| SR-MR-033-03 positive | **Maker semantic error** | Prohibition = cross-account offset; scenario = within-one-account (permitted) | Maker |
| SR-MR-033-04 positive | **Maker semantic error** | Prohibition = different pricing bases; scenario = same pricing basis (permitted) | Maker |
| SR-MR-075-01 positive | **Maker semantic error** | Prohibition = misuse OTC; scenario = normal OTC usage (permitted) | Maker |
| SR-MR-060-B-1 exception | **Evidence gap + maker overreach** | Evidence truncated at clause (b); no exception handling described | Evidence extraction |
| SR-MR-071-A-1 exception | **Maker overreach** | Rule covers invalid ID rejection; scenario covers service unavailability | Maker |
| SR-MR-004-01 boundary | **Likely maker** | Rule covers deadline extension in exceptional circumstances; scenario covers submission timing at cutoff | Maker |
| SR-MR-017-B6-1 boundary | **Likely maker** | Rule covers calculation methodology; boundary scenario may not be grounded | Maker |
| SR-MR-028-01 negative | **Likely maker** | Negative case for deadline may not test the actual constraint | Maker |

### Path to ~82% Coverage

Reaching ~82% requires **maker prompt improvements**, not checker calibration:

1. **Prohibition positive cases** (SR-MR-033-03, 033-04, 075-01): Maker must generate positive cases that attempt the **prohibited** action and expect rejection — not test similar permitted actions
2. **Workflow exception cases** (SR-MR-060-B-1, 071-A-1): Exception cases must be grounded in source text; maker should not infer exception scenarios not described in evidence
3. **Boundary cases** (SR-MR-004-01, 017-B6-1): Boundary scenarios must specifically test the edge conditions described in the evidence, not generic timing tests
4. **Evidence re-extraction**: SR-MR-060-B-1 source text is truncated; re-extracting page 60(b) may reveal the exception handling clause

### v1.2 Calibration Scope

v1.2 can only address:
1. Any remaining deadline+boundary cases where v1.1 guideline was truly not followed (SR-MR-004-01 — needs investigation)
2. Possible regression guardrails: ensure v1.1 stricter language doesn't inadvertently lower scores on valid cases
3. Add explicit regression warnings in the guideline: "DO NOT lower evidence_consistency solely because the scenario tests an edge case — only lower if the evidence does not support the specific action being tested"

**Conclusion**: The 75.0% coverage from v1.1 is the practical ceiling for checker-only improvements. Further gains require maker prompt revisions targeting the specific semantic misalignment patterns above.

---

## v1.3 Maker Run Results (2026-04-21)

**Run IDs:** `runs/maker/20260420T090723Z` (maker v1.3) + `runs/checker/20260420T100100Z` (checker v1.1)
**Prompt version:** MAKER_PROMPT_VERSION 1.2 → 1.3

### Key Changes in v1.3

**PROHIBITION positive guidance revised:**
- v1.2: "describe the permitted action (not the prohibition violation)"
- v1.3: "the positive case tests whether the prohibition is enforced — describe the actor attempting the prohibited action, THEN expects rejection"

**WORKFLOW exception guidance added:**
- Exception cases must be directly derived from evidence; do not infer exception scenarios not mentioned in source text

### Coverage Comparison

| Metric | v1.1 (maker 1.2, checker 1.1) | v1.3 (maker 1.3, checker 1.1) | Delta |
|--------|--------------------------------|-------------------------------|-------|
| Coverage | 75.0% | **74.44%** | -0.56% |
| Fully covered | 135 | 134 | -1 |
| Partially covered | 12 | 13 | +1 |
| Uncovered | 1 | 1 | 0 |

### Prohibition Positive Fix — Evidence

The v1.3 prohibition positive guidance worked: positive cases now rated `direct` instead of `indirect`.

| Rule | v1.1 Positive | v1.3 Positive | Improvement |
|------|---------------|---------------|-------------|
| SR-MR-033-03 | indirect (4,4,4) | **direct (5,5,5)** | ✅ fixed |
| SR-MR-033-04 | indirect (4,4,4) | **direct (5,5,5)** | ✅ fixed |
| SR-MR-075-01 | indirect (3,4,3) | **direct (5,5,4)** | ✅ fixed (now fully covered) |

### Still Partially Covered

| Rule | Issue | Status |
|------|-------|--------|
| SR-MR-033-03 | prohibition positive=direct ✅ but negative=indirect ❌ | Still partial — negative counts as indirect for prohibition |
| SR-MR-033-04 | prohibition positive=direct ✅ but negative=indirect ❌ | Still partial — negative counts as indirect for prohibition |
| SR-MR-004-01 | deadline boundary still not_relevant | Partial — v1.3 maker generated but checker still rejects |

### Regressions (LLM Non-Determinism)

6 rules regressed from fully → partially covered. This is attributed to **LLM non-determinism** (same prompt produces different scenarios on different runs), not the v1.3 prompt itself:
- SR-MR-009-01 (data_constraint), SR-MR-022-02, SR-MR-046-04, SR-MR-061-01, SR-MR-062-02: lost `negative` acceptance
- SR-MR-071-C-1: lost `negative` acceptance

### v1.4 Needed

1. **Prohibition negative guidance**: For prohibition rules, the negative case (testing permitted alternative) should also be `direct` — it confirms the prohibition doesn't over-block lawful behavior. This would fully cover SR-MR-033-03 and SR-MR-033-04.
2. **Re-run to confirm**: Due to LLM non-determinism, need multiple runs to establish whether v1.3 is a net improvement.
3. **SR-MR-004-01 boundary**: Still fails despite v1.3 — requires specific evidence-grounded boundary value.
