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
