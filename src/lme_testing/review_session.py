
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
from .bdd_export import apply_human_step_edits
from .pipelines import _case_map_from_maker_records, run_bdd_pipeline, run_checker_pipeline, run_rewrite_pipeline
from .reporting import generate_html_report
from .schemas import load_issue_type_options, validate_human_review_payload
from .storage import atomic_write_json, ensure_dir, load_json, load_jsonl, timestamp_slug
from .step_registry import (
    compute_step_matches,
    extract_steps_from_normalized_bdd,
    extract_steps_from_python_step_defs,
    render_step_visibility_report,
)
from .audit_trail import build_audit_trail
from .case_compare import build_case_compare

logger = logging.getLogger(__name__)


@dataclass
class ReviewJobStatus:
    job_id: str
    status: str
    iteration: int
    phase: str = "queued"
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
        rewrite_concurrency: int = 1,
        checker_concurrency: int = 1,
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
        self.rewrite_concurrency = rewrite_concurrency
        self.checker_concurrency = checker_concurrency
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
        atomic_write_json(snapshot_path, normalized)
        atomic_write_json(latest_path, normalized)
        state["iterations"][str(iteration)]["human_reviews_latest_path"] = str(latest_path)
        reviews = normalized.get("reviews", [])
        any_decided = any(r.get("review_decision", "pending") != "pending" for r in reviews)
        if any_decided:
            if "stage_gates" not in state:
                state["stage_gates"] = {"review_decided": False, "bdd_edited": False, "scripts_viewed": False}
            state["stage_gates"]["review_decided"] = True
            if "stage_gates" not in state["iterations"][str(iteration)]:
                state["iterations"][str(iteration)]["stage_gates"] = {"review_decided": False, "bdd_edited": False, "scripts_viewed": False}
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

        # Also write BDD edits to human_scripts_edits_latest.json (merged) so the
        # rewrite pipeline picks them up via apply_human_step_edits.
        # Load existing Scripts tab edits first so we don't overwrite them.
        scripts_latest = state.get("human_scripts_edits_latest_path")
        scripts_edits = []
        if scripts_latest:
            scripts_path = Path(scripts_latest)
            if scripts_path.exists():
                existing = load_json(scripts_path)
                scripts_edits = existing.get("edits", []) if isinstance(existing, dict) else []

        # Flatten BDD tab edits into apply_human_step_edits-compatible format:
        # {scenario_id, step_type, step_index, step_text}
        flat_edits: list[dict[str, Any]] = []
        for edit in edits:
            sid = edit.get("scenario_id", "")
            for step_type in ("given", "when", "then"):
                steps = edit.get(f"{step_type}_steps", [])
                for idx, step in enumerate(steps):
                    if isinstance(step, dict) and step.get("step_text"):
                        flat_edits.append({
                            "scenario_id": sid,
                            "step_type": step_type,
                            "step_index": idx,
                            "step_text": step["step_text"],
                        })
                    elif isinstance(step, str) and step:
                        flat_edits.append({
                            "scenario_id": sid,
                            "step_type": step_type,
                            "step_index": idx,
                            "step_text": step,
                        })

        merged_edits = scripts_edits + flat_edits
        scripts_snapshot = bdd_dir / f"human_scripts_edits_{timestamp}.json"
        scripts_latest_path = bdd_dir / "human_scripts_edits_latest.json"
        latest_path = bdd_dir / "human_bdd_edits_latest.json"
        atomic_write_json(scripts_snapshot, {"edits": merged_edits, "timestamp": timestamp})
        atomic_write_json(scripts_latest_path, {"edits": merged_edits, "timestamp": timestamp})

        # Persist the merged scripts path in state so _run_job passes it to the pipeline
        state["human_scripts_edits_latest_path"] = str(scripts_latest_path)
        state["human_bdd_edits_latest_path"] = str(latest_path)
        state["iterations"][str(iteration)]["human_scripts_edits_latest_path"] = str(scripts_latest_path)
        state["iterations"][str(iteration)]["human_bdd_edits_latest_path"] = str(latest_path)

        # Keep human_bdd_edits_latest.json as an audit trail (BDD-tab-native format)
        atomic_write_json(snapshot_path, {"edits": edits, "timestamp": timestamp})
        atomic_write_json(latest_path, {"edits": edits, "timestamp": timestamp})

        if flat_edits:
            if "stage_gates" not in state:
                state["stage_gates"] = {"review_decided": False, "bdd_edited": False, "scripts_viewed": False}
            state["stage_gates"]["bdd_edited"] = True
            if "stage_gates" not in state["iterations"][str(iteration)]:
                state["iterations"][str(iteration)]["stage_gates"] = {"review_decided": False, "bdd_edited": False, "scripts_viewed": False}
            state["iterations"][str(iteration)]["stage_gates"]["bdd_edited"] = True
        refresh_result = self._refresh_reviewed_bdd_and_step_registry(state, iteration)
        self._save_manifest(state)
        logger.info("Saved BDD edits. session_id=%s iteration=%s saved=%s latest=%s flat_edit_count=%s merged_edit_count=%s", state["session_id"], iteration, snapshot_path, latest_path, len(flat_edits), len(merged_edits))
        return {
            "saved_path": str(snapshot_path),
            "latest_path": str(latest_path),
            "edit_count": len(flat_edits),
            "merged_edit_count": len(merged_edits),
            **refresh_result,
        }

    def scripts_payload(self) -> dict[str, Any]:
        """Return step registry visibility data for the Scripts tab."""
        state = self._load_state()
        iteration = int(state["current_iteration"])
        # Mark scripts as viewed when tab is loaded
        if "stage_gates" not in state:
            state["stage_gates"] = {"review_decided": False, "bdd_edited": False, "scripts_viewed": False}
        state["stage_gates"]["scripts_viewed"] = True
        if "stage_gates" not in state["iterations"][str(iteration)]:
            state["iterations"][str(iteration)]["stage_gates"] = {"review_decided": False, "bdd_edited": False, "scripts_viewed": False}
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
        edits = self._enrich_script_edits(payload.get("edits", []), state, iteration)
        preserved_bdd_edits = self._existing_bdd_flat_edits(state)
        merged_edits = preserved_bdd_edits + edits
        timestamp = timestamp_slug()
        snapshot_path = scripts_dir / f"human_scripts_edits_{timestamp}.json"
        latest_path = scripts_dir / "human_scripts_edits_latest.json"
        atomic_write_json(snapshot_path, {"edits": merged_edits, "timestamp": timestamp})
        atomic_write_json(latest_path, {"edits": merged_edits, "timestamp": timestamp})
        # Persist path in state so rewrite jobs can find it
        state["human_scripts_edits_latest_path"] = str(latest_path)
        state["iterations"][str(iteration)]["human_scripts_edits_latest_path"] = str(latest_path)
        refresh_result = self._refresh_reviewed_bdd_and_step_registry(state, iteration)
        self._save_manifest(state)
        logger.info("Saved scripts edits. session_id=%s iteration=%s saved=%s latest=%s edit_count=%s merged_edit_count=%s", state["session_id"], iteration, snapshot_path, latest_path, len(edits), len(merged_edits))
        return {"saved_path": str(snapshot_path), "latest_path": str(latest_path), "edit_count": len(edits), "merged_edit_count": len(merged_edits), **refresh_result}

    def _existing_bdd_flat_edits(self, state: dict[str, Any]) -> list[dict]:
        """Preserve BDD-tab edits when Scripts-tab edits replace script edits."""
        scripts_latest = state.get("human_scripts_edits_latest_path")
        if not scripts_latest:
            return []
        scripts_path = Path(scripts_latest)
        if not scripts_path.exists():
            return []
        existing = load_json(scripts_path)
        if not isinstance(existing, dict):
            return []
        return [
            edit
            for edit in existing.get("edits", [])
            if isinstance(edit, dict) and edit.get("scenario_id")
        ]

    def _enrich_script_edits(self, edits: list[dict], state: dict[str, Any], iteration: int) -> list[dict]:
        """Attach registry metadata needed to apply Scripts-tab edits deterministically."""
        step_registry_path = state.get("step_registry_path") or state["iterations"][str(iteration)].get("step_registry_path")
        registry_data: dict[str, Any] = {}
        if step_registry_path and Path(step_registry_path).exists():
            registry_data = load_json(Path(step_registry_path))

        enriched: list[dict] = []
        for edit in edits:
            item = dict(edit)
            if item.get("is_gap"):
                gap_index = item.get("gap_index")
                gaps = registry_data.get("gaps", []) if isinstance(registry_data, dict) else []
                if isinstance(gap_index, int) and 0 <= gap_index < len(gaps):
                    gap = gaps[gap_index]
                    item.setdefault("step_type", gap.get("step_type", ""))
                    item.setdefault("source_scenario_ids", gap.get("source_scenario_ids", []))
                    item.setdefault("original_step_text", gap.get("step_text", ""))
                    item.setdefault("original_step_pattern", gap.get("step_pattern", ""))
            else:
                step_type = item.get("step_type", "")
                step_index = item.get("step_index")
                steps = registry_data.get(f"{step_type}_steps", []) if isinstance(registry_data, dict) else []
                if isinstance(step_index, int) and 0 <= step_index < len(steps):
                    step = steps[step_index]
                    item.setdefault("source_scenario_ids", step.get("source_scenario_ids", []))
                    item.setdefault("original_step_text", step.get("step_text", ""))
                    item.setdefault("original_step_pattern", step.get("step_pattern", ""))
            enriched.append(item)
        return enriched

    def _refresh_reviewed_bdd_and_step_registry(self, state: dict[str, Any], iteration: int) -> dict[str, Any]:
        """Materialize reviewed BDD and refresh step matching after UI edits.

        The original normalized BDD remains the governed source artifact. Review
        edits are exported to an iteration-local reviewed artifact, and the
        Scripts tab points at a refreshed step visibility report.
        """
        source_bdd_path = self._source_normalized_bdd_path(state, iteration)
        human_scripts_path = state.get("human_scripts_edits_latest_path")
        if not source_bdd_path or not Path(source_bdd_path).exists() or not human_scripts_path:
            return {"reviewed_bdd_path": None, "refreshed_step_registry_path": None}
        human_scripts_path_obj = Path(human_scripts_path)
        if not human_scripts_path_obj.exists():
            return {"reviewed_bdd_path": None, "refreshed_step_registry_path": None}

        bdd_dir = ensure_dir(self._iteration_dir(iteration) / "bdd")
        timestamp = timestamp_slug()
        reviewed_snapshot = bdd_dir / f"reviewed_normalized_bdd_{timestamp}.jsonl"
        reviewed_latest = bdd_dir / "reviewed_normalized_bdd_latest.jsonl"
        registry_snapshot = bdd_dir / f"step_visibility_{timestamp}.json"
        registry_latest = bdd_dir / "step_visibility_latest.json"

        bdd_records = load_jsonl(Path(source_bdd_path))
        reviewed_records = apply_human_step_edits(bdd_records, human_scripts_path_obj)
        self._atomic_write_jsonl(reviewed_snapshot, reviewed_records)
        self._atomic_write_jsonl(reviewed_latest, reviewed_records)

        library_path = self.repo_root / "src" / "lme_testing" / "step_library.py"
        bdd_inventory = extract_steps_from_normalized_bdd(reviewed_latest)
        library_inventory = extract_steps_from_python_step_defs(library_path)
        report = compute_step_matches(bdd_inventory, library_inventory)
        render_step_visibility_report(bdd_inventory, report, registry_snapshot)
        render_step_visibility_report(bdd_inventory, report, registry_latest)

        state["normalized_bdd_path"] = str(reviewed_latest)
        state["step_registry_path"] = str(registry_latest)
        state["iterations"][str(iteration)]["normalized_bdd_path"] = str(reviewed_latest)
        state["iterations"][str(iteration)]["step_registry_path"] = str(registry_latest)
        return {
            "reviewed_bdd_path": str(reviewed_latest),
            "refreshed_step_registry_path": str(registry_latest),
            "reviewed_bdd_snapshot_path": str(reviewed_snapshot),
            "refreshed_step_registry_snapshot_path": str(registry_snapshot),
        }

    def _source_normalized_bdd_path(self, state: dict[str, Any], iteration: int) -> str | None:
        iteration_state = state["iterations"][str(iteration)]
        source_path = iteration_state.get("source_normalized_bdd_path") or state.get("source_normalized_bdd_path")
        if source_path:
            return source_path
        current_path = state.get("normalized_bdd_path") or iteration_state.get("normalized_bdd_path")
        if current_path:
            state["source_normalized_bdd_path"] = current_path
            iteration_state["source_normalized_bdd_path"] = current_path
        return current_path

    def _atomic_write_jsonl(self, path: Path, records: list[dict]) -> None:
        tmp = path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, ensure_ascii=False))
                handle.write("\n")
        tmp.replace(path)

    def submit_reviews(self, payload: dict[str, Any]) -> dict[str, Any]:
        # Un-finalize the session if the user returns after viewing the final report
        # and wants to start a new review iteration
        state = self._load_state()
        if state.get("status") == "finalized":
            state["status"] = "running"
            self._save_manifest(state)
            logger.info("Session un-finalized for new iteration. session_id=%s", self.session_id)
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
        atomic_write_json(final_manifest, state)
        self._save_manifest(state)
        audit_trail_path = final_dir / "audit_trail.html"
        try:
            trail_result = build_audit_trail(self.session_dir, audit_trail_path)
            state["audit_trail_path"] = str(audit_trail_path)
            atomic_write_json(final_manifest, state)
            self._save_manifest(state)
            logger.info("Audit trail generated. path=%s divergent_count=%s", audit_trail_path, trail_result.get("divergent_count"))
        except Exception:
            logger.warning("Audit trail generation failed. session_id=%s error=%s", self.session_id, traceback.format_exc())
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
            "audit_trail_path": str(audit_trail_path) if audit_trail_path.exists() else None,
        }

    def rebuild_audit_trail(self) -> dict[str, Any]:
        """Rebuild audit_trail.html against the current iteration set."""
        audit_path = self.session_dir / "audit_trail.html"
        result = build_audit_trail(self.session_dir, audit_path)
        state = self._load_state()
        state["audit_trail_path"] = str(audit_path)
        self._save_manifest(state)
        return {
            "audit_trail_path": str(audit_path),
            "audit_trail_url": self._file_url(audit_path),
            "divergent_count": result.get("divergent_count", 0),
        }

    def job_status(self, job_id: str) -> dict[str, Any]:
        with self._lock:
            status = self._jobs.get(job_id)
        if not status:
            raise KeyError(job_id)
        return {
            "job_id": status.job_id,
            "status": status.status,
            "phase": status.phase,
            "iteration": status.iteration,
            "saved_review_path": status.saved_review_path,
            "latest_review_path": status.latest_review_path,
            "error": status.error,
            "result": status.result,
        }

    def _set_phase(self, job_id: str, phase: str) -> None:
        with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id].phase = phase

    def _run_job(self, job_id: str, iteration: int, human_reviews_path: Path) -> None:
        with self._lock:
            self._jobs[job_id].status = "running"
            self._jobs[job_id].phase = "rewrite"
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
                concurrency=self.rewrite_concurrency,
                human_scripts_edits_path=Path(state.get("human_scripts_edits_latest_path") or ""),
            )
            next_iteration = iteration + 1

            compare_path: Path | None = None
            rewritten_case_ids: set[str] = set(rewrite_summary.get("rewritten_case_ids", []))
            try:
                if rewritten_case_ids:
                    prev_cases_path = Path(state["current_maker_cases_path"])
                    compare_out = self._iteration_dir(iteration) / f"compare_iter_{iteration:03d}_vs_{next_iteration:03d}.html"
                    build_case_compare(
                        prev_cases_path=prev_cases_path,
                        next_cases_path=Path(rewrite_summary["merged_cases_path"]),
                        rewritten_case_ids=rewritten_case_ids,
                        iteration_prev=iteration,
                        iteration_next=next_iteration,
                        output_html_path=compare_out,
                        display_iteration=iteration,
                    )
                    compare_path = compare_out
            except Exception:
                logger.exception("build_case_compare failed; continuing without compare file.")

            self._set_phase(job_id, "checker")
            checker_summary = run_checker_pipeline(
                config=self.config,
                semantic_rules_path=self.rules_path,
                maker_cases_path=Path(rewrite_summary["merged_cases_path"]),
                output_dir=checker_dir,
                limit=None,
                batch_size=self.checker_batch_size,
                resume_from=None,
                concurrency=self.checker_concurrency,
                only_case_ids=rewritten_case_ids if rewritten_case_ids else None,
                previous_reviews_path=Path(state["current_checker_reviews_path"]) if rewritten_case_ids else None,
            )

            # Re-run BDD pipeline so rewritten maker cases get fresh normalized_bdd
            # with human (BDD tab + Scripts tab) edits applied.
            bdd_dir = ensure_dir(self._iteration_dir(iteration) / "bdd")
            human_scripts_path = state.get("human_scripts_edits_latest_path")
            bdd_summary = None
            if human_scripts_path and Path(human_scripts_path).exists():
                try:
                    bdd_summary = run_bdd_pipeline(
                        config=self.config,
                        maker_cases_path=Path(rewrite_summary["merged_cases_path"]),
                        output_dir=bdd_dir,
                        limit=None,
                        batch_size=self.checker_batch_size,
                        resume_from=None,
                        human_scripts_edits_path=Path(human_scripts_path),
                    )
                    curr_normalized = bdd_summary.get("results_path") or state.get("normalized_bdd_path")
                    state["iterations"][str(iteration)]["normalized_bdd_path"] = curr_normalized
                    logger.info("BDD pipeline re-run after rewrite. session_id=%s iteration=%s results_path=%s", self.session_id, iteration, curr_normalized)
                except Exception:
                    logger.warning("BDD pipeline re-run failed after rewrite (BDD tab edits not applied). session_id=%s error=%s", self.session_id, traceback.format_exc())
                    curr_normalized = state.get("normalized_bdd_path") or state["iterations"][str(iteration)].get("normalized_bdd_path")
            else:
                curr_normalized = state.get("normalized_bdd_path") or state["iterations"][str(iteration)].get("normalized_bdd_path")
            curr_step_reg = state.get("step_registry_path") or state["iterations"][str(iteration)].get("step_registry_path")

            self._set_phase(job_id, "report")
            state["history"].append(
                {
                    "iteration": iteration,
                    "next_iteration": next_iteration,
                    "human_reviews_path": str(human_reviews_path),
                    "rewrite_summary_path": str(Path(rewrite_summary["output_dir"]) / "summary.json"),
                    "checker_summary_path": str(Path(checker_summary["output_dir"]) / "summary.json"),
                    "coverage_report_path": checker_summary["coverage_report_path"],
                    "compare_path": str(compare_path) if compare_path else None,
                }
            )
            state["iterations"][str(iteration)]["rewrite_summary_path"] = str(Path(rewrite_summary["output_dir"]) / "summary.json")
            state["iterations"][str(iteration)]["checker_summary_path"] = str(Path(checker_summary["output_dir"]) / "summary.json")
            state["iterations"][str(iteration)]["coverage_report_path"] = checker_summary["coverage_report_path"]

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
                "normalized_bdd_path": curr_normalized,
                "step_registry_path": curr_step_reg,
                "stage_gates": {"review_decided": False, "bdd_edited": False, "scripts_viewed": False},
            }
            state["iterations"][str(next_iteration)] = next_state
            state["current_iteration"] = next_iteration
            state["current_maker_cases_path"] = rewrite_summary["merged_cases_path"]
            state["current_checker_reviews_path"] = checker_summary["results_path"]
            state["normalized_bdd_path"] = curr_normalized
            state["step_registry_path"] = curr_step_reg
            report_path = self._render_iteration_report(next_iteration, state=state)
            next_state["report_path"] = str(report_path)
            state["current_report_path"] = str(report_path)
            self._save_manifest(state)
            logger.info("Review-session job succeeded. session_id=%s job_id=%s next_iteration=%s report=%s", self.session_id, job_id, next_iteration, report_path)

            result = {
                "rewrite_summary": rewrite_summary,
                "checker_summary": checker_summary,
                "bdd_summary": bdd_summary,
                "report_summary": {
                    "output_html": str(report_path),
                    "maker_html": str(report_path.with_name("maker_readable.html")),
                    "checker_html": str(report_path.with_name("checker_readable.html")),
                },
                "next_iteration": next_iteration,
                "history_iteration": iteration,
                "compare_path": str(compare_path) if compare_path else None,
                "links": {
                    "human_reviews_latest": self._file_url(Path(next_state["human_reviews_latest_path"])),
                    "rewritten_cases": self._file_url(Path(rewrite_summary["rewritten_cases_path"])),
                    "merged_cases": self._file_url(Path(rewrite_summary["merged_cases_path"])),
                    "checker_reviews": self._file_url(Path(checker_summary["results_path"])),
                    "coverage_report": self._file_url(Path(checker_summary["coverage_report_path"])),
                    "report_html": self._file_url(report_path),
                    "compare_html": self._file_url(compare_path) if compare_path else None,
                    "case_compare_html": self._file_url(compare_path) if compare_path else None,
                    "normalized_bdd": self._file_url(Path(curr_normalized)) if curr_normalized else None,
                },
            }
            with self._lock:
                self._jobs[job_id].status = "succeeded"
                self._jobs[job_id].phase = "done"
                self._jobs[job_id].result = result
        except Exception as exc:  # pragma: no cover
            logger.exception("Review-session job failed. session_id=%s job_id=%s iteration=%s", self.session_id, job_id, iteration)
            with self._lock:
                self._jobs[job_id].status = "failed"
                self._jobs[job_id].phase = "failed"
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
                seeded.append(
                    {
                        "case_id": case_id,
                        "semantic_rule_id": semantic_rule_id,
                        "review_decision": "pending",
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
            audit_trail_path=Path(state["audit_trail_path"]) if state.get("audit_trail_path") else None,
            audit_trail_url=self._file_url(Path(state["audit_trail_path"])) if state.get("audit_trail_path") else None,
            compare_links=self._report_compare_links(state),
        )
        return report_output

    def _report_compare_links(self, state: dict[str, Any]) -> list[dict[str, str]]:
        links: list[dict[str, str]] = []
        for item in state.get("history", []):
            compare_path = item.get("compare_path")
            if not compare_path:
                continue
            iteration = item.get("iteration")
            next_iteration = item.get("next_iteration")
            if next_iteration is None:
                try:
                    next_iteration = int(iteration) + 1
                except Exception:
                    next_iteration = ""
            label = f"Iteration {iteration} Compare"
            if next_iteration != "":
                label = f"Iteration {iteration} -> {next_iteration} Compare"
            links.append({"label": label, "path": str(compare_path), "url": self._file_url(Path(compare_path))})
        return links

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
        atomic_write_json(self.manifest_path, self._state)

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
                if parsed.path == "/api/audit_trail":
                    self._send_json(manager.rebuild_audit_trail())
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
                if parsed.path == "/coverage.csv":
                    csv_path = manager.current_report_file("report").with_suffix(".csv")
                    self._send_download(csv_path, repo_root)
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

        def _send_download(self, raw_path: Path, root: Path) -> None:
            """Serve a file as a forced download with Content-Disposition header."""
            if not raw_path.exists() or not raw_path.is_file():
                self.send_error(HTTPStatus.NOT_FOUND, "File not found")
                return
            try:
                raw_path.relative_to(root)
            except ValueError:
                self.send_error(HTTPStatus.FORBIDDEN, "Path outside repo root")
                return
            content = raw_path.read_bytes()
            filename = raw_path.name
            mime_type = mimetypes.guess_type(str(raw_path))[0] or "application/octet-stream"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Content-Disposition", f"attachment; filename={filename}")
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
    button:disabled { opacity: 0.5; cursor: not-allowed; }
    ul { margin: 8px 0 0 18px; }
    pre { white-space: pre-wrap; word-break: break-word; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; font-size: 12px; }
    .progress-wrap { margin-top: 8px; background: #e2e8f0; border-radius: 8px; height: 18px; overflow: hidden; }
    .progress-bar { height: 100%; background: linear-gradient(90deg, #3b82f6, #6366f1); width: 0%; transition: width 0.4s ease; }
    .progress-label { font-size: 12px; color: #334155; margin-top: 4px; }
    .history-row { padding: 6px 0; border-bottom: 1px dashed #e2e8f0; }
    .history-row:last-child { border-bottom: none; }
    .history-row.current { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 8px 10px; }
    .history-row a { margin-left: 10px; }
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
      <li><strong>Decision</strong>: 人工最终动作。<code>approve</code> 表示放行，<code>rewrite</code> 表示回流给 maker 重写。人工与 checker 判断的分歧会自动记录到 Audit Trail，不需要再手动打二次标签。</li>
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
      <button id="auditBtn">查看 Audit Trail</button>
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
const PHASE_PROGRESS = { queued: 5, rewrite: 20, checker: 55, report: 90, done: 100, failed: 100 };
const PHASE_LABEL = { queued: '已排队', rewrite: '正在重写 cases', checker: '正在 checker 复检', report: '正在生成报告', done: '完成', failed: '失败' };
let bddPayload = null;
let scriptsPayload = null;
let bddDirty = false;
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
  if (tab === 'bdd' && (!bddPayload || !bddDirty)) loadBddData();
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
  bddDirty = false;
  document.querySelectorAll('#bddContent textarea[data-scenario]').forEach(ta => {
    ta.addEventListener('input', () => { bddDirty = true; });
  });
}
async function saveBddEdits() {
  try {
    const byScenario = {};
    document.querySelectorAll('#bddContent textarea[data-scenario]').forEach(ta => {
      const sid = String(ta.dataset.scenario || '');
      const stype = String(ta.dataset.stepType || '').toLowerCase();
      const sidx = parseInt(ta.dataset.stepIndex || '0', 10);
      if (!sid || !stype) return;
      if (!byScenario[sid]) byScenario[sid] = { scenario_id: sid, given_steps: [], when_steps: [], then_steps: [] };
      const stepsKey = stype + '_steps';
      if (!byScenario[sid][stepsKey]) byScenario[sid][stepsKey] = [];
      byScenario[sid][stepsKey][sidx] = { step_text: ta.value, step_pattern: '' };
    });
    const edits = Object.values(byScenario);
    const result = await postJson('/api/bdd/save', { edits });
    document.getElementById('bddStatus').textContent = `已保存 ${result.edit_count} 条编辑到 ${escapeHtml(result.latest_path)}；reviewed BDD: ${escapeHtml(result.reviewed_bdd_path || '')}`;
    scriptsPayload = null;
    bddDirty = false;
    await loadStageData();
  } catch (err) {
    document.getElementById('bddStatus').textContent = `保存失败: ${err.message}`;
    console.error('saveBddEdits error:', err);
  }
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
          ${steps.map((step, idx) => `
            <div class="step-item ${step.match_type || ''}">
              <div class="step-item-header">
                <span class="step-item-badge ${matchBadgeClass(step.match_type)}">${escapeHtml(step.match_type || 'unmatched')}</span>
                ${step.source_scenario_ids && step.source_scenario_ids.length ? `<span class="muted" style="font-size:11px;">来源: ${escapeHtml(step.source_scenario_ids.join(', '))}</span>` : ''}
              </div>
              <textarea class="step-textarea" data-step-type="${type}" data-step-index="${idx}" rows="2" placeholder="step text">${escapeHtml(step.step_text || '')}</textarea>
              ${step.step_pattern ? `<div class="step-item-pattern">pattern: ${escapeHtml(step.step_pattern || '')}</div>` : ''}
              ${step.library_step_text ? `<div class="step-item-pattern">→ lib: ${escapeHtml(step.library_step_text || '')}</div>` : ''}
              ${step.confidence && step.match_type !== 'exact' ? `<div class="muted" style="font-size:11px;">confidence: ${(step.confidence * 100).toFixed(0)}%</div>` : ''}
              ${step.suggestions && step.suggestions.length ? `<div style="margin-top:4px;"><strong>Suggestions:</strong>${step.suggestions.map(sg => `<div class="suggestion-item">${escapeHtml(sg.library_step_text || '')} (${((sg.similarity || 0) * 100).toFixed(0)}%)</div>`).join('')}</div>` : ''}
            </div>
          `).join('')}
        </div>`;
      }).join('')}
    </div>
    ${(data.gaps && data.gaps.length) ? `<div class="step-type-section">
      <h3 style="color:#991b1b;">GAPS (${data.gaps.length}) — 需要人工实现</h3>
      ${data.gaps.map((g, idx) => `
        <div class="step-item unmatched">
          <div class="step-item-header">
            <span class="step-item-badge badge-unmatched">GAP</span>
            ${g.source_scenario_ids && g.source_scenario_ids.length ? `<span class="muted" style="font-size:11px;">来源: ${escapeHtml(g.source_scenario_ids.join(', '))}</span>` : ''}
          </div>
          <textarea class="step-textarea" data-gap-index="${idx}" data-step-type="${escapeHtml(g.step_type || '')}" rows="2" placeholder="step text (editable)">${escapeHtml(g.step_text || '')}</textarea>
          ${g.step_pattern ? `<div class="step-item-pattern">pattern: ${escapeHtml(g.step_pattern || '')}</div>` : ''}
        </div>`).join('')}
    </div>` : ''}
  `;
}
async function saveScriptsEdits() {
  const edits = [];
  document.querySelectorAll('.step-textarea[data-step-type]:not([data-gap-index])').forEach(ta => {
    edits.push({
      step_type: ta.dataset.stepType,
      step_index: parseInt(ta.dataset.stepIndex),
      step_text: ta.value,
    });
  });
  document.querySelectorAll('.step-textarea[data-gap-index]').forEach(ta => {
    edits.push({
      is_gap: true,
      gap_index: parseInt(ta.dataset.gapIndex),
      step_type: ta.dataset.stepType,
      step_text: ta.value,
    });
  });
  const result = await postJson('/api/scripts/save', { edits });
  document.getElementById('scriptsStatus').textContent = `已保存到 ${escapeHtml(result.latest_path)}；匹配报告: ${escapeHtml(result.refreshed_step_registry_path || '')}`;
  scriptsPayload = null;
  await loadScriptsData();
  await loadStageData();
}
function issueOptionMap() { return new Map((sessionPayload.issue_type_options || []).map(item => [item.code, item])); }
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
  const caseId = escapeHtml(review.case_id);
  return `<div><label>Decision<br/><select data-field="review_decision" data-case-id="${caseId}"><option value="pending" ${review.review_decision === 'pending' ? 'selected' : ''}>pending</option><option value="approve" ${review.review_decision === 'approve' ? 'selected' : ''}>approve</option><option value="rewrite" ${review.review_decision === 'rewrite' ? 'selected' : ''}>rewrite</option></select></label></div><div><label>Issue Types</label><details class="issue-picker"><summary class="issue-summary" data-issue-summary="${caseId}">${escapeHtml(issueSummaryText(review))}</summary><table class="issue-table"><thead><tr><th>Select</th><th>Label</th><th>Code</th><th>Description</th></tr></thead><tbody>${issueTableHtml(review)}</tbody></table></details></div><div><label>Comment<br/><textarea data-field="human_comment" data-case-id="${caseId}" rows="4"></textarea></label></div>`;
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
function hideResult() { const card = document.getElementById('resultCard'); card.style.display = 'none'; card.innerHTML = ''; }
function renderProgress(percent, label) { const safe = Math.max(0, Math.min(100, percent)); const body = `<div class="progress-wrap"><div class="progress-bar" style="width:${safe}%"></div></div><div class="progress-label">${escapeHtml(label)} · ${safe}%</div>`; renderResult('后台执行中', body, 'status-running'); }
function compareLinkHtml(item) { if (!item.compare_path) return ''; const url = `/files?path=${encodeURIComponent(item.compare_path)}`; return `<a href="${url}" target="_blank">View Changes</a>`; }
function renderHistory(currentIteration = null) { const items = sessionPayload.history || []; const container = document.getElementById('historyCard'); if (!items.length) { container.textContent = '暂无历史'; return; } container.innerHTML = items.map(item => { const isCurrent = currentIteration !== null && Number(item.iteration) === Number(currentIteration); const nextIteration = item.next_iteration ?? (Number.isFinite(Number(item.iteration)) ? Number(item.iteration) + 1 : ''); const title = nextIteration === '' ? `Iteration ${escapeHtml(String(item.iteration))} changes` : `Iteration ${escapeHtml(String(item.iteration))} -> ${escapeHtml(String(nextIteration))} changes`; const compare = compareLinkHtml(item); const compareHint = compare ? compare : '<span class="muted">本次没有 case 修改</span>'; return `<div class="history-row ${isCurrent ? 'current' : ''}"><strong>${title}</strong>${isCurrent ? ' <span class="status-succeeded">本次迭代</span>' : ''}<div>${compareHint}</div></div>`; }).join(''); }
function resultLinksHtml(links) { return Object.entries(links || {}).map(([key, href]) => `<div><a href="${href}" target="_blank">${escapeHtml(key)}</a></div>`).join(''); }
async function saveDraft() { const result = await postJson('/api/reviews/save', currentPayload()); renderResult('保存成功', `<div>Iteration ${escapeHtml(String(result.iteration))} 草稿已保存</div>`); }
async function refreshSession(currentIteration = null) { const response = await fetch('/api/session'); sessionPayload = await response.json(); reviewMap = new Map(sessionPayload.reviews.map(item => [item.case_id, item])); document.getElementById('summaryCard').innerHTML = `<div class="grid"><div class="metric"><strong>Session ID</strong><br/>${escapeHtml(sessionPayload.session_id)}</div><div class="metric"><strong>Status</strong><br/>${escapeHtml(sessionPayload.session_status)}</div><div class="metric"><strong>Current Iteration</strong><br/>${escapeHtml(String(sessionPayload.current_iteration))}</div></div>`; renderRows(); renderHistory(currentIteration); applyFilters(); await loadStageData(); }
function iterationCompareLink(iteration) { const item = (sessionPayload.history || []).find(entry => Number(entry.iteration) === Number(iteration)); return item ? compareLinkHtml(item) : ''; }
async function pollJob(jobId) { const response = await fetch(`/api/status/${jobId}`); const payload = await response.json(); const phase = payload.phase || payload.status || 'queued'; if (payload.status === 'queued' || payload.status === 'running') { renderProgress(PHASE_PROGRESS[phase] ?? 10, PHASE_LABEL[phase] || phase); pollTimer = setTimeout(() => pollJob(jobId), 2000); return; } if (payload.status === 'failed') { renderResult('执行失败', `<pre>${escapeHtml(payload.error || '')}</pre>`, 'status-failed'); return; } const result = payload.result || {}; const iteration = result.next_iteration || ''; const historyIteration = result.history_iteration ?? iteration; renderProgress(100, PHASE_LABEL.done); await refreshSession(historyIteration); const compare = result.links?.case_compare_html ? `<a href="${result.links.case_compare_html}" target="_blank">View Changes</a>` : iterationCompareLink(historyIteration); renderResult('执行成功', `<div class="status-succeeded">Iteration ${escapeHtml(String(iteration))} 已生成</div>${compare ? `<div>${compare}</div>` : '<div class="muted">本次没有生成可对比的 case 修改。</div>'}`, 'status-succeeded'); }
async function submitAndRun() { if (pollTimer) clearTimeout(pollTimer); renderProgress(0, '提交中'); const result = await postJson('/api/submit', currentPayload()); pollJob(result.job_id); }
async function openAuditTrail() { const resp = await fetch('/api/audit_trail'); const data = await resp.json(); if (data.audit_trail_url) window.open(data.audit_trail_url, '_blank'); }
async function finalizeSession() { try { const result = await postJson('/api/finalize', {}); if (result.error) { renderResult('Finalize Failed', `<div class="status-failed">${escapeHtml(result.error)}</div>`, 'status-failed'); return; } if (result.final_report_url) { window.location.href = result.final_report_url; return; } await refreshSession(); renderResult('Session Finalized', `<div class="status-finalized">Status: ${escapeHtml(result.status || '')}</div><div><strong>Final Report</strong>: ${escapeHtml(result.final_report_path || "")}</div><div>${resultLinksHtml({ report_html: result.final_report_url, maker_html: result.final_maker_url, checker_html: result.final_checker_url })}</div>`, 'status-finalized'); } catch (err) { renderResult('Finalize Failed', `<div class="status-failed">${escapeHtml(err.message)}</div>`, 'status-failed'); } }
async function bootstrap() { await refreshSession(); attachHandlers(); }
function attachHandlers() { document.getElementById('overallFilter').addEventListener('change', applyFilters); document.getElementById('coverageFilter').addEventListener('change', applyFilters); document.getElementById('blockingFilter').addEventListener('change', applyFilters); document.getElementById('saveBtn').addEventListener('click', saveDraft); document.getElementById('submitBtn').addEventListener('click', submitAndRun); document.getElementById('auditBtn').addEventListener('click', openAuditTrail); document.getElementById('finalizeBtn').addEventListener('click', finalizeSession); document.querySelectorAll('.tab-btn').forEach(btn => btn.addEventListener('click', () => switchTab(btn.dataset.tab))); document.getElementById('saveBddBtn').addEventListener('click', saveBddEdits); document.getElementById('saveScriptsBtn').addEventListener('click', saveScriptsEdits); document.querySelectorAll('.stage-step').forEach(el => el.addEventListener('click', () => { const stage = el.dataset.stage; if (stage === 'finalize') { if (confirm('Finalize this review session? No further edits will be possible.')) finalizeSession(); } else { const tab = STAGE_TAB_MAP[stage]; if (tab) switchTab(tab); } })); }
// Re-attach handlers and refresh state when navigating via browser back/forward (bfcache restore)
window.addEventListener('pageshow', async (event) => { if (event.persisted) { await refreshSession(); attachHandlers(); } });
bootstrap();
</script>
</body>
</html>
"""

