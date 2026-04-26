#!/usr/bin/env python3
"""Checker Stability Benchmark

Runs the checker pipeline twice on the same baseline input and produces a
machine-readable stability report identifying inconsistent verdicts across runs.

Usage:
    # Stub run (fast, no API cost)
    python scripts/checker_stability.py --cases runs/maker/<run_id>/maker_cases.jsonl
                                        --rules artifacts/poc_two_rules/semantic_rules.json
                                        --output runs/checker-stability/<run_id>/stability_report.json

    # Real API run (MiniMax)
    python scripts/checker_stability.py --cases runs/maker/<run_id>/maker_cases.jsonl
                                        --rules artifacts/poc_two_rules/semantic_rules.json
                                        --output runs/stability_real/
                                        --config config/llm_profiles.minimax.json

Exit codes:
    0 = stability check complete (unstable cases reported in output)
    1 = check failed due to error
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

# Ensure local src-layout packages are importable when run as a script.
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from lme_testing.config import ProjectConfig, ProviderConfig, RoleDefaults, load_project_config
from lme_testing.pipelines import run_checker_pipeline
from lme_testing.storage import load_json, load_jsonl, write_json


def make_stub_config() -> ProjectConfig:
    """Build an in-process config for stability runs (no real API calls)."""
    provider = ProviderConfig(
        name="stub",
        provider_type="openai_compatible",
        model="stub-model",
        base_url="https://stub.example.com/v1",
        api_key="stub",
    )
    return ProjectConfig(
        providers={"stub": provider},
        roles={"maker": "stub", "checker": "stub"},
        output_root=Path(tempfile.gettempdir()) / "lme_stability",
        maker_defaults=RoleDefaults(),
        checker_defaults=RoleDefaults(),
    )


class StubResponse:
    """A deterministic stub response that returns pre-defined checker output.

    Each `generate` call returns the next response from `checker_responses`
    in sequence. Responses are pre-built by `build_stub_responses` to match
    the exact case_ids expected by each batch call from run_checker_pipeline.
    """

    def __init__(self, checker_responses: list[dict]):
        self.checker_responses = checker_responses
        self.call_index = 0

    def generate(self, system_prompt: str, user_prompt: str):
        import json

        if self.call_index >= len(self.checker_responses):
            raise RuntimeError(
                f"StubResponse exhausted: call {self.call_index + 1} but only "
                f"{len(self.checker_responses)} responses configured"
            )
        response_payload = self.checker_responses[self.call_index]
        self.call_index += 1
        return type(
            "Response",
            (),
            {
                "content": json.dumps(response_payload, ensure_ascii=False),
                "raw_response": response_payload,
            },
        )()


def build_stub_responses(maker_records: list[dict]) -> list[dict]:
    """Build deterministic stub responses for checker stability testing.

    Returns one response dict per checker API call (one per scenario with
    batch_size=1). Each response contains exactly one result matching the
    expected case_id for that call.
    """
    responses = []
    for record in maker_records:
        sid = record["semantic_rule_id"]
        scenarios = record.get("scenarios", [])
        for scenario in scenarios:
            cid = scenario.get("scenario_id", "")
            case_type = scenario.get("case_type", "positive")
            responses.append({
                "results": [{
                    "case_id": cid,
                    "semantic_rule_id": sid,
                    "case_type": case_type,
                    "case_type_accepted": True,
                    "coverage_relevance": "direct",
                    "overall_status": "pass",
                    "blocking_findings_count": 0,
                    "is_blocking": False,
                    "scores": {
                        "evidence_consistency": 5,
                        "requirement_coverage": 5,
                        "test_design_quality": 5,
                        "non_hallucination": 5,
                    },
                    "findings": [],
                    "coverage_assessment": {
                        "status": "covered",
                        "reason": "deterministic stub",
                        "missing_aspects": [],
                    },
                }]
            })
    return responses


def _compare_reviews(run_a: list[dict], run_b: list[dict]) -> dict:
    """Compare two checker review lists and return instability report."""
    index_a = {r["case_id"]: r for r in run_a}
    index_b = {r["case_id"]: r for r in run_b}
    all_ids = set(index_a.keys()) | set(index_b.keys())

    unstable_cases: list[dict] = []
    stable_cases: list[str] = []
    missing_in_run_a: list[str] = []
    missing_in_run_b: list[str] = []

    for case_id in sorted(all_ids):
        if case_id not in index_a:
            missing_in_run_a.append(case_id)
            continue
        if case_id not in index_b:
            missing_in_run_b.append(case_id)
            continue

        a = index_a[case_id]
        b = index_b[case_id]
        diffs: list[dict] = []

        # Compare booleans
        for field in ("case_type_accepted", "is_blocking"):
            if a.get(field) != b.get(field):
                diffs.append(
                    {
                        "field": field,
                        "run_a": a.get(field),
                        "run_b": b.get(field),
                    }
                )

        # Compare strings
        for field in ("coverage_relevance", "overall_status"):
            if a.get(field) != b.get(field):
                diffs.append(
                    {
                        "field": field,
                        "run_a": a.get(field),
                        "run_b": b.get(field),
                    }
                )

        # Compare scores
        scores_a = a.get("scores", {})
        scores_b = b.get("scores", {})
        score_diffs: list[dict] = []
        for score_key in set(scores_a.keys()) | set(scores_b.keys()):
            val_a = scores_a.get(score_key)
            val_b = scores_b.get(score_key)
            if val_a is None or val_b is None:
                continue
            if val_a != val_b:
                score_diffs.append(
                    {
                        "score": score_key,
                        "run_a": val_a,
                        "run_b": val_b,
                        "delta": abs(val_a - val_b),
                    }
                )
        if score_diffs:
            diffs.append({"field": "scores", "differences": score_diffs})

        # Compare coverage_assessment.status
        status_a = a.get("coverage_assessment", {}).get("status")
        status_b = b.get("coverage_assessment", {}).get("status")
        if status_a != status_b:
            diffs.append(
                {
                    "field": "coverage_assessment.status",
                    "run_a": status_a,
                    "run_b": status_b,
                }
            )

        if diffs:
            unstable_cases.append(
                {
                    "case_id": case_id,
                    "semantic_rule_id": a.get("semantic_rule_id"),
                    "differences": diffs,
                }
            )
        else:
            stable_cases.append(case_id)

    return {
        "total_cases": len(all_ids),
        "stable_count": len(stable_cases),
        "unstable_count": len(unstable_cases),
        "missing_in_run_a": missing_in_run_a,
        "missing_in_run_b": missing_in_run_b,
        "stable_cases": stable_cases,
        "unstable_cases": unstable_cases,
    }


def run_stability_check(
    semantic_rules_path: Path,
    maker_cases_path: Path,
    output_path: Path,
    config,
    data_source: str = "stub",
) -> dict:
    """Run checker twice on same input and compare results.

    Args:
        semantic_rules_path: Path to semantic_rules.json
        maker_cases_path: Path to maker_cases.jsonl
        output_path: Output directory for the stability report
        config: ProjectConfig (stub or real)
        data_source: "stub" or "real_api" — written to stability_report.json
    """
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    maker_records = load_jsonl(maker_cases_path)

    run_a_dir = output_path / "run_a"
    run_b_dir = output_path / "run_b"
    run_a_dir.mkdir(parents=True, exist_ok=True)
    run_b_dir.mkdir(parents=True, exist_ok=True)

    if data_source == "stub":
        from unittest.mock import patch

        stub_responses = build_stub_responses(maker_records)

        def make_stub_provider(cfg):
            return StubResponse(stub_responses)

        # Run A
        with patch("lme_testing.pipelines.build_provider", make_stub_provider):
            summary_a = run_checker_pipeline(
                config=config,
                semantic_rules_path=semantic_rules_path,
                maker_cases_path=maker_cases_path,
                output_dir=run_a_dir,
                limit=None,
                batch_size=1,
                resume_from=None,
            )

        # Run B with fresh stub
        stub_responses_b = build_stub_responses(maker_records)

        def make_stub_provider_b(cfg):
            return StubResponse(stub_responses_b)

        with patch("lme_testing.pipelines.build_provider", make_stub_provider_b):
            summary_b = run_checker_pipeline(
                config=config,
                semantic_rules_path=semantic_rules_path,
                maker_cases_path=maker_cases_path,
                output_dir=run_b_dir,
                limit=None,
                batch_size=1,
                resume_from=None,
            )
    else:
        # Real API run — no patching, run B after 5-minute gap to avoid cache effects
        print(f"[{data_source}] Running checker (run A)...")
        summary_a = run_checker_pipeline(
            config=config,
            semantic_rules_path=semantic_rules_path,
            maker_cases_path=maker_cases_path,
            output_dir=run_a_dir,
            limit=None,
            batch_size=1,
            resume_from=None,
        )

        print(f"[{data_source}] Run A complete. Waiting 5 minutes before run B...")
        time.sleep(300)  # 5-minute gap to reduce cache correlation

        print(f"[{data_source}] Running checker (run B)...")
        summary_b = run_checker_pipeline(
            config=config,
            semantic_rules_path=semantic_rules_path,
            maker_cases_path=maker_cases_path,
            output_dir=run_b_dir,
            limit=None,
            batch_size=1,
            resume_from=None,
        )

    # Read results
    results_path_a = Path(summary_a["results_path"])
    results_path_b = Path(summary_b["results_path"])
    reviews_a = load_jsonl(results_path_a)
    reviews_b = load_jsonl(results_path_b)
    comparison = _compare_reviews(reviews_a, reviews_b)

    stability_report = {
        "data_source": data_source,
        "semantic_rules_path": str(semantic_rules_path),
        "maker_cases_path": str(maker_cases_path),
        "run_a_summary": {
            "run_id": summary_a["run_id"],
            "results_path": summary_a["results_path"],
            "review_count": len(reviews_a),
        },
        "run_b_summary": {
            "run_id": summary_b["run_id"],
            "results_path": summary_b["results_path"],
            "review_count": len(reviews_b),
        },
        "comparison": comparison,
    }

    write_json(output_path / "stability_report.json", stability_report)

    # Write human-readable summary to stdout
    print(f"Stable: {comparison['stable_count']}")
    print(f"Unstable: {comparison['unstable_count']}")

    if comparison["unstable_cases"]:
        print(f"\nUnstable cases:")
        for uc in comparison["unstable_cases"]:
            print(f"  {uc['case_id']} ({uc['semantic_rule_id']}):")
            for diff in uc["differences"]:
                print(f"    - {diff}")

    if comparison["missing_in_run_a"]:
        print(f"\nMissing in Run A: {comparison['missing_in_run_a']}")
    if comparison["missing_in_run_b"]:
        print(f"\nMissing in Run B: {comparison['missing_in_run_b']}")

    print(f"\nFull report: {output_path / 'stability_report.json'}")
    return stability_report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run checker stability benchmark: executes checker twice and compares results."
    )
    parser.add_argument(
        "--rules",
        default="artifacts/poc_two_rules/semantic_rules.json",
        help="Path to semantic_rules.json baseline.",
    )
    parser.add_argument(
        "--cases",
        required=True,
        help="Path to maker_cases.jsonl from a prior maker run.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output directory for stability report.",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to LLM config file. If provided, uses real API (maker+checker roles must be configured). If omitted, uses stub provider.",
    )
    args = parser.parse_args()

    rules_path = Path(args.rules)
    cases_path = Path(args.cases)
    output_path = Path(args.output)

    if not rules_path.exists():
        print(f"ERROR: rules file not found: {rules_path}")
        return 1
    if not cases_path.exists():
        print(f"ERROR: cases file not found: {cases_path}")
        return 1

    if args.config:
        config = load_project_config(Path(args.config))
        data_source = "real_api"
        print(f"Using real API config: {args.config}")
    else:
        config = make_stub_config()
        data_source = "stub"

    try:
        run_stability_check(rules_path, cases_path, output_path, config, data_source=data_source)
        return 0
    except Exception as e:
        print(f"ERROR: stability check failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

