"""Unit tests for the deterministic oracle framework (Phase 3 Gate 3)."""
from __future__ import annotations

import unittest

from lme_testing.oracles import (
    list_oracles,
    evaluate_assertion,
    get_oracle,
    OracleResult,
)


class OracleRegistryTests(unittest.TestCase):
    def test_all_eight_oracles_registered(self) -> None:
        oracles = list_oracles()
        expected = {
            "calculation_validation",
            "compliance_check",
            "deadline_check",
            "event_sequence",
            "field_validation",
            "null_check",
            "pass_fail_accounting",
            "state_validation",
        }
        self.assertEqual(set(oracles), expected)

    def test_get_oracle_returns_class(self) -> None:
        for atype in list_oracles():
            cls = get_oracle(atype)
            self.assertIsNotNone(cls, f"No oracle for {atype}")


class NullCheckOracleTests(unittest.TestCase):
    def test_non_null_passes_when_value_present(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "nc-1",
                "type": "null_check",
                "parameters": {"field": "processing_result", "expected": "non_null"},
            },
            {"input_data": {"processing_result": "success"}},
            None,
            {},
        )
        self.assertEqual(result.status, "pass")
        self.assertEqual(result.outcome, "non_null")

    def test_non_null_fails_when_value_is_none(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "nc-2",
                "type": "null_check",
                "parameters": {"field": "processing_result", "expected": "non_null"},
            },
            {"input_data": {"processing_result": None}},
            None,
            {},
        )
        self.assertEqual(result.status, "fail")
        self.assertEqual(result.outcome, "non_null")

    def test_null_passes_when_value_is_none(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "nc-3",
                "type": "null_check",
                "parameters": {"field": "error_message", "expected": "null"},
            },
            {"input_data": {"error_message": None}},
            None,
            {},
        )
        self.assertEqual(result.status, "pass")
        self.assertEqual(result.outcome, "null")

    def test_null_fails_when_value_is_present(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "nc-4",
                "type": "null_check",
                "parameters": {"field": "error_message", "expected": "null"},
            },
            {"input_data": {"error_message": "some error"}},
            None,
            {},
        )
        self.assertEqual(result.status, "fail")

    def test_missing_field_returns_error(self) -> None:
        result = evaluate_assertion(
            {"assertion_id": "nc-5", "type": "null_check", "parameters": {}},
            {"input_data": {}},
            None,
            {},
        )
        self.assertEqual(result.status, "error")


class FieldValidationOracleTests(unittest.TestCase):
    def test_string_type_check_passes(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "fv-1",
                "type": "field_validation",
                "parameters": {"field": "member_name", "expected_type": "string"},
            },
            {"input_data": {"member_name": "ABC Corp"}},
            None,
            {},
        )
        self.assertEqual(result.status, "pass")

    def test_string_type_check_fails_on_int(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "fv-2",
                "type": "field_validation",
                "parameters": {"field": "member_name", "expected_type": "string"},
            },
            {"input_data": {"member_name": 123}},
            None,
            {},
        )
        self.assertEqual(result.status, "fail")

    def test_min_value_check(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "fv-3",
                "type": "field_validation",
                "parameters": {"field": "price", "min_value": 10},
            },
            {"input_data": {"price": 5}},
            None,
            {},
        )
        self.assertEqual(result.status, "fail")

    def test_max_value_check(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "fv-4",
                "type": "field_validation",
                "parameters": {"field": "price", "max_value": 100},
            },
            {"input_data": {"price": 200}},
            None,
            {},
        )
        self.assertEqual(result.status, "fail")

    def test_enum_check(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "fv-5",
                "type": "field_validation",
                "parameters": {"field": "status", "enum": ["active", "suspended"]},
            },
            {"input_data": {"status": "active"}},
            None,
            {},
        )
        self.assertEqual(result.status, "pass")

    def test_enum_check_fails(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "fv-6",
                "type": "field_validation",
                "parameters": {"field": "status", "enum": ["active", "suspended"]},
            },
            {"input_data": {"status": "deleted"}},
            None,
            {},
        )
        self.assertEqual(result.status, "fail")

    def test_pattern_check(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "fv-7",
                "type": "field_validation",
                "parameters": {"field": "member_id", "pattern": r"^M-\d{3}$"},
            },
            {"input_data": {"member_id": "M-001"}},
            None,
            {},
        )
        self.assertEqual(result.status, "pass")

    def test_pattern_check_fails(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "fv-8",
                "type": "field_validation",
                "parameters": {"field": "member_id", "pattern": r"^M-\d{3}$"},
            },
            {"input_data": {"member_id": "INVALID"}},
            None,
            {},
        )
        self.assertEqual(result.status, "fail")

    def test_format_uuid(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "fv-9",
                "type": "field_validation",
                "parameters": {"field": "transaction_id", "expected_format": "uuid"},
            },
            {"input_data": {"transaction_id": "550e8400-e29b-41d4-a716-446655440000"}},
            None,
            {},
        )
        self.assertEqual(result.status, "pass")

    def test_format_uuid_fails(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "fv-10",
                "type": "field_validation",
                "parameters": {"field": "transaction_id", "expected_format": "uuid"},
            },
            {"input_data": {"transaction_id": "not-a-uuid"}},
            None,
            {},
        )
        self.assertEqual(result.status, "fail")


class StateValidationOracleTests(unittest.TestCase):
    def test_expected_state_match_passes(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "sv-1",
                "type": "state_validation",
                "parameters": {"current_state": "compliance_status", "expected_state": "compliant"},
            },
            {"input_data": {"compliance_status": "compliant"}},
            None,
            {},
        )
        self.assertEqual(result.status, "pass")

    def test_expected_state_mismatch_fails(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "sv-2",
                "type": "state_validation",
                "parameters": {"current_state": "compliance_status", "expected_state": "compliant"},
            },
            {"input_data": {"compliance_status": "non_compliant"}},
            None,
            {},
        )
        self.assertEqual(result.status, "fail")

    def test_forbidden_states(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "sv-3",
                "type": "state_validation",
                "parameters": {"current_state": "account_status", "forbidden_states": ["suspended", "terminated"]},
            },
            {"input_data": {"account_status": "active"}},
            None,
            {},
        )
        self.assertEqual(result.status, "pass")

    def test_forbidden_states_fails(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "sv-4",
                "type": "state_validation",
                "parameters": {"current_state": "account_status", "forbidden_states": ["suspended", "terminated"]},
            },
            {"input_data": {"account_status": "suspended"}},
            None,
            {},
        )
        self.assertEqual(result.status, "fail")

    def test_allowed_states(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "sv-5",
                "type": "state_validation",
                "parameters": {"current_state": "account_status", "allowed_states": ["active", "suspended"]},
            },
            {"input_data": {"account_status": "active"}},
            None,
            {},
        )
        self.assertEqual(result.status, "pass")

    def test_missing_state_returns_undetermined(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "sv-6",
                "type": "state_validation",
                "parameters": {"current_state": "nonexistent_field", "expected_state": "active"},
            },
            {"input_data": {}},
            None,
            {},
        )
        self.assertEqual(result.status, "unable_to_determine")


class DeadlineCheckOracleTests(unittest.TestCase):
    def test_before_deadline_passes(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "dc-1",
                "type": "deadline_check",
                "parameters": {
                    "submission_time": "submission_ts",
                    "deadline": "2026-04-14T12:00:00Z",
                    "operator": "before",
                },
            },
            {"input_data": {"submission_ts": "2026-04-14T11:30:00Z"}},
            None,
            {},
        )
        self.assertEqual(result.status, "pass", result.message)
        self.assertEqual(result.outcome, "deadline_met")

    def test_after_deadline_fails(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "dc-2",
                "type": "deadline_check",
                "parameters": {
                    "submission_time": "submission_ts",
                    "deadline": "2026-04-14T12:00:00Z",
                    "operator": "before",
                },
            },
            {"input_data": {"submission_ts": "2026-04-14T13:00:00Z"}},
            None,
            {},
        )
        self.assertEqual(result.status, "fail", result.message)
        self.assertEqual(result.outcome, "deadline_missed")

    def test_within_tolerance_passes(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "dc-3",
                "type": "deadline_check",
                "parameters": {
                    "submission_time": "submission_ts",
                    "deadline": "2026-04-14T12:00:00Z",
                    "tolerance_minutes": 5,
                    "operator": "before",
                },
            },
            {"input_data": {"submission_ts": "2026-04-14T12:04:00Z"}},
            None,
            {},
        )
        self.assertEqual(result.status, "pass", result.message)


class PassFailAccountingOracleTests(unittest.TestCase):
    def test_pass_result_matches_expected(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "pfa-1",
                "type": "pass_fail_accounting",
                "parameters": {"result_field": "test_result", "expected_outcome": "pass"},
            },
            {"input_data": {"test_result": "pass"}},
            None,
            {},
        )
        self.assertEqual(result.status, "pass")

    def test_pass_result_mismatches_expected(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "pfa-2",
                "type": "pass_fail_accounting",
                "parameters": {"result_field": "test_result", "expected_outcome": "pass"},
            },
            {"input_data": {"test_result": "fail"}},
            None,
            {},
        )
        self.assertEqual(result.status, "fail")

    def test_min_passes_check(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "pfa-3",
                "type": "pass_fail_accounting",
                "parameters": {"pass_count_field": "passed_count", "min_passes": 5},
            },
            {"input_data": {"passed_count": 3}},
            None,
            {},
        )
        self.assertEqual(result.status, "fail")

    def test_max_fails_check(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "pfa-4",
                "type": "pass_fail_accounting",
                "parameters": {"fail_count_field": "failed_count", "max_fails": 2},
            },
            {"input_data": {"failed_count": 5}},
            None,
            {},
        )
        self.assertEqual(result.status, "fail")


class CalculationValidationOracleTests(unittest.TestCase):
    def test_result_equals_expected(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "cv-1",
                "type": "calculation_validation",
                "parameters": {"result_field": "total", "expected": 150},
            },
            {"input_data": {"total": 150}},
            None,
            {},
        )
        self.assertEqual(result.status, "pass")

    def test_result_differs_from_expected(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "cv-2",
                "type": "calculation_validation",
                "parameters": {"result_field": "total", "expected": 150},
            },
            {"input_data": {"total": 100}},
            None,
            {},
        )
        self.assertEqual(result.status, "fail")

    def test_within_tolerance(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "cv-3",
                "type": "calculation_validation",
                "parameters": {"result_field": "total", "expected": 100, "tolerance": 5},
            },
            {"input_data": {"total": 103}},
            None,
            {},
        )
        self.assertEqual(result.status, "pass")

    def test_formula_evaluation(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "cv-4",
                "type": "calculation_validation",
                "parameters": {"result_field": "total", "expected_formula": "{subtotal} + {tax}"},
            },
            {"input_data": {"subtotal": 100, "tax": 20, "total": 120}},
            None,
            {},
        )
        self.assertEqual(result.status, "pass")


class EventSequenceOracleTests(unittest.TestCase):
    def test_events_in_correct_order(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "es-1",
                "type": "event_sequence",
                "parameters": {
                    "events": [
                        {"name": "submit", "timestamp_field": "submit_ts", "order_rank": 1},
                        {"name": "process", "timestamp_field": "process_ts", "order_rank": 2},
                        {"name": "complete", "timestamp_field": "complete_ts", "order_rank": 3},
                    ],
                    "strict_order": True,
                },
            },
            {
                "input_data": {
                    "submit_ts": "2026-04-14T10:00:00Z",
                    "process_ts": "2026-04-14T10:01:00Z",
                    "complete_ts": "2026-04-14T10:02:00Z",
                }
            },
            None,
            {},
        )
        self.assertEqual(result.status, "pass")

    def test_events_out_of_order_fails(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "es-2",
                "type": "event_sequence",
                "parameters": {
                    "events": [
                        {"name": "submit", "timestamp_field": "submit_ts", "order_rank": 1},
                        {"name": "process", "timestamp_field": "process_ts", "order_rank": 2},
                    ],
                    "strict_order": True,
                },
            },
            {
                "input_data": {
                    "submit_ts": "2026-04-14T10:02:00Z",
                    "process_ts": "2026-04-14T10:01:00Z",
                }
            },
            None,
            {},
        )
        self.assertEqual(result.status, "fail")


class ComplianceCheckOracleTests(unittest.TestCase):
    def test_obligations_positive_case_must_be_fulfilled(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "cc-1",
                "type": "compliance_check",
                "parameters": {
                    "rule_type": "obligation",
                    "expected_compliance_status": "fulfilled",
                    "outcome_field": "obligation_status",
                },
            },
            {"case_type": "positive", "input_data": {"obligation_status": "fulfilled"}},
            {"classification": {"rule_type": "obligation"}},
            {},
        )
        self.assertEqual(result.status, "pass")

    def test_obligations_negative_case_must_not_be_fulfilled(self) -> None:
        result = evaluate_assertion(
            {
                "assertion_id": "cc-2",
                "type": "compliance_check",
                "parameters": {
                    "rule_type": "obligation",
                    "expected_compliance_status": "violated",
                    "outcome_field": "obligation_status",
                },
            },
            {"case_type": "negative", "input_data": {"obligation_status": "violated"}},
            {"classification": {"rule_type": "obligation"}},
            {},
        )
        # Negative obligation: violation (not fulfilled) is the expected/correct outcome -> pass
        self.assertEqual(result.status, "pass")


if __name__ == "__main__":
    unittest.main()
