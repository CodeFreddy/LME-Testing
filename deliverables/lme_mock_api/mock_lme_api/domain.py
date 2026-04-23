"""Deterministic rule checks for the LME Matching Rules mock API."""

from __future__ import annotations

from datetime import datetime, time, timezone
from typing import Any

from .rules import VALID_ACCOUNTS, VALID_AUCTION_TUPLE, VALID_TRADE_CATEGORIES, VALID_VENUES


def parse_iso(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value).astimezone(timezone.utc)


def response(ok: bool, status: str, reason: str | None = None, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"ok": ok, "status": status}
    if reason:
        payload["reason"] = reason
    payload.update(extra)
    return payload


def validate_terminology(payload: dict[str, Any]) -> dict[str, Any]:
    term = payload.get("term", "")
    defined_in_document = bool(payload.get("defined_in_document", False))
    supplied_meaning = payload.get("supplied_meaning")
    rulebook_meaning = payload.get("rulebook_meaning", "LME Rulebook meaning")
    if not term:
        return response(False, "rejected", "missing_term")
    if defined_in_document:
        return response(True, "accepted", source="document")
    if supplied_meaning and supplied_meaning != rulebook_meaning:
        return response(False, "rejected", "TERM_DEVIATION", source="LME Rulebook")
    return response(True, "accepted", source="LME Rulebook", meaning=rulebook_meaning)


def validate_price(payload: dict[str, Any]) -> dict[str, Any]:
    trade = payload.get("trade", {})
    price = float(trade.get("price", 0))
    reference_price = float(trade.get("reference_price", 0))
    tolerance = float(trade.get("tolerance", 0.10))
    if reference_price <= 0:
        return response(False, "rejected", "missing_reference_price")
    deviation = abs(price - reference_price) / reference_price
    if deviation > tolerance:
        return response(False, "failed_checks", "price_validation_failed", deviation=round(deviation, 6))
    return response(True, "passed", deviation=round(deviation, 6))


def contact_exchange(payload: dict[str, Any]) -> dict[str, Any]:
    trade_id = payload.get("trade_id")
    rationale = payload.get("rationale")
    if not trade_id:
        return response(False, "rejected", "missing_trade_id")
    if not rationale:
        return response(False, "rejected", "missing_rationale")
    return response(True, "recorded", contact_id=f"CONT-{trade_id}", compliance="COMPLIANT")


def validate_resubmission(payload: dict[str, Any]) -> dict[str, Any]:
    failed_checks = bool(payload.get("failed_checks"))
    additional_info_required = bool(payload.get("additional_info_required"))
    additional_info = payload.get("additional_information")
    if not failed_checks:
        return response(True, "not_required")
    if additional_info_required and not additional_info:
        return response(False, "rejected", "additional_information_required")
    return response(True, "permitted", validation_result="ACCEPTED")


def validate_deadline(payload: dict[str, Any]) -> dict[str, Any]:
    deadline = parse_iso(payload["deadline_at"])
    submitted = parse_iso(payload["submitted_at"])
    minutes_before = (deadline - submitted).total_seconds() / 60
    if minutes_before >= 15:
        return response(True, "accepted", result="pass", minutes_before=minutes_before)
    return response(False, "rejected", "late_submission", result="fail", minutes_before=minutes_before)


def submit_trade(payload: dict[str, Any]) -> dict[str, Any]:
    trade = payload.get("trade", {})
    errors: list[str] = []
    category = trade.get("category", "Normal")
    venue = trade.get("venue")
    account = trade.get("account")
    if category not in VALID_TRADE_CATEGORIES:
        errors.append("invalid_trade_category")
    if venue not in VALID_VENUES:
        errors.append("invalid_venue")
    if account and account not in VALID_ACCOUNTS:
        errors.append("invalid_account")

    # Paragraph 7: Asian-hours Client Contracts must be submitted by 08:30.
    if trade.get("client_contract") and trade.get("asian_business_hours"):
        submitted_at = parse_iso(trade["submitted_at"])
        cutoff = time(8, 30)
        if submitted_at.time() > cutoff:
            errors.append("asian_hours_client_contract_late")

    if errors:
        return response(False, "rejected", ",".join(errors), errors=errors)
    return response(True, "accepted", trade_id=trade.get("trade_id", "TRADE-001"))


def validate_audit(payload: dict[str, Any]) -> dict[str, Any]:
    trail = payload.get("audit_trail", {})
    required = {"orders", "trades", "post_trade_operations"}
    present = {k for k, v in trail.items() if v}
    missing = sorted(required - present)
    if missing:
        return response(False, "rejected", "incomplete_audit_trail", missing=missing)
    return response(True, "accepted")


def submit_giveup(payload: dict[str, Any]) -> dict[str, Any]:
    trade = payload.get("trade", {})
    errors: list[str] = []
    if trade.get("venue") != "Inter-office":
        errors.append("giveup_venue_must_be_inter_office")
    if int(trade.get("minutes_after_execution", 0)) > 10:
        errors.append("giveup_late")
    if trade.get("account") != "H":
        errors.append("giveup_executor_account_must_be_H")
    if trade.get("counterparty") == "UNA":
        generated = {"counterparty": "UNA", "account": "U", "status": "system_generated"}
    else:
        generated = None
    if errors:
        return response(False, "rejected", ",".join(errors), errors=errors)
    return response(True, "accepted", generated_clearer_half=generated)


def validate_otc_bring_on(payload: dict[str, Any]) -> dict[str, Any]:
    tx = payload.get("transaction", {})
    errors: list[str] = []
    if tx.get("category") != "OTC Bring-On":
        errors.append("category_must_be_otc_bring_on")
    if not tx.get("pre_existing_otc_contract"):
        errors.append("missing_pre_existing_otc_contract")
    if not tx.get("booked_by_both_counterparties"):
        errors.append("not_booked_by_both_counterparties")
    if not tx.get("documented"):
        errors.append("not_documented")
    if tx.get("original_trade_date") and tx.get("bring_on_trade_date"):
        if tx["original_trade_date"] >= tx["bring_on_trade_date"]:
            errors.append("original_trade_date_must_precede_bring_on")
    if errors:
        return response(False, "rejected", ",".join(errors), errors=errors)
    return response(True, "accepted")


def submit_auction_bid(payload: dict[str, Any]) -> dict[str, Any]:
    bid = payload.get("bid", {})
    errors: list[str] = []
    if not bid.get("auction_id_valid", False):
        errors.append("invalid_or_expired_auction_id")
    if not bid.get("fixed_parameters_valid", False):
        errors.append("invalid_fixed_parameters")
    for field, expected in VALID_AUCTION_TUPLE.items():
        if bid.get(field) != expected:
            errors.append(f"{field}_must_be_{expected}")
    if errors:
        return response(False, "rejected", ",".join(errors), errors=errors)
    return response(True, "accepted")


def validate_ptt(payload: dict[str, Any]) -> dict[str, Any]:
    order = payload.get("order", {})
    if order.get("uses_otc_bring_on") and order.get("purpose") == "avoid_ptt":
        return response(False, "rejected", "misuse_otc_bring_on_to_avoid_ptt")
    return response(True, "accepted")

