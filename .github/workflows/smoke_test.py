#!/usr/bin/env python3
"""End-to-end smoke test that runs the full pipeline using FakeProvider.

This exercises the complete maker -> checker -> report flow without making
any real LLM API calls. All model responses are served from in-memory fixtures.

Exit codes:
  0 = all steps passed
  1 = one or more steps failed
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

# Ensure lme_testing is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from lme_testing.config import ProjectConfig, ProviderConfig, RoleDefaults
from lme_testing.pipelines import RULE_TYPE_CASE_REQUIREMENTS, run_checker_pipeline, run_maker_pipeline
from lme_testing.reporting import generate_html_report
from lme_testing.storage import load_json, load_jsonl
from lme_testing.signals import compute_governance_signals, write_signals_report


WORK = Path(tempfile.mkdtemp(prefix="lme_smoke_"))


def make_config() -> ProjectConfig:
    provider = ProviderConfig(
        name="fake",
        provider_type="openai_compatible",
        model="fake-model",
        base_url="https://fake.example.com/v1",
        api_key="fake",
    )
    return ProjectConfig(
        providers={"fake": provider},
        roles={"maker": "fake", "checker": "fake"},
        output_root=WORK / "runs",
        maker_defaults=RoleDefaults(),
        checker_defaults=RoleDefaults(),
    )


def _required_case_types(rule: dict) -> list[str]:
    rule_type = rule.get("classification", {}).get("rule_type", "reference_only")
    return list(
        RULE_TYPE_CASE_REQUIREMENTS.get(
            rule_type, {"required": ["positive"], "optional": []}
        )["required"]
    )


def build_maker_responses(semantic_rules: list[dict]) -> list[str]:
    """Build FakeProvider response payloads for the maker stage."""
    results = []
    for rule in semantic_rules:
        sid = rule["semantic_rule_id"]
        aid = rule.get("source", {}).get("atomic_rule_ids", [sid])[0]
        quote = rule.get("evidence", [{}])[0].get("quote", "test quote")[:100]
        page = rule.get("evidence", [{}])[0].get("page", 1)
        required_types = _required_case_types(rule)

        scenarios = []
        for i, case_type in enumerate(required_types):
            scenarios.append(
                {
                    "scenario_id": f"TC-{sid}-{i + 1}",
                    "title": f"Scenario {i + 1} for {sid}",
                    "intent": f"Test intent for {sid} [{case_type}]",
                    "priority": "high",
                    "case_type": case_type,
                    "given": ["given precondition"],
                    "when": ["when action occurs"],
                    "then": ["then outcome expected"],
                    "assumptions": [],
                    "evidence": [
                        {"atomic_rule_id": aid, "page": page, "quote": quote}
                    ],
                }
            )

        results.append(
            json.dumps(
                {
                    "results": [
                        {
                            "semantic_rule_id": sid,
                            "requirement_ids": [aid],
                            "feature": f"Feature for {sid}",
                            "scenarios": scenarios,
                        }
                    ]
                },
                ensure_ascii=False,
            )
        )
    return results


def build_checker_responses(maker_records: list[dict]) -> list[str]:
    """Build FakeProvider response payloads for the checker stage."""
    results = []
    for record in maker_records:
        sid = record["semantic_rule_id"]
        for scenario in record.get("scenarios", []):
            cid = scenario["scenario_id"]
            results.append(
                json.dumps(
                    {
                        "results": [
                            {
                                "case_id": cid,
                                "semantic_rule_id": sid,
                                "overall_status": "pass",
                                "scores": {
                                    "evidence_consistency": 5,
                                    "requirement_coverage": 5,
                                    "test_design_quality": 5,
                                    "non_hallucination": 5,
                                },
                                "case_type": scenario.get("case_type", "positive"),
                                "case_type_accepted": True,
                                "coverage_relevance": "direct",
                                "blocking_findings_count": 0,
                                "is_blocking": False,
                                "findings": [],
                                "coverage_assessment": {
                                    "status": "covered",
                                    "reason": "all required aspects present",
                                    "missing_aspects": [],
                                },
                            }
                        ]
                    },
                    ensure_ascii=False,
                )
            )
    return results


class SmokeFakeProvider:
    """FakeProvider that serves pre-built responses in order."""

    def __init__(self, responses: list[str]):
        self.responses = responses
        self.index = 0

    def generate(self, system_prompt: str, user_prompt: str):
        if self.index >= len(self.responses):
            raise RuntimeError(
                f"SmokeFakeProvider exhausted: asked for response {self.index + 1} but only {len(self.responses)} were configured"
            )
        payload = json.loads(self.responses[self.index])
        self.index += 1
        return type(
            "Response",
            (),
            {"content": json.dumps(payload, ensure_ascii=False), "raw_response": payload},
        )()


def run_smoke():
    config = make_config()

    # Use the minimal poc_two_rules baseline
    baseline = Path("artifacts/poc_two_rules/semantic_rules.json")
    if not baseline.exists():
        print(f"FAIL: Baseline not found: {baseline}")
        return False

    semantic_rules = load_json(baseline)
    if not isinstance(semantic_rules, list):
        print(f"FAIL: semantic_rules.json is not a list")
        return False

    maker_responses = build_maker_responses(semantic_rules)
    maker_call_count = [0]

    def fake_maker_provider(cfg):
        maker_call_count[0] += 1
        return SmokeFakeProvider(maker_responses)

    checker_responses = build_checker_responses([])
    checker_call_count = [0]

    def fake_checker_provider(cfg):
        checker_call_count[0] += 1
        return SmokeFakeProvider(checker_responses)

    maker_output_dir = WORK / "maker"
    checker_output_dir = WORK / "checker"
    report_output_dir = WORK / "report"

    # --- Maker ---
    try:
        with patch("lme_testing.pipelines.build_provider", fake_maker_provider):
            maker_summary = run_maker_pipeline(
                config=config,
                semantic_rules_path=baseline,
                output_dir=maker_output_dir,
                limit=None,
                batch_size=1,
                resume_from=None,
            )
    except Exception as e:
        print(f"FAIL: Maker pipeline raised: {e}")
        return False

    maker_cases_path = Path(maker_summary["results_path"])
    if not maker_cases_path.exists():
        print(f"FAIL: Maker did not produce {maker_cases_path}")
        return False

    maker_records = load_jsonl(maker_cases_path)
    if not maker_records:
        print(f"FAIL: Maker produced empty {maker_cases_path}")
        return False

    # Rebuild checker responses with actual maker records now available
    checker_responses = build_checker_responses(maker_records)
    checker_call_count[0] = 0

    # --- Checker ---
    try:
        with patch("lme_testing.pipelines.build_provider", fake_checker_provider):
            checker_summary = run_checker_pipeline(
                config=config,
                semantic_rules_path=baseline,
                maker_cases_path=maker_cases_path,
                output_dir=checker_output_dir,
                limit=None,
                batch_size=1,
                resume_from=None,
            )
    except Exception as e:
        print(f"FAIL: Checker pipeline raised: {e}")
        return False

    checker_reviews_path = Path(checker_summary["results_path"])
    coverage_report_path = Path(checker_summary["coverage_report_path"])

    if not checker_reviews_path.exists():
        print(f"FAIL: Checker did not produce {checker_reviews_path}")
        return False

    if not coverage_report_path.exists():
        print(f"FAIL: Checker did not produce {coverage_report_path}")
        return False

    # --- Report ---
    try:
        generate_html_report(
            maker_cases_path=maker_cases_path,
            checker_reviews_path=checker_reviews_path,
            maker_summary_path=Path(maker_summary["output_dir"]) / "summary.json",
            checker_summary_path=Path(checker_summary["output_dir"]) / "summary.json",
            coverage_report_path=coverage_report_path,
            output_html_path=report_output_dir / "report.html",
        )
    except Exception as e:
        print(f"FAIL: Report generation raised: {e}")
        return False

    expected_report = report_output_dir / "report.html"
    if not expected_report.exists():
        print(f"FAIL: Report did not produce {expected_report}")
        return False

    # --- Assertions ---
    passed = True
    expected_scenario_count = sum(len(_required_case_types(r)) for r in semantic_rules)

    if maker_summary["processed_rule_count"] != len(semantic_rules):
        print(
            f"FAIL: Maker processed {maker_summary['processed_rule_count']} rules, expected {len(semantic_rules)}"
        )
        passed = False

    if maker_summary["scenario_count"] != expected_scenario_count:
        print(
            f"FAIL: Maker produced {maker_summary['scenario_count']} scenarios, expected {expected_scenario_count}"
        )
        passed = False

    checker_reviews = load_jsonl(checker_reviews_path)
    if len(checker_reviews) != expected_scenario_count:
        print(
            f"FAIL: Checker produced {len(checker_reviews)} reviews, expected {expected_scenario_count}"
        )
        passed = False

    # --- Governance Signals ---
    # Compute governance signals from the smoke test's run artifacts so the
    # release-governance job always has a current signal (even if no real runs exist).
    signals = compute_governance_signals(WORK / "runs")
    write_signals_report(signals, WORK / "runs" / "governance_signals.json")

    if passed:
        print(
            f"PASS: smoke test passed — "
            f"{maker_summary['processed_rule_count']} rules, "
            f"{maker_summary['scenario_count']} scenarios, "
            f"{len(checker_reviews)} checker reviews"
        )

    return passed


if __name__ == "__main__":
    try:
        ok = run_smoke()
    finally:
        shutil.rmtree(WORK, ignore_errors=True)
    sys.exit(0 if ok else 1)
