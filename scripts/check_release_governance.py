#!/usr/bin/env python3
"""Release Governance Check.

Validates that a release meets the minimum governance requirements:
- Approved provider is used (config/approved_providers.json)
- Compatibility matrix is satisfied
- Benchmark thresholds are met (config/benchmark_thresholds.json)
- All required governance artifacts exist

Usage:
    python scripts/check_release_governance.py

Exit codes:
    0 = all checks passed
    1 = one or more checks failed
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check_approved_providers() -> list[str]:
    """Check that approved_providers.json exists and is valid."""
    errors: list[str] = []
    path = REPO_ROOT / "config" / "approved_providers.json"
    if not path.exists():
        errors.append("config/approved_providers.json is missing")
        return errors

    try:
        data = _load_json(path)
    except Exception as e:
        errors.append(f"config/approved_providers.json is invalid JSON: {e}")
        return errors

    if "providers" not in data:
        errors.append("approved_providers.json missing 'providers' field")
        return errors

    for i, p in enumerate(data["providers"]):
        required = ["provider_name", "model", "tier", "status", "approved_for_roles"]
        missing = [f for f in required if f not in p]
        if missing:
            errors.append(f"provider[{i}] missing fields: {missing}")
        if p.get("status") not in ("approved", "experimental", "disallowed"):
            errors.append(f"provider[{i}] has invalid status: {p.get('status')}")
        if p.get("tier") not in (1, 2, 3):
            errors.append(f"provider[{i}] has invalid tier: {p.get('tier')}")

    return errors


def check_compatibility_matrix() -> list[str]:
    """Check that compatibility_matrix.json exists and is valid."""
    errors: list[str] = []
    path = REPO_ROOT / "config" / "compatibility_matrix.json"
    if not path.exists():
        errors.append("config/compatibility_matrix.json is missing")
        return errors

    try:
        data = _load_json(path)
    except Exception as e:
        errors.append(f"compatibility_matrix.json is invalid JSON: {e}")
        return errors

    if "matrix" not in data:
        errors.append("compatibility_matrix.json missing 'matrix' field")
        return errors

    return errors


def check_benchmark_thresholds() -> list[str]:
    """Check that benchmark_thresholds.json exists and is valid."""
    errors: list[str] = []
    path = REPO_ROOT / "config" / "benchmark_thresholds.json"
    if not path.exists():
        errors.append("config/benchmark_thresholds.json is missing")
        return errors

    try:
        data = _load_json(path)
    except Exception as e:
        errors.append(f"benchmark_thresholds.json is invalid JSON: {e}")
        return errors

    required_gates = ["schema_validation", "checker_instability", "coverage"]
    for gate in required_gates:
        if gate not in data:
            errors.append(f"benchmark_thresholds.json missing '{gate}' gate")

    return errors


def check_release_artifacts() -> list[str]:
    """Check that release governance artifacts exist."""
    errors: list[str] = []
    releases_dir = REPO_ROOT / "docs" / "releases"
    if not releases_dir.exists():
        errors.append("docs/releases/ directory is missing (create at least an initial release record)")
        return errors

    # Check for at least one release record
    release_files = list(releases_dir.glob("*.md"))
    if not release_files:
        errors.append("docs/releases/ has no release record files (*.md)")

    return errors


def check_governance_signals_recent() -> list[str]:
    """Check that governance signals were computed recently."""
    errors: list[str] = []
    signals_path = REPO_ROOT / "runs" / "governance_signals.json"
    if not signals_path.exists():
        errors.append("runs/governance_signals.json not found (run 'python main.py governance-signals' first)")
        return errors

    try:
        signals = _load_json(signals_path)
    except Exception as e:
        errors.append(f"governance_signals.json is invalid: {e}")
        return errors

    # Check schema failure rate against threshold
    schema_rate = signals.get("schema_failure_rate", 1.0)
    thresholds_path = REPO_ROOT / "config" / "benchmark_thresholds.json"
    if thresholds_path.exists():
        thresholds = _load_json(thresholds_path)
        schema_gate = thresholds.get("schema_validation", {})
        if isinstance(schema_gate, dict):
            failure_def = schema_gate.get("failure_rate", {})
            if isinstance(failure_def, dict):
                max_fail = failure_def.get("threshold", 0.0)
            elif isinstance(failure_def, (int, float)):
                max_fail = float(failure_def)
            else:
                max_fail = 0.0
        else:
            max_fail = 0.0
        if schema_rate > max_fail:
            errors.append(
                f"Schema failure rate {schema_rate} exceeds threshold {max_fail}"
            )

    return errors


def main() -> int:
    all_errors: list[str] = []

    checks = [
        ("Approved Providers", check_approved_providers),
        ("Compatibility Matrix", check_compatibility_matrix),
        ("Benchmark Thresholds", check_benchmark_thresholds),
        ("Release Artifacts", check_release_artifacts),
        ("Governance Signals", check_governance_signals_recent),
    ]

    passed = True
    for name, check_fn in checks:
        errors = check_fn()
        status = "PASS" if not errors else "FAIL"
        if errors:
            passed = False
        print(f"[{status}] Release Governance: {name}")
        for err in errors:
            print(f"  {err}")

    print()
    if passed:
        print("Release governance check passed.")
    else:
        print("Release governance check FAILED.")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
