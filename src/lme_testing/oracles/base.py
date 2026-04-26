"""Base types for the deterministic oracle framework."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class UnableToDetermine(Exception):
    """Raised when an oracle cannot reach a deterministic conclusion.

    This is not an error — it signals that the available data is insufficient
    for a deterministic check and the assertion should be escalated to human review.
    """


class OracleError(Exception):
    """Raised when an oracle encounters an unexpected error during evaluation."""


@dataclass
class OracleResult:
    """Result of a deterministic oracle evaluation.

    Attributes:
        assertion_id: Identifier of the assertion being evaluated.
        status: One of 'pass', 'fail', 'unable_to_determine', 'error'.
        outcome: Human-readable outcome (e.g., 'pass', 'non_null', 'fulfilled').
        message: Supplementary explanation or error detail.
        evidence: Optional dict with computed values used to reach the result.
    """

    assertion_id: str
    status: str = "unable_to_determine"
    outcome: str = ""
    message: str = ""
    evidence: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        valid = {"pass", "fail", "unable_to_determine", "error"}
        if self.status not in valid:
            raise ValueError(f"status must be one of {valid}, got: {self.status}")

    @property
    def passed(self) -> bool:
        return self.status == "pass"

    @property
    def failed(self) -> bool:
        return self.status == "fail"

    @property
    def undetermined(self) -> bool:
        return self.status == "unable_to_determine"

    @property
    def errored(self) -> bool:
        return self.status == "error"
