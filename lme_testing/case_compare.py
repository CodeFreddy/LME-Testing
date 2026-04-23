from __future__ import annotations

import difflib
import html
import json
import re
from pathlib import Path
from typing import Any

from .storage import load_jsonl


def _scenario_map(records: list[dict]) -> dict[str, dict[str, Any]]:
    scenarios: dict[str, dict[str, Any]] = {}
    for record in records:
        for scenario in record.get("scenarios", []):
            case_id = scenario.get("scenario_id")
            if case_id:
                scenarios[str(case_id)] = scenario
    return scenarios


def _scenario_html(scenario: dict[str, Any] | None) -> str:
    if not scenario:
        return '<span class="muted">Missing</span>'
    return (
        '<pre>'
        + html.escape(json.dumps(scenario, ensure_ascii=False, indent=2))
        + '</pre>'
    )


def _json_lines(scenario: dict[str, Any] | None) -> list[str]:
    if not scenario:
        return ["Missing"]
    return json.dumps(scenario, ensure_ascii=False, indent=2).splitlines()


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\s+|[^\s]+", text)


def _inline_diff(before: str, after: str) -> tuple[str, str]:
    before_tokens = _tokenize(before)
    after_tokens = _tokenize(after)
    matcher = difflib.SequenceMatcher(a=before_tokens, b=after_tokens)
    before_parts: list[str] = []
    after_parts: list[str] = []
    for tag, before_start, before_end, after_start, after_end in matcher.get_opcodes():
        before_text = html.escape("".join(before_tokens[before_start:before_end]))
        after_text = html.escape("".join(after_tokens[after_start:after_end]))
        if tag == "equal":
            before_parts.append(before_text)
            after_parts.append(after_text)
        elif tag == "delete":
            before_parts.append(f'<span class="diff-del-text">{before_text}</span>')
        elif tag == "insert":
            after_parts.append(f'<span class="diff-add-text">{after_text}</span>')
        else:
            before_parts.append(f'<span class="diff-del-text">{before_text}</span>')
            after_parts.append(f'<span class="diff-add-text">{after_text}</span>')
    return "".join(before_parts), "".join(after_parts)


def _diff_html(before: dict[str, Any] | None, after: dict[str, Any] | None) -> tuple[str, str]:
    before_lines = _json_lines(before)
    after_lines = _json_lines(after)
    matcher = difflib.SequenceMatcher(a=before_lines, b=after_lines)
    before_rendered: list[str] = []
    after_rendered: list[str] = []
    for tag, before_start, before_end, after_start, after_end in matcher.get_opcodes():
        if tag == "equal":
            before_rendered.extend(html.escape(line) for line in before_lines[before_start:before_end])
            after_rendered.extend(html.escape(line) for line in after_lines[after_start:after_end])
        elif tag == "delete":
            before_rendered.extend(f'<span class="diff-line diff-del">{html.escape(line)}</span>' for line in before_lines[before_start:before_end])
        elif tag == "insert":
            after_rendered.extend(f'<span class="diff-line diff-add">{html.escape(line)}</span>' for line in after_lines[after_start:after_end])
        else:
            replaced_before = before_lines[before_start:before_end]
            replaced_after = after_lines[after_start:after_end]
            max_len = max(len(replaced_before), len(replaced_after))
            for index in range(max_len):
                before_line = replaced_before[index] if index < len(replaced_before) else ""
                after_line = replaced_after[index] if index < len(replaced_after) else ""
                before_text, after_text = _inline_diff(before_line, after_line)
                if before_line:
                    before_rendered.append(f'<span class="diff-line diff-del">{before_text}</span>')
                if after_line:
                    after_rendered.append(f'<span class="diff-line diff-add">{after_text}</span>')
    return (
        '<pre class="diff-pre">' + "\n".join(before_rendered) + '</pre>',
        '<pre class="diff-pre">' + "\n".join(after_rendered) + '</pre>',
    )


def _row_html(case_id: str, before: dict[str, Any] | None, after: dict[str, Any] | None, before_label: str, after_label: str) -> str:
    changed = before != after
    status = "changed" if changed else "unchanged"
    before_html, after_html = _diff_html(before, after)
    return (
        f'<tr data-status="{html.escape(status)}">'
        f"<td>{html.escape(case_id)}</td>"
        f"<td>{html.escape(status)}</td>"
        f"<td><div class=\"label\">{html.escape(before_label)}</div>{before_html}</td>"
        f"<td><div class=\"label\">{html.escape(after_label)}</div>{after_html}</td>"
        "</tr>"
    )


def build_case_compare(
    prev_cases_path: Path,
    next_cases_path: Path,
    rewritten_case_ids: set[str],
    iteration_prev: int,
    iteration_next: int,
    output_html_path: Path,
    display_iteration: int | None = None,
) -> dict[str, Any]:
    """Render a compact before/after HTML view for rewritten scenarios."""
    display_iteration = iteration_next if display_iteration is None else display_iteration
    previous = _scenario_map(load_jsonl(prev_cases_path))
    current = _scenario_map(load_jsonl(next_cases_path))
    case_ids = sorted(rewritten_case_ids or (set(previous) | set(current)))
    before_label = f"Iteration {display_iteration} (before)"
    after_label = f"Iteration {display_iteration} (after)"
    rows = [
        _row_html(case_id, previous.get(case_id), current.get(case_id), before_label, after_label)
        for case_id in case_ids
    ]
    changed_count = sum(1 for case_id in case_ids if previous.get(case_id) != current.get(case_id))
    title = f"Case Compare: Iteration {display_iteration:03d}"
    output_html_path.parent.mkdir(parents=True, exist_ok=True)
    output_html_path.write_text(
        f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>{html.escape(title)}</title>
  <style>
    body {{ font-family: 'Microsoft YaHei', 'Segoe UI', sans-serif; margin: 24px; color: #1f2937; background: #f8fafc; }}
    h1 {{ color: #0f172a; }}
    .card {{ background: white; border: 1px solid #cbd5e1; border-radius: 12px; padding: 16px 20px; margin-bottom: 20px; }}
    .muted {{ color: #64748b; }}
    .label {{ font-weight: 700; color: #334155; margin-bottom: 6px; }}
    table {{ width: 100%; border-collapse: collapse; background: white; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 10px; vertical-align: top; text-align: left; font-size: 13px; }}
    th {{ background: #e2e8f0; }}
    pre {{ white-space: pre-wrap; word-break: break-word; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; font-size: 12px; }}
    .diff-pre {{ line-height: 1.55; color: #1f2937; }}
    .diff-line {{ display: block; margin: 0 -4px; padding: 0 4px; border-radius: 4px; }}
    .diff-del {{ background: #fee2e2; }}
    .diff-add {{ background: #dcfce7; }}
    .diff-del-text {{ background: #fca5a5; color: #7f1d1d; font-weight: 700; text-decoration: line-through; }}
    .diff-add-text {{ background: #86efac; color: #14532d; font-weight: 700; }}
  </style>
</head>
<body>
  <h1>{html.escape(title)}</h1>
  <div class="card">
    <div><strong>Previous Source</strong>: {html.escape(str(prev_cases_path))}</div>
    <div><strong>Next Source</strong>: {html.escape(str(next_cases_path))}</div>
    <div><strong>Requested Rewrites</strong>: {len(case_ids)}</div>
    <div><strong>Changed</strong>: {changed_count}</div>
  </div>
  <table>
    <thead><tr><th>Case ID</th><th>Status</th><th>{html.escape(before_label)}</th><th>{html.escape(after_label)}</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</body>
</html>
""",
        encoding="utf-8",
    )
    return {
        "output_html": str(output_html_path),
        "display_iteration": display_iteration,
        "iteration_prev": iteration_prev,
        "iteration_next": iteration_next,
        "case_count": len(case_ids),
        "changed_count": changed_count,
    }
