#!/usr/bin/env python3
"""
Schema validation script for CI.

Validates governed artifact files against JSON schemas.

Usage:
    python scripts/validate_schemas.py

Exit codes:
    0 = all validations passed
    1 = one or more validations failed
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure lme_testing is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from schemas import (
    validate_atomic_rule,
    validate_semantic_rule,
    validate_maker_output,
    validate_checker_output,
    validate_executable_scenario,
    validate_artifact_list,
    validate_jsonl,
)


def validate_file(
    path: Path,
    validator_fn,
    artifact_type: str,
) -> bool:
    """Validate a single file. Returns True if valid, False if errors."""
    result = validate_artifact_list(path, validator_fn) if path.suffix == ".json" else validate_jsonl(path, validator_fn)

    total = result["total"]
    valid = result["valid_count"]
    invalid = result["invalid_count"]
    errors = result.get("errors_by_index") or result.get("errors_by_line") or []

    status = "PASS" if invalid == 0 else "FAIL"
    print(f"[{status}] {artifact_type} {path}: {total} total, {valid} valid, {invalid} invalid")

    for err in errors[:5]:
        entry = err.get("index", err.get("line", "?"))
        for msg in err["errors"][:2]:
            print(f"  [{entry}] {msg}")
    if len(errors) > 5:
        print(f"  ... and {len(errors) - 5} more errors")

    return invalid == 0


def main() -> int:
    repo_root = Path(__file__).parent.parent
    passed = True

    # Validate poc_two_rules artifacts
    passed &= validate_file(
        repo_root / "artifacts" / "poc_two_rules" / "atomic_rules.json",
        validate_atomic_rule,
        "atomic_rule (poc)",
    )
    passed &= validate_file(
        repo_root / "artifacts" / "poc_two_rules" / "semantic_rules.json",
        validate_semantic_rule,
        "semantic_rule (poc)",
    )

    # Validate lme_rules_v2_2 artifacts
    passed &= validate_file(
        repo_root / "artifacts" / "lme_rules_v2_2" / "atomic_rules.json",
        validate_atomic_rule,
        "atomic_rule (lme)",
    )
    passed &= validate_file(
        repo_root / "artifacts" / "lme_rules_v2_2" / "semantic_rules.json",
        validate_semantic_rule,
        "semantic_rule (lme)",
    )

    print()
    if passed:
        print("All schema validations passed.")
    else:
        print("Some schema validations FAILED.")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
