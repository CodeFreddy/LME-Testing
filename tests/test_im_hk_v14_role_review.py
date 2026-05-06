from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from lme_testing.im_hk_v14_role_review import (
    RoleReviewValidationError,
    build_decision_record,
    parse_treatment_mapping,
    render_markdown_summary,
    validate_decision_record,
    write_review_package,
)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def diff_report() -> dict:
    return {
        "source_versions": {
            "previous": {"doc_id": "im_hk_v13"},
            "current": {"doc_id": "im_hk_v14"},
        },
        "rule_delta": {
            "changed_rule_candidates": [
                {
                    "rule_id": "MR-012-A-1",
                    "similarity": 0.9,
                    "previous_rule_type": "calculation",
                    "current_rule_type": "calculation",
                    "previous_anchor": {
                        "paragraph_id": "MR-012-A-1",
                        "clause_id": "MR-012",
                        "start_page": 8,
                        "end_page": 23,
                    },
                    "current_anchor": {
                        "paragraph_id": "MR-012-A-1",
                        "clause_id": "MR-012",
                        "start_page": 8,
                        "end_page": 23,
                    },
                }
            ],
            "id_drift_candidates": [
                {
                    "previous_rule_id": "MR-012-B-4",
                    "current_rule_id": "MR-012-C-2",
                    "similarity": 1.0,
                    "previous_anchor": {
                        "paragraph_id": "MR-012-B-4",
                        "clause_id": "MR-012",
                        "start_page": 23,
                        "end_page": 23,
                    },
                    "current_anchor": {
                        "paragraph_id": "MR-012-C-2",
                        "clause_id": "MR-012",
                        "start_page": 23,
                        "end_page": 23,
                    },
                }
            ],
        },
    }


MAPPING = """# Mapping

| Candidate | Diff signal | Treatment | Downstream action |
| --- | --- | --- | --- |
| `MR-012-A-1` | changed values | `requires_hkv14_validation_data_update` | Update HKv14 validation data. |
| `MR-012-B-4` → `MR-012-C-2` | id drift | `advisory_reference_only` | Preserve as advisory. |
"""


class InitialMarginHKv14RoleReviewTests(unittest.TestCase):
    def test_parse_treatment_mapping_normalizes_id_drift_arrow(self) -> None:
        mapping = parse_treatment_mapping(MAPPING)

        self.assertIn("MR-012-A-1", mapping)
        self.assertIn("MR-012-B-4 -> MR-012-C-2", mapping)
        self.assertEqual(mapping["MR-012-B-4 -> MR-012-C-2"].treatment_category, "advisory_reference_only")

    def test_build_decision_record_links_candidates_to_treatment_mapping(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            diff_path = tmp_path / "diff.json"
            mapping_path = tmp_path / "mapping.md"
            write_json(diff_path, diff_report())
            mapping_path.write_text(MAPPING, encoding="utf-8")

            record = build_decision_record(
                diff_report_path=diff_path,
                mapping_path=mapping_path,
                reviewer_role="QA Lead",
                reviewer_name="Reviewer",
                decision="approve",
                rationale="Evidence reviewed.",
                review_timestamp="20260427T000000Z",
            )

            validate_decision_record(record)
            self.assertEqual(record["review_scope"]["candidate_count"], 2)
            self.assertEqual(record["summary"]["by_decision"]["approve"], 2)
            self.assertEqual(record["open_items"], [])
            self.assertEqual(
                record["candidate_decisions"][1]["candidate_id"],
                "MR-012-B-4 -> MR-012-C-2",
            )

    def test_validation_rejects_unsupported_decision(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            diff_path = tmp_path / "diff.json"
            mapping_path = tmp_path / "mapping.md"
            write_json(diff_path, diff_report())
            mapping_path.write_text(MAPPING, encoding="utf-8")
            record = build_decision_record(diff_report_path=diff_path, mapping_path=mapping_path)
            record["candidate_decisions"][0]["decision"] = "auto_approve"

            with self.assertRaises(RoleReviewValidationError):
                validate_decision_record(record)

    def test_write_review_package_emits_canonical_json_markdown_and_html(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            diff_path = tmp_path / "diff.json"
            mapping_path = tmp_path / "mapping.md"
            output_dir = tmp_path / "runs"
            write_json(diff_path, diff_report())
            mapping_path.write_text(MAPPING, encoding="utf-8")

            result = write_review_package(
                diff_report_path=diff_path,
                mapping_path=mapping_path,
                output_dir=output_dir,
                reviewer_name="Reviewer",
                rationale="Evidence reviewed.",
            )

            record_path = Path(result["decision_record"])
            summary_path = Path(result["decision_summary"])
            html_path = Path(result["review_html"])
            self.assertTrue(record_path.exists())
            self.assertTrue(summary_path.exists())
            self.assertTrue(html_path.exists())
            record = json.loads(record_path.read_text(encoding="utf-8"))
            self.assertTrue(record["metadata"]["canonical"])
            self.assertIn("Markdown summary is derived", summary_path.read_text(encoding="utf-8"))
            self.assertIn("HKv14 Impact Decision Review", html_path.read_text(encoding="utf-8"))

    def test_markdown_export_is_derived_from_valid_record(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            diff_path = tmp_path / "diff.json"
            mapping_path = tmp_path / "mapping.md"
            write_json(diff_path, diff_report())
            mapping_path.write_text(MAPPING, encoding="utf-8")
            record = build_decision_record(diff_report_path=diff_path, mapping_path=mapping_path)

            markdown = render_markdown_summary(record)

            self.assertIn("decision_record.json", markdown)
            self.assertIn("MR-012-A-1", markdown)


if __name__ == "__main__":
    unittest.main()
