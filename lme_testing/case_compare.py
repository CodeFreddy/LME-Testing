from __future__ import annotations

import difflib
import html
import json
from pathlib import Path

from .storage import load_jsonl

COMPARE_FIELDS = ("given", "when", "then", "evidence", "assumptions", "case_type")


def _field_lines(scenario: dict, field: str) -> list[str]:
    value = scenario.get(field)
    if value is None:
        return []
    if isinstance(value, list):
        return [json.dumps(item, ensure_ascii=False) if isinstance(item, dict) else str(item) for item in value]
    return [str(value)]


def _diff_html(prev_lines: list[str], next_lines: list[str]) -> tuple[str, str]:
    """Return (left_html, right_html) with changed lines highlighted."""
    matcher = difflib.SequenceMatcher(None, prev_lines, next_lines, autojunk=False)
    left_parts: list[str] = []
    right_parts: list[str] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        for line in prev_lines[i1:i2]:
            escaped = html.escape(line)
            if tag == "equal":
                left_parts.append(f'<div class="line">{escaped}</div>')
            else:
                left_parts.append(f'<div class="line changed">{escaped}</div>')
        for line in next_lines[j1:j2]:
            escaped = html.escape(line)
            if tag == "equal":
                right_parts.append(f'<div class="line">{escaped}</div>')
            else:
                right_parts.append(f'<div class="line changed">{escaped}</div>')

    return "".join(left_parts) or '<div class="line muted">(empty)</div>', \
           "".join(right_parts) or '<div class="line muted">(empty)</div>'


def _build_case_index(cases_path: Path) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for record in load_jsonl(cases_path):
        for scenario in record.get("scenarios", []):
            case_id = scenario.get("scenario_id")
            if case_id:
                index[case_id] = scenario
    return index


def build_case_compare(
    prev_cases_path: Path,
    next_cases_path: Path,
    rewritten_case_ids: set[str],
    iteration_prev: int,
    iteration_next: int,
    output_html_path: Path,
    display_iteration: int | None = None,
) -> dict:
    """Build side-by-side HTML diff for rewritten cases between two iterations."""
    prev_index = _build_case_index(prev_cases_path)
    next_index = _build_case_index(next_cases_path)
    before_label_iteration = iteration_prev if display_iteration is None else display_iteration
    after_label_iteration = iteration_next if display_iteration is None else display_iteration

    common_ids = sorted(rewritten_case_ids & set(prev_index) & set(next_index))
    cards_html = ""
    for case_id in common_ids:
        prev_scenario = prev_index[case_id]
        next_scenario = next_index[case_id]
        field_rows = ""
        for field in COMPARE_FIELDS:
            prev_lines = _field_lines(prev_scenario, field)
            next_lines = _field_lines(next_scenario, field)
            left_html, right_html = _diff_html(prev_lines, next_lines)
            field_rows += (
                f'<tr>'
                f'<td class="field-label">{html.escape(field)}</td>'
                f'<td class="diff-cell">{left_html}</td>'
                f'<td class="diff-cell">{right_html}</td>'
                f'</tr>'
            )
        cards_html += (
            f'<div class="card">'
            f'<h3>{html.escape(case_id)}</h3>'
            f'<table class="diff-table">'
            f'<thead><tr>'
            f'<th style="width:12%">Field</th>'
            f'<th>Iteration {before_label_iteration} (before)</th>'
            f'<th>Iteration {after_label_iteration} (after)</th>'
            f'</tr></thead>'
            f'<tbody>{field_rows}</tbody>'
            f'</table>'
            f'</div>'
        )

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>Case Compare: Iteration {before_label_iteration:03d}</title>
  <style>
    body {{ font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif; margin: 24px; color: #1f2937; background: #f8fafc; }}
    h1, h3 {{ color: #0f172a; }}
    .card {{ background: white; border: 1px solid #cbd5e1; border-radius: 12px; padding: 16px 20px; margin-bottom: 20px; box-shadow: 0 6px 18px rgba(15,23,42,0.06); }}
    .diff-table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
    .diff-table th, .diff-table td {{ border: 1px solid #cbd5e1; padding: 8px 10px; vertical-align: top; font-size: 12px; }}
    .diff-table th {{ background: #e2e8f0; }}
    .field-label {{ font-weight: 600; color: #334155; background: #f1f5f9; white-space: nowrap; }}
    .diff-cell {{ font-family: monospace; white-space: pre-wrap; word-break: break-word; }}
    .line {{ margin: 2px 0; padding: 1px 4px; border-radius: 3px; }}
    .line.changed {{ background: #fef9c3; border-left: 3px solid #f59e0b; }}
    .muted {{ color: #94a3b8; font-style: italic; }}
  </style>
</head>
<body>
<h1>Case Compare: Iteration {before_label_iteration:03d}</h1>
<div class="card">
  <p>Only rewritten cases are shown. <strong>{len(common_ids)}</strong> case(s) compared.</p>
</div>
{cards_html}
</body>
</html>
"""
    output_html_path.parent.mkdir(parents=True, exist_ok=True)
    output_html_path.write_text(page, encoding="utf-8")
    return {
        "compared_case_count": len(common_ids),
        "output_html": str(output_html_path),
        "iteration_prev": iteration_prev,
        "iteration_next": iteration_next,
        "display_iteration": before_label_iteration,
    }
