"""Unit tests for scripts/governance_checks.py."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import scripts.governance_checks as gc_module


# -------------------------------------------------------------------------- #
# Helpers
# -------------------------------------------------------------------------- #

def _make_atomic_rules(root: Path, rules: list[dict]) -> None:
    (root / "artifacts").mkdir(parents=True, exist_ok=True)
    (root / "artifacts" / "test_atomic_rules.json").write_text(
        json.dumps(rules, indent=2), encoding="utf-8"
    )


def _make_semantic_rules(root: Path, rules: list[dict]) -> None:
    (root / "artifacts").mkdir(parents=True, exist_ok=True)
    (root / "artifacts" / "test_semantic_rules.json").write_text(
        json.dumps(rules, indent=2), encoding="utf-8"
    )


def _make_metadata(root: Path, data: dict) -> None:
    (root / "artifacts").mkdir(parents=True, exist_ok=True)
    (root / "artifacts" / "metadata.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )


def _make_summary(root: Path, data: dict) -> None:
    (root / "runs").mkdir(parents=True, exist_ok=True)
    (root / "runs" / "summary.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )


# -------------------------------------------------------------------------- #
# Tests for _check_atomic_rules
# -------------------------------------------------------------------------- #

class CheckAtomicRulesTests(unittest.TestCase):
    """Tests for _check_atomic_rules()."""

    def test_valid_rules_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_atomic_rules(root, [
                {"rule_id": "AR-001", "clause_id": "c1", "raw_text": "Some clause text."},
                {"rule_id": "AR-002", "clause_id": "c2", "raw_text": "Another clause."},
            ])
            path = root / "artifacts" / "test_atomic_rules.json"
            with patch.object(gc_module, "REPO_ROOT", root):
                errors = gc_module._check_atomic_rules(path)
        self.assertEqual(errors, [])

    def test_missing_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_atomic_rules(root, [
                {"rule_id": "AR-001"},  # missing clause_id and raw_text
            ])
            path = root / "artifacts" / "test_atomic_rules.json"
            with patch.object(gc_module, "REPO_ROOT", root):
                errors = gc_module._check_atomic_rules(path)
        self.assertTrue(errors)

    def test_empty_raw_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_atomic_rules(root, [
                {"rule_id": "AR-001", "clause_id": "c1", "raw_text": ""},
            ])
            path = root / "artifacts" / "test_atomic_rules.json"
            with patch.object(gc_module, "REPO_ROOT", root):
                errors = gc_module._check_atomic_rules(path)
        self.assertTrue(errors)

    def test_whitespace_raw_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_atomic_rules(root, [
                {"rule_id": "AR-001", "clause_id": "c1", "raw_text": "   \n\t  "},
            ])
            path = root / "artifacts" / "test_atomic_rules.json"
            with patch.object(gc_module, "REPO_ROOT", root):
                errors = gc_module._check_atomic_rules(path)
        self.assertTrue(errors)


# -------------------------------------------------------------------------- #
# Tests for _check_semantic_rules
# -------------------------------------------------------------------------- #

class CheckSemanticRulesTests(unittest.TestCase):
    """Tests for _check_semantic_rules()."""

    def _make_valid_semantic_rule(self) -> dict:
        return {
            "semantic_rule_id": "SR-001",
            "source": {
                "doc_id": "D1",
                "doc_title": "Test Doc",
                "doc_version": "1.0",
                "atomic_rule_ids": ["AR-001"],
                "pages": [1],
            },
            "classification": {
                "rule_type": "obligation",
                "coverage_eligible": True,
            },
            "evidence": [
                {"atomic_rule_id": "AR-001", "page": 1, "quote": "Test quote."},
            ],
        }

    def test_valid_rules_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_semantic_rules(root, [self._make_valid_semantic_rule()])
            path = root / "artifacts" / "test_semantic_rules.json"
            with patch.object(gc_module, "REPO_ROOT", root):
                errors = gc_module._check_semantic_rules(path)
        self.assertEqual(errors, [])

    def test_invalid_rule_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rule = self._make_valid_semantic_rule()
            rule["classification"]["rule_type"] = "not_a_valid_type"
            _make_semantic_rules(root, [rule])
            path = root / "artifacts" / "test_semantic_rules.json"
            with patch.object(gc_module, "REPO_ROOT", root):
                errors = gc_module._check_semantic_rules(path)
        self.assertTrue(errors)
        self.assertTrue(any("invalid classification.rule_type" in e for e in errors))

    def test_empty_atomic_rule_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rule = self._make_valid_semantic_rule()
            rule["source"]["atomic_rule_ids"] = []
            _make_semantic_rules(root, [rule])
            path = root / "artifacts" / "test_semantic_rules.json"
            with patch.object(gc_module, "REPO_ROOT", root):
                errors = gc_module._check_semantic_rules(path)
        self.assertTrue(errors)
        self.assertTrue(any("empty source.atomic_rule_ids" in e for e in errors))

    def test_empty_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rule = self._make_valid_semantic_rule()
            rule["evidence"] = []
            _make_semantic_rules(root, [rule])
            path = root / "artifacts" / "test_semantic_rules.json"
            with patch.object(gc_module, "REPO_ROOT", root):
                errors = gc_module._check_semantic_rules(path)
        self.assertTrue(errors)


# -------------------------------------------------------------------------- #
# Tests for _check_metadata_artifact
# -------------------------------------------------------------------------- #

class CheckMetadataArtifactTests(unittest.TestCase):
    """Tests for _check_metadata_artifact()."""

    def test_valid_metadata_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_metadata(root, {
                "doc_id": "D1",
                "doc_title": "Test",
                "doc_version": "1.0",
            })
            path = root / "artifacts" / "metadata.json"
            with patch.object(gc_module, "REPO_ROOT", root):
                errors = gc_module._check_metadata_artifact(path)
        self.assertEqual(errors, [])

    def test_missing_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_metadata(root, {"doc_id": "D1"})  # missing doc_title and doc_version
            path = root / "artifacts" / "metadata.json"
            with patch.object(gc_module, "REPO_ROOT", root):
                errors = gc_module._check_metadata_artifact(path)
        self.assertTrue(errors)
        self.assertTrue(any("missing required keys" in e for e in errors))


# -------------------------------------------------------------------------- #
# Tests for check_artifact_metadata_in_runs
# -------------------------------------------------------------------------- #

class CheckArtifactMetadataInRunsTests(unittest.TestCase):
    """Tests for check_artifact_metadata_in_runs()."""

    REQUIRED = {"run_id", "role", "pipeline_version", "prompt_version", "provider", "model"}

    def test_passes_with_valid_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary = {
                "run_id": "20260418T000000+0800",
                "role": "maker",
                "pipeline_version": "2.0",
                "prompt_version": "1.0",
                "provider": "stub",
                "model": "stub-model",
            }
            # Use a date-based dir name >= PHASE1_COMPLETION_DATE
            run_dir = root / "runs" / "20260418T000000+0800"
            run_dir.mkdir(parents=True)
            (run_dir / "summary.json").write_text(
                json.dumps(summary), encoding="utf-8"
            )
            with patch.object(gc_module, "REPO_ROOT", root):
                errors = gc_module.check_artifact_metadata_in_runs(root)
        self.assertEqual(errors, [])

    def test_skips_pre_phase1_runs(self) -> None:
        # Runs before PHASE1_COMPLETION_DATE (20260413) should be skipped
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Empty or malformed summary — but should be skipped
            run_dir = root / "runs" / "20260410T000000+0800"
            run_dir.mkdir(parents=True)
            (run_dir / "summary.json").write_text(
                json.dumps({"run_id": "old-run"}), encoding="utf-8"
            )
            with patch.object(gc_module, "REPO_ROOT", root):
                errors = gc_module.check_artifact_metadata_in_runs(root)
        # Should have no errors since pre-Phase1 runs are skipped
        self.assertEqual(errors, [])


# -------------------------------------------------------------------------- #
# Tests for check_model_governance
# -------------------------------------------------------------------------- #

class CheckModelGovernanceTests(unittest.TestCase):
    """Tests for check_model_governance()."""

    REQUIRED = {"run_id", "role", "pipeline_version", "prompt_version", "provider", "model"}

    def test_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            summary = {
                "run_id": "20260418T000000+0800",
                "role": "maker",
                "pipeline_version": "2.0",
                "prompt_version": "1.0",
                "provider": "stub",
                "model": "stub-model",
            }
            run_dir = root / "runs" / "20260418T000000+0800"
            run_dir.mkdir(parents=True)
            (run_dir / "summary.json").write_text(
                json.dumps(summary), encoding="utf-8"
            )
            with patch.object(gc_module, "REPO_ROOT", root):
                errors = gc_module.check_model_governance(root)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
