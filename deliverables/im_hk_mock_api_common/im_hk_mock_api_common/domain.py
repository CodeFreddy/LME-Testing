"""Deterministic rule checks for the Initial Margin HKv13 mock API."""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

from .rules import REQUIRED_RPF_GLOBAL_FIELDS, SUPPORTED_FIELD_TYPES


def response(ok: bool, status: str, reason: str | None = None, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"ok": ok, "status": status}
    if reason:
        payload["reason"] = reason
    payload.update(extra)
    return payload


def _amount(value: Any) -> float:
    return float(value or 0)


def _round_up(value: float, unit: float) -> float:
    if unit <= 0:
        return value
    return math.ceil(value / unit) * unit


def validate_rpf(payload: dict[str, Any]) -> dict[str, Any]:
    rpf = payload.get("risk_parameter_file", {})
    global_fields = set(rpf.get("global_fields", {}).keys())
    records = rpf.get("records", [])
    missing = sorted(REQUIRED_RPF_GLOBAL_FIELDS - global_fields)
    field_types = {int(record.get("FieldType", 0)) for record in records}
    unsupported = sorted(field_types - SUPPORTED_FIELD_TYPES)
    if missing:
        return response(False, "rejected", "missing_global_fields", missing=missing)
    if unsupported:
        return response(False, "rejected", "unsupported_field_type", unsupported=unsupported)
    if not field_types:
        return response(False, "rejected", "missing_field_type_records")
    return response(True, "accepted", field_types=sorted(field_types), record_count=len(records))


def normalize_positions(payload: dict[str, Any]) -> dict[str, Any]:
    normalized: list[dict[str, Any]] = []
    errors: list[str] = []
    for position in payload.get("positions", []):
        quantity = _amount(position.get("quantity"))
        market_price = _amount(position.get("market_price"))
        if "instrument_id" not in position:
            errors.append("missing_instrument_id")
        market_value = quantity * market_price
        item = dict(position)
        item["market_value"] = round(market_value, 2)
        normalized.append(item)
    if errors:
        return response(False, "rejected", ",".join(sorted(set(errors))), errors=sorted(set(errors)))
    return response(True, "accepted", positions=normalized)


def calculate_market_risk_components(payload: dict[str, Any]) -> dict[str, Any]:
    portfolio = payload.get("portfolio", {})
    parameters = payload.get("parameters", {})
    components: list[dict[str, Any]] = []
    total = 0.0
    for position in portfolio.get("positions", []):
        instrument_id = str(position.get("instrument_id"))
        quantity = abs(_amount(position.get("quantity")))
        market_value = abs(_amount(position.get("market_value")))
        p = parameters.get(instrument_id, {})
        tier = p.get("tier", "P")
        if tier == "P":
            hvar = market_value * _amount(p.get("hvar_rate"))
            svar = market_value * _amount(p.get("svar_rate"))
            amount = hvar * _amount(parameters.get("HVaR_WGT", 0.75)) + svar * _amount(parameters.get("SVaR_WGT", 0.25))
            component_type = "portfolio_margin"
        else:
            amount = market_value * _amount(p.get("flat_rate"))
            component_type = "flat_rate_margin"
        lra = max(0.0, quantity * _amount(p.get("cash_delta", 0)) - _amount(p.get("delta_threshold", 0))) * _amount(p.get("bucket_rate", 0))
        structured = market_value * _amount(p.get("structured_product_add_on_rate", 0))
        component_total = amount + lra + structured
        total += component_total
        components.append(
            {
                "instrument_id": instrument_id,
                "component_type": component_type,
                "base_margin": round(amount, 2),
                "liquidation_risk_add_on": round(lra, 2),
                "structured_product_add_on": round(structured, 2),
                "total": round(component_total, 2),
            }
        )
    return response(True, "calculated", components=components, market_risk_total=round(total, 2))


def calculate_flat_rate_margin(payload: dict[str, Any]) -> dict[str, Any]:
    positions = payload.get("positions", [])
    flat_rates = {str(key): _amount(value) for key, value in payload.get("flat_rates", {}).items()}
    multiplier = _amount(payload.get("flat_rate_margin_multiplier", 1))

    subcategories: dict[str, dict[str, Any]] = {}
    for position in positions:
        subcategory = str(position.get("flat_rate_subcategory"))
        side = "long" if _amount(position.get("quantity")) >= 0 else "short"
        group = subcategories.setdefault(
            subcategory,
            {"long_total": 0.0, "short_total": 0.0, "included_side": None, "included_positions": []},
        )
        group[f"{side}_total"] += abs(_amount(position.get("market_value")))

    for subcategory, group in subcategories.items():
        group["included_side"] = "long" if group["long_total"] >= group["short_total"] else "short"
        included_positions = []
        for position in positions:
            if str(position.get("flat_rate_subcategory")) != subcategory:
                continue
            side = "long" if _amount(position.get("quantity")) >= 0 else "short"
            if side == group["included_side"]:
                instrument_id = str(position.get("instrument_id"))
                absolute_market_value = abs(_amount(position.get("market_value")))
                flat_rate = flat_rates.get(instrument_id)
                if flat_rate is None:
                    return response(False, "rejected", "missing_flat_rate", instrument_id=instrument_id)
                included_positions.append(
                    {
                        "instrument_id": instrument_id,
                        "side": side,
                        "absolute_market_value": round(absolute_market_value, 2),
                        "flat_rate": flat_rate,
                        "margin": round(absolute_market_value * flat_rate, 2),
                    }
                )
        group["included_positions"] = included_positions

    pre_multiplier_margin = sum(
        item["margin"]
        for group in subcategories.values()
        for item in group["included_positions"]
    )
    return response(
        True,
        "calculated",
        subcategories=subcategories,
        pre_multiplier_margin=round(pre_multiplier_margin, 2),
        flat_rate_margin_multiplier=multiplier,
        flat_rate_margin=round(pre_multiplier_margin * multiplier, 2),
    )


def calculate_mtm(payload: dict[str, Any]) -> dict[str, Any]:
    mtm_total = sum(_amount(item.get("mtm_hkd")) for item in payload.get("items", []))
    favorable_mtm = abs(mtm_total) if mtm_total < 0 else 0.0
    mtm_requirement = mtm_total if mtm_total > 0 else 0.0
    return response(
        True,
        "calculated",
        mtm_hkd=round(mtm_total, 2),
        favorable_mtm=round(favorable_mtm, 2),
        mtm_requirement=round(mtm_requirement, 2),
    )


def aggregate_margin(payload: dict[str, Any]) -> dict[str, Any]:
    market_risk_total = _amount(payload.get("market_risk_total"))
    rounding = _amount(payload.get("rounding", 1))
    favorable_mtm = _amount(payload.get("favorable_mtm"))
    margin_credit = _amount(payload.get("margin_credit"))
    other_components = sum(_amount(value) for value in payload.get("other_components", {}).values())
    rounded_market_risk = _round_up(market_risk_total, rounding)
    total = max(0.0, rounded_market_risk - favorable_mtm - margin_credit + other_components)
    return response(
        True,
        "calculated",
        rounded_market_risk=round(rounded_market_risk, 2),
        total_margin_requirement=round(total, 2),
    )


def adjust_corporate_actions(payload: dict[str, Any]) -> dict[str, Any]:
    positions = payload.get("positions", [])
    actions = payload.get("corporate_actions", [])
    adjusted = [dict(position) for position in positions]
    for action in actions:
        original = str(action.get("instrument_id"))
        conversion_ratio = _amount(action.get("quantity_conversion_ratio", 1))
        for position in list(adjusted):
            if str(position.get("instrument_id")) != original:
                continue
            original_quantity = _amount(position.get("quantity"))
            position["instrument_id"] = str(action.get("converted_instrument_id", original))
            position["quantity"] = round(original_quantity * conversion_ratio, 6)
            if action.get("cash_dividend_code"):
                adjusted.append(
                    {
                        "instrument_id": action["cash_dividend_code"],
                        "quantity": 0,
                        "contract_value": round(original_quantity * _amount(action.get("cash_dividend_amount")), 2),
                    }
                )
            if action.get("stock_dividend_code"):
                adjusted.append(
                    {
                        "instrument_id": action["stock_dividend_code"],
                        "quantity": round(original_quantity * _amount(action.get("entitled_stock_quantity")), 6),
                        "contract_value": 0,
                    }
                )
            if action.get("rights_code"):
                adjusted.append(
                    {
                        "instrument_id": action["rights_code"],
                        "quantity": round(original_quantity * _amount(action.get("rights_quantity")), 6),
                        "contract_value": 0,
                    }
                )
    return response(True, "calculated", positions=adjusted)


def cross_day_net(payload: dict[str, Any]) -> dict[str, Any]:
    grouped: dict[str, dict[str, Any]] = {}
    for position in payload.get("positions", []):
        instrument = str(position.get("instrument_id"))
        group = grouped.setdefault(instrument, {"instrument_id": instrument, "quantity": 0.0, "contract_value": 0.0})
        group["quantity"] += _amount(position.get("quantity"))
        group["contract_value"] += _amount(position.get("contract_value"))
    netted = []
    for group in grouped.values():
        market_price = _amount(payload.get("market_prices", {}).get(group["instrument_id"]))
        group["market_value"] = round(group["quantity"] * market_price, 2)
        group["quantity"] = round(group["quantity"], 6)
        group["contract_value"] = round(group["contract_value"], 2)
        netted.append(group)
    return response(True, "calculated", positions=sorted(netted, key=lambda item: item["instrument_id"]))


def cross_currency_net(payload: dict[str, Any]) -> dict[str, Any]:
    by_currency: dict[str, float] = defaultdict(float)
    for item in payload.get("items", []):
        by_currency[str(item.get("currency", "HKD"))] += _amount(item.get("mtm"))
    total_hkd = 0.0
    converted: dict[str, float] = {}
    for currency, mtm in by_currency.items():
        fx = _amount(payload.get("fx_rates", {}).get(currency, 1))
        haircut = _amount(payload.get("haircuts", {}).get(currency, 0))
        multiplier = 1 + haircut if mtm > 0 else 1 - haircut
        hkd = mtm * fx * multiplier
        converted[currency] = round(hkd, 2)
        total_hkd += hkd
    favorable_mtm = abs(total_hkd) if total_hkd < 0 else 0.0
    mtm_requirement = total_hkd if total_hkd > 0 else 0.0
    return response(
        True,
        "calculated",
        converted_hkd=converted,
        mtm_hkd=round(total_hkd, 2),
        favorable_mtm=round(favorable_mtm, 2),
        mtm_requirement=round(mtm_requirement, 2),
    )


def intraday_mtm(payload: dict[str, Any]) -> dict[str, Any]:
    run_time = str(payload.get("run_time_hkt"))
    positions = payload.get("positions", [])
    if run_time == "11:00":
        offset_ratio = _amount(payload.get("offset_ratio"))
        adjusted = []
        for position in positions:
            item = dict(position)
            if item.get("due_today") and _amount(item.get("quantity")) > 0:
                item["quantity"] = round(_amount(item.get("quantity")) * (1 - offset_ratio), 6)
                item["contract_value"] = round(_amount(item.get("contract_value")) * (1 - offset_ratio), 2)
            adjusted.append(item)
        return response(True, "calculated", positions=adjusted, treatment="cash_prepayment_or_unposted_credit_offset")
    if run_time == "14:00":
        remaining = [dict(position) for position in positions if not position.get("due_today")]
        return response(True, "calculated", positions=remaining, treatment="due_today_positions_excluded")
    return response(False, "rejected", "unsupported_intraday_run_time")
