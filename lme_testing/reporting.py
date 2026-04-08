from __future__ import annotations

import html
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


def generate_html_report(
    maker_cases_path: Path,
    checker_reviews_path: Path,
    maker_summary_path: Path,
    checker_summary_path: Path,
    coverage_report_path: Path,
    output_html_path: Path,
) -> dict:
    maker_cases = load_jsonl(maker_cases_path)
    checker_reviews = load_jsonl(checker_reviews_path)
    maker_summary = load_json(maker_summary_path)
    checker_summary = load_json(checker_summary_path)
    coverage_report = load_json(coverage_report_path)

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
            f"<td><details><summary>展开场景</summary>{''.join(_render_maker_scenario_block(s) for s in maker_record.get('scenarios', []))}</details></td>"
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
                f"<td><details><summary>展开详情</summary>{_render_combined_detail(scenario, review)}</details></td>"
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
        'maker_case_count': len(maker_cases),
        'checker_review_count': len(checker_reviews),
    }


def _render_maker_scenario_block(scenario: dict) -> str:
    return (
        '<div class="detail">'
        f'<div class="kv"><span class="label">Scenario ID</span>: {html.escape(str(scenario.get("scenario_id", "")))}</div>'
        f'<div class="kv"><span class="label">Title</span>: {html.escape(str(scenario.get("title", "")))}</div>'
        f'<div class="kv"><span class="label">Intent</span>: {html.escape(str(scenario.get("intent", "")))}</div>'
        f'<div class="kv"><span class="label">Priority</span>: {html.escape(str(scenario.get("priority", "")))}</div>'
        f'<div class="kv"><span class="label">Case Type</span>: {html.escape(str(scenario.get("case_type", scenario.get("scenario_type", ""))))}</div>'
        f'<div class="kv"><span class="label">Given</span>{_list_html(scenario.get("given", []))}</div>'
        f'<div class="kv"><span class="label">When</span>{_list_html(scenario.get("when", []))}</div>'
        f'<div class="kv"><span class="label">Then</span>{_list_html(scenario.get("then", []))}</div>'
        f'<div class="kv"><span class="label">Assumptions</span>{_list_html(scenario.get("assumptions", []))}</div>'
        f'<div class="kv"><span class="label">Evidence</span>{_evidence_html(scenario.get("evidence", []))}</div>'
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


def _render_combined_detail(scenario: dict, review: dict) -> str:
    return _render_maker_scenario_block(scenario) + _render_checker_detail(review)
