"""Pass/fail accounting oracle: validates explicit pass/fail bookkeeping."""
from __future__ import annotations

from typing import Any

from .base import OracleResult
from . import register_oracle


class PassFailAccountingOracle:
    """Oracle for pass_fail_accounting assertion type.

    Validates explicit pass/fail bookkeeping:
    - A result field equals "pass" or "fail"
    - A counter of passes meets a threshold
    - A total count matches an expected sum

    Assertion parameters:
        result_field (str): Dot-notation path to the result field.
        expected_outcome (str): "pass" | "fail". Default "pass".
        pass_count_field (str, optional): Dot-notation path to a pass count.
        fail_count_field (str, optional): Dot-notation path to a fail count.
        total_count_field (str, optional): Dot-notation path to a total count.
        min_passes (int, optional): Minimum number of passes required.
        max_fails (int, optional): Maximum number of failures allowed.
        expected_total (int, optional): Expected total count (passes + fails must equal this).
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

        result_field = params.get("result_field", "")
        expected_outcome = params.get("expected_outcome", "pass")
        pass_count_field = params.get("pass_count_field")
        fail_count_field = params.get("fail_count_field")
        total_count_field = params.get("total_count_field")
        min_passes = params.get("min_passes")
        max_fails = params.get("max_fails")
        expected_total = params.get("expected_total")

        errors: list[str] = []

        # Primary result check
        if result_field:
            result = _resolve(result_field, scenario, ctx)
            if result is None:
                errors.append(f"Cannot resolve result_field at '{result_field}'")
            elif result != expected_outcome:
                errors.append(f"Result '{result}' does not match expected '{expected_outcome}'")

        # Pass count check
        pass_count: int | None = None
        if pass_count_field:
            val = _resolve(pass_count_field, scenario, ctx)
            if val is None:
                errors.append(f"Cannot resolve pass_count_field at '{pass_count_field}'")
            else:
                try:
                    pass_count = int(val)
                    if min_passes is not None and pass_count < min_passes:
                        errors.append(f"Pass count {pass_count} is below minimum {min_passes}")
                except (TypeError, ValueError):
                    errors.append(f"Pass count value '{val}' is not an integer")

        # Fail count check
        fail_count: int | None = None
        if fail_count_field:
            val = _resolve(fail_count_field, scenario, ctx)
            if val is None:
                errors.append(f"Cannot resolve fail_count_field at '{fail_count_field}'")
            else:
                try:
                    fail_count = int(val)
                    if max_fails is not None and fail_count > max_fails:
                        errors.append(f"Fail count {fail_count} exceeds maximum {max_fails}")
                except (TypeError, ValueError):
                    errors.append(f"Fail count value '{val}' is not an integer")

        # Total count check
        if total_count_field and expected_total is not None:
            val = _resolve(total_count_field, scenario, ctx)
            if val is not None:
                try:
                    total = int(val)
                    if total != expected_total:
                        errors.append(f"Total count {total} does not match expected {expected_total}")
                except (TypeError, ValueError):
                    errors.append(f"Total count value '{val}' is not an integer")

        # Cross-check: passes + fails = total
        if pass_count is not None and fail_count is not None and expected_total is not None:
            if pass_count + fail_count != expected_total:
                errors.append(
                    f"Pass count {pass_count} + fail count {fail_count} "
                    f"!= expected total {expected_total}"
                )

        status = "pass" if not errors else "fail"
        outcome = expected_outcome if not errors else f"{expected_outcome}_violated"
        message = "; ".join(errors) if errors else f"Pass/fail accounting is valid (expected {expected_outcome})"

        return OracleResult(
            assertion_id=assertion_id,
            status=status,
            outcome=outcome,
            message=message,
            evidence={
                "result_field": result_field,
                "expected_outcome": expected_outcome,
                "pass_count": pass_count,
                "fail_count": fail_count,
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


register_oracle("pass_fail_accounting", PassFailAccountingOracle)
