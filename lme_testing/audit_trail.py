from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from .storage import load_json, load_jsonl


def _safe_load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return load_json(path)


def _safe_load_jsonl(path: Path | None) -> list[dict]:
    if not path or not path.exists():
        return []
    return load_jsonl(path)


def _review_decision_for_checker(checker_review: dict[str, Any]) -> str:
    return "rewrite" if checker_review.get("checker_blocking") or checker_review.get("is_blocking") else "approve"


def _find_latest_human_reviews(iteration_state: dict[str, Any]) -> Path | None:
    latest = iteration_state.get("human_reviews_latest_path")
    if latest and Path(latest).exists():
        return Path(latest)
    return None


def _audit_rows(session_dir: Path) -> tuple[list[str], int]:
    manifest = _safe_load_json(session_dir / "session_manifest.json")
    iterations = manifest.get("iterations", {}) if isinstance(manifest, dict) else {}
    rows: list[str] = []
    divergent_count = 0

    for iteration_key in sorted(iterations, key=lambda value: int(value)):
        iteration_state = iterations[iteration_key]
        checker_reviews = {
            item.get("case_id"): item
            for item in _safe_load_jsonl(Path(iteration_state.get("checker_reviews_path", "")))
            if item.get("case_id")
        }
        human_path = _find_latest_human_reviews(iteration_state)
        human_payload = _safe_load_json(human_path) if human_path else {}
        human_reviews = human_payload.get("reviews", []) if isinstance(human_payload, dict) else []

        for review in human_reviews:
            case_id = review.get("case_id", "")
            checker = checker_reviews.get(case_id, {})
            checker_decision = _review_decision_for_checker(checker)
            human_decision = review.get("review_decision", "")
            divergent = bool(checker) and human_decision in {"approve", "rewrite"} and checker_decision != human_decision
            if not divergent:
                continue
            divergent_count += 1
            rows.append(
                "<tr>"
                f"<td>{html.escape(str(iteration_key))}</td>"
                f"<td>{html.escape(str(review.get('semantic_rule_id', '')))}</td>"
                f"<td>{html.escape(str(case_id))}</td>"
                f"<td>{html.escape(str(checker.get('overall_status', 'missing')))}</td>"
                f"<td>{html.escape(str(checker.get('checker_blocking', checker.get('is_blocking', 'missing'))))}</td>"
                f"<td>{html.escape(checker_decision if checker else 'missing')}</td>"
                f"<td>{html.escape(str(human_decision))}</td>"
                f"<td>{html.escape(str(review.get('human_comment', '')))}</td>"
                "</tr>"
            )
    return rows, divergent_count


def build_audit_trail(session_dir: Path, output_html_path: Path) -> dict[str, Any]:
    """Build an HTML audit trail for human/checker decisions across a review session."""
    rows, divergent_count = _audit_rows(session_dir)
    output_html_path.parent.mkdir(parents=True, exist_ok=True)
    output_html_path.write_text(
        f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>Audit Trail</title>
  <style>
    body {{ font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif; margin: 24px; color: #1f2937; background: #f8fafc; }}
    h1 {{ color: #0f172a; }}
    .card {{ background: white; border: 1px solid #cbd5e1; border-radius: 12px; padding: 16px 20px; margin-bottom: 20px; }}
    table {{ width: 100%; border-collapse: collapse; background: white; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 10px; vertical-align: top; text-align: left; font-size: 13px; }}
    th {{ background: #e2e8f0; }}
  </style>
</head>
<body>
  <h1>Audit Trail</h1>
  <div class="card">
    <div><strong>Session Dir</strong>: {html.escape(str(session_dir))}</div>
    <div><strong>Decision Divergences</strong>: {divergent_count}</div>
    <div>Only cases where human Decision conflicts with the checker implied decision are listed.</div>
  </div>
  <table>
    <thead>
      <tr>
        <th>Iteration</th><th>Semantic Rule</th><th>Case ID</th><th>Checker Overall</th>
        <th>Checker Blocking</th><th>Checker Implied Decision</th><th>Human Decision</th>
        <th>Human Comment</th>
      </tr>
    </thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</body>
</html>
""",
        encoding="utf-8",
    )
    return {
        "output_html": str(output_html_path),
        "row_count": len(rows),
        "divergent_count": divergent_count,
    }
