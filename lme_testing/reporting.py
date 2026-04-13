from __future__ import annotations

import csv
import html
import io
import json
from pathlib import Path

from .storage import load_json, load_jsonl


def _status_options(values: list[str]) -> str:
    options = ['<option value="">全部</option>']
    for value in sorted({value for value in values if value}):
        options.append(f'<option value="{html.escape(value)}">{html.escape(value)}</option>')
    return ''.join(options)


def _render_page(title: str, body: str, extra_script: str = "") -> str:
    return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif; margin: 24px; color: #1f2937; background: #f8fafc; }}
    h1, h2 {{ color: #0f172a; }}
    .card {{ background: white; border: 1px solid #cbd5e1; border-radius: 12px; padding: 16px 20px; margin-bottom: 20px; box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06); }}
    table {{ width: 100%; border-collapse: collapse; background: white; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 10px; vertical-align: top; text-align: left; font-size: 13px; }}
    th {{ background: #e2e8f0; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 12px; }}
    .metric {{ background: #eff6ff; border-radius: 10px; padding: 12px; border: 1px solid #bfdbfe; }}
    .toolbar {{ display: flex; gap: 12px; flex-wrap: wrap; align-items: center; margin-bottom: 12px; }}
    .toolbar label {{ font-size: 13px; color: #334155; }}
    .toolbar select, .toolbar input {{ min-width: 180px; padding: 8px 10px; border-radius: 8px; border: 1px solid #cbd5e1; background: white; }}
    .muted {{ color: #64748b; font-size: 12px; }}
    .detail {{ margin-top: 8px; }}
    details {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 10px; }}
    summary {{ cursor: pointer; font-weight: 600; color: #0f172a; }}
    .kv {{ margin: 6px 0; }}
    .label {{ font-weight: 600; color: #334155; }}
    ul {{ margin: 6px 0 0 18px; padding: 0; }}
    li {{ margin: 4px 0; }}
    pre {{ white-space: pre-wrap; word-break: break-word; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; font-size: 12px; }}
    code {{ background: #e2e8f0; padding: 2px 6px; border-radius: 6px; }}
  </style>
</head>
<body>
{body}
<script>
{extra_script}
</script>
</body>
</html>
"""


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def _list_html(items: list[str]) -> str:
    if not items:
        return '&nbsp;'
    return '<ul>' + ''.join(f'<li>{html.escape(str(item))}</li>' for item in items) + '</ul>'


def _evidence_html(items: list[dict]) -> str:
    if not items:
        return '&nbsp;'
    rendered = []
    for item in items:
        rendered.append(
            '<div class="kv">'
            f'<span class="label">{html.escape(str(item.get("atomic_rule_id", "")))}</span>: '
            f'{html.escape(str(item.get("quote", "")))} '
            f'(p.{html.escape(str(item.get("page", "")))})'
            '</div>'
        )
    return ''.join(rendered)


def _findings_html(findings: list[dict]) -> str:
    if not findings:
        return '&nbsp;'
    blocks = []
    for item in findings:
        blocks.append(
            '<div class="detail">'
            f'<div class="kv"><span class="label">Severity</span>: {html.escape(str(item.get("severity", "")))}</div>'
            f'<div class="kv"><span class="label">Category</span>: {html.escape(str(item.get("category", "")))}</div>'
            f'<div class="kv"><span class="label">Summary</span>: {html.escape(str(item.get("summary", "")))}</div>'
            f'<div class="kv"><span class="label">Details</span>: {html.escape(str(item.get("details", "")))}</div>'
            f'<div class="kv"><span class="label">Suggested Fix</span>: {html.escape(str(item.get("suggested_fix", "")))}</div>'
            '</div>'
        )
    return ''.join(blocks)


def _render_rule_coverage_rows(status_by_rule: dict[str, dict]) -> str:
    rows = []
    for semantic_rule_id in sorted(status_by_rule):
        item = status_by_rule[semantic_rule_id]
        rows.append(
            f"<tr>"
            f"<td>{html.escape(semantic_rule_id)}</td>"
            f"<td>{html.escape(', '.join(item.get('paragraph_ids', [])))}</td>"
            f"<td>{html.escape(str(item.get('rule_type', '')))}</td>"
            f"<td>{html.escape(str(item.get('rule_coverage_status', '')))}</td>"
            f"<td>{html.escape(str(item.get('rule_pass_status', '')))}</td>"
            f"<td>{_list_html(item.get('required_case_types', []))}</td>"
            f"<td>{_list_html(item.get('present_case_types', []))}</td>"
            f"<td>{_list_html(item.get('accepted_case_types', []))}</td>"
            f"<td>{_list_html(item.get('missing_case_types', []))}</td>"
            f"</tr>"
        )
    return ''.join(rows)


def _render_coverage_heatmap(status_by_rule: dict[str, dict]) -> str:
    """Render a rule-type × coverage-status heatmap."""
    # Collect all rule types and statuses
    rule_types: set[str] = set()
    statuses: set[str] = {"fully_covered", "partially_covered", "uncovered", "not_applicable"}
    counts: dict[tuple[str, str], int] = {}
    for rule_id, item in status_by_rule.items():
        rt = item.get("rule_type", "unknown")
        cov = item.get("rule_coverage_status", "uncovered")
        rule_types.add(rt)
        counts[(rt, cov)] = counts.get((rt, cov), 0) + 1

    status_colors = {
        "fully_covered": "#22c55e",
        "partially_covered": "#eab308",
        "uncovered": "#ef4444",
        "not_applicable": "#94a3b8",
    }

    # Build matrix table
    header = "<thead><tr><th>Rule Type</th>"
    for s in ["fully_covered", "partially_covered", "uncovered", "not_applicable"]:
        header += f"<th style='background:#f1f5f9;text-align:center'>{s.replace('_', ' ').title()}</th>"
    header += "</tr></thead>"

    rows = "<tbody>"
    for rt in sorted(rule_types):
        rows += f"<tr><td style='font-weight:600'>{html.escape(rt)}</td>"
        for s in ["fully_covered", "partially_covered", "uncovered", "not_applicable"]:
            count = counts.get((rt, s), 0)
            color = status_colors[s]
            opacity = 0.3 if count == 0 else 1.0
            rows += f"<td style='background:{color};opacity:{opacity};text-align:center;font-weight:600'>{count}</td>"
        rows += "</tr>"
    rows += "</tbody>"

    return f"<table style='border-collapse:collapse;min-width:500px'>{header}{rows}</table>"


def _render_drift_view(drift_report: dict | None) -> str:
    """Render a drift view section comparing current vs previous coverage."""
    if not drift_report:
        return "<p class='muted'>No previous coverage report available for drift comparison.</p>"

    delta = drift_report.get("coverage_delta", 0)
    delta_color = "#22c55e" if delta >= 0 else "#ef4444"
    delta_sign = "+" if delta >= 0 else ""

    improved = drift_report.get("rules_improved", [])
    regressed = drift_report.get("rules_regressed", [])
    unchanged = drift_report.get("rules_unchanged", [])
    new_rules = drift_report.get("new_rules", [])

    lines = [
        f"<div class='grid'>",
        f"<div class='metric' style='background:{'#22c55e20' if delta>=0 else '#ef444420'};border-color:{'#22c55e' if delta>=0 else '#ef4444'}'>",
        f"<strong>Coverage Δ</strong><br/>",
        f"<span style='color:{delta_color};font-size:1.5em'>{delta_sign}{delta}%</span><br/>",
        f"<span class='muted'>prev: {drift_report.get('previous_coverage_percent', 0)}% → curr: {drift_report.get('current_coverage_percent', 0)}%</span>",
        f"</div>",
        f"<div class='metric'><strong>Improved</strong><br/><span style='color:#22c55e;font-size:1.5em'>{drift_report.get('improved_count', 0)}</span></div>",
        f"<div class='metric'><strong>Regressed</strong><br/><span style='color:#ef4444;font-size:1.5em'>{drift_report.get('regressed_count', 0)}</span></div>",
        f"<div class='metric'><strong>Unchanged</strong><br/><span style='color:#64748b;font-size:1.5em'>{drift_report.get('unchanged_count', 0)}</span></div>",
        f"</div>",
    ]

    if regressed:
        lines.append("<h3>Regressed Rules</h3>")
        lines.append("<ul>")
        for rule_id in regressed:
            lines.append(f"<li><code>{html.escape(rule_id)}</code></li>")
        lines.append("</ul>")

    if improved:
        lines.append("<h3>Improved Rules</h3>")
        lines.append("<ul>")
        for rule_id in improved:
            lines.append(f"<li><code>{html.escape(rule_id)}</code></li>")
        lines.append("</ul>")

    return "\n".join(lines)


def export_coverage_csv(coverage_report: dict, output_path: Path) -> None:
    """Export coverage report to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    status_by_rule = coverage_report.get("status_by_rule", {})

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "semantic_rule_id", "rule_type", "rule_coverage_status", "rule_pass_status",
            "required_case_types", "present_case_types", "accepted_case_types",
            "missing_case_types", "review_count", "paragraph_ids",
        ])
        for rule_id in sorted(status_by_rule.keys()):
            item = status_by_rule[rule_id]
            writer.writerow([
                rule_id,
                item.get("rule_type", ""),
                item.get("rule_coverage_status", ""),
                item.get("rule_pass_status", ""),
                "|".join(item.get("required_case_types", [])),
                "|".join(item.get("present_case_types", [])),
                "|".join(item.get("accepted_case_types", [])),
                "|".join(item.get("missing_case_types", [])),
                item.get("review_count", 0),
                "|".join(item.get("paragraph_ids", [])),
            ])


def generate_html_report(
    maker_cases_path: Path,
    checker_reviews_path: Path,
    maker_summary_path: Path,
    checker_summary_path: Path,
    coverage_report_path: Path,
    output_html_path: Path,
    previous_coverage_report_path: Path | None = None,
) -> dict:
    """Generate HTML report from pipeline outputs.

    Args:
        maker_cases_path: Path to maker_cases.jsonl
        checker_reviews_path: Path to checker_reviews.jsonl
        maker_summary_path: Path to maker summary.json
        checker_summary_path: Path to checker summary.json
        coverage_report_path: Path to coverage_report.json
        output_html_path: Output path for main HTML report
        previous_coverage_report_path: Optional path to a previous coverage_report.json
            for computing drift. If provided, a Drift View section is included.
    """
    maker_cases = load_jsonl(maker_cases_path)
    checker_reviews = load_jsonl(checker_reviews_path)
    maker_summary = load_json(maker_summary_path)
    checker_summary = load_json(checker_summary_path)
    coverage_report = load_json(coverage_report_path)

    # Import here to avoid circular dependency
    from .pipelines import calculate_drift

    drift_report: dict | None = None
    if previous_coverage_report_path and previous_coverage_report_path.exists():
        previous_coverage = load_json(previous_coverage_report_path)
        drift_report = calculate_drift(coverage_report, previous_coverage)

    # Export CSV alongside HTML
    csv_path = output_html_path.with_suffix(".csv")
    export_coverage_csv(coverage_report, csv_path)

    reviews_by_case = {item['case_id']: item for item in checker_reviews}

    combined_rows = []
    overall_values: list[str] = []
    coverage_values: list[str] = []
    maker_rows = []
    checker_rows = []

    for maker_record in maker_cases:
        semantic_rule_id = maker_record['semantic_rule_id']
        feature = maker_record.get('feature', '')
        scenario_count = len(maker_record.get('scenarios', []))
        maker_rows.append(
            f"<tr>"
            f"<td>{html.escape(semantic_rule_id)}</td>"
            f"<td>{html.escape(feature)}</td>"
            f"<td>{scenario_count}</td>"
            f"<td>{html.escape(', '.join(maker_record.get('requirement_ids', [])))}</td>"
            f"<td><details><summary>展开场景</summary>{''.join(_render_maker_scenario_block(s, paragraph_ids=maker_record.get('paragraph_ids', [])) for s in maker_record.get('scenarios', []))}</details></td>"
            f"</tr>"
        )

        for scenario in maker_record.get('scenarios', []):
            case_id = scenario.get('scenario_id', '')
            review = reviews_by_case.get(case_id, {})
            overall = str(review.get('overall_status', 'missing'))
            coverage = str(review.get('coverage_assessment', {}).get('status', 'missing'))
            overall_values.append(overall)
            coverage_values.append(coverage)
            combined_rows.append(
                f"<tr data-overall=\"{html.escape(overall)}\" data-coverage=\"{html.escape(coverage)}\" data-rule=\"{html.escape(semantic_rule_id)}\" data-case=\"{html.escape(case_id)}\">"
                f"<td>{html.escape(semantic_rule_id)}</td>"
                f"<td>{html.escape(case_id)}</td>"
                f"<td>{html.escape(feature)}</td>"
                f"<td>{html.escape(overall)}</td>"
                f"<td>{html.escape(coverage)}</td>"
                f"<td><details><summary>展开详情</summary>{_render_combined_detail(scenario, review, paragraph_ids=maker_record.get('paragraph_ids', []))}</details></td>"
                f"</tr>"
            )

    for review in checker_reviews:
        checker_rows.append(
            f"<tr>"
            f"<td>{html.escape(review.get('case_id', ''))}</td>"
            f"<td>{html.escape(review.get('semantic_rule_id', ''))}</td>"
            f"<td>{html.escape(str(review.get('overall_status', '')))}</td>"
            f"<td>{html.escape(str(review.get('coverage_assessment', {}).get('status', '')))}</td>"
            f"<td><details><summary>展开详情</summary>{_render_checker_detail(review)}</details></td>"
            f"</tr>"
        )

    filter_script = """
const overallFilter = document.getElementById('overallFilter');
const coverageFilter = document.getElementById('coverageFilter');
const keywordFilter = document.getElementById('keywordFilter');
const tableRows = Array.from(document.querySelectorAll('tbody tr[data-overall]'));
function applyFilters() {
  const overall = overallFilter.value;
  const coverage = coverageFilter.value;
  const keyword = keywordFilter.value.trim().toLowerCase();
  let visible = 0;
  for (const row of tableRows) {
    const matchesOverall = !overall || row.dataset.overall === overall;
    const matchesCoverage = !coverage || row.dataset.coverage === coverage;
    const haystack = row.innerText.toLowerCase();
    const matchesKeyword = !keyword || haystack.includes(keyword);
    const show = matchesOverall && matchesCoverage && matchesKeyword;
    row.style.display = show ? '' : 'none';
    if (show) visible += 1;
  }
  document.getElementById('visibleCount').innerText = String(visible);
}
overallFilter.addEventListener('change', applyFilters);
coverageFilter.addEventListener('change', applyFilters);
keywordFilter.addEventListener('input', applyFilters);
applyFilters();
"""

    combined_body = f"""
  <h1>Maker / Checker HTML 报告</h1>
  <div class="card">
    <h2>运行摘要</h2>
    <div class="grid">
      <div class="metric"><strong>Maker Rule 数</strong><br/>{maker_summary.get('merged_rule_count', maker_summary.get('processed_rule_count', 0))}</div>
      <div class="metric"><strong>Maker Scenario 数</strong><br/>{maker_summary.get('scenario_count', 0)}</div>
      <div class="metric"><strong>Checker Review 数</strong><br/>{checker_summary.get('merged_review_count', checker_summary.get('review_count', 0))}</div>
      <div class="metric"><strong>Fully Covered</strong><br/>{coverage_report.get('fully_covered', 0)}</div>
      <div class="metric"><strong>Partially Covered</strong><br/>{coverage_report.get('partially_covered', 0)}</div>
      <div class="metric"><strong>Uncovered</strong><br/>{coverage_report.get('uncovered', 0)}</div>
      <div class="metric"><strong>Not Applicable</strong><br/>{coverage_report.get('not_applicable', 0)}</div>
      <div class="metric"><strong>覆盖率</strong><br/>{coverage_report.get('coverage_percent', 0)}%</div>
    </div>
  </div>
  <div class="card">
    <h2>Rule 级覆盖判定</h2>
    <table>
      <thead>
        <tr>
          <th>Semantic Rule</th>
          <th>Paragraph IDs</th>
          <th>Rule Type</th>
          <th>Coverage Status</th>
          <th>Pass Status</th>
          <th>Required</th>
          <th>Present</th>
          <th>Accepted</th>
          <th>Missing</th>
        </tr>
      </thead>
      <tbody>
        {_render_rule_coverage_rows(coverage_report.get('status_by_rule', {}))}
      </tbody>
    </table>
  </div>
  <div class="card">
    <h2>导出</h2>
    <p><a href="{html.escape(csv_path.name)}" download>Download Coverage CSV</a></p>
    <p class="muted">Coverage report: {html.escape(str(coverage_report_path))}</p>
  </div>
  <div class="card">
    <h2>Rule Type × Coverage Status Heatmap</h2>
    {_render_coverage_heatmap(coverage_report.get('status_by_rule', {}))}
  </div>
  <div class="card">
    <h2>Drift View</h2>
    {_render_drift_view(drift_report)}
  </div>
  <div class="card">
    <h2>筛选</h2>
    <div class="toolbar">
      <label>Overall
        <select id="overallFilter">{_status_options(overall_values)}</select>
      </label>
      <label>Coverage
        <select id="coverageFilter">{_status_options(coverage_values)}</select>
      </label>
      <label>关键词
        <input id="keywordFilter" type="text" placeholder="rule id / case id / finding" />
      </label>
    </div>
    <div class="muted">可按 Overall、Coverage、关键词组合筛选。</div>
  </div>
  <div class="card">
    <h2>场景审核明细</h2>
    <table>
      <thead>
        <tr>
          <th>Semantic Rule</th>
          <th>Case ID</th>
          <th>Feature</th>
          <th>Overall</th>
          <th>Coverage</th>
          <th>详细信息</th>
        </tr>
      </thead>
      <tbody>
        {''.join(combined_rows)}
      </tbody>
    </table>
  </div>
"""

    maker_body = f"""
  <h1>Maker 可读结果</h1>
  <div class="card">
    <p><code>{html.escape(str(maker_cases_path))}</code></p>
    <table>
      <thead>
        <tr>
          <th>Semantic Rule</th>
          <th>Feature</th>
          <th>Scenario Count</th>
          <th>Requirement IDs</th>
          <th>详细场景</th>
        </tr>
      </thead>
      <tbody>
        {''.join(maker_rows)}
      </tbody>
    </table>
  </div>
"""

    checker_body = f"""
  <h1>Checker 可读结果</h1>
  <div class="card">
    <p><code>{html.escape(str(checker_reviews_path))}</code></p>
    <table>
      <thead>
        <tr>
          <th>Case ID</th>
          <th>Semantic Rule</th>
          <th>Overall</th>
          <th>Coverage</th>
          <th>详细信息</th>
        </tr>
      </thead>
      <tbody>
        {''.join(checker_rows)}
      </tbody>
    </table>
  </div>
"""

    maker_html_path = output_html_path.with_name('maker_readable.html')
    checker_html_path = output_html_path.with_name('checker_readable.html')

    _write_text(output_html_path, _render_page('Maker Checker Report', combined_body, filter_script))
    _write_text(maker_html_path, _render_page('Maker Readable Report', maker_body))
    _write_text(checker_html_path, _render_page('Checker Readable Report', checker_body))

    return {
        'output_html': str(output_html_path),
        'maker_html': str(maker_html_path),
        'checker_html': str(checker_html_path),
        'coverage_csv': str(csv_path),
        'maker_case_count': len(maker_cases),
        'checker_review_count': len(checker_reviews),
    }


def _render_maker_scenario_block(scenario: dict, paragraph_ids: list = None) -> str:
    if paragraph_ids is None:
        paragraph_ids = []
    scenario_para_ids = scenario.get("paragraph_ids", paragraph_ids)
    return (
        '<div class="detail">'
        f'<div class="kv"><span class="label">Scenario ID</span>: {html.escape(str(scenario.get("scenario_id", "")))}</div>'
        f'<div class="kv"><span class="label">Title</span>: {html.escape(str(scenario.get("title", "")))}</div>'
        f'<div class="kv"><span class="label">Intent</span>: {html.escape(str(scenario.get("intent", "")))}</div>'
        f'<div class="kv"><span class="label">Priority</span>: {html.escape(str(scenario.get("priority", "")))}</div>'
        f'<div class="kv"><span class="label">Case Type</span>: {html.escape(str(scenario.get("case_type", scenario.get("scenario_type", ""))))}</div>'
        + (f'<div class="kv"><span class="label">Paragraph IDs</span>: {html.escape(", ".join(scenario_para_ids))}</div>' if scenario_para_ids else '')
        + f'<div class="kv"><span class="label">Given</span>{_list_html(scenario.get("given", []))}</div>'
        + f'<div class="kv"><span class="label">When</span>{_list_html(scenario.get("when", []))}</div>'
        + f'<div class="kv"><span class="label">Then</span>{_list_html(scenario.get("then", []))}</div>'
        + f'<div class="kv"><span class="label">Assumptions</span>{_list_html(scenario.get("assumptions", []))}</div>'
        + f'<div class="kv"><span class="label">Evidence</span>{_evidence_html(scenario.get("evidence", []))}</div>'
        '</div>'
    )


def _render_checker_detail(review: dict) -> str:
    return (
        f'<div class="kv"><span class="label">Case Type</span>: {html.escape(str(review.get("case_type", "")))}</div>'
        f'<div class="kv"><span class="label">Case Type Accepted</span>: {html.escape(str(review.get("case_type_accepted", "")))}</div>'
        f'<div class="kv"><span class="label">Coverage Relevance</span>: {html.escape(str(review.get("coverage_relevance", "")))}</div>'
        f'<div class="kv"><span class="label">Blocking Findings Count</span>: {html.escape(str(review.get("blocking_findings_count", "")))}</div>'
        f'<div class="kv"><span class="label">Is Blocking</span>: {html.escape(str(review.get("is_blocking", "")))}</div>'
        f'<div class="kv"><span class="label">Scores</span><pre>{html.escape(json.dumps(review.get("scores", {}), ensure_ascii=False, indent=2))}</pre></div>'
        f'<div class="kv"><span class="label">Coverage Reason</span>: {html.escape(str(review.get("coverage_assessment", {}).get("reason", "")))}</div>'
        f'<div class="kv"><span class="label">Missing Aspects</span>{_list_html(review.get("coverage_assessment", {}).get("missing_aspects", []))}</div>'
        f'<div class="kv"><span class="label">Findings</span>{_findings_html(review.get("findings", []))}</div>'
    )


def _render_combined_detail(scenario: dict, review: dict, paragraph_ids: list = None) -> str:
    return _render_maker_scenario_block(scenario, paragraph_ids=paragraph_ids) + _render_checker_detail(review)
