"""Audit trail generator — renders the maker → checker → human-review decision chain per rule."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_audit_trail(session_dir: Path, output_path: Path) -> dict[str, Any]:
    """Render an audit trail HTML for a review session.

    Args:
        session_dir: Path to the review session directory (contains session_manifest.json).
        output_path: Where to write the HTML file.

    Returns:
        dict with "divergent_count" (number of rules with rewrite/reject decisions).

    Raises:
        Exception: If the session manifest or critical data is missing.
    """
    manifest = _load_json(session_dir / "session_manifest.json")
    iterations = manifest.get("iterations", {})

    # Collect per-iteration data organized by semantic_rule_id
    rule_timeline: dict[str, list[dict[str, Any]]] = {}

    for iter_key in sorted(iterations.keys(), key=int):
        iter_data = iterations[iter_key]
        iteration = int(iter_key)

        # Load maker cases
        maker_cases = _load_maker_cases(Path(iter_data["maker_cases_path"]))
        # Load checker reviews (indexed by case_id)
        checker_reviews = _load_checker_reviews(iter_data.get("checker_reviews_path"))
        # Load human reviews
        human_reviews = _load_human_reviews(iter_data.get("human_reviews_latest_path"))

        for rule_record in maker_cases:
            semantic_rule_id = rule_record.get("semantic_rule_id", "unknown")
            if semantic_rule_id not in rule_timeline:
                rule_timeline[semantic_rule_id] = []

            scenarios = rule_record.get("scenarios", [])
            rule_entry = {
                "iteration": iteration,
                "rule_id": semantic_rule_id,
                "feature": rule_record.get("feature", ""),
                "scenarios": [],
            }

            for scenario in scenarios:
                case_id = scenario.get("scenario_id")
                checker = checker_reviews.get(case_id, {})
                human = human_reviews.get(case_id, {})
                rule_entry["scenarios"].append({
                    "scenario_id": case_id,
                    "case_type": scenario.get("case_type", ""),
                    "title": scenario.get("title", ""),
                    "given": scenario.get("given", []),
                    "when": scenario.get("when", []),
                    "then": scenario.get("then", []),
                    "evidence": scenario.get("evidence", []),
                    "checker": checker,
                    "human": human,
                })

            rule_timeline[semantic_rule_id].append(rule_entry)

    divergent_count = _count_divergent(rule_timeline)
    html = _render_html(rule_timeline, divergent_count)
    output_path.write_text(html, encoding="utf-8")
    return {"divergent_count": divergent_count}


def _load_json(path: Path) -> dict[str, Any]:
    if not path or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_maker_cases(path: Path | None) -> list[dict[str, Any]]:
    if not path:
        return []
    path = Path(path)
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def _load_checker_reviews(path: str | Path | None) -> dict[str, dict]:
    if not path:
        return {}
    path = Path(path)
    if not path.exists():
        return {}
    reviews = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rec = json.loads(line)
            case_id = rec.get("case_id")
            if case_id:
                reviews[case_id] = rec
    return reviews


def _load_human_reviews(path: str | Path | None) -> dict[str, dict]:
    if not path:
        return {}
    path = Path(path)
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    reviews = {}
    for rec in data.get("reviews", []):
        case_id = rec.get("case_id")
        if case_id:
            reviews[case_id] = rec
    return reviews


def _count_divergent(rule_timeline: dict[str, list[dict]]) -> int:
    count = 0
    for entries in rule_timeline.values():
        for entry in entries:
            for scenario in entry.get("scenarios", []):
                human = scenario.get("human", {})
                if human.get("review_decision") not in ("approve", "", None):
                    count += 1
                    break
    return count


def _esc(s: str | None) -> str:
    if s is None:
        return ""
    return (str(s)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;"))


def _render_scenario_block(scenario: dict, decision_cls: str) -> str:
    checker = scenario.get("checker", {})
    human = scenario.get("human", {})
    scores = checker.get("scores", {})

    evidence_items = ""
    for ev in scenario.get("evidence", []):
        quote = _esc(ev.get("quote", ""))
        page = _esc(str(ev.get("page", "")))
        ar_id = _esc(ev.get("atomic_rule_id", ""))
        evidence_items += f"<li><strong>{ar_id} (p.{page})</strong>: {quote}</li>"

    given = "".join(f"<li>{_esc(g)}</li>" for g in scenario.get("given", []))
    when = "".join(f"<li>{_esc(w)}</li>" for w in scenario.get("when", []))
    then = "".join(f"<li>{_esc(t)}</li>" for t in scenario.get("then", []))

    return f"""
        <div class="scenario">
          <div class="scenario-header">
            <span class="case-type {scenario.get('case_type', '')}">{_esc(scenario.get('case_type', ''))}</span>
            <strong>{_esc(scenario.get('title', ''))}</strong>
            <span class="case-id">{_esc(scenario.get('scenario_id', ''))}</span>
          </div>
          <div class="scenario-body">
            <div class="col">
              <h4>Given</h4><ul>{given}</ul>
              <h4>When</h4><ul>{when}</ul>
              <h4>Then</h4><ul>{then}</ul>
              <h4>Evidence</h4><ul>{evidence_items}</ul>
            </div>
            <div class="col">
              <h4>Checker</h4>
              <p>Accepted: {str(checker.get('case_type_accepted', '')).capitalize()}</p>
              <p>Coverage: {checker.get('coverage_assessment', {}).get('status', 'n/a')}</p>
              <p>Relevance: {checker.get('coverage_relevance', 'n/a')}</p>
              <p>Scores: evidence={scores.get('evidence_consistency','')}, coverage={scores.get('requirement_coverage','')}, design={scores.get('test_design_quality','')}</p>
              <p>Blocking: {str(checker.get('is_blocking', '')).capitalize()}</p>
              <h4>Human Review</h4>
              <p>Decision: <span class="decision {decision_cls}">{_esc(human.get('review_decision', 'pending'))}</span></p>
              <p>Notes: {_esc(human.get('review_notes', ''))}</p>
              <p>Findings: {len(checker.get('findings', []))} issue(s)</p>
            </div>
          </div>
        </div>"""


def _render_html(rule_timeline: dict[str, list[dict]], divergent_count: int) -> str:
    rules_html = ""
    for rule_id in sorted(rule_timeline.keys()):
        entries = rule_timeline[rule_id]
        feature = _esc(entries[0]["feature"]) if entries else ""

        iteration_blocks = ""
        for entry in entries:
            iter_num = entry["iteration"]
            scenarios_html = ""
            for scenario in entry["scenarios"]:
                human = scenario.get("human", {})
                decision = human.get("review_decision", "pending")
                decision_cls = _decision_class(decision)
                scenarios_html += _render_scenario_block(scenario, decision_cls)

            iteration_blocks += f"""
        <div class="iteration">
          <h3>Iteration {iter_num}</h3>
          {scenarios_html}
        </div>"""

        rules_html += f"""
    <div class="rule-block">
      <h2>{rule_id}: {feature}</h2>
      {iteration_blocks}
    </div>"""

    return (
        "<!DOCTYPE html>\n"
        "<html lang='en'>\n"
        "<head>\n"
        "<meta charset='utf-8'>\n"
        "<title>Audit Trail</title>\n"
        "<style>\n"
        "  body { font-family: sans-serif; margin: 2rem; background: #f9f9f9; }\n"
        "  .rule-block { background: white; border: 1px solid #ddd; border-radius: 6px; margin-bottom: 1.5rem; padding: 1rem; }\n"
        "  .rule-block h2 { margin-top: 0; font-size: 1rem; color: #333; }\n"
        "  .iteration { margin: 0.5rem 0; padding: 0.5rem; background: #f0f0f0; border-radius: 4px; }\n"
        "  .iteration h3 { margin: 0 0 0.5rem 0; font-size: 0.85rem; color: #666; }\n"
        "  .scenario { border: 1px solid #e0e0e0; border-radius: 4px; margin: 0.5rem 0; padding: 0.75rem; background: white; }\n"
        "  .scenario-header { display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.5rem; }\n"
        "  .case-type { background: #e3f2fd; padding: 2px 6px; border-radius: 3px; font-size: 0.75rem; }\n"
        "  .case-type.positive { background: #e8f5e9; }\n"
        "  .case-type.negative { background: #ffebee; }\n"
        "  .case-type.boundary { background: #fff8e1; }\n"
        "  .case-id { margin-left: auto; font-size: 0.7rem; color: #999; }\n"
        "  .scenario-body { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }\n"
        "  .scenario-body h4 { margin: 0 0 0.25rem 0; font-size: 0.75rem; color: #555; text-transform: uppercase; }\n"
        "  .scenario-body ul { margin: 0 0 0.5rem 0; padding-left: 1.25rem; font-size: 0.8rem; }\n"
        "  .scenario-body p { margin: 0.25rem 0; font-size: 0.8rem; }\n"
        "  .decision { padding: 2px 6px; border-radius: 3px; font-weight: bold; }\n"
        "  .decision.approve { background: #c8e6c9; color: #2e7d32; }\n"
        "  .decision.rewrite { background: #fff9c4; color: #f57f17; }\n"
        "  .decision.reject { background: #ffcdd2; color: #c62828; }\n"
        "  .decision.pending { background: #eceff1; color: #546e7a; }\n"
        "</style>\n"
        "</head>\n"
        "<body>\n"
        "<h1>Audit Trail"
        f" <span style='font-weight:normal;font-size:0.7rem'>— {divergent_count} divergent rule(s)</span>"
        "</h1>\n"
        f"{rules_html}\n"
        "</body>\n"
        "</html>"
    )


def _decision_class(decision: str) -> str:
    return {"approve": "approve", "rewrite": "rewrite", "reject": "reject"}.get(decision, "pending")
