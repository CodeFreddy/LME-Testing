"""
Schema-based validation for governed LME Testing artifacts.

Uses JSON Schema (draft-07) to validate:
- atomic_rule artifacts
- semantic_rule artifacts
- maker_output (maker_cases.jsonl records)
- checker_output (checker_reviews.jsonl records)

Each artifact type has a "required" section defining mandatory fields
and a "properties" section defining all accepted fields with their types
and constraints.

Usage:
    from schemas import validate_atomic_rule, validate_semantic_rule
    from schemas import validate_maker_output, validate_checker_output

    errors = validate_semantic_rule(artifact)
    if errors:
        for err in errors:
            print(err)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

import jsonschema
from jsonschema import Draft7Validator, ValidationError

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = Path(__file__).resolve().parent


def _load_schema(name: str) -> dict:
    """Load a JSON schema file by name."""
    path = SCHEMAS_DIR / f"{name}.schema.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


ATOMIC_RULE_SCHEMA = _load_schema("atomic_rule")
SEMANTIC_RULE_SCHEMA = _load_schema("semantic_rule")
MAKER_OUTPUT_SCHEMA = _load_schema("maker_output")
CHECKER_OUTPUT_SCHEMA = _load_schema("checker_output")


def validate_atomic_rule(artifact: dict) -> list[str]:
    """Validate an atomic_rule artifact against its schema.

    Returns a list of error messages. Empty list means valid.
    """
    validator = Draft7Validator(ATOMIC_RULE_SCHEMA)
    return _format_errors(validator.iter_errors(artifact))


def validate_semantic_rule(artifact: dict) -> list[str]:
    """Validate a semantic_rule artifact against its schema.

    Returns a list of error messages. Empty list means valid.
    """
    validator = Draft7Validator(SEMANTIC_RULE_SCHEMA)
    return _format_errors(validator.iter_errors(artifact))


def validate_maker_output(artifact: dict) -> list[str]:
    """Validate a maker_output record (one line from maker_cases.jsonl) against its schema.

    Returns a list of error messages. Empty list means valid.
    """
    validator = Draft7Validator(MAKER_OUTPUT_SCHEMA)
    return _format_errors(validator.iter_errors(artifact))


def validate_checker_output(artifact: dict) -> list[str]:
    """Validate a checker_output record (one line from checker_reviews.jsonl) against its schema.

    Returns a list of error messages. Empty list means valid.
    """
    validator = Draft7Validator(CHECKER_OUTPUT_SCHEMA)
    return _format_errors(validator.iter_errors(artifact))


def _format_errors(errors: Iterator[ValidationError]) -> list[str]:
    """Format jsonschema ValidationError iterator into human-readable messages."""
    result = []
    for err in errors:
        path = ".".join(str(p) for p in err.path) if err.path else "(root)"
        result.append(f"[{path}] {err.message}")
    return result


def validate_artifact_list(
    artifact_path: Path,
    validator_fn,
) -> dict:
    """Validate a JSON artifact file (list of objects) using the given validator.

    Args:
        artifact_path: Path to the JSON artifact file.
        validator_fn: One of validate_atomic_rule, validate_semantic_rule, etc.

    Returns:
        Dict with 'total', 'valid_count', 'invalid_count', 'errors_by_index'.
    """
    with open(artifact_path, encoding="utf-8") as f:
        artifacts = json.load(f)

    if not isinstance(artifacts, list):
        return {
            "valid": False,
            "error": f"Artifact must be a JSON list, got {type(artifacts).__name__}",
            "total": 0,
            "valid_count": 0,
            "invalid_count": 0,
            "errors_by_index": [],
        }

    valid_count = 0
    invalid_count = 0
    errors_by_index: list[dict | None] = []

    for i, artifact in enumerate(artifacts):
        errs = validator_fn(artifact)
        if errs:
            invalid_count += 1
            errors_by_index.append({"index": i, "errors": errs})
        else:
            valid_count += 1
            errors_by_index.append(None)

    return {
        "valid": invalid_count == 0,
        "total": len(artifacts),
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "errors_by_index": [e for e in errors_by_index if e is not None],
    }


def validate_jsonl(
    jsonl_path: Path,
    validator_fn,
) -> dict:
    """Validate a JSONL artifact file (one JSON object per line) using the given validator.

    Args:
        jsonl_path: Path to the JSONL artifact file.
        validator_fn: One of validate_maker_output, validate_checker_output, etc.

    Returns:
        Dict with 'total', 'valid_count', 'invalid_count', 'errors_by_line'.
    """
    valid_count = 0
    invalid_count = 0
    errors_by_line: list[dict] = []

    with open(jsonl_path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                artifact = json.loads(line)
            except json.JSONDecodeError as e:
                invalid_count += 1
                errors_by_line.append({
                    "line": line_num,
                    "errors": [f"Invalid JSON on line {line_num}: {e}"],
                })
                continue

            errs = validator_fn(artifact)
            if errs:
                invalid_count += 1
                errors_by_line.append({"line": line_num, "errors": errs})
            else:
                valid_count += 1

    return {
        "valid": invalid_count == 0,
        "total": valid_count + invalid_count,
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "errors_by_line": errors_by_line,
    }


# ----------------------------------------------------------------------
# Convenience CLI entry points (can be run via: python -m schemas)
# ----------------------------------------------------------------------

def _main() -> int:
    """Validate governed artifacts using their schemas. Exits 0 if all pass, 1 otherwise."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate LME Testing artifacts against JSON schemas.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    atomic_parser = subparsers.add_parser("atomic-rules", help="Validate atomic_rules.json")
    atomic_parser.add_argument("file", help="Path to atomic_rules.json")

    semantic_parser = subparsers.add_parser("semantic-rules", help="Validate semantic_rules.json")
    semantic_parser.add_argument("file", help="Path to semantic_rules.json")

    maker_parser = subparsers.add_parser("maker", help="Validate maker_cases.jsonl")
    maker_parser.add_argument("file", help="Path to maker_cases.jsonl")

    checker_parser = subparsers.add_parser("checker", help="Validate checker_reviews.jsonl")
    checker_parser.add_argument("file", help="Path to checker_reviews.jsonl")

    args = parser.parse_args()
    path = Path(args.file)

    if not path.exists():
        print(f"ERROR: file not found: {path}")
        return 1

    if args.command == "atomic-rules":
        result = validate_artifact_list(path, validate_atomic_rule)
    elif args.command == "semantic-rules":
        result = validate_artifact_list(path, validate_semantic_rule)
    elif args.command == "maker":
        result = validate_jsonl(path, validate_maker_output)
    elif args.command == "checker":
        result = validate_jsonl(path, validate_checker_output)
    else:
        return 1

    print(f"Total: {result['total']}, Valid: {result['valid_count']}, Invalid: {result['invalid_count']}")

    if result["errors_by_index"]:
        for e in result["errors_by_index"]:
            print(f"  Index {e['index']}:")
            for err in e["errors"]:
                print(f"    - {err}")
    if result.get("errors_by_line"):
        for e in result["errors_by_line"]:
            print(f"  Line {e['line']}:")
            for err in e["errors"]:
                print(f"    - {err}")

    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(_main())
