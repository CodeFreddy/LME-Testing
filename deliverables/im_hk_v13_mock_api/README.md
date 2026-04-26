# Initial Margin HKv13 Mock API Package

This package provides a runnable mock API service derived from `Initial Margin Calculation Guide HKv13`, plus executable BDD feature files and Python step definitions that call the mock API over HTTP.

It is intended to validate the end-to-end path:

`Initial Margin guide -> governed rules -> BDD -> executable script -> API under test`

The mock is deterministic and scoped to representative calculation and data-validation behaviours from the guide. It is not a production HKSCC/HKEX margin engine.

## Contents

```text
mock_im_api/
  server.py              # HTTP mock service
  domain.py              # deterministic rule checks
  rules.py               # rule catalog and constants
  client.py              # HTTP client used by step definitions
features/
  initial_margin/
    core_initial_margin.feature
    flat_rate_margin_poc.feature
  step_definitions/
    initial_margin_steps.py
run_bdd.py               # lightweight Gherkin runner
poc_flat_rate_margin.py  # section 3.2.4.2 focused POC runner
data/
  normalized_bdd_sample.json
  flat_rate_margin_poc.json
  sample_risk_parameter_file.json
  sample_marginable_positions.json
tests/
  test_mock_api.py
```

## Rule Coverage in This Mock

The service implements executable checks for these guide areas:

| Area | Source in guide | Mock endpoint |
|------|-----------------|---------------|
| RPF validation | Section 2.2, pages 6-8 | `POST /rpf/validate` |
| Position normalization | Section 3.1.2, page 8 | `POST /positions/normalize` |
| Market risk components | Sections 3.2.2-3.2.4, pages 10-19 | `POST /margin/market-risk-components` |
| Flat rate margin POC | Section 3.2.4.2, pages 15-16 | `POST /margin/flat-rate` |
| MTM split | Sections 3.2.5.2 and 3.2.6.1, pages 20-21 | `POST /margin/mtm` |
| Margin aggregation and rounding | Section 3.2.5.1, page 20 | `POST /margin/aggregate` |
| Corporate action adjustment | Section 4.4, pages 28-33 | `POST /corporate-actions/adjust` |
| Cross-day position netting | Section 4.5, pages 33-34 | `POST /positions/cross-day-net` |
| Cross-currency MTM netting | Section 4.6, pages 34-35 | `POST /mtm/cross-currency-net` |
| Intraday MTM treatment | Section 4.7, pages 35-38 | `POST /mtm/intraday` |

## Quick Start

Use Python 3.11 or newer.

Terminal 1:

```powershell
cd deliverables\im_hk_v13_mock_api
python -m mock_im_api.server --port 8767
```

Terminal 2:

```powershell
cd deliverables\im_hk_v13_mock_api
python run_bdd.py
```

Expected result:

```text
Summary: 37 passed, 0 failed
```

## Direct API Examples

```powershell
Invoke-RestMethod http://127.0.0.1:8767/health
Invoke-RestMethod http://127.0.0.1:8767/rules
```

Margin aggregation example:

```powershell
$body = @{
  market_risk_total = 123456
  rounding = 10000
  favorable_mtm = 3000
  margin_credit = 2000
  other_components = @{ position_limit_add_on = 1000 }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8767/margin/aggregate `
  -ContentType "application/json" `
  -Body $body
```

## Using With Generated BDD

The file `data/normalized_bdd_sample.json` shows the normalized BDD shape expected by the existing repository. To make generated BDD executable against this mock:

1. Keep generated step text close to the phrases in `features/step_definitions/initial_margin_steps.py`.
2. Add or adjust step definitions using the `@step(...)` decorator.
3. Make each step call `context.client.post(...)` or `context.client.get(...)`.
4. Keep the API response assertions in `Then` steps.

The important shift from pure stubs is that step definitions must call the mock API, for example:

```python
context.last_response = context.client.post(
    "/margin/aggregate",
    {
        "market_risk_total": 123456,
        "rounding": 10000,
        "favorable_mtm": 3000,
        "margin_credit": 2000,
        "other_components": {"position_limit_add_on": 1000},
    },
)
assert context.last_response.body["status"] == "calculated"
```

## Running Tests

From the repository root:

```powershell
python -m unittest discover -s deliverables\im_hk_v13_mock_api\tests -t deliverables\im_hk_v13_mock_api -v
```

Or just run the BDD suite:

```powershell
python run_bdd.py features\initial_margin\core_initial_margin.feature
```

Run the focused section 3.2.4.2 POC:

```powershell
cd deliverables\im_hk_v13_mock_api
python poc_flat_rate_margin.py
python run_bdd.py features\initial_margin\flat_rate_margin_poc.feature
```

If a sandbox blocks local server startup from the deliverable directory, use the repository-root unittest command above. It starts the mock API in-process and still exercises the BDD runner over HTTP.

## Notes and Boundaries

- No external Python packages are required.
- The mock uses curated deterministic formulas for script executability, not full model replication.
- The mock does not replace Stage 3 real system integration or production-grade Initial Margin calculation validation.
- The package is intentionally separate from the main `lme_testing` and `hkex_testing` packages so it does not alter existing artifact schemas, prompts, provider defaults, or governance gates.
