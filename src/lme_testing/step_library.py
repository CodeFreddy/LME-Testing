"""Python step definition registry for LME-Testing.

A centralized, language-consistent step definition library where step_text keys
exactly match the output of the BDD LLM (MiniMax-M2.7).

Architecture:
    BDD LLM emits step_text + step_pattern + code (Python) in normalized BDD.
    STEP_LIBRARY provides canonical Python implementations keyed by step_text.
    step_registry.py matches BDD steps against this library using
    exact/parameterized/TF-IDF candidate matching.

Usage:
    from lme_testing.step_library import STEP_LIBRARY, step, extract_pattern
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable


class StepType(Enum):
    GIVEN = "given"
    WHEN = "when"
    THEN = "then"


@dataclass
class PythonStepDefinition:
    """A single Python step definition entry."""

    step_type: str  # "given" | "when" | "then"
    step_text: str  # natural language key (exact match to BDD LLM output)
    step_pattern: str  # regex pattern for parameterized matching
    function_name: str  # Python-safe identifier
    code: str  # full Python function code (decorated)

    def render(self) -> str:
        """Render the step as a Python function definition."""
        return self.code


STEP_LIBRARY: dict[str, PythonStepDefinition] = {}
"""Global step definition registry keyed by step_text."""


def step(step_text: str, step_type: StepType) -> Callable:
    """Decorator to register a Python step definition.

    Usage:
        @step("the member contacts the Exchange", StepType.THEN)
        def step_member_contacts_exchange():
            contact_response = LME.PostTrade.contact_exchange(...)
            assert contact_response is not None
    """
    def decorator(fn: Callable) -> Callable:
        fn_name = fn.__name__
        pattern = extract_pattern(step_text)
        code = _build_decorated_code(step_type.value, step_text, fn_name, _extract_body(fn))
        STEP_LIBRARY[step_text] = PythonStepDefinition(
            step_type=step_type.value,
            step_text=step_text,
            step_pattern=pattern,
            function_name=fn_name,
            code=code,
        )
        return fn
    return decorator


def _extract_body(fn: Callable) -> str:
    """Extract the indented body of a function as a string."""
    import inspect
    try:
        source_lines = inspect.getsource(fn).splitlines()
    except OSError:
        return "    pass  # implementation needed"
    # Find the def line and grab everything after it
    def_idx = 0
    for i, line in enumerate(source_lines):
        if line.strip().startswith("def "):
            def_idx = i
            break
    body_lines = source_lines[def_idx + 1 :]
    if not body_lines:
        return "    pass"
    # Dedent by the minimum indentation of non-empty lines
    non_empty = [ln for ln in body_lines if ln.strip()]
    if not non_empty:
        return "    pass"
    min_indent = min(len(ln) - len(ln.lstrip()) for ln in non_empty)
    dedented = [ln[min_indent:] if ln.strip() else "" for ln in body_lines]
    return "\n".join(dedented)


def _build_decorated_code(step_type: str, step_text: str, fn_name: str, body: str) -> str:
    """Build the full decorated Python function as a string."""
    keyword = step_type.capitalize()
    step_call = f'@{keyword.lower()}("{_escape_text(step_text)}")'
    # Indent body by 4 spaces (Python requires function body to be indented)
    indented_body = "\n".join("    " + line if line else "    " for line in body.split("\n"))
    return f"{step_call}\ndef {fn_name}():\n{indented_body}"


def _escape_text(text: str) -> str:
    """Escape double-quotes in step_text for Python string literal."""
    return text.replace('"', '\\"')


def extract_pattern(text: str) -> str:
    """Convert natural language step text to a regex pattern.

    - Converts stopwords (a/an/the) to non-capturing alternation
    - Converts specific numbers (e.g. "16") to capture groups (\\d+)
    - Lowercases the result for case-insensitive matching
    """
    pattern = text
    pattern = re.sub(r"\b(a|an|the)\b", "(?:a|an|the)", pattern, flags=re.IGNORECASE)
    pattern = re.sub(r"\b(\d+)\b", r"(\\d+)", pattern)
    return pattern.lower()


# ---------------------------------------------------------------------------
# Given steps — from actual MiniMax BDD output + translated Ruby library
# ---------------------------------------------------------------------------

_SENTINEL = object()  # unique object to detect unused closures


def _lme_login(role: str = "member") -> str:
    return (
        "    session = LME.Client.login(\n"
        "        username=ENV.get('LME_USERNAME', 'test_trader'),\n"
        "        password=ENV.get('LME_PASSWORD', 'test_pass'),\n"
        "        role=role,\n"
        "    )\n"
        "    return session"
    )


@step("an order or trade has been submitted for processing", StepType.GIVEN)
def step_order_submitted_for_processing():
    session = LME.Client.login(
        username=ENV.get("LME_USERNAME", "test_trader"),
        password=ENV.get("LME_PASSWORD", "test_pass"),
    )
    order_params = {
        "metal": "ALU",
        "quantity": 25,
        "delivery_date": "2024-03-27",
    }
    # Price will be set by subsequent When steps


@step("the price validation check has been performed", StepType.GIVEN)
def step_price_validation_performed():
    # Assumes step_order_submitted_for_processing ran first
    validation_result = LME.api.check_price_validation(
        order_id="PENDING_ORDER_ID",
        metal="ALU",
    )
    assert validation_result is not None


@step("a request needs to be submitted to LME Post-Trade Operations", StepType.GIVEN)
def step_request_submitted_to_lme_post_trade():
    session = LME.Client.login(
        username=ENV.get("LME_USERNAME", "test_trader"),
        password=ENV.get("LME_PASSWORD", "test_pass"),
    )
    request_type = "post_trade_correction"


@step("a relevant deadline exists for the request", StepType.GIVEN)
def step_deadline_exists_for_request():
    deadline = LME.PostTrade.get_deadline(
        request_type="post_trade_correction",
    )
    assert deadline is not None
    assert deadline.get("active") is True


@step("a registered_intermediating_broker submits a document containing capitalised terms", StepType.GIVEN)
def step_broker_submits_capitalised_document():
    broker = LME.Client.registered_intermediary
    document = LME.API.create_document(
        broker=broker,
        terms="capitalised",
    )


@step("the terms are not otherwise defined within the document", StepType.GIVEN)
def step_terms_not_defined_in_document():
    document.terms_defined = False
    document.terms_conflict = False


@step("the terms are defined differently than in the LME Rulebook", StepType.GIVEN)
def step_terms_defined_differently():
    document.terms_defined = True
    document.terms_conflict = True


@step("Exchange defines matching rules", StepType.GIVEN)
def step_exchange_defines_matching_rules():
    rules = LME.PostTrade.define_matching_rules(version="1.0")


@step("business is transacted on the Exchange", StepType.GIVEN)
def step_business_transacted_on_exchange():
    session = LME.Client.login(
        username=ENV.get("LME_USERNAME", "test_trader"),
        password=ENV.get("LME_PASSWORD", "test_pass"),
    )


@step("trade submission resulted in Failed Checks", StepType.GIVEN)
def step_trade_submission_failed_checks():
    trade_params = {
        "price": "999999",
        "metal": "ALU",
        "quantity": 25,
    }
    trade_submission = LME.API.submit_trade(trade_params)
    assert trade_submission.status == "SUBMITTED"


@step("Exchange requested additional information", StepType.GIVEN)
def step_exchange_requested_additional_info():
    info_request = LME.PostTrade.get_info_request(trade_submission.id)
    assert info_request is not None


@step("Member provided the requested additional information", StepType.GIVEN)
def step_member_provided_additional_info():
    LME.PostTrade.provide_info(
        trade_submission.id,
        {"price_explanation": "Market volatility adjustment"},
    )


@step("LME trading environment is active", StepType.GIVEN)
def step_lme_trading_environment_active():
    env = LME.Client.environment
    assert env.status == "active"


# ---------------------------------------------------------------------------
# When steps — from actual MiniMax BDD output + translated Ruby library
# ---------------------------------------------------------------------------


@step("the order or trade fails the price validation check", StepType.WHEN)
def step_order_fails_price_validation():
    order_params["price"] = "999999"  # Intentionally invalid
    response = LME.API.submit_order(order_params)
    assert response.status == "rejected"


@step("the order or trade passes the price validation check", StepType.WHEN)
def step_order_passes_price_validation():
    order_params["price"] = "2500.00"
    response = LME.API.submit_order(order_params)
    assert response.status == "accepted"


@step("the system processes the document terminology", StepType.WHEN)
def step_system_processes_terminology():
    validation_result = LME.API.validate_terminology(document)


@step("the rules are submitted for adoption", StepType.WHEN)
def step_rules_submitted_for_adoption():
    adoption_status = LME.PostTrade.submit_adoption(rules)


@step("trade agreement occurs", StepType.WHEN)
def step_trade_agreement_occurs():
    trade_agreement = LME.PostTrade.create_agreement()


@step("the request is submitted (\\d+) minutes before the relevant deadline", StepType.WHEN)
def step_request_submitted_minutes_before(minutes: str):
    deadline_ts = deadline.get("timestamp")
    offset_seconds = int(minutes) * 60
    submitted_at = deadline_ts - offset_seconds
    response = LME.API.submit_request(
        request_type="post_trade_correction",
        submitted_at=submitted_at,
        session=session,
    )


@step("the request is submitted 16 minutes before the relevant deadline", StepType.WHEN)
def step_request_submitted_16min_before():
    deadline_ts = deadline.get("timestamp")
    submitted_at = deadline_ts - (16 * 60)
    response = LME.API.submit_request(
        request_type="post_trade_correction",
        submitted_at=submitted_at,
        session=session,
    )


@step("the request is submitted exactly 15 minutes before the relevant deadline", StepType.WHEN)
def step_request_submitted_exactly_15min_before():
    deadline_ts = deadline.get("timestamp")
    submitted_at = deadline_ts - (15 * 60)
    response = LME.API.submit_request(
        request_type="post_trade_correction",
        submitted_at=submitted_at,
        session=session,
    )


@step("the request is submitted 14 minutes before the relevant deadline", StepType.WHEN)
def step_request_submitted_14min_before():
    deadline_ts = deadline.get("timestamp")
    submitted_at = deadline_ts - (14 * 60)
    response = LME.API.submit_request(
        request_type="post_trade_correction",
        submitted_at=submitted_at,
        session=session,
    )


@step("the Member contacts the Exchange to explain the rationale for the price", StepType.WHEN)
def step_member_contacts_exchange_to_explain():
    contact_response = LME.PostTrade.contact_exchange(
        reason=validation_result.rejection_reason,
        member=session.member_id,
    )


@step("the Member does not contact the Exchange to explain the rationale for the price", StepType.WHEN)
def step_member_does_not_contact_exchange():
    # Intentionally does nothing — contact should not occur
    pass


@step("Member requests to re-submit the trade in its original form", StepType.WHEN)
def step_member_requests_resubmit():
    resubmission_response = LME.API.resubmit_trade(
        trade_submission.id,
        original_form=trade_params,
    )


@step("trade agreement occurs on any venue", StepType.WHEN)
def step_trade_agreement_on_any_venue():
    agreement = LME.PostTrade.create_agreement()


# ---------------------------------------------------------------------------
# Then steps — from actual MiniMax BDD output + translated Ruby library
# ---------------------------------------------------------------------------


@step("the terms are assigned the meaning ascribed in the LME Rulebook", StepType.THEN)
def step_terms_assigned_rulebook_meaning():
    assert validation_result.compliant is True
    assert validation_result.source == "LME Rulebook"


@step("the obligation is fulfilled", StepType.THEN)
def step_obligation_fulfilled():
    assert validation_result.status == "fulfilled"


@step("the system identifies the deviation from the LME Rulebook", StepType.THEN)
def step_system_identifies_deviation():
    assert validation_result.compliant is False
    assert "TERM_DEVIATION" in validation_result.errors


@step("the obligation is not fulfilled", StepType.THEN)
def step_obligation_not_fulfilled():
    assert validation_result.status == "rejected"


@step("the rules are recognized as part of Administrative Procedures", StepType.THEN)
def step_rules_recognized_administrative():
    assert adoption_status.adopted is True
    assert adoption_status.classification == "Administrative_Procedures"


@step("business is subject to price validation", StepType.THEN)
def step_business_subject_to_price_validation():
    assert trade_agreement.price_validation_required is True


@step("the member contacts the Exchange", StepType.THEN)
def step_member_contacts_exchange():
    contact = LME.PostTrade.contact_exchange(
        member=session.member_id,
        order_id=response.order_id,
        reason=validation_result.rejection_reason,
    )
    assert contact is not None


@step("the member explains the rationale as to the price of the rejected order or trade", StepType.THEN)
def step_member_explains_price_rationale():
    assert contact is not None
    assert contact.get("rationale") is not None


@step("the contact action is recorded", StepType.THEN)
def step_contact_action_recorded():
    record = LME.API.get_contact_record(order_id=response.order_id)
    assert record is not None
    assert record.get("action") == "contact_exchange"


@step("Exchange records the contact", StepType.THEN)
def step_exchange_records_contact():
    contact = LME.PostTrade.get_contact(reason=validation_result.rejection_reason)
    assert contact is not None
    assert contact.get("member_id") == session.member_id


@step("the member is not required to contact the Exchange to explain price rationale", StepType.THEN)
def step_member_not_required_to_contact():
    contact_records = LME.API.get_contact_records(
        member=session.member_id,
        order_id=response.order_id,
    )
    assert len(contact_records) == 0


@step("the processing result indicates compliance", StepType.THEN)
def step_processing_result_indicates_compliance():
    assert contact_response is not None
    assert contact_response.status == "RECORDED"
    compliance = LME.PostTrade.get_compliance_status(
        validation_result.rejection_reason,
    )
    assert compliance == "COMPLIANT"


@step("the processing result indicates non-compliance or failure", StepType.THEN)
def step_processing_result_indicates_non_compliance():
    assert contact_response is None
    compliance = LME.PostTrade.get_compliance_status("trade_without_contact")
    assert compliance == "NON_COMPLIANT"


@step("the order or trade proceeds without the contact obligation", StepType.THEN)
def step_proceeds_without_contact_obligation():
    response.reload()
    assert response.status == "accepted"
    assert response.contact_obligation is False


@step("system permits the trade re-submission", StepType.THEN)
def step_system_permits_resubmission():
    assert resubmission_response.status == "PERMITTED"


@step("validation result indicates acceptance", StepType.THEN)
def step_validation_result_indicates_acceptance():
    assert resubmission_response.validation_result == "ACCEPTED"


@step("the request is accepted", StepType.THEN)
def step_request_accepted():
    assert response.status == "accepted"


@step("the deadline validation result is 'pass'", StepType.THEN)
def step_deadline_validation_pass():
    result = LME.API.get_deadline_validation(response.request_id)
    assert result == "pass"


@step("the recorded timestamp reflects timely submission", StepType.THEN)
def step_timestamp_reflects_timely_submission():
    submitted_at = response.submitted_at
    deadline_ts = deadline.get("timestamp")
    assert submitted_at <= (deadline_ts - (15 * 60))


@step("the submission meets the deadline requirement", StepType.THEN)
def step_submission_meets_deadline_requirement():
    result = LME.API.get_deadline_validation(response.request_id)
    assert result.get("meets_requirement") is True


@step("the request is rejected as a late submission", StepType.THEN)
def step_request_rejected_late_submission():
    assert response.status == "rejected"
    assert response.rejection_reason == "late_submission"


@step("the deadline validation result indicates failure", StepType.THEN)
def step_deadline_validation_failure():
    result = LME.API.get_deadline_validation(response.request_id)
    assert result == "fail"


@step("the late_submission outcome is recorded", StepType.THEN)
def step_late_submission_outcome_recorded():
    outcome = LME.PostTrade.get_submission_outcome("late_submission")
    assert outcome is not None


@step("trade is subject to price validation", StepType.THEN)
def step_trade_subject_to_price_validation():
    assert agreement.price_validation_required is True


# ---------------------------------------------------------------------------
# Utility: load Python step library from a .py file
# ---------------------------------------------------------------------------

PYTHON_STEP_DEF_RE = re.compile(
    "@(given|when|then)\\(['\"](.+?)['\"]\\)"
    "\\s*def\\s+(\\w+)\\s*\\([^)]*\\)\\s*:\\s*\\n((?:[ \\t]+.+\\n)*)",
    re.DOTALL | re.IGNORECASE,
)


def extract_steps_from_python_library(
    library_file: Path,
    library_name: str = "",
) -> dict[str, PythonStepDefinition]:
    """Extract step definitions from a Python step library file.

    Parses @step decorator patterns and returns a dict keyed by step_text.

    Args:
        library_file: Path to a Python file containing @step decorated functions.
        library_name: Optional name for the library (used in reporting).

    Returns:
        dict[str, PythonStepDefinition]: registry keyed by step_text.
    """
    from .step_registry import StepEntry

    result: dict[str, PythonStepDefinition] = {}
    if not library_file.exists():
        return result

    if not library_name:
        library_name = library_file.stem.replace("_steps", "").replace("-", "_")

    text = library_file.read_text(encoding="utf-8")

    for match in PYTHON_STEP_DEF_RE.finditer(text):
        step_type = match.group(1).lower()
        step_text = match.group(2)
        function_name = match.group(3)
        code_body = match.group(4)

        # Rebuild the full decorated function string
        keyword = step_type.capitalize()
        code = (
            f'@{keyword.lower()}("{step_text.replace(chr(34), chr(92) + chr(34))}")\n'
            f"def {function_name}():\n"
            f"{code_body}"
        )

        pattern = extract_pattern(step_text)

        result[step_text] = PythonStepDefinition(
            step_type=step_type,
            step_text=step_text,
            step_pattern=pattern,
            function_name=function_name,
            code=code,
        )

    return result


# ---------------------------------------------------------------------------
# MOCK: LME module for standalone testing
# In real usage, this module is provided by the test harness/environment.
# ---------------------------------------------------------------------------

try:
    import LME  # type: ignore
except ImportError:

    class _MockLME:
        class Client:
            @staticmethod
            def login(**kwargs):
                class _Session:
                    member_id = "TEST_MEMBER_001"
                return _Session()

            @staticmethod
            def registered_intermediary():
                return {"member_id": "TEST_BROKER_001"}

            @staticmethod
            def environment():
                return type("Env", (), {"status": "active"})()

        class API:
            @staticmethod
            def create_document(**kwargs):
                return type("Doc", (), {
                    "terms": kwargs.get("terms", "capitalised"),
                    "terms_defined": False,
                    "terms_conflict": False,
                })()

            @staticmethod
            def validate_terminology(doc):
                return type("VR", (), {
                    "compliant": True,
                    "source": "LME Rulebook",
                    "status": "fulfilled",
                    "errors": [],
                })()

            @staticmethod
            def submit_order(params):
                return type("Ord", (), {
                    "status": "accepted",
                    "order_id": "ORD_001",
                    "contact_obligation": False,
                    "rejection_reason": None,
                    "submitted_at": None,
                })()

            @staticmethod
            def check_price_validation(**kwargs):
                return type("VR2", (), {
                    "status": "PASSED",
                    "rejection_reason": None,
                })()

            @staticmethod
            def submit_trade(params):
                return type("TS", (), {"status": "SUBMITTED", "id": "TRADE_001"})()

            @staticmethod
            def resubmit_trade(id, original_form):
                return type("RR", (), {
                    "status": "PERMITTED",
                    "validation_result": "ACCEPTED",
                })()

            @staticmethod
            def get_contact_record(order_id):
                return {"action": "contact_exchange", "record_id": "REC_001"}

            @staticmethod
            def get_contact_records(**kwargs):
                return []

            @staticmethod
            def submit_request(**kwargs):
                return type("Req", (), {
                    "status": "accepted",
                    "request_id": "REQ_001",
                    "submitted_at": kwargs.get("submitted_at"),
                    "rejection_reason": None,
                })()

            @staticmethod
            def get_deadline_validation(request_id):
                return {"result": "pass", "meets_requirement": True}

        class PostTrade:
            @staticmethod
            def contact_exchange(**kwargs):
                return type("CR", (), {
                    "status": "RECORDED",
                    "contact_id": "CONT_001",
                    "member_id": kwargs.get("member", "TEST_MEMBER"),
                })()

            @staticmethod
            def get_contact(**kwargs):
                return {"member_id": "TEST_MEMBER_001", "contact_id": "CONT_001"}

            @staticmethod
            def define_matching_rules(**kwargs):
                return {"version": kwargs.get("version", "1.0"), "rules": []}

            @staticmethod
            def submit_adoption(rules):
                return type("AS", (), {
                    "adopted": True,
                    "classification": "Administrative_Procedures",
                })()

            @staticmethod
            def create_agreement():
                return type("Agg", (), {
                    "price_validation_required": True,
                    "agreement_id": "AGG_001",
                })()

            @staticmethod
            def get_deadline(**kwargs):
                from datetime import datetime, timedelta
                return {
                    "timestamp": int((datetime.now() + timedelta(hours=1)).timestamp() * 1000),
                    "active": True,
                    "request_type": kwargs.get("request_type", "post_trade_correction"),
                }

            @staticmethod
            def get_info_request(trade_id):
                return {"trade_id": trade_id, "status": "REQUESTED"}

            @staticmethod
            def provide_info(trade_id, info):
                return {"status": "INFO_PROVIDED"}

            @staticmethod
            def get_compliance_status(reason):
                if reason == "trade_without_contact":
                    return "NON_COMPLIANT"
                return "COMPLIANT"

            @staticmethod
            def get_submission_outcome(outcome_type):
                return {"outcome": outcome_type, "recorded": True}

    LME = _MockLME()  # type: ignore

    class ENV:
        @staticmethod
        def get(key, default=None):
            return default

    globals()["ENV"] = ENV

