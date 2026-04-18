"""Unit tests for scripts/check_release_governance.py."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Import from the scripts directory
import scripts.check_release_governance as rg_module


# -------------------------------------------------------------------------- #
# Helper: build a minimal repo structure in a temp directory
# -------------------------------------------------------------------------- #

def _make_config_files(root: Path) -> None:
    """Create the three config files with valid content."""
    # approved_providers.json
    approved = {
        "providers": [
            {
                "provider_name": "stub",
                "model": "stub-model",
                "tier": 1,
                "status": "approved",
                "approved_for_roles": ["maker", "checker", "planner"],
            },
            {
                "provider_name": "minimax",
                "model": "MiniMax-M2.7",
                "tier": 1,
                "status": "approved",
                "approved_for_roles": ["maker", "checker", "planner"],
            },
            {
                "provider_name": "experimental_provider",
                "model": "exp-model",
                "tier": 2,
                "status": "experimental",
                "approved_for_roles": ["maker"],
            },
        ]
    }
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "config" / "approved_providers.json").write_text(
        json.dumps(approved, indent=2), encoding="utf-8"
    )

    # benchmark_thresholds.json
    thresholds = {
        "schema_validation": {
            "failure_rate": {"threshold": 0.0}
        },
        "checker_instability": {"threshold": 0.05},
        "coverage": {"minimum_coverage_percent": 80.0},
    }
    (root / "config" / "benchmark_thresholds.json").write_text(
        json.dumps(thresholds, indent=2), encoding="utf-8"
    )

    # compatibility_matrix.json
    matrix = {
        "matrix": [
            {
                "provider": "stub",
                "model": "stub-model",
                "phases": {
                    "phase1": {"compatible": True},
                    "phase2": {"compatible": True},
                    "phase3": {"compatible": True},
                },
                "pipelines": {"maker": True, "checker": True},
            },
            {
                "provider": "minimax",
                "model": "MiniMax-M2.7",
                "phases": {
                    "phase1": {"compatible": True},
                    "phase2": {"compatible": True},
                    "phase3": {"compatible": True},
                },
                "pipelines": {"maker": True, "checker": True},
            },
        ]
    }
    (root / "config" / "compatibility_matrix.json").write_text(
        json.dumps(matrix, indent=2), encoding="utf-8"
    )


def _make_releases_md(root: Path, content: str) -> None:
    """Write docs/releases/RELEASES.md with given content."""
    (root / "docs" / "releases").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "releases" / "RELEASES.md").write_text(content, encoding="utf-8")


def _make_governance_signals(root: Path, data: dict) -> None:
    """Write runs/governance_signals.json."""
    (root / "runs").mkdir(parents=True, exist_ok=True)
    (root / "runs" / "governance_signals.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )


# -------------------------------------------------------------------------- #
# Tests for check_approved_providers
# -------------------------------------------------------------------------- #

class ApprovedProvidersTests(unittest.TestCase):
    """Tests for check_approved_providers()."""

    def test_passes_with_valid_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_config_files(root)
            with patch.object(rg_module, "REPO_ROOT", root):
                errors = rg_module.check_approved_providers()
        self.assertEqual(errors, [])

    def test_fails_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(rg_module, "REPO_ROOT", root):
                errors = rg_module.check_approved_providers()
        self.assertTrue(errors)
        self.assertIn("approved_providers.json is missing", errors[0])

    def test_fails_with_invalid_provider_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir()
            (root / "config" / "approved_providers.json").write_text(
                json.dumps({"providers": [
                    {"provider_name": "bad", "model": "m", "tier": 1, "status": "invalid_status",
                     "approved_for_roles": []}
                ]}), encoding="utf-8"
            )
            with patch.object(rg_module, "REPO_ROOT", root):
                errors = rg_module.check_approved_providers()
        self.assertTrue(errors)
        self.assertTrue(any("invalid status" in e for e in errors))


# -------------------------------------------------------------------------- #
# Tests for check_compatibility_matrix
# -------------------------------------------------------------------------- #

class CompatibilityMatrixTests(unittest.TestCase):
    """Tests for check_compatibility_matrix()."""

    def test_passes_with_valid_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_config_files(root)
            with patch.object(rg_module, "REPO_ROOT", root):
                errors = rg_module.check_compatibility_matrix()
        self.assertEqual(errors, [])

    def test_fails_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(rg_module, "REPO_ROOT", root):
                errors = rg_module.check_compatibility_matrix()
        self.assertTrue(errors)
        self.assertIn("compatibility_matrix.json is missing", errors[0])

    def test_fails_when_missing_matrix_field(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir()
            (root / "config" / "compatibility_matrix.json").write_text(
                json.dumps({}), encoding="utf-8"
            )
            with patch.object(rg_module, "REPO_ROOT", root):
                errors = rg_module.check_compatibility_matrix()
        self.assertTrue(errors)
        self.assertIn("missing 'matrix' field", errors[0])


# -------------------------------------------------------------------------- #
# Tests for check_benchmark_thresholds
# -------------------------------------------------------------------------- #

class BenchmarkThresholdsTests(unittest.TestCase):
    """Tests for check_benchmark_thresholds()."""

    def test_passes_with_all_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_config_files(root)
            with patch.object(rg_module, "REPO_ROOT", root):
                errors = rg_module.check_benchmark_thresholds()
        self.assertEqual(errors, [])

    def test_fails_when_missing_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir()
            (root / "config" / "benchmark_thresholds.json").write_text(
                json.dumps({"schema_validation": {}}), encoding="utf-8"
            )
            with patch.object(rg_module, "REPO_ROOT", root):
                errors = rg_module.check_benchmark_thresholds()
        self.assertTrue(errors)
        self.assertTrue(any("missing" in e for e in errors))


# -------------------------------------------------------------------------- #
# Tests for check_release_artifacts
# -------------------------------------------------------------------------- #

class ReleaseArtifactsTests(unittest.TestCase):
    """Tests for check_release_artifacts()."""

    def test_passes_with_release_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_releases_md(root, "# Release\n\n| Version | Date |\n| 1.0.0 | 2026-04-14 |\n")
            with patch.object(rg_module, "REPO_ROOT", root):
                errors = rg_module.check_release_artifacts()
        self.assertEqual(errors, [])

    def test_fails_when_no_release_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs" / "releases").mkdir(parents=True)
            with patch.object(rg_module, "REPO_ROOT", root):
                errors = rg_module.check_release_artifacts()
        self.assertTrue(errors)
        self.assertIn("no release record files", errors[0])


# -------------------------------------------------------------------------- #
# Tests for check_governance_signals_recent
# -------------------------------------------------------------------------- #

class GovernanceSignalsRecentTests(unittest.TestCase):
    """Tests for check_governance_signals_recent()."""

    def test_passes_within_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_config_files(root)
            _make_governance_signals(root, {
                "schema_failure_rate": 0.0,
                "schema_signals": {"failure_rate": 0.0},
                "coverage_signals": {"latest_coverage_percent": 100.0},
                "checker_instability_signals": {"instability_rate": 0.0},
            })
            with patch.object(rg_module, "REPO_ROOT", root):
                errors = rg_module.check_governance_signals_recent()
        self.assertEqual(errors, [])

    def test_fails_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with patch.object(rg_module, "REPO_ROOT", root):
                errors = rg_module.check_governance_signals_recent()
        self.assertTrue(errors)
        self.assertIn("not found", errors[0])


# -------------------------------------------------------------------------- #
# Tests for check_release_record_governance
# -------------------------------------------------------------------------- #

class ReleaseRecordGovernanceTests(unittest.TestCase):
    """Tests for check_release_record_governance()."""

    def test_passes_with_valid_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_config_files(root)
            releases_md = (
                "# Release\n\n"
                "| Release | Date | Phase | Status |\n"
                "| 1.0.0 | 2026-04-14 | Phase 3 | Current |\n\n"
                "**Approved Providers:**\n"
                "- `stub` (Tier 1, all roles)\n"
                "- `minimax/MiniMax-M2.7` (Tier 1, all roles)\n"
            )
            _make_releases_md(root, releases_md)
            with patch.object(rg_module, "REPO_ROOT", root):
                errors = rg_module.check_release_record_governance()
        self.assertEqual(errors, [])

    def test_fails_when_provider_not_approved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_config_files(root)
            releases_md = (
                "# Release\n\n"
                "| Release | Date | Phase | Status |\n"
                "| 1.0.0 | 2026-04-14 | Phase 3 | Current |\n\n"
                "**Approved Providers:**\n"
                "- `unknown_provider` (Tier 1)\n"
            )
            _make_releases_md(root, releases_md)
            with patch.object(rg_module, "REPO_ROOT", root):
                errors = rg_module.check_release_record_governance()
        self.assertTrue(errors)
        self.assertTrue(any("not in approved_providers.json" in e for e in errors))

    def test_fails_when_experimental_provider_used(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_config_files(root)
            releases_md = (
                "# Release\n\n"
                "| Release | Date | Phase | Status |\n"
                "| 1.0.0 | 2026-04-14 | Phase 3 | Current |\n\n"
                "**Approved Providers:**\n"
                "- `experimental_provider/exp-model` (Tier 2)\n"
            )
            _make_releases_md(root, releases_md)
            with patch.object(rg_module, "REPO_ROOT", root):
                errors = rg_module.check_release_record_governance()
        self.assertTrue(errors)
        self.assertTrue(any("experimental" in e for e in errors))

    def test_passes_when_releases_md_missing(self) -> None:
        # When RELEASES.md is missing, the check should fail gracefully
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_config_files(root)
            with patch.object(rg_module, "REPO_ROOT", root):
                errors = rg_module.check_release_record_governance()
        self.assertTrue(errors)
        self.assertTrue(any("not found" in e or "could not be parsed" in e for e in errors))


# -------------------------------------------------------------------------- #
# Tests for check_release_signals_thresholds
# -------------------------------------------------------------------------- #

class ReleaseSignalsThresholdsTests(unittest.TestCase):
    """Tests for check_release_signals_thresholds()."""

    def test_passes_within_thresholds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_config_files(root)
            _make_governance_signals(root, {
                "schema_failure_rate": 0.0,
                "checker_instability_rate": 0.0,
                "checker_instability_signals": {"instability_rate": 0.0},
                "coverage_signals": {"latest_coverage_percent": 100.0},
            })
            with patch.object(rg_module, "REPO_ROOT", root):
                errors = rg_module.check_release_signals_thresholds()
        self.assertEqual(errors, [])

    def test_fails_exceeds_schema_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_config_files(root)
            _make_governance_signals(root, {
                "schema_failure_rate": 0.5,  # > 0.0 threshold
                "checker_instability_signals": {"instability_rate": 0.0},
                "coverage_signals": {"latest_coverage_percent": 100.0},
            })
            with patch.object(rg_module, "REPO_ROOT", root):
                errors = rg_module.check_release_signals_thresholds()
        self.assertTrue(errors)
        self.assertTrue(any("Schema failure rate" in e for e in errors))

    def test_fails_below_coverage_minimum(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_config_files(root)
            _make_governance_signals(root, {
                "schema_failure_rate": 0.0,
                "checker_instability_signals": {"instability_rate": 0.0},
                "coverage_signals": {"latest_coverage_percent": 50.0},  # < 80.0 minimum
            })
            with patch.object(rg_module, "REPO_ROOT", root):
                errors = rg_module.check_release_signals_thresholds()
        self.assertTrue(errors)
        self.assertTrue(any("Coverage" in e and "below minimum" in e for e in errors))

    def test_fails_exceeds_instability_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_config_files(root)
            _make_governance_signals(root, {
                "schema_failure_rate": 0.0,
                "checker_instability_signals": {"instability_rate": 0.1},  # > 0.05
                "coverage_signals": {"latest_coverage_percent": 100.0},
            })
            with patch.object(rg_module, "REPO_ROOT", root):
                errors = rg_module.check_release_signals_thresholds()
        self.assertTrue(errors)
        self.assertTrue(any("Checker instability" in e for e in errors))


# -------------------------------------------------------------------------- #
# Tests for check_compatibility_matrix_for_release_provider
# -------------------------------------------------------------------------- #

class ReleaseProviderCompatibilityTests(unittest.TestCase):
    """Tests for check_compatibility_matrix_for_release_provider()."""

    def test_passes_with_compatible_provider(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_config_files(root)
            releases_md = (
                "# Release\n\n"
                "| Release | Date | Phase | Status |\n"
                "| 1.0.0 | 2026-04-14 | Phase 3 | Current |\n\n"
                "**Approved Providers:**\n"
                "- `stub` (Tier 1, all roles)\n"
            )
            _make_releases_md(root, releases_md)
            with patch.object(rg_module, "REPO_ROOT", root):
                errors = rg_module.check_compatibility_matrix_for_release_provider()
        self.assertEqual(errors, [])

    def test_fails_when_provider_not_in_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_config_files(root)
            releases_md = (
                "# Release\n\n"
                "| Release | Date | Phase | Status |\n"
                "| 1.0.0 | 2026-04-14 | Phase 3 | Current |\n\n"
                "**Approved Providers:**\n"
                "- `nonexistent_provider` (Tier 1)\n"
            )
            _make_releases_md(root, releases_md)
            with patch.object(rg_module, "REPO_ROOT", root):
                errors = rg_module.check_compatibility_matrix_for_release_provider()
        self.assertTrue(errors)
        self.assertTrue(any("not found in compatibility_matrix.json" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
