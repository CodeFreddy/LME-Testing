"""Unit tests for lme_testing/providers.py."""
from __future__ import annotations

import json
import unittest

from lme_testing.config import ProviderConfig
from lme_testing import providers


def _stub_config() -> ProviderConfig:
    return ProviderConfig(
        name="stub",
        provider_type="stub",
        model="stub-model",
        base_url="https://stub.example.com",
        api_key="stub",
    )


def _openai_config() -> ProviderConfig:
    return ProviderConfig(
        name="test-openai",
        provider_type="openai_compatible",
        model="test-model",
        base_url="https://api.example.com",
        api_key="sk-test",
    )


class StubProviderRoleDetectionTests(unittest.TestCase):
    """Tests for StubProvider._detect_role()."""

    def _provider(self) -> providers.StubProvider:
        return providers.StubProvider(_stub_config())

    def test_detects_planner_role(self) -> None:
        p = self._provider()
        self.assertEqual(
            p._detect_role("You are a PLANNER. Plan test scenarios."),
            "planner",
        )
        self.assertEqual(
            p._detect_role("test_objective field is required"),
            "planner",
        )

    def test_detects_checker_role(self) -> None:
        p = self._provider()
        self.assertEqual(
            p._detect_role("You are a CHECKER. Evaluate coverage."),
            "checker",
        )
        self.assertEqual(
            p._detect_role("coverage_relevance field required"),
            "checker",
        )

    def test_detects_maker_role(self) -> None:
        p = self._provider()
        self.assertEqual(
            p._detect_role("You are a MAKER. Generate evidence-backed BDD scenarios."),
            "maker",
        )
        self.assertEqual(
            p._detect_role(
                "You are the maker model for an LME test design workflow. "
                "The checker will rate coverage_relevance later."
            ),
            "maker",
        )
        self.assertEqual(
            p._detect_role("Generate a scenario based on the rule."),
            "maker",
        )

    def test_detects_bdd_role(self) -> None:
        p = self._provider()
        self.assertEqual(
            p._detect_role("You are a BDD normalizer. Normalize given_steps."),
            "bdd",
        )
        self.assertEqual(
            p._detect_role("given_steps and when_steps should be normalized."),
            "bdd",
        )
        self.assertEqual(
            p._detect_role("normalized output format"),
            "bdd",
        )

    def test_defaults_to_maker(self) -> None:
        p = self._provider()
        self.assertEqual(p._detect_role(""), "maker")
        self.assertEqual(p._detect_role("some unrelated prompt"), "maker")


class StubProviderExtractRuleIdsTests(unittest.TestCase):
    """Tests for StubProvider._extract_semantic_rule_ids()."""

    def _provider(self) -> providers.StubProvider:
        return providers.StubProvider(_stub_config())

    def test_extracts_semantic_rule_ids(self) -> None:
        p = self._provider()
        prompt = (
            'Input semantic rules:\n'
            '{"semantic_rule_id": "SR-001"}\n'
            '{"semantic_rule_id": "SR-002"}\n'
        )
        ids = p._extract_semantic_rule_ids(prompt)
        self.assertEqual(ids, ["SR-001", "SR-002"])

    def test_deduplicates_rule_ids(self) -> None:
        p = self._provider()
        prompt = (
            'Input semantic rules:\n'
            '{"semantic_rule_id": "SR-001"}\n'
            '{"semantic_rule_id": "SR-001"}\n'
        )
        ids = p._extract_semantic_rule_ids(prompt)
        self.assertEqual(ids, ["SR-001"])

    def test_returns_empty_for_no_ids(self) -> None:
        p = self._provider()
        ids = p._extract_semantic_rule_ids("No IDs here")
        self.assertEqual(ids, [])


class StubProviderGenerateTests(unittest.TestCase):
    """Tests for StubProvider.generate()."""

    def _provider(self) -> providers.StubProvider:
        return providers.StubProvider(_stub_config())

    def test_maker_response_structure(self) -> None:
        p = self._provider()
        system = "You are a MAKER"
        user = 'Input semantic rules:\n{"semantic_rule_id": "SR-001"}\n'
        resp = p.generate(system, user)
        self.assertIsInstance(resp, providers.ModelResponse)
        payload = json.loads(resp.content)
        self.assertIn("results", payload)
        self.assertEqual(len(payload["results"]), 1)
        self.assertEqual(payload["results"][0]["semantic_rule_id"], "SR-001")
        self.assertIn("feature", payload["results"][0])
        self.assertIn("scenarios", payload["results"][0])
        self.assertTrue(resp.raw_response["stub"])

    def test_checker_response_structure(self) -> None:
        p = self._provider()
        system = "You are a CHECKER"
        user = (
            'Input semantic rules:\n{"semantic_rule_id": "SR-001"}\n'
            '{"scenario_id": "TC-SR-001-1", "case_type": "negative"}\n'
        )
        resp = p.generate(system, user)
        payload = json.loads(resp.content)
        self.assertIn("results", payload)
        self.assertGreaterEqual(len(payload["results"]), 1)
        self.assertIn("case_id", payload["results"][0])
        self.assertIn("scores", payload["results"][0])
        self.assertEqual(payload["results"][0]["case_type"], "negative")

    def test_planner_response_structure(self) -> None:
        p = self._provider()
        system = "You are a PLANNER"
        user = 'Input semantic rules:\n{"semantic_rule_id": "SR-001"}\n'
        resp = p.generate(system, user)
        payload = json.loads(resp.content)
        self.assertIn("results", payload)
        self.assertEqual(payload["results"][0]["semantic_rule_id"], "SR-001")
        self.assertIn("risk_level", payload["results"][0])
        self.assertIn("test_objective", payload["results"][0])

    def test_bdd_response_structure(self) -> None:
        p = self._provider()
        system = "You are a BDD normalizer"
        user = 'Input semantic rules:\n{"semantic_rule_id": "SR-001"}\n'
        resp = p.generate(system, user)
        payload = json.loads(resp.content)
        self.assertIn("results", payload)
        self.assertEqual(payload["results"][0]["semantic_rule_id"], "SR-001")
        self.assertIn("scenarios", payload["results"][0])
        self.assertIn("given_steps", payload["results"][0]["scenarios"][0])


class BuildProviderTests(unittest.TestCase):
    """Tests for build_provider()."""

    def test_returns_stub_for_stub_type(self) -> None:
        config = _stub_config()
        result = providers.build_provider(config)
        self.assertIsInstance(result, providers.StubProvider)

    def test_returns_stub_for_stub_api_key(self) -> None:
        config = _openai_config()
        config.api_key = providers.STUB_API_KEY
        result = providers.build_provider(config)
        self.assertIsInstance(result, providers.StubProvider)

    def test_returns_openai_for_openai_compatible(self) -> None:
        config = _openai_config()
        result = providers.build_provider(config)
        self.assertIsInstance(result, providers.OpenAICompatibleProvider)

    def test_raises_for_unsupported_provider_type(self) -> None:
        config = _openai_config()
        config.provider_type = "unknown"
        with self.assertRaises(providers.ProviderError):
            providers.build_provider(config)


if __name__ == "__main__":
    unittest.main()

