"""Deterministic oracle framework for evaluating execution-ready scenarios.

Each oracle module evaluates a specific assertion type without LLM calls.
Oracles receive a scenario's executable data + upstream rule context and
return a deterministic pass/fail/unable_to_determine result.

Assertion types handled:
- field_validation  : field content or structure checks
- state_validation  : system state transitions
- calculation_validation : arithmetic or formula checks
- deadline_check    : time-window and deadline constraints
- event_sequence     : ordering requirements between events
- pass_fail_accounting : explicit pass/fail bookkeeping
- null_check        : null/non-null field expectations
- compliance_check  : obligation/prohibition/permission fulfillment

Phase 3 Gate 3: Deterministic Oracle Framework
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Re-export result type for convenience
from .base import OracleResult, UnableToDetermine, OracleError

__all__ = [
    "OracleResult",
    "UnableToDetermine",
    "OracleError",
    "get_oracle",
    "evaluate_assertion",
    "list_oracles",
]


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_ORACLES: dict[str, type] = {}


def register_oracle(assertion_type: str, cls: type) -> None:
    """Register an oracle class for an assertion type."""
    _ORACLES[assertion_type] = cls


def get_oracle(assertion_type: str) -> type | None:
    """Return the oracle class for an assertion type, or None."""
    return _ORACLES.get(assertion_type)


def list_oracles() -> list[str]:
    """Return sorted list of registered assertion types."""
    return sorted(_ORACLES.keys())


def evaluate_assertion(
    assertion: dict,
    scenario: dict,
    rule: dict | None = None,
    context: dict | None = None,
) -> OracleResult:
    """Evaluate a single assertion using the appropriate oracle.

    Args:
        assertion: Assertion object from executable_scenario.assertions[]
        scenario: ExecutableScenario being evaluated
        rule: Source semantic rule (optional, for contextual checks)
        context: Additional execution context (optional)

    Returns:
        OracleResult with deterministic outcome
    """
    assertion_type = assertion.get("type", "")
    oracle_cls = get_oracle(assertion_type)

    if oracle_cls is None:
        return OracleResult(
            assertion_id=assertion.get("assertion_id", "unknown"),
            status="error",
            outcome="",
            message=f"No oracle registered for assertion type: {assertion_type}",
        )

    try:
        oracle = oracle_cls()
        return oracle.evaluate(assertion, scenario, rule, context or {})
    except Exception as e:
        return OracleResult(
            assertion_id=assertion.get("assertion_id", "unknown"),
            status="error",
            outcome="",
            message=f"Oracle evaluation error: {e}",
        )


# ---------------------------------------------------------------------------
# Auto-register all concrete oracles from submodules
# ---------------------------------------------------------------------------
# Import all submodules to trigger their @register_oracle decorators.
# Each submodule registers itself when imported.
# ---------------------------------------------------------------------------
from . import field_validation  # noqa: F401, E402
from . import state_validation  # noqa: F401, E402
from . import calculation_validation  # noqa: F401, E402
from . import deadline_check  # noqa: F401, E402
from . import event_sequence  # noqa: F401, E402
from . import pass_fail_accounting  # noqa: F401, E402
from . import null_check  # noqa: F401, E402
from . import compliance_check  # noqa: F401, E402
