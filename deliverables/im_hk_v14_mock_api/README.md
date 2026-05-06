# Initial Margin HKv14 Mock API Package

This package provides a runnable HKv14 proof-of-concept mock API service for Initial Margin, plus executable BDD feature files and Python step definitions that call the mock API over HTTP.

It validates the end-to-end POC path:

`Initial Margin HKv14 guide -> governed rules -> BDD -> executable script -> API under test`

This package reuses shared deterministic logic from `../im_hk_mock_api_common/` and keeps HKv14-specific behavior in a thin wrapper:

```text
../im_hk_mock_api_common/
  im_hk_mock_api_common/
    client.py
    domain.py
    rules.py
    runner.py
    server.py
    steps.py
mock_im_api/
  server.py          # HKv14 service wrapper
  rules.py           # HKv14 rule catalog labels
  client.py          # wrapper export
features/
  initial_margin/
  step_definitions/
data/
tests/
```

The HKv13 bridge remains preserved in `../im_hk_v13_mock_api/`. This package must not overwrite or replace it.

## Scope

The HKv14 POC accepts the deterministic HKv13/HKv14 diff candidates documented in:

- `../../docs/planning/im_hk_v14_diff_report.md`
- `../../docs/planning/im_hk_v14_downstream_decision.md`

For POC purposes, the deterministic endpoint behavior remains aligned with the HKv13 bridge unless a reviewed HKv14-specific calculation behavior is later identified.

## Quick Start

Use Python 3.11 or newer.

Terminal 1:

```powershell
cd deliverables\im_hk_v14_mock_api
python -m mock_im_api.server --port 8768
```

Terminal 2:

```powershell
cd deliverables\im_hk_v14_mock_api
python run_bdd.py
```

Expected result:

```text
Summary: 37 passed, 0 failed
```

## Running Tests

From the repository root:

```powershell
python -m unittest discover -s deliverables\im_hk_v14_mock_api\tests -t deliverables\im_hk_v14_mock_api -v
```

Run the focused section 3.2.4.2 POC:

```powershell
cd deliverables\im_hk_v14_mock_api
python poc_flat_rate_margin.py
python run_bdd.py features\initial_margin\flat_rate_margin_poc.feature
```

## Notes and Boundaries

- This is a mock/stub execution bridge, not a production margin engine.
- It does not represent real VaR Platform, HKSCC, HKEX or production Initial Margin readiness.
- It does not change artifact schemas, prompts, provider defaults, or main pipeline contracts.
- HKv13 and HKv14 deliverables remain separate versioned POC packages.
