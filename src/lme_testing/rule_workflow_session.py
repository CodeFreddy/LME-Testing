from __future__ import annotations

import base64
import copy
import hashlib
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
from .pipelines import run_bdd_pipeline, run_checker_pipeline, run_maker_pipeline
from .review_session import ReviewSessionManager, _render_review_session_shell
from .rule_extraction import extract_rule_artifacts, infer_default_metadata, sha256_file
from .step_registry import (
    compute_step_matches,
    extract_steps_from_normalized_bdd,
    extract_steps_from_python_step_defs,
    render_step_visibility_report,
)
from .storage import atomic_write_json, ensure_dir, load_json, timestamp_slug, write_json

logger = logging.getLogger(__name__)


@dataclass
class RuleWorkflowJobStatus:
    job_id: str
    status: str
    phase: str
    error: str | None = None
    result: dict[str, Any] | None = None


class RuleWorkflowSessionManager:
    def __init__(
        self,
        config: ProjectConfig,
        repo_root: Path,
        output_root: Path,
        host: str,
        port: int,
        maker_batch_size: int = 1,
        checker_batch_size: int = 1,
        bdd_batch_size: int = 1,
        bdd_generation_mode: str = "llm-with-fallback",
        maker_concurrency: int = 1,
        checker_concurrency: int = 1,
        bdd_concurrency: int = 1,
    ) -> None:
        self.config = config
        self.repo_root = repo_root.resolve()
        self.output_root = ensure_dir(output_root)
        self.host = host
        self.port = port
        self.maker_batch_size = maker_batch_size
        self.checker_batch_size = checker_batch_size
        self.bdd_batch_size = bdd_batch_size
        self.bdd_generation_mode = bdd_generation_mode
        self.maker_concurrency = maker_concurrency
        self.checker_concurrency = checker_concurrency
        self.bdd_concurrency = bdd_concurrency
        self.session_id = timestamp_slug()
        self.session_dir = ensure_dir(self.output_root / self.session_id)
        self.upload_dir = ensure_dir(self.session_dir / "uploads")
        self.artifact_dir = ensure_dir(self.session_dir / "artifacts")
        self.history_root = ensure_dir(self.output_root / "history")
        self.current_source_path: Path | None = None
        self.current_artifacts_dir: Path | None = None
        self.current_metadata: dict[str, Any] = {}
        self.original_atomic_rules: list[dict] = []
        self.original_semantic_rules: list[dict] = []
        self.current_atomic_rules: list[dict] = []
        self.current_semantic_rules: list[dict] = []
        self.current_semantic_review_diffs: list[dict] = []
        self.current_atomic_review_diffs: list[dict] = []
        self.current_review_basis = "current_vs_extracted_baseline"
        self.review_manager: ReviewSessionManager | None = None
        self._jobs: dict[str, RuleWorkflowJobStatus] = {}
        self._lock = threading.Lock()

    def upload_source(self, payload: dict[str, Any]) -> dict[str, Any]:
        filename = safe_filename(payload.get("filename") or "uploaded_document")
        content = decode_base64_file(payload)
        target = unique_path(self.upload_dir / filename)
        target.write_bytes(content)
        defaults = infer_default_metadata(filename)
        self.current_source_path = target
        self.current_metadata = {
            "doc_id": payload.get("doc_id") or defaults["doc_id"],
            "doc_title": payload.get("doc_title") or defaults["doc_title"],
            "doc_version": payload.get("doc_version") or defaults["doc_version"],
            "source_filename": filename,
            "source_path": str(target),
            "source_hash": sha256_file(target),
        }
        return {
            "status": "uploaded",
            "source_path": str(target),
            "metadata": self.current_metadata,
        }

    def extract_current(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = payload or {}
        if not self.current_source_path:
            raise ValueError("No source document uploaded.")
        doc_id = payload.get("doc_id") or self.current_metadata.get("doc_id") or "uploaded_document"
        doc_title = payload.get("doc_title") or self.current_metadata.get("doc_title") or "Uploaded Document"
        doc_version = payload.get("doc_version") or self.current_metadata.get("doc_version") or "uploaded"
        artifacts_dir = ensure_dir(self.artifact_dir / doc_id)
        result = extract_rule_artifacts(
            source_path=self.current_source_path,
            output_dir=artifacts_dir,
            doc_id=doc_id,
            doc_title=doc_title,
            doc_version=doc_version,
        )
        self._load_artifact_dir(artifacts_dir)
        self._write_history_snapshot("extracted")
        return result | {"status": "extracted", "review_payload": self.rules_payload()}

    def upload_artifacts(self, payload: dict[str, Any]) -> dict[str, Any]:
        files = payload.get("files") or []
        if not files:
            raise ValueError("No artifact files were provided.")
        import_dir = ensure_dir(self.artifact_dir / f"imported_{timestamp_slug()}")
        for item in files:
            rel = safe_relative_path(item.get("relative_path") or item.get("filename") or "")
            if not rel:
                continue
            target = import_dir / rel
            ensure_dir(target.parent)
            target.write_bytes(decode_base64_file(item))
        required = ["atomic_rules.json", "semantic_rules.json"]
        missing = [name for name in required if not find_file_by_name(import_dir, name)]
        if missing:
            raise ValueError("Selected folder is missing required rule artifacts: " + ", ".join(missing))
        atomic_path = find_file_by_name(import_dir, "atomic_rules.json")
        semantic_path = find_file_by_name(import_dir, "semantic_rules.json")
        metadata_path = find_file_by_name(import_dir, "metadata.json")
        normalized_dir = ensure_dir(import_dir / "_normalized")
        write_json(normalized_dir / "atomic_rules.json", load_json(atomic_path))
        write_json(normalized_dir / "semantic_rules.json", load_json(semantic_path))
        if metadata_path:
            metadata = load_json(metadata_path)
            if not isinstance(metadata, dict):
                metadata = {}
            metadata.setdefault("source_hash", combined_artifact_hash([atomic_path, semantic_path]))
            metadata.setdefault("source_filename", "artifact_folder")
            write_json(normalized_dir / "metadata.json", metadata)
        else:
            source_hash = combined_artifact_hash([atomic_path, semantic_path])
            write_json(
                normalized_dir / "metadata.json",
                {
                    "doc_id": payload.get("doc_id") or "selected_rules",
                    "doc_title": payload.get("doc_title") or "Selected Rules",
                    "doc_version": payload.get("doc_version") or "selected",
                    "source_hash": source_hash,
                    "source_filename": "artifact_folder",
                    "source_format": "artifact_folder",
                },
            )
        self._load_artifact_dir(normalized_dir)
        self._write_history_snapshot("imported")
        return {"status": "imported", "review_payload": self.rules_payload()}

    def rules_payload(self) -> dict[str, Any]:
        diffs = self.current_semantic_review_diffs
        atomic_diffs = self.current_atomic_review_diffs
        edited_ids = {item["semantic_rule_id"] for item in diffs}
        atomic_edited_ids = {item["rule_id"] for item in atomic_diffs}
        history = self.history_payload()
        return {
            "session_id": self.session_id,
            "metadata": self.current_metadata,
            "has_rules": bool(self.current_semantic_rules),
            "has_review_session": self.review_manager is not None,
            "atomic_rules": annotate_atomic_rules(
                self.current_atomic_rules,
                atomic_edited_ids,
                atomic_diffs,
                self.current_review_basis,
            ),
            "semantic_rules": annotate_rules(
                self.current_semantic_rules,
                edited_ids,
                diffs,
                self.current_review_basis,
            ),
            "diffs": diffs,
            "atomic_diffs": atomic_diffs,
            "history": history["history"],
            "history_pagination": history["pagination"],
            "reviewed_semantic_rules_path": str(self._reviewed_semantic_path()) if self.current_artifacts_dir else None,
        }

    def save_rules(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.current_artifacts_dir:
            raise ValueError("No current artifact directory is loaded.")
        atomic_rules = payload.get("atomic_rules")
        semantic_rules = payload.get("semantic_rules")
        if not isinstance(semantic_rules, list):
            raise ValueError("semantic_rules must be a list.")
        if atomic_rules is not None and not isinstance(atomic_rules, list):
            raise ValueError("atomic_rules must be a list.")
        if atomic_rules is not None:
            self.current_atomic_rules = [strip_private_rule_fields(item) for item in atomic_rules]
        self.current_semantic_rules = [strip_private_rule_fields(item) for item in semantic_rules]
        review_dir = ensure_dir(self.current_artifacts_dir / "rule_review")
        atomic_write_json(review_dir / "reviewed_atomic_rules.json", self.current_atomic_rules)
        atomic_write_json(review_dir / "reviewed_semantic_rules.json", self.current_semantic_rules)
        diffs = diff_rules_by_id(self.original_semantic_rules, self.current_semantic_rules)
        atomic_diffs = diff_atomic_rules_by_id(self.original_atomic_rules, self.current_atomic_rules)
        self._set_current_review_context(diffs, atomic_diffs, "current_vs_extracted_baseline")
        atomic_write_json(review_dir / "rule_review_diff.json", {"diffs": diffs, "atomic_diffs": atomic_diffs})
        snapshot = self._write_history_snapshot("reviewed")
        snapshot = self._history_item_by_attempt_id(snapshot["attempt_id"]) or snapshot
        return {
            "status": "saved",
            "reviewed_semantic_rules_path": str(review_dir / "reviewed_semantic_rules.json"),
            "diff_count": len(diffs) + len(atomic_diffs),
            "semantic_diff_count": len(diffs),
            "atomic_diff_count": len(atomic_diffs),
            "history_snapshot": snapshot,
        }

    def history_payload(self, page: int = 1, page_size: int = 10) -> dict[str, Any]:
        items = list(reversed(self._all_history_items()))
        page = max(1, int(page or 1))
        page_size = min(100, max(1, int(page_size or 10)))
        total = len(items)
        total_pages = max(1, (total + page_size - 1) // page_size) if total else 1
        page = min(page, total_pages)
        start = (page - 1) * page_size
        end = start + page_size
        return {
            "history": items[start:end],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
            },
        }

    def history_detail(self, attempt_id: str) -> dict[str, Any]:
        attempt_dir = self._find_history_attempt_dir(attempt_id)
        if not attempt_dir:
            raise KeyError(attempt_id)
        manifest_path = attempt_dir / "manifest.json"
        manifest = load_json(manifest_path) if manifest_path.exists() else {}
        if isinstance(manifest, dict):
            decorated = self._history_item_by_attempt_id(attempt_id)
            if decorated:
                manifest.update(decorated)
        return {
            "manifest": manifest,
            "atomic_rules": load_json(attempt_dir / "atomic_rules.json") if (attempt_dir / "atomic_rules.json").exists() else [],
            "semantic_rules": load_json(attempt_dir / "semantic_rules.json") if (attempt_dir / "semantic_rules.json").exists() else [],
            "diff": load_json(attempt_dir / "rule_diff.json") if (attempt_dir / "rule_diff.json").exists() else {"diffs": []},
        }

    def apply_history(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.current_artifacts_dir:
            raise ValueError("No current artifact directory is loaded.")
        attempt_id = payload.get("attempt_id")
        if not attempt_id:
            raise ValueError("Missing attempt_id.")
        detail = self.history_detail(str(attempt_id))
        atomic_rules = detail.get("atomic_rules") or []
        semantic_rules = detail.get("semantic_rules") or []
        history_diff = detail.get("diff") or {}
        diffs = history_diff.get("diffs") or []
        atomic_diffs = history_diff.get("atomic_diffs") or []
        if not isinstance(atomic_rules, list) or not isinstance(semantic_rules, list):
            raise ValueError("History attempt does not contain valid rule artifacts.")
        self.current_atomic_rules = [strip_private_rule_fields(item) for item in atomic_rules]
        self.current_semantic_rules = [strip_private_rule_fields(item) for item in semantic_rules]
        self._set_current_review_context(diffs, atomic_diffs, "applied_history_snapshot")
        review_dir = ensure_dir(self.current_artifacts_dir / "rule_review")
        atomic_write_json(review_dir / "reviewed_atomic_rules.json", self.current_atomic_rules)
        atomic_write_json(review_dir / "reviewed_semantic_rules.json", self.current_semantic_rules)
        atomic_write_json(review_dir / "rule_review_diff.json", {"diffs": diffs, "atomic_diffs": atomic_diffs})
        applied_from_label = (detail.get("manifest") or {}).get("display_label")
        snapshot = self._write_history_snapshot(
            "history_applied",
            extra={"applied_from_attempt_id": attempt_id, "applied_from_label": applied_from_label},
        )
        snapshot = self._history_item_by_attempt_id(snapshot["attempt_id"]) or snapshot
        return {
            "status": "applied",
            "applied_from_attempt_id": attempt_id,
            "applied_from_label": applied_from_label,
            "diff_count": len(diffs) + len(atomic_diffs),
            "semantic_diff_count": len(diffs),
            "atomic_diff_count": len(atomic_diffs),
            "history_snapshot": snapshot,
            "review_payload": self.rules_payload(),
        }

    def generate_cases(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.current_artifacts_dir:
            raise ValueError("No reviewed rules are available.")
        if payload and "semantic_rules" in payload:
            self.save_rules(payload)
        job_id = timestamp_slug()
        status = RuleWorkflowJobStatus(job_id=job_id, status="queued", phase="queued")
        with self._lock:
            self._jobs[job_id] = status
        thread = threading.Thread(target=self._run_generate_cases_job, args=(job_id,), daemon=True)
        thread.start()
        return {"job_id": job_id, "status": "queued"}

    def generate_bdd(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self.review_manager:
            raise ValueError("Generate test cases before generating BDD.")
        job_id = timestamp_slug()
        status = RuleWorkflowJobStatus(job_id=job_id, status="queued", phase="queued")
        with self._lock:
            self._jobs[job_id] = status
        thread = threading.Thread(target=self._run_generate_bdd_job, args=(job_id,), daemon=True)
        thread.start()
        return {"job_id": job_id, "status": "queued"}

    def job_status(self, job_id: str) -> dict[str, Any]:
        with self._lock:
            status = self._jobs.get(job_id)
            if not status:
                raise KeyError(job_id)
            return status.__dict__

    def _run_generate_cases_job(self, job_id: str) -> None:
        try:
            self._set_job(job_id, status="running", phase="maker")
            workflow_dir = ensure_dir(self.session_dir / "generated_cases" / job_id)
            semantic_path = self._reviewed_semantic_path()
            if not semantic_path.exists():
                self.save_rules({"atomic_rules": self.current_atomic_rules, "semantic_rules": self.current_semantic_rules})
                semantic_path = self._reviewed_semantic_path()

            maker_dir = ensure_dir(workflow_dir / "maker")
            maker_summary = run_maker_pipeline(
                config=self.config,
                semantic_rules_path=semantic_path,
                output_dir=maker_dir,
                limit=None,
                batch_size=self.maker_batch_size,
                resume_from=None,
                concurrency=self.maker_concurrency,
            )
            maker_cases_path = Path(maker_summary["results_path"])
            maker_summary_path = maker_dir / maker_summary["run_id"] / "summary.json"

            self._set_job(job_id, status="running", phase="checker")
            checker_dir = ensure_dir(workflow_dir / "checker")
            checker_summary = run_checker_pipeline(
                config=self.config,
                semantic_rules_path=semantic_path,
                maker_cases_path=maker_cases_path,
                output_dir=checker_dir,
                limit=None,
                batch_size=self.checker_batch_size,
                resume_from=None,
                concurrency=self.checker_concurrency,
            )
            checker_reviews_path = Path(checker_summary["results_path"])
            checker_summary_path = checker_dir / checker_summary["run_id"] / "summary.json"
            coverage_report_path = Path(checker_summary["coverage_report_path"])

            self._set_job(job_id, status="running", phase="review_session")
            self.review_manager = ReviewSessionManager(
                config=self.config,
                rules_path=semantic_path,
                maker_cases_path=maker_cases_path,
                checker_reviews_path=checker_reviews_path,
                output_root=ensure_dir(self.session_dir / "scenario_review_sessions"),
                repo_root=self.repo_root,
                rewrite_batch_size=self.maker_batch_size,
                checker_batch_size=self.checker_batch_size,
                rewrite_concurrency=self.maker_concurrency,
                checker_concurrency=self.checker_concurrency,
                initial_maker_summary_path=maker_summary_path,
                initial_checker_summary_path=checker_summary_path,
                initial_coverage_report_path=coverage_report_path,
                normalized_bdd_path=None,
                step_registry_path=None,
            )
            result = {
                "review_url": "/",
                "maker_summary": maker_summary,
                "checker_summary": checker_summary,
                "bdd_summary": None,
                "step_registry_path": None,
                "review_session_id": self.review_manager.session_id,
            }
            self._write_history_snapshot("cases_generated", extra=result)
            self._set_job(job_id, status="succeeded", phase="done", result=result)
        except Exception as exc:
            logger.exception("Rule workflow generate-cases job failed")
            self._set_job(job_id, status="failed", phase="failed", error=f"{exc}\n{traceback.format_exc()}")

    def _run_generate_bdd_job(self, job_id: str) -> None:
        try:
            if not self.review_manager:
                raise ValueError("Generate test cases before generating BDD.")
            self._set_job(job_id, status="running", phase="bdd")
            workflow_dir = ensure_dir(self.session_dir / "generated_bdd" / job_id)
            bdd_dir = ensure_dir(workflow_dir / "bdd")
            bdd_summary = run_bdd_pipeline(
                config=self.config,
                maker_cases_path=self.review_manager.current_maker_cases_path(),
                output_dir=bdd_dir,
                limit=None,
                batch_size=self.bdd_batch_size,
                resume_from=None,
                bdd_generation_mode=self.bdd_generation_mode,
                concurrency=self.bdd_concurrency,
            )
            normalized_bdd_path = Path(bdd_summary["results_path"])

            self._set_job(job_id, status="running", phase="step_registry")
            step_registry_dir = ensure_dir(workflow_dir / "step_registry" / timestamp_slug())
            step_registry_path = step_registry_dir / "step_visibility.json"
            bdd_inventory = extract_steps_from_normalized_bdd(normalized_bdd_path)
            library_inventory = extract_steps_from_python_step_defs(self.repo_root / "src/lme_testing/step_library.py")
            match_report = compute_step_matches(bdd_inventory, library_inventory)
            render_step_visibility_report(bdd_inventory, match_report, step_registry_path)
            attached = self.review_manager.attach_bdd_outputs(normalized_bdd_path, step_registry_path)
            result = {
                "bdd_summary": bdd_summary,
                "bdd_generation_mode": self.bdd_generation_mode,
                "normalized_bdd_path": str(normalized_bdd_path),
                "step_registry_path": str(step_registry_path),
                "review_session_id": self.review_manager.session_id,
                **attached,
            }
            self._set_job(job_id, status="succeeded", phase="done", result=result)
        except Exception as exc:
            logger.exception("Rule workflow generate-bdd job failed")
            self._set_job(job_id, status="failed", phase="failed", error=f"{exc}\n{traceback.format_exc()}")

    def _set_job(
        self,
        job_id: str,
        status: str,
        phase: str,
        error: str | None = None,
        result: dict[str, Any] | None = None,
    ) -> None:
        with self._lock:
            self._jobs[job_id] = RuleWorkflowJobStatus(job_id, status, phase, error, result)

    def _load_artifact_dir(self, artifacts_dir: Path) -> None:
        self.current_artifacts_dir = artifacts_dir
        self.current_metadata = load_json(artifacts_dir / "metadata.json")
        if not isinstance(self.current_metadata, dict):
            self.current_metadata = {}
        self.current_metadata.setdefault("doc_id", artifacts_dir.name)
        self.current_metadata.setdefault("doc_title", artifacts_dir.name)
        self.current_metadata.setdefault("doc_version", "unknown")
        self.current_metadata.setdefault("source_filename", Path(self.current_metadata.get("source_path", artifacts_dir.name)).name)
        if not self.current_metadata.get("source_hash"):
            self.current_metadata["source_hash"] = combined_artifact_hash(
                [artifacts_dir / "atomic_rules.json", artifacts_dir / "semantic_rules.json"]
            )
            write_json(artifacts_dir / "metadata.json", self.current_metadata)
        self.original_atomic_rules = load_json(artifacts_dir / "atomic_rules.json")
        self.original_semantic_rules = load_json(artifacts_dir / "semantic_rules.json")
        self.current_atomic_rules = copy.deepcopy(self.original_atomic_rules)
        self.current_semantic_rules = copy.deepcopy(self.original_semantic_rules)
        self._set_current_review_context([], [], "current_vs_extracted_baseline")

    def _reviewed_semantic_path(self) -> Path:
        if not self.current_artifacts_dir:
            raise ValueError("No artifact directory is loaded.")
        reviewed = self.current_artifacts_dir / "rule_review" / "reviewed_semantic_rules.json"
        return reviewed if reviewed.exists() else self.current_artifacts_dir / "semantic_rules.json"

    def _reviewed_atomic_path(self) -> Path:
        if not self.current_artifacts_dir:
            raise ValueError("No artifact directory is loaded.")
        reviewed = self.current_artifacts_dir / "rule_review" / "reviewed_atomic_rules.json"
        return reviewed if reviewed.exists() else self.current_artifacts_dir / "atomic_rules.json"

    def _history_dir(self, source_hash: str) -> Path:
        return ensure_dir(self.history_root / "by_source_hash" / source_hash[:16])

    def _legacy_history_dir(self, doc_id: str | None, source_hash: str) -> Path | None:
        if not doc_id:
            return None
        return self.history_root / safe_filename(doc_id) / source_hash[:16]

    def _history_roots(self, doc_id: str | None, source_hash: str) -> list[Path]:
        roots = [self._history_dir(source_hash)]
        legacy = self._legacy_history_dir(doc_id, source_hash)
        if legacy and legacy.exists() and legacy.resolve() != roots[0].resolve():
            roots.append(legacy)
        return roots

    def _all_history_items(self) -> list[dict[str, Any]]:
        doc_id = self.current_metadata.get("doc_id")
        source_hash = self.current_metadata.get("source_hash")
        if not source_hash:
            return []
        items: list[dict[str, Any]] = []
        for root in self._history_roots(doc_id, source_hash):
            for path in sorted(root.glob("attempt_*/manifest.json")):
                try:
                    manifest = load_json(path)
                    if isinstance(manifest, dict):
                        manifest.setdefault("attempt_dir", str(path.parent))
                        items.append(manifest)
                except Exception:
                    logger.warning("Failed to load history manifest: %s", path)
        items = sorted(dedupe_history_items(items), key=history_item_sort_key)
        return decorate_history_items(items)

    def _find_history_attempt_dir(self, attempt_id: str) -> Path | None:
        source_hash = self.current_metadata.get("source_hash")
        if not source_hash:
            return None
        doc_id = self.current_metadata.get("doc_id")
        safe_attempt_id = safe_filename(attempt_id)
        for root in self._history_roots(doc_id, source_hash):
            candidate = root / safe_attempt_id
            if candidate.exists() and candidate.is_dir():
                return candidate
        return None

    def _history_item_by_attempt_id(self, attempt_id: str) -> dict[str, Any] | None:
        for item in self._all_history_items():
            if item.get("attempt_id") == attempt_id:
                return item
        return None

    def _set_current_review_context(
        self,
        semantic_diffs: list[dict],
        atomic_diffs: list[dict],
        basis: str,
    ) -> None:
        self.current_semantic_review_diffs = copy.deepcopy(semantic_diffs)
        self.current_atomic_review_diffs = copy.deepcopy(atomic_diffs)
        self.current_review_basis = basis

    def _write_history_snapshot(self, status: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        doc_id = self.current_metadata.get("doc_id", "unknown_doc")
        source_hash = self.current_metadata.get("source_hash") or "unknown_hash"
        created_at = timestamp_slug()
        attempt_id = f"attempt_{created_at}"
        attempt_dir = self._unique_history_attempt_dir(self._history_dir(source_hash), attempt_id)
        attempt_id = attempt_dir.name
        if self.current_atomic_rules:
            write_json(attempt_dir / "atomic_rules.json", self.current_atomic_rules)
        if self.current_semantic_rules:
            write_json(attempt_dir / "semantic_rules.json", self.current_semantic_rules)
        diffs = self.current_semantic_review_diffs
        atomic_diffs = self.current_atomic_review_diffs
        write_json(attempt_dir / "rule_diff.json", {"diffs": diffs, "atomic_diffs": atomic_diffs})
        manifest = {
            "attempt_id": attempt_id,
            "created_at": created_at,
            "status": status,
            "status_label": history_status_label(status),
            "doc_id": doc_id,
            "source_hash": source_hash,
            "doc_title": self.current_metadata.get("doc_title"),
            "doc_version": self.current_metadata.get("doc_version"),
            "source_filename": self.current_metadata.get("source_filename"),
            "semantic_rule_count": len(self.current_semantic_rules),
            "edited_rule_count": len(diffs) + len(atomic_diffs),
            "semantic_edited_rule_count": len(diffs),
            "atomic_edited_rule_count": len(atomic_diffs),
            "attempt_dir": str(attempt_dir),
        }
        if extra:
            manifest.update(extra)
        write_json(attempt_dir / "manifest.json", manifest)
        return manifest

    def _unique_history_attempt_dir(self, root: Path, attempt_id: str) -> Path:
        candidate = root / attempt_id
        if not candidate.exists():
            return ensure_dir(candidate)
        for index in range(1, 1000):
            candidate = root / f"{attempt_id}_{index:03d}"
            if not candidate.exists():
                return ensure_dir(candidate)
        raise ValueError(f"Unable to allocate history attempt directory under {root}")


def serve_rule_workflow_session(manager: RuleWorkflowSessionManager) -> tuple[ThreadingHTTPServer, str]:
    handler = _build_handler(manager)
    server = ThreadingHTTPServer((manager.host, manager.port), handler)
    actual_port = server.server_address[1]
    return server, f"http://{manager.host}:{actual_port}/"


def _build_handler(manager: RuleWorkflowSessionManager):
    repo_root = manager.repo_root

    class RuleWorkflowHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            try:
                parsed = urlparse(self.path)
                if parsed.path == "/":
                    self._send_html(render_rule_workflow_shell(manager.bdd_generation_mode))
                    return
                if parsed.path == "/scenario-review":
                    if not manager.review_manager:
                        self.send_error(HTTPStatus.NOT_FOUND, "Scenario Review is not ready. Generate cases first.")
                        return
                    self._send_html(_render_review_session_shell())
                    return
                if parsed.path == "/api/rule-workflow/rules":
                    self._send_json(manager.rules_payload())
                    return
                if parsed.path == "/api/rule-workflow/history":
                    query = parse_qs(parsed.query)
                    page = int(query.get("page", ["1"])[0] or "1")
                    page_size = int(query.get("page_size", ["10"])[0] or "10")
                    self._send_json(manager.history_payload(page=page, page_size=page_size))
                    return
                if parsed.path == "/api/rule-workflow/history/detail":
                    query = parse_qs(parsed.query)
                    attempt_id = query.get("attempt_id", [""])[0]
                    self._send_json(manager.history_detail(attempt_id))
                    return
                if parsed.path.startswith("/api/rule-workflow/status/"):
                    job_id = parsed.path.rsplit("/", 1)[-1]
                    self._send_json(manager.job_status(job_id))
                    return
                if manager.review_manager and self._handle_review_get(parsed):
                    return
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            except KeyError:
                self.send_error(HTTPStatus.NOT_FOUND, "Unknown job id")
            except Exception as exc:
                logger.exception("Rule workflow GET failed: %s", self.path)
                self._send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

        def do_POST(self) -> None:  # noqa: N802
            try:
                parsed = urlparse(self.path)
                payload = self._read_json_body()
                if parsed.path == "/api/rule-workflow/upload-source":
                    self._send_json(manager.upload_source(payload))
                    return
                if parsed.path == "/api/rule-workflow/extract":
                    self._send_json(manager.extract_current(payload))
                    return
                if parsed.path == "/api/rule-workflow/upload-artifacts":
                    self._send_json(manager.upload_artifacts(payload))
                    return
                if parsed.path == "/api/rule-workflow/rules/save":
                    self._send_json(manager.save_rules(payload))
                    return
                if parsed.path == "/api/rule-workflow/generate-cases":
                    self._send_json(manager.generate_cases(payload), status=HTTPStatus.ACCEPTED)
                    return
                if parsed.path == "/api/rule-workflow/generate-bdd":
                    self._send_json(manager.generate_bdd(payload), status=HTTPStatus.ACCEPTED)
                    return
                if parsed.path == "/api/rule-workflow/history/apply":
                    self._send_json(manager.apply_history(payload))
                    return
                if manager.review_manager and self._handle_review_post(parsed, payload):
                    return
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            except Exception as exc:
                logger.exception("Rule workflow POST failed: %s", self.path)
                self._send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)

        def _handle_review_get(self, parsed) -> bool:
            review = manager.review_manager
            if review is None:
                return False
            if parsed.path == "/api/session":
                self._send_json(review.session_payload())
                return True
            if parsed.path == "/api/history":
                self._send_json({"history": review.session_payload().get("history", [])})
                return True
            if parsed.path == "/api/audit_trail":
                self._send_json(review.rebuild_audit_trail())
                return True
            if parsed.path == "/api/bdd":
                self._send_json(review.bdd_payload())
                return True
            if parsed.path == "/api/scripts":
                self._send_json(review.scripts_payload())
                return True
            if parsed.path == "/api/stage":
                self._send_json(review.stage_payload())
                return True
            if parsed.path.startswith("/api/status/"):
                self._send_json(review.job_status(parsed.path.rsplit("/", 1)[-1]))
                return True
            if parsed.path == "/report.html":
                self._send_file(str(review.current_report_file("report")), repo_root)
                return True
            if parsed.path == "/maker_readable.html":
                self._send_file(str(review.current_report_file("maker")), repo_root)
                return True
            if parsed.path == "/checker_readable.html":
                self._send_file(str(review.current_report_file("checker")), repo_root)
                return True
            if parsed.path == "/coverage.csv":
                self._send_file(str(review.current_report_file("report").with_suffix(".csv")), repo_root)
                return True
            if parsed.path == "/files":
                target = parse_qs(parsed.query).get("path", [""])[0]
                self._send_file(target, repo_root)
                return True
            return False

        def _handle_review_post(self, parsed, payload: dict[str, Any]) -> bool:
            review = manager.review_manager
            if review is None:
                return False
            if parsed.path == "/api/reviews/save":
                self._send_json(review.save_reviews(payload))
                return True
            if parsed.path == "/api/submit":
                self._send_json(review.submit_reviews(payload), status=HTTPStatus.ACCEPTED)
                return True
            if parsed.path == "/api/finalize":
                self._send_json(review.finalize_session())
                return True
            if parsed.path == "/api/bdd/save":
                self._send_json(review.save_bdd_edits(payload))
                return True
            if parsed.path == "/api/scripts/save":
                self._send_json(review.save_scripts_edits(payload))
                return True
            if parsed.path == "/api/scripts/create-by-ai":
                self._send_json(review.create_scripts_by_ai(payload), status=HTTPStatus.ACCEPTED)
                return True
            if parsed.path == "/api/stage/advance":
                self._send_json(review.advance_stage(payload.get("to_stage", "")))
                return True
            return False

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
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", mimetypes.guess_type(str(path))[0] or "application/octet-stream")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    return RuleWorkflowHandler


def decode_base64_file(payload: dict[str, Any]) -> bytes:
    content = payload.get("content_base64")
    if not isinstance(content, str) or not content:
        raise ValueError("Missing content_base64.")
    return base64.b64decode(content)


def safe_filename(value: str) -> str:
    name = Path(value).name
    name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in name)
    return name or "file"


def safe_relative_path(value: str) -> Path | None:
    value = value.replace("\\", "/").strip("/")
    if not value or ".." in value.split("/"):
        return None
    parts = [safe_filename(part) for part in value.split("/") if part]
    return Path(*parts) if parts else None


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    for index in range(1, 1000):
        candidate = path.with_name(f"{stem}_{index}{suffix}")
        if not candidate.exists():
            return candidate
    raise ValueError(f"Unable to allocate unique path for {path}")


def find_file_by_name(root: Path, filename: str) -> Path | None:
    matches = list(root.rglob(filename))
    return matches[0] if matches else None


def combined_artifact_hash(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def diff_rules_by_id(original_rules: list[dict], current_rules: list[dict]) -> list[dict]:
    return diff_items_by_id(original_rules, current_rules, "semantic_rule_id")


def diff_atomic_rules_by_id(original_rules: list[dict], current_rules: list[dict]) -> list[dict]:
    return diff_items_by_id(original_rules, current_rules, "rule_id")


def diff_items_by_id(original_rules: list[dict], current_rules: list[dict], id_key: str) -> list[dict]:
    original_by_id = {item.get(id_key): item for item in original_rules}
    current_by_id = {item.get(id_key): item for item in current_rules}
    diffs: list[dict[str, Any]] = []
    for rule_id in sorted(set(original_by_id) | set(current_by_id)):
        if not rule_id:
            continue
        original = original_by_id.get(rule_id)
        current = current_by_id.get(rule_id)
        if original is None:
            diffs.append({id_key: rule_id, "change_type": "added", "fields": []})
        elif current is None:
            diffs.append({id_key: rule_id, "change_type": "deleted", "fields": []})
        else:
            fields = compare_json_fields(original, current)
            if fields:
                diffs.append({id_key: rule_id, "change_type": "modified", "fields": fields})
    return diffs


def compare_json_fields(left: Any, right: Any, prefix: str = "") -> list[dict[str, Any]]:
    if isinstance(left, dict) and isinstance(right, dict):
        changes: list[dict[str, Any]] = []
        for key in sorted(set(left) | set(right)):
            path = f"{prefix}.{key}" if prefix else str(key)
            if key not in left:
                changes.append({"path": path, "change_type": "added", "before": None, "after": right[key]})
            elif key not in right:
                changes.append({"path": path, "change_type": "deleted", "before": left[key], "after": None})
            else:
                changes.extend(compare_json_fields(left[key], right[key], path))
        return changes
    if left != right:
        return [{"path": prefix, "change_type": "modified", "before": left, "after": right}]
    return []


def annotate_rules(rules: list[dict], edited_ids: set[str], diffs: list[dict], basis: str) -> list[dict]:
    diff_map = {item["semantic_rule_id"]: item for item in diffs}
    annotated = []
    label = review_basis_label(basis)
    for rule in rules:
        item = copy.deepcopy(rule)
        rule_id = item.get("semantic_rule_id")
        item["_review"] = {
            "edited": rule_id in edited_ids,
            "label": label if rule_id in edited_ids else "No reviewed change in selected snapshot",
            "basis": basis,
            "diff": diff_map.get(rule_id),
        }
        annotated.append(item)
    return annotated


def annotate_atomic_rules(rules: list[dict], edited_ids: set[str], diffs: list[dict], basis: str) -> list[dict]:
    diff_map = {item["rule_id"]: item for item in diffs}
    annotated = []
    label = review_basis_label(basis)
    for rule in rules:
        item = copy.deepcopy(rule)
        rule_id = item.get("rule_id")
        item["_review"] = {
            "edited": rule_id in edited_ids,
            "label": label if rule_id in edited_ids else "No reviewed change in selected snapshot",
            "basis": basis,
            "diff": diff_map.get(rule_id),
        }
        annotated.append(item)
    return annotated


def dedupe_history_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for item in items:
        key = str(item.get("attempt_dir") or item.get("attempt_id") or "")
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def decorate_history_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decorated: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        copy_item = dict(item)
        copy_item["iteration_number"] = index
        copy_item["display_label"] = f"Iteration {index}"
        copy_item.setdefault("status_label", history_status_label(str(copy_item.get("status") or "")))
        decorated.append(copy_item)
    return decorated


def history_item_sort_key(item: dict[str, Any]) -> tuple[str, str]:
    return (str(item.get("created_at") or attempt_timestamp(item.get("attempt_id"))), str(item.get("attempt_id") or ""))


def attempt_timestamp(attempt_id: Any) -> str:
    text = str(attempt_id or "")
    if text.startswith("attempt_"):
        text = text.removeprefix("attempt_")
    return text.split("_", 1)[0]


def history_status_label(status: str) -> str:
    labels = {
        "extracted": "Extracted draft",
        "imported": "Imported existing rules",
        "reviewed": "Saved review edits",
        "history_applied": "Applied history version",
        "cases_generated": "Cases generated",
    }
    return labels.get(status, status.replace("_", " ").title() if status else "Unknown")


def review_basis_label(basis: str) -> str:
    if basis == "applied_history_snapshot":
        return "manual edited in applied snapshot"
    return "changed from extracted baseline"


def strip_private_rule_fields(rule: dict) -> dict:
    item = copy.deepcopy(rule)
    for key in list(item):
        if key.startswith("_"):
            item.pop(key, None)
    return item


def render_rule_workflow_shell(bdd_generation_mode: str = "llm-with-fallback") -> str:
    return RULE_WORKFLOW_HTML.replace("__BDD_GENERATION_MODE__", bdd_generation_mode)


RULE_WORKFLOW_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Rule Extraction Review</title>
  <style>
    body { margin: 0; font-family: "Segoe UI", Arial, sans-serif; color: #172033; background: #f6f7f9; }
    header { background: #18212f; color: white; padding: 16px 24px; }
    h1 { margin: 0; font-size: 22px; letter-spacing: 0; }
    main { padding: 18px 24px 40px; }
    section { margin-bottom: 18px; }
    .band { background: white; border: 1px solid #d6dbe3; border-radius: 8px; padding: 14px; }
    .row { display: flex; gap: 10px; flex-wrap: wrap; align-items: end; }
    label { font-size: 12px; color: #4b5565; display: grid; gap: 4px; }
    input, select, textarea, button { font: inherit; }
    input, select, textarea { border: 1px solid #cbd3df; border-radius: 6px; padding: 7px 8px; background: white; }
    button { border: 1px solid #aeb8c7; border-radius: 6px; background: #fff; padding: 8px 11px; cursor: pointer; }
    button.primary { background: #1d4ed8; color: white; border-color: #1d4ed8; }
    button:disabled { opacity: .5; cursor: not-allowed; }
    .muted { color: #667085; font-size: 12px; }
    .status { white-space: pre-wrap; font-size: 12px; background: #eef2f7; border: 1px solid #d6dbe3; border-radius: 6px; padding: 8px; }
    .rule-list { display: grid; gap: 12px; }
    .rule { background: white; border: 1px solid #d6dbe3; border-radius: 8px; padding: 12px; }
    .rule.edited { border-left: 5px solid #b45309; }
    .rule-head { display: flex; justify-content: space-between; gap: 12px; align-items: start; }
    .badge { display: inline-block; border-radius: 999px; padding: 2px 8px; font-size: 11px; border: 1px solid #cbd3df; color: #344054; }
    .badge.edited { border-color: #f59e0b; background: #fffbeb; color: #92400e; }
    .fields { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 8px; margin: 10px 0; }
    .wide { grid-column: 1 / -1; }
    .business-editor { margin-top: 10px; }
    .business-editor textarea { width: 100%; min-height: 72px; box-sizing: border-box; }
    .atomic-box { border: 1px solid #d8dee8; border-radius: 6px; background: #f8fafc; padding: 10px; margin-top: 8px; }
    .atomic-box textarea { width: 100%; box-sizing: border-box; }
    details { border: 1px solid #e1e6ee; border-radius: 6px; padding: 8px; background: #fbfcfe; margin-top: 8px; }
    summary { cursor: pointer; font-weight: 600; }
    pre { white-space: pre-wrap; word-break: break-word; font-size: 12px; background: #f8fafc; border: 1px solid #e1e6ee; border-radius: 6px; padding: 8px; }
    .json-editor { width: 100%; min-height: 220px; box-sizing: border-box; font-family: Consolas, monospace; font-size: 12px; }
    .source { max-height: 280px; overflow: auto; }
    .diff-item { border-left: 3px solid #b45309; padding: 4px 8px; margin: 4px 0; background: #fff7ed; font-size: 12px; }
    .history-item { padding: 6px 0; border-bottom: 1px dashed #d6dbe3; font-size: 12px; }
    .history-title { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
    .history-detail { border: 1px solid #cbd5e1; background: #f8fafc; border-radius: 6px; padding: 10px; margin-bottom: 10px; }
    .history-actions { display: flex; gap: 6px; margin-top: 4px; }
    .pager { display: flex; align-items: center; gap: 8px; margin-top: 8px; }
    .history-rules { display: grid; gap: 8px; margin-top: 8px; }
    .history-rule { border: 1px solid #d6dbe3; border-radius: 6px; background: white; padding: 8px; font-size: 12px; }
    .field-guide dl { display: grid; grid-template-columns: minmax(120px, 180px) 1fr; gap: 8px 12px; font-size: 13px; }
    .field-guide dt { font-weight: 700; }
    .field-guide dd { margin: 0; color: #475569; }
    .technical { font-size: 12px; color: #64748b; }
    .hidden { display: none; }
    .workflow-progress { display: flex; align-items: center; gap: 0; margin: 16px 0 18px; background: #fff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 14px 18px; }
    .workflow-step { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 8px; color: #64748b; cursor: pointer; }
    .workflow-step.locked { cursor: not-allowed; opacity: .55; }
    .workflow-step.active, .workflow-step.completed { color: #047857; font-weight: 700; }
    .workflow-dot { width: 28px; height: 28px; border-radius: 999px; background: #e5e7eb; color: #64748b; display: flex; align-items: center; justify-content: center; font-weight: 700; }
    .workflow-step.active .workflow-dot, .workflow-step.completed .workflow-dot { background: #16a34a; color: #fff; }
    .workflow-arrow { color: #cbd5e1; font-size: 20px; }
    .workflow-panel { display: none; }
    .workflow-panel.active { display: block; }
    .case-toolbar { display: flex; gap: 12px; flex-wrap: wrap; align-items: end; }
    .metric-grid { display: grid; grid-template-columns: repeat(3, minmax(160px, 1fr)); gap: 12px; }
    .metric { background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 10px; }
    table { width: 100%; border-collapse: collapse; background: #fff; }
    th, td { border: 1px solid #cbd5e1; padding: 9px; text-align: left; vertical-align: top; font-size: 12px; }
    th { background: #e2e8f0; }
    .issue-picker { margin-top: 4px; border: 1px solid #cbd5e1; border-radius: 6px; background: #f8fafc; }
    .issue-table th, .issue-table td { padding: 5px 7px; font-size: 11px; }
    .suggestion-yes { display: inline-block; color: #166534; background: #dcfce7; border: 1px solid #86efac; border-radius: 999px; padding: 2px 8px; font-weight: 700; }
    .suggestion-no { display: inline-block; color: #991b1b; background: #fee2e2; border: 1px solid #fecaca; border-radius: 999px; padding: 2px 8px; font-weight: 700; }
    .progress-wrap { margin-top: 8px; background: #e2e8f0; border-radius: 8px; height: 18px; overflow: hidden; }
    .progress-bar { height: 100%; background: #16a34a; width: 0%; transition: width 0.4s ease; }
    .progress-label { font-size: 12px; color: #334155; margin-top: 4px; }
    .status-running { color: #92400e; }
    .status-succeeded { color: #166534; }
    .status-failed { color: #991b1b; }
    .history-row { padding: 7px 0; border-bottom: 1px dashed #e2e8f0; }
    .history-row.current { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 8px 10px; }
    .bdd-rule-block, .step-block { background: #fff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px; margin-bottom: 10px; }
    .bdd-scenario-card { margin: 8px 0 8px 12px; padding: 10px; border: 1px solid #e2e8f0; border-radius: 8px; }
    .step-label { font-weight: 700; font-size: 12px; color: #475569; margin: 6px 0 4px; }
    .step-textarea { width: 100%; box-sizing: border-box; font-family: Consolas, monospace; font-size: 12px; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px 8px; resize: vertical; }
    .scripts-metrics { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 10px; margin-bottom: 14px; }
    .scripts-metric { background: #eff6ff; border-radius: 8px; padding: 10px; border: 1px solid #bfdbfe; text-align: center; }
    .scripts-metric strong { display: block; font-size: 20px; }
    .scripts-metric span { font-size: 11px; color: #64748b; }
    .step-item { margin-bottom: 8px; padding: 6px 8px; border: 1px solid #e2e8f0; border-radius: 6px; }
    .step-item.unmatched { border-left: 3px solid #991b1b; background: #fff5f5; }
    .step-item-badge { font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: 700; background: #e2e8f0; }
    .script-code-textarea { width: 100%; box-sizing: border-box; min-height: 180px; font-family: Consolas, monospace; font-size: 12px; }
  </style>
</head>
<body>
  <header><h1>HKEX AI Assisted Workflow</h1></header>
  <main>
    <div class="workflow-progress" id="workflowProgress">
      <div class="workflow-step active" data-workflow-step="rule_extraction"><div class="workflow-dot">1</div><div>Rule Extraction</div></div>
      <div class="workflow-arrow">-&gt;</div>
      <div class="workflow-step" data-workflow-step="test_case"><div class="workflow-dot">2</div><div>Test Case</div></div>
      <div class="workflow-arrow">-&gt;</div>
      <div class="workflow-step" data-workflow-step="bdd"><div class="workflow-dot">3</div><div>BDD</div></div>
      <div class="workflow-arrow">-&gt;</div>
      <div class="workflow-step" data-workflow-step="scripts"><div class="workflow-dot">4</div><div>Scripts</div></div>
      <div class="workflow-arrow">-&gt;</div>
      <div class="workflow-step" data-workflow-step="finalize"><div class="workflow-dot">5</div><div>Finalize</div></div>
    </div>

    <div class="workflow-panel active" data-workflow-panel="rule_extraction">
    <section class="band">
      <div class="row">
        <label>Requirement document <input id="sourceFile" type="file" accept=".pdf,.md,.markdown,.docx"></label>
        <label>doc_id <input id="docId" value="im_hk_v14"></label>
        <label>doc_title <input id="docTitle" value="Initial Margin Calculation Guide HKv14"></label>
        <label>doc_version <input id="docVersion" value="HKv14"></label>
        <button id="uploadBtn">Upload</button>
        <button id="extractBtn" class="primary" disabled>Start Extraction</button>
      </div>
      <p class="muted">PDF/Markdown/DOCX are supported. HKEX HKv14 demo extracts core calculation sections deterministically.</p>
    </section>

    <section class="band">
      <div class="row">
        <button id="saveRulesBtn" disabled>Save Rule Edits</button>
        <button id="ruleNextBtn" class="primary" disabled>Next Step</button>
      </div>
      <div id="status" class="status">Ready.</div>
    </section>

    <section class="band">
      <h2>History</h2>
      <div id="historyDetail" class="history-detail hidden"></div>
      <div id="history" class="muted">No history loaded.</div>
      <div id="historyPager" class="pager hidden"></div>
    </section>

    <section class="band hidden">
      <details class="field-guide">
        <summary>Semantic Field Guide</summary>
        <dl>
          <dt>rule_type</dt><dd>Business rule category used by downstream case generation. Allowed values: obligation, prohibition, permission, deadline, state_transition, data_constraint, enum_definition, workflow, calculation, reference_only. HKEX demo core sections default to calculation.</dd>
          <dt>testability</dt><dd>Whether the rule can directly produce tests: testable, partially_testable, non_testable.</dd>
          <dt>priority</dt><dd>Relative test-generation priority: high, medium, low. Calculation rules default to high in the current HKEX demo.</dd>
          <dt>actor</dt><dd>The business party responsible for the rule action. HKEX demo normalizes this to clearing_participant.</dd>
          <dt>action</dt><dd>The business action expressed by the rule. It may come from current heuristics or human review edits.</dd>
          <dt>object</dt><dd>The business object affected by the action. HKEX demo normalizes this to initial_margin_requirement.</dd>
        </dl>
      </details>
    </section>

    <section>
      <div id="rules" class="rule-list"></div>
    </section>
    </div>

    <div class="workflow-panel" data-workflow-panel="test_case">
      <section class="band" id="summaryCard">Loading test cases...</section>
      <section class="band">
        <div class="case-toolbar">
          <label>Coverage <select id="coverageFilter"><option value="">All</option><option value="covered">covered</option><option value="partial">partial</option><option value="uncovered">uncovered</option><option value="missing">missing</option></select></label>
          <label>Checker Suggestion <select id="blockingFilter"><option value="">All</option><option value="false">Yes</option><option value="true">No</option></select></label>
          <button id="saveRerunBtn" class="primary" disabled>Save &amp; Rerun</button>
          <button id="testCaseReportBtn">Check Reports</button>
          <button id="auditBtn">Audit Trail</button>
          <button id="testCaseNextBtn">Next Step</button>
        </div>
        <p class="muted">Choose rewrite to rerun a case. A non-empty comment on a pending case is also treated as rewrite feedback.</p>
      </section>
      <section class="band" id="resultCard" style="display:none"></section>
      <section class="band"><h2>History</h2><div id="reviewHistoryCard" class="muted">No history.</div></section>
      <section class="band">
        <table>
          <thead>
            <tr>
              <th>Business Rule</th>
              <th>Case ID</th>
              <th>Feature</th>
              <th>Case Type</th>
              <th>Coverage</th>
              <th>Checker Suggestion</th>
              <th>Blocking Reason</th>
              <th>Detail</th>
              <th>Human Review</th>
            </tr>
          </thead>
          <tbody id="reviewRows"></tbody>
        </table>
      </section>
    </div>

    <div class="workflow-panel" data-workflow-panel="bdd">
      <section class="band">
        <div class="row">
          <button id="saveBddBtn">Save BDD Edits</button>
          <button id="bddNextBtn">Next Step</button>
          <span id="bddStatus" class="muted"></span>
        </div>
        <div id="bddModeNotice" class="muted"></div>
      </section>
      <section class="band" id="bddProgressCard" style="display:none"></section>
      <section id="bddContent"><em>Loading BDD...</em></section>
    </div>

    <div class="workflow-panel" data-workflow-panel="scripts">
      <section class="band">
        <div class="row">
          <button id="createScriptsAiBtn" class="primary">Create Scripts By AI</button>
          <button id="saveScriptsBtn" class="hidden">Save</button>
          <button id="scriptsNextBtn">Next Step</button>
          <span id="scriptsStatus" class="muted"></span>
        </div>
        <div id="scriptsProgressCard" class="hidden"></div>
      </section>
      <section id="scriptsContent"><em>Loading scripts...</em></section>
    </div>

    <div class="workflow-panel" data-workflow-panel="finalize">
      <section class="band">
        <div class="row">
          <button id="finalizeWorkflowBtn" class="primary">Finalize Workflow</button>
          <button id="finalAuditBtn">Audit Trail</button>
        </div>
        <div id="finalizeStatus" class="status">Ready to finalize the workflow.</div>
      </section>
    </div>
  </main>
<script>
let state = { semantic_rules: [], atomic_rules: [] };
let historyPage = 1;
let historyPageSize = 10;
let historyPagination = { page: 1, page_size: 10, total: 0, total_pages: 1 };
let activeWorkflowStep = localStorage.getItem('hkexWorkflowStep') || 'rule_extraction';
let casesGenerated = false;
let casesGenerating = false;
let sessionPayload = null;
let reviewMap = new Map();
let reviewBaselineMap = new Map();
let pollTimer = null;
let bddPayload = null;
let scriptsPayload = null;
let bddDirty = false;
let scriptsDirty = false;
const BDD_GENERATION_MODE = '__BDD_GENERATION_MODE__';
const WORKFLOW_STEPS = ['rule_extraction', 'test_case', 'bdd', 'scripts', 'finalize'];
const GENERATE_PROGRESS = { queued: 5, maker: 25, checker: 55, bdd: 75, step_registry: 88, review_session: 95, done: 100 };
const GENERATE_LABEL = { queued: 'Queued', maker: 'Generating test cases', checker: 'Checking test cases', bdd: 'Generating BDD', step_registry: 'Preparing scripts', review_session: 'Preparing review session', done: 'Cases generated' };
const BDD_PROGRESS = { queued: 5, bdd: 75, step_registry: 92, done: 100 };
const BDD_LABEL = { queued: 'Queued', bdd: 'Generating BDD from reviewed test cases', step_registry: 'Preparing script visibility', done: 'BDD generated' };
const SCRIPTS_PROGRESS = { queued: 5, loading_api_catalog: 18, calling_llm: 55, validating: 78, writing_scripts: 92, done: 100 };
const SCRIPTS_LABEL = { queued: 'Queued', loading_api_catalog: 'Loading API catalog', calling_llm: 'Generating scripts with AI', validating: 'Validating generated scripts', writing_scripts: 'Writing scripts', done: 'Scripts generated' };
const PHASE_PROGRESS = { queued: 5, rewrite: 20, checker: 55, report: 90, done: 100, failed: 100 };
const PHASE_LABEL = { queued: 'Queued', rewrite: 'Rewriting selected cases', checker: 'Running checker', report: 'Generating report', done: 'Completed', failed: 'Failed' };
let maxReachedWorkflowIndex = Number(localStorage.getItem('hkexMaxReachedWorkflowIndex') || '0');

function $(id) { return document.getElementById(id); }
function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
}
function setStatus(text) { $('status').textContent = text; }
function updateBddModeNotice(extra) {
  const suffix = extra ? ` ${extra}` : '';
  $('bddModeNotice').textContent = `BDD generation mode: ${BDD_GENERATION_MODE}.${suffix}`;
}
function cloneJson(value) { return JSON.parse(JSON.stringify(value)); }
function workflowStepAllowed(step) {
  const idx = WORKFLOW_STEPS.indexOf(step);
  if (idx <= 0) return true;
  if (idx === 1) return casesGenerated || casesGenerating;
  return casesGenerated;
}
function setWorkflowStep(step) {
  if (!WORKFLOW_STEPS.includes(step)) step = 'rule_extraction';
  if (!workflowStepAllowed(step)) step = 'rule_extraction';
  activeWorkflowStep = step;
  localStorage.setItem('hkexWorkflowStep', step);
  document.querySelectorAll('[data-workflow-panel]').forEach(panel => {
    panel.classList.toggle('active', panel.dataset.workflowPanel === step);
  });
  const activeIdx = WORKFLOW_STEPS.indexOf(step);
  document.querySelectorAll('[data-workflow-step]').forEach(el => {
    const idx = WORKFLOW_STEPS.indexOf(el.dataset.workflowStep);
    el.classList.remove('active', 'completed');
    if (idx < activeIdx) el.classList.add('completed');
    if (idx === activeIdx) el.classList.add('active');
    const dot = el.querySelector('.workflow-dot');
    if (dot) dot.textContent = idx < activeIdx ? '✓' : String(idx + 1);
  });
  if (step === 'test_case') {
    if (casesGenerating && !casesGenerated) {
      $('summaryCard').innerHTML = '<div class="metric"><strong>Generating test cases</strong><br>Maker/checker is running. The generated cases will appear here when ready.</div>';
      $('reviewRows').innerHTML = '';
    } else {
      refreshSession().catch(err => renderResult('Load failed', `<pre>${esc(err.message)}</pre>`, 'status-failed'));
    }
  }
  if (step === 'bdd') loadBddData();
  if (step === 'scripts') loadScriptsData();
}
function nextWorkflowStep() {
  const idx = WORKFLOW_STEPS.indexOf(activeWorkflowStep);
  if (idx >= 0 && idx < WORKFLOW_STEPS.length - 1) setWorkflowStep(WORKFLOW_STEPS[idx + 1]);
}
function stageFromLocation() {
  const stage = (window.location.hash || '').replace('#', '');
  return WORKFLOW_STEPS.includes(stage) ? stage : null;
}
function markWorkflowReached(step) {
  const idx = WORKFLOW_STEPS.indexOf(step);
  if (idx > maxReachedWorkflowIndex) {
    maxReachedWorkflowIndex = idx;
    localStorage.setItem('hkexMaxReachedWorkflowIndex', String(idx));
  }
}
workflowStepAllowed = function(step) {
  const idx = WORKFLOW_STEPS.indexOf(step);
  return idx >= 0 && idx <= maxReachedWorkflowIndex;
};
setWorkflowStep = function(step, options = {}) {
  const push = options.push !== false;
  if (!WORKFLOW_STEPS.includes(step)) step = 'rule_extraction';
  if (!workflowStepAllowed(step)) {
    setStatus(`You can open ${step.replaceAll('_', ' ')} after the workflow reaches that stage.`);
    return false;
  }
  activeWorkflowStep = step;
  localStorage.setItem('hkexWorkflowStep', step);
  if (push && window.location.hash !== '#' + step) {
    history.pushState({ workflowStep: step }, '', '#' + step);
  }
  document.querySelectorAll('[data-workflow-panel]').forEach(panel => {
    panel.classList.toggle('active', panel.dataset.workflowPanel === step);
  });
  const activeIdx = WORKFLOW_STEPS.indexOf(step);
  document.querySelectorAll('[data-workflow-step]').forEach(el => {
    const idx = WORKFLOW_STEPS.indexOf(el.dataset.workflowStep);
    el.classList.remove('active', 'completed', 'locked');
    if (idx < activeIdx) el.classList.add('completed');
    if (idx === activeIdx) el.classList.add('active');
    if (idx > maxReachedWorkflowIndex) el.classList.add('locked');
    const dot = el.querySelector('.workflow-dot');
    if (dot) dot.textContent = idx < activeIdx ? '✓' : String(idx + 1);
  });
  if (step === 'test_case') {
    if (casesGenerating && !casesGenerated) {
      $('summaryCard').innerHTML = '<div class="metric"><strong>Generating test cases</strong><br>Maker/checker is running. The generated cases will appear here when ready.</div>';
      $('reviewRows').innerHTML = '';
    } else {
      refreshSession().catch(err => renderResult('Load failed', `<pre>${esc(err.message)}</pre>`, 'status-failed'));
    }
  }
  if (step === 'bdd') loadBddData();
  if (step === 'scripts') loadScriptsData();
  return true;
};
nextWorkflowStep = function() {
  const idx = WORKFLOW_STEPS.indexOf(activeWorkflowStep);
  if (idx >= 0 && idx < WORKFLOW_STEPS.length - 1) {
    const next = WORKFLOW_STEPS[idx + 1];
    markWorkflowReached(next);
    setWorkflowStep(next);
  }
};
function renderInlineProgress(targetId, percent, label) {
  const el = $(targetId);
  if (!el) return;
  const safe = Math.max(0, Math.min(100, percent));
  el.innerHTML = `<div class="progress-wrap"><div class="progress-bar" style="width:${safe}%"></div></div><div class="progress-label">${esc(label)} - ${safe}%</div>`;
}
async function fileToBase64(file) {
  const buf = await file.arrayBuffer();
  let binary = '';
  const bytes = new Uint8Array(buf);
  for (let i = 0; i < bytes.length; i++) binary += String.fromCharCode(bytes[i]);
  return btoa(binary);
}
async function postJson(url, payload) {
  const resp = await fetch(url, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload || {}) });
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.error || JSON.stringify(data));
  return data;
}
async function refreshRules() {
  const resp = await fetch('/api/rule-workflow/rules');
  state = await resp.json();
  historyPagination = state.history_pagination || historyPagination;
  historyPage = historyPagination.page || 1;
  historyPageSize = historyPagination.page_size || 10;
  renderRules();
  renderHistory(state.history || [], historyPagination);
  $('saveRulesBtn').disabled = !state.has_rules;
  casesGenerated = !!state.has_review_session;
  if (casesGenerated || casesGenerating) markWorkflowReached('test_case');
  $('ruleNextBtn').disabled = !state.has_rules || casesGenerating;
  if (casesGenerated && activeWorkflowStep === 'rule_extraction') {
    setStatus('Cases are ready. Click Next Step to review test cases or regenerate them.');
  }
  setWorkflowStep(activeWorkflowStep);
}
async function loadHistoryPage(page) {
  const nextPage = Math.max(1, page || 1);
  const resp = await fetch(`/api/rule-workflow/history?page=${encodeURIComponent(nextPage)}&page_size=${encodeURIComponent(historyPageSize)}`);
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.error || 'Failed to load history.');
  state.history = data.history || [];
  historyPagination = data.pagination || historyPagination;
  historyPage = historyPagination.page || nextPage;
  renderHistory(state.history, historyPagination);
}
function renderHistory(items, pagination) {
  pagination = pagination || { page: 1, page_size: historyPageSize, total: items.length, total_pages: 1 };
  if (!items.length) {
    $('history').textContent = 'No history loaded.';
    $('historyPager').classList.add('hidden');
    return;
  }
  $('history').innerHTML = items.map(item => `<div class="history-item">
    <div class="history-title">
      <strong>${esc(item.display_label || item.attempt_id)}</strong>
      <span class="badge">${esc(item.status_label || item.status)}</span>
      <span class="muted">Rules ${esc(item.semantic_rule_count || 0)}</span>
      <span class="muted">Reviewed changes ${esc(item.edited_rule_count || 0)}</span>
    </div>
    <div class="muted">${esc(item.doc_title || item.doc_id || '')} / ${esc(item.doc_version || '')} / ${esc(item.source_filename || '')}</div>
    <div class="history-actions">
      <button class="primary" data-history-view="${esc(item.attempt_id)}">View Details</button>
      <button data-history-apply="${esc(item.attempt_id)}">Apply This Version</button>
    </div>
    <details><summary>Technical details</summary><div class="technical">${esc(item.attempt_id)}<br>${esc(item.attempt_dir || '')}</div></details>
  </div>`).join('');
  $('historyPager').classList.remove('hidden');
  $('historyPager').innerHTML = `<button id="historyPrev" ${pagination.page <= 1 ? 'disabled' : ''}>Previous</button>
    <span>Page ${esc(pagination.page)} / ${esc(pagination.total_pages)} (${esc(pagination.total)} versions)</span>
    <button id="historyNext" ${pagination.page >= pagination.total_pages ? 'disabled' : ''}>Next</button>`;
  $('historyPrev').addEventListener('click', () => loadHistoryPage((pagination.page || 1) - 1).catch(err => setStatus(err.message)));
  $('historyNext').addEventListener('click', () => loadHistoryPage((pagination.page || 1) + 1).catch(err => setStatus(err.message)));
  document.querySelectorAll('[data-history-view]').forEach(btn => btn.addEventListener('click', () => viewHistory(btn.dataset.historyView)));
  document.querySelectorAll('[data-history-apply]').forEach(btn => btn.addEventListener('click', () => applyHistory(btn.dataset.historyApply)));
}
function ruleDiffHtml(rule) {
  const diff = rule._review && rule._review.diff;
  if (!diff || !diff.fields || !diff.fields.length) return '<div class="muted">No business rule changes.</div>';
  return `<h4>Business rule changes</h4>` + diff.fields.map(f => `<div class="diff-item"><strong>${esc(f.change_type)}</strong> ${esc(f.path)}<br><em>before</em>: ${esc(JSON.stringify(f.before))}<br><em>after</em>: ${esc(JSON.stringify(f.after))}</div>`).join('');
}
function atomicDiffHtml(item) {
  const atomic = item && item.rule;
  const diff = atomic && atomic._review && atomic._review.diff;
  if (!diff || !diff.fields || !diff.fields.length) return '<div class="muted">No rule split changes.</div>';
  return `<h4>Rule split changes</h4>` + diff.fields.map(f => `<div class="diff-item"><strong>${esc(f.change_type)}</strong> ${esc(f.path)}<br><em>before</em>: ${esc(JSON.stringify(f.before))}<br><em>after</em>: ${esc(JSON.stringify(f.after))}</div>`).join('');
}
function renderRules() {
  const rules = state.semantic_rules || [];
  if (!rules.length) { $('rules').innerHTML = '<div class="band muted">No rules yet. Upload and extract a document first.</div>'; return; }
  $('rules').innerHTML = rules.map((rule, idx) => {
    const source = rule.source || {};
    const cls = rule.classification || {};
    const stmt = rule.statement || {};
    const hints = rule.test_design_hints || {};
    const exec = rule.execution_mapping || {};
    const review = rule.review || {};
    const calc = (((rule.type_payload || {}).calculation || {}).formula_description) || '';
    const expected = (stmt.outcome || {}).expected_state || '';
    const conditions = (stmt.conditions || []).map(item => item.value || item.description || JSON.stringify(item)).join('\n');
    const inputs = (exec.business_inputs || []).join('\n');
    const exceptions = (stmt.exceptions || []).map(item => item.value || item.reason || JSON.stringify(item)).join('\n');
    const actor = (stmt.actor || {}).value || '';
    const action = (stmt.action || {}).value || '';
    const object = (stmt.object || {}).value || '';
    const evidence = (rule.evidence && rule.evidence[0] && rule.evidence[0].quote) || source.source_excerpt || '';
    const atomic = atomicForRule(rule);
    const semanticEdited = rule._review && rule._review.edited;
    const atomicEdited = atomic && atomic.rule && atomic.rule._review && atomic.rule._review.edited;
    const edited = semanticEdited || atomicEdited;
    const badgeText = (rule._review && rule._review.label) || (atomic && atomic.rule && atomic.rule._review && atomic.rule._review.label) || 'reviewed change';
    return `<div class="rule ${edited ? 'edited' : ''}" data-rule-index="${idx}">
      <div class="rule-head">
        <div>
          <strong>${esc(rule.semantic_rule_id)}</strong>
          <span class="badge">${esc(source.section || '')}</span>
          ${edited ? `<span class="badge edited">${esc(badgeText)}</span>` : ''}
          <div class="muted">pages: ${esc((source.pages || []).join(', '))}</div>
        </div>
      </div>
      <div class="fields">
        <label>business_rule_type <select data-field="classification.rule_type">${['calculation','data_constraint','workflow','obligation','reference_only'].map(v => `<option value="${v}" ${cls.rule_type===v?'selected':''}>${v}</option>`).join('')}</select></label>
        <label>business_testability <select data-field="classification.testability">${['testable','partially_testable','non_testable'].map(v => `<option value="${v}" ${cls.testability===v?'selected':''}>${v}</option>`).join('')}</select></label>
        <label>business_priority <select data-field="classification.priority">${['high','medium','low'].map(v => `<option value="${v}" ${cls.priority===v?'selected':''}>${v}</option>`).join('')}</select></label>
        <label>actor <input data-field="statement.actor.value" value="${esc(actor)}"></label>
        <label>action <input data-field="statement.action.value" value="${esc(action)}"></label>
        <label>object <input data-field="statement.object.value" value="${esc(object)}"></label>
      </div>
      <div class="fields business-editor">
        <label class="wide">Business Rule Summary<textarea data-field="test_design_hints.gherkin_intent">${esc(hints.gherkin_intent || '')}</textarea></label>
        <label class="wide">Conditions<textarea data-object-lines-field="statement.conditions" data-object-kind="document_context">${esc(conditions)}</textarea></label>
        <label>Inputs<textarea data-lines-field="execution_mapping.business_inputs">${esc(inputs)}</textarea></label>
        <label>Calculation / Expected Result<textarea data-field="type_payload.calculation.formula_description">${esc(calc)}</textarea></label>
        <label>Expected State<input data-field="statement.outcome.expected_state" value="${esc(expected)}"></label>
        <label>Exceptions<textarea data-object-lines-field="statement.exceptions" data-object-kind="exception">${esc(exceptions)}</textarea></label>
        <label class="wide">Reviewer Notes<textarea data-field="review.reviewer_notes">${esc(review.reviewer_notes || '')}</textarea></label>
      </div>
      <details open><summary>Source text</summary><pre class="source">${esc(evidence)}</pre></details>
      <details><summary>Reviewed changes</summary>${ruleDiffHtml(rule)}${atomicDiffHtml(atomic)}</details>
      <details><summary>Advanced / Technical Raw JSON</summary><textarea class="json-editor" data-json-index="${idx}">${esc(JSON.stringify(businessRuleJsonForDisplay(rule), null, 2))}</textarea><button data-apply-json="${idx}">Apply JSON</button></details>
    </div>`;
  }).join('');
  document.querySelectorAll('[data-field]').forEach(el => el.addEventListener('change', updateFieldFromInput));
  document.querySelectorAll('[data-field]').forEach(el => el.addEventListener('input', updateFieldFromInput));
  document.querySelectorAll('[data-lines-field]').forEach(el => el.addEventListener('input', updateFieldFromInput));
  document.querySelectorAll('[data-object-lines-field]').forEach(el => el.addEventListener('input', updateFieldFromInput));
  document.querySelectorAll('[data-atomic-field]').forEach(el => el.addEventListener('input', updateAtomicFieldFromInput));
  document.querySelectorAll('select[data-atomic-field]').forEach(el => el.addEventListener('change', updateAtomicFieldFromInput));
  document.querySelectorAll('[data-apply-json]').forEach(btn => btn.addEventListener('click', applyRawJson));
}
function atomicForRule(rule) {
  const ids = (rule.source && rule.source.atomic_rule_ids) || [];
  const id = ids[0];
  if (!id) return null;
  const idx = (state.atomic_rules || []).findIndex(item => item.rule_id === id);
  if (idx < 0) return null;
  return { index: idx, rule: state.atomic_rules[idx] };
}
function atomicHtml(item) {
  const atomic = item.rule || {};
  const edited = atomic._review && atomic._review.edited;
  const label = (atomic._review && atomic._review.label) || 'reviewed change';
  return `<details><summary>Rule Split Detail ${edited ? `<span class="badge edited">${esc(label)}</span>` : ''}</summary>
    <div class="atomic-box" data-atomic-index="${item.index}">
      <div><strong>${esc(atomic.rule_id || '')}</strong> <span class="badge">${esc(atomic.section || '')}</span></div>
      <div class="fields">
        <label>rule_type <select data-atomic-field="rule_type">${['calculation','data_constraint','workflow','obligation','reference_only'].map(v => `<option value="${v}" ${atomic.rule_type===v?'selected':''}>${v}</option>`).join('')}</select></label>
        <label>testability <select data-atomic-field="testability">${['testable','partially_testable','non_testable'].map(v => `<option value="${v}" ${atomic.testability===v?'selected':''}>${v}</option>`).join('')}</select></label>
        <label class="wide">Business split text<textarea rows="5" data-atomic-field="raw_text">${esc(atomic.raw_text || '')}</textarea></label>
        <label class="wide">Atomic reviewer note<textarea rows="2" data-atomic-field="review_note">${esc(atomic.review_note || '')}</textarea></label>
      </div>
    </div>
  </details>`;
}
function stripPrivate(rule) {
  const cloned = JSON.parse(JSON.stringify(rule));
  delete cloned._review;
  return cloned;
}
const BUSINESS_JSON_KEY_MAP = {
  semantic_rule_id: 'business_rule_id',
  semantic_rule_ref: 'business_rule_ref',
  semantic_rules: 'business_rules',
};
const SCHEMA_JSON_KEY_MAP = {
  business_rule_id: 'semantic_rule_id',
  business_rule_ref: 'semantic_rule_ref',
  business_rules: 'semantic_rules',
};
function replaceBusinessTerms(value, toBusiness) {
  if (typeof value !== 'string') return value;
  if (toBusiness) {
    return value
      .replaceAll('semantic_rule_id', 'business_rule_id')
      .replaceAll('semantic_rule_ref', 'business_rule_ref')
      .replaceAll('semantic rules', 'business rules')
      .replaceAll('Semantic Rules', 'Business Rules')
      .replaceAll('semantic rule', 'business rule')
      .replaceAll('Semantic Rule', 'Business Rule');
  }
  return value
    .replaceAll('business_rule_id', 'semantic_rule_id')
    .replaceAll('business_rule_ref', 'semantic_rule_ref')
    .replaceAll('business rules', 'semantic rules')
    .replaceAll('Business Rules', 'Semantic Rules')
    .replaceAll('business rule', 'semantic rule')
    .replaceAll('Business Rule', 'Semantic Rule');
}
function renameRuleJson(value, keyMap, toBusiness) {
  if (Array.isArray(value)) return value.map(item => renameRuleJson(item, keyMap, toBusiness));
  if (value && typeof value === 'object') {
    const out = {};
    for (const [key, item] of Object.entries(value)) {
      out[keyMap[key] || key] = renameRuleJson(item, keyMap, toBusiness);
    }
    return out;
  }
  return replaceBusinessTerms(value, toBusiness);
}
function businessRuleJsonForDisplay(rule) {
  return renameRuleJson(stripPrivate(rule), BUSINESS_JSON_KEY_MAP, true);
}
function schemaRuleJsonFromDisplay(rule) {
  return renameRuleJson(rule, SCHEMA_JSON_KEY_MAP, false);
}
function setPath(obj, path, value) {
  const parts = path.split('.');
  let cur = obj;
  for (let i = 0; i < parts.length - 1; i++) {
    if (!cur[parts[i]] || typeof cur[parts[i]] !== 'object') cur[parts[i]] = {};
    cur = cur[parts[i]];
  }
  cur[parts[parts.length - 1]] = value;
}
function setLinesPath(obj, path, value) {
  setPath(obj, path, String(value || '').split('\n').map(item => item.trim()).filter(Boolean));
}
function setObjectLinesPath(obj, path, value, kind) {
  const items = String(value || '').split('\n').map(item => item.trim()).filter(Boolean).map((line, idx) => ({
    id: `${kind === 'exception' ? 'E' : 'C'}${idx + 1}`,
    kind: kind || 'document_context',
    field: kind === 'exception' ? 'exception' : 'business_condition',
    operator: 'describes',
    value: line,
    source_type: 'human_review',
  }));
  setPath(obj, path, items);
}
function updateFieldFromInput(event) {
  const card = event.target.closest('[data-rule-index]');
  const idx = Number(card.dataset.ruleIndex);
  if (event.target.dataset.linesField) {
    setLinesPath(state.semantic_rules[idx], event.target.dataset.linesField, event.target.value);
  } else if (event.target.dataset.objectLinesField) {
    setObjectLinesPath(state.semantic_rules[idx], event.target.dataset.objectLinesField, event.target.value, event.target.dataset.objectKind);
  } else {
    setPath(state.semantic_rules[idx], event.target.dataset.field, event.target.value);
  }
}
function updateAtomicFieldFromInput(event) {
  const card = event.target.closest('[data-atomic-index]');
  if (!card) return;
  const idx = Number(card.dataset.atomicIndex);
  const field = event.target.dataset.atomicField;
  state.atomic_rules[idx][field] = event.target.value;
}
function applyRawJson(event) {
  const idx = Number(event.target.dataset.applyJson);
  const textarea = document.querySelector(`[data-json-index="${idx}"]`);
  state.semantic_rules[idx] = schemaRuleJsonFromDisplay(JSON.parse(textarea.value));
  renderRules();
}
async function uploadSource() {
  const file = $('sourceFile').files[0];
  if (!file) throw new Error('Choose a source file first.');
  setStatus('Uploading source...');
  const data = await postJson('/api/rule-workflow/upload-source', {
    filename: file.name,
    content_base64: await fileToBase64(file),
    doc_id: $('docId').value,
    doc_title: $('docTitle').value,
    doc_version: $('docVersion').value,
  });
  $('docId').value = data.metadata.doc_id || $('docId').value;
  $('docTitle').value = data.metadata.doc_title || $('docTitle').value;
  $('docVersion').value = data.metadata.doc_version || $('docVersion').value;
  $('extractBtn').disabled = false;
  setStatus('Uploaded: ' + data.source_path);
}
async function extractSource() {
  setStatus('Extracting rules...');
  const data = await postJson('/api/rule-workflow/extract', {
    doc_id: $('docId').value,
    doc_title: $('docTitle').value,
    doc_version: $('docVersion').value,
  });
  setStatus(`Extracted ${data.semantic_rule_count} business rules.\nSections:\n` + (data.sections || []).join('\n'));
  await refreshRules();
}
async function saveRules() {
  setStatus('Saving reviewed rules...');
  const payload = { atomic_rules: state.atomic_rules, semantic_rules: state.semantic_rules.map(stripPrivate) };
  const data = await postJson('/api/rule-workflow/rules/save', payload);
  const label = (data.history_snapshot && data.history_snapshot.display_label) || 'new iteration';
  setStatus(`Saved as ${label}. Business rule changes=${data.semantic_diff_count || 0}.`);
  await refreshRules();
}
async function viewHistory(attemptId) {
  const resp = await fetch('/api/rule-workflow/history/detail?attempt_id=' + encodeURIComponent(attemptId));
  const detail = await resp.json();
  if (!resp.ok) { setStatus(detail.error || 'Failed to load history detail.'); return; }
  const manifest = detail.manifest || {};
  const rules = detail.semantic_rules || [];
  const diffs = (detail.diff && detail.diff.diffs) || [];
  const atomicDiffs = (detail.diff && detail.diff.atomic_diffs) || [];
  $('historyDetail').classList.remove('hidden');
  $('historyDetail').innerHTML = `<h3>Selected History Detail: ${esc(manifest.display_label || attemptId)}</h3>
    <div class="history-title">
      <span class="badge">${esc(manifest.status_label || manifest.status || '')}</span>
      <span class="muted">${esc(manifest.doc_title || manifest.doc_id || '')}; ${esc(manifest.doc_version || '')}; ${esc(manifest.source_filename || '')}</span>
    </div>
    <div class="history-actions"><button class="primary" data-history-detail-apply="${esc(manifest.attempt_id || attemptId)}">Apply This Version</button></div>
    <div class="history-rules">
      ${rules.map(rule => `<div class="history-rule"><strong>${esc(rule.semantic_rule_id)}</strong> <span class="badge">${esc((rule.source || {}).section || '')}</span><pre>${esc(((rule.evidence || [])[0] || {}).quote || '')}</pre></div>`).join('')}
    </div>
    <details open><summary>Reviewed changes in this history version (${diffs.length + atomicDiffs.length})</summary>
      ${diffs.map(item => `<div class="diff-item"><strong>${esc(item.semantic_rule_id)}</strong> semantic ${esc(item.change_type)}<br>${(item.fields || []).map(f => `${esc(f.path)}: ${esc(JSON.stringify(f.before))} -> ${esc(JSON.stringify(f.after))}`).join('<br>')}</div>`).join('')}
      ${atomicDiffs.map(item => `<div class="diff-item"><strong>${esc(item.rule_id)}</strong> rule split ${esc(item.change_type)}<br>${(item.fields || []).map(f => `${esc(f.path)}: ${esc(JSON.stringify(f.before))} -> ${esc(JSON.stringify(f.after))}`).join('<br>')}</div>`).join('')}
      ${(diffs.length + atomicDiffs.length) ? '' : '<span class="muted">No reviewed changes.</span>'}
    </details>
    <details><summary>Technical details</summary><div class="technical">${esc(manifest.attempt_id || attemptId)}<br>${esc(manifest.attempt_dir || '')}</div></details>`;
  document.querySelectorAll('[data-history-detail-apply]').forEach(btn => btn.addEventListener('click', () => applyHistory(btn.dataset.historyDetailApply)));
}
async function applyHistory(attemptId) {
  const data = await postJson('/api/rule-workflow/history/apply', { attempt_id: attemptId });
  state = data.review_payload;
  renderRules();
  historyPagination = state.history_pagination || historyPagination;
  renderHistory(state.history || [], historyPagination);
  setStatus(`Applied ${data.applied_from_label || attemptId}. Current badges show reviewed changes from that history snapshot.`);
}
function issueOptionMap() {
  return new Map(((sessionPayload && sessionPayload.issue_type_options) || []).map(item => [item.code, item]));
}
function issueSummaryText(review) {
  const selected = review.issue_types || [];
  if (!selected.length) return 'None selected';
  const map = issueOptionMap();
  return selected.map(code => (map.get(code) && map.get(code).label) || code).join(', ');
}
function issueTableHtml(review) {
  return ((sessionPayload && sessionPayload.issue_type_options) || []).map(item => `
    <tr>
      <td><input type="checkbox" data-field="issue_type_option" data-case-id="${esc(review.case_id)}" data-issue-code="${esc(item.code)}" ${review.issue_types?.includes(item.code) ? 'checked' : ''}></td>
      <td>${esc(item.label)}</td>
      <td>${esc(item.code)}</td>
      <td>${esc(item.description)}</td>
    </tr>
  `).join('');
}
function reviewControls(review) {
  const caseId = esc(review.case_id);
  return `<div><label>Decision<select data-field="review_decision" data-case-id="${caseId}">
    <option value="pending" ${review.review_decision === 'pending' ? 'selected' : ''}>pending</option>
    <option value="approve" ${review.review_decision === 'approve' ? 'selected' : ''}>approve</option>
    <option value="rewrite" ${review.review_decision === 'rewrite' ? 'selected' : ''}>rewrite</option>
  </select></label></div>
  <div><label>Issue Types</label><details class="issue-picker"><summary class="issue-summary" data-issue-summary="${caseId}">${esc(issueSummaryText(review))}</summary><table class="issue-table"><thead><tr><th>Select</th><th>Label</th><th>Code</th><th>Description</th></tr></thead><tbody>${issueTableHtml(review)}</tbody></table></details></div>
  <div><label>Comment<textarea data-field="human_comment" data-case-id="${caseId}" rows="4">${esc(review.human_comment || '')}</textarea></label></div>`;
}
function checkerSuggestionHtml(value) {
  return value ? '<span class="suggestion-no">No</span>' : '<span class="suggestion-yes">Yes</span>';
}
function renderReviewRows() {
  if (!sessionPayload) return;
  $('reviewRows').innerHTML = sessionPayload.table_rows.map(row => {
    const review = reviewMap.get(row.case_id) || {};
    return `<tr data-coverage="${esc(row.coverage)}" data-blocking="${String(row.checker_blocking)}">
      <td>${esc(row.semantic_rule_id)}</td>
      <td>${esc(row.case_id)}</td>
      <td>${esc(row.feature)}</td>
      <td>${esc(row.case_type)}</td>
      <td>${esc(row.coverage)}</td>
      <td>${checkerSuggestionHtml(!!row.checker_blocking)}</td>
      <td>${esc(row.blocking_reason)}</td>
      <td><details><summary>Details</summary>${row.detail_html}</details></td>
      <td>${reviewControls(review)}</td>
    </tr>`;
  }).join('');
  hydrateReviewControls();
}
function hydrateReviewControls() {
  for (const review of reviewMap.values()) {
    for (const el of document.querySelectorAll(`[data-case-id="${CSS.escape(review.case_id)}"]`)) {
      const field = el.dataset.field;
      if (!field) continue;
      if (field === 'issue_type_option') el.checked = (review.issue_types || []).includes(el.dataset.issueCode);
      else if (field === 'human_comment') el.value = review.human_comment || '';
      else el.value = review[field] || '';
      el.addEventListener('change', () => syncReviewField(el));
      el.addEventListener('input', () => syncReviewField(el));
    }
    syncIssueSummary(review.case_id);
  }
  updateSaveRerunState();
}
function syncIssueSummary(caseId) {
  const review = reviewMap.get(caseId);
  const summary = document.querySelector(`[data-issue-summary="${CSS.escape(caseId)}"]`);
  if (review && summary) summary.textContent = issueSummaryText(review);
}
function syncReviewField(el) {
  const review = reviewMap.get(el.dataset.caseId);
  if (!review) return;
  const field = el.dataset.field;
  if (field === 'issue_type_option') {
    const selected = new Set(review.issue_types || []);
    if (el.checked) selected.add(el.dataset.issueCode);
    else selected.delete(el.dataset.issueCode);
    review.issue_types = Array.from(selected);
    syncIssueSummary(el.dataset.caseId);
  } else {
    review[field] = el.value;
  }
  updateSaveRerunState();
}
function reviewRequiresRerun(review) {
  const decision = review.review_decision || 'pending';
  const comment = String(review.human_comment || '');
  return decision === 'rewrite' || (decision === 'pending' && /\S/.test(comment));
}
function hasRerunEdits() {
  return Array.from(reviewMap.values()).some(reviewRequiresRerun);
}
function normalizedReviewForSubmit(review) {
  const item = cloneJson(review);
  if ((item.review_decision || 'pending') === 'pending' && /\S/.test(String(item.human_comment || ''))) {
    item.review_decision = 'rewrite';
  }
  return item;
}
function updateSaveRerunState() {
  const btn = $('saveRerunBtn');
  if (btn) btn.disabled = !hasRerunEdits();
}
function applyReviewFilters() {
  const coverage = $('coverageFilter').value;
  const blocking = $('blockingFilter').value;
  for (const row of document.querySelectorAll('#reviewRows tr')) {
    const show = (!coverage || row.dataset.coverage === coverage) && (!blocking || row.dataset.blocking === blocking);
    row.style.display = show ? '' : 'none';
  }
}
function currentReviewPayload({ forRerun = false } = {}) {
  const reviews = Array.from(reviewMap.values()).map(item => forRerun ? normalizedReviewForSubmit(item) : cloneJson(item));
  return { metadata: sessionPayload ? sessionPayload.metadata : {}, reviews };
}
function renderResult(title, bodyHtml, cssClass='') {
  const card = $('resultCard');
  card.style.display = '';
  card.innerHTML = `<h2 class="${cssClass}">${esc(title)}</h2>${bodyHtml}`;
}
function compareLinkHtml(item) {
  if (!item || !item.compare_path) return '';
  return `<a href="/files?path=${encodeURIComponent(item.compare_path)}" target="_blank">View Changes</a>`;
}
function renderReviewHistory(currentIteration = null) {
  const items = (sessionPayload && sessionPayload.history) || [];
  const container = $('reviewHistoryCard');
  if (!items.length) { container.textContent = 'No history.'; return; }
  container.innerHTML = items.map(item => {
    const isCurrent = currentIteration !== null && Number(item.iteration) === Number(currentIteration);
    const nextIteration = item.next_iteration ?? (Number.isFinite(Number(item.iteration)) ? Number(item.iteration) + 1 : '');
    const title = nextIteration === '' ? `Iteration ${esc(String(item.iteration))} changes` : `Iteration ${esc(String(item.iteration))} -> ${esc(String(nextIteration))} changes`;
    const compare = compareLinkHtml(item) || '<span class="muted">No case changes in this iteration.</span>';
    return `<div class="history-row ${isCurrent ? 'current' : ''}"><strong>${title}</strong>${isCurrent ? ' <span class="status-succeeded">Current iteration</span>' : ''}<div>${compare}</div></div>`;
  }).join('');
}
async function refreshSession(currentIteration = null) {
  const response = await fetch('/api/session');
  if (!response.ok) throw new Error('Test Case review is not ready. Generate cases first.');
  sessionPayload = await response.json();
  reviewMap = new Map(sessionPayload.reviews.map(item => [item.case_id, cloneJson(item)]));
  reviewBaselineMap = new Map(sessionPayload.reviews.map(item => [item.case_id, cloneJson(item)]));
  $('summaryCard').innerHTML = `<div class="metric-grid">
    <div class="metric"><strong>Session ID</strong><br>${esc(sessionPayload.session_id)}</div>
    <div class="metric"><strong>Status</strong><br>${esc(sessionPayload.session_status)}</div>
    <div class="metric"><strong>Current Iteration</strong><br>${esc(String(sessionPayload.current_iteration))}</div>
  </div>`;
  renderReviewRows();
  renderReviewHistory(currentIteration);
  applyReviewFilters();
}
async function saveAndRerun() {
  if (!hasRerunEdits()) return;
  if (pollTimer) clearTimeout(pollTimer);
  renderInlineProgress('resultCard', 0, 'Submitting');
  $('resultCard').style.display = '';
  const result = await postJson('/api/submit', currentReviewPayload({ forRerun: true }));
  pollReviewJob(result.job_id);
}
async function pollReviewJob(jobId) {
  const response = await fetch(`/api/status/${encodeURIComponent(jobId)}`);
  const payload = await response.json();
  const phase = payload.phase || payload.status || 'queued';
  if (payload.status === 'queued' || payload.status === 'running') {
    renderInlineProgress('resultCard', PHASE_PROGRESS[phase] ?? 10, PHASE_LABEL[phase] || phase);
    pollTimer = setTimeout(() => pollReviewJob(jobId), 2000);
    return;
  }
  if (payload.status === 'failed') {
    renderResult('Rerun failed', `<pre>${esc(payload.error || '')}</pre>`, 'status-failed');
    return;
  }
  const result = payload.result || {};
  const iteration = result.next_iteration || '';
  const historyIteration = result.history_iteration ?? iteration;
  await refreshSession(historyIteration);
  const compare = result.links?.case_compare_html ? `<a href="${result.links.case_compare_html}" target="_blank">View Changes</a>` : '';
  renderResult('Rerun completed', `<div class="status-succeeded">Iteration ${esc(String(iteration))} generated.</div>${compare ? `<div>${compare}</div>` : '<div class="muted">No comparable case changes generated.</div>'}`, 'status-succeeded');
}
async function openAuditTrail() {
  const resp = await fetch('/api/audit_trail');
  const data = await resp.json();
  if (data.audit_trail_url) window.open(data.audit_trail_url, '_blank');
}
function checkTestCaseReports() {
  const links = [
    '<a href="/report.html" target="_blank">Test Case Report</a>',
    '<a href="/maker_readable.html" target="_blank">Maker Report</a>',
    '<a href="/checker_readable.html" target="_blank">Checker Report</a>',
  ].join('<br>');
  renderResult('Reports', `<div class="status-succeeded">Reports are ready.</div>${links}`, 'status-succeeded');
  window.open('/report.html', '_blank');
}
async function goFromTestCaseToBdd() {
  if (hasRerunEdits()) {
    renderResult('Rerun needed', '<div class="warning">There are rewrite comments or decisions. Use Save &amp; Rerun before moving to BDD.</div>');
    return;
  }
  if (sessionPayload) await postJson('/api/reviews/save', currentReviewPayload());
  markWorkflowReached('bdd');
  setWorkflowStep('bdd');
  await generateBdd();
}
function loadBddData() {
  fetch('/api/bdd').then(r => r.json()).then(data => {
    bddPayload = data;
    renderBddPanel(data);
  }).catch(err => { $('bddContent').innerHTML = `<section class="band status-failed">${esc(err.message)}</section>`; });
}
function renderBddPanel(data) {
  const el = $('bddContent');
  updateBddModeNotice('');
  $('saveBddBtn').disabled = !data.has_bdd;
  $('bddNextBtn').disabled = !data.has_bdd;
  if (!data.has_bdd) {
    el.innerHTML = '<section class="band muted">BDD has not been generated for the current Test Case output. Use Next Step from Test Case to generate BDD.</section>';
    return;
  }
  markWorkflowReached('bdd');
  el.innerHTML = data.scenarios_by_rule.map(rule => `
    <div class="bdd-rule-block">
      <strong>${esc(rule.semantic_rule_id)} - ${esc(rule.feature_title)}</strong>
      ${rule.scenarios.map(s => `
        <div class="bdd-scenario-card">
          <div><strong>${esc(s.scenario_id)}</strong> <em>${esc(s.case_type)} / ${esc(s.priority)}</em></div>
          ${['given','when','then'].map(type => `<div class="step-label">${type.toUpperCase()}</div>${(s[type + '_steps'] || []).map((st,i) => `<textarea class="step-textarea" rows="2" data-scenario="${esc(s.scenario_id)}" data-step-type="${type}" data-step-index="${i}">${esc(st.step_text || '')}</textarea>`).join('')}`).join('')}
        </div>`).join('')}
    </div>`).join('');
  bddDirty = false;
  document.querySelectorAll('#bddContent textarea[data-scenario]').forEach(ta => ta.addEventListener('input', () => { bddDirty = true; }));
}
async function generateBdd() {
  $('bddProgressCard').style.display = '';
  renderInlineProgress('bddProgressCard', 5, 'Starting BDD generation');
  $('bddStatus').textContent = 'Starting BDD generation...';
  updateBddModeNotice('');
  const data = await postJson('/api/rule-workflow/generate-bdd', {});
  pollBddJob(data.job_id);
}
async function pollBddJob(jobId) {
  const response = await fetch('/api/rule-workflow/status/' + encodeURIComponent(jobId));
  const payload = await response.json();
  if (payload.status === 'failed') {
    $('bddProgressCard').style.display = '';
    $('bddProgressCard').innerHTML = `<div class="status-failed">${esc(payload.error || 'BDD generation failed.')}</div>`;
    $('bddStatus').textContent = payload.error || 'BDD generation failed.';
    return;
  }
  if (payload.status !== 'succeeded') {
    const phase = payload.phase || payload.status || 'queued';
    const progress = BDD_PROGRESS[phase] || 10;
    renderInlineProgress('bddProgressCard', progress, BDD_LABEL[phase] || phase);
    $('bddStatus').textContent = `${BDD_LABEL[phase] || phase} - ${progress}%`;
    setTimeout(() => pollBddJob(jobId), 1500);
    return;
  }
  const summary = payload.result && payload.result.bdd_summary ? payload.result.bdd_summary : {};
  const fallbackCount = Number(summary.fallback_batch_count || 0);
  const fallbackNote = fallbackCount > 0 ? `Deterministic fallback was used for ${fallbackCount} batch(es).` : 'Generated by LLM without fallback.';
  renderInlineProgress('bddProgressCard', 100, 'BDD generated. Review BDD below.');
  $('bddStatus').textContent = `BDD generated. ${fallbackNote}`;
  updateBddModeNotice(fallbackNote);
  markWorkflowReached('bdd');
  scriptsPayload = null;
  await loadBddData();
}
async function saveBddEdits() {
  const byScenario = {};
  document.querySelectorAll('#bddContent textarea[data-scenario]').forEach(ta => {
    const sid = String(ta.dataset.scenario || '');
    const stype = String(ta.dataset.stepType || '').toLowerCase();
    const sidx = parseInt(ta.dataset.stepIndex || '0', 10);
    if (!sid || !stype) return;
    if (!byScenario[sid]) byScenario[sid] = { scenario_id: sid, given_steps: [], when_steps: [], then_steps: [] };
    byScenario[sid][stype + '_steps'][sidx] = { step_text: ta.value, step_pattern: '' };
  });
  const result = await postJson('/api/bdd/save', { edits: Object.values(byScenario) });
  $('bddStatus').textContent = `Saved ${result.edit_count} BDD edits.`;
  scriptsPayload = null;
  bddDirty = false;
}
async function saveBddAndNext() {
  if (bddDirty) await saveBddEdits();
  markWorkflowReached('scripts');
  nextWorkflowStep();
}
function loadScriptsData() {
  fetch('/api/scripts').then(r => r.json()).then(data => {
    scriptsPayload = data;
    if (data.has_registry) markWorkflowReached('scripts');
    renderScriptsPanel(data);
  }).catch(err => { $('scriptsContent').innerHTML = `<section class="band status-failed">${esc(err.message)}</section>`; });
}
function scriptStatusLabel(type) {
  return type === 'unmatched' ? 'need to create' : (type || 'need to create');
}
function scriptCodeBlock(step, attrs) {
  const code = step.code || '';
  const source = step.script_source ? ` (${step.script_source})` : '';
  const disabled = code ? '' : ' disabled';
  return `<details class="script-code"><summary>Script Code${esc(source)}</summary>
    ${step.endpoint_name ? `<div class="muted">endpoint: ${esc(step.endpoint_name)}</div>` : ''}
    <textarea class="script-code-textarea" ${attrs}${disabled}>${esc(code || 'Script code has not been generated yet.')}</textarea>
  </details>`;
}
function renderScriptsPanel(data) {
  const el = $('scriptsContent');
  if (!data.has_registry) { el.innerHTML = '<section class="band muted">No step registry linked.</section>'; return; }
  const s = data.summary || {};
  const pendingCount = ((data.steps_by_type && ['given','when','then'].flatMap(t => data.steps_by_type[t] || []).filter(st => st.match_type === 'unmatched' && !st.code).length) || 0)
    + ((data.gaps || []).filter(g => !g.code).length);
  $('createScriptsAiBtn').disabled = pendingCount === 0 || !!data.generated_scripts_path;
  scriptsDirty = false;
  updateScriptsSaveButton();
  el.innerHTML = `<div class="scripts-metrics">
    <div class="scripts-metric"><strong>${s.total_steps || 0}</strong><span>Total Steps</span></div>
    <div class="scripts-metric"><strong>${s.exact_matches || 0}</strong><span>Exact Matches</span></div>
    <div class="scripts-metric"><strong>${s.parameterized_matches || 0}</strong><span>Parameterized</span></div>
    <div class="scripts-metric"><strong>${s.unmatched || 0}</strong><span>Need to Create</span></div>
    <div class="scripts-metric"><strong>${s.candidates || 0}</strong><span>Candidates</span></div>
  </div>
  ${['given','when','then'].map(type => {
    const steps = (data.steps_by_type && data.steps_by_type[type]) || [];
    if (!steps.length) return '';
    return `<div class="step-block"><h3>${type.toUpperCase()}</h3>${steps.map((step, idx) => `
      <div class="step-item ${step.match_type || ''}">
        <span class="step-item-badge">${esc(scriptStatusLabel(step.match_type))}</span>
        <textarea class="step-textarea" data-step-type="${type}" data-step-index="${idx}" rows="2">${esc(step.step_text || '')}</textarea>
        ${scriptCodeBlock(step, `data-script-step-type="${type}" data-script-step-index="${idx}"`)}
      </div>`).join('')}</div>`;
  }).join('')}
  ${(data.gaps && data.gaps.length) ? `<div class="step-block"><h3>GAPS (${data.gaps.length})</h3>${data.gaps.map((g, idx) => `
    <div class="step-item unmatched">
      <span class="step-item-badge">need to create</span>
      <textarea class="step-textarea" data-gap-index="${idx}" data-step-type="${esc(g.step_type || '')}" rows="2">${esc(g.step_text || '')}</textarea>
      ${scriptCodeBlock(g, `data-script-gap-index="${idx}" data-script-step-type="${esc(g.step_type || '')}"`)}
    </div>`).join('')}</div>` : ''}`;
  document.querySelectorAll('#scriptsContent .step-textarea, #scriptsContent .script-code-textarea').forEach(el => {
    el.addEventListener('input', markScriptsDirty);
    el.addEventListener('change', markScriptsDirty);
  });
}
function markScriptsDirty() {
  scriptsDirty = true;
  updateScriptsSaveButton();
}
function updateScriptsSaveButton() {
  const btn = $('saveScriptsBtn');
  if (!btn) return;
  btn.classList.toggle('hidden', !scriptsDirty);
}
function collectScriptsEdits() {
  const edits = [];
  document.querySelectorAll('#scriptsContent .step-textarea[data-step-type]:not([data-gap-index])').forEach(ta => {
    const selector = `.script-code-textarea[data-script-step-type="${ta.dataset.stepType}"][data-script-step-index="${ta.dataset.stepIndex}"]`;
    const codeEl = document.querySelector(selector);
    edits.push({ step_type: ta.dataset.stepType, step_index: parseInt(ta.dataset.stepIndex || '0', 10), step_text: ta.value, code: codeEl && !codeEl.disabled ? codeEl.value : '' });
  });
  document.querySelectorAll('#scriptsContent .step-textarea[data-gap-index]').forEach(ta => {
    const selector = `.script-code-textarea[data-script-gap-index="${ta.dataset.gapIndex}"]`;
    const codeEl = document.querySelector(selector);
    edits.push({ is_gap: true, gap_index: parseInt(ta.dataset.gapIndex || '0', 10), step_type: ta.dataset.stepType, step_text: ta.value, code: codeEl && !codeEl.disabled ? codeEl.value : '' });
  });
  return edits;
}
async function saveScriptsEdits({ reload = true, silent = false } = {}) {
  const edits = collectScriptsEdits();
  if (!edits.length) {
    scriptsDirty = false;
    updateScriptsSaveButton();
    return {};
  }
  const result = await postJson('/api/scripts/save', { edits });
  scriptsDirty = false;
  updateScriptsSaveButton();
  if (!silent) $('scriptsStatus').textContent = `Saved scripts edits.`;
  scriptsPayload = null;
  if (reload && result.refreshed_step_registry_path) loadScriptsData();
  return result;
}
async function createScriptsByAi() {
  $('scriptsProgressCard').classList.remove('hidden');
  renderInlineProgress('scriptsProgressCard', 5, 'Starting Scripts AI generation');
  $('scriptsStatus').textContent = 'Starting Scripts AI generation...';
  $('createScriptsAiBtn').disabled = true;
  $('saveScriptsBtn').classList.add('hidden');
  const data = await postJson('/api/scripts/create-by-ai', {});
  pollScriptsAiJob(data.job_id);
}
async function pollScriptsAiJob(jobId) {
  const response = await fetch(`/api/status/${encodeURIComponent(jobId)}`);
  const payload = await response.json();
  if (payload.status === 'failed') {
    $('scriptsProgressCard').innerHTML = `<div class="status-failed">${esc(payload.error || 'Scripts generation failed.')}</div>`;
    $('scriptsStatus').textContent = payload.error || 'Scripts generation failed.';
    $('createScriptsAiBtn').disabled = false;
    return;
  }
  if (payload.status !== 'succeeded') {
    const phase = payload.phase || payload.status || 'queued';
    const progress = SCRIPTS_PROGRESS[phase] || 10;
    renderInlineProgress('scriptsProgressCard', progress, SCRIPTS_LABEL[phase] || phase);
    $('scriptsStatus').textContent = `${SCRIPTS_LABEL[phase] || phase} - ${progress}%`;
    setTimeout(() => pollScriptsAiJob(jobId), 1500);
    return;
  }
  const result = payload.result || {};
  renderInlineProgress('scriptsProgressCard', 100, `Generated ${result.generated_count || 0} scripts`);
  $('scriptsStatus').textContent = `Generated ${result.generated_count || 0} scripts. Review or edit the code. Edits are saved by Save or Next Step.`;
  await loadScriptsData();
}
async function saveScriptsAndNext() {
  await saveScriptsEdits({ reload: false, silent: true });
  markWorkflowReached('finalize');
  nextWorkflowStep();
}
async function finalizeWorkflow() {
  try {
    const result = await postJson('/api/finalize', {});
    const links = [
      result.final_report_url ? `<a href="${result.final_report_url}" target="_blank">Final Report</a>` : '',
      result.final_maker_url ? `<a href="${result.final_maker_url}" target="_blank">Maker Report</a>` : '',
      result.final_checker_url ? `<a href="${result.final_checker_url}" target="_blank">Checker Report</a>` : '',
    ].filter(Boolean).join('<br>');
    $('finalizeStatus').innerHTML = `<div class="status-succeeded">Workflow finalized.</div>${links}`;
  } catch (err) {
    $('finalizeStatus').innerHTML = `<div class="status-failed">${esc(err.message)}</div>`;
  }
}
async function generateCases() {
  await saveRules();
  casesGenerating = true;
  casesGenerated = false;
  markWorkflowReached('test_case');
  $('ruleNextBtn').disabled = true;
  setWorkflowStep('test_case');
  renderInlineProgress('resultCard', 5, 'Starting test case generation');
  $('resultCard').style.display = '';
  setStatus('Generating test cases...');
  const data = await postJson('/api/rule-workflow/generate-cases', {});
  pollGenerate(data.job_id);
}
async function pollGenerate(jobId) {
  const resp = await fetch('/api/rule-workflow/status/' + encodeURIComponent(jobId));
  const data = await resp.json();
  if (data.status === 'failed') { setStatus(data.error || 'Generate cases failed.'); return; }
  if (data.status !== 'succeeded') {
    const phase = data.phase || data.status || 'queued';
    renderInlineProgress('resultCard', GENERATE_PROGRESS[phase] ?? 10, GENERATE_LABEL[phase] || phase);
    setStatus(`Generate cases: ${GENERATE_LABEL[phase] || phase}`);
    setTimeout(() => pollGenerate(jobId), 1500);
    return;
  }
  casesGenerating = false;
  casesGenerated = true;
  markWorkflowReached('test_case');
  $('ruleNextBtn').disabled = false;
  await refreshRules();
  await refreshSession();
  renderInlineProgress('resultCard', 100, 'Test cases generated. Review cases below.');
  setStatus('Test cases generated.');
}

const initialStageFromUrl = stageFromLocation();
if (initialStageFromUrl) activeWorkflowStep = initialStageFromUrl;
document.querySelectorAll('[data-workflow-step]').forEach(el => {
  el.addEventListener('click', () => setWorkflowStep(el.dataset.workflowStep));
});
window.addEventListener('popstate', () => {
  const stage = stageFromLocation() || 'rule_extraction';
  setWorkflowStep(stage, { push: false });
});
window.addEventListener('hashchange', () => {
  const stage = stageFromLocation() || 'rule_extraction';
  if (stage !== activeWorkflowStep) setWorkflowStep(stage, { push: false });
});

$('uploadBtn').addEventListener('click', () => uploadSource().catch(err => setStatus(err.message)));
$('extractBtn').addEventListener('click', () => extractSource().catch(err => setStatus(err.message)));
$('saveRulesBtn').addEventListener('click', () => saveRules().catch(err => setStatus(err.message)));
$('ruleNextBtn').addEventListener('click', () => generateCases().catch(err => setStatus(err.message)));
$('coverageFilter').addEventListener('change', applyReviewFilters);
$('blockingFilter').addEventListener('change', applyReviewFilters);
$('saveRerunBtn').addEventListener('click', () => saveAndRerun().catch(err => renderResult('Rerun failed', `<pre>${esc(err.message)}</pre>`, 'status-failed')));
$('testCaseReportBtn').addEventListener('click', () => checkTestCaseReports());
$('auditBtn').addEventListener('click', () => openAuditTrail().catch(err => renderResult('Audit Trail failed', `<pre>${esc(err.message)}</pre>`, 'status-failed')));
$('testCaseNextBtn').addEventListener('click', () => goFromTestCaseToBdd().catch(err => renderResult('Next Step failed', `<pre>${esc(err.message)}</pre>`, 'status-failed')));
$('saveBddBtn').addEventListener('click', () => saveBddEdits().catch(err => { $('bddStatus').textContent = err.message; }));
$('bddNextBtn').addEventListener('click', () => saveBddAndNext().catch(err => { $('bddStatus').textContent = err.message; }));
$('createScriptsAiBtn').addEventListener('click', () => createScriptsByAi().catch(err => { $('scriptsStatus').textContent = err.message; $('createScriptsAiBtn').disabled = false; }));
$('saveScriptsBtn').addEventListener('click', () => saveScriptsEdits().catch(err => { $('scriptsStatus').textContent = err.message; }));
$('scriptsNextBtn').addEventListener('click', () => saveScriptsAndNext().catch(err => { $('scriptsStatus').textContent = err.message; }));
$('finalizeWorkflowBtn').addEventListener('click', () => finalizeWorkflow());
$('finalAuditBtn').addEventListener('click', () => openAuditTrail().catch(err => { $('finalizeStatus').textContent = err.message; }));
refreshRules().catch(() => {});
</script>
</body>
</html>
"""
