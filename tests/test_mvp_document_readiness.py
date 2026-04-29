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
