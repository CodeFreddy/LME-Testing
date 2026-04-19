from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

from lme_testing.config import ProjectConfig, ProviderConfig, RoleDefaults
from lme_testing.case_compare import build_case_compare
from lme_testing.human_review import generate_human_review_page
from lme_testing.pipelines import run_checker_pipeline, run_maker_pipeline, run_rewrite_pipeline
from lme_testing.reporting import generate_html_report


WORK_TMP = Path('.tmp_test')


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
        WORK_TMP.mkdir(exist_ok=True)

    def tearDown(self) -> None:
        if WORK_TMP.exists():
            shutil.rmtree(WORK_TMP)

    def test_maker_pipeline_persists_records(self) -> None:
        semantic_rules = [
            {
                "semantic_rule_id": "SR-MR-001-01",
                "classification": {"rule_type": "permission", "coverage_eligible": True},
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
                                    {"atomic_rule_id": "MR-001-01", "page": 1, "quote": "q"}
                                ],
                            }
                        ],
                    }
                ]
            }
        )
        rules_path = WORK_TMP / "semantic_rules.json"
        output_dir = WORK_TMP / "maker"
        rules_path.write_text(json.dumps(semantic_rules), encoding="utf-8")
        with patch("lme_testing.pipelines.build_provider", return_value=FakeProvider([maker_response])):
            summary = run_maker_pipeline(
                config=make_config(),
                semantic_rules_path=rules_path,
                output_dir=output_dir,
                limit=None,
                batch_size=1,
                resume_from=None,
            )
        self.assertEqual(summary["processed_rule_count"], 1)
        self.assertEqual(summary["scenario_count"], 1)
        self.assertTrue(Path(summary["results_path"]).exists())

    def test_checker_pipeline_generates_coverage_and_blocking_summary(self) -> None:
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
            ],
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
                            "non_hallucination": 5,
                        },
                        "case_type": "positive",
                        "case_type_accepted": True,
                        "coverage_relevance": "direct",
                        "blocking_findings_count": 0,
                        "is_blocking": False,
                        "blocking_category": "none",
                        "blocking_reason": "",
                        "checker_confidence": 0.91,
                        "findings": [],
                        "coverage_assessment": {"status": "covered", "reason": "ok", "missing_aspects": []},
                    }
                ]
            }
        )
        rules_path = WORK_TMP / "semantic_rules.json"
        cases_path = WORK_TMP / "cases.jsonl"
        output_dir = WORK_TMP / "checker"
        rules_path.write_text(json.dumps(semantic_rules), encoding="utf-8")
        cases_path.write_text(json.dumps(maker_record) + "\n", encoding="utf-8")
        with patch("lme_testing.pipelines.build_provider", return_value=FakeProvider([checker_response])):
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
        review = json.loads(Path(summary["results_path"]).read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(coverage["fully_covered"], 1)
        self.assertEqual(coverage["uncovered"], 1)
        self.assertEqual(coverage["checker_block_count"], 0)
        self.assertEqual(summary["checker_block_count"], 0)
        self.assertEqual(review["checker_blocking"], False)
        self.assertEqual(review["block_recommendation_review"], "not_applicable")

    def test_human_review_page_generation(self) -> None:
        maker_cases_path = WORK_TMP / "maker_cases.jsonl"
        checker_reviews_path = WORK_TMP / "checker_reviews.jsonl"
        output_html = WORK_TMP / "human_review.html"
        maker_cases_path.write_text(
            json.dumps(
                {
                    "semantic_rule_id": "SR-MR-001-01",
                    "feature": "Feature A",
                    "scenarios": [{"scenario_id": "TC-1", "case_type": "positive", "given": [], "when": [], "then": [], "assumptions": [], "evidence": []}],
                }
            ) + "\n",
            encoding="utf-8",
        )
        checker_reviews_path.write_text(
            json.dumps(
                {
                    "case_id": "TC-1",
                    "semantic_rule_id": "SR-MR-001-01",
                    "overall_status": "fail",
                    "coverage_assessment": {"status": "partial", "reason": "needs work", "missing_aspects": []},
                    "checker_blocking": True,
                    "checker_blocking_category": "rule_mismatch",
                    "checker_blocking_reason": "rule mismatch",
                    "findings": [],
                }
            ) + "\n",
            encoding="utf-8",
        )
        result = generate_human_review_page(maker_cases_path, checker_reviews_path, output_html)
        html_text = output_html.read_text(encoding="utf-8")
        self.assertEqual(result["total_cases"], 1)
        self.assertTrue(output_html.exists())
        self.assertIn("Block Recommendation Review", html_text)
        self.assertIn("Issue Types", html_text)

    def test_rewrite_pipeline_rewrites_only_decision_equals_rewrite(self) -> None:
        semantic_rules = [
            {
                "semantic_rule_id": "SR-MR-001-01",
                "source": {"atomic_rule_ids": ["MR-001-01"]},
                "classification": {"rule_type": "permission", "coverage_eligible": True},
                "evidence": [{"atomic_rule_id": "MR-001-01", "page": 1, "quote": "q"}],
            },
            {
                "semantic_rule_id": "SR-MR-002-01",
                "source": {"atomic_rule_ids": ["MR-002-01"]},
                "classification": {"rule_type": "permission", "coverage_eligible": True},
                "evidence": [{"atomic_rule_id": "MR-002-01", "page": 1, "quote": "q2"}],
            },
        ]
        maker_records = [
            {
                "run_id": "r1",
                "semantic_rule_id": "SR-MR-001-01",
                "requirement_ids": ["MR-001-01"],
                "feature": "Feature A",
                "scenarios": [{"scenario_id": "TC-1", "case_type": "positive", "given": [], "when": [], "then": [], "assumptions": [], "evidence": [{"atomic_rule_id": "MR-001-01", "page": 1, "quote": "q"}]}],
            },
            {
                "run_id": "r1",
                "semantic_rule_id": "SR-MR-002-01",
                "requirement_ids": ["MR-002-01"],
                "feature": "Feature B",
                "scenarios": [{"scenario_id": "TC-2", "case_type": "positive", "given": [], "when": [], "then": [], "assumptions": [], "evidence": [{"atomic_rule_id": "MR-002-01", "page": 1, "quote": "q2"}]}],
            },
        ]
        checker_reviews = [
            {"case_id": "TC-1", "semantic_rule_id": "SR-MR-001-01"},
            {"case_id": "TC-2", "semantic_rule_id": "SR-MR-002-01"},
        ]
        human_reviews = {
            "reviews": [
                {
                    "case_id": "TC-1",
                    "semantic_rule_id": "SR-MR-001-01",
                    "review_decision": "rewrite",
                    "block_recommendation_review": "pending_review",
                    "human_comment": "rewrite this rule",
                    "issue_types": ["bad_assertion"],
                },
                {
                    "case_id": "TC-2",
                    "semantic_rule_id": "SR-MR-002-01",
                    "review_decision": "approve",
                    "block_recommendation_review": "confirmed",
                    "human_comment": "approved by human despite checker suggestion",
                    "issue_types": ["coverage_dispute"],
                },
            ]
        }
        rewrite_response = json.dumps(
            {
                "results": [
                    {
                        "semantic_rule_id": "SR-MR-001-01",
                        "requirement_ids": ["MR-001-01"],
                        "feature": "Feature A rewritten",
                        "scenarios": [
                            {
                                "scenario_id": "TC-1-rewritten",
                                "title": "Rewritten case",
                                "intent": "rewrite",
                                "priority": "high",
                                "case_type": "positive",
                                "given": ["g"],
                                "when": ["w"],
                                "then": ["t"],
                                "assumptions": [],
                                "evidence": [{"atomic_rule_id": "MR-001-01", "page": 1, "quote": "q"}],
                            }
                        ],
                    }
                ]
            }
        )
        rules_path = WORK_TMP / "semantic_rules.json"
        maker_cases_path = WORK_TMP / "maker_cases.jsonl"
        checker_reviews_path = WORK_TMP / "checker_reviews.jsonl"
        human_reviews_path = WORK_TMP / "human_reviews.json"
        output_dir = WORK_TMP / "rewrite"
        rules_path.write_text(json.dumps(semantic_rules), encoding="utf-8")
        maker_cases_path.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in maker_records) + "\n", encoding="utf-8")
        checker_reviews_path.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in checker_reviews) + "\n", encoding="utf-8")
        human_reviews_path.write_text(json.dumps(human_reviews, ensure_ascii=False), encoding="utf-8")
        with patch("lme_testing.pipelines.build_provider", return_value=FakeProvider([rewrite_response])):
            summary = run_rewrite_pipeline(
                config=make_config(),
                semantic_rules_path=rules_path,
                maker_cases_path=maker_cases_path,
                checker_reviews_path=checker_reviews_path,
                human_reviews_path=human_reviews_path,
                output_dir=output_dir,
                limit=None,
                batch_size=1,
            )
        self.assertEqual(summary["target_rule_count"], 1)
        self.assertEqual(summary["rewritten_rule_count"], 1)
        merged_records = [json.loads(line) for line in Path(summary["merged_cases_path"]).read_text(encoding="utf-8").splitlines() if line.strip()]
        rewritten_record = next(item for item in merged_records if item["semantic_rule_id"] == "SR-MR-001-01")
        untouched_record = next(item for item in merged_records if item["semantic_rule_id"] == "SR-MR-002-01")
        self.assertEqual(rewritten_record["feature"], "Feature A rewritten")
        self.assertEqual(untouched_record["feature"], "Feature B")

    def test_generate_html_report_uses_case_files_for_metrics_with_rewrite_summary(self) -> None:
        maker_cases_path = WORK_TMP / "maker_cases.jsonl"
        checker_reviews_path = WORK_TMP / "checker_reviews.jsonl"
        maker_summary_path = WORK_TMP / "rewrite_summary.json"
        checker_summary_path = WORK_TMP / "checker_summary.json"
        coverage_report_path = WORK_TMP / "coverage_report.json"
        output_html = WORK_TMP / "report.html"

        maker_records = [
            {
                "semantic_rule_id": "SR-1",
                "feature": "Feature 1",
                "requirement_ids": ["AR-1"],
                "scenarios": [
                    {"scenario_id": "TC-1", "case_type": "positive", "title": "t1", "intent": "i1", "priority": "high", "given": [], "when": [], "then": [], "assumptions": [], "evidence": []},
                    {"scenario_id": "TC-2", "case_type": "negative", "title": "t2", "intent": "i2", "priority": "high", "given": [], "when": [], "then": [], "assumptions": [], "evidence": []},
                ],
            },
            {
                "semantic_rule_id": "SR-2",
                "feature": "Feature 2",
                "requirement_ids": ["AR-2"],
                "scenarios": [
                    {"scenario_id": "TC-3", "case_type": "positive", "title": "t3", "intent": "i3", "priority": "high", "given": [], "when": [], "then": [], "assumptions": [], "evidence": []},
                    {"scenario_id": "TC-4", "case_type": "boundary", "title": "t4", "intent": "i4", "priority": "high", "given": [], "when": [], "then": [], "assumptions": [], "evidence": []},
                    {"scenario_id": "TC-5", "case_type": "negative", "title": "t5", "intent": "i5", "priority": "high", "given": [], "when": [], "then": [], "assumptions": [], "evidence": []},
                ],
            },
        ]
        checker_reviews = [
            {"case_id": f"TC-{i}", "semantic_rule_id": "SR-1" if i <= 2 else "SR-2", "overall_status": "pass", "coverage_assessment": {"status": "covered", "reason": "ok", "missing_aspects": []}, "scores": {}, "findings": []}
            for i in range(1, 6)
        ]
        rewrite_summary = {
            "run_id": "rw1",
            "role": "maker_rewrite",
            "target_rule_count": 1,
            "rewritten_rule_count": 1,
            "rewritten_scenario_count": 2,
        }
        checker_summary = {"run_id": "ck1", "review_count": 99}
        coverage_report = {
            "fully_covered": 2,
            "partially_covered": 0,
            "uncovered": 0,
            "checker_block_count": 0,
            "coverage_percent": 100.0,
            "status_by_rule": {},
        }

        maker_cases_path.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in maker_records) + "\n", encoding="utf-8")
        checker_reviews_path.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in checker_reviews) + "\n", encoding="utf-8")
        maker_summary_path.write_text(json.dumps(rewrite_summary, ensure_ascii=False), encoding="utf-8")
        checker_summary_path.write_text(json.dumps(checker_summary, ensure_ascii=False), encoding="utf-8")
        coverage_report_path.write_text(json.dumps(coverage_report, ensure_ascii=False), encoding="utf-8")

        generate_html_report(
            maker_cases_path=maker_cases_path,
            checker_reviews_path=checker_reviews_path,
            maker_summary_path=maker_summary_path,
            checker_summary_path=checker_summary_path,
            coverage_report_path=coverage_report_path,
            output_html_path=output_html,
        )

        html_text = output_html.read_text(encoding="utf-8")
        self.assertIn("Maker Rule 数</strong><br/>2", html_text)
        self.assertIn("Maker Scenario 数</strong><br/>5", html_text)
        self.assertIn("Checker Review 数</strong><br/>5", html_text)
        self.assertIn("Fully Covered</strong><br/>2", html_text)
        self.assertIn("覆盖率</strong><br/>100.0%", html_text)

    def test_generate_html_report_keeps_standard_maker_metrics(self) -> None:
        maker_cases_path = WORK_TMP / "maker_cases_standard.jsonl"
        checker_reviews_path = WORK_TMP / "checker_reviews_standard.jsonl"
        maker_summary_path = WORK_TMP / "maker_summary.json"
        checker_summary_path = WORK_TMP / "checker_summary_standard.json"
        coverage_report_path = WORK_TMP / "coverage_report_standard.json"
        output_html = WORK_TMP / "report_standard.html"

        maker_records = [
            {
                "semantic_rule_id": "SR-1",
                "feature": "Feature 1",
                "requirement_ids": ["AR-1"],
                "scenarios": [
                    {"scenario_id": "TC-1", "case_type": "positive", "title": "t1", "intent": "i1", "priority": "high", "given": [], "when": [], "then": [], "assumptions": [], "evidence": []},
                ],
            }
        ]
        checker_reviews = [
            {"case_id": "TC-1", "semantic_rule_id": "SR-1", "overall_status": "pass", "coverage_assessment": {"status": "covered", "reason": "ok", "missing_aspects": []}, "scores": {}, "findings": []}
        ]
        maker_summary = {"run_id": "mk1", "processed_rule_count": 1, "scenario_count": 1}
        checker_summary = {"run_id": "ck2", "review_count": 1}
        coverage_report = {
            "fully_covered": 1,
            "partially_covered": 0,
            "uncovered": 0,
            "checker_block_count": 0,
            "coverage_percent": 100.0,
            "status_by_rule": {},
        }

        maker_cases_path.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in maker_records) + "\n", encoding="utf-8")
        checker_reviews_path.write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in checker_reviews) + "\n", encoding="utf-8")
        maker_summary_path.write_text(json.dumps(maker_summary, ensure_ascii=False), encoding="utf-8")
        checker_summary_path.write_text(json.dumps(checker_summary, ensure_ascii=False), encoding="utf-8")
        coverage_report_path.write_text(json.dumps(coverage_report, ensure_ascii=False), encoding="utf-8")

        generate_html_report(
            maker_cases_path=maker_cases_path,
            checker_reviews_path=checker_reviews_path,
            maker_summary_path=maker_summary_path,
            checker_summary_path=checker_summary_path,
            coverage_report_path=coverage_report_path,
            output_html_path=output_html,
        )

        html_text = output_html.read_text(encoding="utf-8")
        self.assertIn("Maker Rule 数</strong><br/>1", html_text)
        self.assertIn("Maker Scenario 数</strong><br/>1", html_text)
        self.assertIn("Checker Review 数</strong><br/>1", html_text)

    def test_generate_html_report_uses_coverage_report_for_partial_uncovered_and_blocking(self) -> None:
        maker_cases_path = WORK_TMP / "maker_cases_coverage.jsonl"
        checker_reviews_path = WORK_TMP / "checker_reviews_coverage.jsonl"
        maker_summary_path = WORK_TMP / "maker_summary_coverage.json"
        checker_summary_path = WORK_TMP / "checker_summary_coverage.json"
        coverage_report_path = WORK_TMP / "coverage_report_metrics.json"
        output_html = WORK_TMP / "report_coverage.html"

        maker_cases_path.write_text(
            json.dumps(
                {
                    "semantic_rule_id": "SR-1",
                    "feature": "Feature 1",
                    "requirement_ids": ["AR-1"],
                    "scenarios": [
                        {"scenario_id": "TC-1", "case_type": "positive", "title": "t1", "intent": "i1", "priority": "high", "given": [], "when": [], "then": [], "assumptions": [], "evidence": []},
                    ],
                },
                ensure_ascii=False,
            ) + "\n",
            encoding="utf-8",
        )
        checker_reviews_path.write_text(
            json.dumps(
                {
                    "case_id": "TC-1",
                    "semantic_rule_id": "SR-1",
                    "overall_status": "fail",
                    "coverage_assessment": {"status": "partial", "reason": "needs work", "missing_aspects": []},
                    "checker_blocking": False,
                    "scores": {},
                    "findings": [],
                },
                ensure_ascii=False,
            ) + "\n",
            encoding="utf-8",
        )
        maker_summary_path.write_text(json.dumps({"run_id": "mk3", "processed_rule_count": 88, "scenario_count": 77}, ensure_ascii=False), encoding="utf-8")
        checker_summary_path.write_text(json.dumps({"run_id": "ck3", "review_count": 66}, ensure_ascii=False), encoding="utf-8")
        coverage_report_path.write_text(
            json.dumps(
                {
                    "fully_covered": 1,
                    "partially_covered": 3,
                    "uncovered": 4,
                    "checker_block_count": 2,
                    "coverage_percent": 12.5,
                    "status_by_rule": {},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        generate_html_report(
            maker_cases_path=maker_cases_path,
            checker_reviews_path=checker_reviews_path,
            maker_summary_path=maker_summary_path,
            checker_summary_path=checker_summary_path,
            coverage_report_path=coverage_report_path,
            output_html_path=output_html,
        )

        html_text = output_html.read_text(encoding="utf-8")
        self.assertIn("Partially Covered</strong><br/>3", html_text)
        self.assertIn("Uncovered</strong><br/>4", html_text)
        self.assertIn("Checker Blocking</strong><br/>2", html_text)

    def test_build_case_compare_can_align_iteration_labels_with_history(self) -> None:
        prev_cases_path = WORK_TMP / "compare_prev.jsonl"
        next_cases_path = WORK_TMP / "compare_next.jsonl"
        output_html = WORK_TMP / "compare.html"

        prev_cases_path.write_text(
            json.dumps(
                {
                    "semantic_rule_id": "SR-1",
                    "scenarios": [
                        {"scenario_id": "TC-1", "given": ["before"], "when": [], "then": [], "assumptions": [], "evidence": [], "case_type": "positive"},
                    ],
                },
                ensure_ascii=False,
            ) + "\n",
            encoding="utf-8",
        )
        next_cases_path.write_text(
            json.dumps(
                {
                    "semantic_rule_id": "SR-1",
                    "scenarios": [
                        {"scenario_id": "TC-1", "given": ["after"], "when": [], "then": [], "assumptions": [], "evidence": [], "case_type": "positive"},
                    ],
                },
                ensure_ascii=False,
            ) + "\n",
            encoding="utf-8",
        )

        result = build_case_compare(
            prev_cases_path=prev_cases_path,
            next_cases_path=next_cases_path,
            rewritten_case_ids={"TC-1"},
            iteration_prev=0,
            iteration_next=1,
            output_html_path=output_html,
            display_iteration=0,
        )

        html_text = output_html.read_text(encoding="utf-8")
        self.assertEqual(result["display_iteration"], 0)
        self.assertIn("Case Compare: Iteration 000", html_text)
        self.assertIn("Iteration 0 (before)", html_text)
        self.assertIn("Iteration 0 (after)", html_text)


if __name__ == "__main__":
    unittest.main()

