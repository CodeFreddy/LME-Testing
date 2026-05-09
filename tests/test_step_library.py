"""Unit tests for lme_testing/step_library.py."""
from __future__ import annotations

import unittest
from pathlib import Path

from lme_testing.step_library import HKEX_API_CLIENT, HKEX_CLIENT, STEP_LIBRARY, extract_pattern


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


class HKEXStepLibraryTests(unittest.TestCase):
    """Tests that bundled step implementations target HKEX clients."""

    def test_business_transacted_step_uses_hkex_client_credentials(self) -> None:
        code = STEP_LIBRARY["business is transacted on the Exchange"].code

        self.assertIn("HKEX.Client.login", code)
        self.assertIn("HKEX_USERNAME", code)
        self.assertIn("HKEX_PASSWORD", code)
        self.assertNotIn("LME.Client.login", code)
        self.assertNotIn("LME_USERNAME", code)
        self.assertNotIn("LME_PASSWORD", code)

    def test_hkex_client_stub_is_exported_for_generated_environment(self) -> None:
        self.assertTrue(hasattr(HKEX_CLIENT, "Client"))
        self.assertTrue(hasattr(HKEX_CLIENT, "API"))
        self.assertTrue(hasattr(HKEX_CLIENT, "PostTrade"))

    def test_hkex_catalog_api_client_supports_mock_margin_endpoints(self) -> None:
        result = HKEX_API_CLIENT.post(
            "/api/margin/market-risk/aggregate",
            json={
                "components": {
                    "portfolio_margin": 10000000,
                    "flat_rate_margin": 15180000,
                    "liquidation_risk_add_on": 266865,
                    "structured_product_add_on": 550000,
                    "corporate_action_position_margin": 2500000,
                    "holiday_add_on": 18433039,
                },
                "rounding_parameter": 10000,
            },
        )

        self.assertEqual(result["aggregated_margin_before_rounding"], 46929904)
        self.assertEqual(result["rounded_aggregated_market_risk_component_margin"], 46930000)
        self.assertEqual(result["components"]["liquidation_risk_addon"], 266865)

    def test_step_sources_do_not_contain_lme_runtime_references(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]

        for relative in ("src/lme_testing/step_library.py", "src/lme_testing/bdd_export.py"):
            text = (repo_root / relative).read_text(encoding="utf-8")
            self.assertNotIn("LME", text, relative)


if __name__ == "__main__":
    unittest.main()

