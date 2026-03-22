from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_project_config
from .pipelines import run_checker_pipeline, run_maker_pipeline
from .reporting import generate_html_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run maker/checker pipelines against LME rule artifacts."
    )
    parser.add_argument(
        "--config",
        default="config/llm_profiles.example.json",
        help="Path to the project LLM config file.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    maker = subparsers.add_parser(
        "maker",
        help="Generate structured BDD-style test cases from semantic rules.",
    )
    maker.add_argument("--input", default="artifacts/lme_rules_v2_2/semantic_rules.json")
    maker.add_argument("--output-dir", default="runs/maker")
    maker.add_argument("--limit", type=int, default=None)
    maker.add_argument("--batch-size", type=int, default=1)
    maker.add_argument("--resume-from", default=None)

    checker = subparsers.add_parser(
        "checker",
        help="Review maker outputs and compute requirement coverage.",
    )
    checker.add_argument("--rules", default="artifacts/lme_rules_v2_2/semantic_rules.json")
    checker.add_argument("--cases", required=True)
    checker.add_argument("--output-dir", default="runs/checker")
    checker.add_argument("--limit", type=int, default=None)
    checker.add_argument("--batch-size", type=int, default=1)
    checker.add_argument("--resume-from", default=None)

    report = subparsers.add_parser(
        "report",
        help="Render maker/checker outputs into a human-readable HTML report.",
    )
    report.add_argument("--maker-cases", required=True)
    report.add_argument("--checker-reviews", required=True)
    report.add_argument("--maker-summary", required=True)
    report.add_argument("--checker-summary", required=True)
    report.add_argument("--coverage-report", required=True)
    report.add_argument("--output-html", required=True)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "report":
        result = generate_html_report(
            maker_cases_path=Path(args.maker_cases),
            checker_reviews_path=Path(args.checker_reviews),
            maker_summary_path=Path(args.maker_summary),
            checker_summary_path=Path(args.checker_summary),
            coverage_report_path=Path(args.coverage_report),
            output_html_path=Path(args.output_html),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    config = load_project_config(Path(args.config))

    if args.command == "maker":
        result = run_maker_pipeline(
            config=config,
            semantic_rules_path=Path(args.input),
            output_dir=Path(args.output_dir),
            limit=args.limit,
            batch_size=args.batch_size,
            resume_from=Path(args.resume_from) if args.resume_from else None,
        )
    else:
        result = run_checker_pipeline(
            config=config,
            semantic_rules_path=Path(args.rules),
            maker_cases_path=Path(args.cases),
            output_dir=Path(args.output_dir),
            limit=args.limit,
            batch_size=args.batch_size,
            resume_from=Path(args.resume_from) if args.resume_from else None,
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0
