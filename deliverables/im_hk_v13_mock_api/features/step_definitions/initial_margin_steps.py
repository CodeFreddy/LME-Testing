"""Executable BDD step definitions for the Initial Margin HKv13 mock API."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable

from mock_im_api.client import MockIMClient


StepFunc = Callable[..., None]


@dataclass
class Context:
    client: MockIMClient = field(default_factory=MockIMClient)
    data: dict[str, Any] = field(default_factory=dict)
    last_response: Any = None


STEP_DEFINITIONS: list[tuple[str, re.Pattern[str], StepFunc]] = []


def step(pattern: str) -> Callable[[StepFunc], StepFunc]:
    compiled = re.compile("^" + pattern + "$", re.IGNORECASE)

    def decorator(fn: StepFunc) -> StepFunc:
        STEP_DEFINITIONS.append((pattern, compiled, fn))
        return fn

    return decorator


def dispatch(context: Context, step_text: str) -> None:
    for _pattern, compiled, fn in STEP_DEFINITIONS:
        match = compiled.match(step_text)
        if match:
            fn(context, *match.groups())
            return
    raise AssertionError(f"No step definition matched: {step_text}")


def _assert_status(context: Context, expected: str) -> None:
    assert context.last_response is not None, "No API response has been recorded"
    body = context.last_response.body
    assert body.get("status") == expected, f"Expected status {expected!r}, got {body!r}"


@step(r"an Initial Margin Risk Parameter File contains required global fields and supported FieldType records")
def given_valid_rpf(context: Context) -> None:
    context.data["rpf"] = {
        "global_fields": {
            "Valuation_DT": "01/04/2019",
            "HVaR_WGT": 0.75,
            "SVaR_WGT": 0.25,
            "HVaR_Scen_Count": 1000,
            "SVaR_Scen_Count": 1018,
            "HVaR_CL": 0.994,
            "SVaR_CL": 0.98,
            "Rounding": 10000,
        },
        "records": [
            {"InstrumentID": "700", "FieldType": 1, "values": [0.01391, 0.01422]},
            {"InstrumentID": "700", "FieldType": 2, "values": [0.041026, 0.092873]},
            {"InstrumentID": "658", "FieldType": 3, "values": [0.12]},
            {"InstrumentID": "700", "FieldType": 4, "values": [0.0022, 0.9, 300000000, 400]},
        ],
    }


@step(r"the risk parameter file is validated")
def when_rpf_validated(context: Context) -> None:
    context.last_response = context.client.post("/rpf/validate", {"risk_parameter_file": context.data["rpf"]})


@step(r"the risk parameter file validation is accepted")
def then_rpf_accepted(context: Context) -> None:
    _assert_status(context, "accepted")
    assert context.last_response.body.get("record_count") == 4


@step(r"an Initial Margin Risk Parameter File is missing the SVaR confidence level")
def given_rpf_missing_svar_cl(context: Context) -> None:
    given_valid_rpf(context)
    del context.data["rpf"]["global_fields"]["SVaR_CL"]


@step(r"the risk parameter file validation is rejected for missing global fields")
def then_rpf_missing_fields(context: Context) -> None:
    _assert_status(context, "rejected")
    assert context.last_response.reason == "missing_global_fields"
    assert "SVaR_CL" in context.last_response.body.get("missing", [])


@step(r"a portfolio position has quantity and market price")
def given_portfolio_position(context: Context) -> None:
    context.data["positions"] = [{"instrument_id": "700", "quantity": 1000, "market_price": 380, "contract_value": 360000}]


@step(r"the positions are normalized")
def when_positions_normalized(context: Context) -> None:
    context.last_response = context.client.post("/positions/normalize", {"positions": context.data["positions"]})


@step(r"the market value equals quantity times market price")
def then_market_value_calculated(context: Context) -> None:
    _assert_status(context, "accepted")
    assert context.last_response.body["positions"][0]["market_value"] == 380000


@step(r"a mixed Tier P and Tier N portfolio has risk parameters")
def given_mixed_portfolio(context: Context) -> None:
    context.data["market_risk"] = {
        "portfolio": {
            "positions": [
                {"instrument_id": "700", "quantity": 1000, "market_value": 380000},
                {"instrument_id": "658", "quantity": 500, "market_value": 50000},
            ]
        },
        "parameters": {
            "HVaR_WGT": 0.75,
            "SVaR_WGT": 0.25,
            "700": {"tier": "P", "hvar_rate": 0.10, "svar_rate": 0.20, "cash_delta": 400, "delta_threshold": 300000, "bucket_rate": 0.0022},
            "658": {"tier": "N", "flat_rate": 0.12},
        },
    }


@step(r"market risk components are calculated")
def when_market_risk_calculated(context: Context) -> None:
    context.last_response = context.client.post("/margin/market-risk-components", context.data["market_risk"])


@step(r"portfolio margin and flat rate margin components are returned")
def then_components_returned(context: Context) -> None:
    _assert_status(context, "calculated")
    types = {component["component_type"] for component in context.last_response.body["components"]}
    assert types == {"portfolio_margin", "flat_rate_margin"}


@step(r"the HKv13 flat rate margin example portfolio is prepared")
def given_hkv13_flat_rate_example(context: Context) -> None:
    context.data["flat_rate_margin"] = {
        "positions": [
            {
                "instrument_id": "3457",
                "quantity": -1,
                "market_value": -1000000,
                "flat_rate_subcategory": "1",
            },
            {
                "instrument_id": "3456",
                "quantity": 10000,
                "market_value": 1300000,
                "flat_rate_subcategory": "1",
            },
            {
                "instrument_id": "658",
                "quantity": -10000000,
                "market_value": -60000000,
                "flat_rate_subcategory": "2",
            },
            {
                "instrument_id": "3606",
                "quantity": 1000000,
                "market_value": 30000000,
                "flat_rate_subcategory": "2",
            },
        ],
        "flat_rates": {
            "3456": 0.30,
            "3457": 0.30,
            "658": 0.12,
            "3606": 0.12,
        },
        "flat_rate_margin_multiplier": 2,
    }


@step(r"flat rate margin is calculated under section 3\.2\.4\.2")
def when_flat_rate_margin_calculated(context: Context) -> None:
    context.last_response = context.client.post("/margin/flat-rate", context.data["flat_rate_margin"])


@step(r"only dominant-side positions per sub-category are included")
def then_dominant_sides_included(context: Context) -> None:
    _assert_status(context, "calculated")
    subcategories = context.last_response.body["subcategories"]
    assert subcategories["1"]["included_side"] == "long"
    assert subcategories["2"]["included_side"] == "short"
    included_ids = {
        item["instrument_id"]
        for group in subcategories.values()
        for item in group["included_positions"]
    }
    assert included_ids == {"3456", "658"}


@step(r"the flat rate margin equals 15,180,000 HKD")
def then_flat_rate_margin_expected(context: Context) -> None:
    _assert_status(context, "calculated")
    assert context.last_response.body["pre_multiplier_margin"] == 7590000
    assert context.last_response.body["flat_rate_margin"] == 15180000


@step(r"market risk total is below a rounding unit")
def given_market_risk_below_rounding(context: Context) -> None:
    context.data["aggregate"] = {
        "market_risk_total": 123456,
        "rounding": 10000,
        "favorable_mtm": 3000,
        "margin_credit": 2000,
        "other_components": {"position_limit_add_on": 1000},
    }


@step(r"the margin is aggregated")
def when_margin_aggregated(context: Context) -> None:
    context.last_response = context.client.post("/margin/aggregate", context.data["aggregate"])


@step(r"the market risk is rounded up before offsets and add-ons")
def then_market_risk_rounded(context: Context) -> None:
    _assert_status(context, "calculated")
    assert context.last_response.body["rounded_market_risk"] == 130000
    assert context.last_response.body["total_margin_requirement"] == 126000


@step(r"MTM items net to a favorable MTM amount")
def given_favorable_mtm(context: Context) -> None:
    context.data["mtm"] = {"items": [{"mtm_hkd": -2000}, {"mtm_hkd": 500}]}


@step(r"MTM is calculated")
def when_mtm_calculated(context: Context) -> None:
    context.last_response = context.client.post("/margin/mtm", context.data["mtm"])


@step(r"favorable MTM is separated from MTM requirement")
def then_favorable_mtm_separated(context: Context) -> None:
    _assert_status(context, "calculated")
    assert context.last_response.body["favorable_mtm"] == 1500
    assert context.last_response.body["mtm_requirement"] == 0


@step(r"a stock split and cash dividend apply before the ex-date")
def given_corporate_actions(context: Context) -> None:
    context.data["corporate_actions"] = {
        "positions": [{"instrument_id": "5", "quantity": 400, "contract_value": 24000}],
        "corporate_actions": [
            {
                "instrument_id": "5",
                "converted_instrument_id": "5",
                "quantity_conversion_ratio": 2,
                "cash_dividend_code": "DIV5",
                "cash_dividend_amount": 0.78,
            }
        ],
    }


@step(r"corporate action adjustment is performed")
def when_corporate_actions_adjusted(context: Context) -> None:
    context.last_response = context.client.post("/corporate-actions/adjust", context.data["corporate_actions"])


@step(r"the adjusted position and benefit entitlement position are produced")
def then_corporate_actions_produced(context: Context) -> None:
    _assert_status(context, "calculated")
    positions = context.last_response.body["positions"]
    assert any(item["instrument_id"] == "5" and item["quantity"] == 800 for item in positions)
    assert any(item["instrument_id"] == "DIV5" and item["quantity"] == 0 for item in positions)


@step(r"positions exist across trade dates for the same instrument")
def given_cross_day_positions(context: Context) -> None:
    context.data["netting"] = {
        "positions": [
            {"instrument_id": "5", "quantity": 400, "contract_value": 24000},
            {"instrument_id": "5", "quantity": -600, "contract_value": -36600},
            {"instrument_id": "5", "quantity": 1200, "contract_value": 73200},
        ],
        "market_prices": {"5": 70},
    }


@step(r"cross-day netting is performed")
def when_cross_day_netting(context: Context) -> None:
    context.last_response = context.client.post("/positions/cross-day-net", context.data["netting"])


@step(r"one netted position is returned for the instrument")
def then_one_netted_position(context: Context) -> None:
    _assert_status(context, "calculated")
    position = context.last_response.body["positions"][0]
    assert position["instrument_id"] == "5"
    assert position["quantity"] == 1000
    assert position["market_value"] == 70000


@step(r"MTM exists in multiple currencies with FX haircuts")
def given_cross_currency_mtm(context: Context) -> None:
    context.data["cross_currency"] = {
        "items": [
            {"currency": "HKD", "mtm": -2000},
            {"currency": "CNY", "mtm": 1300},
            {"currency": "USD", "mtm": -50},
        ],
        "fx_rates": {"HKD": 1, "CNY": 1.15, "USD": 7.8},
        "haircuts": {"HKD": 0, "CNY": 0.03, "USD": 0.01},
    }


@step(r"cross-currency MTM netting is performed")
def when_cross_currency_mtm(context: Context) -> None:
    context.last_response = context.client.post("/mtm/cross-currency-net", context.data["cross_currency"])


@step(r"positive and favorable MTM use directional haircut conversion")
def then_directional_haircut(context: Context) -> None:
    _assert_status(context, "calculated")
    converted = context.last_response.body["converted_hkd"]
    assert converted["CNY"] == 1539.85
    assert converted["USD"] == -386.1


@step(r"due-today long positions and an offset ratio exist at 11:00")
def given_intraday_11(context: Context) -> None:
    context.data["intraday"] = {
        "run_time_hkt": "11:00",
        "offset_ratio": 0.25,
        "positions": [
            {"instrument_id": "700", "quantity": 100, "contract_value": 20000, "due_today": True},
            {"instrument_id": "80737", "quantity": -1000, "contract_value": -6000, "due_today": False},
        ],
    }


@step(r"intraday MTM treatment is applied")
def when_intraday_applied(context: Context) -> None:
    context.last_response = context.client.post("/mtm/intraday", context.data["intraday"])


@step(r"the due-today long position is reduced by the offset ratio")
def then_due_position_reduced(context: Context) -> None:
    _assert_status(context, "calculated")
    position = context.last_response.body["positions"][0]
    assert position["quantity"] == 75
    assert position["contract_value"] == 15000


@step(r"due-today positions exist at 14:00")
def given_intraday_14(context: Context) -> None:
    context.data["intraday"] = {
        "run_time_hkt": "14:00",
        "positions": [
            {"instrument_id": "700", "quantity": 100, "contract_value": 20000, "due_today": True},
            {"instrument_id": "80737", "quantity": -1000, "contract_value": -6000, "due_today": False},
        ],
    }


@step(r"due-today positions are excluded")
def then_due_positions_excluded(context: Context) -> None:
    _assert_status(context, "calculated")
    positions = context.last_response.body["positions"]
    assert len(positions) == 1
    assert positions[0]["instrument_id"] == "80737"
