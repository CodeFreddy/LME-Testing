from __future__ import annotations

import html
from pathlib import Path

from .storage import load_json, load_jsonl


def _is_divergent(checker: dict, human: dict) -> bool:
    # Disagreement rule (agreed with user):
    # - checker "negative" (blocking OR overall=fail OR coverage=uncovered) AND human approve  → divergent
    # - checker "positive" (not blocking AND overall=pass AND coverage=covered) AND human rewrite → divergent
    # - human decision == pending is treated as "unscored" and never divergent.
    decision = human.get("review_decision", "")
    if decision == "pending":
        return False
    checker_blocking = bool(checker.get("checker_blocking") or checker.get("is_blocking"))
    overall = checker.get("overall_status", "")
    coverage = checker.get("coverage_assessment", {}).get("status", "")
    checker_negative = checker_blocking or overall == "fail" or coverage == "uncovered"
    if checker_negative and decision == "approve":
        return True
    checker_positive = (not checker_blocking) and overall == "pass" and coverage == "covered"
    if checker_positive and decision == "rewrite":
        return True
    return False


def _summarize_checker(checker: dict) -> str:
    parts: list[str] = []
    parts.append(f"overall={checker.get('overall_status', '')}")
    parts.append(f"coverage={checker.get('coverage_assessment', {}).get('status', '')}")
    parts.append(f"blocking={bool(checker.get('checker_blocking') or checker.get('is_blocking'))}")
    category = checker.get("checker_blocking_category") or checker.get("blocking_category")
    if category and category != "none":
        parts.append(f"category={category}")
    reason = checker.get("checker_blocking_reason") or checker.get("blocking_reason")
    if reason:
        parts.append(f"reason={reason}")
    return " · ".join(parts)


def build_audit_trail(session_dir: Path, output_html_path: Path) -> dict:
    """Scan all iterations in session_dir, extract checker/human divergences, write audit_trail.html."""
    iterations_dir = session_dir / "iterations"
    divergent_rows: list[dict] = []

    if iterations_dir.exists():
        for iter_dir in sorted(iterations_dir.iterdir()):
            if not iter_dir.is_dir():
                continue
            try:
                iteration = int(iter_dir.name)
            except ValueError:
                continue

            checker_path = None
            for candidate in iter_dir.rglob("checker_reviews.jsonl"):
                checker_path = candidate
                break
            human_path = iter_dir / "reviews" / "human_reviews_latest.json"
            if not checker_path or not human_path.exists():
                continue

            checker_reviews_list = load_jsonl(checker_path)
            human_payload = load_json(human_path)
            checker_by_case = {r.get("case_id"): r for r in checker_reviews_list}
            for human_review in human_payload.get("reviews", []):
                case_id = human_review.get("case_id", "")
                checker = checker_by_case.get(case_id, {})
                if _is_divergent(checker, human_review):
                    divergent_rows.append({
                        "iteration": iteration,
                        "rule_id": human_review.get("semantic_rule_id", ""),
                        "case_id": case_id,
                        "checker_summary": _summarize_checker(checker),
                        "human_decision": human_review.get("review_decision", ""),
                        "human_comment": human_review.get("human_comment", ""),
                        "issue_types": human_review.get("issue_types", []),
                    })

    rows_html = ""
    for row in divergent_rows:
        issue_types_str = ", ".join(str(t) for t in row["issue_types"]) if row["issue_types"] else ""
        rows_html += (
            f"<tr>"
            f"<td>{html.escape(str(row['iteration']))}</td>"
            f"<td>{html.escape(str(row['rule_id']))}</td>"
            f"<td>{html.escape(str(row['case_id']))}</td>"
            f"<td>{html.escape(str(row['checker_summary']))}</td>"
            f"<td>{html.escape(str(row['human_decision']))}</td>"
            f"<td>{html.escape(str(row['human_comment']))}</td>"
            f"<td>{html.escape(issue_types_str)}</td>"
            f"</tr>"
        )

    body = f"""
<h1>Audit Trail — Checker / Human 分歧记录</h1>
<div class="card">
  <p>仅展示 checker 与 human 意见不一致的 case。共 <strong>{len(divergent_rows)}</strong> 条分歧。</p>
  <p class="muted">分歧口径：① checker 判定负向（blocking / overall=fail / coverage=uncovered）但人工 approve；② checker 判定正向（非 blocking 且 overall=pass 且 coverage=covered）但人工 rewrite。<code>pending</code> 视为未审核，不计入分歧。</p>
  <table>
    <thead>
      <tr>
        <th>Iteration</th>
        <th>Rule ID</th>
        <th>Case ID</th>
        <th>Checker Summary</th>
        <th>Human Decision</th>
        <th>Comment</th>
        <th>Issue Types</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>
</div>
"""

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>Audit Trail</title>
  <style>
    body {{ font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif; margin: 24px; color: #1f2937; background: #f8fafc; }}
    h1 {{ color: #0f172a; }}
    .card {{ background: white; border: 1px solid #cbd5e1; border-radius: 12px; padding: 16px 20px; margin-bottom: 20px; box-shadow: 0 6px 18px rgba(15,23,42,0.06); }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 8px 10px; vertical-align: top; text-align: left; font-size: 13px; }}
    th {{ background: #e2e8f0; }}
    .muted {{ color: #64748b; font-size: 12px; }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""
    output_html_path.parent.mkdir(parents=True, exist_ok=True)
    output_html_path.write_text(page, encoding="utf-8")
    return {"divergent_count": len(divergent_rows), "output_html": str(output_html_path)}
