"""Unit tests for lme_testing/step_registry.py."""
from __future__ import annotations

import unittest

from lme_testing.step_registry import (
    _normalize_pattern,
    _step_key,
    _groups_compatible,
    _cosine_similarity,
    _extract_capture_groups,
    compute_step_gaps,
    StepEntry,
    StepInventory,
    GapReport,
)


class NormalizePatternTests(unittest.TestCase):
    """Tests for _normalize_pattern()."""

    def test_strips_leading_anchor(self) -> None:
        result = _normalize_pattern("^the pattern")
        self.assertEqual(result, "the pattern")

    def test_strips_trailing_anchor(self) -> None:
        result = _normalize_pattern("the pattern$")
        self.assertEqual(result, "the pattern")

    def test_strips_both_anchors(self) -> None:
        result = _normalize_pattern("^the pattern$")
        self.assertEqual(result, "the pattern")

    def test_normalizes_whitespace(self) -> None:
        result = _normalize_pattern("the   pattern\n\twith\rmultiple  spaces")
        self.assertEqual(result, "the pattern with multiple spaces")

    def test_lowercases(self) -> None:
        result = _normalize_pattern("The Pattern With CAPS")
        self.assertEqual(result, "the pattern with caps")


class StepKeyTests(unittest.TestCase):
    """Tests for _step_key()."""

    def test_includes_type_and_normalized_pattern(self) -> None:
        entry = StepEntry(
            step_type="given",
            step_text="The user logs in",
            step_pattern="^the user logs in$",
        )
        key = _step_key(entry)
        self.assertTrue(key.startswith("given:"))
        self.assertIn("user logs in", key)

    def test_different_types_different_keys(self) -> None:
        entry_given = StepEntry(step_type="given", step_text="log in", step_pattern="log in")
        entry_when = StepEntry(step_type="when", step_text="log in", step_pattern="log in")
        self.assertNotEqual(_step_key(entry_given), _step_key(entry_when))


class GroupsCompatibleTests(unittest.TestCase):
    """Tests for _groups_compatible()."""

    def test_same_type_hint(self) -> None:
        bdd = [("grp0", "int"), ("grp1", "string")]
        lib = [("grp0", "int"), ("grp1", "string")]
        self.assertTrue(_groups_compatible(bdd, lib))

    def test_any_matches_any(self) -> None:
        bdd = [("grp0", "any"), ("grp1", "any")]
        lib = [("grp0", "string"), ("grp1", "int")]
        self.assertTrue(_groups_compatible(bdd, lib))

    def test_incompatible_different_types(self) -> None:
        bdd = [("grp0", "int")]
        lib = [("grp0", "string")]
        # int and string are in different families
        self.assertFalse(_groups_compatible(bdd, lib))

    def test_different_lengths(self) -> None:
        bdd = [("grp0", "int"), ("grp1", "int")]
        lib = [("grp0", "int")]
        self.assertFalse(_groups_compatible(bdd, lib))

    def test_subtype_compatible(self) -> None:
        # "id" is a subtype of "int"
        bdd = [("grp0", "id")]
        lib = [("grp0", "int")]
        self.assertTrue(_groups_compatible(bdd, lib))


class CosineSimilarityTests(unittest.TestCase):
    """Tests for _cosine_similarity()."""

    def test_identical_tokens(self) -> None:
        idf = {"hello": 1.0, "world": 1.0}
        result = _cosine_similarity(["hello", "world"], ["hello", "world"], idf)
        self.assertAlmostEqual(result, 1.0)

    def test_no_overlap(self) -> None:
        idf = {"hello": 1.0, "world": 1.0, "foo": 1.0, "bar": 1.0}
        result = _cosine_similarity(["hello"], ["foo"], idf)
        self.assertEqual(result, 0.0)

    def test_empty_input(self) -> None:
        result = _cosine_similarity([], ["hello"], {})
        self.assertEqual(result, 0.0)

    def test_partial_overlap(self) -> None:
        idf = {"hello": 1.0, "world": 1.0, "foo": 1.0}
        result = _cosine_similarity(["hello", "world"], ["hello", "foo"], idf)
        self.assertGreater(result, 0.0)
        self.assertLess(result, 1.0)


class ExtractCaptureGroupsTests(unittest.TestCase):
    """Tests for _extract_capture_groups()."""

    def test_named_groups(self) -> None:
        pattern = "(?P<order_id>\\d+)"
        groups = _extract_capture_groups(pattern)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0][0], "order_id")
        self.assertEqual(groups[0][1], "order_id")

    def test_plain_groups(self) -> None:
        pattern = "order (\\d+) for (\\d+) items"
        groups = _extract_capture_groups(pattern)
        self.assertEqual(len(groups), 2)
        self.assertEqual(groups[0][1], "any")
        self.assertEqual(groups[1][1], "any")


class ComputeStepGapsTests(unittest.TestCase):
    """Tests for compute_step_gaps()."""

    def _make_inventory(self, steps: list[StepEntry]) -> StepInventory:
        inv = StepInventory()
        for step in steps:
            if step.step_type == "given":
                inv.given_steps.append(step)
            elif step.step_type == "when":
                inv.when_steps.append(step)
            elif step.step_type == "then":
                inv.then_steps.append(step)
        return inv

    def test_exact_match(self) -> None:
        # BDD step exactly matches library step
        bdd = self._make_inventory([
            StepEntry(step_type="given", step_text="user logs in", step_pattern="user logs in"),
        ])
        lib = self._make_inventory([
            StepEntry(step_type="given", step_text="user logs in", step_pattern="user logs in"),
        ])
        report = compute_step_gaps(bdd, lib)
        self.assertEqual(report.total_bdd_steps, 1)
        # Should have 0 gaps if matched (exact match)
        self.assertEqual(len(report.gaps), 0)

    def test_unmatched_step(self) -> None:
        # BDD step has no match in library
        bdd = self._make_inventory([
            StepEntry(step_type="given", step_text="user cancels order", step_pattern="user cancels order"),
        ])
        lib = StepInventory()  # empty library
        report = compute_step_gaps(bdd, lib)
        self.assertEqual(report.total_bdd_steps, 1)
        self.assertEqual(len(report.gaps), 1)
        self.assertEqual(report.gaps[0].step_text, "user cancels order")

    def test_empty_bdd_inventory(self) -> None:
        bdd = StepInventory()
        lib = self._make_inventory([
            StepEntry(step_type="given", step_text="user logs in", step_pattern="user logs in"),
        ])
        report = compute_step_gaps(bdd, lib)
        self.assertEqual(report.total_bdd_steps, 0)


if __name__ == "__main__":
    unittest.main()

