from __future__ import annotations

import json
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch

from lme_testing.config import ProjectConfig, ProviderConfig, RoleDefaults
from lme_testing.pipelines import run_checker_pipeline, run_maker_pipeline


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
        rules_path = WORK_TMP / "semantic_rules.json"
        output_dir = WORK_TMP / "maker"
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
        self.assertEqual(summary["scenario_count"], 1)
        self.assertTrue(Path(summary["results_path"]).exists())

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
        rules_path = WORK_TMP / "semantic_rules.json"
        cases_path = WORK_TMP / "cases.jsonl"
        output_dir = WORK_TMP / "checker"
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


if __name__ == "__main__":
    unittest.main()
