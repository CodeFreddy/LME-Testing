"""Deadline oracle: validates time-window and deadline constraints."""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any

from .base import OracleResult
from . import register_oracle


class DeadlineCheckOracle:
    """Oracle for deadline_check assertion type.

    Evaluates whether an action occurred within an acceptable time window:
    - before a deadline (on time submission)
    - after a start window opens
    - within a tolerance of a target time

    Assertion parameters:
        submission_time (str): Dot-notation path to the submission timestamp.
        deadline (str): ISO-8601 deadline string, or dot-notation reference.
        tolerance_minutes (int): Optional grace period in minutes.
        window_start (str): Optional window start ISO-8601 string.
        operator (str): "before" (default) | "after" | "between" | "exactly".
        expected_outcome (str): "pass" | "fail" (whether a timely submission is expected to pass).
    """

    _ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

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

        submission_time_path = params.get("submission_time")
        deadline_path = params.get("deadline")
        window_start_path = params.get("window_start")
        tolerance_minutes = params.get("tolerance_minutes", 0)
        operator = params.get("operator", "before")
        expected_outcome = params.get("expected_outcome", "pass")

        # Resolve values
        submission_time = _resolve_ts(submission_time_path, scenario, ctx)
        deadline = _resolve_ts(deadline_path, scenario, ctx)
        window_start = _resolve_ts(window_start_path, scenario, ctx)

        # If we can't resolve timestamps, return unable_to_determine
        missing = []
        if submission_time_path and submission_time is None:
            missing.append(f"submission_time at '{submission_time_path}'")
        if deadline_path and deadline is None:
            missing.append(f"deadline at '{deadline_path}'")
        if missing:
            return OracleResult(
                assertion_id=assertion_id,
                status="unable_to_determine",
                outcome="",
                message=f"Cannot resolve timestamp(s): {', '.join(missing)}",
            )

        if submission_time is None and deadline is None:
            # No timestamps available at all
            return OracleResult(
                assertion_id=assertion_id,
                status="unable_to_determine",
                outcome="",
                message="No timestamp data available in scenario or context",
            )

        # Parse submission_time if it's a string
        if isinstance(submission_time, str):
            submission_time = _parse_iso(submission_time)
        if isinstance(deadline, str):
            deadline = _parse_iso(deadline)
        if isinstance(window_start, str):
            window_start = _parse_iso(window_start)

        # Determine pass/fail
        result = self._check_deadline(
            submission_time, deadline, window_start, tolerance_minutes, operator
        )

        return OracleResult(
            assertion_id=assertion_id,
            status="pass" if result else "fail",
            outcome="deadline_met" if result else "deadline_missed",
            message=self._build_message(result, submission_time, deadline, operator),
            evidence={
                "submission_time": _iso_str(submission_time),
                "deadline": _iso_str(deadline),
                "window_start": _iso_str(window_start),
                "tolerance_minutes": tolerance_minutes,
                "operator": operator,
            },
        )

    def _check_deadline(
        self,
        submission_time: datetime | None,
        deadline: datetime | None,
        window_start: datetime | None,
        tolerance_minutes: int,
        operator: str,
    ) -> bool:
        if submission_time is None:
            return False

        if deadline is not None:
            # Apply tolerance
            effective_deadline = deadline + timedelta(minutes=tolerance_minutes)

            if operator == "before":
                return submission_time <= effective_deadline
            if operator == "after":
                return submission_time >= deadline
            if operator == "between" and window_start is not None:
                return window_start <= submission_time <= effective_deadline
            if operator == "exactly":
                return submission_time == deadline

        if window_start is not None and deadline is not None:
            return window_start <= submission_time <= deadline

        return True

    def _build_message(
        self,
        result: bool,
        submission_time: datetime | None,
        deadline: datetime | None,
        operator: str,
    ) -> str:
        status_str = "deadline met" if result else "deadline missed"
        parts = [status_str]
        if submission_time:
            parts.append(f"submitted at {_iso_str(submission_time)}")
        if deadline:
            parts.append(f"deadline was {_iso_str(deadline)}")
        if operator:
            parts.append(f"operator={operator}")
        return ", ".join(parts)


def _resolve_ts(path: str | None, scenario: dict, context: dict) -> Any:
    if not path:
        return None
    # Detect direct ISO datetime strings (not dot-notation paths)
    if re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", str(path)):
        return path
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


def _parse_iso(value: str) -> datetime | None:
    if value is None:
        return None
    try:
        # Normalize Z suffix to +00:00 for fromisoformat compatibility
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except (ValueError, TypeError):
        return None


def _iso_str(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.isoformat()


register_oracle("deadline_check", DeadlineCheckOracle)
