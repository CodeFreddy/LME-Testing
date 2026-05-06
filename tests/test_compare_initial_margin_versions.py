from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "compare_initial_margin_versions.py"

spec = importlib.util.spec_from_file_location("compare_initial_margin_versions", SCRIPT_PATH)
compare_versions = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = compare_versions
spec.loader.exec_module(compare_versions)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def atomic(rule_id: str, text: str, rule_type: str = "calculation") -> dict:
    return {
        "rule_id": rule_id,
        "paragraph_id": rule_id,
        "clause_id": rule_id.rsplit("-", 1)[0],
        "start_page": 1,
        "end_page": 1,
        "rule_type": rule_type,
        "raw_text": text,
    }


class CompareInitialMarginVersionsTests(unittest.TestCase):
    def test_build_report_classifies_changed_added_removed_and_id_drift(self) -> None:
        previous = {
            "path": "previous",
            "metadata": {"doc_id": "old", "atomic_rule_count": 4},
            "clauses": [],
            "atomic_rules": [
                atomic("R-001", "same text"),
                atomic("R-002", "old calculation uses one amount"),
                atomic("R-003", "removed only"),
                atomic("R-004", "same text but id drift"),
            ],
            "semantic_rules": [],
            "validation_report": {},
        }
        current = {
            "path": "current",
            "metadata": {"doc_id": "new", "atomic_rule_count": 4},
            "clauses": [],
            "atomic_rules": [
                atomic("R-001", "same text"),
                atomic("R-002", "new calculation uses two amounts"),
                atomic("R-005", "added only"),
                atomic("R-999", "same text but id drift"),
            ],
            "semantic_rules": [],
            "validation_report": {},
        }

        report = compare_versions.build_report(
            previous,
            current,
            changed_threshold=0.985,
            match_threshold=0.95,
        )

        self.assertEqual(report["rule_delta"]["changed_count"], 1)
        self.assertEqual(report["rule_delta"]["added_count"], 1)
        self.assertEqual(report["rule_delta"]["removed_count"], 1)
        self.assertEqual(report["rule_delta"]["id_drift_candidate_count"], 1)

    def test_write_report_emits_json_and_markdown(self) -> None:
        report = {
            "metadata": {
                "generated_at": "2026-04-26T00:00:00Z",
                "changed_threshold": 0.985,
                "match_threshold": 0.9,
            },
            "source_versions": {
                "previous": {"doc_id": "old", "doc_title": "Old", "doc_version": "1", "atomic_rule_count": 1},
                "current": {"doc_id": "new", "doc_title": "New", "doc_version": "2", "atomic_rule_count": 1},
            },
            "rule_delta": {
                "previous_count": 1,
                "current_count": 1,
                "delta": 0,
                "common_id_count": 1,
                "unchanged_count": 1,
                "changed_count": 0,
                "added_count": 0,
                "removed_count": 0,
                "id_drift_candidate_count": 0,
                "changed_rule_candidates": [],
                "added_rule_candidates": [],
                "removed_rule_candidates": [],
                "id_drift_candidates": [],
                "source_anchor_warnings": [],
            },
            "rule_type_distribution_delta": [],
            "clause_delta": {
                "previous_count": 0,
                "current_count": 0,
                "delta": 0,
                "changed_clause_candidates": [],
            },
            "downstream_impact_candidates": [],
            "limitations": [],
        }

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            json_output = tmp_path / "out" / "diff.json"
            markdown_output = tmp_path / "out" / "diff.md"
            compare_versions.write_report(report, json_output, markdown_output, max_items=10)

            self.assertTrue(json_output.exists())
            self.assertTrue(markdown_output.exists())
            self.assertIn("Initial Margin Version Diff Report", markdown_output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
