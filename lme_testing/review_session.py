
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
            "history": [],
            "iterations": {},
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
        self._save_manifest(state)
        logger.info("Saved human reviews. session_id=%s iteration=%s saved=%s latest=%s review_count=%s", state["session_id"], iteration, snapshot_path, latest_path, len(normalized.get("reviews", [])))
        return {
            "iteration": iteration,
            "saved_review_path": str(snapshot_path),
            "latest_review_path": str(latest_path),
            "review_count": len(normalized.get("reviews", [])),
        }

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
  </style>
</head>
<body>
  <h1>Review Session</h1>
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
<script>
let sessionPayload = null;
let reviewMap = new Map();
let pollTimer = null;
function escapeHtml(value) { return String(value ?? '').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;'); }
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
async function refreshSession() { const response = await fetch('/api/session'); sessionPayload = await response.json(); reviewMap = new Map(sessionPayload.reviews.map(item => [item.case_id, item])); document.getElementById('summaryCard').innerHTML = `<div class="grid"><div class="metric"><strong>Session ID</strong><br/>${escapeHtml(sessionPayload.session_id)}</div><div class="metric"><strong>Status</strong><br/>${escapeHtml(sessionPayload.session_status)}</div><div class="metric"><strong>Current Iteration</strong><br/>${escapeHtml(String(sessionPayload.current_iteration))}</div></div><div class="muted">Latest review path: ${escapeHtml(sessionPayload.metadata.latest_review_path || '')}</div><div class="muted">Current report path: ${escapeHtml(sessionPayload.metadata.current_report_path || '')}</div>`; renderRows(); renderHistory(); applyFilters(); }
async function pollJob(jobId) { const response = await fetch(`/api/status/${jobId}`); const payload = await response.json(); if (payload.status === 'queued' || payload.status === 'running') { renderResult('后台执行中', `<div class="status-running">状态: ${escapeHtml(payload.status)}</div>`, 'status-running'); pollTimer = setTimeout(() => pollJob(jobId), 2000); return; } if (payload.status === 'failed') { renderResult('执行失败', `<pre>${escapeHtml(payload.error || '')}</pre>`, 'status-failed'); return; } const result = payload.result || {}; await refreshSession(); renderResult('执行成功', `<div class="status-succeeded">状态: ${escapeHtml(payload.status)}</div><div><strong>Next Iteration</strong>: ${escapeHtml(String(result.next_iteration || ''))}</div><pre>${escapeHtml(JSON.stringify({ rewrite_summary: result.rewrite_summary, checker_summary: result.checker_summary, report_summary: result.report_summary }, null, 2))}</pre><div>${resultLinksHtml(result.links)}</div>`, 'status-succeeded'); }
async function submitAndRun() { if (pollTimer) clearTimeout(pollTimer); const result = await postJson('/api/submit', currentPayload()); renderResult('已提交', `<div>Job ID: ${escapeHtml(result.job_id)}</div><div>Latest: ${escapeHtml(result.latest_review_path)}</div>`); pollJob(result.job_id); }
async function finalizeSession() { const result = await postJson('/api/finalize', {}); if (result.final_report_url) { window.location.href = result.final_report_url; return; } await refreshSession(); renderResult('Session Finalized', `<div class="status-finalized">??: ${escapeHtml(result.status)}</div><div><strong>Final Report</strong>: ${escapeHtml(result.final_report_path || "")}</div><div>${resultLinksHtml({ report_html: result.final_report_url, maker_html: result.final_maker_url, checker_html: result.final_checker_url })}</div>`, 'status-finalized'); }
async function bootstrap() { await refreshSession(); document.getElementById('overallFilter').addEventListener('change', applyFilters); document.getElementById('coverageFilter').addEventListener('change', applyFilters); document.getElementById('blockingFilter').addEventListener('change', applyFilters); document.getElementById('saveBtn').addEventListener('click', saveDraft); document.getElementById('submitBtn').addEventListener('click', submitAndRun); document.getElementById('finalizeBtn').addEventListener('click', finalizeSession); }
bootstrap();
</script>
</body>
</html>
"""
