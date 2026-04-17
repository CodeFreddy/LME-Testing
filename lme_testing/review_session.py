
from __future__ import annotations

import json
import logging
import mimetypes
import threading
import traceback
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, urlparse

from .config import ProjectConfig
from .human_review import _render_case_detail
from .pipelines import _case_map_from_maker_records, run_checker_pipeline, run_rewrite_pipeline
from .reporting import generate_html_report
from .schemas import load_issue_type_options, validate_human_review_payload
from .storage import ensure_dir, load_json, load_jsonl, timestamp_slug, write_json

logger = logging.getLogger(__name__)


@dataclass
class ReviewJobStatus:
    job_id: str
    status: str
    iteration: int
    saved_review_path: str | None = None
    latest_review_path: str | None = None
    error: str | None = None
    result: dict[str, Any] | None = None


class ReviewSessionManager:
    # 管理 review session 的状态：当前工作集、每轮人工审核、后台回流任务和最终完成状态。
    def __init__(
        self,
        config: ProjectConfig,
        rules_path: Path,
        maker_cases_path: Path,
        checker_reviews_path: Path,
        output_root: Path,
        repo_root: Path,
        rewrite_batch_size: int = 1,
        checker_batch_size: int = 1,
        initial_maker_summary_path: Path | None = None,
        initial_checker_summary_path: Path | None = None,
        initial_coverage_report_path: Path | None = None,
        normalized_bdd_path: Path | None = None,
        step_registry_path: Path | None = None,
    ) -> None:
        self.config = config
        self.rules_path = rules_path.resolve()
        self.repo_root = repo_root.resolve()
        self.rewrite_batch_size = rewrite_batch_size
        self.checker_batch_size = checker_batch_size
        self.session_id = timestamp_slug()
        self.session_dir = ensure_dir(output_root / self.session_id)
        self.issue_type_options = load_issue_type_options()
        self.manifest_path = self.session_dir / "session_manifest.json"
        self._jobs: dict[str, ReviewJobStatus] = {}
        self._lock = threading.Lock()
        logger.info("Creating review session. rules=%s maker_cases=%s checker_reviews=%s output_root=%s", self.rules_path, maker_cases_path, checker_reviews_path, output_root)

        self._state: dict[str, Any] = {
            "session_id": self.session_id,
            "status": "running",
            "rules_path": str(self.rules_path),
            "current_iteration": 0,
            "current_maker_cases_path": str(Path(maker_cases_path).resolve()),
            "current_checker_reviews_path": str(Path(checker_reviews_path).resolve()),
            "current_report_path": None,
            "normalized_bdd_path": str(normalized_bdd_path.resolve()) if normalized_bdd_path else None,
            "step_registry_path": str(step_registry_path.resolve()) if step_registry_path else None,
            "history": [],
            "iterations": {},
            "stage_gates": {
                "review_decided": False,
                "bdd_edited": False,
                "scripts_viewed": False,
            },
        }
        self._ensure_iteration_dirs(0)
        self._state["iterations"]["0"] = {
            "iteration": 0,
            "maker_cases_path": str(Path(maker_cases_path).resolve()),
            "checker_reviews_path": str(Path(checker_reviews_path).resolve()),
            "report_path": None,
            "human_reviews_latest_path": str(self._iteration_dir(0) / "reviews" / "human_reviews_latest.json"),
            "rewrite_summary_path": None,
            "checker_summary_path": str(initial_checker_summary_path.resolve()) if initial_checker_summary_path else None,
            "maker_summary_path": str(initial_maker_summary_path.resolve()) if initial_maker_summary_path else None,
            "coverage_report_path": str(initial_coverage_report_path.resolve()) if initial_coverage_report_path else None,
            "normalized_bdd_path": str(normalized_bdd_path.resolve()) if normalized_bdd_path else None,
            "step_registry_path": str(step_registry_path.resolve()) if step_registry_path else None,
            "stage_gates": {
                "review_decided": False,
                "bdd_edited": False,
                "scripts_viewed": False,
            },
        }
        if initial_maker_summary_path and initial_checker_summary_path and initial_coverage_report_path:
            initial_report = self._render_iteration_report(0)
            self._state["current_report_path"] = str(initial_report)
            self._state["iterations"]["0"]["report_path"] = str(initial_report)
        self._save_manifest()
        logger.info("Review session initialized. session_id=%s session_dir=%s", self.session_id, self.session_dir)

    def session_payload(self) -> dict[str, Any]:
        state = self._load_state()
        iteration = int(state["current_iteration"])
        latest_path = Path(state["iterations"][str(iteration)]["human_reviews_latest_path"])
        if latest_path.exists():
            latest_payload = validate_human_review_payload(
                load_json(latest_path),
                expected_case_map=self._current_case_map(state),
            )
            reviews = latest_payload.get("reviews", [])
        else:
            reviews = self._seed_reviews(state)
        return {
            "session_id": state["session_id"],
            "session_status": state["status"],
            "current_iteration": iteration,
            "metadata": {
                "rules_path": state["rules_path"],
                "maker_cases_path": state["current_maker_cases_path"],
                "checker_reviews_path": state["current_checker_reviews_path"],
                "latest_review_path": str(latest_path),
                "current_report_path": state.get("current_report_path"),
            },
            "issue_type_options": self.issue_type_options,
            "reviews": reviews,
            "table_rows": self._table_rows(state),
            "history": state.get("history", []),
        }

    def save_reviews(self, payload: dict[str, Any]) -> dict[str, Any]:
        state = self._load_state()
        if state["status"] != "running":
            raise ValueError("Session is already finalized and cannot accept new reviews.")
        iteration = int(state["current_iteration"])
        reviews_dir = ensure_dir(self._iteration_dir(iteration) / "reviews")
        normalized = validate_human_review_payload(payload, expected_case_map=self._current_case_map(state))
        timestamp = timestamp_slug()
        snapshot_path = reviews_dir / f"human_reviews_{timestamp}.json"
        latest_path = reviews_dir / "human_reviews_latest.json"
        write_json(snapshot_path, normalized)
        write_json(latest_path, normalized)
        state["iterations"][str(iteration)]["human_reviews_latest_path"] = str(latest_path)
        reviews = normalized.get("reviews", [])
        any_decided = any(r.get("review_decision", "pending") != "pending" for r in reviews)
        if any_decided:
            if "stage_gates" not in state:
                state["stage_gates"] = {"review_decided": False, "bdd_edited": False, "scripts_viewed": False}
            state["stage_gates"]["review_decided"] = True
            state["iterations"][str(iteration)]["stage_gates"]["review_decided"] = True
        self._save_manifest(state)
        logger.info("Saved human reviews. session_id=%s iteration=%s saved=%s latest=%s review_count=%s", state["session_id"], iteration, snapshot_path, latest_path, len(reviews))
        return {
            "iteration": iteration,
            "saved_review_path": str(snapshot_path),
            "latest_review_path": str(latest_path),
            "review_count": len(reviews),
            "review_decided": any_decided,
        }

    def bdd_payload(self) -> dict[str, Any]:
        state = self._load_state()
        iteration = int(state["current_iteration"])
        normalized_bdd_path = state.get("normalized_bdd_path") or state["iterations"][str(iteration)].get("normalized_bdd_path")
        if not normalized_bdd_path:
            return {"bdd_path": None, "has_bdd": False, "scenarios_by_rule": [], "total_count": 0}
        normalized_bdd_path = Path(normalized_bdd_path)
        if not normalized_bdd_path.exists():
            return {"bdd_path": str(normalized_bdd_path), "has_bdd": False, "scenarios_by_rule": [], "total_count": 0}

        bdd_records = load_jsonl(normalized_bdd_path)
        latest_reviews_path = Path(state["iterations"][str(iteration)]["human_reviews_latest_path"])
        approved_case_ids: set[str] = set()
        if latest_reviews_path.exists():
            reviews_data = load_json(latest_reviews_path)
            approved_case_ids = {r["case_id"] for r in reviews_data.get("reviews", []) if r.get("review_decision") == "approve"}

        scenarios_by_rule: list[dict[str, Any]] = []
        total_count = 0
        for record in bdd_records:
            semantic_rule_id = record.get("semantic_rule_id", "")
            scenarios: list[dict[str, Any]] = []
            for scenario in record.get("scenarios", []):
                scenario_id = scenario.get("scenario_id", "")
                if scenario_id in approved_case_ids or not approved_case_ids:
                    scenarios.append({
                        "scenario_id": scenario_id,
                        "case_type": scenario.get("case_type", ""),
                        "priority": scenario.get("priority", ""),
                        "given_steps": scenario.get("given_steps", []),
                        "when_steps": scenario.get("when_steps", []),
                        "then_steps": scenario.get("then_steps", []),
                        "approved": scenario_id in approved_case_ids,
                    })
                    total_count += 1
            if scenarios:
                scenarios_by_rule.append({
                    "semantic_rule_id": semantic_rule_id,
                    "feature_title": record.get("feature_title", ""),
                    "scenarios": scenarios,
                })
        return {
            "bdd_path": str(normalized_bdd_path),
            "has_bdd": True,
            "scenarios_by_rule": scenarios_by_rule,
            "total_count": total_count,
        }

    def save_bdd_edits(self, payload: dict[str, Any]) -> dict[str, Any]:
        state = self._load_state()
        if state["status"] != "running":
            raise ValueError("Session is already finalized and cannot accept new edits.")
        iteration = int(state["current_iteration"])
        bdd_dir = ensure_dir(self._iteration_dir(iteration) / "bdd")
        edits = payload.get("edits", [])
        timestamp = timestamp_slug()
        snapshot_path = bdd_dir / f"human_bdd_edits_{timestamp}.json"
        latest_path = bdd_dir / "human_bdd_edits_latest.json"
        write_json(snapshot_path, {"edits": edits, "timestamp": timestamp})
        write_json(latest_path, {"edits": edits, "timestamp": timestamp})
        if edits:
            if "stage_gates" not in state:
                state["stage_gates"] = {"review_decided": False, "bdd_edited": False, "scripts_viewed": False}
            state["stage_gates"]["bdd_edited"] = True
            state["iterations"][str(iteration)]["stage_gates"]["bdd_edited"] = True
        self._save_manifest(state)
        logger.info("Saved BDD edits. session_id=%s iteration=%s saved=%s latest=%s edit_count=%s", state["session_id"], iteration, snapshot_path, latest_path, len(edits))
        return {"saved_path": str(snapshot_path), "latest_path": str(latest_path), "edit_count": len(edits)}

    def scripts_payload(self) -> dict[str, Any]:
        """Return step registry visibility data for the Scripts tab."""
        state = self._load_state()
        iteration = int(state["current_iteration"])
        # Mark scripts as viewed when tab is loaded
        if "stage_gates" not in state:
            state["stage_gates"] = {"review_decided": False, "bdd_edited": False, "scripts_viewed": False}
        state["stage_gates"]["scripts_viewed"] = True
        state["iterations"][str(iteration)]["stage_gates"]["scripts_viewed"] = True
        self._save_manifest(state)
        step_registry_path = state.get("step_registry_path") or state["iterations"][str(iteration)].get("step_registry_path")

        if not step_registry_path:
            return {
                "has_registry": False,
                "registry_path": None,
                "summary": {},
                "steps_by_type": {"given": [], "when": [], "then": []},
                "gaps": [],
                "candidates": [],
            }

        step_registry_path = Path(step_registry_path)
        if not step_registry_path.exists():
            return {
                "has_registry": False,
                "registry_path": str(step_registry_path),
                "summary": {},
                "steps_by_type": {"given": [], "when": [], "then": []},
                "gaps": [],
                "candidates": [],
            }

        registry_data = load_json(step_registry_path)
        summary = {
            "total_steps": registry_data.get("total_steps", 0),
            "given_count": registry_data.get("given_count", 0),
            "when_count": registry_data.get("when_count", 0),
            "then_count": registry_data.get("then_count", 0),
            "unique_bdd_patterns": registry_data.get("unique_bdd_patterns", 0),
            "exact_matches": registry_data.get("exact_matches", 0),
            "parameterized_matches": registry_data.get("parameterized_matches", 0),
            "candidates": len(registry_data.get("candidates", [])),
            "unmatched": registry_data.get("unmatched", 0),
            "reuse_scores": registry_data.get("reuse_scores", {}),
        }

        steps_by_type: dict[str, list[dict]] = {"given": [], "when": [], "then": []}
        for step_type in ("given", "when", "then"):
            key = f"{step_type}_steps"
            if key in registry_data:
                steps_by_type[step_type] = registry_data[key]
            elif step_type in registry_data:
                steps_by_type[step_type] = registry_data[step_type]

        return {
            "has_registry": True,
            "registry_path": str(step_registry_path),
            "summary": summary,
            "steps_by_type": steps_by_type,
            "gaps": registry_data.get("gaps", []),
            "candidates": registry_data.get("candidates", []),
        }

    def stage_payload(self) -> dict[str, Any]:
        """Return current stage gates and allowed transitions."""
        state = self._load_state()
        iteration = int(state["current_iteration"])
        gates = state.get("stage_gates", {"review_decided": False, "bdd_edited": False, "scripts_viewed": False})
        iter_gates = state["iterations"][str(iteration)].get("stage_gates", gates)
        # Merge: iteration gates override session gates
        merged_gates = {**gates, **iter_gates}
        return {
            "review_decided": merged_gates.get("review_decided", False),
            "bdd_edited": merged_gates.get("bdd_edited", False),
            "scripts_viewed": merged_gates.get("scripts_viewed", False),
            "status": state["status"],
        }

    def advance_stage(self, to_stage: str) -> dict[str, Any]:
        """Attempt to advance to a named stage. Returns success/failure with reason."""
        gates = self.stage_payload()
        stage_order = ["review", "bdd", "scripts", "finalize"]
        current_idx = 0
        if gates["review_decided"]:
            current_idx = 1
        if gates["bdd_edited"]:
            current_idx = 2
        if gates["scripts_viewed"]:
            current_idx = 3
        target_idx = stage_order.index(to_stage) if to_stage in stage_order else -1
        if target_idx < 0:
            return {"success": False, "error": f"Unknown stage: {to_stage}"}
        if target_idx > current_idx + 1:
            return {"success": False, "error": f"Complete '{stage_order[current_idx]}' stage before advancing to '{to_stage}'"}
        return {"success": True, "current_stage": stage_order[current_idx], "target_stage": to_stage}

    def save_scripts_edits(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Save step definition edits to session snapshot."""
        state = self._load_state()
        if state["status"] != "running":
            raise ValueError("Session is already finalized and cannot accept new edits.")
        iteration = int(state["current_iteration"])
        scripts_dir = ensure_dir(self._iteration_dir(iteration) / "scripts")
        edits = payload.get("edits", [])
        timestamp = timestamp_slug()
        snapshot_path = scripts_dir / f"human_scripts_edits_{timestamp}.json"
        latest_path = scripts_dir / "human_scripts_edits_latest.json"
        write_json(snapshot_path, {"edits": edits, "timestamp": timestamp})
        write_json(latest_path, {"edits": edits, "timestamp": timestamp})
        logger.info("Saved scripts edits. session_id=%s iteration=%s saved=%s latest=%s edit_count=%s", state["session_id"], iteration, snapshot_path, latest_path, len(edits))
        return {"saved_path": str(snapshot_path), "latest_path": str(latest_path), "edit_count": len(edits)}

    def submit_reviews(self, payload: dict[str, Any]) -> dict[str, Any]:
        save_result = self.save_reviews(payload)
        iteration = int(save_result["iteration"])
        latest_path = Path(save_result["latest_review_path"])
        job_id = timestamp_slug()
        status = ReviewJobStatus(
            job_id=job_id,
            status="queued",
            iteration=iteration,
            saved_review_path=save_result["saved_review_path"],
            latest_review_path=save_result["latest_review_path"],
        )
        with self._lock:
            self._jobs[job_id] = status
        logger.info("Queued review-session job. session_id=%s job_id=%s iteration=%s latest=%s", self.session_id, job_id, iteration, latest_path)
        thread = threading.Thread(target=self._run_job, args=(job_id, iteration, latest_path), daemon=True)
        thread.start()
        return {"job_id": job_id, **save_result}

    def finalize_session(self) -> dict[str, Any]:
        state = self._load_state()
        if state["status"] == "finalized":
            final_report_path = Path(state.get("current_report_path") or "")
            final_maker_path = final_report_path.with_name("maker_readable.html") if final_report_path else None
            final_checker_path = final_report_path.with_name("checker_readable.html") if final_report_path else None
            return {
                "session_id": state["session_id"],
                "status": state["status"],
                "final_report_path": state.get("current_report_path"),
                "final_report_url": self.report_route_url("report") if final_report_path else None,
                "final_maker_path": str(final_maker_path) if final_maker_path else None,
                "final_maker_url": self.report_route_url("maker") if final_maker_path else None,
                "final_checker_path": str(final_checker_path) if final_checker_path else None,
                "final_checker_url": self.report_route_url("checker") if final_checker_path else None,
            }
        if not state.get("current_report_path"):
            raise ValueError("Current session has no report yet; run at least one checker/report cycle before finalize.")
        state["status"] = "finalized"
        final_dir = ensure_dir(self.session_dir / "final")
        final_manifest = final_dir / "final_session_manifest.json"
        write_json(final_manifest, state)
        self._save_manifest(state)
        final_report_path = Path(state.get("current_report_path") or "")
        final_maker_path = final_report_path.with_name("maker_readable.html") if final_report_path else None
        final_checker_path = final_report_path.with_name("checker_readable.html") if final_report_path else None
        return {
            "session_id": state["session_id"],
            "status": state["status"],
            "final_report_path": state.get("current_report_path"),
            "final_report_url": self.report_route_url("report") if final_report_path else None,
            "final_maker_path": str(final_maker_path) if final_maker_path else None,
            "final_maker_url": self.report_route_url("maker") if final_maker_path else None,
            "final_checker_path": str(final_checker_path) if final_checker_path else None,
            "final_checker_url": self.report_route_url("checker") if final_checker_path else None,
            "final_manifest_path": str(final_manifest),
        }

    def job_status(self, job_id: str) -> dict[str, Any]:
        with self._lock:
            status = self._jobs.get(job_id)
        if not status:
            raise KeyError(job_id)
        return {
            "job_id": status.job_id,
            "status": status.status,
            "iteration": status.iteration,
            "saved_review_path": status.saved_review_path,
            "latest_review_path": status.latest_review_path,
            "error": status.error,
            "result": status.result,
        }
    def _run_job(self, job_id: str, iteration: int, human_reviews_path: Path) -> None:
        with self._lock:
            self._jobs[job_id].status = "running"
        logger.info("Review-session job started. session_id=%s job_id=%s iteration=%s human_reviews=%s", self.session_id, job_id, iteration, human_reviews_path)
        try:
            state = self._load_state()
            if iteration != int(state["current_iteration"]):
                raise ValueError("Session iteration has advanced; stale submit is rejected.")

            rewrite_dir = ensure_dir(self._iteration_dir(iteration) / "rewrite")
            checker_dir = ensure_dir(self._iteration_dir(iteration) / "checker")
            rewrite_summary = run_rewrite_pipeline(
                config=self.config,
                semantic_rules_path=self.rules_path,
                maker_cases_path=Path(state["current_maker_cases_path"]),
                checker_reviews_path=Path(state["current_checker_reviews_path"]),
                human_reviews_path=human_reviews_path,
                output_dir=rewrite_dir,
                limit=None,
                batch_size=self.rewrite_batch_size,
            )
            checker_summary = run_checker_pipeline(
                config=self.config,
                semantic_rules_path=self.rules_path,
                maker_cases_path=Path(rewrite_summary["merged_cases_path"]),
                output_dir=checker_dir,
                limit=None,
                batch_size=self.checker_batch_size,
                resume_from=None,
            )

            state["history"].append(
                {
                    "iteration": iteration,
                    "human_reviews_path": str(human_reviews_path),
                    "rewrite_summary_path": str(Path(rewrite_summary["output_dir"]) / "summary.json"),
                    "checker_summary_path": str(Path(checker_summary["output_dir"]) / "summary.json"),
                    "coverage_report_path": checker_summary["coverage_report_path"],
                }
            )
            state["iterations"][str(iteration)]["rewrite_summary_path"] = str(Path(rewrite_summary["output_dir"]) / "summary.json")
            state["iterations"][str(iteration)]["checker_summary_path"] = str(Path(checker_summary["output_dir"]) / "summary.json")
            state["iterations"][str(iteration)]["coverage_report_path"] = checker_summary["coverage_report_path"]

            next_iteration = iteration + 1
            self._ensure_iteration_dirs(next_iteration)
            next_state = {
                "iteration": next_iteration,
                "maker_cases_path": rewrite_summary["merged_cases_path"],
                "checker_reviews_path": checker_summary["results_path"],
                "report_path": None,
                "human_reviews_latest_path": str(self._iteration_dir(next_iteration) / "reviews" / "human_reviews_latest.json"),
                "rewrite_summary_path": None,
                "checker_summary_path": str(Path(checker_summary["output_dir"]) / "summary.json"),
                "maker_summary_path": str(Path(rewrite_summary["output_dir"]) / "summary.json"),
                "coverage_report_path": checker_summary["coverage_report_path"],
            }
            state["iterations"][str(next_iteration)] = next_state
            state["current_iteration"] = next_iteration
            state["current_maker_cases_path"] = rewrite_summary["merged_cases_path"]
            state["current_checker_reviews_path"] = checker_summary["results_path"]
            report_path = self._render_iteration_report(next_iteration, state=state)
            next_state["report_path"] = str(report_path)
            state["current_report_path"] = str(report_path)
            self._save_manifest(state)
            logger.info("Review-session job succeeded. session_id=%s job_id=%s next_iteration=%s report=%s", self.session_id, job_id, next_iteration, report_path)

            result = {
                "rewrite_summary": rewrite_summary,
                "checker_summary": checker_summary,
                "report_summary": {
                    "output_html": str(report_path),
                    "maker_html": str(report_path.with_name("maker_readable.html")),
                    "checker_html": str(report_path.with_name("checker_readable.html")),
                },
                "next_iteration": next_iteration,
                "links": {
                    "human_reviews_latest": self._file_url(Path(next_state["human_reviews_latest_path"])),
                    "rewritten_cases": self._file_url(Path(rewrite_summary["rewritten_cases_path"])),
                    "merged_cases": self._file_url(Path(rewrite_summary["merged_cases_path"])),
                    "checker_reviews": self._file_url(Path(checker_summary["results_path"])),
                    "coverage_report": self._file_url(Path(checker_summary["coverage_report_path"])),
                    "report_html": self._file_url(report_path),
                },
            }
            with self._lock:
                self._jobs[job_id].status = "succeeded"
                self._jobs[job_id].result = result
        except Exception as exc:  # pragma: no cover
            logger.exception("Review-session job failed. session_id=%s job_id=%s iteration=%s", self.session_id, job_id, iteration)
            with self._lock:
                self._jobs[job_id].status = "failed"
                self._jobs[job_id].error = f"{exc}\n{traceback.format_exc()}"

    def _seed_reviews(self, state: dict[str, Any]) -> list[dict]:
        maker_records = load_jsonl(Path(state["current_maker_cases_path"]))
        checker_reviews = load_jsonl(Path(state["current_checker_reviews_path"]))
        reviews_by_case = {item["case_id"]: item for item in checker_reviews}
        seeded: list[dict] = []
        for maker_record in maker_records:
            semantic_rule_id = maker_record.get("semantic_rule_id", "")
            for scenario in maker_record.get("scenarios", []):
                case_id = scenario.get("scenario_id", "")
                checker = reviews_by_case.get(case_id, {})
                checker_blocking = checker.get("checker_blocking") is True or checker.get("is_blocking") is True
                seeded.append(
                    {
                        "case_id": case_id,
                        "semantic_rule_id": semantic_rule_id,
                        "review_decision": "pending",
                        "block_recommendation_review": "pending_review" if checker_blocking else "not_applicable",
                        "human_comment": "",
                        "issue_types": [],
                    }
                )
        return seeded

    def _table_rows(self, state: dict[str, Any]) -> list[dict]:
        maker_records = load_jsonl(Path(state["current_maker_cases_path"]))
        checker_reviews = load_jsonl(Path(state["current_checker_reviews_path"]))
        reviews_by_case = {item["case_id"]: item for item in checker_reviews}
        rows: list[dict] = []
        for maker_record in maker_records:
            semantic_rule_id = maker_record.get("semantic_rule_id", "")
            feature = maker_record.get("feature", "")
            for scenario in maker_record.get("scenarios", []):
                case_id = scenario.get("scenario_id", "")
                checker = reviews_by_case.get(case_id, {})
                checker_blocking = checker.get("checker_blocking") is True or checker.get("is_blocking") is True
                rows.append(
                    {
                        "semantic_rule_id": semantic_rule_id,
                        "case_id": case_id,
                        "feature": feature,
                        "case_type": str(scenario.get("case_type", "")),
                        "overall": str(checker.get("overall_status", "missing")),
                        "coverage": str(checker.get("coverage_assessment", {}).get("status", "missing")),
                        "checker_blocking": checker_blocking,
                        "blocking_category": str(checker.get("checker_blocking_category", checker.get("blocking_category", "none"))),
                        "blocking_reason": str(checker.get("checker_blocking_reason", checker.get("blocking_reason", ""))),
                        "detail_html": _render_case_detail(scenario, checker),
                    }
                )
        return rows

    def _render_iteration_report(self, iteration: int, state: dict[str, Any] | None = None) -> Path:
        state = state or self._load_state()
        iteration_state = state["iterations"][str(iteration)]
        maker_summary_path = iteration_state.get("maker_summary_path")
        checker_summary_path = iteration_state.get("checker_summary_path")
        coverage_report_path = iteration_state.get("coverage_report_path")
        if not (maker_summary_path and checker_summary_path and coverage_report_path):
            raise ValueError(f"Iteration {iteration} is missing summary/coverage paths for report generation.")
        report_dir = ensure_dir(self._iteration_dir(iteration) / "report")
        report_output = report_dir / "report.html"
        generate_html_report(
            maker_cases_path=Path(iteration_state["maker_cases_path"]),
            checker_reviews_path=Path(iteration_state["checker_reviews_path"]),
            maker_summary_path=Path(maker_summary_path),
            checker_summary_path=Path(checker_summary_path),
            coverage_report_path=Path(coverage_report_path),
            output_html_path=report_output,
        )
        return report_output

    def _current_case_map(self, state: dict[str, Any]) -> dict[str, str]:
        return _case_map_from_maker_records(load_jsonl(Path(state["current_maker_cases_path"])))

    def _iteration_dir(self, iteration: int) -> Path:
        return self.session_dir / "iterations" / f"{iteration:03d}"

    def _ensure_iteration_dirs(self, iteration: int) -> None:
        base = ensure_dir(self._iteration_dir(iteration))
        ensure_dir(base / "reviews")
        ensure_dir(base / "rewrite")
        ensure_dir(base / "checker")
        ensure_dir(base / "report")
        ensure_dir(base / "bdd")

    def _load_state(self) -> dict[str, Any]:
        if self.manifest_path.exists():
            return load_json(self.manifest_path)
        return self._state

    def _save_manifest(self, state: dict[str, Any] | None = None) -> None:
        if state is None:
            state = self._state
        else:
            self._state = state
        write_json(self.manifest_path, self._state)

    def current_report_file(self, route_name: str) -> Path:
        state = self._load_state()
        report_path = Path(state.get("current_report_path") or "")
        if not report_path:
            raise ValueError("Current session has no report file.")
        mapping = {
            "report": report_path,
            "maker": report_path.with_name("maker_readable.html"),
            "checker": report_path.with_name("checker_readable.html"),
        }
        target = mapping.get(route_name)
        if not target:
            raise ValueError(f"Unsupported report route: {route_name}")
        return target.resolve()

    def report_route_url(self, route_name: str) -> str:
        mapping = {
            "report": "/report.html",
            "maker": "/maker_readable.html",
            "checker": "/checker_readable.html",
        }
        return mapping[route_name]

    def _file_url(self, path: Path) -> str:
        return f"/files?path={quote(str(path.resolve()))}"

def serve_review_session(
    manager: ReviewSessionManager,
    host: str,
    port: int,
) -> tuple[ThreadingHTTPServer, str]:
    # 本地 HTTP 服务，负责把人工审核页面与后台回流任务串起来。
    handler = _build_handler(manager)
    server = ThreadingHTTPServer((host, port), handler)
    actual_port = server.server_address[1]
    logger.info("Review-session HTTP server started. session_id=%s host=%s port=%s", manager.session_id, host, actual_port)
    return server, f"http://{host}:{actual_port}/"


def _build_handler(manager: ReviewSessionManager):
    repo_root = manager.repo_root

    class ReviewSessionHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            try:
                parsed = urlparse(self.path)
                logger.info("HTTP GET %s", parsed.path)
                if parsed.path == "/":
                    self._send_html(_render_review_session_shell())
                    return
                if parsed.path == "/api/session":
                    self._send_json(manager.session_payload())
                    return
                if parsed.path == "/api/history":
                    self._send_json({"history": manager.session_payload().get("history", [])})
                    return
                if parsed.path == "/api/bdd":
                    self._send_json(manager.bdd_payload())
                    return
                if parsed.path == "/api/scripts":
                    self._send_json(manager.scripts_payload())
                    return
                if parsed.path == "/api/stage":
                    self._send_json(manager.stage_payload())
                    return
                if parsed.path == "/report.html":
                    self._send_file(str(manager.current_report_file("report")), repo_root)
                    return
                if parsed.path == "/maker_readable.html":
                    self._send_file(str(manager.current_report_file("maker")), repo_root)
                    return
                if parsed.path == "/checker_readable.html":
                    self._send_file(str(manager.current_report_file("checker")), repo_root)
                    return
                if parsed.path.startswith("/api/status/"):
                    job_id = parsed.path.rsplit("/", 1)[-1]
                    try:
                        self._send_json(manager.job_status(job_id))
                    except KeyError:
                        self.send_error(HTTPStatus.NOT_FOUND, "Unknown job id")
                    return
                if parsed.path == "/files":
                    query = parse_qs(parsed.query)
                    target = query.get("path", [""])[0]
                    self._send_file(target, repo_root)
                    return
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            except Exception as exc:
                logger.exception("HTTP GET failed for path=%s", self.path)
                self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

        def do_POST(self) -> None:  # noqa: N802
            try:
                parsed = urlparse(self.path)
                logger.info("HTTP POST %s", parsed.path)
                payload = self._read_json_body()
                if parsed.path == "/api/reviews/save":
                    self._send_json(manager.save_reviews(payload))
                    return
                if parsed.path == "/api/submit":
                    self._send_json(manager.submit_reviews(payload), status=HTTPStatus.ACCEPTED)
                    return
                if parsed.path == "/api/finalize":
                    self._send_json(manager.finalize_session())
                    return
                if parsed.path == "/api/bdd/save":
                    self._send_json(manager.save_bdd_edits(payload))
                    return
                if parsed.path == "/api/scripts/save":
                    self._send_json(manager.save_scripts_edits(payload))
                    return
                if parsed.path == "/api/stage/advance":
                    target = payload.get("to_stage", "")
                    self._send_json(manager.advance_stage(target))
                    return
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            except Exception as exc:
                logger.exception("HTTP POST failed for path=%s", self.path)
                self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

        def _read_json_body(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length) if length else b"{}"
            return json.loads(body.decode("utf-8"))

        def _send_json(self, payload: dict[str, Any], status: int = HTTPStatus.OK) -> None:
            encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _send_html(self, html_text: str) -> None:
            encoded = html_text.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _send_file(self, raw_path: str, root: Path) -> None:
            if not raw_path:
                self.send_error(HTTPStatus.BAD_REQUEST, "Missing path")
                return
            path = Path(raw_path).resolve()
            try:
                path.relative_to(root)
            except ValueError:
                self.send_error(HTTPStatus.FORBIDDEN, "Path outside repo root")
                return
            if not path.exists() or not path.is_file():
                self.send_error(HTTPStatus.NOT_FOUND, "File not found")
                return
            content = path.read_bytes()
            mime_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

    return ReviewSessionHandler


def _render_review_session_shell() -> str:
    return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>Review Session</title>
  <style>
    body { font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif; margin: 24px; color: #1f2937; background: #f8fafc; }
    h1, h2 { color: #0f172a; }
    .card { background: white; border: 1px solid #cbd5e1; border-radius: 12px; padding: 16px 20px; margin-bottom: 20px; box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06); }
    .toolbar { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
    .grid { display: grid; grid-template-columns: repeat(3, minmax(180px, 1fr)); gap: 12px; }
    .metric { background: #eff6ff; border-radius: 10px; padding: 12px; border: 1px solid #bfdbfe; }
    table { width: 100%; border-collapse: collapse; background: white; }
    th, td { border: 1px solid #cbd5e1; padding: 10px; vertical-align: top; text-align: left; font-size: 13px; }
    th { background: #e2e8f0; }
    details { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 10px; }
    summary { cursor: pointer; font-weight: 600; }
    textarea, select { width: 100%; box-sizing: border-box; margin-top: 4px; }
    .issue-picker { margin-top: 4px; border: 1px solid #cbd5e1; border-radius: 8px; background: #f8fafc; }
    .issue-picker summary { list-style: none; }
    .issue-picker[open] summary { margin-bottom: 8px; }
    .issue-summary { color: #334155; font-size: 12px; }
    .issue-table { width: 100%; border-collapse: collapse; background: white; }
    .issue-table th, .issue-table td { border: 1px solid #e2e8f0; padding: 6px 8px; font-size: 12px; }
    .issue-table th { background: #f1f5f9; }
    .muted { color: #64748b; font-size: 12px; }
    .warning { color: #92400e; background: #fffbeb; border: 1px solid #fcd34d; border-radius: 8px; padding: 8px 10px; margin-top: 8px; }
    .status-running { color: #92400e; }
    .status-succeeded { color: #166534; }
    .status-failed { color: #991b1b; }
    .status-finalized { color: #1d4ed8; }
    button { padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 8px; background: white; cursor: pointer; }
    ul { margin: 8px 0 0 18px; }
    pre { white-space: pre-wrap; word-break: break-word; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; font-size: 12px; }
    .tab-bar { display: flex; gap: 4px; margin-bottom: 16px; border-bottom: 2px solid #e2e8f0; }
    .tab-btn { padding: 8px 16px; border: 1px solid #cbd5e1; border-radius: 8px 8px 0 0; background: #f1f5f9; cursor: pointer; }
    .tab-btn.active { background: white; border-bottom-color: white; font-weight: 600; }
    .tab-panel { display: none; }
    .tab-panel.active { display: block; }
    .bdd-rule-block { background: white; border: 1px solid #cbd5e1; border-radius: 10px; padding: 14px; margin-bottom: 12px; }
    .bdd-rule-header { font-weight: 700; color: #0f172a; margin-bottom: 10px; font-size: 14px; }
    .step-group { margin-bottom: 10px; }
    .step-label { font-weight: 600; font-size: 13px; color: #475569; margin-bottom: 4px; }
    .step-textarea { width: 100%; box-sizing: border-box; font-family: monospace; font-size: 12px; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px 8px; resize: vertical; }
    .bdd-scenario-card { margin-left: 12px; margin-bottom: 10px; padding: 10px; border: 1px solid #e2e8f0; border-radius: 8px; }
    .scripts-metrics { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 10px; margin-bottom: 16px; }
    .scripts-metric { background: #eff6ff; border-radius: 10px; padding: 10px; border: 1px solid #bfdbfe; text-align: center; }
    .scripts-metric strong { font-size: 20px; display: block; }
    .scripts-metric span { font-size: 11px; color: #64748b; }
    .step-block { background: white; border: 1px solid #cbd5e1; border-radius: 10px; padding: 12px; margin-bottom: 10px; }
    .step-block-header { font-weight: 700; margin-bottom: 8px; }
    .step-type-section { margin-bottom: 12px; }
    .step-item { margin-bottom: 8px; padding: 6px 8px; border: 1px solid #e2e8f0; border-radius: 6px; }
    .step-item.exact { border-left: 3px solid #166534; }
    .step-item.parameterized { border-left: 3px solid #92400e; }
    .step-item.candidate { border-left: 3px solid #1d4ed8; }
    .step-item.unmatched { border-left: 3px solid #991b1b; background: #fff5f5; }
    .step-item-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
    .step-item-badge { font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: 600; }
    .badge-exact { background: #dcfce7; color: #166534; }
    .badge-parameterized { background: #fff7ed; color: #92400e; }
    .badge-candidate { background: #dbeafe; color: #1d4ed8; }
    .badge-unmatched { background: #fee2e2; color: #991b1b; }
    .step-item-text { font-family: monospace; font-size: 12px; color: #334155; }
    .step-item-pattern { font-family: monospace; font-size: 11px; color: #64748b; margin-top: 2px; }
    .suggestion-item { margin-left: 12px; padding: 4px 8px; border-left: 2px solid #e2e8f0; font-size: 12px; }
    .stage-progress { display: flex; align-items: center; gap: 0; margin-bottom: 16px; background: white; border: 1px solid #cbd5e1; border-radius: 12px; padding: 12px 20px; box-shadow: 0 4px 12px rgba(15,23,42,0.06); }
    .stage-step { display: flex; align-items: center; gap: 8px; cursor: pointer; padding: 6px 12px; border-radius: 8px; transition: background 0.2s; }
    .stage-step:hover { background: #f1f5f9; }
    .stage-step.active { background: #eff6ff; cursor: default; }
    .stage-step.active:hover { background: #eff6ff; }
    .stage-step.completed { cursor: pointer; }
    .stage-step.completed:hover { background: #f0fdf4; }
    .stage-step.locked { cursor: not-allowed; opacity: 0.5; }
    .stage-step.locked:hover { background: transparent; }
    .stage-dot { width: 28px; height: 28px; border-radius: 50%; background: #e2e8f0; color: #64748b; font-weight: 700; font-size: 13px; display: flex; align-items: center; justify-content: center; }
    .stage-step.active .stage-dot { background: #2563eb; color: white; }
    .stage-step.completed .stage-dot { background: #16a34a; color: white; }
    .stage-label { font-size: 13px; font-weight: 600; color: #64748b; }
    .stage-step.active .stage-label { color: #1e40af; }
    .stage-step.completed .stage-label { color: #166534; }
    .stage-arrow { color: #cbd5e1; font-size: 18px; margin: 0 4px; }
  </style>
</head>
<body>
  <h1>Review Session</h1>
  <div class="stage-progress" id="stageProgress">
    <div class="stage-step" data-stage="review" id="stage-review">
      <div class="stage-dot">1</div>
      <div class="stage-label">Scenario Review</div>
    </div>
    <div class="stage-arrow">→</div>
    <div class="stage-step" data-stage="bdd" id="stage-bdd">
      <div class="stage-dot">2</div>
      <div class="stage-label">BDD Edit</div>
    </div>
    <div class="stage-arrow">→</div>
    <div class="stage-step" data-stage="scripts" id="stage-scripts">
      <div class="stage-dot">3</div>
      <div class="stage-label">Scripts</div>
    </div>
    <div class="stage-arrow">→</div>
    <div class="stage-step" data-stage="finalize" id="stage-finalize">
      <div class="stage-dot">4</div>
      <div class="stage-label">Finalize</div>
    </div>
  </div>
  <div class="tab-bar">
    <button class="tab-btn active" data-tab="review">Scenario Review</button>
    <button class="tab-btn" data-tab="bdd">BDD Review</button>
    <button class="tab-btn" data-tab="scripts">Scripts</button>
  </div>
  <div id="tab-review" class="tab-panel active">
  <div class="card" id="summaryCard">加载中...</div>
  <div class="card">
    <h2>字段说明</h2>
    <ul>
      <li><strong>Decision</strong>: 人工最终动作。只要不是 <code>pending</code>，系统就按这个动作执行。<code>approve</code> 表示放行，<code>rewrite</code> 表示回流给 maker 重写，<code>reject</code> 表示人工拒绝当前 case。</li>
      <li><strong>Block Recommendation Review</strong>: 人工对 checker blocking 建议的裁定，只用于审计和统计，不决定最终执行动作。</li>
      <li><strong>Issue Types</strong>: 人工问题标签，可多选。用于后续统计与 maker 定向重写。</li>
    </ul>
    <div class="warning">当前版本中，只有 <code>Decision = rewrite</code> 才会触发 maker 回流。每次提交成功后，会话会自动切换到最新一轮结果继续审核。</div>
  </div>
  <div class="card">
    <div class="toolbar">
      <label>Overall <select id="overallFilter"><option value="">全部</option><option value="pass">pass</option><option value="fail">fail</option><option value="missing">missing</option></select></label>
      <label>Coverage <select id="coverageFilter"><option value="">全部</option><option value="covered">covered</option><option value="partial">partial</option><option value="uncovered">uncovered</option><option value="missing">missing</option></select></label>
      <label>Checker Blocking <select id="blockingFilter"><option value="">全部</option><option value="true">true</option><option value="false">false</option></select></label>
      <button id="saveBtn">保存草稿</button>
      <button id="submitBtn">提交并执行回流</button>
      <button id="finalizeBtn">Finalize</button>
    </div>
    <div class="muted">页面会自动把 human reviews 落到 session 目录，并在提交后串行执行 rewrite、checker、report。</div>
  </div>
  <div class="card" id="resultCard" style="display:none"></div>
  <div class="card"><h2>History</h2><div id="historyCard" class="muted">暂无历史</div></div>
  <div class="card">
    <table>
      <thead>
        <tr>
          <th>Semantic Rule</th>
          <th>Case ID</th>
          <th>Feature</th>
          <th>Case Type</th>
          <th>Overall</th>
          <th>Coverage</th>
          <th>Checker Blocking</th>
          <th>Blocking Category</th>
          <th>Blocking Reason</th>
          <th>Detail</th>
          <th>Human Review</th>
        </tr>
      </thead>
      <tbody id="reviewRows"></tbody>
    </table>
  </div>
  </div>
  <div id="tab-bdd" class="tab-panel">
    <div class="card">
      <div class="toolbar">
        <button id="saveBddBtn">Save BDD Edits</button>
        <span id="bddStatus" class="muted"></span>
      </div>
    </div>
    <div id="bddContent"><em>加载中...</em></div>
  </div>
  <div id="tab-scripts" class="tab-panel">
    <div class="card">
      <div class="toolbar">
        <button id="saveScriptsBtn">Save Scripts Edits</button>
        <span id="scriptsStatus" class="muted"></span>
      </div>
    </div>
    <div id="scriptsContent"><em>加载中...</em></div>
  </div>
<script>
let sessionPayload = null;
let reviewMap = new Map();
let pollTimer = null;
let bddPayload = null;
let scriptsPayload = null;
let currentStageGates = { review_decided: false, bdd_edited: false, scripts_viewed: false };
function escapeHtml(value) { return String(value ?? '').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;'); }
const STAGE_ORDER = ['review', 'bdd', 'scripts', 'finalize'];
const STAGE_TAB_MAP = { review: 'review', bdd: 'bdd', scripts: 'scripts', finalize: 'review' };
function currentStageIdx(gates) {
  if (gates.scripts_viewed) return 3;
  if (gates.bdd_edited) return 2;
  if (gates.review_decided) return 1;
  return 0;
}
function refreshStageProgress(gates) {
  currentStageGates = gates;
  const idx = currentStageIdx(gates);
  STAGE_ORDER.forEach((stage, i) => {
    const el = document.getElementById('stage-' + stage);
    if (!el) return;
    el.classList.remove('active', 'completed', 'locked');
    if (i === idx) el.classList.add('active');
    else if (i < idx) el.classList.add('completed');
    else el.classList.add('locked');
    el.querySelector('.stage-dot').textContent = i < idx ? '✓' : (i + 1);
  });
  // Sync tab buttons with stage
  const currentTab = STAGE_TAB_MAP[STAGE_ORDER[idx]];
  const tabBtns = document.querySelectorAll('.tab-btn');
  tabBtns.forEach(btn => {
    const tab = btn.dataset.tab;
    const tabIdx = STAGE_TAB_MAP[tab] === 'review' ? 0 : STAGE_TAB_MAP[tab] === 'bdd' ? 1 : STAGE_TAB_MAP[tab] === 'scripts' ? 2 : 3;
    if (tabIdx > idx + 1) {
      btn.disabled = true;
      btn.title = `Complete "${STAGE_ORDER[idx]}" stage first`;
    } else {
      btn.disabled = false;
      btn.title = '';
    }
  });
}
async function loadStageData() {
  try {
    const resp = await fetch('/api/stage');
    const data = await resp.json();
    refreshStageProgress(data);
  } catch(e) { console.error('Failed to load stage data', e); }
}
function switchTab(tab) {
  const idx = currentStageIdx(currentStageGates);
  const tabStageIdx = tab === 'review' ? 0 : tab === 'bdd' ? 1 : tab === 'scripts' ? 2 : 3;
  if (tabStageIdx > idx + 1) {
    alert(`Complete "${STAGE_ORDER[idx]}" stage before accessing this tab.`);
    return;
  }
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + tab).classList.add('active');
  document.querySelector('[data-tab="' + tab + '"]').classList.add('active');
  if (tab === 'bdd' && !bddPayload) loadBddData();
  if (tab === 'scripts' && !scriptsPayload) loadScriptsData();
}
function loadBddData() {
  fetch('/api/bdd').then(r => r.json()).then(data => {
    bddPayload = data;
    renderBddTab(data);
  });
}
function renderBddTab(data) {
  const el = document.getElementById('bddContent');
  if (!data.has_bdd) { el.innerHTML = '<em>No normalized BDD file linked. Run the BDD pipeline first, then restart the session with --normalized-bdd.</em>'; return; }
  el.innerHTML = data.scenarios_by_rule.map(rule => `
    <div class="bdd-rule-block">
      <div class="bdd-rule-header">${escapeHtml(rule.semantic_rule_id)} — ${escapeHtml(rule.feature_title)}</div>
      ${rule.scenarios.map(s => `
        <div class="bdd-scenario-card">
          <div><strong>${escapeHtml(s.scenario_id)}</strong> <em>(${escapeHtml(s.case_type)}, ${escapeHtml(s.priority)})</em></div>
          <div class="step-group">
            <div class="step-label">Given</div>
            ${s.given_steps.map((st,i) => `<textarea class="step-textarea" rows="2" data-scenario="${escapeHtml(s.scenario_id)}" data-step-type="given" data-step-index="${i}">${escapeHtml(st.step_text || '')}</textarea>`).join('')}
          </div>
          <div class="step-group">
            <div class="step-label">When</div>
            ${s.when_steps.map((st,i) => `<textarea class="step-textarea" rows="2" data-scenario="${escapeHtml(s.scenario_id)}" data-step-type="when" data-step-index="${i}">${escapeHtml(st.step_text || '')}</textarea>`).join('')}
          </div>
          <div class="step-group">
            <div class="step-label">Then</div>
            ${s.then_steps.map((st,i) => `<textarea class="step-textarea" rows="2" data-scenario="${escapeHtml(s.scenario_id)}" data-step-type="then" data-step-index="${i}">${escapeHtml(st.step_text || '')}</textarea>`).join('')}
          </div>
        </div>
      `).join('')}
    </div>
  `).join('');
}
async function saveBddEdits() {
  const byScenario = {};
  document.querySelectorAll('.step-textarea').forEach(ta => {
    const sid = ta.dataset.scenario, stype = ta.dataset.stepType, sidx = parseInt(ta.dataset.stepIndex);
    if (!byScenario[sid]) byScenario[sid] = { scenario_id: sid, given_steps: [], when_steps: [], then_steps: [] };
    byScenario[sid][stype + '_steps'][sidx] = { step_text: ta.value, step_pattern: '' };
  });
  const edits = Object.values(byScenario);
  const result = await postJson('/api/bdd/save', { edits });
  document.getElementById('bddStatus').textContent = `已保存 ${result.edit_count} 条编辑到 ${escapeHtml(result.latest_path)}`;
  await loadStageData();
}
function loadScriptsData() {
  fetch('/api/scripts').then(r => r.json()).then(data => {
    scriptsPayload = data;
    renderScriptsTab(data);
  });
}
function matchBadgeClass(type) {
  const map = { exact: 'badge-exact', parameterized: 'badge-parameterized', candidate: 'badge-candidate', unmatched: 'badge-unmatched' };
  return map[type] || '';
}
function renderScriptsTab(data) {
  const el = document.getElementById('scriptsContent');
  if (!data.has_registry) {
    el.innerHTML = '<em>No step registry linked. Run the step-registry pipeline first, then restart the session with --step-registry pointing to step_visibility.json.</em>';
    return;
  }
  const s = data.summary || {};
  el.innerHTML = `
    <div class="scripts-metrics">
      <div class="scripts-metric"><strong>${s.total_steps || 0}</strong><span>Total Steps</span></div>
      <div class="scripts-metric"><strong>${s.exact_matches || 0}</strong><span>Exact Matches</span></div>
      <div class="scripts-metric"><strong>${s.parameterized_matches || 0}</strong><span>Parameterized</span></div>
      <div class="scripts-metric"><strong>${s.unmatched || 0}</strong><span>Unmatched (Gaps)</span></div>
      <div class="scripts-metric"><strong>${s.candidates || 0}</strong><span>Candidates</span></div>
      <div class="scripts-metric"><strong>${s.unique_bdd_patterns || 0}</strong><span>Unique Patterns</span></div>
    </div>
    <div>
      ${['given', 'when', 'then'].map(type => {
        const steps = (data.steps_by_type && data.steps_by_type[type]) || [];
        if (!steps.length) return '';
        return `<div class="step-type-section">
          <h3 style="text-transform:uppercase;">${type} (${steps.length})</h3>
          ${steps.map(step => `
            <div class="step-item ${step.match_type || ''}">
              <div class="step-item-header">
                <span class="step-item-text">${escapeHtml(step.step_text || '')}</span>
                ${step.match_type ? `<span class="step-item-badge ${matchBadgeClass(step.match_type)}">${escapeHtml(step.match_type || '')}</span>` : ''}
              </div>
              ${step.step_pattern ? `<div class="step-item-pattern">${escapeHtml(step.step_pattern || '')}</div>` : ''}
              ${step.library_step_text ? `<div class="step-item-pattern">→ ${escapeHtml(step.library_step_text || '')}</div>` : ''}
              ${step.confidence && step.match_type !== 'exact' ? `<div class="muted" style="font-size:11px;">confidence: ${(step.confidence * 100).toFixed(0)}%</div>` : ''}
              ${step.suggestions && step.suggestions.length ? `<div style="margin-top:4px;"><strong>Suggestions:</strong>${step.suggestions.map(sg => `<div class="suggestion-item">${escapeHtml(sg.library_step_text || '')} (${((sg.similarity || 0) * 100).toFixed(0)}%)</div>`).join('')}</div>` : ''}
            </div>
          `).join('')}
        </div>`;
      }).join('')}
    </div>
    ${(data.gaps && data.gaps.length) ? `<div class="step-type-section">
      <h3 style="color:#991b1b;">GAPS (${data.gaps.length})</h3>
      ${data.gaps.map(g => `<div class="step-item unmatched">
        <div class="step-item-text">${escapeHtml(g.step_text || '')}</div>
        ${g.step_pattern ? `<div class="step-item-pattern">${escapeHtml(g.step_pattern || '')}</div>` : ''}
        ${g.source_scenario_ids && g.source_scenario_ids.length ? `<div class="muted" style="font-size:11px;">来源: ${escapeHtml(g.source_scenario_ids.join(', '))}</div>` : ''}
      </div>`).join('')}
    </div>` : ''}
  `;
}
async function saveScriptsEdits() {
  const edits = scriptsPayload ? Object.values(scriptsPayload).map(d => d) : [];
  const result = await postJson('/api/scripts/save', { edits });
  document.getElementById('scriptsStatus').textContent = `已保存到 ${escapeHtml(result.latest_path)}`;
  await loadStageData();
} new Map((sessionPayload.issue_type_options || []).map(item => [item.code, item])); }
function issueSummaryText(review) { const selected = review.issue_types || []; if (!selected.length) return 'None selected'; const map = issueOptionMap(); return selected.map(code => map.get(code)?.label || code).join(', '); }
function issueTableHtml(review) { return (sessionPayload.issue_type_options || []).map(item => `
    <tr>
      <td><input type="checkbox" data-field="issue_type_option" data-case-id="${escapeHtml(review.case_id)}" data-issue-code="${escapeHtml(item.code)}" ${review.issue_types?.includes(item.code) ? 'checked' : ''}></td>
      <td>${escapeHtml(item.label)}</td>
      <td>${escapeHtml(item.code)}</td>
      <td>${escapeHtml(item.description)}</td>
    </tr>
  `).join(''); }
function reviewControls(review) {
  const caseId = escapeHtml(review.case_id); const blockReview = review.block_recommendation_review;
  return `<div><label>Decision<br/><select data-field="review_decision" data-case-id="${caseId}"><option value="pending" ${review.review_decision === 'pending' ? 'selected' : ''}>pending</option><option value="approve" ${review.review_decision === 'approve' ? 'selected' : ''}>approve</option><option value="rewrite" ${review.review_decision === 'rewrite' ? 'selected' : ''}>rewrite</option><option value="reject" ${review.review_decision === 'reject' ? 'selected' : ''}>reject</option></select></label></div><div><label>Block Recommendation Review<br/><select data-field="block_recommendation_review" data-case-id="${caseId}"><option value="not_applicable" ${blockReview === 'not_applicable' ? 'selected' : ''}>not_applicable</option><option value="pending_review" ${blockReview === 'pending_review' ? 'selected' : ''}>pending_review</option><option value="confirmed" ${blockReview === 'confirmed' ? 'selected' : ''}>confirmed</option><option value="dismissed" ${blockReview === 'dismissed' ? 'selected' : ''}>dismissed</option></select></label></div><div><label>Issue Types</label><details class="issue-picker"><summary class="issue-summary" data-issue-summary="${caseId}">${escapeHtml(issueSummaryText(review))}</summary><table class="issue-table"><thead><tr><th>Select</th><th>Label</th><th>Code</th><th>Description</th></tr></thead><tbody>${issueTableHtml(review)}</tbody></table></details></div><div><label>Comment<br/><textarea data-field="human_comment" data-case-id="${caseId}" rows="4"></textarea></label></div>`;
}
function renderRows() {
  document.getElementById('reviewRows').innerHTML = sessionPayload.table_rows.map(row => { const review = reviewMap.get(row.case_id); return `<tr data-overall="${escapeHtml(row.overall)}" data-coverage="${escapeHtml(row.coverage)}" data-blocking="${String(row.checker_blocking)}"><td>${escapeHtml(row.semantic_rule_id)}</td><td>${escapeHtml(row.case_id)}</td><td>${escapeHtml(row.feature)}</td><td>${escapeHtml(row.case_type)}</td><td>${escapeHtml(row.overall)}</td><td>${escapeHtml(row.coverage)}</td><td>${escapeHtml(String(row.checker_blocking))}</td><td>${escapeHtml(row.blocking_category)}</td><td>${escapeHtml(row.blocking_reason)}</td><td><details><summary>展开</summary>${row.detail_html}</details></td><td>${reviewControls(review)}</td></tr>`; }).join('');
  hydrateControls();
}
function hydrateControls() {
  for (const review of reviewMap.values()) {
    for (const el of document.querySelectorAll(`[data-case-id="${review.case_id}"]`)) {
      const field = el.dataset.field; if (!field) continue;
      if (field === 'issue_type_option') el.checked = (review.issue_types || []).includes(el.dataset.issueCode);
      else if (field === 'human_comment') el.value = review.human_comment || '';
      else el.value = review[field] || '';
      el.addEventListener('change', () => syncField(el)); el.addEventListener('input', () => syncField(el));
    }
    syncIssueSummary(review.case_id);
  }
}
function syncIssueSummary(caseId) { const review = reviewMap.get(caseId); const summary = document.querySelector(`[data-issue-summary="${caseId}"]`); if (review && summary) summary.textContent = issueSummaryText(review); }
function syncField(el) { const review = reviewMap.get(el.dataset.caseId); if (!review) return; const field = el.dataset.field; if (field === 'issue_type_option') { const code = el.dataset.issueCode; const selected = new Set(review.issue_types || []); if (el.checked) selected.add(code); else selected.delete(code); review.issue_types = Array.from(selected); syncIssueSummary(el.dataset.caseId); } else review[field] = el.value; }
function applyFilters() { const overall = document.getElementById('overallFilter').value; const coverage = document.getElementById('coverageFilter').value; const blocking = document.getElementById('blockingFilter').value; for (const row of document.querySelectorAll('#reviewRows tr')) { const show = (!overall || row.dataset.overall === overall) && (!coverage || row.dataset.coverage === coverage) && (!blocking || row.dataset.blocking === blocking); row.style.display = show ? '' : 'none'; } }
async function postJson(url, payload) { const response = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload || {}) }); const data = await response.json(); if (!response.ok) throw new Error(data.error || JSON.stringify(data)); return data; }
function currentPayload() { return { metadata: sessionPayload.metadata, reviews: Array.from(reviewMap.values()) }; }
function renderResult(title, bodyHtml, cssClass='') { const card = document.getElementById('resultCard'); card.style.display = ''; card.innerHTML = `<h2 class="${cssClass}">${escapeHtml(title)}</h2>${bodyHtml}`; }
function renderHistory() { const items = sessionPayload.history || []; document.getElementById('historyCard').innerHTML = items.length ? items.map(item => `<div><strong>Iteration ${item.iteration}</strong>: checker=${escapeHtml(item.checker_summary_path || '')}</div>`).join('') : '暂无历史'; }
function resultLinksHtml(links) { return Object.entries(links || {}).map(([key, href]) => `<div><a href="${href}" target="_blank">${escapeHtml(key)}</a></div>`).join(''); }
async function saveDraft() { const result = await postJson('/api/reviews/save', currentPayload()); renderResult('保存成功', `<div><strong>Iteration</strong>: ${result.iteration}</div><div><strong>Snapshot</strong>: ${escapeHtml(result.saved_review_path)}</div><div><strong>Latest</strong>: ${escapeHtml(result.latest_review_path)}</div>`); }
async function refreshSession() { const response = await fetch('/api/session'); sessionPayload = await response.json(); reviewMap = new Map(sessionPayload.reviews.map(item => [item.case_id, item])); document.getElementById('summaryCard').innerHTML = `<div class="grid"><div class="metric"><strong>Session ID</strong><br/>${escapeHtml(sessionPayload.session_id)}</div><div class="metric"><strong>Status</strong><br/>${escapeHtml(sessionPayload.session_status)}</div><div class="metric"><strong>Current Iteration</strong><br/>${escapeHtml(String(sessionPayload.current_iteration))}</div></div><div class="muted">Latest review path: ${escapeHtml(sessionPayload.metadata.latest_review_path || '')}</div><div class="muted">Current report path: ${escapeHtml(sessionPayload.metadata.current_report_path || '')}</div>`; renderRows(); renderHistory(); applyFilters(); await loadStageData(); }
async function pollJob(jobId) { const response = await fetch(`/api/status/${jobId}`); const payload = await response.json(); if (payload.status === 'queued' || payload.status === 'running') { renderResult('后台执行中', `<div class="status-running">状态: ${escapeHtml(payload.status)}</div>`, 'status-running'); pollTimer = setTimeout(() => pollJob(jobId), 2000); return; } if (payload.status === 'failed') { renderResult('执行失败', `<pre>${escapeHtml(payload.error || '')}</pre>`, 'status-failed'); return; } const result = payload.result || {}; await refreshSession(); renderResult('执行成功', `<div class="status-succeeded">状态: ${escapeHtml(payload.status)}</div><div><strong>Next Iteration</strong>: ${escapeHtml(String(result.next_iteration || ''))}</div><pre>${escapeHtml(JSON.stringify({ rewrite_summary: result.rewrite_summary, checker_summary: result.checker_summary, report_summary: result.report_summary }, null, 2))}</pre><div>${resultLinksHtml(result.links)}</div>`, 'status-succeeded'); }
async function submitAndRun() { if (pollTimer) clearTimeout(pollTimer); const result = await postJson('/api/submit', currentPayload()); renderResult('已提交', `<div>Job ID: ${escapeHtml(result.job_id)}</div><div>Latest: ${escapeHtml(result.latest_review_path)}</div>`); pollJob(result.job_id); }
async function finalizeSession() { const result = await postJson('/api/finalize', {}); if (result.final_report_url) { window.location.href = result.final_report_url; return; } await refreshSession(); renderResult('Session Finalized', `<div class="status-finalized">??: ${escapeHtml(result.status)}</div><div><strong>Final Report</strong>: ${escapeHtml(result.final_report_path || "")}</div><div>${resultLinksHtml({ report_html: result.final_report_url, maker_html: result.final_maker_url, checker_html: result.final_checker_url })}</div>`, 'status-finalized'); }
async function bootstrap() { await refreshSession(); document.getElementById('overallFilter').addEventListener('change', applyFilters); document.getElementById('coverageFilter').addEventListener('change', applyFilters); document.getElementById('blockingFilter').addEventListener('change', applyFilters); document.getElementById('saveBtn').addEventListener('click', saveDraft); document.getElementById('submitBtn').addEventListener('click', submitAndRun); document.getElementById('finalizeBtn').addEventListener('click', finalizeSession); document.querySelectorAll('.tab-btn').forEach(btn => btn.addEventListener('click', () => switchTab(btn.dataset.tab))); document.getElementById('saveBddBtn').addEventListener('click', saveBddEdits); document.getElementById('saveScriptsBtn').addEventListener('click', saveScriptsEdits); document.querySelectorAll('.stage-step').forEach(el => el.addEventListener('click', () => { const stage = el.dataset.stage; if (stage === 'finalize') { if (confirm('Finalize this review session? No further edits will be possible.')) finalizeSession(); } else { const tab = STAGE_TAB_MAP[stage]; if (tab) switchTab(tab); } })); }
bootstrap();
</script>
</body>
</html>
"""
