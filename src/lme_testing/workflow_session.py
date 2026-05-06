from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from .config import ProjectConfig
from .pipelines import run_checker_pipeline, run_maker_pipeline
from .review_session import ReviewSessionManager, serve_review_session
from .storage import ensure_dir


WORKFLOW_STEPS = ["extract", "semantic", "maker", "checker", "review"]


@dataclass
class WorkflowArtifacts:
    source_path: Path
    artifacts_dir: Path
    atomic_rules_path: Path
    semantic_rules_path: Path
    maker_cases_path: Path | None = None
    maker_summary_path: Path | None = None
    checker_reviews_path: Path | None = None
    checker_summary_path: Path | None = None
    coverage_report_path: Path | None = None


# 发现当前仓库里可复用的产物，供 workflow-session 启动时选择从哪一步开始。
def discover_workflow_artifacts(
    repo_root: Path,
    source_path: Path,
    artifacts_dir: Path,
    maker_cases_path: Path | None = None,
    maker_summary_path: Path | None = None,
    checker_reviews_path: Path | None = None,
    checker_summary_path: Path | None = None,
    coverage_report_path: Path | None = None,
) -> WorkflowArtifacts:
    def latest_file(pattern: str) -> Path | None:
        matches = list(repo_root.glob(pattern))
        if not matches:
            return None
        return max(matches, key=lambda item: item.stat().st_mtime)

    atomic_rules = artifacts_dir / "atomic_rules.json"
    semantic_rules = artifacts_dir / "semantic_rules.json"
    return WorkflowArtifacts(
        source_path=source_path,
        artifacts_dir=artifacts_dir,
        atomic_rules_path=atomic_rules,
        semantic_rules_path=semantic_rules,
        maker_cases_path=maker_cases_path or latest_file("runs/**/maker_cases.jsonl"),
        maker_summary_path=maker_summary_path or latest_file("runs/**/maker/*/summary.json") or latest_file("runs/**/summary.json"),
        checker_reviews_path=checker_reviews_path or latest_file("runs/**/checker_reviews.jsonl"),
        checker_summary_path=checker_summary_path or latest_file("runs/**/checker/*/summary.json"),
        coverage_report_path=coverage_report_path or latest_file("runs/**/coverage_report.json"),
    )


def choose_start_step(artifacts: WorkflowArtifacts, requested: str | None) -> str:
    available: list[str] = ["extract"]
    if artifacts.atomic_rules_path.exists():
        available.append("semantic")
    if artifacts.semantic_rules_path.exists():
        available.append("maker")
    if artifacts.semantic_rules_path.exists() and artifacts.maker_cases_path and artifacts.maker_cases_path.exists():
        available.append("checker")
    if (
        artifacts.semantic_rules_path.exists()
        and artifacts.maker_cases_path and artifacts.maker_cases_path.exists()
        and artifacts.checker_reviews_path and artifacts.checker_reviews_path.exists()
        and artifacts.maker_summary_path and artifacts.maker_summary_path.exists()
        and artifacts.checker_summary_path and artifacts.checker_summary_path.exists()
        and artifacts.coverage_report_path and artifacts.coverage_report_path.exists()
    ):
        available.append("review")

    if requested:
        if requested not in available:
            raise ValueError(f"Requested start step '{requested}' is not available. Available: {', '.join(available)}")
        return requested

    print("Available workflow start steps:")
    for index, step in enumerate(available, start=1):
        print(f"  {index}. {step}")
    while True:
        raw = input(f"Choose start step [1-{len(available)}]: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(available):
            return available[int(raw) - 1]
        print("Invalid selection.")


# 从指定起点准备首轮 maker/checker/report，并自动拉起 review-session。
def start_workflow_session(
    config: ProjectConfig,
    repo_root: Path,
    artifacts: WorkflowArtifacts,
    output_root: Path,
    host: str,
    port: int,
    start_step: str,
    maker_batch_size: int,
    checker_batch_size: int,
    maker_concurrency: int = 1,
    checker_concurrency: int = 1,
    write_page_text: bool = False,
) -> tuple[object, str, ReviewSessionManager] | None:
    workflow_dir = ensure_dir(output_root / "workflow_bootstrap")
    current_artifacts = WorkflowArtifacts(**artifacts.__dict__)
    provider_out: list = []

    if WORKFLOW_STEPS.index(start_step) <= WORKFLOW_STEPS.index("extract"):
        print("[workflow] Step 1/4: Extracting rules from source...")
        _run_extract(repo_root, current_artifacts.source_path, current_artifacts.artifacts_dir, write_page_text=write_page_text)
    if WORKFLOW_STEPS.index(start_step) <= WORKFLOW_STEPS.index("semantic"):
        print("[workflow] Step 2/4: Normalizing to semantic rules...")
        _run_generate_semantic(repo_root, current_artifacts.artifacts_dir)

    if WORKFLOW_STEPS.index(start_step) <= WORKFLOW_STEPS.index("maker"):
        print(f"[workflow] Step 3/4: Running maker (API call, timeout={config.maker_defaults.timeout_seconds}s)...")
        maker_dir = ensure_dir(workflow_dir / "maker")
        try:
            maker_summary = run_maker_pipeline(
                config=config,
                semantic_rules_path=current_artifacts.semantic_rules_path,
                output_dir=maker_dir,
                limit=None,
                batch_size=maker_batch_size,
                resume_from=None,
                concurrency=maker_concurrency,
                provider_out=provider_out,
            )
        except KeyboardInterrupt:
            print("[workflow] Maker step interrupted by user — aborting workflow.", flush=True)
            for p in provider_out:
                p.shutdown()
            return None
        current_artifacts.maker_cases_path = Path(maker_summary["results_path"])
        current_artifacts.maker_summary_path = Path(maker_dir / maker_summary["run_id"] / "summary.json")

    if WORKFLOW_STEPS.index(start_step) <= WORKFLOW_STEPS.index("checker"):
        print(f"[workflow] Step 4/4: Running checker (API call, timeout={config.checker_defaults.timeout_seconds}s)...")
        checker_dir = ensure_dir(workflow_dir / "checker")
        try:
            checker_summary = run_checker_pipeline(
                config=config,
                semantic_rules_path=current_artifacts.semantic_rules_path,
                maker_cases_path=current_artifacts.maker_cases_path,
                output_dir=checker_dir,
                limit=None,
                batch_size=checker_batch_size,
                resume_from=None,
                concurrency=checker_concurrency,
                provider_out=provider_out,
            )
        except KeyboardInterrupt:
            print("[workflow] Checker step interrupted by user — aborting workflow.", flush=True)
            for p in provider_out:
                p.shutdown()
            return None
        current_artifacts.checker_reviews_path = Path(checker_summary["results_path"])
        current_artifacts.checker_summary_path = Path(checker_dir / checker_summary["run_id"] / "summary.json")
        current_artifacts.coverage_report_path = Path(checker_summary["coverage_report_path"])

    manager = ReviewSessionManager(
        config=config,
        rules_path=current_artifacts.semantic_rules_path,
        maker_cases_path=current_artifacts.maker_cases_path,
        checker_reviews_path=current_artifacts.checker_reviews_path,
        output_root=output_root,
        repo_root=repo_root,
        rewrite_batch_size=maker_batch_size,
        checker_batch_size=checker_batch_size,
        rewrite_concurrency=maker_concurrency,
        checker_concurrency=checker_concurrency,
        initial_maker_summary_path=current_artifacts.maker_summary_path,
        initial_checker_summary_path=current_artifacts.checker_summary_path,
        initial_coverage_report_path=current_artifacts.coverage_report_path,
        normalized_bdd_path=None,
        step_registry_path=None,
    )
    server, url = serve_review_session(manager=manager, host=host, port=port)
    return server, url, manager


def _run_extract(repo_root: Path, source_path: Path, artifacts_dir: Path, write_page_text: bool) -> None:
    command = [
        sys.executable,
        "scripts/extract_matching_rules.py",
        "--input",
        str(source_path),
        "--output-dir",
        str(artifacts_dir),
    ]
    if write_page_text:
        command.append("--write-page-text")
    subprocess.run(command, cwd=repo_root, check=True)


def _run_generate_semantic(repo_root: Path, artifacts_dir: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            "scripts/generate_semantic_rules.py",
            "--input",
            str(artifacts_dir / "atomic_rules.json"),
            "--output",
            str(artifacts_dir / "semantic_rules.json"),
        ],
        cwd=repo_root,
        check=True,
    )
