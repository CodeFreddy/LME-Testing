"""Null/non-null oracle: checks whether a field is or is not null."""
from __future__ import annotations

from .base import OracleResult, UnableToDetermine
from . import register_oracle


class NullCheckOracle:
    """Oracle for null_check assertion type.

    Evaluates whether a named field is null or non-null based on
    scenario input_data or execution context.

    Assertion parameters:
        field (str): Dot-notation path to the field to check (e.g., "processing_result").
        expected (str): "null" | "non_null". Default "non_null".
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
        field_path = params.get("field", "")
        expected = params.get("expected", "non_null")

        if not field_path:
            return OracleResult(
                assertion_id=assertion_id,
                status="error",
                outcome="",
                message="null_check requires 'parameters.field' to be set",
            )

        # Resolve field value from input_data, then context
        value = _resolve_field(field_path, scenario, context or {})

        if expected == "null":
            is_null = value is None or value == ""
            status = "pass" if is_null else "fail"
            outcome = "null"
        else:
            is_null = value is None or value == ""
            status = "pass" if not is_null else "fail"
            outcome = "non_null"

        return OracleResult(
            assertion_id=assertion_id,
            status=status,
            outcome=outcome,
            message=f"field '{field_path}' is {outcome}",
            evidence={"field": field_path, "value": value, "expected": expected},
        )


def _resolve_field(path: str, scenario: dict, context: dict) -> Any:
    """Resolve a dot-notation field path from scenario + context."""
    # Try input_data first
    input_data = scenario.get("input_data", {})
    if path in input_data:
        return input_data[path]

    # Try nested: input_data.parameters.foo
    parts = path.split(".")
    if parts[0] == "input_data":
        val = input_data
        for part in parts[1:]:
            if isinstance(val, dict):
                val = val.get(part)
            else:
                return None
        return val

    # Try context
    if path in context:
        return context[path]

    # Try nested in context
    val = context
    for part in parts:
        if isinstance(val, dict):
            val = val.get(part)
        else:
            return None
    return val


register_oracle("null_check", NullCheckOracle)
