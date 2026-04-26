from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lme_testing.config import ProjectConfig, ProviderConfig, RoleDefaults
from lme_testing.pipelines import analyze_maker_input_quality, run_bdd_pipeline, run_checker_pipeline, run_maker_pipeline


class FakeProvider:
    def __init__(self, responses: list[str]):
        self.responses = responses
        self.index = 0

    def generate(self, system_prompt: str, user_prompt: str):
        payload = json.loads(self.responses[self.index])
        self.index += 1
        return type(
            "Response",
            (),
            {"content": json.dumps(payload, ensure_ascii=False), "raw_response": payload},
        )()


def make_config() -> ProjectConfig:
    provider = ProviderConfig(
        name="shared",
        provider_type="openai_compatible",
        model="demo-model",
        base_url="https://example.com/v1",
        api_key="secret",
    )
    return ProjectConfig(
        providers={"shared": provider},
        roles={"maker": "shared", "checker": "shared"},
        output_root=Path("runs"),
        maker_defaults=RoleDefaults(),
        checker_defaults=RoleDefaults(),
    )


class PipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.work_tmp = Path(self.tmpdir.name)

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def test_maker_pipeline_persists_records(self) -> None:
        semantic_rules = [
            {
                "semantic_rule_id": "SR-MR-001-01",
                "source": {"atomic_rule_ids": ["MR-001-01"]},
                "evidence": [{"atomic_rule_id": "MR-001-01", "page": 1, "quote": "q"}],
            }
        ]
        maker_response = json.dumps(
            {
                "results": [
                    {
                        "semantic_rule_id": "SR-MR-001-01",
                        "requirement_ids": ["MR-001-01"],
                        "feature": "Feature A",
                        "scenarios": [
                            {
                                "scenario_id": "TC-1",
                                "title": "Case 1",
                                "intent": "test",
                                "priority": "high",
                                "case_type": "positive",
                                "given": ["g"],
                                "when": ["w"],
                                "then": ["t"],
                                "assumptions": [],
                                "evidence": [
                                    {
                                        "atomic_rule_id": "MR-001-01",
                                        "page": 1,
                                        "quote": "q"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        )
        rules_path = self.work_tmp / "semantic_rules.json"
        output_dir = self.work_tmp / "maker"
        rules_path.write_text(json.dumps(semantic_rules), encoding="utf-8")
        with patch(
            "lme_testing.pipelines.build_provider",
            return_value=FakeProvider([maker_response]),
        ):
            summary = run_maker_pipeline(
                config=make_config(),
                semantic_rules_path=rules_path,
                output_dir=output_dir,
                limit=None,
                batch_size=1,
                resume_from=None,
            )
        self.assertEqual(summary["processed_rule_count"], 1)
        self.assertEqual(summary["excluded_rule_count"], 0)
        self.assertEqual(summary["scenario_count"], 1)
        self.assertTrue(Path(summary["results_path"]).exists())
        self.assertTrue(Path(summary["quality_report_path"]).exists())

    def test_maker_pipeline_excludes_reference_only_rules(self) -> None:
        semantic_rules = [
            {
                "semantic_rule_id": "SR-MR-001-01",
                "source": {"atomic_rule_ids": ["MR-001-01"]},
                "classification": {
                    "rule_type": "reference_only",
                    "testability": "non_testable",
                    "coverage_eligible": False,
                },
                "evidence": [{"atomic_rule_id": "MR-001-01", "page": 1, "quote": "toc"}],
            },
            {
                "semantic_rule_id": "SR-MR-002-01",
                "source": {"atomic_rule_ids": ["MR-002-01"]},
                "classification": {
                    "rule_type": "permission",
                    "testability": "testable",
                    "coverage_eligible": True,
                },
                "evidence": [{"atomic_rule_id": "MR-002-01", "page": 2, "quote": "may use"}],
            },
        ]
        maker_response = json.dumps(
            {
                "results": [
                    {
                        "semantic_rule_id": "SR-MR-002-01",
                        "requirement_ids": ["MR-002-01"],
                        "feature": "Feature B",
                        "scenarios": [
                            {
                                "scenario_id": "TC-2",
                                "title": "Case 2",
                                "intent": "test",
                                "priority": "high",
                                "case_type": "positive",
                                "given": ["g"],
                                "when": ["w"],
                                "then": ["t"],
                                "assumptions": [],
                                "evidence": [
                                    {
                                        "atomic_rule_id": "MR-002-01",
                                        "page": 2,
                                        "quote": "may use"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        )
        rules_path = self.work_tmp / "semantic_rules.json"
        output_dir = self.work_tmp / "maker"
        rules_path.write_text(json.dumps(semantic_rules), encoding="utf-8")
        with patch(
            "lme_testing.pipelines.build_provider",
            return_value=FakeProvider([maker_response]),
        ):
            summary = run_maker_pipeline(
                config=make_config(),
                semantic_rules_path=rules_path,
                output_dir=output_dir,
                limit=None,
                batch_size=1,
                resume_from=None,
            )
        self.assertEqual(summary["input_rule_count"], 2)
        self.assertEqual(summary["processed_rule_count"], 1)
        self.assertEqual(summary["excluded_rule_count"], 1)
        quality = json.loads(Path(summary["quality_report_path"]).read_text(encoding="utf-8"))
        self.assertEqual(quality["maker_testable_count"], 1)
        self.assertEqual(quality["reference_only_count"], 1)

    def test_analyze_maker_input_quality_counts_reference_only_ratio(self) -> None:
        report = analyze_maker_input_quality([
            {
                "semantic_rule_id": "SR-1",
                "classification": {"rule_type": "reference_only", "coverage_eligible": False},
            },
            {
                "semantic_rule_id": "SR-2",
                "classification": {"rule_type": "calculation", "coverage_eligible": True},
            },
        ])
        self.assertEqual(report["total_rules"], 2)
        self.assertEqual(report["maker_testable_count"], 1)
        self.assertEqual(report["reference_only_ratio"], 0.5)

    def test_checker_pipeline_generates_coverage(self) -> None:
        semantic_rules = [
            {
                "semantic_rule_id": "SR-MR-001-01",
                "classification": {"rule_type": "permission", "coverage_eligible": True},
            },
            {
                "semantic_rule_id": "SR-MR-002-01",
                "classification": {"rule_type": "permission", "coverage_eligible": True},
            },
        ]
        maker_record = {
            "run_id": "r1",
            "semantic_rule_id": "SR-MR-001-01",
            "feature": "Feature A",
            "scenarios": [
                {
                    "scenario_id": "TC-1",
                    "case_type": "positive",
                    "given": [],
                    "when": [],
                    "then": [],
                    "assumptions": [],
                }
            ]
        }
        checker_response = json.dumps(
            {
                "results": [
                    {
                        "case_id": "TC-1",
                        "semantic_rule_id": "SR-MR-001-01",
                        "overall_status": "pass",
                        "scores": {
                            "evidence_consistency": 5,
                            "requirement_coverage": 4,
                            "test_design_quality": 4,
                            "non_hallucination": 5
                        },
                        "case_type": "positive",
                        "case_type_accepted": True,
                        "coverage_relevance": "direct",
                        "blocking_findings_count": 0,
                        "is_blocking": False,
                        "findings": [],
                        "coverage_assessment": {"status": "covered", "reason": "ok", "missing_aspects": []}
                    }
                ]
            }
        )
        rules_path = self.work_tmp / "semantic_rules.json"
        cases_path = self.work_tmp / "cases.jsonl"
        output_dir = self.work_tmp / "checker"
        rules_path.write_text(json.dumps(semantic_rules), encoding="utf-8")
        cases_path.write_text(json.dumps(maker_record) + "\n", encoding="utf-8")
        with patch(
            "lme_testing.pipelines.build_provider",
            return_value=FakeProvider([checker_response]),
        ):
            summary = run_checker_pipeline(
                config=make_config(),
                semantic_rules_path=rules_path,
                maker_cases_path=cases_path,
                output_dir=output_dir,
                limit=None,
                batch_size=1,
                resume_from=None,
            )
        coverage = json.loads(Path(summary["coverage_report_path"]).read_text(encoding="utf-8"))
        self.assertEqual(coverage["fully_covered"], 1)
        self.assertEqual(coverage["uncovered"], 1)

    def test_bdd_pipeline_reports_processed_rules_not_batches(self) -> None:
        maker_records = [
            {
                "run_id": "r1",
                "semantic_rule_id": "SR-MR-001-01",
                "feature": "Feature A",
                "scenarios": [{"scenario_id": "TC-1", "case_type": "positive"}],
            },
            {
                "run_id": "r1",
                "semantic_rule_id": "SR-MR-002-01",
                "feature": "Feature B",
                "scenarios": [{"scenario_id": "TC-2", "case_type": "negative"}],
            },
        ]
        bdd_response = json.dumps(
            {
                "results": [
                    {
                        "semantic_rule_id": record["semantic_rule_id"],
                        "feature_title": record["feature"],
                        "scenarios": [
                            {
                                "scenario_id": record["scenarios"][0]["scenario_id"],
                                "title": "Scenario",
                                "case_type": record["scenarios"][0]["case_type"],
                                "given_steps": [{"step_text": "Given state", "step_pattern": "Given state"}],
                                "when_steps": [{"step_text": "When action", "step_pattern": "When action"}],
                                "then_steps": [{"step_text": "Then result", "step_pattern": "Then result"}],
                            }
                        ],
                    }
                    for record in maker_records
                ]
            }
        )
        cases_path = self.work_tmp / "maker_cases.jsonl"
        output_dir = self.work_tmp / "bdd"
        cases_path.write_text(
            "".join(json.dumps(record) + "\n" for record in maker_records),
            encoding="utf-8",
        )
        with patch(
            "lme_testing.pipelines.build_provider",
            return_value=FakeProvider([bdd_response]),
        ):
            summary = run_bdd_pipeline(
                config=make_config(),
                maker_cases_path=cases_path,
                output_dir=output_dir,
                limit=None,
                batch_size=2,
                resume_from=None,
            )
        self.assertEqual(summary["processed_rule_count"], 2)
        self.assertEqual(summary["batch_count"], 1)
        self.assertEqual(summary["feature_files_count"], 2)


if __name__ == "__main__":
    unittest.main()

