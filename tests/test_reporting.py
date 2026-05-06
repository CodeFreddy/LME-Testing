from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lme_testing.reporting import generate_html_report


class ReportingTests(unittest.TestCase):
    def test_report_renders_compare_and_audit_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            maker_cases_path = base / "maker_cases.jsonl"
            checker_reviews_path = base / "checker_reviews.jsonl"
            maker_summary_path = base / "maker_summary.json"
            checker_summary_path = base / "checker_summary.json"
            coverage_report_path = base / "coverage_report.json"
            output_html_path = base / "report" / "report.html"
            compare_path = base / "compare.html"

            maker_cases_path.write_text(
                json.dumps(
                    {
                        "semantic_rule_id": "SR-1",
                        "requirement_ids": ["AR-1"],
                        "feature": "Feature",
                        "scenarios": [
                            {
                                "scenario_id": "TC-1",
                                "title": "Case",
                                "case_type": "positive",
                                "given": [],
                                "when": [],
                                "then": [],
                                "assumptions": [],
                                "evidence": [],
                            }
                        ],
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            checker_reviews_path.write_text(
                json.dumps(
                    {
                        "case_id": "TC-1",
                        "semantic_rule_id": "SR-1",
                        "overall_status": "pass",
                        "coverage_assessment": {"status": "covered"},
                        "findings": [],
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            maker_summary_path.write_text(json.dumps({"processed_rule_count": 1, "scenario_count": 1}), encoding="utf-8")
            checker_summary_path.write_text(json.dumps({"review_count": 1}), encoding="utf-8")
            coverage_report_path.write_text(
                json.dumps(
                    {
                        "total_requirements": 1,
                        "fully_covered": 1,
                        "partially_covered": 0,
                        "uncovered": 0,
                        "not_applicable": 0,
                        "coverage_percent": 100,
                        "status_by_rule": {
                            "SR-1": {
                                "paragraph_ids": [],
                                "rule_type": "permission",
                                "rule_coverage_status": "fully_covered",
                                "rule_pass_status": "pass",
                                "required_case_types": ["positive"],
                                "present_case_types": ["positive"],
                                "accepted_case_types": ["positive"],
                                "missing_case_types": [],
                            }
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            compare_path.write_text("<html>compare</html>", encoding="utf-8")

            generate_html_report(
                maker_cases_path=maker_cases_path,
                checker_reviews_path=checker_reviews_path,
                maker_summary_path=maker_summary_path,
                checker_summary_path=checker_summary_path,
                coverage_report_path=coverage_report_path,
                output_html_path=output_html_path,
                audit_trail_url="/files?path=audit",
                compare_links=[{"label": "Iteration 0 Compare", "path": str(compare_path)}],
            )

            report_html = output_html_path.read_text(encoding="utf-8")
            maker_html = output_html_path.with_name("maker_readable.html").read_text(encoding="utf-8")
            checker_html = output_html_path.with_name("checker_readable.html").read_text(encoding="utf-8")

            self.assertIn("Iteration 0 Compare", report_html)
            self.assertIn("Audit Trail", report_html)
            self.assertIn("/files?path=audit", maker_html)
            self.assertIn("Checker", checker_html)


if __name__ == "__main__":
    unittest.main()
