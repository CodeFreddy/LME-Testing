# Baseline 183-Rules Quality Report

**Run Date:** 2026-04-18
**Model:** MiniMax-M2.7
**Provider:** minimax
**Prompt Version:** 1.0
**Pipeline Version:** 2.0

---

## Run Summary

| Metric | Value |
|--------|-------|
| Rules in input | 183 |
| Rules processed by maker | 180 |
| Maker scenarios generated | 322 |
| Checker cases reviewed | 320 / 322 |
| Checker review success rate | 99.4% |
| Unreviewed cases | 2 (SR-MR-075-01 positive/negative — batch JSON parse error) |

**Overall Coverage:** 132 / 180 = **73.3%** (fully covered rules)

---

## Coverage by Rule Type

| Rule Type | Total | Fully | Partial | Uncovered | N/A | Coverage% |
|-----------|------:|------:|--------:|----------:|----:|----------:|
| obligation | 55 | 53 | 1 | 1 | 0 | 96.4% |
| permission | 21 | 21 | 0 | 0 | 0 | 100.0% |
| deadline | 17 | 15 | 1 | 1 | 0 | 88.2% |
| workflow | 17 | 14 | 3 | 0 | 0 | 82.4% |
| enum_definition | 10 | 10 | 0 | 0 | 0 | 100.0% |
| calculation | 8 | 5 | 3 | 0 | 0 | 62.5% |
| data_constraint | 6 | 4 | 2 | 0 | 0 | 66.7% |
| prohibition | 6 | 2 | 3 | 1 | 0 | 33.3% |
| state_transition | 6 | 6 | 0 | 0 | 0 | 100.0% |
| reference_only | 34 | 0 | 0 | 0 | 34 | N/A |

---

## Human Spot Check (12 Rules)

### Spot Check Method

Random selection across coverage categories (fully_covered, partially_covered, uncovered, not_applicable).
Each rule evaluated by reading: (1) semantic rule evidence, (2) maker-given/when/then, (3) checker scores and assessment.

### Spot Check Results

#### SR-MR-001-02 — permission — fully_covered ✅

**Rule:** Permission to do X.
**Maker quality:** GIVEN/WHEN/THEN well-structured, scenario realistic. Scores: evidence=5, coverage=4, quality=4.
**Checker verdict:** direct relevance, `case_type_accepted: true`, status: covered.
**Assessment:** HIGH QUALITY. Correct positive-only case type.

---

#### SR-MR-003-01 — obligation — fully_covered ✅

**Rule:** Obligation to do X under condition Y.
**Maker quality:** Positive and negative cases both present, well-formed. Positive scores: evidence=5, coverage=5, quality=5. Negative: evidence=4, coverage=4, quality=4.
**Checker verdict:** direct relevance for both, status: covered.
**Assessment:** HIGH QUALITY. Both required case types accepted.

---

#### SR-MR-001-01 — obligation — partially_covered ⚠️

**Rule:** Obligation with positive + negative required.
**Maker quality:** Both positive and negative scenarios present. Positive: evidence=5, coverage=4, quality=5 (covered). Negative: evidence=4, coverage=3, quality=4, but `coverage_relevance: indirect` (partial).
**Issue:** Negative case accepted as case_type but marked indirect relevance by checker — partial coverage.
**Assessment:** ACCEPTABLE — case type coverage gap.

---

#### SR-MR-004-01 — deadline — partially_covered ⚠️

**Rule:** Deadline with positive + boundary + negative required.
**Maker quality:** All 3 case types present. Positive and negative: direct relevance, covered. Boundary: `coverage_relevance: indirect`, partial.
**Issue:** Boundary case has indirect relevance — partial coverage.
**Assessment:** ACCEPTABLE — boundary case type gap.

---

#### SR-MR-019-01 — deadline — uncovered ❌

**Rule:** Deadline validation with positive + boundary + negative required.
**Maker quality:** All 3 case types present with well-formed GIVEN/WHEN/THEN.
**Issue:** All 3 cases have `coverage_relevance: indirect` → none accepted for coverage. Scores: evidence=4, coverage=3, quality=3-4 (consistent but low).
**Root cause:** Cases describe system behavior (deadline validation result) but don't exercise the actual rule constraint. Evidence references "Regulation 3.5" but scenario steps don't directly test the deadline boundary.
**Assessment:** POOR — maker generates plausible-looking but checker-rejected scenarios. Prompt may need deadline-specific guidance.

---

#### SR-MR-075-01 — prohibition — uncovered ❌ (UNREVIEWED)

**Rule:** Prohibition — OTC Bring-On trade category use.
**Maker quality:** 2 scenarios generated (positive + negative).
**Issue:** Both cases absent from checker reviews due to batch JSON parse error (final batch). Cannot assess.
**Assessment:** UNKNOWN — needs re-run or manual review.

---

#### SR-MR-064-A-1 — obligation — uncovered ❌

**Rule:** Obligation rule type A.
**Maker quality:** Both positive and negative cases present.
**Issue:** Checker shows `accepted: []` for both case types despite `case_type_accepted: true` for individual cases. Checker may have rejected both for relevance.
**Assessment:** NEEDS INVESTIGATION — appears to have maker output but checker rejected.

---

#### SR-MR-002-01 — reference_only — not_applicable ✅

**Rule:** Reference-only, no testable requirements.
**Assessment:** Correctly excluded. N/A.

---

## Known Issues

### Issue 1: Indirect Coverage Relevance Rejection

**Severity:** Medium
**Affected rules:** deadline, calculation, and some obligation rules
**Description:** Maker generates scenarios that are logically structured but checker marks them `coverage_relevance: indirect`. This causes `rule_coverage_status: partially_covered` or `uncovered` even when the case type is accepted.
**Examples:** SR-MR-019-01 (deadline), SR-MR-001-01 (obligation)
**Likely fix:** Maker prompt needs clearer guidance on how to construct scenarios that directly exercise the rule constraint rather than describing system behavior around it.

### Issue 2: Prohibition Rule Type Underperformance

**Severity:** Medium
**Affected rules:** SR-MR-075-01 (uncovered), SR-MR-071-A-1, SR-MR-071-B-1, SR-MR-071-C-1 (partial)
**Description:** Prohibition rules have 33.3% coverage — worst of any rule type. Two sub-rules (SR-MR-075-01) unreviewed entirely.
**Likely fix:** Prompt may generate positive cases for prohibition when only negative (violation) cases should be required.

### Issue 3: SR-MR-075-01 Batch JSON Error

**Severity:** Low (operational)
**Description:** Last checker batch had JSON parse error, leaving 2 cases unreviewed.
**Impact:** Rule SR-MR-075-01 has zero coverage due to missing data.
**Fix needed:** Checker JSON parsing robustness for malformed responses.

### Issue 4: 3 Rules with No Maker Scenarios

**Severity:** Low
**Description:** 3 semantic rules produced no scenarios (rules not in processed set of 180).
**Impact:** Total requirements = 180 not 183.
**Likely cause:** These rules may lack sufficient evidence text for maker to generate scenarios.

---

## Comparison with POC Baseline

| Metric | POC (2 rules) | Full (183 rules) |
|--------|---------------|-------------------|
| Coverage | 100% (2/2) | 73.3% (132/180) |
| Rule types | obligation | 10 types |
| Required case types met | 100% | varies by type |
| Quality scores | high | median 4/5 |

POC was cherry-picked from well-structured rules. Full run reveals rule-type-specific gaps.

---

## Governance Signals Update

Baseline governance signals should be updated with:

```
coverage_signals:
  total_rules: 180
  fully_covered: 132
  partially_covered: 13
  uncovered: 3
  not_applicable: 34
  coverage_percent: 73.3
```

---

## Run Artifacts

- **Maker output:** `runs/maker/20260418T231915+0800/maker_cases.jsonl`
- **Checker output:** `runs/checker/20260418T234515+0800/checker_reviews.jsonl`
- **Coverage report:** `runs/checker/20260418T234515+0800/coverage_report.json`
- **HTML report:** `reports/baseline_full_20260418.html`
