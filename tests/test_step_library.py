"""Unit tests for lme_testing/step_library.py."""
from __future__ import annotations

import unittest

from lme_testing.step_library import extract_pattern


class ExtractPatternTests(unittest.TestCase):
    """Tests for extract_pattern()."""

    def test_converts_stopwords(self) -> None:
        # a, an, the should become non-capturing alternation
        result = extract_pattern("the member submits an order")
        self.assertEqual(result, "(?:a|an|the) member submits (?:a|an|the) order")

    def test_converts_numbers(self) -> None:
        result = extract_pattern("order quantity is 25")
        self.assertEqual(result, "order quantity is (\\d+)")

    def test_preserves_literal_text(self) -> None:
        result = extract_pattern("I navigate to the page")
        self.assertEqual(result, "i navigate to (?:a|an|the) page")

    def test_converts_multiple_numbers(self) -> None:
        result = extract_pattern("order 123 for quantity 456")
        self.assertEqual(result, "order (\\d+) for quantity (\\d+)")

    def test_no_stopwords_unchanged(self) -> None:
        result = extract_pattern("login to system")
        self.assertEqual(result, "login to system")

    def test_case_insensitive_stopwords(self) -> None:
        result = extract_pattern("THE member submits AN order")
        self.assertEqual(result, "(?:a|an|the) member submits (?:a|an|the) order")


if __name__ == "__main__":
    unittest.main()
