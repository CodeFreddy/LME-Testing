"""Field validation oracle: checks field content, type, format, and constraints."""
from __future__ import annotations

import re
from typing import Any

from .base import OracleResult, UnableToDetermine
from . import register_oracle


class FieldValidationOracle:
    """Oracle for field_validation assertion type.

    Validates that a field's value satisfies constraints such as:
    - type (string, integer, boolean, etc.)
    - format (email, uuid, enum value)
    - range (min/max for numeric)
    - length (min_length/max_length)
    - pattern (regex)

    Assertion parameters:
        field (str): Dot-notation path to the field.
        expected_type (str, optional): "string", "integer", "boolean", "number".
        expected_format (str, optional): "email", "uuid", "uri", "date-time", etc.
        enum (list, optional): Allowed values.
        min_value (number, optional): Minimum for numeric fields.
        max_value (number, optional): Maximum for numeric fields.
        min_length (int, optional): Minimum string length.
        max_length (int, optional): Maximum string length.
        pattern (str, optional): Regex pattern the field must match.
        equals (any, optional): Exact value the field must equal.
        not_equals (any, optional): Value the field must not equal.
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

        if not field_path:
            return OracleResult(
                assertion_id=assertion_id,
                status="error",
                outcome="",
                message="field_validation requires 'parameters.field' to be set",
            )

        value = _resolve_field(field_path, scenario, context or {})
        errors: list[str] = []

        # Type check
        expected_type = params.get("expected_type")
        if expected_type and value is not None:
            type_ok = _check_type(value, expected_type)
            if not type_ok:
                errors.append(f"type mismatch: expected {expected_type}, got {type(value).__name__}")

        # Enum check
        enum_values = params.get("enum")
        if enum_values is not None and value not in enum_values:
            errors.append(f"value '{value}' not in allowed enum {enum_values}")

        # Equals check
        expected_value = params.get("equals")
        if "equals" in params and value != expected_value:
            errors.append(f"value '{value}' does not equal expected '{expected_value}'")

        # Not-equals check
        forbidden_value = params.get("not_equals")
        if "not_equals" in params and value == forbidden_value:
            errors.append(f"value '{value}' must not equal forbidden '{forbidden_value}'")

        # Range checks (numeric)
        if isinstance(value, (int, float)) and value is not None:
            min_val = params.get("min_value")
            if min_val is not None and value < min_val:
                errors.append(f"value {value} is below minimum {min_val}")
            max_val = params.get("max_value")
            if max_val is not None and value > max_val:
                errors.append(f"value {value} exceeds maximum {max_val}")

        # Length checks (string)
        if isinstance(value, str):
            min_len = params.get("min_length")
            if min_len is not None and len(value) < min_len:
                errors.append(f"length {len(value)} is below minimum {min_len}")
            max_len = params.get("max_length")
            if max_len is not None and len(value) > max_len:
                errors.append(f"length {len(value)} exceeds maximum {max_len}")

            # Pattern check
            pattern = params.get("pattern")
            if pattern and value is not None:
                try:
                    if not re.search(pattern, value):
                        errors.append(f"value does not match pattern {pattern}")
                except re.error as e:
                    errors.append(f"invalid regex pattern: {e}")

        # Format check
        expected_format = params.get("expected_format")
        if expected_format and value is not None:
            fmt_ok = _check_format(value, expected_format)
            if not fmt_ok:
                errors.append(f"value does not match format '{expected_format}'")

        status = "pass" if not errors else "fail"
        outcome = "valid" if not errors else "invalid"
        message = "; ".join(errors) if errors else f"field '{field_path}' is valid"

        return OracleResult(
            assertion_id=assertion_id,
            status=status,
            outcome=outcome,
            message=message,
            evidence={"field": field_path, "value": value, "errors": errors},
        )


def _check_type(value: Any, expected: str) -> bool:
    """Check if value matches expected type name."""
    type_map = {
        "string": str,
        "integer": int,
        "int": int,
        "number": (int, float),
        "float": float,
        "boolean": bool,
        "bool": bool,
        "object": dict,
        "array": list,
    }
    expected_cls = type_map.get(expected)
    if expected_cls is None:
        return True  # Unknown type, skip check
    return isinstance(value, expected_cls)


_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_URI_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*://")


def _check_format(value: str, fmt: str) -> bool:
    if fmt == "uuid":
        return bool(_UUID_RE.match(value))
    if fmt == "email":
        return bool(_EMAIL_RE.match(value))
    if fmt == "uri":
        return bool(_URI_RE.match(value))
    if fmt == "date-time":
        # Basic ISO-8601 check
        return bool(re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", value))
    return True  # Unknown format, skip


def _resolve_field(path: str, scenario: dict, context: dict) -> Any:
    """Resolve a dot-notation field path from scenario + context."""
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


register_oracle("field_validation", FieldValidationOracle)
