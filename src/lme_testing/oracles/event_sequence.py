"""Event sequence oracle: validates ordering requirements between events."""
from __future__ import annotations

from typing import Any

from .base import OracleResult
from . import register_oracle


class EventSequenceOracle:
    """Oracle for event_sequence assertion type.

    Validates that events occurred in the required order and that
    required events are all present.

    Assertion parameters:
        events (list[dict]): List of events, each with:
            - name (str): Event identifier
            - timestamp_field (str): Dot-notation path to the event's timestamp
            - order_rank (int): Expected sequence position (1-indexed)
        required_events (list[str], optional): Events that must all be present.
        strict_order (bool): If true, all events must appear in rank order.
                              Default false (only adjacent pairs checked).
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

        events = params.get("events", [])
        required_events = set(params.get("required_events", []))
        strict_order = params.get("strict_order", False)

        if not events:
            return OracleResult(
                assertion_id=assertion_id,
                status="error",
                outcome="",
                message="event_sequence requires 'parameters.events' list",
            )

        # Resolve timestamps for each event
        resolved_events: list[dict] = []
        missing: list[str] = []

        for evt in events:
            name = evt.get("name", "unnamed")
            ts_path = evt.get("timestamp_field", "")
            rank = evt.get("order_rank")
            ts = _resolve_ts(ts_path, scenario, ctx) if ts_path else None
            resolved_events.append({"name": name, "timestamp": ts, "order_rank": rank})
            if ts is None and name in required_events:
                missing.append(name)

        # Check for missing required events
        if missing:
            return OracleResult(
                assertion_id=assertion_id,
                status="unable_to_determine",
                outcome="",
                message=f"Missing timestamp(s) for required event(s): {missing}",
                evidence={"missing_events": missing},
            )

        errors: list[str] = []

        # Check that all required events are present
        present_events = {e["name"] for e in resolved_events if e["timestamp"] is not None}
        if required_events:
            absent = required_events - present_events
            if absent:
                errors.append(f"Required events not present: {absent}")

        # Sort by timestamp and check order
        timed_events = [e for e in resolved_events if e["timestamp"] is not None]
        timed_events.sort(key=lambda e: e["timestamp"])

        # Check strict ordering by rank
        if strict_order:
            ranked = sorted(timed_events, key=lambda e: e["order_rank"] or 0)
            ranked_names = [e["name"] for e in ranked]
            timed_names = [e["name"] for e in timed_events]
            if ranked_names != timed_names:
                errors.append(
                    f"Events out of order. Expected: {ranked_names}, Got: {timed_names}"
                )

        # Adjacent pair ordering: for each pair of consecutive ranked events,
        # ensure timestamp(event[i]) <= timestamp(event[i+1])
        ranked_timed = sorted(timed_events, key=lambda e: e["order_rank"] or 0)
        for i in range(len(ranked_timed) - 1):
            curr = ranked_timed[i]
            nxt = ranked_timed[i + 1]
            if curr["timestamp"] and nxt["timestamp"]:
                if curr["timestamp"] > nxt["timestamp"]:
                    errors.append(
                        f"Event ordering violation: {curr['name']} "
                        f"(ts={curr['timestamp']}) occurred after "
                        f"{nxt['name']} (ts={nxt['timestamp']})"
                    )

        status = "pass" if not errors else "fail"
        outcome = "sequence_valid" if not errors else "sequence_invalid"
        message = "; ".join(errors) if errors else "Event sequence is valid"

        return OracleResult(
            assertion_id=assertion_id,
            status=status,
            outcome=outcome,
            message=message,
            evidence={
                "events": [
                    {"name": e["name"], "timestamp": e["timestamp"], "rank": e["order_rank"]}
                    for e in resolved_events
                ],
                "errors": errors,
            },
        )


def _resolve_ts(path: str | None, scenario: dict, context: dict) -> Any:
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


register_oracle("event_sequence", EventSequenceOracle)
