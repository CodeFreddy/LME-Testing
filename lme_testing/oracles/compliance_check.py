"""Compliance check oracle: validates obligation, prohibition, and permission fulfillment."""
from __future__ import annotations

from typing import Any

from .base import OracleResult
from . import register_oracle


# Rule types that use compliance checks
OBLIGATION_RULE_TYPES = {"obligation"}
PROHIBITION_RULE_TYPES = {"prohibition"}
PERMISSION_RULE_TYPES = {"permission"}


class ComplianceCheckOracle:
    """Oracle for compliance_check assertion type.

    Validates that an obligation, prohibition, or permission rule is
    correctly fulfilled or violated based on the observed outcome.

    This oracle uses the source semantic rule's type_payload to determine
    the expected behavior and matches it against the scenario's outcome.

    Assertion parameters:
        rule_type (str, optional): Override rule type ("obligation" | "prohibition" | "permission").
                                   If not set, derived from the source rule.
        expected_compliance_status (str): "fulfilled" | "violated" | "compliant" | "non_compliant".
        outcome_field (str, optional): Dot-notation path to the compliance status field.
        bound_step (str, optional): BDD step text this assertion is bound to (for traceability).
    """

    def evaluate(
        self,
        assertion: dict,
        scenario: dict,
        rule: dict | None = None,
        context: dict | None = None,
    ) -> OracleResult:
        assertion_id = assertion.get("assertion_id", "unknown")
        params = assertion.get("parameters", {})
        ctx = context or {}

        expected_status = params.get("expected_compliance_status", "fulfilled")
        outcome_field = params.get("outcome_field", "")
        bound_step = params.get("bound_step", "")

        # Determine rule type from assertion param or source rule
        rule_type_override = params.get("rule_type")
        if rule_type_override:
            rule_type = rule_type_override
        elif rule:
            rule_type = rule.get("classification", {}).get("rule_type", "unknown")
        else:
            rule_type = "unknown"

        # Resolve observed outcome
        observed_status: str | None = None
        if outcome_field:
            observed_status = _resolve(outcome_field, scenario, ctx)

        # If no explicit outcome field, try to infer from assertions or step_bindings
        if observed_status is None:
            # Look at step_bindings for "then" steps that might indicate status
            then_steps = [
                b for b in scenario.get("step_bindings", [])
                if b.get("step_type") == "then"
            ]
            # Check if "then" steps that match the bound_step indicate fulfillment
            for step in then_steps:
                step_text = step.get("step_text", "")
                if bound_step and bound_step in step_text:
                    # Try to infer from step text keywords
                    if any(k in step_text.lower() for k in ["fulfilled", "compliant", "accepted", "valid"]):
                        observed_status = "fulfilled"
                    elif any(k in step_text.lower() for k in ["not fulfilled", "violated", "rejected", "invalid"]):
                        observed_status = "violated"

        if observed_status is None:
            return OracleResult(
                assertion_id=assertion_id,
                status="unable_to_determine",
                outcome="",
                message="Cannot determine compliance status: no outcome field or inference available",
            )

        # Normalize comparison
        observed_norm = _normalize_status(observed_status)
        expected_norm = _normalize_status(expected_status)

        # For obligations: fulfilled = compliant, not fulfilled = non-compliant
        # For prohibitions: violated = non-compliant, not violated = compliant
        # For permissions: compliant = action allowed, non-compliant = action denied
        if rule_type in OBLIGATION_RULE_TYPES:
            pass_if = observed_norm == expected_norm
        elif rule_type in PROHIBITION_RULE_TYPES:
            # For prohibition, expected "fulfilled" means prohibition was NOT violated
            # expected "violated" means prohibition was violated
            pass_if = observed_norm == expected_norm
        elif rule_type in PERMISSION_RULE_TYPES:
            pass_if = observed_norm == expected_norm
        else:
            # Generic comparison
            pass_if = observed_norm == expected_norm

        # Special case: when case_type is "negative" for obligation, we expect non-fulfillment
        case_type = scenario.get("case_type", "")
        if case_type == "negative" and rule_type in OBLIGATION_RULE_TYPES:
            # Negative case: obligation should NOT be fulfilled
            pass_if = observed_norm in ("violated", "non_compliant", "not_fulfilled")

        status = "pass" if pass_if else "fail"
        outcome = observed_norm
        message = (
            f"Compliance check: rule_type={rule_type}, case_type={case_type}, "
            f"expected={expected_norm}, observed={observed_norm} -> {status}"
        )

        return OracleResult(
            assertion_id=assertion_id,
            status=status,
            outcome=outcome,
            message=message,
            evidence={
                "rule_type": rule_type,
                "case_type": case_type,
                "expected_compliance_status": expected_norm,
                "observed_compliance_status": observed_norm,
                "bound_step": bound_step,
            },
        )


def _resolve(path: str, scenario: dict, context: dict) -> Any:
    if not path:
        return None
    input_data = scenario.get("input_data", {})
    if path in input_data:
        return input_data[path]
    parts = path.split(".")
    if parts[0] == "input_data":
        val = input_data
        for part in parts[1:]:
            if isinstance(val, dict):
                val = val.get(part)
            else:
                return None
        return val
    if path in context:
        return context[path]
    val = context
    for part in parts:
        if isinstance(val, dict):
            val = val.get(part)
        else:
            return None
    return val


_STATUS_NORM: dict[str, str] = {
    "fulfilled": "fulfilled",
    "fulfillled": "fulfilled",  # typo in some data
    "compliant": "compliant",
    "accepted": "fulfilled",
    "violated": "violated",
    "not_fulfilled": "violated",
    "non_compliant": "violated",
    "rejected": "violated",
    "noncompliant": "violated",
    "unfulfilled": "violated",
}


def _normalize_status(status: str | Any) -> str:
    if not isinstance(status, str):
        return str(status).lower()
    lower = status.lower().strip()
    return _STATUS_NORM.get(lower, lower)


register_oracle("compliance_check", ComplianceCheckOracle)
