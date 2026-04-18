"""Unit tests for schema validation of governed artifacts."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from schemas import (
    validate_atomic_rule,
    validate_semantic_rule,
    validate_maker_output,
    validate_checker_output,
    validate_executable_scenario,
)


def _fixture_path(name: str) -> Path:
    return Path(__file__).parent.parent / "schemas" / "fixtures" / name


class ExecutableScenarioSchemaTests(unittest.TestCase):
    """Tests for the executable_scenario schema (Phase 3 Gate 2)."""

    def test_valid_executable_scenario_passes(self) -> None:
        path = _fixture_path("executable_scenario_valid.json")
        with open(path, encoding="utf-8") as f:
            artifacts = json.load(f)
        for artifact in artifacts:
            errors = validate_executable_scenario(artifact)
            self.assertEqual(errors, [], f"Valid artifact failed: {errors}")

    def test_invalid_executable_scenario_missing_required_fields(self) -> None:
        path = _fixture_path("executable_scenario_invalid.json")
        with open(path, encoding="utf-8") as f:
            artifacts = json.load(f)
        for artifact in artifacts:
            errors = validate_executable_scenario(artifact)
            self.assertGreater(len(errors), 0, "Invalid artifact should have failed validation")

    def test_executable_scenario_requires_scenario_id(self) -> None:
        artifact = {
            "executable_scenario_id": "ES-TEST-001",
            "semantic_rule_ref": "SR-TEST-001",
            "case_type": "positive",
            "environment": {"target": "test"},
            "input_data": {},
            "step_bindings": [],
        }
        errors = validate_executable_scenario(artifact)
        self.assertTrue(any("scenario_id" in e for e in errors))

    def test_executable_scenario_requires_semantic_rule_ref(self) -> None:
        artifact = {
            "executable_scenario_id": "ES-TEST-001",
            "scenario_id": "TC-TEST-001",
            "case_type": "positive",
            "environment": {"target": "test"},
            "input_data": {},
            "step_bindings": [],
        }
        errors = validate_executable_scenario(artifact)
        self.assertTrue(any("semantic_rule_ref" in e for e in errors))

    def test_executable_scenario_requires_environment(self) -> None:
        artifact = {
            "executable_scenario_id": "ES-TEST-001",
            "semantic_rule_ref": "SR-TEST-001",
            "scenario_id": "TC-TEST-001",
            "case_type": "positive",
            "input_data": {},
            "step_bindings": [],
        }
        errors = validate_executable_scenario(artifact)
        self.assertTrue(any("environment" in e for e in errors))

    def test_executable_scenario_requires_input_data(self) -> None:
        artifact = {
            "executable_scenario_id": "ES-TEST-001",
            "semantic_rule_ref": "SR-TEST-001",
            "scenario_id": "TC-TEST-001",
            "case_type": "positive",
            "environment": {"target": "test"},
            "step_bindings": [],
        }
        errors = validate_executable_scenario(artifact)
        self.assertTrue(any("input_data" in e for e in errors))

    def test_executable_scenario_requires_step_bindings(self) -> None:
        artifact = {
            "executable_scenario_id": "ES-TEST-001",
            "semantic_rule_ref": "SR-TEST-001",
            "scenario_id": "TC-TEST-001",
            "case_type": "positive",
            "environment": {"target": "test"},
            "input_data": {},
        }
        errors = validate_executable_scenario(artifact)
        self.assertTrue(any("step_bindings" in e for e in errors))

    def test_executable_scenario_case_type_enum(self) -> None:
        artifact = {
            "executable_scenario_id": "ES-TEST-001",
            "semantic_rule_ref": "SR-TEST-001",
            "scenario_id": "TC-TEST-001",
            "case_type": "invalid_case_type",
            "environment": {"target": "test"},
            "input_data": {},
            "step_bindings": [],
        }
        errors = validate_executable_scenario(artifact)
        self.assertTrue(any("case_type" in e for e in errors))

    def test_executable_scenario_binding_status_enum(self) -> None:
        artifact = {
            "executable_scenario_id": "ES-TEST-001",
            "semantic_rule_ref": "SR-TEST-001",
            "scenario_id": "TC-TEST-001",
            "case_type": "positive",
            "environment": {"target": "test"},
            "input_data": {},
            "step_bindings": [
                {
                    "step_type": "given",
                    "step_text": "test step",
                    "step_pattern": "test step",
                    "binding_status": "invalid_status",
                }
            ],
        }
        errors = validate_executable_scenario(artifact)
        self.assertTrue(any("binding_status" in e for e in errors))

    def test_executable_scenario_assertion_type_enum(self) -> None:
        artifact = {
            "executable_scenario_id": "ES-TEST-001",
            "semantic_rule_ref": "SR-TEST-001",
            "scenario_id": "TC-TEST-001",
            "case_type": "positive",
            "environment": {"target": "test"},
            "input_data": {},
            "step_bindings": [],
            "assertions": [
                {
                    "assertion_id": "assert-001",
                    "type": "invalid_type",
                    "description": "test",
                }
            ],
        }
        errors = validate_executable_scenario(artifact)
        self.assertTrue(any("assertions" in e or "type" in e for e in errors))

    def test_executable_scenario_id_pattern(self) -> None:
        artifact = {
            "executable_scenario_id": "INVALID-NO-PREFIX",
            "semantic_rule_ref": "SR-TEST-001",
            "scenario_id": "TC-TEST-001",
            "case_type": "positive",
            "environment": {"target": "test"},
            "input_data": {},
            "step_bindings": [],
        }
        errors = validate_executable_scenario(artifact)
        self.assertTrue(any("executable_scenario_id" in e for e in errors))

    def test_executable_scenario_scenario_id_pattern(self) -> None:
        artifact = {
            "executable_scenario_id": "ES-TEST-001",
            "semantic_rule_ref": "SR-TEST-001",
            "scenario_id": "INVALID-NO-TC-PREFIX",
            "case_type": "positive",
            "environment": {"target": "test"},
            "input_data": {},
            "step_bindings": [],
        }
        errors = validate_executable_scenario(artifact)
        self.assertTrue(any("scenario_id" in e for e in errors))


class AtomicRuleSchemaTests(unittest.TestCase):
    def test_valid_atomic_rule_passes(self) -> None:
        path = _fixture_path("atomic_rule_valid.json")
        with open(path, encoding="utf-8") as f:
            artifacts = json.load(f)
        for artifact in artifacts:
            errors = validate_atomic_rule(artifact)
            self.assertEqual(errors, [], f"Valid artifact failed: {errors}")

    def test_invalid_atomic_rule_fails(self) -> None:
        path = _fixture_path("atomic_rule_invalid.json")
        with open(path, encoding="utf-8") as f:
            artifacts = json.load(f)
        for artifact in artifacts:
            errors = validate_atomic_rule(artifact)
            self.assertGreater(len(errors), 0)

    def test_atomic_rule_rule_id_pattern_violation(self) -> None:
        """rule_id with spaces must fail schema validation."""
        artifact = {
            "rule_id": "MR 001-01",
            "clause_id": "MR-001",
            "raw_text": "Some rule text",
        }
        errors = validate_atomic_rule(artifact)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("rule_id" in e for e in errors))

    def test_atomic_rule_start_page_string_type(self) -> None:
        """start_page as string must fail integer type check."""
        artifact = {
            "rule_id": "MR-001-01",
            "clause_id": "MR-001",
            "start_page": "2",
            "end_page": 2,
            "raw_text": "Some rule text",
        }
        errors = validate_atomic_rule(artifact)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("start_page" in e for e in errors))


class SemanticRuleSchemaTests(unittest.TestCase):
    def test_valid_semantic_rule_passes(self) -> None:
        path = _fixture_path("semantic_rule_valid.json")
        with open(path, encoding="utf-8") as f:
            artifacts = json.load(f)
        for artifact in artifacts:
            errors = validate_semantic_rule(artifact)
            self.assertEqual(errors, [], f"Valid artifact failed: {errors}")

    def test_invalid_semantic_rule_fails(self) -> None:
        path = _fixture_path("semantic_rule_invalid.json")
        with open(path, encoding="utf-8") as f:
            artifacts = json.load(f)
        for artifact in artifacts:
            errors = validate_semantic_rule(artifact)
            self.assertGreater(len(errors), 0)

    def test_semantic_rule_atomic_rule_ids_empty(self) -> None:
        """atomic_rule_ids must have at least 1 item (minItems: 1)."""
        artifact = {
            "semantic_rule_id": "SR-MR-001-01",
            "source": {
                "doc_id": "lme_matching_rules_v2_2",
                "doc_title": "LME Matching Rules",
                "doc_version": "2.2",
                "atomic_rule_ids": [],
                "pages": [2],
            },
            "classification": {"rule_type": "obligation", "coverage_eligible": True},
            "evidence": [{"quote": "q", "page": 2, "atomic_rule_id": "MR-001-01"}],
        }
        errors = validate_semantic_rule(artifact)
        self.assertGreater(len(errors), 0)

    def test_semantic_rule_priority_invalid_enum(self) -> None:
        """priority must be high/medium/low."""
        artifact = {
            "semantic_rule_id": "SR-MR-001-01",
            "source": {
                "doc_id": "lme_matching_rules_v2_2",
                "doc_title": "LME Matching Rules",
                "doc_version": "2.2",
                "atomic_rule_ids": ["MR-001-01"],
                "pages": [2],
            },
            "classification": {"rule_type": "obligation", "priority": "critical", "coverage_eligible": True},
            "evidence": [{"quote": "q", "page": 2, "atomic_rule_id": "MR-001-01"}],
        }
        errors = validate_semantic_rule(artifact)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("priority" in e for e in errors))

    def test_semantic_rule_evidence_quote_empty(self) -> None:
        """evidence quote must be non-empty (minLength: 1)."""
        artifact = {
            "semantic_rule_id": "SR-MR-001-01",
            "source": {
                "doc_id": "lme_matching_rules_v2_2",
                "doc_title": "LME Matching Rules",
                "doc_version": "2.2",
                "atomic_rule_ids": ["MR-001-01"],
                "pages": [2],
            },
            "classification": {"rule_type": "obligation", "coverage_eligible": True},
            "evidence": [{"quote": "", "page": 2, "atomic_rule_id": "MR-001-01"}],
        }
        errors = validate_semantic_rule(artifact)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("quote" in e.lower() for e in errors))


class MakerOutputSchemaTests(unittest.TestCase):
    def test_valid_maker_output_passes(self) -> None:
        path = _fixture_path("maker_output_valid.json")
        with open(path, encoding="utf-8") as f:
            artifacts = json.load(f)
        for artifact in artifacts:
            errors = validate_maker_output(artifact)
            self.assertEqual(errors, [], f"Valid artifact failed: {errors}")

    def test_invalid_maker_output_fails(self) -> None:
        path = _fixture_path("maker_output_invalid.json")
        with open(path, encoding="utf-8") as f:
            artifacts = json.load(f)
        for artifact in artifacts:
            errors = validate_maker_output(artifact)
            self.assertGreater(len(errors), 0)


class CheckerOutputSchemaTests(unittest.TestCase):
    def test_valid_checker_output_passes(self) -> None:
        path = _fixture_path("checker_output_valid.json")
        with open(path, encoding="utf-8") as f:
            artifacts = json.load(f)
        for artifact in artifacts:
            errors = validate_checker_output(artifact)
            self.assertEqual(errors, [], f"Valid artifact failed: {errors}")

    def test_invalid_checker_output_fails(self) -> None:
        path = _fixture_path("checker_output_invalid.json")
        with open(path, encoding="utf-8") as f:
            artifacts = json.load(f)
        for artifact in artifacts:
            errors = validate_checker_output(artifact)
            self.assertGreater(len(errors), 0)


if __name__ == "__main__":
    unittest.main()
