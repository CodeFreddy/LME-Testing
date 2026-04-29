from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_project_config
from .storage import ensure_dir, timestamp_slug
from .schemas import init_schema_config_dir
from .pipelines import run_bdd_pipeline, run_checker_pipeline, run_maker_pipeline, run_planner_pipeline, run_rewrite_pipeline
from .bdd_export import run_bdd_export
from .reporting import generate_html_report
from .step_registry import extract_steps_from_normalized_bdd, extract_steps_from_python_step_defs, extract_steps_from_step_defs, compute_step_gaps, compute_step_matches, render_step_visibility_report, StepInventory, MatchReport
from .signals import compute_governance_signals, write_signals_report
from .human_review import generate_human_review_page
from .im_hk_v14_role_review import write_review_package
from .mvp_document_readiness import write_document_readiness_package
from .logging_utils import configure_logging
from .review_session import ReviewSessionManager, serve_review_session
from .workflow_session import choose_start_step, discover_workflow_artifacts, start_workflow_session


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run maker/checker pipelines against governed rule artifacts."
    )
    parser.add_argument(
        "--config",
        default="config/llm_profiles.json",
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
    maker.add_argument("--batch-size", type=int, default=4)
    maker.add_argument("--resume-from", default=None)

    checker = subparsers.add_parser(
        "checker",
        help="Review maker outputs and compute requirement coverage.",
    )
    checker.add_argument("--rules", default="artifacts/lme_rules_v2_2/semantic_rules.json")
    checker.add_argument("--cases", required=True)
    checker.add_argument("--output-dir", default="runs/checker")
    checker.add_argument("--limit", type=int, default=None)
    checker.add_argument("--batch-size", type=int, default=4)
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
    bdd.add_argument(
        "--human-scripts-edits",
        default=None,
        help="Path to human_scripts_edits_latest.json from a review session. "
             "When provided, step definitions reflect human-edited and gap steps.",
    )

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

    signals = subparsers.add_parser(
        "governance-signals",
        help="Compute governance signals from run artifacts.",
    )
    signals.add_argument(
        "--repo-root",
        default=".",
        help="Path to the repository root (default: current directory).",
    )
    signals.add_argument(
        "--runs-dir",
        default=None,
        help="Path to runs directory (default: <repo-root>/runs). Use this to analyze runs from a different location.",
    )
    signals.add_argument(
        "--output",
        default="runs/governance_signals.json",
        help="Output path for the signals JSON file.",
    )

    rewrite = subparsers.add_parser(
        "rewrite",
        help="Regenerate maker outputs for rules flagged by human review.",
    )
    rewrite.add_argument("--rules", default="artifacts/lme_rules_v2_2/semantic_rules.json")
    rewrite.add_argument("--cases", required=True)
    rewrite.add_argument("--checker-reviews", required=True)
    rewrite.add_argument("--human-reviews", required=True)
    rewrite.add_argument("--output-dir", default="runs/rewrite")
    rewrite.add_argument("--limit", type=int, default=None)
    rewrite.add_argument("--batch-size", type=int, default=4)
    rewrite.add_argument(
        "--human-scripts-edits",
        default=None,
        help="Path to human_scripts_edits_latest.json. When provided, applies "
             "human step edits when rendering step definitions.",
    )

    human_review = subparsers.add_parser(
        "human-review",
        help="Generate a minimal local HTML page for human audit and export of review decisions.",
    )
    human_review.add_argument("--maker-cases", required=True)
    human_review.add_argument("--checker-reviews", required=True)
    human_review.add_argument("--output-html", required=True)

    review_session = subparsers.add_parser(
        "review-session",
        help="Start a local review session server that saves reviews and runs rewrite/checker/report.",
    )
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
    review_session.add_argument("--normalized-bdd", default=None, help="Path to normalized_bdd.jsonl to link into the session.")
    review_session.add_argument("--step-registry", default=None, help="Path to step_visibility.json from step-registry pipeline.")

    workflow_session = subparsers.add_parser(
        "workflow-session",
        help="Run the end-to-end workflow and auto-start review-session after first checker output.",
    )
    workflow_session.add_argument("--source", default="docs/materials/LME_Matching_Rules_Aug_2022.md")
    workflow_session.add_argument("--artifacts-dir", default="artifacts/lme_rules_v2_2")
    workflow_session.add_argument("--maker-cases", default=None)
    workflow_session.add_argument("--maker-summary", default=None)
    workflow_session.add_argument("--checker-reviews", default=None)
    workflow_session.add_argument("--checker-summary", default=None)
    workflow_session.add_argument("--coverage-report", default=None)
    workflow_session.add_argument(
        "--start-step",
        choices=["extract", "semantic", "maker", "checker", "review"],
        default=None,
    )
    workflow_session.add_argument("--output-dir", default="runs/review_sessions")
    workflow_session.add_argument("--maker-batch-size", type=int, default=1)
    workflow_session.add_argument("--checker-batch-size", type=int, default=1)
    workflow_session.add_argument("--host", default="127.0.0.1")
    workflow_session.add_argument("--port", type=int, default=8765)
    workflow_session.add_argument("--write-page-text", action="store_true")

    im_hk_v14_role_review = subparsers.add_parser(
        "im-hk-v14-role-review",
        help="Generate the S2-F1 HKv14 role-friendly impact decision review package.",
    )
    im_hk_v14_role_review.add_argument(
        "--diff-report",
        default="evidence/im_hk_v14_diff/im_hk_v13_to_v14_diff.json",
        help="Path to HKv13 -> HKv14 deterministic diff JSON.",
    )
    im_hk_v14_role_review.add_argument(
        "--mapping",
        default="docs/planning/im_hk_v14_downstream_treatment_mapping.md",
        help="Path to HKv14 downstream treatment mapping Markdown.",
    )
    im_hk_v14_role_review.add_argument(
        "--output-dir",
        default="runs/im_hk_v14/review_decisions",
        help="Output root for decision_record.json, decision_summary.md, and review.html.",
    )
    im_hk_v14_role_review.add_argument(
        "--reviewer-role",
        default="BA",
        choices=["BA", "QA Lead", "Automation Lead", "PM / Release Owner"],
        help="Default reviewer role to seed into the decision record.",
    )
    im_hk_v14_role_review.add_argument("--reviewer-name", default="")
    im_hk_v14_role_review.add_argument(
        "--decision",
        default="defer",
        choices=["approve", "reject", "defer", "request_rework"],
        help="Default decision to seed into the decision record.",
    )
    im_hk_v14_role_review.add_argument("--rationale", default="")
    im_hk_v14_role_review.add_argument("--comments", default="")

    mvp_document_readiness = subparsers.add_parser(
        "mvp-document-readiness",
        help="Generate the S2-F2 deterministic MVP document readiness registry.",
    )
    mvp_document_readiness.add_argument(
        "--previous-spec",
        default="docs/materials/Initial Margin Calculation Guide HKv13.pdf",
        help="Path to the previous Function Spec stand-in document.",
    )
    mvp_document_readiness.add_argument(
        "--current-spec",
        default="docs/materials/Initial Margin Calculation Guide HKv14.pdf",
        help="Path to the current Function Spec stand-in document.",
    )
    mvp_document_readiness.add_argument(
        "--test-plan",
        default=None,
        help="Optional path to a real Test Plan input. If omitted, the registry keeps the Test Plan placeholder blocker.",
    )
    mvp_document_readiness.add_argument("--test-plan-title", default="MVP Test Plan")
    mvp_document_readiness.add_argument("--test-plan-version", default="not_available")
    mvp_document_readiness.add_argument(
        "--regression-pack-index",
        default=None,
        help="Optional path to a real Regression Pack Index input. If omitted, the registry keeps the placeholder blocker.",
    )
    mvp_document_readiness.add_argument("--regression-pack-index-title", default="MVP Regression Pack Index")
    mvp_document_readiness.add_argument("--regression-pack-index-version", default="not_available")
    mvp_document_readiness.add_argument(
        "--output-dir",
        default="evidence/mvp_document_readiness",
        help="Output root for document_readiness.json and document_readiness_summary.md.",
    )

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

    if args.command == "governance-signals":
        repo_root = Path(args.repo_root).resolve()
        output_path = Path(args.output)
        runs_dir = Path(args.runs_dir).resolve() if args.runs_dir else None
        signals = compute_governance_signals(repo_root, runs_dir=runs_dir)
        write_signals_report(signals, output_path)
        result = {
            "output_path": str(output_path),
            "schema_failure_rate": signals.schema_signals.failure_rate,
            "checker_instability_rate": signals.checker_instability_signals.instability_rate,
            "coverage_percent": signals.coverage_signals.latest_coverage_percent,
            "step_binding_rate": signals.step_binding_signals.binding_rate,
            "coverage_trend": signals.coverage_signals.coverage_trend,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "im-hk-v14-role-review":
        result = write_review_package(
            diff_report_path=Path(args.diff_report),
            mapping_path=Path(args.mapping),
            output_dir=Path(args.output_dir),
            reviewer_role=args.reviewer_role,
            reviewer_name=args.reviewer_name,
            decision=args.decision,
            rationale=args.rationale,
            comments=args.comments,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command == "mvp-document-readiness":
        result = write_document_readiness_package(
            output_dir=Path(args.output_dir),
            previous_spec_path=Path(args.previous_spec),
            current_spec_path=Path(args.current_spec),
            test_plan_path=Path(args.test_plan) if args.test_plan else None,
            test_plan_title=args.test_plan_title,
            test_plan_version=args.test_plan_version,
            regression_pack_index_path=Path(args.regression_pack_index) if args.regression_pack_index else None,
            regression_pack_index_title=args.regression_pack_index_title,
            regression_pack_index_version=args.regression_pack_index_version,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    config = load_project_config(Path(args.config))
    init_schema_config_dir(config.config_dir)

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
            human_scripts_edits_path=Path(args.human_scripts_edits) if args.human_scripts_edits else None,
        )
    elif args.command == "bdd-export":
        result = run_bdd_export(
            maker_cases_path=Path(args.cases),
            output_dir=Path(args.output_dir),
        )
    elif args.command == "step-registry":
        normalized_bdd_path = Path(args.bdd_cases)
        output_dir = Path(args.output_dir)
        run_id = timestamp_slug()
        run_dir = ensure_dir(output_dir / run_id)
        output_path = run_dir / "step_visibility.json"

        bdd_inventory = extract_steps_from_normalized_bdd(normalized_bdd_path)

        # Default to the src-layout canonical step library.
        step_defs_path = Path(args.step_defs) if args.step_defs else Path("src/lme_testing/step_library.py")
        if step_defs_path.suffix == ".py":
            library_inventory = extract_steps_from_python_step_defs(step_defs_path)
        else:
            library_inventory = extract_steps_from_step_defs(step_defs_path)

        report = compute_step_matches(
            bdd_inventory,
            library_inventory,
            candidate_top_k=args.candidate_top_k,
            similarity_threshold=args.similarity_threshold,
        )
        render_step_visibility_report(bdd_inventory, report, output_path)

        result = {
            "run_id": run_id,
            "output_path": str(output_path),
            "total_steps": bdd_inventory.total_steps,
            "unique_bdd_patterns": report.unique_bdd_patterns,
            "exact_matches": report.exact_matches,
            "parameterized_matches": report.parameterized_matches,
            "candidates": len(report.candidates),
            "unmatched": report.unmatched,
            "reuse_score_count": len(report.reuse_scores),
        }
    elif args.command == "rewrite":
        output_dir = Path(args.output_dir)
        log_path = configure_logging("rewrite", output_dir / "logs")
        print(json.dumps({"status": "starting", "log_path": str(log_path)}, ensure_ascii=False, indent=2))
        result = run_rewrite_pipeline(
            config=config,
            semantic_rules_path=Path(args.rules),
            maker_cases_path=Path(args.cases),
            checker_reviews_path=Path(args.checker_reviews),
            human_reviews_path=Path(args.human_reviews),
            output_dir=output_dir,
            limit=args.limit,
            batch_size=args.batch_size,
            human_scripts_edits_path=Path(args.human_scripts_edits) if args.human_scripts_edits else None,
        )
    elif args.command == "human-review":
        output_html_path = Path(args.output_html)
        log_path = configure_logging("human-review", output_html_path.resolve().parent / "logs")
        print(json.dumps({"status": "starting", "log_path": str(log_path)}, ensure_ascii=False, indent=2))
        result = generate_human_review_page(
            maker_cases_path=Path(args.maker_cases),
            checker_reviews_path=Path(args.checker_reviews),
            output_html_path=output_html_path,
        )
    elif args.command == "review-session":
        output_dir = Path(args.output_dir)
        log_path = configure_logging("review-session", output_dir / "logs")
        print(json.dumps({"status": "starting", "log_path": str(log_path)}, ensure_ascii=False, indent=2))
        manager = ReviewSessionManager(
            config=config,
            rules_path=Path(args.rules),
            maker_cases_path=Path(args.cases),
            checker_reviews_path=Path(args.checker_reviews),
            output_root=output_dir,
            repo_root=Path.cwd(),
            rewrite_batch_size=args.rewrite_batch_size,
            checker_batch_size=args.checker_batch_size,
            initial_maker_summary_path=Path(args.maker_summary) if args.maker_summary else None,
            initial_checker_summary_path=Path(args.checker_summary) if args.checker_summary else None,
            initial_coverage_report_path=Path(args.coverage_report) if args.coverage_report else None,
            normalized_bdd_path=Path(args.normalized_bdd) if args.normalized_bdd else None,
            step_registry_path=Path(args.step_registry) if args.step_registry else None,
        )
        server, url = serve_review_session(manager=manager, host=args.host, port=args.port)
        print(json.dumps({"session_id": manager.session_id, "url": url, "output_dir": str(manager.session_dir)}, ensure_ascii=False, indent=2))
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.shutdown()
        return 0
    elif args.command == "workflow-session":
        output_dir = Path(args.output_dir)
        log_path = configure_logging("workflow-session", output_dir / "logs")
        print(json.dumps({"status": "starting", "log_path": str(log_path)}, ensure_ascii=False, indent=2))
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
        print(json.dumps({"status": "running_step", "step": start_step}, ensure_ascii=False, indent=2))
        result = start_workflow_session(
            config=config,
            repo_root=Path.cwd(),
            artifacts=artifacts,
            output_root=output_dir,
            host=args.host,
            port=args.port,
            start_step=start_step,
            maker_batch_size=args.maker_batch_size,
            checker_batch_size=args.checker_batch_size,
            write_page_text=args.write_page_text,
        )
        if result is None:
            print("[workflow] Workflow aborted by user.", flush=True)
            return 1
        server, url, manager = result
        print(json.dumps({"session_id": manager.session_id, "start_step": start_step, "url": url, "output_dir": str(manager.session_dir)}, ensure_ascii=False, indent=2))
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.shutdown()
        return 0

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

