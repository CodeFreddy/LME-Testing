"""Case comparison generator — side-by-side diff view between two iteration outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_case_compare(
    prev_cases_path: Path,
    next_cases_path: Path,
    rewritten_case_ids: list[str],
    iteration_prev: int,
    iteration_next: int,
    output_path: Path,
) -> dict[str, Any]:
    """Render a side-by-side HTML comparison of two maker_cases.jsonl iterations.

    Args:
        prev_cases_path: Path to iteration N maker_cases.jsonl.
        next_cases_path: Path to iteration N+1 maker_cases.jsonl (after rewrite).
        rewritten_case_ids: List of case_ids that were rewritten.
        iteration_prev: Iteration number N.
        iteration_next: Iteration number N+1.
        output_path: Where to write the HTML file.

    Returns:
        dict with "total_compared", "rewritten_count", "added_count", "removed_count".
    """
    prev_records = _load_maker_cases(prev_cases_path)
    next_records = _load_maker_cases(next_cases_path)

    prev_by_rule = {r["semantic_rule_id"]: r for r in prev_records}
    next_by_rule = {r["semantic_rule_id"]: r for r in next_records}

    prev_scenarios: dict[str, dict] = {}
    for r in prev_records:
        for s in r.get("scenarios", []):
            prev_scenarios[s["scenario_id"]] = s

    next_scenarios: dict[str, dict] = {}
    for r in next_records:
        for s in r.get("scenarios", []):
            next_scenarios[s["scenario_id"]] = s

    all_rule_ids = sorted(set(list(prev_by_rule.keys()) + list(next_by_rule.keys())))

    rewritten_set = set(rewritten_case_ids)
    added = [cid for cid in rewritten_case_ids if cid not in prev_scenarios]
    removed = [cid for cid in rewritten_case_ids if cid not in next_scenarios]

    rule_blocks = ""
    for rule_id in all_rule_ids:
        prev_rule = prev_by_rule.get(rule_id, {})
        next_rule = next_by_rule.get(rule_id, {})
        feature = next_rule.get("feature") or prev_rule.get("feature", "")

        prev_by_cid = {s["scenario_id"]: s for s in prev_rule.get("scenarios", [])}
        next_by_cid = {s["scenario_id"]: s for s in next_rule.get("scenarios", [])}
        all_cids = sorted(set(list(prev_by_cid.keys()) + list(next_by_cid.keys())))

        scenario_rows = ""
        for cid in all_cids:
            prev_s = prev_by_cid.get(cid)
            next_s = next_by_cid.get(cid)
            is_rewritten = cid in rewritten_set

            if prev_s and next_s:
                diff_fields = _diff_scenarios(prev_s, next_s)
                diff_html = _render_diff_rows(diff_fields)
                left = _render_scenario_col(prev_s)
                right = _render_scenario_col(next_s)
                row_cls = "rewritten" if is_rewritten else ""
            elif prev_s:
                left = _render_scenario_col(prev_s)
                right = "<em>removed</em>"
                diff_html = ""
                row_cls = "removed"
            else:
                left = "<em>added</em>"
                right = _render_scenario_col(next_s)
                diff_html = ""
                row_cls = "added"

            scenario_rows += (
                '<tr class="' + row_cls + '">'
                "<td>" + cid + "</td>"
                "<td>" + left + "</td>"
                "<td>" + right + "</td>"
                '<td class="diff-cell">' + diff_html + "</td>"
                "</tr>"
            )

        rule_blocks += (
            '<table class="rule-table">'
            "<thead>"
            '<tr><th colspan="3">' + rule_id + ": " + feature + "</th></tr>"
            "<tr>"
            "<th>Case ID</th>"
            "<th>Iteration " + str(iteration_prev) + "</th>"
            "<th>Iteration " + str(iteration_next) + "</th>"
            "<th>Changes</th>"
            "</tr>"
            "</thead>"
            "<tbody>" + scenario_rows + "</tbody>"
            "</table>"
        )

    stats = {
        "total_compared": len(all_rule_ids),
        "rewritten_count": len(rewritten_case_ids),
        "added_count": len(added),
        "removed_count": len(removed),
    }

    html = (
        "<!DOCTYPE html>\n"
        "<html lang='en'>\n"
        "<head>\n"
        "<meta charset='utf-8'>\n"
        "<title>Case Comparison — Iter " + str(iteration_prev) + " vs Iter " + str(iteration_next) + "</title>\n"
        "<style>\n"
        "  body { font-family: sans-serif; margin: 1.5rem; background: #f9f9f9; }\n"
        "  .stats { background: white; border: 1px solid #ddd; padding: 0.75rem 1rem; margin-bottom: 1.5rem; border-radius: 4px; }\n"
        "  .stats span { margin-right: 1.5rem; }\n"
        "  .rule-table { width: 100%; border-collapse: collapse; background: white; margin-bottom: 1.5rem; }\n"
        "  .rule-table th { background: #eceff1; padding: 0.5rem; text-align: left; }\n"
        "  .rule-table td { padding: 0.5rem; vertical-align: top; border-top: 1px solid #eee; font-size: 0.8rem; }\n"
        "  .rule-table tr.rewritten td { background: #fffde7; }\n"
        "  .rule-table tr.added td { background: #e8f5e9; }\n"
        "  .rule-table tr.removed td { background: #ffebee; }\n"
        "  td.diff-cell { font-size: 0.75rem; color: #666; }\n"
        "  .diff-row td { background: #f5f5f5 !important; color: #333; }\n"
        "  .field-name { font-weight: bold; color: #1565c0; }\n"
        "  .old-val { color: #c62828; text-decoration: line-through; }\n"
        "  .new-val { color: #2e7d32; }\n"
        "  em { color: #999; font-style: italic; }\n"
        "</style>\n"
        "</head>\n"
        "<body>\n"
        "<h1>Case Comparison: Iteration " + str(iteration_prev) + " → Iteration " + str(iteration_next) + "</h1>\n"
        "<div class='stats'>\n"
        "<span><strong>" + str(stats["total_compared"]) + "</strong> rules compared</span>\n"
        "<span><strong>" + str(stats["rewritten_count"]) + "</strong> rewritten</span>\n"
        "<span><strong>" + str(stats["added_count"]) + "</strong> added</span>\n"
        "<span><strong>" + str(stats["removed_count"]) + "</strong> removed</span>\n"
        "</div>\n"
        + rule_blocks +
        "\n</body>\n"
        "</html>"
    )

    output_path.write_text(html, encoding="utf-8")
    return stats


def _load_maker_cases(path: Path | None) -> list[dict[str, Any]]:
    if not path or not path.exists():
        return []
    records = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def _diff_scenarios(a: dict, b: dict) -> list[dict]:
    diffs = []
    for field in ["title", "given", "when", "then", "case_type", "priority", "intent"]:
        val_a = a.get(field)
        val_b = b.get(field)
        if val_a != val_b:
            diffs.append({"field": field, "old": val_a, "new": val_b})
    return diffs


def _render_diff_rows(diffs: list[dict]) -> str:
    if not diffs:
        return "<em>no field changes</em>"
    rows = ""
    for d in diffs:
        old = _fmt_val(d["old"])
        new = _fmt_val(d["new"])
        rows += (
            '<div class="diff-row">'
            '<span class="field-name">' + d["field"] + "</span>: "
            '<span class="old-val">' + old + "</span> → "
            '<span class="new-val">' + new + "</span>"
            "</div>"
        )
    return rows


def _fmt_val(v: Any) -> str:
    if isinstance(v, list):
        return "<br>".join("• " + str(item) for item in v)
    if v is None:
        return "<em>—</em>"
    return str(v)


def _render_scenario_col(s: dict) -> str:
    case_type = s.get("case_type", "")
    title = s.get("title", "")
    given = "<br>".join("• " + str(g) for g in s.get("given", []))
    when = "<br>".join("• " + str(w) for w in s.get("when", []))
    then = "<br>".join("• " + str(t) for t in s.get("then", []))
    return (
        "<strong>" + title + "</strong> <em>(" + case_type + ")</em><br>"
        "<span>G: " + given + "</span><br>"
        "<span>W: " + when + "</span><br>"
        "<span>T: " + then + "</span>"
    )
