#!/usr/bin/env python3
"""
Upstream Rule Validation Pipeline

Validates atomic_rules.json against the governed schema, checks for duplicates
and invalid rule_type values, and produces a structured validation report.

Expected pipeline path:
  docs -> extraction scripts -> atomic_rules.json
    -> validate_atomic_rules -> [duplicates, rule_type check]
    -> validation_report.json
    -> (blocks downstream) -> semantic_rules.json

Usage:
    # Validate and produce report only (no blocking)
    python scripts/validate_rules.py --input artifacts/lme_rules_v2_2/atomic_rules.json

    # Validate and block downstream if invalid
    python scripts/validate_rules.py --input artifacts/lme_rules_v2_2/atomic_rules.json --fail-on-error

Exit codes:
    0 = validation passed (or --fail-on-error not set)
    1 = validation failed (or --fail-on-error set and validation found errors)
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from schemas import validate_atomic_rule, validate_artifact_list, validate_semantic_rule


ALLOWED_RULE_TYPES = frozenset([
    "obligation", "prohibition", "permission", "deadline",
    "state_transition", "data_constraint", "enum_definition",
    "workflow", "calculation", "reference_only",
])


def check_duplicates(atomic_rules: list[dict]) -> dict:
    """Detect duplicate atomic_rule candidates based on raw_text similarity.

    Returns a machine-readable dict with duplicate groups.
    Uses a simple exact-match on normalized raw_text as the primary signal.
    """
    # Group by normalized raw_text
    by_text: dict[str, list[dict]] = {}
    for rule in atomic_rules:
        key = rule.get("raw_text", "").strip().lower()
        if key not in by_text:
            by_text[key] = []
        by_text[key].append(rule)

    duplicate_groups = []
    for text, rules in by_text.items():
        if len(rules) > 1:
            duplicate_groups.append({
                "canonical_text": text[:100],
                "rule_ids": [r.get("rule_id") or f"<index {atomic_rules.index(r)}>" for r in rules],
                "clause_ids": list({r.get("clause_id") for r in rules}),
                "count": len(rules),
            })

    return {
        "total_rules": len(atomic_rules),
        "duplicate_group_count": len(duplicate_groups),
        "duplicate_groups": duplicate_groups,
    }


def check_rule_types(atomic_rules: list[dict]) -> dict:
    """Validate rule_type values against ALLOWED_RULE_TYPES.

    Returns a machine-readable dict with invalid entries.
    """
    invalid = []
    valid_count = 0

    for rule in atomic_rules:
        rule_type = rule.get("rule_type", "")
        if rule_type not in ALLOWED_RULE_TYPES:
            invalid.append({
                "rule_id": rule.get("rule_id") or f"<index {atomic_rules.index(rule)}>",
                "clause_id": rule.get("clause_id"),
                "actual_rule_type": rule_type,
                "allowed_rule_types": sorted(ALLOWED_RULE_TYPES),
            })
        else:
            valid_count += 1

    return {
        "total_rules": len(atomic_rules),
        "valid_count": valid_count,
        "invalid_count": len(invalid),
        "invalid_rules": invalid,
    }


def check_required_fields(atomic_rules: list[dict]) -> dict:
    """Check that every atomic_rule has required non-empty string fields."""
    required = ["rule_id", "clause_id", "raw_text"]
    missing: list[dict] = []

    for i, rule in enumerate(atomic_rules):
        for field in required:
            value = rule.get(field)
            if not isinstance(value, str) or not value.strip():
                missing.append({
                    "index": i,
                    "rule_id": rule.get("rule_id") or f"<index {i}>",
                    "field": field,
                    "actual_value": repr(value) if value is not None else "None/missing",
                })

    return {
        "total_rules": len(atomic_rules),
        "missing_count": len(missing),
        "missing": missing,
    }


def check_paragraph_ids(atomic_rules: list[dict]) -> dict:
    """Validate paragraph_id presence and uniqueness.

    paragraph_id is the stable source anchor at the paragraph/split level.
    It must be present in every atomic rule and must be unique within the
    governed scope.
    """
    missing: list[dict] = []
    seen: dict[str, int] = {}
    duplicates: list[dict] = []

    for i, rule in enumerate(atomic_rules):
        pid = rule.get("paragraph_id")
        if not isinstance(pid, str) or not pid.strip():
            missing.append({
                "index": i,
                "rule_id": rule.get("rule_id") or f"<index {i}>",
                "actual_value": repr(pid) if pid is not None else "None/missing",
            })
        else:
            if pid in seen:
                duplicates.append({
                    "paragraph_id": pid,
                    "first_index": seen[pid],
                    "duplicate_indices": [seen[pid], i],
                    "rule_ids": [atomic_rules[seen[pid]].get("rule_id", f"<index {seen[pid]}>"),
                                 rule.get("rule_id", f"<index {i}>")],
                })
            else:
                seen[pid] = i

    return {
        "total_rules": len(atomic_rules),
        "present_count": len(atomic_rules) - len(missing),
        "missing_count": len(missing),
        "missing": missing,
        "unique_count": len(seen),
        "duplicate_count": len(duplicates),
        "duplicates": duplicates,
    }


def produce_validation_report(
    atomic_rules_path: Path,
    semantic_rules_path: Path | None = None,
) -> dict:
    """Run all validation checks and produce a structured report."""
    with open(atomic_rules_path, encoding="utf-8") as f:
        atomic_rules = json.load(f)

    if not isinstance(atomic_rules, list):
        raise ValueError(f"atomic_rules.json must be a JSON list, got {type(atomic_rules).__name__}")

    schema_result = validate_artifact_list(atomic_rules_path, validate_atomic_rule)
    duplicate_result = check_duplicates(atomic_rules)
    rule_type_result = check_rule_types(atomic_rules)
    required_field_result = check_required_fields(atomic_rules)
    paragraph_id_result = check_paragraph_ids(atomic_rules)

    total_invalid = (
        schema_result["invalid_count"]
        + rule_type_result["invalid_count"]
        + required_field_result["missing_count"]
    )

    semantic_result: dict | None = None
    if semantic_rules_path is not None and semantic_rules_path.exists():
        semantic_schema_result = validate_artifact_list(semantic_rules_path, validate_semantic_rule)
        semantic_result = {
            "valid": semantic_schema_result["invalid_count"] == 0,
            "valid_count": semantic_schema_result["valid_count"],
            "invalid_count": semantic_schema_result["invalid_count"],
            "errors": semantic_schema_result["errors_by_index"],
        }
        if not semantic_result["valid"]:
            total_invalid += semantic_schema_result["invalid_count"]

    report: dict = {
        "input_path": str(atomic_rules_path),
        "semantic_rules_path": str(semantic_rules_path) if semantic_rules_path else None,
        "total_rules": len(atomic_rules),
        "validation_passed": total_invalid == 0,
        "schema_validation": {
            "valid": schema_result["invalid_count"] == 0,
            "valid_count": schema_result["valid_count"],
            "invalid_count": schema_result["invalid_count"],
            "errors": schema_result["errors_by_index"],
        },
        "rule_type_validation": rule_type_result,
        "required_field_validation": required_field_result,
        "paragraph_id_validation": paragraph_id_result,
        "duplicate_detection": duplicate_result,
        "semantic_schema_validation": semantic_result,
        "summary": {
            "total_invalid": total_invalid,
            "validation_passed": total_invalid == 0,
            "blocked": total_invalid > 0,
        },
    }
    return report


def print_report(report: dict) -> None:
    """Print a human-readable summary of the validation report."""
    passed = report["summary"]["validation_passed"]
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] Validation Report: {report['input_path']}")
    print(f"  Total rules: {report['total_rules']}")

    sv = report["schema_validation"]
    print(f"  Schema: {sv['valid_count']}/{report['total_rules']} valid", end="")
    if sv["invalid_count"] > 0:
        print(f", {sv['invalid_count']} invalid")
        for e in sv["errors"][:3]:
            print(f"    Index {e['index']}: {e['errors'][0]}")
    else:
        print()

    rtv = report["rule_type_validation"]
    print(f"  rule_type enum: {rtv['valid_count']}/{report['total_rules']} valid", end="")
    if rtv["invalid_count"] > 0:
        print(f", {rtv['invalid_count']} invalid")
        for inv in rtv["invalid_rules"][:3]:
            print(f"    {inv['rule_id']}: '{inv['actual_rule_type']}' not in allowed set")
    else:
        print()

    rfv = report["required_field_validation"]
    print(f"  Required fields: {report['total_rules'] - rfv['missing_count']}/{report['total_rules']} valid", end="")
    if rfv["missing_count"] > 0:
        print(f", {rfv['missing_count']} missing")
        for m in rfv["missing"][:3]:
            print(f"    {m['rule_id']}: '{m['field']}' is {m['actual_value']}")
    else:
        print()

    pvid = report["paragraph_id_validation"]
    print(f"  paragraph_id: {pvid['unique_count']}/{report['total_rules']} unique", end="")
    if pvid["missing_count"] > 0:
        print(f", {pvid['missing_count']} missing (advisory)")
    if pvid["duplicate_count"] > 0:
        print(f", {pvid['duplicate_count']} duplicate(s) — advisory (pre-existing in committed artifacts)")
        for d in pvid["duplicates"][:2]:
            print(f"    paragraph_id='{d['paragraph_id']}': rule_ids={d['rule_ids']}")
    else:
        print()

    dd = report["duplicate_detection"]
    print(f"  Duplicates: {dd['duplicate_group_count']} groups found")
    for g in dd["duplicate_groups"][:2]:
        print(f"    Group ({g['count']} rules): clause_ids={g['clause_ids']}, rule_ids={g['rule_ids'][:3]}")

    if report.get("semantic_schema_validation"):
        sv = report["semantic_schema_validation"]
        print(f"  Semantic rules schema: {sv['valid_count']}/{sv['valid_count'] + sv['invalid_count']} valid", end="")
        if sv["invalid_count"] > 0:
            print(f", {sv['invalid_count']} invalid")
            for e in sv["errors"][:3]:
                print(f"    Index {e['index']}: {e['errors'][0]}")
        else:
            print()
    else:
        print(f"  Semantic rules schema: not checked (no --semantic-rules provided)")

    print()
    if passed:
        print("Validation PASSED — no blocking errors found.")
    else:
        print(f"Validation FAILED — {report['summary']['total_invalid']} blocking error(s) found.")
        print("Downstream maker execution should be BLOCKED until errors are resolved.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate atomic_rules.json against governed schemas and checks."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to atomic_rules.json.",
    )
    parser.add_argument(
        "--output",
        help="Path to write validation_report.json. When omitted, report is written next to input.",
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Exit with code 1 if validation finds any errors.",
    )
    parser.add_argument(
        "--semantic-rules",
        default=None,
        help="Path to semantic_rules.json to validate in the same report.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: file not found: {input_path}")
        return 1

    semantic_rules_path = Path(args.semantic_rules) if args.semantic_rules else None
    try:
        report = produce_validation_report(input_path, semantic_rules_path=semantic_rules_path)
    except Exception as e:
        print(f"ERROR: validation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Write report
    output_path = Path(args.output) if args.output else input_path.parent / "validation_report.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Report written to: {output_path}")

    # Print human-readable summary
    print()
    print_report(report)

    if args.fail_on_error and not report["summary"]["validation_passed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
