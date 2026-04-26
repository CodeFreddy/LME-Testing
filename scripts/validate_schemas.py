#!/usr/bin/env python3
"""
Schema validation script for CI.

Validates governed artifact files against JSON schemas.

Usage:
    python scripts/validate_schemas.py [--output-json <path>]

Exit codes:
    0 = all validations passed
    1 = one or more validations failed
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Ensure local src-layout packages are importable when run as a script.
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from schemas import (
    validate_atomic_rule,
    validate_semantic_rule,
    validate_artifact_list,
    validate_jsonl,
)


def _validate_and_track(
    path: Path,
    validator_fn,
    artifact_type: str,
    results: list,
) -> bool:
    """Validate a file and append structured result to results list. Returns True if valid."""
    result = validate_artifact_list(path, validator_fn) if path.suffix == ".json" else validate_jsonl(path, validator_fn)

    total = result["total"]
    valid = result["valid_count"]
    invalid = result["invalid_count"]
    errors = result.get("errors_by_index") or result.get("errors_by_line") or []

    # Normalize errors for JSON output
    normalized_errors: list[dict] = []
    for err in errors:
        entry = err.get("index", err.get("line", "?"))
        for msg in err["errors"][:3]:
            normalized_errors.append({"entry": entry, "message": msg})

    results.append({
        "artifact_type": artifact_type,
        "path": str(path),
        "total": total,
        "valid_count": valid,
        "invalid_count": invalid,
        "errors": normalized_errors,
    })

    status = "PASS" if invalid == 0 else "FAIL"
    print(f"[{status}] {artifact_type} {path}: {total} total, {valid} valid, {invalid} invalid")
    for err in normalized_errors[:5]:
        print(f"  [{err['entry']}] {err['message']}")
    if len(normalized_errors) > 5:
        print(f"  ... and {len(normalized_errors) - 5} more errors")

    return invalid == 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate governed artifact schemas.")
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Path to write validation summary JSON (e.g. runs/schema_validation_latest.json)",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    passed = True

    # Track per-artifact validation results for JSON output
    validation_results: list[dict] = []
    total_fixtures = 0
    passed_fixtures = 0
    failed_fixtures = 0
    all_failures: list[dict] = []

    # Validate poc_two_rules artifacts
    passed &= _validate_and_track(
        repo_root / "artifacts" / "poc_two_rules" / "atomic_rules.json",
        validate_atomic_rule,
        "atomic_rule (poc)",
        validation_results,
    )
    passed &= _validate_and_track(
        repo_root / "artifacts" / "poc_two_rules" / "semantic_rules.json",
        validate_semantic_rule,
        "semantic_rule (poc)",
        validation_results,
    )

    # Validate lme_rules_v2_2 artifacts
    passed &= _validate_and_track(
        repo_root / "artifacts" / "lme_rules_v2_2" / "atomic_rules.json",
        validate_atomic_rule,
        "atomic_rule (lme)",
        validation_results,
    )
    passed &= _validate_and_track(
        repo_root / "artifacts" / "lme_rules_v2_2" / "semantic_rules.json",
        validate_semantic_rule,
        "semantic_rule (lme)",
        validation_results,
    )

    # Compute totals
    for vr in validation_results:
        total_fixtures += vr["total"]
        passed_fixtures += vr["valid_count"]
        failed_fixtures += vr["invalid_count"]
        all_failures.extend(vr.get("errors", []))

    print()
    if passed:
        print("All schema validations passed.")
    else:
        print("Some schema validations FAILED.")

    # Write JSON output if requested
    if args.output_json is not None:
        output = {
            "validated_at": datetime.now().isoformat(timespec="seconds") + "Z",
            "total_schemas": len(validation_results),
            "total_fixtures": total_fixtures,
            "passed": passed_fixtures,
            "failed": failed_fixtures,
            "failures": all_failures[:50],  # cap at 50 for readability
            "validation_results": validation_results,
        }
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        tmp = args.output_json.with_suffix(".tmp")
        tmp.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(args.output_json)
        print(f"Validation summary written to {args.output_json}")

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

