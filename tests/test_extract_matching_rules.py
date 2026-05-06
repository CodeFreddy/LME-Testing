from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "extract_matching_rules.py"

spec = importlib.util.spec_from_file_location("extract_matching_rules", SCRIPT_PATH)
extract_matching_rules = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = extract_matching_rules
spec.loader.exec_module(extract_matching_rules)


class ExtractMatchingRulesTests(unittest.TestCase):
    def test_pages_to_markdown_preserves_page_headings(self) -> None:
        pages = [
            extract_matching_rules.PageText(page_number=1, text="First page text"),
            extract_matching_rules.PageText(page_number=2, text="Second page text"),
        ]

        markdown = extract_matching_rules.pages_to_markdown("Sample Document", pages)

        self.assertTrue(markdown.startswith("# Sample Document\n\n## Page 1\n"))
        self.assertIn("\n## Page 2\nSecond page text\n", markdown)

    def test_write_pdf_source_markdown_writes_output_dir_file(self) -> None:
        pages = [extract_matching_rules.PageText(page_number=1, text="Extracted PDF text")]

        with TemporaryDirectory() as tmp:
            output_path = extract_matching_rules.write_pdf_source_markdown(
                Path(tmp),
                "PDF Source",
                pages,
            )

            self.assertEqual(output_path.name, "source_from_pdf.md")
            self.assertEqual(
                output_path.read_text(encoding="utf-8"),
                "# PDF Source\n\n## Page 1\nExtracted PDF text\n",
            )


if __name__ == "__main__":
    unittest.main()
