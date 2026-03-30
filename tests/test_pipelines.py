from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

from lme_testing.config import ProjectConfig, ProviderConfig, RoleDefaults
from lme_testing.human_review import generate_human_review_page
from lme_testing.pipelines import run_checker_pipeline, run_maker_pipeline, run_rewrite_pipeline


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


if __name__ == "__main__":
    unittest.main()

