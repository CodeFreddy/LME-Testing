"""Executable BDD step definitions for the Mock LME API.

These steps are intentionally written as normal Python functions so the package
can run without Behave. The included mini runner dispatches Gherkin step text to
the regex patterns registered here. The same HTTP calls can be copied into a
Behave step library later if the project adopts a real BDD runner.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from mock_lme_api.client import MockLMEClient


StepFunc = Callable[..., None]


@dataclass
class Context:
    client: MockLMEClient = field(default_factory=MockLMEClient)
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


@step(r"a capitalised term is used without a local definition")
def given_capitalised_term_without_definition(context: Context) -> None:
    context.data["terminology"] = {
        "term": "Business Day",
        "defined_in_document": False,
        "rulebook_meaning": "A day on which the LME is open for business",
    }


@step(r"the term is interpreted according to the LME Rulebook")
def when_interpreted_rulebook(context: Context) -> None:
    context.last_response = context.client.post("/terminology/validate", context.data["terminology"])


@step(r"the terminology validation is accepted with LME Rulebook source")
def then_terminology_accepted(context: Context) -> None:
    _assert_status(context, "accepted")
    assert context.last_response.body.get("source") == "LME Rulebook"


@step(r"an order or trade fails the price validation check")
def given_trade_fails_price_validation(context: Context) -> None:
    context.data["trade"] = {
        "trade_id": "TRADE-PVF-001",
        "price": 1500,
        "reference_price": 2000,
        "tolerance": 0.10,
    }
    context.last_response = context.client.post("/trades/validate-price", {"trade": context.data["trade"]})
    _assert_status(context, "failed_checks")


@step(r"the Member contacts the Exchange to explain the rationale as to the price")
def when_member_contacts_exchange(context: Context) -> None:
    context.last_response = context.client.post(
        "/trades/contact-exchange",
        {"trade_id": context.data["trade"]["trade_id"], "rationale": "fat finger price entry"},
    )


@step(r"the contact action is recorded as compliant")
def then_contact_recorded(context: Context) -> None:
    _assert_status(context, "recorded")
    assert context.last_response.body.get("compliance") == "COMPLIANT"


@step(r"the Member does not contact the Exchange to explain the rationale")
def when_member_does_not_contact(context: Context) -> None:
    context.last_response = context.client.post(
        "/trades/contact-exchange",
        {"trade_id": context.data["trade"]["trade_id"], "rationale": ""},
    )


@step(r"the contact obligation is rejected for missing rationale")
def then_missing_rationale_rejected(context: Context) -> None:
    _assert_status(context, "rejected")
    assert context.last_response.reason == "missing_rationale"


@step(r"a post-trade request has a relevant deadline")
def given_relevant_deadline(context: Context) -> None:
    context.data["deadline_at"] = datetime(2026, 4, 23, 20, 0, tzinfo=timezone.utc)


@step(r"the request is submitted (\d+) minutes before the relevant deadline")
def when_request_submitted_minutes_before(context: Context, minutes: str) -> None:
    submitted = context.data["deadline_at"] - timedelta(minutes=int(minutes))
    context.last_response = context.client.post(
        "/deadlines/validate",
        {
            "deadline_at": context.data["deadline_at"].isoformat(),
            "submitted_at": submitted.isoformat(),
        },
    )


@step(r"the request is accepted as timely")
def then_request_accepted_timely(context: Context) -> None:
    _assert_status(context, "accepted")
    assert context.last_response.body.get("result") == "pass"


@step(r"the request is rejected as a late submission")
def then_request_rejected_late(context: Context) -> None:
    _assert_status(context, "rejected")
    assert context.last_response.reason == "late_submission"


@step(r"an Asian business hours Client Contract is prepared")
def given_asian_client_contract(context: Context) -> None:
    context.data["trade"] = {
        "trade_id": "TRADE-ASIA-001",
        "category": "Normal",
        "venue": "Inter-office",
        "account": "C",
        "client_contract": True,
        "asian_business_hours": True,
        "submitted_at": "2026-04-23T08:29:00Z",
    }


@step(r"the trade is submitted to the Matching System")
def when_trade_submitted(context: Context) -> None:
    context.last_response = context.client.post("/trades/submit", {"trade": context.data["trade"]})


@step(r"the trade submission is accepted")
def then_trade_submission_accepted(context: Context) -> None:
    _assert_status(context, "accepted")


@step(r"an Asian business hours Client Contract is submitted after 08:30 London time")
def given_late_asian_client_contract(context: Context) -> None:
    context.data["trade"] = {
        "trade_id": "TRADE-ASIA-LATE-001",
        "category": "Normal",
        "venue": "Inter-office",
        "account": "C",
        "client_contract": True,
        "asian_business_hours": True,
        "submitted_at": "2026-04-23T08:31:00Z",
    }


@step(r"the trade submission is rejected for missing the Asian-hours deadline")
def then_trade_rejected_asian_deadline(context: Context) -> None:
    _assert_status(context, "rejected")
    assert "asian_hours_client_contract_late" in context.last_response.body.get("errors", [])


@step(r"a Give-Up Executor trade half is entered within 10 minutes")
def given_giveup_executor_within_10(context: Context) -> None:
    context.data["giveup"] = {
        "trade_id": "GIVEUP-001",
        "venue": "Inter-office",
        "minutes_after_execution": 9,
        "account": "H",
        "counterparty": "UNA",
    }


@step(r"the Give-Up trade is submitted")
def when_giveup_submitted(context: Context) -> None:
    context.last_response = context.client.post("/giveups/submit", {"trade": context.data["giveup"]})


@step(r"the Matching System generates a Give-Up Clearer half with U account")
def then_giveup_clearer_generated(context: Context) -> None:
    _assert_status(context, "accepted")
    generated = context.last_response.body.get("generated_clearer_half")
    assert generated and generated.get("account") == "U"


@step(r"an OTC Bring-On transaction has complete prior OTC evidence")
def given_otc_bring_on_complete(context: Context) -> None:
    context.data["otc"] = {
        "category": "OTC Bring-On",
        "pre_existing_otc_contract": True,
        "booked_by_both_counterparties": True,
        "documented": True,
        "original_trade_date": "2026-04-20",
        "bring_on_trade_date": "2026-04-23",
    }


@step(r"the OTC Bring-On transaction is validated")
def when_otc_validated(context: Context) -> None:
    context.last_response = context.client.post("/otc-bring-ons/validate", {"transaction": context.data["otc"]})


@step(r"the OTC Bring-On transaction is accepted")
def then_otc_accepted(context: Context) -> None:
    _assert_status(context, "accepted")


@step(r"an auction bid has an invalid Auction ID")
def given_invalid_auction_bid(context: Context) -> None:
    context.data["auction_bid"] = {
        "auction_id_valid": False,
        "fixed_parameters_valid": True,
        "category": "Normal",
        "price_type": "Current",
        "venue": "Inter-office",
    }


@step(r"the auction bid is submitted")
def when_auction_bid_submitted(context: Context) -> None:
    context.last_response = context.client.post("/auctions/bids", {"bid": context.data["auction_bid"]})


@step(r"the auction bid is rejected for invalid or expired Auction ID")
def then_auction_bid_rejected_id(context: Context) -> None:
    _assert_status(context, "rejected")
    assert "invalid_or_expired_auction_id" in context.last_response.body.get("errors", [])


@step(r"an Inter-Office order uses OTC Bring-On to avoid PTT")
def given_ptt_avoidance_order(context: Context) -> None:
    context.data["ptt"] = {
        "uses_otc_bring_on": True,
        "purpose": "avoid_ptt",
        "venue": "Inter-office",
    }


@step(r"the PTT applicability is validated")
def when_ptt_validated(context: Context) -> None:
    context.last_response = context.client.post("/ptt/validate", {"order": context.data["ptt"]})


@step(r"the order is rejected for misuse of OTC Bring-On")
def then_ptt_rejected(context: Context) -> None:
    _assert_status(context, "rejected")
    assert context.last_response.reason == "misuse_otc_bring_on_to_avoid_ptt"

