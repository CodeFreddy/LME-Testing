from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_project_config
from .pipelines import run_bdd_pipeline, run_checker_pipeline, run_maker_pipeline, run_planner_pipeline
from .bdd_export import run_bdd_export
from .reporting import generate_html_report
from .step_registry import extract_steps_from_normalized_bdd, extract_steps_from_step_defs, compute_step_gaps, compute_step_matches, render_step_visibility_report, StepInventory, MatchReport


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

    planner = subparsers.add_parser(
        "planner",
        help="Generate test planning artifacts from semantic rules (Phase 2).",
    )
    planner.add_argument("--input", default="artifacts/lme_rules_v2_2/semantic_rules.json")
    planner.add_argument("--output-dir", default="runs/planner")
    planner.add_argument("--limit", type=int, default=None)
    planner.add_argument("--batch-size", type=int, default=4)
    planner.add_argument("--resume-from", default=None)

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

    bdd = subparsers.add_parser(
        "bdd",
        help="Generate refined BDD/Gherkin from maker test cases.",
    )
    bdd.add_argument("--cases", required=True, help="Path to maker_cases.jsonl")
    bdd.add_argument("--output-dir", default="runs/bdd")
    bdd.add_argument("--limit", type=int, default=None)
    bdd.add_argument("--batch-size", type=int, default=4)
    bdd.add_argument("--resume-from", default=None)

    bdd_export = subparsers.add_parser(
        "bdd-export",
        help="Export BDD feature files and step definitions from maker cases (template-based, no LLM).",
    )
    bdd_export.add_argument("--cases", required=True, help="Path to maker_cases.jsonl")
    bdd_export.add_argument("--output-dir", default="runs/bdd-export")

    step_registry = subparsers.add_parser(
        "step-registry",
        help="Generate step visibility report from normalized BDD output (Phase 3 Gate 1).",
    )
    step_registry.add_argument(
        "--bdd-cases",
        required=True,
        help="Path to normalized_bdd.jsonl from run_bdd_pipeline.",
    )
    step_registry.add_argument(
        "--step-defs",
        default=None,
        help="Path to existing Ruby step definitions file (optional). "
             "If provided, computes gap analysis against existing library.",
    )
    step_registry.add_argument(
        "--output-dir",
        default="runs/step-registry",
        help="Output directory for step visibility report.",
    )
    step_registry.add_argument(
        "--candidate-top-k",
        type=int,
        default=3,
        help="Number of candidate suggestions per unmatched step (default: 3).",
    )
    step_registry.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.3,
        help="Minimum similarity score to surface a candidate (default: 0.3).",
    )

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

    if args.command == "planner":
        result = run_planner_pipeline(
            config=config,
            semantic_rules_path=Path(args.input),
            output_dir=Path(args.output_dir),
            limit=args.limit,
            batch_size=args.batch_size,
            resume_from=Path(args.resume_from) if args.resume_from else None,
        )
    elif args.command == "maker":
        result = run_maker_pipeline(
            config=config,
            semantic_rules_path=Path(args.input),
            output_dir=Path(args.output_dir),
            limit=args.limit,
            batch_size=args.batch_size,
            resume_from=Path(args.resume_from) if args.resume_from else None,
        )
    elif args.command == "checker":
        result = run_checker_pipeline(
            config=config,
            semantic_rules_path=Path(args.rules),
            maker_cases_path=Path(args.cases),
            output_dir=Path(args.output_dir),
            limit=args.limit,
            batch_size=args.batch_size,
            resume_from=Path(args.resume_from) if args.resume_from else None,
        )
    elif args.command == "bdd":
        result = run_bdd_pipeline(
            config=config,
            maker_cases_path=Path(args.cases),
            output_dir=Path(args.output_dir),
            limit=args.limit,
            batch_size=args.batch_size,
            resume_from=Path(args.resume_from) if args.resume_from else None,
        )
    elif args.command == "bdd-export":
        result = run_bdd_export(
            maker_cases_path=Path(args.cases),
            output_dir=Path(args.output_dir),
        )
    elif args.command == "step-registry":
        normalized_bdd_path = Path(args.bdd_cases)
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "step_visibility.json"

        bdd_inventory = extract_steps_from_normalized_bdd(normalized_bdd_path)

        library_inventory = StepInventory()
        if args.step_defs:
            library_inventory = extract_steps_from_step_defs(Path(args.step_defs))

        report = compute_step_matches(
            bdd_inventory,
            library_inventory,
            candidate_top_k=args.candidate_top_k,
            similarity_threshold=args.similarity_threshold,
        )
        render_step_visibility_report(bdd_inventory, report, output_path)

        result = {
            "output_path": str(output_path),
            "total_steps": bdd_inventory.total_steps,
            "unique_bdd_patterns": report.unique_bdd_patterns,
            "exact_matches": report.exact_matches,
            "parameterized_matches": report.parameterized_matches,
            "candidates": len(report.candidates),
            "unmatched": report.unmatched,
            "reuse_score_count": len(report.reuse_scores),
        }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0
