#!/usr/bin/env python
"""Generate a trend report from multiple coverage reports (Phase 2 Gate 6).

Usage:
    # Compare two runs:
    python scripts/generate_trend_report.py \
        --current runs/checker/<run_id>/coverage_report.json \
        --previous runs/checker/<previous_run_id>/coverage_report.json \
        --output runs/trends/latest_drift.json

    # Scan runs directory for all checker coverage reports and compare sequentially:
    python scripts/generate_trend_report.py \
        --runs-dir runs/checker \
        --output runs/trends/trend_report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add scripts dir to path for governance_checks import
sys.path.insert(0, str(Path(__file__).resolve().parent))

from governance_checks import REPO_ROOT


def load_coverage(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def compute_pairwise_drift(reports: list[dict]) -> list[dict]:
    """Compute drift between consecutive coverage reports."""
    drifts = []
    for i in range(1, len(reports)):
        prev = reports[i - 1]
        curr = reports[i]
        delta_pct = round(
            curr.get("coverage_percent", 0) - prev.get("coverage_percent", 0), 2
        )
        current_status = curr.get("status_by_rule", {})
        previous_status = prev.get("status_by_rule", {})

        status_weight = {"fully_covered": 3, "partially_covered": 2, "uncovered": 1, "not_applicable": 0}
        improved, regressed, new = [], [], []

        for rule_id, item in current_status.items():
            curr_status = item.get("rule_coverage_status", "")
            prev_item = previous_status.get(rule_id, {})
            prev_status = prev_item.get("rule_coverage_status", "")

            if rule_id not in previous_status:
                new.append(rule_id)
            elif status_weight.get(curr_status, 0) > status_weight.get(prev_status, 0):
                improved.append(rule_id)
            elif status_weight.get(curr_status, 0) < status_weight.get(prev_status, 0):
                regressed.append(rule_id)

        drifts.append({
            "from_run": prev.get("run_id", ""),
            "to_run": curr.get("run_id", ""),
            "from_coverage": prev.get("coverage_percent", 0),
            "to_coverage": curr.get("coverage_percent", 0),
            "coverage_delta": delta_pct,
            "improved": improved,
            "regressed": regressed,
            "new": new,
            "improved_count": len(improved),
            "regressed_count": len(regressed),
            "new_count": len(new),
        })
    return drifts


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate trend/drift report from coverage reports.")
    parser.add_argument("--current", type=Path, help="Path to current coverage_report.json")
    parser.add_argument("--previous", type=Path, help="Path to previous coverage_report.json")
    parser.add_argument("--runs-dir", type=Path, help="Directory of checker runs to compare sequentially")
    parser.add_argument("--output", type=Path, default=Path("runs/trends/trend_report.json"),
                        help="Output path for trend report")
    args = parser.parse_args()

    if args.runs_dir:
        # Scan all coverage_report.json in checker runs directory
        runs_dir: Path = args.runs_dir
        if not runs_dir.is_absolute():
            runs_dir = REPO_ROOT / runs_dir

        coverage_files = sorted(
            [
                (d.name, d / "coverage_report.json")
                for d in runs_dir.iterdir()
                if d.is_dir() and (d / "coverage_report.json").exists()
            ]
        )
        if not coverage_files:
            print("No coverage reports found.")
            return 1

        reports = [{"run_id": name, **load_coverage(path)}
                   for name, path in coverage_files]
        drifts = compute_pairwise_drift(reports)

        trend = {
            "runs": [{"run_id": r["run_id"], "coverage_percent": r["coverage_percent"]} for r in reports],
            "drifts": drifts,
            "summary": {
                "total_runs": len(reports),
                "total_improved": sum(d.get("improved_count", 0) for d in drifts),
                "total_regressed": sum(d.get("regressed_count", 0) for d in drifts),
                "overall_delta": round(
                    reports[-1].get("coverage_percent", 0) - reports[0].get("coverage_percent", 0), 2
                ) if len(reports) > 1 else 0.0,
            }
        }
    elif args.current and args.previous:
        current = {"run_id": args.current.stem, **load_coverage(args.current)}
        previous = {"run_id": args.previous.stem, **load_coverage(args.previous)}
        from lme_testing.pipelines import calculate_drift  # type: ignore
        drift = calculate_drift(current, previous)
        trend = {
            "current_run": {"run_id": current["run_id"], "coverage_percent": current["coverage_percent"]},
            "previous_run": {"run_id": previous["run_id"], "coverage_percent": previous["coverage_percent"]},
            "drift": drift,
        }
    else:
        parser.print_help()
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(trend, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Trend report written to: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
