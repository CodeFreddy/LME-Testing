from __future__ import annotations

import base64
import importlib.util
import json
import shutil
import unittest
import zipfile
from pathlib import Path

from lme_testing.config import ProjectConfig, ProviderConfig, RoleDefaults
from lme_testing.rule_extraction import (
    decode_pdf_text_output,
    extract_pages_from_docx,
    extract_pages_from_pdf_with_pypdf,
    extract_rule_artifacts,
    fix_pdf_text_artifacts,
)
from lme_testing.rule_workflow_session import RuleWorkflowSessionManager


WORK_TMP = Path(".tmp_rule_extraction_review")


def make_config() -> ProjectConfig:
    provider = ProviderConfig(
        name="stub",
        provider_type="stub",
        model="stub-model",
        base_url="http://stub",
        api_key="stub",
    )
    return ProjectConfig(
        providers={"stub": provider},
        roles={"maker": "stub", "checker": "stub", "planner": "stub"},
        output_root=Path("runs"),
        maker_defaults=RoleDefaults(),
        checker_defaults=RoleDefaults(),
    )


def sample_hkex_markdown() -> str:
    return """## Page 15

3.2.4.2 Flat Rate Margin

Flat rate margin is calculated according to the steps as follows:

Step 1: Aggregate absolute market value of long positions and absolute market value of short positions separately.
Step 2: Sum the product of absolute position market value and the flat margin rate.
Step 3: Apply flat rate margin multiplier.

3.2.4.3 Liquidation Risk Add-on ("LRA")

This section is not in the demo allow-list.

## Page 20

3.2.5.1 Rounding on Aggregated Market-risk-component Margin

Aggregated market-risk-component margin = Portfolio margin + Flat rate margin.

3.2.5.2 Consideration on Favorable MTM

Favorable MTM (or MTM requirement) = Market value Portfolio - Contract value Portfolio.

3.2.5.3 Application of Margin Credit

Net margin after credit = Maximum [0 , (Net margin - Margin credit)].

3.2.6 Calculate or Retrieve Other Risk Components from Report

Skip this section.

## Page 22

3.2.8 Derive Total MTM and Margin Requirement from Results under §3.2.5 & §3.2.6

Total MTM and margin requirement = Net margin after credit + Other risk components.
"""


class RuleExtractionReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        if WORK_TMP.exists():
            shutil.rmtree(WORK_TMP)
        WORK_TMP.mkdir()

    def tearDown(self) -> None:
        if WORK_TMP.exists():
            shutil.rmtree(WORK_TMP)

    def test_extract_rule_artifacts_selects_hkex_core_sections(self) -> None:
        source = WORK_TMP / "hkex.md"
        source.write_text(sample_hkex_markdown(), encoding="utf-8")
        output = WORK_TMP / "artifacts"

        result = extract_rule_artifacts(
            source_path=source,
            output_dir=output,
            doc_id="im_hk_v14",
            doc_title="Initial Margin Calculation Guide HKv14",
            doc_version="HKv14",
        )

        self.assertEqual(result["semantic_rule_count"], 5)
        semantic_rules = json.loads((output / "semantic_rules.json").read_text(encoding="utf-8"))
        self.assertTrue(all(rule["classification"]["rule_type"] == "calculation" for rule in semantic_rules))
        self.assertIn("source_block_id", semantic_rules[0]["source"])
        self.assertIn("Flat Rate Margin", semantic_rules[0]["source"]["section"])

    def test_pdf_text_decoder_preserves_section_references(self) -> None:
        decoded = decode_pdf_text_output(b"See \xa73.2.5.2 for details.")
        self.assertIn("\u00a73.2.5.2", decoded)
        cleaned = fix_pdf_text_artifacts("See \ufffd3.2.5.2 for details.")
        self.assertEqual(cleaned, "See \u00a73.2.5.2 for details.")
        symbol_font_cleaned = fix_pdf_text_artifacts("See \u222b3.2.5.2 for details.")
        self.assertEqual(symbol_font_cleaned, "See \u00a73.2.5.2 for details.")

    def test_pypdf_extractor_reads_hkv14_pdf_without_pdftotext(self) -> None:
        if importlib.util.find_spec("pypdf") is None:
            self.skipTest("pypdf is not installed in the current test environment.")
        pdf_path = Path("docs/materials/Initial Margin Calculation Guide HKv14.pdf")
        if not pdf_path.exists():
            self.skipTest("HKv14 PDF fixture is not available in the current checkout.")
        pages = extract_pages_from_pdf_with_pypdf(pdf_path)

        self.assertGreaterEqual(len(pages), 30)
        self.assertTrue(any("3.2.4.2" in page.text for page in pages))

    def test_docx_text_extraction_reads_paragraphs_and_tables(self) -> None:
        docx = WORK_TMP / "sample.docx"
        document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>3.2.4.2 Flat Rate Margin</w:t></w:r></w:p>
    <w:tbl>
      <w:tr><w:tc><w:p><w:r><w:t>Field</w:t></w:r></w:p></w:tc><w:tc><w:p><w:r><w:t>Value</w:t></w:r></w:p></w:tc></w:tr>
    </w:tbl>
  </w:body>
</w:document>"""
        with zipfile.ZipFile(docx, "w") as archive:
            archive.writestr("word/document.xml", document_xml)

        pages = extract_pages_from_docx(docx)

        self.assertEqual(len(pages), 1)
        self.assertIn("3.2.4.2 Flat Rate Margin", pages[0].text)
        self.assertIn("| Field | Value |", pages[0].text)

    def test_rule_workflow_manager_saves_review_and_history(self) -> None:
        manager = RuleWorkflowSessionManager(
            config=make_config(),
            repo_root=Path.cwd(),
            output_root=WORK_TMP / "sessions",
            host="127.0.0.1",
            port=0,
        )
        encoded = base64.b64encode(sample_hkex_markdown().encode("utf-8")).decode("ascii")
        manager.upload_source(
            {
                "filename": "Initial Margin Calculation Guide HKv14.md",
                "content_base64": encoded,
                "doc_id": "im_hk_v14",
                "doc_title": "Initial Margin Calculation Guide HKv14",
                "doc_version": "HKv14",
            }
        )
        manager.extract_current({})
        payload = manager.rules_payload()
        self.assertTrue(payload["has_rules"])

        rules = payload["semantic_rules"]
        rules[0]["statement"]["action"]["value"] = "calculate_flat_rate_margin"
        result = manager.save_rules({"atomic_rules": payload["atomic_rules"], "semantic_rules": rules})

        self.assertEqual(result["status"], "saved")
        self.assertEqual(result["diff_count"], 1)
        self.assertEqual(result["semantic_diff_count"], 1)
        self.assertEqual(result["atomic_diff_count"], 0)
        self.assertEqual(result["history_snapshot"]["display_label"], "Iteration 2")
        history_response = manager.history_payload()
        history = history_response["history"]
        self.assertGreaterEqual(len(history), 2)
        self.assertEqual([item["display_label"] for item in history[:2]], ["Iteration 2", "Iteration 1"])
        self.assertEqual(history[0]["status_label"], "Saved review edits")
        self.assertEqual(history_response["pagination"]["page_size"], 10)

    def test_history_uses_source_hash_across_metadata_and_filename_changes(self) -> None:
        content = sample_hkex_markdown().encode("utf-8")
        encoded = base64.b64encode(content).decode("ascii")
        first = RuleWorkflowSessionManager(
            config=make_config(),
            repo_root=Path.cwd(),
            output_root=WORK_TMP / "sessions",
            host="127.0.0.1",
            port=0,
        )
        first.upload_source(
            {
                "filename": "Initial Margin Calculation Guide HKv14.md",
                "content_base64": encoded,
                "doc_id": "im_hk_v14",
                "doc_title": "Initial Margin Calculation Guide HKv14",
                "doc_version": "HKv14",
            }
        )
        first.extract_current({})

        second = RuleWorkflowSessionManager(
            config=make_config(),
            repo_root=Path.cwd(),
            output_root=WORK_TMP / "sessions",
            host="127.0.0.1",
            port=0,
        )
        second.upload_source(
            {
                "filename": "renamed-demo-source.md",
                "content_base64": encoded,
                "doc_id": "different_doc_id",
                "doc_title": "Different Title",
                "doc_version": "Different Version",
            }
        )
        second.extract_current({})
        history = second.history_payload()["history"]

        self.assertGreaterEqual(len(history), 2)
        self.assertEqual(
            {item["source_hash"] for item in history},
            {second.current_metadata["source_hash"]},
        )
        self.assertIn("Initial_Margin_Calculation_Guide_HKv14.md", {item.get("source_filename") for item in history})
        self.assertIn("renamed-demo-source.md", {item.get("source_filename") for item in history})

    def test_history_detail_loads_rules_and_apply_updates_current_rules(self) -> None:
        manager = RuleWorkflowSessionManager(
            config=make_config(),
            repo_root=Path.cwd(),
            output_root=WORK_TMP / "sessions",
            host="127.0.0.1",
            port=0,
        )
        encoded = base64.b64encode(sample_hkex_markdown().encode("utf-8")).decode("ascii")
        manager.upload_source(
            {
                "filename": "Initial Margin Calculation Guide HKv14.md",
                "content_base64": encoded,
                "doc_id": "im_hk_v14",
                "doc_title": "Initial Margin Calculation Guide HKv14",
                "doc_version": "HKv14",
            }
        )
        manager.extract_current({})
        payload = manager.rules_payload()
        edited_rules = copy_json(payload["semantic_rules"])
        edited_rules[0]["statement"]["action"]["value"] = "human_reviewed_action"
        save_result = manager.save_rules(
            {"atomic_rules": payload["atomic_rules"], "semantic_rules": edited_rules}
        )
        attempt_id = save_result["history_snapshot"]["attempt_id"]
        detail = manager.history_detail(attempt_id)

        self.assertEqual(detail["manifest"]["display_label"], "Iteration 2")
        self.assertEqual(detail["semantic_rules"][0]["statement"]["action"]["value"], "human_reviewed_action")
        fresh_rules = copy_json(manager.original_semantic_rules)
        manager.save_rules({"atomic_rules": manager.original_atomic_rules, "semantic_rules": fresh_rules})
        apply_result = manager.apply_history({"attempt_id": attempt_id})

        self.assertEqual(apply_result["status"], "applied")
        self.assertEqual(apply_result["applied_from_label"], "Iteration 2")
        self.assertEqual(
            manager.current_semantic_rules[0]["statement"]["action"]["value"],
            "human_reviewed_action",
        )
        self.assertEqual(apply_result["history_snapshot"]["status"], "history_applied")
        self.assertEqual(apply_result["history_snapshot"]["status_label"], "Applied history version")
        current_payload = manager.rules_payload()
        self.assertTrue(current_payload["semantic_rules"][0]["_review"]["edited"])
        self.assertEqual(
            current_payload["semantic_rules"][0]["_review"]["basis"],
            "applied_history_snapshot",
        )

    def test_business_form_payload_saves_to_rule_json(self) -> None:
        manager = RuleWorkflowSessionManager(
            config=make_config(),
            repo_root=Path.cwd(),
            output_root=WORK_TMP / "sessions",
            host="127.0.0.1",
            port=0,
        )
        encoded = base64.b64encode(sample_hkex_markdown().encode("utf-8")).decode("ascii")
        manager.upload_source(
            {
                "filename": "Initial Margin Calculation Guide HKv14.md",
                "content_base64": encoded,
                "doc_id": "im_hk_v14",
                "doc_title": "Initial Margin Calculation Guide HKv14",
                "doc_version": "HKv14",
            }
        )
        manager.extract_current({})
        payload = manager.rules_payload()
        atomic_rules = copy_json(payload["atomic_rules"])
        semantic_rules = copy_json(payload["semantic_rules"])
        atomic_rules[0]["raw_text"] = "Business edited atomic split text"
        atomic_rules[0]["review_note"] = "Atomic note from reviewer"
        semantic_rules[0]["test_design_hints"]["gherkin_intent"] = "Business edited summary"
        semantic_rules[0]["statement"]["conditions"] = [
            {
                "id": "C1",
                "kind": "document_context",
                "field": "business_condition",
                "operator": "describes",
                "value": "Only apply for eligible portfolios",
                "source_type": "human_review",
            }
        ]
        semantic_rules[0]["execution_mapping"]["business_inputs"] = ["position_market_value"]
        semantic_rules[0]["review"]["reviewer_notes"] = "Semantic note from reviewer"
        manager.save_rules({"atomic_rules": atomic_rules, "semantic_rules": semantic_rules})

        reviewed_atomic = json.loads(manager._reviewed_atomic_path().read_text(encoding="utf-8"))
        reviewed_semantic = json.loads(manager._reviewed_semantic_path().read_text(encoding="utf-8"))
        self.assertEqual(reviewed_atomic[0]["raw_text"], "Business edited atomic split text")
        self.assertEqual(reviewed_atomic[0]["review_note"], "Atomic note from reviewer")
        self.assertEqual(reviewed_semantic[0]["test_design_hints"]["gherkin_intent"], "Business edited summary")
        self.assertEqual(reviewed_semantic[0]["statement"]["conditions"][0]["value"], "Only apply for eligible portfolios")
        self.assertEqual(reviewed_semantic[0]["execution_mapping"]["business_inputs"], ["position_market_value"])
        self.assertEqual(reviewed_semantic[0]["review"]["reviewer_notes"], "Semantic note from reviewer")

    def test_atomic_rule_edit_is_tracked_as_rule_split_change(self) -> None:
        manager = RuleWorkflowSessionManager(
            config=make_config(),
            repo_root=Path.cwd(),
            output_root=WORK_TMP / "sessions",
            host="127.0.0.1",
            port=0,
        )
        encoded = base64.b64encode(sample_hkex_markdown().encode("utf-8")).decode("ascii")
        manager.upload_source(
            {
                "filename": "Initial Margin Calculation Guide HKv14.md",
                "content_base64": encoded,
                "doc_id": "im_hk_v14",
                "doc_title": "Initial Margin Calculation Guide HKv14",
                "doc_version": "HKv14",
            }
        )
        manager.extract_current({})
        payload = manager.rules_payload()
        atomic_rules = copy_json(payload["atomic_rules"])
        atomic_rules[0]["testability"] = "partially_testable"
        result = manager.save_rules(
            {"atomic_rules": atomic_rules, "semantic_rules": payload["semantic_rules"]}
        )

        self.assertEqual(result["diff_count"], 1)
        self.assertEqual(result["semantic_diff_count"], 0)
        self.assertEqual(result["atomic_diff_count"], 1)
        refreshed = manager.rules_payload()
        self.assertTrue(refreshed["atomic_rules"][0]["_review"]["edited"])
        self.assertEqual(refreshed["atomic_rules"][0]["_review"]["diff"]["rule_id"], atomic_rules[0]["rule_id"])
        latest = manager.history_payload()["history"][0]
        self.assertEqual(latest["atomic_edited_rule_count"], 1)
        detail = manager.history_detail(latest["attempt_id"])
        self.assertEqual(detail["diff"]["atomic_diffs"][0]["rule_id"], atomic_rules[0]["rule_id"])

    def test_history_is_descending_and_paginated_with_stable_iteration_numbers(self) -> None:
        manager = make_extracted_manager(WORK_TMP)
        for _ in range(11):
            manager._write_history_snapshot("reviewed")

        first_page = manager.history_payload()
        second_page = manager.history_payload(page=2, page_size=10)

        self.assertEqual(first_page["pagination"]["total"], 12)
        self.assertEqual(first_page["pagination"]["total_pages"], 2)
        self.assertEqual(first_page["history"][0]["display_label"], "Iteration 12")
        self.assertEqual(first_page["history"][-1]["display_label"], "Iteration 3")
        self.assertEqual([item["display_label"] for item in second_page["history"]], ["Iteration 2", "Iteration 1"])

    def test_apply_unedited_history_snapshot_clears_review_badges(self) -> None:
        manager = make_extracted_manager(WORK_TMP)
        extracted_attempt_id = manager.history_payload()["history"][0]["attempt_id"]
        payload = manager.rules_payload()
        edited_rules = copy_json(payload["semantic_rules"])
        edited_rules[0]["statement"]["action"]["value"] = "human_reviewed_action"
        manager.save_rules({"atomic_rules": payload["atomic_rules"], "semantic_rules": edited_rules})

        apply_result = manager.apply_history({"attempt_id": extracted_attempt_id})
        current_payload = apply_result["review_payload"]

        self.assertEqual(apply_result["semantic_diff_count"], 0)
        self.assertFalse(current_payload["semantic_rules"][0]["_review"]["edited"])
        self.assertEqual(
            current_payload["semantic_rules"][0]["_review"]["basis"],
            "applied_history_snapshot",
        )
        self.assertFalse(current_payload["atomic_rules"][0]["_review"]["edited"])
        applied_detail = manager.history_detail(apply_result["history_snapshot"]["attempt_id"])
        self.assertEqual(applied_detail["diff"]["diffs"], [])
        self.assertEqual(applied_detail["diff"]["atomic_diffs"], [])


def copy_json(value):
    return json.loads(json.dumps(value, ensure_ascii=False))


def make_extracted_manager(work_tmp: Path) -> RuleWorkflowSessionManager:
    manager = RuleWorkflowSessionManager(
        config=make_config(),
        repo_root=Path.cwd(),
        output_root=work_tmp / "sessions",
        host="127.0.0.1",
        port=0,
    )
    encoded = base64.b64encode(sample_hkex_markdown().encode("utf-8")).decode("ascii")
    manager.upload_source(
        {
            "filename": "Initial Margin Calculation Guide HKv14.md",
            "content_base64": encoded,
            "doc_id": "im_hk_v14",
            "doc_title": "Initial Margin Calculation Guide HKv14",
            "doc_version": "HKv14",
        }
    )
    manager.extract_current({})
    return manager


if __name__ == "__main__":
    unittest.main()
