# Initial Margin Version Diff Report

**Status:** Deterministic candidate diff for human review
**Generated:** 2026-04-26T09:32:20Z
**Canonical owner:** `docs/planning/im_hk_v14_downstream_decision.md` and `docs/governance/acceptance.md` Gate S2.6
**Related roadmap task:** S2-C3

## Sources

| Side | doc_id | doc_title | doc_version | artifact_count |
| --- | --- | --- | --- | --- |
| Previous | im_hk_v13 | Initial Margin Calculation Guide HKv13 | HKv13 | 164 |
| Current | im_hk_v14 | Initial Margin Calculation Guide HKv14 | HKv14 | 164 |

## Summary

| Metric | Value |
| --- | --- |
| Previous atomic rules | 164 |
| Current atomic rules | 164 |
| Rule count delta | 0 |
| Common rule IDs | 69 |
| Unchanged common rules | 59 |
| Changed candidates | 10 |
| Added candidates | 0 |
| Removed candidates | 0 |
| ID drift candidates | 1 |
| Source anchor warnings | 0 |

## Rule Type Distribution

| Rule type | Previous | Current | Delta |
| --- | --- | --- | --- |
| calculation | 122 | 120 | -2 |
| data_constraint | 13 | 13 | 0 |
| obligation | 8 | 8 | 0 |
| permission | 0 | 1 | 1 |
| reference_only | 21 | 22 | 1 |

## Clause Delta

| Metric | Value |
| --- | --- |
| Previous clauses | 10 |
| Current clauses | 10 |
| Clause count delta | 0 |
| Changed clause candidates | 1 |

## Changed Rule Candidates

- `MR-012-A-1`: 0.892355
  - previous: 12. when using the information in the "marginable position report", please note that: 6 mtm refers to "mark-to-market" a.k.a. the marks. 7 the report will be generated on each business day for cps to download via repo...
  - current: 12. when using the information in the "marginable position report", please note that: 6 mtm refers to "mark-to-market" a.k.a. the marks. 7 the report will be generated on each business day for cps to download via repo...
- `MR-012-A-3`: 0.705882
  - previous: in the mtm and margin requirement report, absolute value of favorable mtm(or mtm requirement) will be shown.
  - current: in the mtm and margin requirement report, absolute value of favorable mtm(or mtm requirement) will be shown. 42 the aggregated value of hkd equivalent contract value and hkd equivalent market value.
- `MR-012-A-4`: 0.794964
  - previous: hkscc - var platform initial margin calculation guide page 21 of 38 favorable mtm(or mtm requirement)42 = market valueportfolio - contract valueportfolio = (,700,000) – (,000,000) =,700,000 the negative number refers...
  - current: hkscc - var platform initial margin calculation guide page 21 of 38 = (,550,000) – (,850,000) =,700,000 the negative number refers to a mtm requirement, which its absolute value will be added after applying margin cre...
- `MR-012-A-5`: 0.584906
  - previous: please refer to appendix 4.6 for calculation logic that involve multiple currencies in the portfolio. 43 such amount may be reduced for risk management purpose.
  - current: for illustration purpose, position limit add -on for the sample portfolio is assumed to be 487,332. 43 such amount may be reduced for risk management purpose.
- `MR-012-A-9`: 0.972067
  - previous: total mtm and margin requirement = net margin after credit + other risk components = net margin after credit + mtm requirement + position limit add-on + credit risk add-on + ad-hoc add-on = 41,930,000 + 12,700,000 + 4...
  - current: total mtm and margin requirement = net margin after credit + other risk components = net margin after credit + mtm requirement + position limit add-on + credit risk add-on + ad-hoc add-on = 41,930,000 + 12,700,000 + 4...
- `MR-012-B-1`: 0.892355
  - previous: 12. when using the information in the "marginable position report", please note that: 6 mtm refers to "mark-to-market" a.k.a. the marks. 7 the report will be generated on each business day for cps to download via repo...
  - current: 12. when using the information in the "marginable position report", please note that: 6 mtm refers to "mark-to-market" a.k.a. the marks. 7 the report will be generated on each business day for cps to download via repo...
- `MR-012-B-2`: 0.025834
  - previous: as there is a positive quantity of instrumentid 26883(i.e., 110,000,000), the instrument is under long position and should be included in the subsequent calculation for structured product add-on34.
  - current: hkscc - var platform initial margin calculation guide page 18 of 38 portfolio-level liquidation risk add-on = m aximum [0, absolute value of(total market value of b eta hedge position) – hedging market value threshold...
- `MR-012-B-3`: 0.352221
  - previous: hkscc will issue circulars to notify the market before any change is made. 34 if the quantity of instrumentid 26883 is negative e.g., it will be excluded from the calculation of structured product add-on. 35 tick size...
  - current: as there is a positive quantity of instrumentid 26883(i.e., 110,000,000), the instrument is under long position and should be included in the subsequent calculation for structured product add-on34.
- `MR-012-C-1`: 0.892355
  - previous: 12. when using the information in the "marginable position report", please note that: 6 mtm refers to "mark-to-market" a.k.a. the marks. 7 the report will be generated on each business day for cps to download via repo...
  - current: 12. when using the information in the "marginable position report", please note that: 6 mtm refers to "mark-to-market" a.k.a. the marks. 7 the report will be generated on each business day for cps to download via repo...
- `MR-012-D-1`: 0.892355
  - previous: 12. when using the information in the "marginable position report", please note that: 6 mtm refers to "mark-to-market" a.k.a. the marks. 7 the report will be generated on each business day for cps to download via repo...
  - current: 12. when using the information in the "marginable position report", please note that: 6 mtm refers to "mark-to-market" a.k.a. the marks. 7 the report will be generated on each business day for cps to download via repo...

## Added Rule Candidates

None detected.

## Removed Rule Candidates

None detected.

## ID Drift Candidates

- `MR-012-B-4`: 1.0
  - previous: hkscc will notify the market before any change is made.
  - current: hkscc will notify the market before any change is made.

## Source Anchor Warnings

None detected.

## Downstream Impact Candidates

| Area | Level | Reason |
| --- | --- | --- |
| maker_checker_bdd | review_required | 11 rule-level candidate difference(s) found. |
| artifact_governance | review_required | Rule type distribution changed between versions. |

## Recommendation

Human review is required before downstream maker/checker/BDD/mock API work. Do not create or update an execution bridge until changed candidates and source-anchor warnings are reviewed.

## Limitations

- This is deterministic artifact comparison, not business interpretation.
- Changed candidates require human review before downstream scope decisions.
- Text similarity can be affected by PDF extraction differences and table layout changes.
- ID-drift candidates are heuristic matches and must not be treated as canonical without review.
