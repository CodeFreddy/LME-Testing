#!/usr/bin/env python3
"""Compare two governed document artifact directories.

The filename keeps the Initial Margin task entrypoint, but the implementation is
document-generic: it compares artifact directories containing metadata.json,
clauses.json, atomic_rules.json, and semantic_rules.json.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import UTC, datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare two governed artifact directories and emit JSON/Markdown reports."
    )
    parser.add_argument("--previous", required=True, help="Previous version artifact directory.")
    parser.add_argument("--current", required=True, help="Current version artifact directory.")
    parser.add_argument(
        "--json-output",
        default="evidence/im_hk_v14_diff/im_hk_v13_to_v14_diff.json",
        help="Path to write structured diff JSON.",
    )
    parser.add_argument(
        "--markdown-output",
        default="docs/planning/im_hk_v14_diff_report.md",
        help="Path to write human-readable Markdown report.",
    )
    parser.add_argument(
        "--changed-threshold",
        type=float,
        default=0.985,
        help="Similarity below this threshold is reported as a changed candidate.",
    )
    parser.add_argument(
        "--match-threshold",
        type=float,
        default=0.90,
        help="Minimum normalized text similarity for ID-drift candidate matching.",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=25,
        help="Maximum detailed items to include per section in the Markdown report.",
    )
    return parser.parse_args()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_artifact_dir(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "metadata": load_json(path / "metadata.json", {}),
        "clauses": load_json(path / "clauses.json", []),
        "atomic_rules": load_json(path / "atomic_rules.json", []),
        "semantic_rules": load_json(path / "semantic_rules.json", []),
        "validation_report": load_json(path / "validation_report.json", {}),
    }


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    text = value.lower()
    text = text.replace("“", '"').replace("”", '"').replace("’", "'")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[.]{3,}", "...", text)
    return text.strip()


def stable_item_id(item: dict[str, Any], id_field: str) -> str:
    value = item.get(id_field)
    if isinstance(value, str) and value.strip():
        return value.strip()
    paragraph_id = item.get("paragraph_id")
    if isinstance(paragraph_id, str) and paragraph_id.strip():
        return paragraph_id.strip()
    raw_text = normalize_text(item.get("raw_text"))
    return f"<raw:{hash(raw_text)}>"


def by_id(items: list[dict[str, Any]], id_field: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        result.setdefault(stable_item_id(item, id_field), item)
    return result


def count_values(items: list[dict[str, Any]], path: tuple[str, ...]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for item in items:
        value: Any = item
        for key in path:
            if not isinstance(value, dict):
                value = None
                break
            value = value.get(key)
        counter[str(value if value is not None else "<missing>")] += 1
    return dict(sorted(counter.items()))


def text_similarity(left: str | None, right: str | None) -> float:
    return SequenceMatcher(None, normalize_text(left), normalize_text(right)).ratio()


def short_text(value: str | None, limit: int = 220) -> str:
    text = normalize_text(value)
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def compare_inventory(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    keys = ["metadata", "pages.json", "clauses", "atomic_rules", "semantic_rules", "validation_report"]
    prev_path = Path(previous["path"])
    curr_path = Path(current["path"])
    return {
        key: {
            "previous_exists": (prev_path / filename_for_inventory_key(key)).exists(),
            "current_exists": (curr_path / filename_for_inventory_key(key)).exists(),
        }
        for key in keys
    }


def filename_for_inventory_key(key: str) -> str:
    return key if key.endswith(".json") else f"{key}.json"


def compare_rules(
    previous_rules: list[dict[str, Any]],
    current_rules: list[dict[str, Any]],
    *,
    changed_threshold: float,
    match_threshold: float,
) -> dict[str, Any]:
    prev_by_id = by_id(previous_rules, "rule_id")
    curr_by_id = by_id(current_rules, "rule_id")
    common_ids = sorted(set(prev_by_id) & set(curr_by_id))

    changed: list[dict[str, Any]] = []
    unchanged_count = 0
    source_anchor_warnings: list[dict[str, Any]] = []

    for rule_id in common_ids:
        prev = prev_by_id[rule_id]
        curr = curr_by_id[rule_id]
        similarity = text_similarity(prev.get("raw_text"), curr.get("raw_text"))
        anchor_changed = {
            "paragraph_id": prev.get("paragraph_id") != curr.get("paragraph_id"),
            "clause_id": prev.get("clause_id") != curr.get("clause_id"),
            "pages": (prev.get("start_page"), prev.get("end_page"))
            != (curr.get("start_page"), curr.get("end_page")),
        }
        if any(anchor_changed.values()):
            source_anchor_warnings.append(
                {
                    "rule_id": rule_id,
                    "anchor_changed": anchor_changed,
                    "previous_anchor": rule_anchor(prev),
                    "current_anchor": rule_anchor(curr),
                }
            )
        if similarity < changed_threshold or prev.get("rule_type") != curr.get("rule_type"):
            changed.append(
                {
                    "rule_id": rule_id,
                    "similarity": round(similarity, 6),
                    "previous_rule_type": prev.get("rule_type"),
                    "current_rule_type": curr.get("rule_type"),
                    "previous_anchor": rule_anchor(prev),
                    "current_anchor": rule_anchor(curr),
                    "previous_text": short_text(prev.get("raw_text")),
                    "current_text": short_text(curr.get("raw_text")),
                }
            )
        else:
            unchanged_count += 1

    removed_ids = sorted(set(prev_by_id) - set(curr_by_id))
    added_ids = sorted(set(curr_by_id) - set(prev_by_id))
    added_by_id = {rule_id: curr_by_id[rule_id] for rule_id in added_ids}
    removed_by_id = {rule_id: prev_by_id[rule_id] for rule_id in removed_ids}
    drift_matches = find_id_drift_candidates(removed_by_id, added_by_id, match_threshold)
    drift_added = {item["current_rule_id"] for item in drift_matches}
    drift_removed = {item["previous_rule_id"] for item in drift_matches}

    return {
        "previous_count": len(previous_rules),
        "current_count": len(current_rules),
        "delta": len(current_rules) - len(previous_rules),
        "common_id_count": len(common_ids),
        "unchanged_count": unchanged_count,
        "changed_count": len(changed),
        "added_count": len([rule_id for rule_id in added_ids if rule_id not in drift_added]),
        "removed_count": len([rule_id for rule_id in removed_ids if rule_id not in drift_removed]),
        "id_drift_candidate_count": len(drift_matches),
        "changed_rule_candidates": changed,
        "added_rule_candidates": summarize_rules(
            [curr_by_id[rule_id] for rule_id in added_ids if rule_id not in drift_added]
        ),
        "removed_rule_candidates": summarize_rules(
            [prev_by_id[rule_id] for rule_id in removed_ids if rule_id not in drift_removed]
        ),
        "id_drift_candidates": drift_matches,
        "source_anchor_warnings": source_anchor_warnings,
    }


def rule_anchor(rule: dict[str, Any]) -> dict[str, Any]:
    return {
        "paragraph_id": rule.get("paragraph_id"),
        "clause_id": rule.get("clause_id"),
        "start_page": rule.get("start_page"),
        "end_page": rule.get("end_page"),
    }


def summarize_rules(rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "rule_id": rule.get("rule_id"),
            "paragraph_id": rule.get("paragraph_id"),
            "clause_id": rule.get("clause_id"),
            "rule_type": rule.get("rule_type"),
            "anchor": rule_anchor(rule),
            "text": short_text(rule.get("raw_text")),
        }
        for rule in rules
    ]


def find_id_drift_candidates(
    removed_by_id: dict[str, dict[str, Any]],
    added_by_id: dict[str, dict[str, Any]],
    match_threshold: float,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    used_added: set[str] = set()
    for removed_id, removed in sorted(removed_by_id.items()):
        best_id = ""
        best_similarity = 0.0
        for added_id, added in sorted(added_by_id.items()):
            if added_id in used_added:
                continue
            similarity = text_similarity(removed.get("raw_text"), added.get("raw_text"))
            if similarity > best_similarity:
                best_id = added_id
                best_similarity = similarity
        if best_id and best_similarity >= match_threshold:
            used_added.add(best_id)
            candidates.append(
                {
                    "previous_rule_id": removed_id,
                    "current_rule_id": best_id,
                    "similarity": round(best_similarity, 6),
                    "previous_anchor": rule_anchor(removed),
                    "current_anchor": rule_anchor(added_by_id[best_id]),
                    "previous_text": short_text(removed.get("raw_text")),
                    "current_text": short_text(added_by_id[best_id].get("raw_text")),
                }
            )
    return candidates


def compare_clauses(previous: list[dict[str, Any]], current: list[dict[str, Any]]) -> dict[str, Any]:
    prev_by_id = by_id(previous, "clause_id")
    curr_by_id = by_id(current, "clause_id")
    changed = []
    for clause_id in sorted(set(prev_by_id) & set(curr_by_id)):
        prev = prev_by_id[clause_id]
        curr = curr_by_id[clause_id]
        similarity = text_similarity(prev.get("raw_text"), curr.get("raw_text"))
        if similarity < 0.985:
            changed.append(
                {
                    "clause_id": clause_id,
                    "similarity": round(similarity, 6),
                    "previous_pages": [prev.get("start_page"), prev.get("end_page")],
                    "current_pages": [curr.get("start_page"), curr.get("end_page")],
                }
            )
    return {
        "previous_count": len(previous),
        "current_count": len(current),
        "delta": len(current) - len(previous),
        "common_id_count": len(set(prev_by_id) & set(curr_by_id)),
        "added_clause_ids": sorted(set(curr_by_id) - set(prev_by_id)),
        "removed_clause_ids": sorted(set(prev_by_id) - set(curr_by_id)),
        "changed_clause_candidates": changed,
    }


def build_downstream_impact(report: dict[str, Any]) -> list[dict[str, str]]:
    impacts: list[dict[str, str]] = []
    rule_delta = report["rule_delta"]
    changed_total = (
        rule_delta["changed_count"]
        + rule_delta["added_count"]
        + rule_delta["removed_count"]
        + rule_delta["id_drift_candidate_count"]
    )
    if changed_total:
        impacts.append(
            {
                "area": "maker_checker_bdd",
                "level": "review_required",
                "reason": f"{changed_total} rule-level candidate difference(s) found.",
            }
        )
    else:
        impacts.append(
            {
                "area": "maker_checker_bdd",
                "level": "no_rule_delta_detected",
                "reason": "No rule-level candidate differences were detected by deterministic comparison.",
            }
        )

    changed_rule_types = report["rule_type_distribution_delta"]
    if any(item["delta"] for item in changed_rule_types):
        impacts.append(
            {
                "area": "artifact_governance",
                "level": "review_required",
                "reason": "Rule type distribution changed between versions.",
            }
        )

    if report["rule_delta"]["source_anchor_warnings"]:
        impacts.append(
            {
                "area": "source_traceability",
                "level": "review_required",
                "reason": "One or more matching rule IDs changed source anchors.",
            }
        )
    return impacts


def distribution_delta(previous: dict[str, int], current: dict[str, int]) -> list[dict[str, Any]]:
    rows = []
    for key in sorted(set(previous) | set(current)):
        prev_count = previous.get(key, 0)
        curr_count = current.get(key, 0)
        rows.append({"value": key, "previous": prev_count, "current": curr_count, "delta": curr_count - prev_count})
    return rows


def build_report(
    previous: dict[str, Any],
    current: dict[str, Any],
    *,
    changed_threshold: float,
    match_threshold: float,
) -> dict[str, Any]:
    report = {
        "metadata": {
            "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "tool": "scripts/compare_initial_margin_versions.py",
            "comparison_mode": "generic_governed_artifact_directory_diff",
            "changed_threshold": changed_threshold,
            "match_threshold": match_threshold,
        },
        "source_versions": {
            "previous": previous["metadata"],
            "current": current["metadata"],
        },
        "artifact_inventory": compare_inventory(previous, current),
        "rule_type_distribution_delta": distribution_delta(
            count_values(previous["atomic_rules"], ("rule_type",)),
            count_values(current["atomic_rules"], ("rule_type",)),
        ),
        "semantic_rule_type_distribution_delta": distribution_delta(
            count_values(previous["semantic_rules"], ("classification", "rule_type")),
            count_values(current["semantic_rules"], ("classification", "rule_type")),
        ),
        "clause_delta": compare_clauses(previous["clauses"], current["clauses"]),
        "rule_delta": compare_rules(
            previous["atomic_rules"],
            current["atomic_rules"],
            changed_threshold=changed_threshold,
            match_threshold=match_threshold,
        ),
        "limitations": [
            "This is deterministic artifact comparison, not business interpretation.",
            "Changed candidates require human review before downstream scope decisions.",
            "Text similarity can be affected by PDF extraction differences and table layout changes.",
            "ID-drift candidates are heuristic matches and must not be treated as canonical without review.",
        ],
    }
    report["downstream_impact_candidates"] = build_downstream_impact(report)
    return report


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(lines)


def render_markdown(report: dict[str, Any], max_items: int) -> str:
    prev = report["source_versions"]["previous"]
    curr = report["source_versions"]["current"]
    rule_delta = report["rule_delta"]
    lines = [
        "# Initial Margin Version Diff Report",
        "",
        "**Status:** Deterministic candidate diff for human review",
        f"**Generated:** {report['metadata']['generated_at']}",
        "",
        "## Sources",
        "",
        markdown_table(
            ["Side", "doc_id", "doc_title", "doc_version", "artifact_count"],
            [
                ["Previous", prev.get("doc_id"), prev.get("doc_title"), prev.get("doc_version"), prev.get("atomic_rule_count")],
                ["Current", curr.get("doc_id"), curr.get("doc_title"), curr.get("doc_version"), curr.get("atomic_rule_count")],
            ],
        ),
        "",
        "## Summary",
        "",
        markdown_table(
            ["Metric", "Value"],
            [
                ["Previous atomic rules", rule_delta["previous_count"]],
                ["Current atomic rules", rule_delta["current_count"]],
                ["Rule count delta", rule_delta["delta"]],
                ["Common rule IDs", rule_delta["common_id_count"]],
                ["Unchanged common rules", rule_delta["unchanged_count"]],
                ["Changed candidates", rule_delta["changed_count"]],
                ["Added candidates", rule_delta["added_count"]],
                ["Removed candidates", rule_delta["removed_count"]],
                ["ID drift candidates", rule_delta["id_drift_candidate_count"]],
                ["Source anchor warnings", len(rule_delta["source_anchor_warnings"])],
            ],
        ),
        "",
        "## Rule Type Distribution",
        "",
        markdown_table(
            ["Rule type", "Previous", "Current", "Delta"],
            [[row["value"], row["previous"], row["current"], row["delta"]] for row in report["rule_type_distribution_delta"]],
        ),
        "",
        "## Clause Delta",
        "",
        markdown_table(
            ["Metric", "Value"],
            [
                ["Previous clauses", report["clause_delta"]["previous_count"]],
                ["Current clauses", report["clause_delta"]["current_count"]],
                ["Clause count delta", report["clause_delta"]["delta"]],
                ["Changed clause candidates", len(report["clause_delta"]["changed_clause_candidates"])],
            ],
        ),
        "",
    ]
    append_item_section(lines, "Changed Rule Candidates", rule_delta["changed_rule_candidates"], max_items)
    append_item_section(lines, "Added Rule Candidates", rule_delta["added_rule_candidates"], max_items)
    append_item_section(lines, "Removed Rule Candidates", rule_delta["removed_rule_candidates"], max_items)
    append_item_section(lines, "ID Drift Candidates", rule_delta["id_drift_candidates"], max_items)
    append_item_section(lines, "Source Anchor Warnings", rule_delta["source_anchor_warnings"], max_items)
    lines.extend(
        [
            "## Downstream Impact Candidates",
            "",
            markdown_table(
                ["Area", "Level", "Reason"],
                [[item["area"], item["level"], item["reason"]] for item in report["downstream_impact_candidates"]],
            ),
            "",
            "## Recommendation",
            "",
            recommendation_text(report),
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend([f"- {item}" for item in report["limitations"]])
    lines.append("")
    return "\n".join(lines)


def append_item_section(lines: list[str], title: str, items: list[dict[str, Any]], max_items: int) -> None:
    lines.extend([f"## {title}", ""])
    if not items:
        lines.extend(["None detected.", ""])
        return
    for item in items[:max_items]:
        item_id = item.get("rule_id") or item.get("previous_rule_id") or item.get("current_rule_id")
        lines.append(f"- `{item_id}`: {item.get('similarity', '')}")
        if item.get("text"):
            lines.append(f"  - text: {item['text']}")
        if item.get("previous_text"):
            lines.append(f"  - previous: {item['previous_text']}")
        if item.get("current_text"):
            lines.append(f"  - current: {item['current_text']}")
    if len(items) > max_items:
        lines.append(f"- ... {len(items) - max_items} more item(s) omitted from Markdown; see JSON report.")
    lines.append("")


def recommendation_text(report: dict[str, Any]) -> str:
    rule_delta = report["rule_delta"]
    changed_total = (
        rule_delta["changed_count"]
        + rule_delta["added_count"]
        + rule_delta["removed_count"]
        + rule_delta["id_drift_candidate_count"]
    )
    if changed_total == 0 and not rule_delta["source_anchor_warnings"]:
        return "No downstream bridge changes are recommended from deterministic diff alone. Human review may still confirm whether editorial version changes are acceptable."
    return (
        "Human review is required before downstream maker/checker/BDD/mock API work. "
        "Do not create or update an execution bridge until changed candidates and source-anchor warnings are reviewed."
    )


def write_report(report: dict[str, Any], json_output: Path, markdown_output: Path, max_items: int) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    markdown_output.write_text(render_markdown(report, max_items=max_items), encoding="utf-8")


def main() -> None:
    args = parse_args()
    previous = load_artifact_dir(Path(args.previous))
    current = load_artifact_dir(Path(args.current))
    report = build_report(
        previous,
        current,
        changed_threshold=args.changed_threshold,
        match_threshold=args.match_threshold,
    )
    write_report(report, Path(args.json_output), Path(args.markdown_output), max_items=args.max_items)
    print(json.dumps({
        "json_output": args.json_output,
        "markdown_output": args.markdown_output,
        "changed_rule_candidates": report["rule_delta"]["changed_count"],
        "added_rule_candidates": report["rule_delta"]["added_count"],
        "removed_rule_candidates": report["rule_delta"]["removed_count"],
        "id_drift_candidates": report["rule_delta"]["id_drift_candidate_count"],
    }, indent=2))


if __name__ == "__main__":
    main()
