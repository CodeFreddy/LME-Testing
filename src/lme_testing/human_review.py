from __future__ import annotations

import html
import json
from pathlib import Path

from .schemas import load_issue_type_options
from .storage import load_jsonl


# Generate a minimal local human review page.
def generate_human_review_page(
    maker_cases_path: Path,
    checker_reviews_path: Path,
    output_html_path: Path,
) -> dict:
    maker_cases = load_jsonl(maker_cases_path)
    checker_reviews = load_jsonl(checker_reviews_path)
    reviews_by_case = {item["case_id"]: item for item in checker_reviews}
    issue_type_options = load_issue_type_options()

    rows: list[str] = []
    page_seed_reviews: list[dict] = []
    total_cases = 0
    checker_blocked = 0

    for maker_record in maker_cases:
        semantic_rule_id = maker_record.get("semantic_rule_id", "")
        feature = maker_record.get("feature", "")
        for scenario in maker_record.get("scenarios", []):
            total_cases += 1
            case_id = scenario.get("scenario_id", "")
            checker = reviews_by_case.get(case_id, {})
            checker_blocking = checker.get("checker_blocking") is True or checker.get("is_blocking") is True
            if checker_blocking:
                checker_blocked += 1

            seed = {
                "case_id": case_id,
                "semantic_rule_id": semantic_rule_id,
                "review_decision": "pending",
                "block_recommendation_review": "pending_review" if checker_blocking else "not_applicable",
                "human_comment": "",
                "issue_types": [],
            }
            page_seed_reviews.append(seed)

            rows.append(
                f'<tr data-case-id="{html.escape(case_id)}" data-overall="{html.escape(str(checker.get("overall_status", "missing")))}" '
                f'data-coverage="{html.escape(str(checker.get("coverage_assessment", {}).get("status", "missing")))}" '
                f'data-blocking="{html.escape(str(checker_blocking).lower())}">'
                f'<td>{html.escape(semantic_rule_id)}</td>'
                f'<td>{html.escape(case_id)}</td>'
                f'<td>{html.escape(feature)}</td>'
                f'<td>{html.escape(str(scenario.get("case_type", "")))}</td>'
                f'<td>{html.escape(str(checker.get("overall_status", "missing")))}</td>'
                f'<td>{html.escape(str(checker.get("coverage_assessment", {}).get("status", "missing")))}</td>'
                f'<td>{html.escape(str(checker_blocking))}</td>'
                f'<td>{html.escape(str(checker.get("checker_blocking_category", checker.get("blocking_category", "none"))))}</td>'
                f'<td>{html.escape(str(checker.get("checker_blocking_reason", checker.get("blocking_reason", ""))))}</td>'
                f'<td><details><summary>Details</summary>{_render_case_detail(scenario, checker)}</details></td>'
                f'<td>{_render_review_controls(seed, issue_type_options)}</td>'
                '</tr>'
            )

    page_data = {
        "metadata": {
            "maker_cases_path": str(maker_cases_path),
            "checker_reviews_path": str(checker_reviews_path),
            "total_cases": total_cases,
        },
        "reviews": page_seed_reviews,
        "issue_type_options": issue_type_options,
    }

    page_html = _render_page(
        rows="".join(rows),
        seed_json=json.dumps(page_data, ensure_ascii=False),
        total_cases=total_cases,
        checker_blocked=checker_blocked,
        issue_type_options=issue_type_options,
    )
    output_html_path.parent.mkdir(parents=True, exist_ok=True)
    output_html_path.write_text(page_html, encoding="utf-8")
    return {
        "output_html": str(output_html_path),
        "total_cases": total_cases,
        "checker_blocked_count": checker_blocked,
    }


def _render_case_detail(scenario: dict, checker: dict) -> str:
    evidence = "".join(
        f'<div><strong>{html.escape(str(item.get("atomic_rule_id", "")))}</strong>: {html.escape(str(item.get("quote", "")))}</div>'
        for item in scenario.get("evidence", [])
    ) or "&nbsp;"
    findings = "".join(
        html.escape(str(item)) if isinstance(item, str) else f'<div><strong>{html.escape(str(item.get("category", "")))}</strong>: {html.escape(str(item.get("summary", "")))}</div>'
        for item in checker.get("findings", [])
    ) or "&nbsp;"
    return (
        f'<div><strong>Given</strong>{_list_html(scenario.get("given", []))}</div>'
        f'<div><strong>When</strong>{_list_html(scenario.get("when", []))}</div>'
        f'<div><strong>Then</strong>{_list_html(scenario.get("then", []))}</div>'
        f'<div><strong>Assumptions</strong>{_list_html(scenario.get("assumptions", []))}</div>'
        f'<div><strong>Evidence</strong>{evidence}</div>'
        f'<div><strong>Checker Findings</strong>{findings}</div>'
        f'<div><strong>Coverage Reason</strong>: {html.escape(str(checker.get("coverage_assessment", {}).get("reason", "")))}</div>'
    )


def _list_html(items: list[str]) -> str:
    if not items:
        return "&nbsp;"
    return "<ul>" + "".join(f'<li>{html.escape(str(item))}</li>' for item in items) + "</ul>"


def _issue_summary(seed: dict, issue_type_options: list[dict]) -> str:
    selected = set(seed.get("issue_types", []))
    labels = [item["label"] for item in issue_type_options if item["code"] in selected]
    return ", ".join(labels) if labels else "None selected"


def _issue_type_rows_html(seed: dict, issue_type_options: list[dict]) -> str:
    selected = set(seed.get("issue_types", []))
    rows: list[str] = []
    for item in issue_type_options:
        rows.append(
            '<tr>'
            f'<td><input type="checkbox" data-field="issue_type_option" data-case-id="{html.escape(seed["case_id"])}" data-issue-code="{html.escape(item["code"])}"{" checked" if item["code"] in selected else ""} /></td>'
            f'<td>{html.escape(item["label"])}</td>'
            f'<td>{html.escape(item["code"])}</td>'
            f'<td>{html.escape(item["description"])}</td>'
            '</tr>'
        )
    return "".join(rows)


def _render_review_controls(seed: dict, issue_type_options: list[dict]) -> str:
    case_id = html.escape(seed["case_id"])
    block_review = seed["block_recommendation_review"]
    return (
        f'<div><label>Decision<br/><select data-field="review_decision" data-case-id="{case_id}">'
        '<option value="pending" selected>pending</option>'
        '<option value="approve">approve</option>'
        '<option value="rewrite">rewrite</option>'
        '<option value="reject">reject</option>'
        '</select></label></div>'
        f'<div><label>Block Recommendation Review<br/><select data-field="block_recommendation_review" data-case-id="{case_id}">'
        f'<option value="not_applicable"{" selected" if block_review == "not_applicable" else ""}>not_applicable</option>'
        f'<option value="pending_review"{" selected" if block_review == "pending_review" else ""}>pending_review</option>'
        '<option value="confirmed">confirmed</option>'
        '<option value="dismissed">dismissed</option>'
        '</select></label></div>'
        f'<div><label>Issue Types</label><details class="issue-picker"><summary class="issue-summary" data-issue-summary="{case_id}">{html.escape(_issue_summary(seed, issue_type_options))}</summary><table class="issue-table"><thead><tr><th>Select</th><th>Label</th><th>Code</th><th>Description</th></tr></thead><tbody>{_issue_type_rows_html(seed, issue_type_options)}</tbody></table></details></div>'
        f'<div><label>Comment<br/><textarea data-field="human_comment" data-case-id="{case_id}" rows="4" cols="36"></textarea></label></div>'
    )


def _render_page(rows: str, seed_json: str, total_cases: int, checker_blocked: int, issue_type_options: list[dict]) -> str:
    issue_legend = "".join(
        f'<li><strong>{html.escape(item["code"])}:</strong> {html.escape(item["label"])} - {html.escape(item["description"])}<li>'
        for item in issue_type_options
    )
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Human Review</title>
  <style>
    body {{ font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif; margin: 24px; color: #1f2937; background: #f8fafc; }}
    h1, h2 {{ color: #0f172a; }}
    .card {{ background: white; border: 1px solid #cbd5e1; border-radius: 12px; padding: 16px 20px; margin-bottom: 20px; box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06); }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(220px, 1fr)); gap: 12px; }}
    .metric {{ background: #eff6ff; border-radius: 10px; padding: 12px; border: 1px solid #bfdbfe; }}
    .toolbar {{ display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }}
    table {{ width: 100%; border-collapse: collapse; background: white; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 10px; vertical-align: top; text-align: left; font-size: 13px; }}
    th {{ background: #e2e8f0; }}
    details {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 10px; }}
    summary {{ cursor: pointer; font-weight: 600; }}
    textarea, select {{ width: 100%; box-sizing: border-box; margin-top: 4px; }}
    .issue-picker {{ margin-top: 4px; border: 1px solid #cbd5e1; border-radius: 8px; background: #f8fafc; }}
    .issue-picker summary {{ list-style: none; }}
    .issue-picker[open] summary {{ margin-bottom: 8px; }}
    .issue-summary {{ color: #334155; font-size: 12px; }}
    .issue-table {{ width: 100%; border-collapse: collapse; background: white; }}
    .issue-table th, .issue-table td {{ border: 1px solid #e2e8f0; padding: 6px 8px; font-size: 12px; }}
    .issue-table th {{ background: #f1f5f9; }}
    .muted {{ color: #64748b; font-size: 12px; }}
    .warning {{ color: #92400e; background: #fffbeb; border: 1px solid #fcd34d; border-radius: 8px; padding: 8px 10px; margin-top: 8px; }}
    button {{ padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 8px; background: white; cursor: pointer; }}
    ul {{ margin: 8px 0 0 18px; }}
  </style>
</head>
<body>
  <h1>Human Review</h1>
  <div class="card">
    <div class="grid">
      <div class="metric"><strong>Total Cases</strong><br/>{total_cases}</div>
      <div class="metric"><strong>Checker Blocking Suggestions</strong><br/>{checker_blocked}</div>
    </div>
  </div>
  <div class="card">
    <h2>Field Guide</h2>
    <ul>
      <li><strong>Decision</strong>: final human action. If it is not <code>pending</code>, the system executes this action.</li>
      <li><strong>Block Recommendation Review</strong>: human review of the checker blocking recommendation. It is used for audit only and does not override <code>Decision</code>.</li>
      <li><strong>Issue Types</strong>: open the panel and select one or more checkboxes. These tags are used for stats and targeted rewrite guidance.</li>
    </ul>
    <div class="warning">If <code>Decision</code> is already set to <code>approve</code>, <code>rewrite</code>, or <code>reject</code>, the system follows that decision even if <code>Block Recommendation Review</code> is still <code>pending_review</code>.</div>
  </div>
  <div class="card">
    <h2>Issue Type Reference</h2>
    <ul>{issue_legend}</ul>
  </div>
  <div class="card">
    <div class="toolbar">
      <label>Overall <select id="overallFilter"><option value="">All</option><option value="pass">pass</option><option value="fail">fail</option><option value="missing">missing</option></select></label>
      <label>Coverage <select id="coverageFilter"><option value="">All</option><option value="covered">covered</option><option value="partial">partial</option><option value="uncovered">uncovered</option><option value="missing">missing</option></select></label>
      <label>Checker Blocking <select id="blockingFilter"><option value="">All</option><option value="true">true</option><option value="false">false</option></select></label>
      <button id="saveBtn">Download JSON</button>
      <label><button type="button" id="loadBtn">Import JSON</button><input id="loadInput" type="file" accept="application/json" style="display:none" /></label>
    </div>
    <div class="muted">This page is static. Download the resulting JSON and pass it to the rewrite command.</div>
  </div>
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
      <tbody id="reviewRows">{rows}</tbody>
    </table>
  </div>
<script>
const reviewState = {seed_json};
const reviewMap = new Map(reviewState.reviews.map(item => [item.case_id, item]));
const rows = Array.from(document.querySelectorAll('#reviewRows tr'));
const issueTypeOptions = reviewState.issue_type_options || [];

function syncIssueSummary(caseId) {{
  const review = reviewMap.get(caseId);
  const summaryEl = document.querySelector(`[data-issue-summary="${{caseId}}"]`);
  if (!review || !summaryEl) return;
  const labels = (review.issue_types || [])
    .map(code => issueTypeOptions.find(item => item.code === code))
    .filter(Boolean)
    .map(item => item.label);
  summaryEl.textContent = labels.length ? labels.join(', ') : 'None selected';
}}

function syncField(el) {{
  const caseId = el.dataset.caseId;
  const field = el.dataset.field;
  const review = reviewMap.get(caseId);
  if (!review) return;
  if (field === 'issue_type_option') {{
    const selected = new Set(review.issue_types || []);
    const issueCode = el.dataset.issueCode;
    if (el.checked) selected.add(issueCode); else selected.delete(issueCode);
    review.issue_types = Array.from(selected);
    syncIssueSummary(caseId);
  }} else {{
    review[field] = el.value;
  }}
}}

for (const el of document.querySelectorAll('[data-field]')) {{
  el.addEventListener('change', () => syncField(el));
  el.addEventListener('input', () => syncField(el));
}}
for (const review of reviewMap.values()) syncIssueSummary(review.case_id);

function applyFilters() {{
  const overall = document.getElementById('overallFilter').value;
  const coverage = document.getElementById('coverageFilter').value;
  const blocking = document.getElementById('blockingFilter').value;
  for (const row of rows) {{
    const show = (!overall || row.dataset.overall === overall) && (!coverage || row.dataset.coverage === coverage) && (!blocking || row.dataset.blocking === blocking);
    row.style.display = show ? '' : 'none';
  }}
}}

document.getElementById('overallFilter').addEventListener('change', applyFilters);
document.getElementById('coverageFilter').addEventListener('change', applyFilters);
document.getElementById('blockingFilter').addEventListener('change', applyFilters);

function downloadReviews() {{
  const payload = {{ metadata: reviewState.metadata, reviews: Array.from(reviewMap.values()) }};
  const blob = new Blob([JSON.stringify(payload, null, 2)], {{ type: 'application/json' }});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'human_reviews.json';
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}}

document.getElementById('saveBtn').addEventListener('click', downloadReviews);
document.getElementById('loadBtn').addEventListener('click', () => document.getElementById('loadInput').click());
document.getElementById('loadInput').addEventListener('change', async (event) => {{
  const file = event.target.files[0];
  if (!file) return;
  const text = await file.text();
  const payload = JSON.parse(text);
  for (const item of (payload.reviews || [])) {{
    const normalized = {{
      ...item,
      review_decision: item.review_decision === 'approved' ? 'approve' : item.review_decision === 'needs_rewrite' ? 'rewrite' : item.review_decision === 'rejected' ? 'reject' : item.review_decision,
      block_recommendation_review: item.block_recommendation_review || (item.human_block_decision === 'not_requested' ? 'not_applicable' : item.human_block_decision === 'pending' ? 'pending_review' : item.human_block_decision === 'confirmed' ? 'confirmed' : item.human_block_decision ? 'dismissed' : 'not_applicable')
    }};
    reviewMap.set(normalized.case_id, normalized);
    for (const el of document.querySelectorAll(`[data-case-id="${{normalized.case_id}}"]`)) {{
      const field = el.dataset.field;
      if (!field) continue;
      if (field === 'issue_type_option') el.checked = (normalized.issue_types || []).includes(el.dataset.issueCode);
      else el.value = normalized[field] ?? '';
    }}
    syncIssueSummary(normalized.case_id);
  }}
}});
</script>
</body>
</html>
"""
