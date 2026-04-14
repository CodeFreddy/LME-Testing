"""State validation oracle: validates system state transitions."""
from __future__ import annotations

from typing import Any

from .base import OracleResult
from . import register_oracle


class StateValidationOracle:
    """Oracle for state_validation assertion type.

    Validates that a system transitioned to an expected state or remains
    in an expected state after an action.

    Assertion parameters:
        current_state (str): Dot-notation path to the current/observed state field.
        expected_state (str): The expected state value.
        previous_state (str, optional): Dot-notation path to the previous state.
        allowed_states (list[str], optional): List of valid states (fail if outside).
        forbidden_states (list[str], optional): List of invalid states (fail if inside).
        state_type (str, optional): "simple" | "flags" | "ordinal". Default "simple".
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

        current_state_path = params.get("current_state", "")
        expected_state = params.get("expected_state")
        previous_state_path = params.get("previous_state")
        allowed_states = params.get("allowed_states")
        forbidden_states = params.get("forbidden_states")
        state_type = params.get("state_type", "simple")

        if not current_state_path:
            return OracleResult(
                assertion_id=assertion_id,
                status="error",
                outcome="",
                message="state_validation requires 'parameters.current_state' to be set",
            )

        current_state = _resolve(current_state_path, scenario, ctx)
        previous_state = _resolve(previous_state_path, scenario, ctx) if previous_state_path else None

        if current_state is None:
            return OracleResult(
                assertion_id=assertion_id,
                status="unable_to_determine",
                outcome="",
                message=f"Cannot resolve current_state at '{current_state_path}'",
            )

        errors: list[str] = []

        # Forbidden states check
        if forbidden_states and current_state in forbidden_states:
            errors.append(f"current state '{current_state}' is in forbidden list {forbidden_states}")

        # Allowed states check
        if allowed_states and current_state not in allowed_states:
            errors.append(f"current state '{current_state}' is not in allowed list {allowed_states}")

        # Expected state check
        if expected_state is not None and current_state != expected_state:
            errors.append(f"current state '{current_state}' does not match expected '{expected_state}'")

        status = "pass" if not errors else "fail"
        outcome = "state_valid" if not errors else "state_invalid"
        message = "; ".join(errors) if errors else f"state '{current_state}' is valid"

        return OracleResult(
            assertion_id=assertion_id,
            status=status,
            outcome=outcome,
            message=message,
            evidence={
                "current_state": current_state,
                "expected_state": expected_state,
                "previous_state": previous_state,
                "state_type": state_type,
                "errors": errors,
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


register_oracle("state_validation", StateValidationOracle)
