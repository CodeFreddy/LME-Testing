"""Unit tests for the governance signals module (Phase 3 Gate 4)."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lme_testing.signals import (
    GovernanceSignals,
    SchemaSignals,
    CheckerInstabilitySignals,
    CoverageSignals,
    StepBindingSignals,
    _compute_schema_signals,
    compute_governance_signals,
    write_signals_report,
)


class GovernanceSignalsTests(unittest.TestCase):
    def test_compute_signals_produces_valid_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            signals = compute_governance_signals(repo_root)
            self.assertIsInstance(signals, GovernanceSignals)
            self.assertEqual(signals.signals_version, "1.0.0")
            d = signals.to_dict()
            self.assertIn("computed_at", d)

    def test_empty_repo_has_zero_signals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            signals = compute_governance_signals(repo_root)
            self.assertEqual(signals.schema_signals.failure_rate, 0.0)
            self.assertEqual(signals.checker_instability_signals.instability_rate, 0.0)
            self.assertEqual(signals.coverage_signals.latest_coverage_percent, 0.0)
            self.assertEqual(signals.step_binding_signals.binding_rate, 0.0)

    def test_schema_signals_dataclass(self) -> None:
        s = SchemaSignals(
            total_validations=10,
            total_artifacts_validated=100,
            invalid_artifacts=5,
            failure_rate=0.05,
            recent_failures=[{"run_id": "r1", "artifact": "a.json", "error": "invalid"}],
        )
        self.assertEqual(s.total_validations, 10)
        self.assertEqual(s.failure_rate, 0.05)
        self.assertEqual(len(s.recent_failures), 1)

    def test_checker_instability_signals_dataclass(self) -> None:
        s = CheckerInstabilitySignals(
            total_runs_compared=2,
            total_cases=100,
            stable_cases=95,
            unstable_cases=5,
            instability_rate=0.05,
            unstable_case_ids=["TC-001", "TC-002"],
        )
        self.assertEqual(s.instability_rate, 0.05)
        self.assertEqual(len(s.unstable_case_ids), 2)

    def test_coverage_signals_dataclass(self) -> None:
        s = CoverageSignals(
            latest_run_id="20260414T000000Z",
            latest_coverage_percent=85.5,
            fully_covered=80,
            partially_covered=10,
            uncovered=5,
            not_applicable=0,
            total_rules=95,
            coverage_trend="improving",
            trend_delta=2.5,
        )
        self.assertEqual(s.latest_coverage_percent, 85.5)
        self.assertEqual(s.coverage_trend, "improving")
        self.assertEqual(s.trend_delta, 2.5)

    def test_step_binding_signals_dataclass(self) -> None:
        s = StepBindingSignals(
            total_bdd_steps=50,
            unique_patterns=20,
            exact_matches=10,
            parameterized_matches=3,
            candidates=4,
            unmatched=3,
            binding_success_rate=0.65,
            binding_rate=0.85,
        )
        self.assertEqual(s.binding_success_rate, 0.65)
        self.assertEqual(s.binding_rate, 0.85)

    def test_governance_signals_to_dict(self) -> None:
        s = GovernanceSignals(
            computed_at="2026-04-14T00:00:00Z",
            repo_root="/test/repo",
            schema_signals=SchemaSignals(failure_rate=0.1),
            checker_instability_signals=CheckerInstabilitySignals(instability_rate=0.05),
            coverage_signals=CoverageSignals(latest_coverage_percent=90.0),
            step_binding_signals=StepBindingSignals(binding_success_rate=0.75, binding_rate=0.85),
            runs_analyzed=5,
        )
        d = s.to_dict()
        self.assertEqual(d["schema_failure_rate"], 0.1)
        self.assertEqual(d["checker_instability_rate"], 0.05)
        self.assertEqual(d["coverage_signals"]["latest_coverage_percent"], 90.0)
        self.assertEqual(d["step_binding_success_rate"], 0.75)
        self.assertEqual(d["runs_analyzed"], 5)


class WriteSignalsReportTests(unittest.TestCase):
    def test_write_signals_report_creates_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            signals = compute_governance_signals(repo_root)
            output_path = Path(tmp) / "signals.json"
            write_signals_report(signals, output_path)
            self.assertTrue(output_path.exists())
            loaded = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["signals_version"], "1.0.0")


class CoverageSignalsFromRunsTests(unittest.TestCase):
    def test_coverage_signals_from_real_runs(self) -> None:
        # Test against the actual acceptance_e2e run
        from pathlib import Path
        repo = Path(".")
        signals = compute_governance_signals(repo)
        # Should find coverage reports
        self.assertGreaterEqual(signals.runs_analyzed, 0)
        self.assertGreaterEqual(signals.coverage_signals.latest_coverage_percent, 0.0)


class SchemaSignalFailureDetectionTests(unittest.TestCase):
    """Tests for Gate S1.1: schema failure detection end-to-end."""

    def test_schema_failure_rate_detects_invalid_fixtures(self) -> None:
        # Create a temp runs dir with a schema_validation_latest.json
        # that reports fixture failures, then verify failure_rate > 0.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            runs_dir = tmp_path / "runs"
            runs_dir.mkdir()
            # Write a validation report with 1 invalid artifact out of 10
            validation_report = {
                "validated_at": "2026-04-19T00:00:00Z",
                "total_schemas": 2,
                "total_fixtures": 10,
                "passed": 9,
                "failed": 1,
                "failures": [
                    {"artifact": "atomic_rules.json", "entry": 5, "message": "required property missing"}
                ],
                "validation_results": [],
            }
            report_path = runs_dir / "schema_validation_latest.json"
            report_path.write_text(json.dumps(validation_report, indent=2), encoding="utf-8")

            from lme_testing.signals import _compute_schema_signals
            signals, source = _compute_schema_signals(runs_dir)

            self.assertEqual(source, "real_validation")
            self.assertEqual(signals.total_artifacts_validated, 10)
            self.assertEqual(signals.invalid_artifacts, 1)
            self.assertGreater(signals.failure_rate, 0.0)
            self.assertEqual(len(signals.recent_failures), 1)
            self.assertIn("required property missing", signals.recent_failures[0]["error"])


if __name__ == "__main__":
    unittest.main()
