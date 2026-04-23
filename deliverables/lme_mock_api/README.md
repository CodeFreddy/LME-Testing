# LME Matching Rules Mock API Package

This package provides a runnable mock API service derived from `LME_Matching_Rules_Aug_2022.md`, plus executable BDD feature files and Python step definitions that call the mock API over HTTP.

It is intended to validate the end-to-end path:

`requirements document -> maker/checker -> BDD -> executable script -> API under test`

The mock is deterministic and scoped to representative rules from the document. It is not a production LME system.

## Contents

```text
mock_lme_api/
  server.py              # HTTP mock service
  domain.py              # deterministic rule checks
  rules.py               # rule catalog and enums
  client.py              # HTTP client used by step definitions
features/
  matching_rules/
    core_matching_rules.feature
  step_definitions/
    matching_rules_steps.py
run_bdd.py               # lightweight Gherkin runner
data/
  normalized_bdd_sample.json
tests/
  test_mock_api.py
```

## Rule Coverage in This Mock

The service implements executable checks for these document areas:

| Rule | Source in document | Mock endpoint |
|------|--------------------|---------------|
| MR-001 | Capitalised terms use LME Rulebook meaning | `POST /terminology/validate` |
| MR-002 | Exchange business is subject to price validation | `POST /trades/validate-price` |
| MR-003 | Contact Exchange after price validation failure | `POST /trades/contact-exchange` |
| MR-004 | Extension requests at least 15 minutes before deadline | `POST /deadlines/validate` |
| MR-007 | Asian-hours Client Contracts by 08:30 | `POST /trades/submit` |
| MR-008 | Complete audit trail | `POST /audit/validate` |
| MR-046 | Give-Up Inter-office venue and UNA process | `POST /giveups/submit` |
| MR-064 | OTC Bring-On evidence requirements | `POST /otc-bring-ons/validate` |
| MR-071 | Auction bid rejection conditions | `POST /auctions/bids` |
| MR-075 | OTC Bring-On misuse to avoid PTT | `POST /ptt/validate` |

## Quick Start

Use Python 3.11 or newer.

Terminal 1:

```powershell
cd deliverables\lme_mock_api
python -m mock_lme_api.server --port 8766
```

Terminal 2:

```powershell
cd deliverables\lme_mock_api
python run_bdd.py
```

Expected result:

```text
Summary: 33 passed, 0 failed
```

## Direct API Examples

```powershell
Invoke-RestMethod http://127.0.0.1:8766/health
Invoke-RestMethod http://127.0.0.1:8766/rules
```

Price validation failure:

```powershell
$body = @{
  trade = @{
    trade_id = "TRADE-PVF-001"
    price = 1500
    reference_price = 2000
    tolerance = 0.10
  }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8766/trades/validate-price `
  -ContentType "application/json" `
  -Body $body
```

## Using With Generated BDD

The file `data/normalized_bdd_sample.json` shows the normalized BDD shape expected by the existing repository. To make generated BDD executable against this mock:

1. Keep generated step text close to the phrases in `features/step_definitions/matching_rules_steps.py`.
2. Add or adjust step definitions using the `@step(...)` decorator.
3. Make each step call `context.client.post(...)` or `context.client.get(...)`.
4. Keep the API response assertions in `Then` steps.

The important shift from earlier stubs is that step definitions must call the mock API, for example:

```python
context.last_response = context.client.post(
    "/deadlines/validate",
    {"deadline_at": "...", "submitted_at": "..."},
)
assert context.last_response.body["status"] == "accepted"
```

## Running Tests

With the server already running:

```powershell
python -m unittest tests.test_mock_api
```

Or just run the BDD suite:

```powershell
python run_bdd.py features\matching_rules\core_matching_rules.feature
```

## Notes and Boundaries

- No external Python packages are required.
- The mock uses UTC timestamps for deterministic tests.
- The mock exposes deterministic rule checks only; it does not simulate matching engine state, clearing, settlement, or real LME connectivity.
- This package is intentionally separate from the main `lme_testing` package so it does not alter existing artifact schemas or governance gates.

