from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from lme_testing.mvp_document_readiness import (
    DocumentReadinessValidationError,
    build_document_record,
    build_hkv14_poc_registry,
    validate_document_readiness,
    write_document_readiness_package,
)


class MVPDocumentReadinessTests(unittest.TestCase):
    def test_valid_registry_generation_registers_sources_hashes_and_supersedes(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            previous = tmp_path / "Initial Margin Calculation Guide HKv13.pdf"
            current = tmp_path / "Initial Margin Calculation Guide HKv14.pdf"
            previous.write_bytes(b"hkv13")
            current.write_bytes(b"hkv14")

            registry = build_hkv14_poc_registry(
                previous_spec_path=previous,
                current_spec_path=current,
                generated_at="20260429T000000Z",
            )

            validate_document_readiness(registry)
            self.assertEqual(registry["metadata"]["task_id"], "S2-F2")
            self.assertEqual(registry["readiness_summary"]["document_count"], 4)
            self.assertEqual(registry["readiness_summary"]["existing_source_count"], 2)
            previous_record = registry["documents"][0]
            current_record = registry["documents"][1]
            self.assertTrue(previous_record["source_exists"])
            self.assertTrue(current_record["source_exists"])
            self.assertTrue(previous_record["checksum"])
            self.assertTrue(current_record["checksum"])
            self.assertEqual(current_record["supersedes"], "im_hk_v13_function_spec")
            self.assertEqual(registry["relationships"][0]["relationship_type"], "supersedes")

    def test_placeholder_documents_are_visible_blockers(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            previous = tmp_path / "old.pdf"
            current = tmp_path / "new.pdf"
            previous.write_bytes(b"old")
            current.write_bytes(b"new")

            registry = build_hkv14_poc_registry(
                previous_spec_path=previous,
                current_spec_path=current,
                generated_at="20260429T000001Z",
            )

            placeholder_roles = {
                document["document_role"]
                for document in registry["documents"]
                if document["readiness_state"] == "placeholder"
            }
            blocker_roles = {blocker["document_role"] for blocker in registry["blockers"]}
            self.assertEqual(placeholder_roles, {"test_plan", "regression_pack_index"})
            self.assertEqual(placeholder_roles, blocker_roles)
            self.assertEqual(registry["readiness_summary"]["overall_readiness"], "blocked")

    def test_real_test_plan_and_regression_pack_index_can_make_registry_ready(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            previous = tmp_path / "old.pdf"
            current = tmp_path / "new.pdf"
            test_plan = tmp_path / "test_plan.md"
            regression_pack = tmp_path / "regression_pack.md"
            previous.write_bytes(b"old")
            current.write_bytes(b"new")
            test_plan.write_text(
                "\n".join(
                    [
                        "Objective: validate Initial Margin HKv14 changes.",
                        "Target system: Initial Margin domain application.",
                        "Function spec version: HKv14.",
                        "In scope test types: functional and regression.",
                        "Out of scope: external integrations.",
                        "QA owner approver: QA Lead.",
                        "Revision version: TP-1.",
                    ]
                ),
                encoding="utf-8",
            )
            regression_pack.write_text(
                "\n".join(
                    [
                        "Regression pack identifier: IM-HK.",
                        "Target system: Initial Margin domain application.",
                        "Release baseline version: HKv14.",
                        "Suite scenario script case list: IM-001, IM-002.",
                        "Automation Lead owner and maintainer: Automation Lead.",
                        "Revision version: RP-1.",
                        "Automation coverage: partial and visible.",
                    ]
                ),
                encoding="utf-8",
            )

            registry = build_hkv14_poc_registry(
                previous_spec_path=previous,
                current_spec_path=current,
                test_plan_path=test_plan,
                test_plan_version="TP-1",
                regression_pack_index_path=regression_pack,
                regression_pack_index_version="RP-1",
                generated_at="20260429T000003Z",
            )

            validate_document_readiness(registry)
            self.assertEqual(registry["readiness_summary"]["overall_readiness"], "ready")
            self.assertEqual(registry["blockers"], [])
            by_role = {document["document_role"]: document for document in registry["documents"]}
            self.assertEqual(by_role["test_plan"]["document_id"], "mvp_test_plan")
            self.assertEqual(by_role["test_plan"]["readiness_state"], "ready")
            self.assertEqual(by_role["regression_pack_index"]["document_id"], "mvp_regression_pack_index")
            self.assertEqual(by_role["regression_pack_index"]["readiness_state"], "ready")

    def test_real_input_with_incomplete_content_is_blocked(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            previous = tmp_path / "old.pdf"
            current = tmp_path / "new.pdf"
            test_plan = tmp_path / "test_plan.md"
            regression_pack = tmp_path / "regression_pack.md"
            previous.write_bytes(b"old")
            current.write_bytes(b"new")
            test_plan.write_text("Objective only.", encoding="utf-8")
            regression_pack.write_text("Regression pack only.", encoding="utf-8")

            registry = build_hkv14_poc_registry(
                previous_spec_path=previous,
                current_spec_path=current,
                test_plan_path=test_plan,
                test_plan_version="TP-1",
                regression_pack_index_path=regression_pack,
                regression_pack_index_version="RP-1",
                generated_at="20260429T000004Z",
            )

            validate_document_readiness(registry)
            self.assertEqual(registry["readiness_summary"]["overall_readiness"], "blocked")
            blocker_roles = {blocker["document_role"] for blocker in registry["blockers"]}
            self.assertEqual(blocker_roles, {"test_plan", "regression_pack_index"})
            self.assertTrue(any("Missing minimum content expectations" in blocker["notes"] for blocker in registry["blockers"]))

    def test_real_input_missing_source_is_blocked_not_placeholder(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            previous = tmp_path / "old.pdf"
            current = tmp_path / "new.pdf"
            previous.write_bytes(b"old")
            current.write_bytes(b"new")

            registry = build_hkv14_poc_registry(
                previous_spec_path=previous,
                current_spec_path=current,
                test_plan_path=tmp_path / "missing_test_plan.md",
                test_plan_version="TP-1",
                generated_at="20260429T000005Z",
            )

            by_role = {document["document_role"]: document for document in registry["documents"]}
            self.assertEqual(by_role["test_plan"]["readiness_state"], "blocked")
            self.assertEqual(by_role["test_plan"]["document_id"], "mvp_test_plan")
            self.assertFalse(by_role["test_plan"]["source_exists"])
            self.assertEqual(by_role["regression_pack_index"]["readiness_state"], "placeholder")

    def test_missing_source_marked_ready_is_rejected(self) -> None:
        record = build_document_record(
            document_id="missing_ready",
            title="Missing Ready",
            version="1",
            document_class="Function Spec",
            document_role="function_spec_previous",
            source_path=Path("does/not/exist.pdf"),
            owner_role="BA",
            status="registered",
            readiness_state="ready",
        )
        registry = {
            "metadata": {},
            "workflow_instance": {},
            "documents": [record],
            "relationships": [],
            "readiness_summary": {},
            "blockers": [],
            "limitations": [],
        }

        with self.assertRaises(DocumentReadinessValidationError):
            validate_document_readiness(registry)

    def test_validation_rejects_unsupported_role_and_state(self) -> None:
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.pdf"
            source.write_bytes(b"source")
            record = build_document_record(
                document_id="bad_role",
                title="Bad Role",
                version="1",
                document_class="Function Spec",
                document_role="future_contract",
                source_path=source,
                owner_role="BA",
                status="registered",
                readiness_state="ready",
            )
            registry = {
                "metadata": {},
                "workflow_instance": {},
                "documents": [record],
                "relationships": [],
                "readiness_summary": {},
                "blockers": [],
                "limitations": [],
            }
            with self.assertRaises(DocumentReadinessValidationError):
                validate_document_readiness(registry)

            record["document_role"] = "function_spec_previous"
            record["readiness_state"] = "almost_ready"
            with self.assertRaises(DocumentReadinessValidationError):
                validate_document_readiness(registry)

    def test_write_package_emits_canonical_json_and_summary(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            previous = tmp_path / "old.pdf"
            current = tmp_path / "new.pdf"
            output_dir = tmp_path / "evidence"
            previous.write_bytes(b"old")
            current.write_bytes(b"new")

            result = write_document_readiness_package(
                output_dir=output_dir,
                previous_spec_path=previous,
                current_spec_path=current,
                generated_at="20260429T000002Z",
            )

            registry_path = Path(result["document_readiness"])
            summary_path = Path(result["document_readiness_summary"])
            self.assertTrue(registry_path.exists())
            self.assertTrue(summary_path.exists())
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            self.assertTrue(registry["metadata"]["canonical"])
            self.assertIn("document_readiness.json", summary_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
