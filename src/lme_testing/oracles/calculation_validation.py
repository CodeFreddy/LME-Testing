"""Calculation validation oracle: validates arithmetic and formula results."""
from __future__ import annotations

import re
from typing import Any

from .base import OracleResult
from . import register_oracle


class CalculationValidationOracle:
    """Oracle for calculation_validation assertion type.

    Validates arithmetic expressions, formula results, and numeric constraints:
    - result field matches expected value/expression
    - result falls within tolerance of expected value
    - result satisfies min/max constraints
    - sum/difference/product/quotient of fields matches expectation

    Assertion parameters:
        result_field (str): Dot-notation path to the computed result field.
        expected (number, optional): Exact expected numeric value.
        expected_formula (str, optional): Simple formula like "{field_a} + {field_b}".
        tolerance (number, optional): Acceptable absolute difference from expected.
        min_value (number, optional): Minimum acceptable value.
        max_value (number, optional): Maximum acceptable value.
        operator (str): "eq" (default) | "lt" | "le" | "gt" | "ge" | "ne".
    """

    _FORMULA_RE = re.compile(r"\{([^}]+)\}")

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
        expected = params.get("expected")
        expected_formula = params.get("expected_formula")
        tolerance = params.get("tolerance", 0)
        min_value = params.get("min_value")
        max_value = params.get("max_value")
        operator = params.get("operator", "eq")

        if not result_field:
            return OracleResult(
                assertion_id=assertion_id,
                status="error",
                outcome="",
                message="calculation_validation requires 'parameters.result_field'",
            )

        result = _resolve(result_field, scenario, ctx)

        if result is None:
            return OracleResult(
                assertion_id=assertion_id,
                status="unable_to_determine",
                outcome="",
                message=f"Cannot resolve result_field at '{result_field}'",
            )

        # Try to coerce to numeric
        try:
            result_val = float(result)
        except (TypeError, ValueError):
            return OracleResult(
                assertion_id=assertion_id,
                status="fail",
                outcome="not_numeric",
                message=f"result field value '{result}' is not numeric",
                evidence={"result_field": result_field, "value": result},
            )

        errors: list[str] = []

        # Formula evaluation
        if expected_formula:
            formula_result = self._eval_formula(expected_formula, scenario, ctx)
            if formula_result is None:
                errors.append(f"Cannot evaluate formula: {expected_formula}")
            else:
                diff = abs(result_val - formula_result)
                if diff > tolerance:
                    errors.append(
                        f"result {result_val} differs from formula '{expected_formula}' "
                        f"(={formula_result}) by {diff}, tolerance={tolerance}"
                    )

        # Explicit expected value
        if expected is not None:
            try:
                expected_val = float(expected)
                diff = abs(result_val - expected_val)
                if diff > tolerance:
                    errors.append(
                        f"result {result_val} differs from expected {expected_val} "
                        f"by {diff}, tolerance={tolerance}"
                    )
            except (TypeError, ValueError):
                errors.append(f"expected value '{expected}' is not numeric")

        # Range checks
        if min_value is not None:
            try:
                if result_val < float(min_value):
                    errors.append(f"result {result_val} is below minimum {min_value}")
            except (TypeError, ValueError):
                pass

        if max_value is not None:
            try:
                if result_val > float(max_value):
                    errors.append(f"result {result_val} exceeds maximum {max_value}")
            except (TypeError, ValueError):
                pass

        # Operator checks
        if operator and not errors:
            if operator == "lt" and not (result_val < float(expected)):
                errors.append(f"result {result_val} is not less than {expected}")
            elif operator == "le" and not (result_val <= float(expected)):
                errors.append(f"result {result_val} is not less than or equal to {expected}")
            elif operator == "gt" and not (result_val > float(expected)):
                errors.append(f"result {result_val} is not greater than {expected}")
            elif operator == "ge" and not (result_val >= float(expected)):
                errors.append(f"result {result_val} is not greater than or equal to {expected}")
            elif operator == "ne" and result_val == float(expected):
                errors.append(f"result {result_val} must not equal {expected}")

        status = "pass" if not errors else "fail"
        outcome = "calculation_valid" if not errors else "calculation_invalid"
        message = "; ".join(errors) if errors else f"result {result_val} is valid"

        return OracleResult(
            assertion_id=assertion_id,
            status=status,
            outcome=outcome,
            message=message,
            evidence={"result_field": result_field, "result_value": result_val, "errors": errors},
        )

    def _eval_formula(
        self,
        formula: str,
        scenario: dict,
        context: dict,
    ) -> float | None:
        """Evaluate a simple {field} +/-/*// {field} formula."""
        try:
            # Replace {field} references with numeric values
            def replacer(m: re.Match) -> str:
                field_path = m.group(1)
                val = _resolve(field_path, scenario, context)
                if val is None:
                    raise UnableToDetermine(f"Cannot resolve {field_path}")
                return str(float(val))

            expr = self._FORMULA_RE.sub(replacer, formula)
            # Only allow safe arithmetic characters
            if not re.match(r"^[\d\s\.\+\-\*\/\(\)\-]+$", expr):
                return None
            return float(eval(expr))  # noqa: S307 — controlled by regex above
        except (ValueError, TypeError, ZeroDivisionError, SyntaxError):
            return None


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


register_oracle("calculation_validation", CalculationValidationOracle)
