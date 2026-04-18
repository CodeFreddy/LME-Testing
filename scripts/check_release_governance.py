#!/usr/bin/env python3
"""Release Governance Check.

Validates that a release meets the minimum governance requirements:
- Approved provider is used (config/approved_providers.json)
- Compatibility matrix is satisfied
- Benchmark thresholds are met (config/benchmark_thresholds.json)
- All required governance artifacts exist
- Release record references approved providers and compatible phases

Usage:
    python scripts/check_release_governance.py

Exit codes:
    0 = all checks passed
    1 = one or more checks failed
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Regex to extract provider/model from "provider/model" strings in release docs.
PROVIDER_MODEL_RE = re.compile(r"`?([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.\-]+)`?")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_releases_md(repo_root: Path) -> dict | None:
    """Parse docs/releases/RELEASES.md to extract current release info.

    Returns a dict with keys: version, date, phase, approved_providers (list of "provider/model" strings)
    or None if the file cannot be parsed.
    """
    releases_path = repo_root / "docs" / "releases" / "RELEASES.md"
    if not releases_path.exists():
        return None
    text = _load_text(releases_path)

    # Extract version/date/phase from the "Current Release" table.
    # Format: | 1.0.0 | 2026-04-14 | Phase 3 Gate 1-4 | Current |
    version = None
    date = None
    phase = None
    table_match = re.search(
        r"\*\*Phase:\*\*\s*(.+?)(?:\n|$)", text, re.IGNORECASE
    )
    if table_match:
        phase = table_match.group(1).strip()

    # Try to extract version and date from table rows like "| 1.0.0 | 2026-04-14 | ..."
    for line in text.splitlines():
        m = re.match(r"\|\s*([0-9]+\.[0-9]+\.[0-9]+)\s*\|\s*([0-9]{4}-[0-9]{2}-[0-9]{2})\s*\|", line)
        if m:
            version = m.group(1)
            date = m.group(2)
            break

    # Extract approved providers from "Approved Providers:" section.
    # Format: "- `stub` (Tier 1, all roles)" or "- `minimax/MiniMax-M2.7` (Tier 1, all roles)"
    approved_providers: list[str] = []
    in_approved_section = False
    for line in text.splitlines():
        if re.match(r"\*\*Approved Providers:\*\*", line, re.IGNORECASE):
            in_approved_section = True
            continue
        if in_approved_section:
            # Stop at next section or empty line after list
            if line.strip() == "" or (line.strip() and not line.strip().startswith("-") and not line.strip().startswith("`")):
                # Check if we've hit a new section
                if not line.strip().startswith("-"):
                    break
            m = re.search(r"`?([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.\-]+)`?", line)
            if m:
                approved_providers.append(f"{m.group(1)}/{m.group(2)}")
            elif re.search(r"`([a-zA-Z0-9_-]+)`", line):
                # Single provider without model
                single = re.search(r"`([a-zA-Z0-9_-]+)`", line)
                if single:
                    provider_name = single.group(1)
                    # Try to find model from approved_providers.json
                    approved_providers.append(provider_name)

    return {
        "version": version,
        "date": date,
        "phase": phase,
        "approved_providers": approved_providers,
    }


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


def check_release_record_governance() -> list[str]:
    """Check that the release record references only approved providers.

    Parses docs/releases/RELEASES.md to extract the "Approved Providers" section,
    then verifies each provider is listed in config/approved_providers.json with
    status "approved" (not "experimental" or "disallowed").
    """
    errors: list[str] = []
    release_info = _parse_releases_md(REPO_ROOT)
    if release_info is None:
        errors.append("docs/releases/RELEASES.md not found or could not be parsed")
        return errors

    providers_path = REPO_ROOT / "config" / "approved_providers.json"
    if not providers_path.exists():
        errors.append("config/approved_providers.json not found")
        return errors

    try:
        approved_data = _load_json(providers_path)
    except Exception as e:
        errors.append(f"config/approved_providers.json is invalid JSON: {e}")
        return errors

    providers_list = approved_data.get("providers", [])
    approved_names = {p.get("provider_name") for p in providers_list}

    for prov in release_info.get("approved_providers", []):
        # prov may be "provider/model" or just "provider"
        if "/" in prov:
            provider_name, model = prov.split("/", 1)
        else:
            provider_name = prov
            model = None

        if provider_name not in approved_names:
            errors.append(
                f"Release record references provider '{provider_name}' which is not in approved_providers.json"
            )
            continue

        # Find the provider entry and check status
        for p in providers_list:
            if p.get("provider_name") == provider_name:
                status = p.get("status", "unknown")
                if status != "approved":
                    errors.append(
                        f"Provider '{provider_name}' has status '{status}', must be 'approved' for release"
                    )
                if model and p.get("model") != model:
                    errors.append(
                        f"Provider '{provider_name}' model '{model}' does not match approved model '{p.get('model')}'"
                    )
                break

    return errors


def check_release_signals_thresholds() -> list[str]:
    """Validate that governance signals meet all benchmark thresholds.

    Reads runs/governance_signals.json and config/benchmark_thresholds.json,
    then checks:
    - schema_failure_rate <= schema_validation threshold
    - instability_rate <= checker_instability threshold
    - coverage_percent >= coverage minimum
    """
    errors: list[str] = []
    signals_path = REPO_ROOT / "runs" / "governance_signals.json"
    if not signals_path.exists():
        errors.append("runs/governance_signals.json not found")
        return errors

    try:
        signals = _load_json(signals_path)
    except Exception as e:
        errors.append(f"governance_signals.json is invalid: {e}")
        return errors

    thresholds_path = REPO_ROOT / "config" / "benchmark_thresholds.json"
    if not thresholds_path.exists():
        errors.append("config/benchmark_thresholds.json not found")
        return errors

    try:
        thresholds = _load_json(thresholds_path)
    except Exception as e:
        errors.append(f"config/benchmark_thresholds.json is invalid JSON: {e}")
        return errors

    # Schema validation threshold
    schema_gate = thresholds.get("schema_validation", {})
    if isinstance(schema_gate, dict):
        failure_def = schema_gate.get("failure_rate", {})
        if isinstance(failure_def, dict):
            max_schema_fail = failure_def.get("threshold", 0.0)
        elif isinstance(failure_def, (int, float)):
            max_schema_fail = float(failure_def)
        else:
            max_schema_fail = 0.0
    else:
        max_schema_fail = 0.0
    schema_rate = signals.get("schema_failure_rate", 1.0)
    if schema_rate > max_schema_fail:
        errors.append(
            f"Schema failure rate {schema_rate} exceeds threshold {max_schema_fail}"
        )

    # Checker instability threshold
    instability_gate = thresholds.get("checker_instability", {})
    if isinstance(instability_gate, dict):
        max_instability = instability_gate.get("threshold", 0.05)
    elif isinstance(instability_gate, (int, float)):
        max_instability = float(instability_gate)
    else:
        max_instability = 0.05
    # Prefer nested signals path, fall back to top-level key
    instability_signals = signals.get("checker_instability_signals", {})
    instability_rate = float(instability_signals.get("instability_rate", signals.get("checker_instability_rate", 0.0)))
    if instability_rate > max_instability:
        errors.append(
            f"Checker instability rate {instability_rate} exceeds threshold {max_instability}"
        )

    # Coverage minimum — prefer nested signals path for latest coverage
    coverage_gate = thresholds.get("coverage", {})
    if isinstance(coverage_gate, dict):
        min_coverage = coverage_gate.get("minimum_coverage_percent", 80.0)
    elif isinstance(coverage_gate, (int, float)):
        min_coverage = float(coverage_gate)
    else:
        min_coverage = 80.0
    coverage_signals_data = signals.get("coverage_signals", {})
    coverage_percent = float(coverage_signals_data.get("latest_coverage_percent", signals.get("coverage_percent", 0.0)))
    if coverage_percent < min_coverage:
        errors.append(
            f"Coverage {coverage_percent}% is below minimum {min_coverage}%"
        )

    return errors


def check_compatibility_matrix_for_release_provider() -> list[str]:
    """Validate that the provider/model in the release record is compatible.

    Parses docs/releases/RELEASES.md to extract approved providers, then checks
    config/compatibility_matrix.json for entries covering each provider/model
    with appropriate phase compatibility.
    """
    errors: list[str] = []
    release_info = _parse_releases_md(REPO_ROOT)
    if release_info is None:
        errors.append("docs/releases/RELEASES.md not found or could not be parsed")
        return errors

    matrix_path = REPO_ROOT / "config" / "compatibility_matrix.json"
    if not matrix_path.exists():
        errors.append("config/compatibility_matrix.json not found")
        return errors

    try:
        matrix_data = _load_json(matrix_path)
    except Exception as e:
        errors.append(f"config/compatibility_matrix.json is invalid JSON: {e}")
        return errors

    matrix_entries = matrix_data.get("matrix", [])
    matrix_keys = {(entry.get("provider"), entry.get("model")) for entry in matrix_entries}

    for prov in release_info.get("approved_providers", []):
        if "/" in prov:
            provider_name, model = prov.split("/", 1)
        else:
            provider_name = prov
            model = None  # stub-type providers may not have model suffix

        # Find the matrix entry for this provider/model
        found = False
        for entry in matrix_entries:
            if entry.get("provider") == provider_name:
                if model is None or entry.get("model") == model:
                    found = True
                    # Validate phase compatibility if phase is specified
                    phase = release_info.get("phase", "")
                    if phase:
                        phases = entry.get("phases", {})
                        phase_key = phase.lower().replace(" ", "_").split("_gate")[0].strip()
                        # Try exact match first
                        phase_entry = phases.get(phase_key)
                        if phase_entry is None:
                            # Try "phase1", "phase2", "phase3" normalization
                            for pk, pv in phases.items():
                                if phase_key.startswith(pk.replace("phase", "")):
                                    phase_entry = pv
                                    break
                        if isinstance(phase_entry, dict) and not phase_entry.get("compatible", False):
                            errors.append(
                                f"Provider '{provider_name}/{model}' is not compatible for phase '{phase}' "
                                f"(compatible={phase_entry.get('compatible')})"
                            )
                    break

        if not found:
            errors.append(
                f"Provider '{prov}' not found in compatibility_matrix.json"
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
        ("Release Record", check_release_record_governance),
        ("Release Signals Thresholds", check_release_signals_thresholds),
        ("Release Provider Compatibility", check_compatibility_matrix_for_release_provider),
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
