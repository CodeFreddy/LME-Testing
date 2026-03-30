from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_project_config
from .human_review import generate_human_review_page
from .logging_utils import configure_logging
from .pipelines import run_checker_pipeline, run_maker_pipeline, run_rewrite_pipeline
from .reporting import generate_html_report
from .review_session import ReviewSessionManager, serve_review_session
from .workflow_session import choose_start_step, discover_workflow_artifacts, start_workflow_session


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

    maker = subparsers.add_parser("maker", help="Generate structured BDD-style test cases from semantic rules.")
    maker.add_argument("--input", default="artifacts/lme_rules_v2_2/semantic_rules.json")
    maker.add_argument("--output-dir", default="runs/maker")
    maker.add_argument("--limit", type=int, default=None)
    maker.add_argument("--batch-size", type=int, default=1)
    maker.add_argument("--resume-from", default=None)

    checker = subparsers.add_parser("checker", help="Review maker outputs and compute requirement coverage.")
    checker.add_argument("--rules", default="artifacts/lme_rules_v2_2/semantic_rules.json")
    checker.add_argument("--cases", required=True)
    checker.add_argument("--output-dir", default="runs/checker")
    checker.add_argument("--limit", type=int, default=None)
    checker.add_argument("--batch-size", type=int, default=1)
    checker.add_argument("--resume-from", default=None)

    rewrite = subparsers.add_parser("rewrite", help="Regenerate maker outputs for rules flagged by human review.")
    rewrite.add_argument("--rules", default="artifacts/lme_rules_v2_2/semantic_rules.json")
    rewrite.add_argument("--cases", required=True)
    rewrite.add_argument("--checker-reviews", required=True)
    rewrite.add_argument("--human-reviews", required=True)
    rewrite.add_argument("--output-dir", default="runs/rewrite")
    rewrite.add_argument("--limit", type=int, default=None)
    rewrite.add_argument("--batch-size", type=int, default=1)

    report = subparsers.add_parser("report", help="Render maker/checker outputs into a human-readable HTML report.")
    report.add_argument("--maker-cases", required=True)
    report.add_argument("--checker-reviews", required=True)
    report.add_argument("--maker-summary", required=True)
    report.add_argument("--checker-summary", required=True)
    report.add_argument("--coverage-report", required=True)
    report.add_argument("--output-html", required=True)

    human_review = subparsers.add_parser("human-review", help="Generate a minimal local HTML page for human audit and export of review decisions.")
    human_review.add_argument("--maker-cases", required=True)
    human_review.add_argument("--checker-reviews", required=True)
    human_review.add_argument("--output-html", required=True)

    review_session = subparsers.add_parser("review-session", help="Start a local review session server that saves reviews and runs rewrite/checker/report.")
    review_session.add_argument("--rules", default="artifacts/lme_rules_v2_2/semantic_rules.json")
    review_session.add_argument("--cases", required=True)
    review_session.add_argument("--checker-reviews", required=True)
    review_session.add_argument("--maker-summary", default=None)
    review_session.add_argument("--checker-summary", default=None)
    review_session.add_argument("--coverage-report", default=None)
    review_session.add_argument("--output-dir", default="runs/review_sessions")
    review_session.add_argument("--rewrite-batch-size", type=int, default=1)
    review_session.add_argument("--checker-batch-size", type=int, default=1)
    review_session.add_argument("--host", default="127.0.0.1")
    review_session.add_argument("--port", type=int, default=8765)

    workflow_session = subparsers.add_parser("workflow-session", help="Run the end-to-end workflow and auto-start review-session after first checker output.")
    workflow_session.add_argument("--source", default="docs/materials/LME_Matching_Rules_Aug_2022.md")
    workflow_session.add_argument("--artifacts-dir", default="artifacts/lme_rules_v2_2")
    workflow_session.add_argument("--maker-cases", default=None)
    workflow_session.add_argument("--maker-summary", default=None)
    workflow_session.add_argument("--checker-reviews", default=None)
    workflow_session.add_argument("--checker-summary", default=None)
    workflow_session.add_argument("--coverage-report", default=None)
    workflow_session.add_argument("--start-step", choices=["extract", "semantic", "maker", "checker", "review"], default=None)
    workflow_session.add_argument("--output-dir", default="runs/review_sessions")
    workflow_session.add_argument("--maker-batch-size", type=int, default=1)
    workflow_session.add_argument("--checker-batch-size", type=int, default=1)
    workflow_session.add_argument("--host", default="127.0.0.1")
    workflow_session.add_argument("--port", type=int, default=8765)
    workflow_session.add_argument("--write-page-text", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    command_name = args.command.replace("-", "_")
    if args.command == "report":
        log_path = configure_logging(command_name, Path(args.output_html).resolve().parent / "logs")
    elif args.command == "human-review":
        log_path = configure_logging(command_name, Path(args.output_html).resolve().parent / "logs")
    else:
        base_dir = Path(getattr(args, "output_dir", "runs")).resolve()
        log_path = configure_logging(command_name, base_dir / "logs")
    print(json.dumps({"log_path": str(log_path)}, ensure_ascii=False, indent=2))

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

    if args.command == "human-review":
        result = generate_human_review_page(
            maker_cases_path=Path(args.maker_cases),
            checker_reviews_path=Path(args.checker_reviews),
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
    elif args.command == "rewrite":
        result = run_rewrite_pipeline(
            config=config,
            semantic_rules_path=Path(args.rules),
            maker_cases_path=Path(args.cases),
            checker_reviews_path=Path(args.checker_reviews),
            human_reviews_path=Path(args.human_reviews),
            output_dir=Path(args.output_dir),
            limit=args.limit,
            batch_size=args.batch_size,
        )
    elif args.command == "review-session":
        manager = ReviewSessionManager(
            config=config,
            rules_path=Path(args.rules),
            maker_cases_path=Path(args.cases),
            checker_reviews_path=Path(args.checker_reviews),
            output_root=Path(args.output_dir),
            repo_root=Path.cwd(),
            rewrite_batch_size=args.rewrite_batch_size,
            checker_batch_size=args.checker_batch_size,
            initial_maker_summary_path=Path(args.maker_summary) if args.maker_summary else None,
            initial_checker_summary_path=Path(args.checker_summary) if args.checker_summary else None,
            initial_coverage_report_path=Path(args.coverage_report) if args.coverage_report else None,
        )
        server, url = serve_review_session(manager=manager, host=args.host, port=args.port)
        print(json.dumps({"session_id": manager.session_id, "url": url, "output_dir": str(manager.session_dir)}, ensure_ascii=False, indent=2))
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.shutdown()
        return 0
    else:
        artifacts = discover_workflow_artifacts(
            repo_root=Path.cwd(),
            source_path=Path(args.source),
            artifacts_dir=Path(args.artifacts_dir),
            maker_cases_path=Path(args.maker_cases) if args.maker_cases else None,
            maker_summary_path=Path(args.maker_summary) if args.maker_summary else None,
            checker_reviews_path=Path(args.checker_reviews) if args.checker_reviews else None,
            checker_summary_path=Path(args.checker_summary) if args.checker_summary else None,
            coverage_report_path=Path(args.coverage_report) if args.coverage_report else None,
        )
        start_step = choose_start_step(artifacts, args.start_step)
        server, url, manager = start_workflow_session(
            config=config,
            repo_root=Path.cwd(),
            artifacts=artifacts,
            output_root=Path(args.output_dir),
            host=args.host,
            port=args.port,
            start_step=start_step,
            maker_batch_size=args.maker_batch_size,
            checker_batch_size=args.checker_batch_size,
            write_page_text=args.write_page_text,
        )
        print(json.dumps({"session_id": manager.session_id, "start_step": start_step, "url": url, "output_dir": str(manager.session_dir)}, ensure_ascii=False, indent=2))
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.shutdown()
        return 0

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0
