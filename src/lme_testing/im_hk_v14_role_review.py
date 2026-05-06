from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .storage import atomic_write_json, ensure_dir, load_json, timestamp_slug


ALLOWED_REVIEWER_ROLES = {
    "BA",
    "QA Lead",
    "Automation Lead",
    "PM / Release Owner",
}

ALLOWED_DECISIONS = {
    "approve",
    "reject",
    "defer",
    "request_rework",
}

ALLOWED_STATUSES = {
    "pending",
    "recorded",
}


class RoleReviewValidationError(ValueError):
    """Raised when an HKv14 role review decision record violates its contract."""


@dataclass(frozen=True)
class CandidateMapping:
    treatment_category: str
    downstream_action: str


def _anchor_text(anchor: dict[str, Any]) -> str:
    paragraph_id = anchor.get("paragraph_id") or ""
    clause_id = anchor.get("clause_id") or ""
    start_page = anchor.get("start_page")
    end_page = anchor.get("end_page")
    page_text = f"p.{start_page}" if start_page == end_page else f"p.{start_page}-{end_page}"
    parts = [part for part in [paragraph_id, clause_id, page_text] if part]
    return " / ".join(parts)


def _candidate_key(candidate: dict[str, Any]) -> str:
    if "rule_id" in candidate:
        return str(candidate["rule_id"])
    return f"{candidate.get('previous_rule_id')} -> {candidate.get('current_rule_id')}"


def _normalize_candidate_id(candidate_id: str) -> str:
    return re.sub(r"\s*(?:->|→)\s*", " -> ", candidate_id.strip())


def parse_treatment_mapping(markdown_text: str) -> dict[str, CandidateMapping]:
    mapping: dict[str, CandidateMapping] = {}
    for raw_line in markdown_text.splitlines():
        line = raw_line.strip()
        if not line.startswith("| `"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 4 or cells[0] == "Candidate":
            continue
        candidate = _normalize_candidate_id(cells[0].replace("`", ""))
        treatment_match = re.search(r"`([^`]+)`", cells[2])
        treatment = treatment_match.group(1) if treatment_match else cells[2]
        mapping[candidate] = CandidateMapping(
            treatment_category=treatment,
            downstream_action=cells[3],
        )
    return mapping


def load_review_candidates(diff_report: dict[str, Any], mapping_markdown: str) -> list[dict[str, Any]]:
    treatment_mapping = parse_treatment_mapping(mapping_markdown)
    rule_delta = diff_report.get("rule_delta", {})
    candidates: list[dict[str, Any]] = []

    for item in rule_delta.get("changed_rule_candidates", []):
        candidate_id = _candidate_key(item)
        mapping = treatment_mapping.get(_normalize_candidate_id(candidate_id))
        candidates.append(
            {
                "candidate_id": candidate_id,
                "candidate_type": "changed_rule",
                "source_rule_id": item.get("rule_id"),
                "target_rule_id": item.get("rule_id"),
                "source_anchor": _anchor_text(item.get("current_anchor") or item.get("previous_anchor") or {}),
                "similarity": item.get("similarity"),
                "treatment_category": mapping.treatment_category if mapping else "unmapped",
                "downstream_action": mapping.downstream_action if mapping else "",
                "diff_summary": _summarize_changed_candidate(item),
            }
        )

    for item in rule_delta.get("id_drift_candidates", []):
        candidate_id = _candidate_key(item)
        mapping = treatment_mapping.get(_normalize_candidate_id(candidate_id))
        candidates.append(
            {
                "candidate_id": candidate_id,
                "candidate_type": "id_drift",
                "source_rule_id": item.get("previous_rule_id"),
                "target_rule_id": item.get("current_rule_id"),
                "source_anchor": _anchor_text(item.get("current_anchor") or item.get("previous_anchor") or {}),
                "similarity": item.get("similarity"),
                "treatment_category": mapping.treatment_category if mapping else "unmapped",
                "downstream_action": mapping.downstream_action if mapping else "",
                "diff_summary": "Rule text appears unchanged but the rule id drifted between versions.",
            }
        )

    return candidates


def _summarize_changed_candidate(item: dict[str, Any]) -> str:
    previous_type = item.get("previous_rule_type")
    current_type = item.get("current_rule_type")
    if previous_type and current_type and previous_type != current_type:
        return f"Rule type changed from {previous_type} to {current_type}."
    return "Rule text changed between HKv13 and HKv14."


def build_decision_record(
    *,
    diff_report_path: Path,
    mapping_path: Path,
    reviewer_role: str = "BA",
    reviewer_name: str = "",
    decision: str = "defer",
    rationale: str = "",
    comments: str = "",
    review_timestamp: str | None = None,
) -> dict[str, Any]:
    diff_report = load_json(diff_report_path)
    if not isinstance(diff_report, dict):
        raise RoleReviewValidationError("Diff report must be a JSON object.")
    mapping_markdown = mapping_path.read_text(encoding="utf-8")
    timestamp = review_timestamp or timestamp_slug()
    candidates = load_review_candidates(diff_report, mapping_markdown)

    candidate_decisions = []
    for candidate in candidates:
        candidate_decisions.append(
            {
                **candidate,
                "reviewer_role": reviewer_role,
                "reviewer_name": reviewer_name,
                "decision": decision,
                "rationale": rationale,
                "comments": comments,
                "review_timestamp": timestamp,
                "status": "pending" if not reviewer_name or not rationale else "recorded",
            }
        )

    record = {
        "metadata": {
            "task_id": "S2-F1",
            "record_type": "im_hk_v14_role_review_decision_record",
            "generated_at": timestamp,
            "review_scope": "Initial Margin HKv13 -> HKv14 role-friendly impact decision review",
            "canonical": True,
        },
        "source_evidence": {
            "diff_report_path": str(diff_report_path),
            "mapping_path": str(mapping_path),
            "previous_doc_id": diff_report.get("source_versions", {}).get("previous", {}).get("doc_id"),
            "current_doc_id": diff_report.get("source_versions", {}).get("current", {}).get("doc_id"),
        },
        "review_scope": {
            "allowed_reviewer_roles": sorted(ALLOWED_REVIEWER_ROLES),
            "allowed_decisions": sorted(ALLOWED_DECISIONS),
            "candidate_count": len(candidate_decisions),
        },
        "candidate_decisions": candidate_decisions,
        "open_items": [
            item["candidate_id"]
            for item in candidate_decisions
            if item["decision"] in {"defer", "request_rework"} or item["status"] == "pending"
        ],
        "summary": summarize_record(candidate_decisions),
    }
    validate_decision_record(record)
    return record


def summarize_record(candidate_decisions: list[dict[str, Any]]) -> dict[str, Any]:
    by_decision: dict[str, int] = {decision: 0 for decision in sorted(ALLOWED_DECISIONS)}
    by_status: dict[str, int] = {status: 0 for status in sorted(ALLOWED_STATUSES)}
    by_treatment: dict[str, int] = {}
    for item in candidate_decisions:
        by_decision[item["decision"]] = by_decision.get(item["decision"], 0) + 1
        by_status[item["status"]] = by_status.get(item["status"], 0) + 1
        treatment = item.get("treatment_category") or "unknown"
        by_treatment[treatment] = by_treatment.get(treatment, 0) + 1
    return {
        "candidate_count": len(candidate_decisions),
        "by_decision": by_decision,
        "by_status": by_status,
        "by_treatment_category": dict(sorted(by_treatment.items())),
    }


def validate_decision_record(record: dict[str, Any]) -> None:
    required_top = {"metadata", "source_evidence", "review_scope", "candidate_decisions", "open_items", "summary"}
    missing_top = required_top - set(record)
    if missing_top:
        raise RoleReviewValidationError(f"Decision record missing top-level fields: {sorted(missing_top)}")

    candidate_decisions = record.get("candidate_decisions")
    if not isinstance(candidate_decisions, list) or not candidate_decisions:
        raise RoleReviewValidationError("Decision record must contain at least one candidate decision.")

    seen: set[str] = set()
    required_candidate_fields = {
        "candidate_id",
        "candidate_type",
        "source_rule_id",
        "target_rule_id",
        "source_anchor",
        "treatment_category",
        "reviewer_role",
        "reviewer_name",
        "decision",
        "rationale",
        "comments",
        "review_timestamp",
        "status",
    }
    for index, item in enumerate(candidate_decisions):
        missing = required_candidate_fields - set(item)
        if missing:
            raise RoleReviewValidationError(f"Candidate {index} missing fields: {sorted(missing)}")
        candidate_id = str(item["candidate_id"])
        if candidate_id in seen:
            raise RoleReviewValidationError(f"Duplicate candidate_id: {candidate_id}")
        seen.add(candidate_id)
        if item["reviewer_role"] not in ALLOWED_REVIEWER_ROLES:
            raise RoleReviewValidationError(f"Unsupported reviewer_role for {candidate_id}: {item['reviewer_role']}")
        if item["decision"] not in ALLOWED_DECISIONS:
            raise RoleReviewValidationError(f"Unsupported decision for {candidate_id}: {item['decision']}")
        if item["status"] not in ALLOWED_STATUSES:
            raise RoleReviewValidationError(f"Unsupported status for {candidate_id}: {item['status']}")
        if not item["source_anchor"]:
            raise RoleReviewValidationError(f"Missing source_anchor for {candidate_id}")
        if item["treatment_category"] == "unmapped":
            raise RoleReviewValidationError(f"Missing downstream treatment mapping for {candidate_id}")


def render_markdown_summary(record: dict[str, Any]) -> str:
    validate_decision_record(record)
    metadata = record["metadata"]
    source = record["source_evidence"]
    lines = [
        "# HKv14 Role-Friendly Impact Decision Summary",
        "",
        f"**Task ID:** {metadata['task_id']}",
        f"**Generated at:** {metadata['generated_at']}",
        f"**Diff evidence:** `{source['diff_report_path']}`",
        f"**Treatment mapping:** `{source['mapping_path']}`",
        "",
        "This Markdown summary is derived from `decision_record.json`; the JSON record is canonical.",
        "",
        "## Summary",
        "",
        f"- Candidate count: {record['summary']['candidate_count']}",
        f"- Open items: {len(record['open_items'])}",
        "",
        "## Candidate Decisions",
        "",
        "| Candidate | Type | Treatment | Role | Decision | Status | Source Anchor |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in record["candidate_decisions"]:
        lines.append(
            "| {candidate_id} | {candidate_type} | {treatment_category} | {reviewer_role} | {decision} | {status} | {source_anchor} |".format(
                **{key: _md_cell(str(value)) for key, value in item.items()}
            )
        )
    lines.extend(
        [
            "",
            "## Boundaries",
            "",
            "- HKv14 remains POC/mock/stub downstream baseline candidate work.",
            "- This record does not claim Stage 3 real execution readiness.",
            "- This record does not change schemas, prompts, default models, or HKv13 preservation baseline artifacts.",
            "",
        ]
    )
    return "\n".join(lines)


def _md_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def render_review_html(record: dict[str, Any]) -> str:
    validate_decision_record(record)
    rows = []
    role_options = "".join(f"<option>{html.escape(role)}</option>" for role in sorted(ALLOWED_REVIEWER_ROLES))
    decision_options = "".join(f"<option>{html.escape(decision)}</option>" for decision in sorted(ALLOWED_DECISIONS))
    for item in record["candidate_decisions"]:
        rows.append(
            "<tr>"
            f"<td><code>{html.escape(str(item['candidate_id']))}</code><br>{html.escape(str(item['diff_summary']))}</td>"
            f"<td>{html.escape(str(item['candidate_type']))}</td>"
            f"<td>{html.escape(str(item['treatment_category']))}<br><small>{html.escape(str(item['downstream_action']))}</small></td>"
            f"<td>{html.escape(str(item['source_anchor']))}</td>"
            f"<td><select>{role_options}</select></td>"
            f"<td><input value=\"{html.escape(str(item['reviewer_name']))}\" placeholder=\"Reviewer name\"></td>"
            f"<td><select>{decision_options}</select></td>"
            f"<td><textarea placeholder=\"Decision rationale\">{html.escape(str(item['rationale']))}</textarea></td>"
            "</tr>"
        )
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>HKv14 Impact Decision Review</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #1f2933; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #c7d0d9; padding: 8px; vertical-align: top; }}
    th {{ background: #eef3f7; text-align: left; }}
    textarea {{ min-height: 64px; width: 100%; }}
    input, select {{ width: 100%; box-sizing: border-box; }}
    small {{ color: #52606d; }}
  </style>
</head>
<body>
  <h1>HKv14 Impact Decision Review</h1>
  <p>This local review surface is generated from deterministic HKv13 -> HKv14 evidence. The canonical record is <code>decision_record.json</code>.</p>
  <table>
    <thead>
      <tr>
        <th>Candidate</th><th>Type</th><th>Treatment</th><th>Source Anchor</th>
        <th>Role</th><th>Reviewer</th><th>Decision</th><th>Rationale</th>
      </tr>
    </thead>
    <tbody>
      {rows}
    </tbody>
  </table>
</body>
</html>
""".format(rows="\n".join(rows))


def write_review_package(
    *,
    diff_report_path: Path,
    mapping_path: Path,
    output_dir: Path,
    reviewer_role: str = "BA",
    reviewer_name: str = "",
    decision: str = "defer",
    rationale: str = "",
    comments: str = "",
) -> dict[str, Any]:
    run_dir = ensure_dir(output_dir / timestamp_slug())
    record = build_decision_record(
        diff_report_path=diff_report_path,
        mapping_path=mapping_path,
        reviewer_role=reviewer_role,
        reviewer_name=reviewer_name,
        decision=decision,
        rationale=rationale,
        comments=comments,
    )
    record_path = run_dir / "decision_record.json"
    summary_path = run_dir / "decision_summary.md"
    html_path = run_dir / "review.html"
    atomic_write_json(record_path, record)
    summary_path.write_text(render_markdown_summary(record), encoding="utf-8")
    html_path.write_text(render_review_html(record), encoding="utf-8")
    return {
        "run_dir": str(run_dir),
        "decision_record": str(record_path),
        "decision_summary": str(summary_path),
        "review_html": str(html_path),
        "candidate_count": len(record["candidate_decisions"]),
        "open_item_count": len(record["open_items"]),
    }
