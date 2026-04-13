"""Step registry and visibility module (Phase 2 Gate 5).

Provides step-level visibility into generated BDD artifacts:
- Extracts step patterns from normalized BDD output and step definition files
- Identifies reusable steps and gaps
- Produces machine-readable visibility reports

This module does NOT provide execution binding (Phase 3 concern).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import DefaultDict

from .storage import load_jsonl


@dataclass
class StepEntry:
    """A single step pattern extracted from BDD or step definitions."""

    step_type: str  # "given" | "when" | "then"
    step_text: str
    step_pattern: str
    code: str = ""
    source_scenario_ids: list[str] = field(default_factory=list)
    source_semantic_rule_ids: list[str] = field(default_factory=list)


@dataclass
class StepInventory:
    """Inventory of steps extracted from normalized BDD or step definition files."""

    given_steps: list[StepEntry] = field(default_factory=list)
    when_steps: list[StepEntry] = field(default_factory=list)
    then_steps: list[StepEntry] = field(default_factory=list)

    @property
    def total_steps(self) -> int:
        return len(self.given_steps) + len(self.when_steps) + len(self.then_steps)

    def all_steps(self) -> list[StepEntry]:
        return self.given_steps + self.when_steps + self.then_steps


@dataclass
class GapEntry:
    """A step gap: pattern has no matching step definition."""

    step_type: str
    step_text: str
    step_pattern: str
    source_scenario_ids: list[str] = field(default_factory=list)


@dataclass
class GapReport:
    """Report of step gaps between BDD inventory and existing library."""

    total_bdd_steps: int = 0
    unique_patterns: int = 0
    matched_patterns: int = 0
    unmatched_patterns: int = 0
    gaps: list[GapEntry] = field(default_factory=list)
    reuse_candidates: list[dict] = field(default_factory=list)


def _normalize_pattern(pattern: str) -> str:
    """Normalize a step pattern for deduplication."""
    # Remove regex anchors and normalize whitespace
    p = re.sub(r"^\^?", "", pattern)
    p = re.sub(r"\$?$", "", p)
    p = re.sub(r"\s+", " ", p).strip()
    return p.lower()


def _step_key(step: StepEntry) -> str:
    """Generate a deduplication key for a step."""
    return f"{step.step_type}:{_normalize_pattern(step.step_pattern)}"


def extract_steps_from_normalized_bdd(normalized_bdd_path: Path) -> StepInventory:
    """Extract all step patterns from a normalized BDD JSONL file."""
    inventory = StepInventory()
    bdd_records = load_jsonl(normalized_bdd_path)

    for record in bdd_records:
        semantic_rule_id = record.get("semantic_rule_id", "")
        scenarios = record.get("scenarios", [])
        step_defs = record.get("step_definitions", {})

        for scenario in scenarios:
            scenario_id = scenario.get("scenario_id", "")
            for step_type in ("given_steps", "when_steps", "then_steps"):
                keyword = step_type.replace("_steps", "")
                steps = scenario.get(step_type, [])
                library_steps = step_defs.get(keyword, [])

                # Build a lookup from step_text to code from step_definitions
                code_by_text: dict[str, str] = {
                    s.get("step_text", ""): s.get("code", "")
                    for s in library_steps
                    if isinstance(s, dict)
                }

                for step in steps:
                    if not isinstance(step, dict):
                        continue
                    step_text = step.get("step_text", "")
                    step_pattern = step.get("step_pattern", step_text)
                    code = code_by_text.get(step_text, "")

                    entry = StepEntry(
                        step_type=keyword,
                        step_text=step_text,
                        step_pattern=step_pattern,
                        code=code,
                        source_scenario_ids=[scenario_id],
                        source_semantic_rule_ids=[semantic_rule_id],
                    )

                    if keyword == "given":
                        inventory.given_steps.append(entry)
                    elif keyword == "when":
                        inventory.when_steps.append(entry)
                    elif keyword == "then":
                        inventory.then_steps.append(entry)

    return inventory


def extract_steps_from_step_defs(step_defs_file: Path) -> StepInventory:
    """Extract step patterns from a Ruby Cucumber step definitions file."""
    inventory = StepInventory()
    if not step_defs_file.exists():
        return inventory

    text = step_defs_file.read_text(encoding="utf-8")
    # Match Given/When/Then patterns
    pattern_re = re.compile(
        r"(Given|When|Then)\(/[\^]?(.*?)[\$]?/\)\s+do\s*(.*?)\s*end",
        re.DOTALL | re.IGNORECASE,
    )
    for match in pattern_re.finditer(text):
        keyword = match.group(1).lower()
        step_pattern = match.group(2).strip()
        code = match.group(3).strip()

        # Extract step_text by reversing pattern normalization
        step_text = re.sub(r"\(\?:.?\)|\[.+?\]|\(\?!\s*\w+\)", lambda m: m.group(0)[2:-1] if m.group(0).startswith("(?:") else m.group(0), step_pattern)
        step_text = re.sub(r"\\", "", step_text)
        step_text = step_text.strip()

        entry = StepEntry(
            step_type=keyword,
            step_text=step_text,
            step_pattern=step_pattern,
            code=code,
        )

        if keyword == "given":
            inventory.given_steps.append(entry)
        elif keyword == "when":
            inventory.when_steps.append(entry)
        elif keyword == "then":
            inventory.then_steps.append(entry)

    return inventory


def compute_step_gaps(bdd_inventory: StepInventory, library_inventory: StepInventory) -> GapReport:
    """Compute gaps between BDD steps and existing step definition library.

    A step is considered "matched" if its normalized pattern exists in the library.
    Gaps are unmatched BDD steps that have no corresponding library step.
    """
    # Build a set of normalized patterns from library
    library_patterns: set[str] = set()
    for step in library_inventory.all_steps():
        library_patterns.add(_normalize_pattern(step.step_pattern))

    # Deduplicate BDD steps by normalized pattern
    seen: dict[str, StepEntry] = {}
    for step in bdd_inventory.all_steps():
        key = _step_key(step)
        if key not in seen:
            seen[key] = step

    # Find gaps and reuse candidates
    gaps: list[GapEntry] = []
    reuse_candidates: list[dict] = []

    for key, step in seen.items():
        norm = _normalize_pattern(step.step_pattern)
        if norm not in library_patterns:
            gaps.append(GapEntry(
                step_type=step.step_type,
                step_text=step.step_text,
                step_pattern=step.step_pattern,
                source_scenario_ids=step.source_scenario_ids,
            ))
        else:
            reuse_candidates.append({
                "step_type": step.step_type,
                "step_text": step.step_text,
                "step_pattern": step.step_pattern,
                "source_count": len(step.source_scenario_ids),
            })

    return GapReport(
        total_bdd_steps=bdd_inventory.total_steps,
        unique_patterns=len(seen),
        matched_patterns=len(reuse_candidates),
        unmatched_patterns=len(gaps),
        gaps=gaps,
        reuse_candidates=reuse_candidates,
    )


def render_step_visibility_report(inventory: StepInventory, gaps: GapReport, output_path: Path) -> None:
    """Write step visibility report as JSON."""
    import json

    output_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "total_steps": inventory.total_steps,
        "given_count": len(inventory.given_steps),
        "when_count": len(inventory.when_steps),
        "then_count": len(inventory.then_steps),
        "unique_patterns": gaps.unique_patterns,
        "matched_patterns": gaps.matched_patterns,
        "unmatched_patterns": gaps.unmatched_patterns,
        "gap_count": len(gaps.gaps),
        "reuse_candidates": gaps.reuse_candidates,
        "gaps": [
            {
                "step_type": g.step_type,
                "step_text": g.step_text,
                "step_pattern": g.step_pattern,
                "source_scenario_ids": g.source_scenario_ids,
            }
            for g in gaps.gaps
        ],
    }
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
