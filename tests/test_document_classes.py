from __future__ import annotations

import unittest

from scripts.document_classes import DocumentClass, infer_rule_type


class DocumentClassTests(unittest.TestCase):
    def test_calculation_guide_formula_is_calculation(self) -> None:
        text = "The margin requirement calculation uses a formula derived from market value and risk parameters."
        self.assertEqual(infer_rule_type(text, DocumentClass.CALCULATION_GUIDE), "calculation")

    def test_calculation_guide_layout_is_data_constraint(self) -> None:
        text = "The Initial Margin Risk Parameter File is generated in csv format with required field columns."
        self.assertEqual(infer_rule_type(text, DocumentClass.CALCULATION_GUIDE), "data_constraint")

    def test_calculation_guide_table_of_contents_is_reference_only(self) -> None:
        text = "1. INTRODUCTION............................................................................................................... 4"
        self.assertEqual(infer_rule_type(text, DocumentClass.CALCULATION_GUIDE), "reference_only")


if __name__ == "__main__":
    unittest.main()
