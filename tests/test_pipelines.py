from __future__ import annotations

import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from lme_testing.config import ProjectConfig, ProviderConfig, RoleDefaults
from lme_testing.pipelines import (
    analyze_maker_input_quality,
    run_bdd_pipeline,
    run_checker_pipeline,
    run_maker_pipeline,
    run_rewrite_pipeline,
)
from lme_testing.schemas import SchemaError


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


class RoutingProvider:
    def __init__(self, responses_by_id: dict[str, dict], delays: dict[str, float] | None = None):
        self.responses_by_id = responses_by_id
        self.delays = delays or {}
        self.calls: list[str] = []
        self.lock = threading.Lock()

    def generate(self, system_prompt: str, user_prompt: str):
        matched_id = next(key for key in self.responses_by_id if key in user_prompt)
        delay = self.delays.get(matched_id, 0)
        if delay:
            time.sleep(delay)
        with self.lock:
            self.calls.append(matched_id)
        payload = self.responses_by_id[matched_id]
        return type(
            "Response",
            (),
            {"content": json.dumps(payload, ensure_ascii=False), "raw_response": payload},
        )()


class TextProvider:
    def __init__(self, contents: list[str]):
        self.contents = contents
        self.index = 0

    def generate(self, system_prompt: str, user_prompt: str):
        content = self.contents[self.index]
        self.index += 1
        return type(
            "Response",
            (),
            {"content": content, "raw_response": {"content": content}},
        )()


class RawTextProvider:
    def __init__(self, responses: list[tuple[str, dict]]):
        self.responses = responses
        self.index = 0

    def generate(self, system_prompt: str, user_prompt: str):
        content, raw_response = self.responses[self.index]
        self.index += 1
        return type(
            "Response",
            (),
            {"content": content, "raw_response": raw_response},
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

    def test_maker_pipeline_concurrency_preserves_output_order(self) -> None:
        semantic_rules = [
            {
                "semantic_rule_id": f"SR-{index}",
                "source": {"atomic_rule_ids": [f"AR-{index}"]},
                "classification": {"rule_type": "permission", "coverage_eligible": True},
                "evidence": [{"atomic_rule_id": f"AR-{index}", "page": index, "quote": f"q{index}"}],
            }
            for index in range(1, 4)
        ]
        responses = {
            f"SR-{index}": {
                "results": [
                    {
                        "semantic_rule_id": f"SR-{index}",
                        "requirement_ids": [f"AR-{index}"],
                        "feature": f"Feature {index}",
                        "scenarios": [
                            {
                                "scenario_id": f"TC-{index}",
                                "title": f"Case {index}",
                                "intent": "test",
                                "priority": "high",
                                "case_type": "positive",
                                "given": ["g"],
                                "when": ["w"],
                                "then": ["t"],
                                "assumptions": [],
                                "evidence": [{"atomic_rule_id": f"AR-{index}", "page": index, "quote": f"q{index}"}],
                            }
                        ],
                    }
                ]
            }
            for index in range(1, 4)
        }
        provider = RoutingProvider(responses, delays={"SR-1": 0.05})
        rules_path = self.work_tmp / "semantic_rules.json"
        output_dir = self.work_tmp / "maker"
        rules_path.write_text(json.dumps(semantic_rules), encoding="utf-8")
        with patch("lme_testing.pipelines.build_provider", return_value=provider):
            summary = run_maker_pipeline(
                config=make_config(),
                semantic_rules_path=rules_path,
                output_dir=output_dir,
                limit=None,
                batch_size=1,
                resume_from=None,
                concurrency=3,
            )

        records = [json.loads(line) for line in Path(summary["results_path"]).read_text(encoding="utf-8").splitlines()]
        self.assertEqual([record["semantic_rule_id"] for record in records], ["SR-1", "SR-2", "SR-3"])
        self.assertEqual(summary["batch_count"], 3)
        self.assertEqual(set(provider.calls), {"SR-1", "SR-2", "SR-3"})

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

    def test_checker_pipeline_concurrency_preserves_output_order(self) -> None:
        semantic_rules = [
            {
                "semantic_rule_id": f"SR-{index}",
                "source": {"atomic_rule_ids": [f"AR-{index}"]},
                "classification": {"rule_type": "permission", "coverage_eligible": True},
                "evidence": [{"atomic_rule_id": f"AR-{index}", "page": index, "quote": f"q{index}"}],
            }
            for index in range(1, 4)
        ]
        maker_records = [
            {
                "run_id": "maker",
                "semantic_rule_id": f"SR-{index}",
                "feature": f"Feature {index}",
                "scenarios": [
                    {
                        "scenario_id": f"TC-{index}",
                        "case_type": "positive",
                        "title": f"Case {index}",
                        "intent": "test",
                        "priority": "high",
                        "given": ["g"],
                        "when": ["w"],
                        "then": ["t"],
                        "assumptions": [],
                        "evidence": [{"atomic_rule_id": f"AR-{index}", "page": index, "quote": f"q{index}"}],
                    }
                ],
            }
            for index in range(1, 4)
        ]
        responses = {
            f"TC-{index}": {
                "results": [
                    {
                        "case_id": f"TC-{index}",
                        "semantic_rule_id": f"SR-{index}",
                        "overall_status": "pass",
                        "scores": {
                            "evidence_consistency": 5,
                            "requirement_coverage": 5,
                            "test_design_quality": 5,
                            "non_hallucination": 5,
                        },
                        "case_type": "positive",
                        "case_type_accepted": True,
                        "coverage_relevance": "direct",
                        "blocking_findings_count": 0,
                        "is_blocking": False,
                        "findings": [],
                        "coverage_assessment": {"status": "covered", "reason": "ok", "missing_aspects": []},
                    }
                ]
            }
            for index in range(1, 4)
        }
        provider = RoutingProvider(responses, delays={"TC-1": 0.05})
        rules_path = self.work_tmp / "semantic_rules.json"
        cases_path = self.work_tmp / "cases.jsonl"
        output_dir = self.work_tmp / "checker"
        rules_path.write_text(json.dumps(semantic_rules), encoding="utf-8")
        cases_path.write_text("".join(json.dumps(record) + "\n" for record in maker_records), encoding="utf-8")
        with patch("lme_testing.pipelines.build_provider", return_value=provider):
            summary = run_checker_pipeline(
                config=make_config(),
                semantic_rules_path=rules_path,
                maker_cases_path=cases_path,
                output_dir=output_dir,
                limit=None,
                batch_size=1,
                resume_from=None,
                concurrency=3,
            )

        records = [json.loads(line) for line in Path(summary["results_path"]).read_text(encoding="utf-8").splitlines()]
        self.assertEqual([record["case_id"] for record in records], ["TC-1", "TC-2", "TC-3"])
        self.assertEqual(summary["review_count"], 3)
        self.assertEqual(set(provider.calls), {"TC-1", "TC-2", "TC-3"})

    def test_rewrite_pipeline_replaces_only_target_case(self) -> None:
        semantic_rules = [
            {
                "semantic_rule_id": "SR-1",
                "source": {"atomic_rule_ids": ["AR-1"]},
                "classification": {"rule_type": "permission", "coverage_eligible": True},
                "evidence": [{"atomic_rule_id": "AR-1", "page": 1, "quote": "q"}],
            }
        ]
        maker_record = {
            "run_id": "maker",
            "semantic_rule_id": "SR-1",
            "requirement_ids": ["AR-1"],
            "feature": "Original feature",
            "scenarios": [
                {
                    "scenario_id": "TC-1",
                    "title": "Original target",
                    "intent": "old",
                    "priority": "high",
                    "case_type": "positive",
                    "given": ["old g"],
                    "when": ["old w"],
                    "then": ["old t"],
                    "assumptions": [],
                    "evidence": [{"atomic_rule_id": "AR-1", "page": 1, "quote": "q"}],
                },
                {
                    "scenario_id": "TC-2",
                    "title": "Keep me",
                    "intent": "keep",
                    "priority": "high",
                    "case_type": "negative",
                    "given": ["keep g"],
                    "when": ["keep w"],
                    "then": ["keep t"],
                    "assumptions": [],
                    "evidence": [{"atomic_rule_id": "AR-1", "page": 1, "quote": "q"}],
                },
            ],
        }
        checker_reviews = [
            {"case_id": "TC-1", "semantic_rule_id": "SR-1", "findings": [{"message": "fix target"}]},
            {"case_id": "TC-2", "semantic_rule_id": "SR-1", "findings": []},
        ]
        human_reviews = {
            "metadata": {},
            "reviews": [
                {
                    "case_id": "TC-1",
                    "semantic_rule_id": "SR-1",
                    "review_decision": "rewrite",
                    "human_comment": "rewrite this case",
                    "issue_types": ["bad_assertion"],
                },
                {
                    "case_id": "TC-2",
                    "semantic_rule_id": "SR-1",
                    "review_decision": "approve",
                    "human_comment": "",
                    "issue_types": [],
                },
            ],
        }
        rewrite_response = json.dumps(
            {
                "results": [
                    {
                        "semantic_rule_id": "SR-1",
                        "requirement_ids": ["AR-1"],
                        "feature": "Rewritten feature",
                        "scenarios": [
                            {
                                "scenario_id": "TC-1-new",
                                "title": "Rewritten target",
                                "intent": "rewrite",
                                "priority": "high",
                                "case_type": "positive",
                                "given": ["new g"],
                                "when": ["new w"],
                                "then": ["new t"],
                                "assumptions": [],
                                "evidence": [{"atomic_rule_id": "AR-1", "page": 1, "quote": "q"}],
                            }
                        ],
                    }
                ]
            }
        )
        rules_path = self.work_tmp / "semantic_rules.json"
        cases_path = self.work_tmp / "maker_cases.jsonl"
        checker_path = self.work_tmp / "checker_reviews.jsonl"
        human_path = self.work_tmp / "human_reviews.json"
        output_dir = self.work_tmp / "rewrite"
        rules_path.write_text(json.dumps(semantic_rules, ensure_ascii=False), encoding="utf-8")
        cases_path.write_text(json.dumps(maker_record, ensure_ascii=False) + "\n", encoding="utf-8")
        checker_path.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in checker_reviews), encoding="utf-8")
        human_path.write_text(json.dumps(human_reviews, ensure_ascii=False), encoding="utf-8")

        with patch("lme_testing.pipelines.build_provider", return_value=FakeProvider([rewrite_response])):
            summary = run_rewrite_pipeline(
                config=make_config(),
                semantic_rules_path=rules_path,
                maker_cases_path=cases_path,
                checker_reviews_path=checker_path,
                human_reviews_path=human_path,
                output_dir=output_dir,
                limit=None,
                batch_size=1,
            )

        merged = [json.loads(line) for line in Path(summary["merged_cases_path"]).read_text(encoding="utf-8").splitlines()]
        scenarios = merged[0]["scenarios"]
        self.assertEqual([scenario["scenario_id"] for scenario in scenarios], ["TC-1", "TC-2"])
        self.assertEqual(scenarios[0]["title"], "Rewritten target")
        self.assertEqual(scenarios[1]["title"], "Keep me")
        self.assertEqual(summary["rewritten_case_ids"], ["TC-1"])
        self.assertTrue(Path(summary["rewritten_cases_path"]).exists())

    def test_checker_pipeline_incremental_inherits_unchanged_reviews(self) -> None:
        semantic_rules = [
            {"semantic_rule_id": "SR-1", "classification": {"rule_type": "permission", "coverage_eligible": True}},
            {"semantic_rule_id": "SR-2", "classification": {"rule_type": "permission", "coverage_eligible": True}},
        ]
        maker_records = [
            {
                "run_id": "maker",
                "semantic_rule_id": "SR-1",
                "feature": "Feature 1",
                "scenarios": [{"scenario_id": "TC-1", "case_type": "positive", "given": [], "when": [], "then": [], "assumptions": []}],
            },
            {
                "run_id": "maker",
                "semantic_rule_id": "SR-2",
                "feature": "Feature 2",
                "scenarios": [{"scenario_id": "TC-2", "case_type": "positive", "given": [], "when": [], "then": [], "assumptions": []}],
            },
        ]
        previous_reviews = [
            {"case_id": "TC-1", "semantic_rule_id": "SR-1", "overall_status": "old", "coverage_assessment": {"status": "partial"}},
            {"case_id": "TC-2", "semantic_rule_id": "SR-2", "overall_status": "inherited", "coverage_assessment": {"status": "covered"}},
        ]
        checker_response = json.dumps(
            {
                "results": [
                    {
                        "case_id": "TC-1-updated",
                        "semantic_rule_id": "SR-1",
                        "overall_status": "pass",
                        "scores": {"evidence_consistency": 5, "requirement_coverage": 5, "test_design_quality": 5, "non_hallucination": 5},
                        "case_type": "positive",
                        "case_type_accepted": True,
                        "coverage_relevance": "direct",
                        "blocking_findings_count": 0,
                        "is_blocking": False,
                        "findings": [],
                        "coverage_assessment": {"status": "covered", "reason": "ok", "missing_aspects": []},
                    }
                ]
            }
        )
        rules_path = self.work_tmp / "semantic_rules.json"
        cases_path = self.work_tmp / "maker_cases.jsonl"
        previous_path = self.work_tmp / "previous_checker.jsonl"
        output_dir = self.work_tmp / "checker_incremental"
        rules_path.write_text(json.dumps(semantic_rules, ensure_ascii=False), encoding="utf-8")
        cases_path.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in maker_records), encoding="utf-8")
        previous_path.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in previous_reviews), encoding="utf-8")

        with patch("lme_testing.pipelines.build_provider", return_value=FakeProvider([checker_response])):
            summary = run_checker_pipeline(
                config=make_config(),
                semantic_rules_path=rules_path,
                maker_cases_path=cases_path,
                output_dir=output_dir,
                limit=None,
                batch_size=1,
                resume_from=None,
                only_case_ids={"TC-1"},
                previous_reviews_path=previous_path,
            )

        records = [json.loads(line) for line in Path(summary["results_path"]).read_text(encoding="utf-8").splitlines()]
        self.assertEqual(summary["new_review_count"], 1)
        self.assertEqual(summary["inherited_review_count"], 1)
        self.assertEqual([record["case_id"] for record in records], ["TC-2", "TC-1"])
        self.assertEqual(records[0]["overall_status"], "inherited")
        self.assertEqual(records[1]["overall_status"], "pass")

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
        self.assertEqual(summary["bdd_provider_role"], "maker")
        self.assertEqual(summary["bdd_generation_mode"], "llm-with-fallback")

    def test_bdd_pipeline_falls_back_when_model_returns_invalid_json(self) -> None:
        maker_records = [
            {
                "run_id": "maker-run",
                "semantic_rule_id": "SR-MR-001-01",
                "feature": "Fallback Feature",
                "paragraph_ids": ["p1"],
                "scenarios": [
                    {
                        "scenario_id": "TC-1",
                        "title": "Fallback scenario",
                        "case_type": "positive",
                        "priority": "high",
                        "given": ["system has a trade"],
                        "when": ["margin is calculated"],
                        "then": ["initial margin is produced"],
                        "assumptions": ["demo fallback"],
                    }
                ],
            }
        ]
        cases_path = self.work_tmp / "maker_cases.jsonl"
        output_dir = self.work_tmp / "bdd_fallback"
        cases_path.write_text(json.dumps(maker_records[0]) + "\n", encoding="utf-8")
        with patch("lme_testing.pipelines.build_provider", return_value=TextProvider(["", "not json"])):
            summary = run_bdd_pipeline(
                config=make_config(),
                maker_cases_path=cases_path,
                output_dir=output_dir,
                limit=None,
                batch_size=1,
                resume_from=None,
            )

        self.assertEqual(summary["processed_rule_count"], 1)
        self.assertEqual(summary["fallback_batch_count"], 1)
        self.assertTrue(Path(summary["fallback_reasons_path"]).exists())
        normalized = [json.loads(line) for line in Path(summary["results_path"]).read_text(encoding="utf-8").splitlines()]
        self.assertEqual(normalized[0]["scenarios"][0]["given_steps"][0]["step_text"], "system has a trade")
        self.assertEqual(normalized[0]["scenarios"][0]["then_steps"][0]["step_pattern"], "initial margin is produced")

    def test_bdd_pipeline_llm_mode_fails_without_fallback(self) -> None:
        maker_record = {
            "run_id": "maker-run",
            "semantic_rule_id": "SR-MR-001-01",
            "feature": "Strict LLM Feature",
            "scenarios": [
                {
                    "scenario_id": "TC-1",
                    "case_type": "positive",
                    "given": ["system has a trade"],
                    "when": ["margin is calculated"],
                    "then": ["initial margin is produced"],
                }
            ],
        }
        cases_path = self.work_tmp / "maker_cases_llm_only.jsonl"
        output_dir = self.work_tmp / "bdd_llm_only"
        cases_path.write_text(json.dumps(maker_record) + "\n", encoding="utf-8")

        with patch("lme_testing.pipelines.build_provider", return_value=TextProvider(["not json", "still not json"])):
            with self.assertRaises(SchemaError):
                run_bdd_pipeline(
                    config=make_config(),
                    maker_cases_path=cases_path,
                    output_dir=output_dir,
                    limit=None,
                    batch_size=1,
                    resume_from=None,
                    bdd_generation_mode="llm",
                )

    def test_bdd_pipeline_records_truncated_output_reason(self) -> None:
        maker_record = {
            "run_id": "maker-run",
            "semantic_rule_id": "SR-MR-001-01",
            "feature": "Truncated Feature",
            "scenarios": [
                {
                    "scenario_id": "TC-1",
                    "case_type": "positive",
                    "given": ["system has a trade"],
                    "when": ["margin is calculated"],
                    "then": ["initial margin is produced"],
                }
            ],
        }
        cases_path = self.work_tmp / "maker_cases_truncated_bdd.jsonl"
        output_dir = self.work_tmp / "bdd_truncated"
        cases_path.write_text(json.dumps(maker_record) + "\n", encoding="utf-8")
        raw = {"choices": [{"finish_reason": "length", "message": {"content": "{\"results\": ["}}]}

        with patch("lme_testing.pipelines.build_provider", return_value=RawTextProvider([("{\"results\": [", raw), ("{\"results\": [", raw)])):
            summary = run_bdd_pipeline(
                config=make_config(),
                maker_cases_path=cases_path,
                output_dir=output_dir,
                limit=None,
                batch_size=1,
                resume_from=None,
                bdd_generation_mode="llm-with-fallback",
            )

        reasons = json.loads(Path(summary["fallback_reasons_path"]).read_text(encoding="utf-8"))
        self.assertTrue(reasons[0]["reason"].startswith("truncated_output:"))

    def test_bdd_pipeline_can_use_deterministic_fallback_without_model_call(self) -> None:
        maker_record = {
            "run_id": "maker-run",
            "semantic_rule_id": "SR-MR-001-01",
            "feature": "Fast Demo Feature",
            "paragraph_ids": ["p1"],
            "scenarios": [
                {
                    "scenario_id": "TC-1",
                    "title": "Fast scenario",
                    "case_type": "positive",
                    "priority": "high",
                    "given": ["system has a trade"],
                    "when": ["margin is calculated"],
                    "then": ["initial margin is produced"],
                    "assumptions": [],
                }
            ],
        }
        cases_path = self.work_tmp / "maker_cases_fast_bdd.jsonl"
        output_dir = self.work_tmp / "bdd_fast_fallback"
        cases_path.write_text(json.dumps(maker_record) + "\n", encoding="utf-8")

        with patch("lme_testing.pipelines.build_provider") as build_provider:
            summary = run_bdd_pipeline(
                config=make_config(),
                maker_cases_path=cases_path,
                output_dir=output_dir,
                limit=None,
                batch_size=1,
                resume_from=None,
                deterministic_fallback_only=True,
            )

        build_provider.assert_not_called()
        self.assertTrue(summary["deterministic_fallback_only"])
        self.assertEqual(summary["bdd_generation_mode"], "deterministic")
        self.assertEqual(summary["processed_rule_count"], 1)
        self.assertEqual(summary["fallback_batch_count"], 1)
        normalized = [json.loads(line) for line in Path(summary["results_path"]).read_text(encoding="utf-8").splitlines()]
        self.assertEqual(normalized[0]["scenarios"][0]["when_steps"][0]["step_text"], "margin is calculated")

    def test_bdd_pipeline_prefers_bdd_provider_role_when_configured(self) -> None:
        maker_provider = ProviderConfig(
            name="maker_provider",
            provider_type="openai_compatible",
            model="maker-model",
            base_url="https://example.com/v1",
            api_key="secret",
        )
        bdd_provider = ProviderConfig(
            name="bdd_provider",
            provider_type="openai_compatible",
            model="bdd-model",
            base_url="https://example.com/v1",
            api_key="secret",
        )
        config = ProjectConfig(
            providers={"maker_provider": maker_provider, "bdd_provider": bdd_provider},
            roles={"maker": "maker_provider", "checker": "maker_provider", "bdd": "bdd_provider"},
            output_root=Path("runs"),
            maker_defaults=RoleDefaults(),
            checker_defaults=RoleDefaults(),
        )
        maker_record = {
            "run_id": "r1",
            "semantic_rule_id": "SR-MR-001-01",
            "feature": "Feature A",
            "scenarios": [{"scenario_id": "TC-1", "case_type": "positive"}],
        }
        bdd_response = json.dumps({
            "results": [{
                "semantic_rule_id": "SR-MR-001-01",
                "feature_title": "Feature A",
                "scenarios": [{
                    "scenario_id": "TC-1",
                    "case_type": "positive",
                    "given_steps": [{"step_text": "g", "step_pattern": "g"}],
                    "when_steps": [{"step_text": "w", "step_pattern": "w"}],
                    "then_steps": [{"step_text": "t", "step_pattern": "t"}],
                }],
            }]
        })
        cases_path = self.work_tmp / "maker_cases_bdd_provider.jsonl"
        output_dir = self.work_tmp / "bdd_provider"
        cases_path.write_text(json.dumps(maker_record) + "\n", encoding="utf-8")

        with patch("lme_testing.pipelines.build_provider", return_value=FakeProvider([bdd_response])) as build_provider:
            summary = run_bdd_pipeline(
                config=config,
                maker_cases_path=cases_path,
                output_dir=output_dir,
                limit=None,
                batch_size=1,
                resume_from=None,
            )

        self.assertEqual(build_provider.call_args.args[0].name, "bdd_provider")
        self.assertEqual(summary["bdd_provider_role"], "bdd")


if __name__ == "__main__":
    unittest.main()

