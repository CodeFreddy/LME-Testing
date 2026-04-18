"""Step registry and visibility module (Phase 2 Gate 5 / Phase 3 Gate 1).

Provides step-level visibility into generated BDD artifacts:
- Extracts step patterns from normalized BDD output and step definition files
- Matches BDD steps to library steps (exact, parameterized, candidate)
- Computes reuse scores and ownership mapping
- Produces machine-readable visibility reports

Phase 2 (Gate 5): basic gap detection with exact normalized matching.
Phase 3 (Gate 1): adds parameterized matching, candidate suggestions,
                  reuse scores, and ownership mapping.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from .storage import load_jsonl


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class StepEntry:
    """A single step pattern extracted from BDD or step definitions."""

    step_type: str  # "given" | "when" | "then"
    step_text: str
    step_pattern: str
    code: str = ""
    source_scenario_ids: list[str] = field(default_factory=list)
    source_semantic_rule_ids: list[str] = field(default_factory=list)
    # Match metadata (populated by compute_step_matches)
    match_type: str = ""  # "exact" | "parameterized" | "candidate" | "unmatched"
    library_step_text: str = ""
    library_name: str = ""  # owner library identifier
    confidence: float = 0.0
    suggestions: list[dict] = field(default_factory=list)


@dataclass
class StepInventory:
    """Inventory of steps extracted from normalized BDD or step definition files."""

    given_steps: list[StepEntry] = field(default_factory=list)
    when_steps: list[StepEntry] = field(default_factory=list)
    then_steps: list[StepEntry] = field(default_factory=list)
    library_name: str = ""  # Owner identifier for this inventory

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
    """Report of step gaps between BDD steps and existing step definition library."""

    total_bdd_steps: int = 0
    unique_patterns: int = 0
    matched_patterns: int = 0
    unmatched_patterns: int = 0
    gaps: list[GapEntry] = field(default_factory=list)
    reuse_candidates: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Phase 3 new structures
# ---------------------------------------------------------------------------


@dataclass
class StepMatch:
    """Result of matching a single BDD step against the library."""

    bdd_step: StepEntry
    library_step: StepEntry | None  # None for candidates
    match_type: str  # "exact" | "parameterized" | "candidate"
    confidence: float  # 0.0–1.0
    capture_group_mapping: dict[int, int] | None = None  # BDD group idx → lib group idx
    library_name: str = ""


@dataclass
class MatchReport:
    """Full match report with multi-tier matching, reuse scores, and ownership."""

    total_bdd_steps: int = 0
    unique_bdd_patterns: int = 0
    exact_matches: int = 0
    parameterized_matches: int = 0
    candidates: list[dict] = field(default_factory=list)
    unmatched: int = 0
    reuse_scores: dict[str, float] = field(default_factory=dict)  # pattern → score
    ownership: dict[str, str] = field(default_factory=dict)  # pattern → library name


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------


def _normalize_pattern(pattern: str) -> str:
    """Normalize a step pattern for deduplication."""
    p = re.sub(r"^\^?", "", pattern)
    p = re.sub(r"\$?$", "", p)
    p = re.sub(r"\s+", " ", p).strip()
    return p.lower()


def _step_key(step: StepEntry) -> str:
    """Generate a deduplication key for a step."""
    return f"{step.step_type}:{_normalize_pattern(step.step_pattern)}"


# ---------------------------------------------------------------------------
# Capture-group extraction for parameterized matching
# ---------------------------------------------------------------------------

# Named type hints that are considered semantically equivalent
_TYPE_HINTS: dict[str, set[str]] = {
    "string": {"string", "str", "text", "name", "value", "label"},
    "int": {"int", "integer", "count", "number", "id", "num"},
    "float": {"float", "decimal", "amount", "price", "rate", "percentage"},
    "bool": {"bool", "boolean", "flag", "enabled"},
    "id": {"id", "identifier", "uuid", "ref", "reference"},
}


def _extract_capture_groups(pattern: str) -> list[tuple[str, str]]:
    """Extract (group_idx, type_hint_or_sample) for each regex capture group.

    Handles:
      - Named groups: (?P<name>...) — extracts name as type hint
      - Numbered groups with inline type hints: (?:int:{...})
      - Plain numbered groups: (...) — uses "any" as catch-all
    """
    groups: list[tuple[str, str]] = []
    # Named groups: (?P<name>pattern)
    for m in re.finditer(r"\(\?P<(\w+)>\s*(.*?)\s*\)", pattern, re.DOTALL):
        hint = m.group(1).lower()
        groups.append((hint, hint))
    # Numbered groups with inline type hint: (?:type:{...})
    for m in re.finditer(r"\(\?:(\w+):\{[^}]*\}", pattern):
        hint = m.group(1).lower()
        groups.append((f"grp_{len(groups)}", hint))
    # Plain numbered groups: (non-greedy any)
    # Replace non-capturing groups first
    temp = re.sub(r"\(\?:[^)]+\)", "__NC__", pattern)
    plain = re.findall(r"(?<!\\)\((?!\?)", temp)
    for _ in plain:
        groups.append((f"grp_{len(groups)}", "any"))
    return groups


def _groups_compatible(
    bdd_groups: list[tuple[str, str]],
    lib_groups: list[tuple[str, str]],
) -> bool:
    """Check if BDD groups can map to library groups.

    Two groups are compatible if:
    1. Both are "any" (plain capture), OR
    2. Both share the same type hint (int/int, float/float, string/string, etc.), OR
    3. One is a supertype of the other (string covers most things).
    """
    if len(bdd_groups) != len(lib_groups):
        return False
    for (b_idx, b_hint), (l_idx, l_hint) in zip(bdd_groups, lib_groups):
        if b_hint == "any" or l_hint == "any":
            continue
        if b_hint == l_hint:
            continue
        # Check if either hint is a subtype of the other
        b_family = next((fam for fam, hints in _TYPE_HINTS.items() if b_hint in hints), b_hint)
        l_family = next((fam for fam, hints in _TYPE_HINTS.items() if l_hint in hints), l_hint)
        if b_family != l_family:
            return False
    return True


def _normalize_for_similarity(text: str) -> list[str]:
    """Tokenize and lowercase for TF-IDF similarity."""
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [t for t in tokens if len(t) > 1]


def _idf(token: str, doc_freq: Counter, n_docs: int) -> float:
    """Inverse document frequency for a token."""
    df = doc_freq.get(token, 0)
    if df == 0:
        return 0.0
    return math.log(n_docs / df)


def _cosine_similarity(tokens1: list[str], tokens2: list[str], idf_vals: dict[str, float]) -> float:
    """TF-IDF cosine similarity between two token lists."""
    if not tokens1 or not tokens2:
        return 0.0
    tf1 = Counter(tokens1)
    tf2 = Counter(tokens2)
    dot = sum(tf1[t] * tf2[t] * (idf_vals.get(t, 0) ** 2) for t in set(tokens1) & set(tokens2))
    norm1 = math.sqrt(sum((tf1[t] * idf_vals.get(t, 0)) ** 2 for t in tf1))
    norm2 = math.sqrt(sum((tf2[t] * idf_vals.get(t, 0)) ** 2 for t in tf2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


# ---------------------------------------------------------------------------
# Core matching engine
# ---------------------------------------------------------------------------


def _build_library_index(inventory: StepInventory) -> dict[str, StepEntry]:
    """Build normalized-pattern → StepEntry index from library inventory.

    Uses step_text (not step_pattern) for the index key so that BDD steps
    with literal stopwords (a/an/the) match library entries whose step_pattern
    contains (?:a|an|the) placeholders.

    Parameterized matching uses step_pattern via _build_library_group_index.
    """
    index: dict[str, StepEntry] = {}
    for step in inventory.all_steps():
        norm = _normalize_pattern(step.step_text)
        if norm not in index:
            index[norm] = step
    return index


def _build_library_group_index(inventory: StepInventory) -> list[tuple[StepEntry, list[tuple[str, str]]]]:
    """Build library steps with their capture groups for parameterized matching."""
    result: list[tuple[StepEntry, list[tuple[str, str]]]] = []
    for step in inventory.all_steps():
        groups = _extract_capture_groups(step.step_pattern)
        if groups:
            result.append((step, groups))
    return result


def compute_step_matches(
    bdd_inventory: StepInventory,
    library_inventory: StepInventory,
    candidate_top_k: int = 3,
    similarity_threshold: float = 0.3,
) -> MatchReport:
    """Compute multi-tier matches between BDD steps and library steps.

    Matching strategy (per step):
      1. Exact — normalized pattern equality
      2. Parameterized — same step type + compatible regex capture groups
      3. Candidate — top-K similar library steps by TF-IDF cosine similarity

    Args:
        bdd_inventory: BDD steps extracted from normalized BDD output.
        library_inventory: Library steps extracted from step definition files.
        candidate_top_k: Number of candidate suggestions per unmatched step.
        similarity_threshold: Minimum similarity to surface a candidate.

    Returns:
        MatchReport with exact_matches, parameterized_matches, candidates, etc.
    """
    # Build library index for exact lookup
    lib_index = _build_library_index(library_inventory)
    lib_grouped = _build_library_group_index(library_inventory)

    # Deduplicate BDD steps
    seen: dict[str, StepEntry] = {}
    for step in bdd_inventory.all_steps():
        key = _step_key(step)
        if key not in seen:
            seen[key] = step

    # Precompute IDF for TF-IDF similarity
    all_tokens: list[list[str]] = [_normalize_for_similarity(s.step_text) for s in library_inventory.all_steps()]
    doc_freq: Counter = Counter()
    for tokens in all_tokens:
        doc_freq.update(set(tokens))
    n_docs = max(len(all_tokens), 1)
    idf_vals = {t: _idf(t, doc_freq, n_docs) for t in doc_freq}

    matches: list[StepMatch] = []
    reuse_counts: Counter = Counter()  # library pattern → BDD scenario count

    # --- Exact and parameterized matching pass ---
    for key, bdd_step in seen.items():
        norm = _normalize_pattern(bdd_step.step_pattern)

        # 1. Exact match
        if norm in lib_index:
            lib_step = lib_index[norm]
            if lib_step.step_type == bdd_step.step_type:
                matches.append(StepMatch(
                    bdd_step=bdd_step,
                    library_step=lib_step,
                    match_type="exact",
                    confidence=1.0,
                    capture_group_mapping=None,
                    library_name=library_inventory.library_name,
                ))
                reuse_counts[_step_key(lib_step)] += 1
                # Annotate the inventory entry with match metadata
                bdd_step.match_type = "exact"
                bdd_step.confidence = 1.0
                bdd_step.library_step_text = lib_step.step_text
                bdd_step.suggestions = []
                continue

        # 2. Parameterized match
        bdd_groups = _extract_capture_groups(bdd_step.step_pattern)
        best_param_match: StepMatch | None = None
        best_param_conf = 0.0

        for lib_step, lib_groups in lib_grouped:
            if lib_step.step_type != bdd_step.step_type:
                continue
            if len(bdd_groups) != len(lib_groups):
                continue
            if _groups_compatible(bdd_groups, lib_groups):
                # Score by specificity: fewer "any" groups = higher confidence
                any_count = sum(1 for (_, h) in lib_groups if h == "any")
                conf = round(1.0 - (0.1 * any_count), 2)
                conf = max(conf, 0.6)
                if conf > best_param_conf:
                    best_param_conf = conf
                    mapping = {i: i for i in range(len(bdd_groups))}
                    best_param_match = StepMatch(
                        bdd_step=bdd_step,
                        library_step=lib_step,
                        match_type="parameterized",
                        confidence=conf,
                        capture_group_mapping=mapping,
                        library_name=library_inventory.library_name,
                    )

        if best_param_match is not None:
            matches.append(best_param_match)
            reuse_counts[_step_key(best_param_match.library_step)] += 1
            # Annotate the inventory entry
            bdd_step.match_type = "parameterized"
            bdd_step.confidence = best_param_match.confidence
            bdd_step.library_step_text = best_param_match.library_step.step_text if best_param_match.library_step else ""
            bdd_step.suggestions = []
            continue

        # 3. Candidate matching (deferred — compute similarity only for unmatched)
        bdd_tokens = _normalize_for_similarity(bdd_step.step_text)
        candidates_for_step: list[dict] = []
        for lib_step in library_inventory.all_steps():
            if lib_step.step_type != bdd_step.step_type:
                continue
            lib_tokens = _normalize_for_similarity(lib_step.step_text)
            sim = _cosine_similarity(bdd_tokens, lib_tokens, idf_vals)
            if sim >= similarity_threshold:
                candidates_for_step.append({
                    "library_step_text": lib_step.step_text,
                    "library_step_pattern": lib_step.step_pattern,
                    "library_name": library_inventory.library_name,
                    "similarity": round(sim, 3),
                    "capture_groups": _extract_capture_groups(lib_step.step_pattern),
                })

        # Sort by similarity descending and take top-K
        candidates_for_step.sort(key=lambda c: c["similarity"], reverse=True)
        top_candidates = candidates_for_step[:candidate_top_k]

        if top_candidates:
            matches.append(StepMatch(
                bdd_step=bdd_step,
                library_step=None,
                match_type="candidate",
                confidence=top_candidates[0]["similarity"] if top_candidates else 0.0,
                capture_group_mapping=None,
                library_name="",
            ))
            bdd_step.match_type = "candidate"
            bdd_step.confidence = top_candidates[0]["similarity"]
            bdd_step.library_step_text = ""
            bdd_step.suggestions = top_candidates
        else:
            matches.append(StepMatch(
                bdd_step=bdd_step,
                library_step=None,
                match_type="unmatched",
                confidence=0.0,
                capture_group_mapping=None,
                library_name="",
            ))
            bdd_step.match_type = "unmatched"
            bdd_step.confidence = 0.0
            bdd_step.library_step_text = ""
            bdd_step.suggestions = []

    # --- Compute reuse scores ---
    total_unique = max(len(seen), 1)
    reuse_scores: dict[str, float] = {}
    for key, count in reuse_counts.items():
        reuse_scores[key] = round(count / total_unique, 3)

    # --- Ownership mapping ---
    ownership: dict[str, str] = {}
    for step in library_inventory.all_steps():
        ownership[_step_key(step)] = library_inventory.library_name

    # --- Categorize ---
    exact_count = sum(1 for m in matches if m.match_type == "exact")
    param_count = sum(1 for m in matches if m.match_type == "parameterized")
    unmatched_count = sum(1 for m in matches if m.match_type == "unmatched")

    candidate_results: list[dict] = []
    for m in matches:
        if m.match_type == "candidate":
            # Find top-K similar for this step
            bdd_tokens = _normalize_for_similarity(m.bdd_step.step_text)
            cands: list[dict] = []
            for lib_step in library_inventory.all_steps():
                if lib_step.step_type != m.bdd_step.step_type:
                    continue
                lib_tokens = _normalize_for_similarity(lib_step.step_text)
                sim = _cosine_similarity(bdd_tokens, lib_tokens, idf_vals)
                if sim >= similarity_threshold:
                    cands.append({
                        "library_step_text": lib_step.step_text,
                        "library_step_pattern": lib_step.step_pattern,
                        "library_name": library_inventory.library_name,
                        "similarity": round(sim, 3),
                    })
            cands.sort(key=lambda c: c["similarity"], reverse=True)
            candidate_results.append({
                "step_type": m.bdd_step.step_type,
                "step_text": m.bdd_step.step_text,
                "step_pattern": m.bdd_step.step_pattern,
                "source_scenario_ids": m.bdd_step.source_scenario_ids,
                "confidence": round(m.confidence, 3),
                "suggestions": cands[:candidate_top_k],
            })

    return MatchReport(
        total_bdd_steps=bdd_inventory.total_steps,
        unique_bdd_patterns=len(seen),
        exact_matches=exact_count,
        parameterized_matches=param_count,
        candidates=candidate_results,
        unmatched=unmatched_count,
        reuse_scores=reuse_scores,
        ownership=ownership,
    )


# ---------------------------------------------------------------------------
# Backward-compatible wrapper
# ---------------------------------------------------------------------------


def compute_step_gaps(
    bdd_inventory: StepInventory,
    library_inventory: StepInventory,
) -> GapReport:
    """Compute gaps between BDD steps and existing step definition library.

    This is a backward-compatible wrapper around compute_step_matches.
    """
    report = compute_step_matches(bdd_inventory, library_inventory)

    # Build gap list from unmatched + candidate steps
    gaps: list[GapEntry] = []
    reuse_candidates: list[dict] = []

    # Matched patterns from exact + parameterized
    matched_patterns = set()
    for m in (m for m in [] if False):  # placeholder to keep structure
        pass

    # We need to re-identify matched vs unmatched using the seen set logic
    seen: dict[str, StepEntry] = {}
    for step in bdd_inventory.all_steps():
        key = _step_key(step)
        if key not in seen:
            seen[key] = step

    lib_index = _build_library_index(library_inventory)
    lib_grouped = _build_library_group_index(library_inventory)

    for key, bdd_step in seen.items():
        norm = _normalize_pattern(bdd_step.step_pattern)
        is_matched = False

        if norm in lib_index and lib_index[norm].step_type == bdd_step.step_type:
            is_matched = True
        else:
            bdd_groups = _extract_capture_groups(bdd_step.step_pattern)
            for lib_step, lib_groups in lib_grouped:
                if lib_step.step_type == bdd_step.step_type:
                    if len(bdd_groups) == len(lib_groups) and _groups_compatible(bdd_groups, lib_groups):
                        is_matched = True
                        break

        if not is_matched:
            gaps.append(GapEntry(
                step_type=bdd_step.step_type,
                step_text=bdd_step.step_text,
                step_pattern=bdd_step.step_pattern,
                source_scenario_ids=bdd_step.source_scenario_ids,
            ))
        else:
            reuse_candidates.append({
                "step_type": bdd_step.step_type,
                "step_text": bdd_step.step_text,
                "step_pattern": bdd_step.step_pattern,
                "source_count": len(bdd_step.source_scenario_ids),
            })

    return GapReport(
        total_bdd_steps=report.total_bdd_steps,
        unique_patterns=report.unique_bdd_patterns,
        matched_patterns=report.exact_matches + report.parameterized_matches,
        unmatched_patterns=report.unmatched,
        gaps=gaps,
        reuse_candidates=reuse_candidates,
    )


# ---------------------------------------------------------------------------
# Extraction from normalized BDD JSONL
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Extraction from Ruby step definition files
# ---------------------------------------------------------------------------


RUBY_STEP_DEF_RE = re.compile(
    r"(Given|When|Then)\(/[\^]?(.*?)[\$]?/\)\s+do\s*(.*?)\s*end",
    re.DOTALL | re.IGNORECASE,
)


def extract_steps_from_step_defs(
    step_defs_file: Path,
    library_name: str = "",
) -> StepInventory:
    """Extract step patterns from a Ruby Cucumber step definitions file.

    Args:
        step_defs_file: Path to the Ruby step definitions file.
        library_name: Optional owner identifier. If empty, derived from file path.
    """
    inventory = StepInventory()
    if not step_defs_file.exists():
        return inventory

    if not library_name:
        library_name = step_defs_file.stem.replace("_steps", "").replace("-", "_")

    text = step_defs_file.read_text(encoding="utf-8")
    # Also try to extract @library tag
    lib_match = re.search(r"#\s*@library:\s*(\S+)", text)
    if lib_match:
        library_name = lib_match.group(1)

    for match in RUBY_STEP_DEF_RE.finditer(text):
        keyword = match.group(1).lower()
        step_pattern = match.group(2).strip()
        code = match.group(3).strip()

        # Extract step_text by reversing pattern normalization
        step_text = re.sub(
            r"\(\?:.?\)|\[.+?\]|\(\?!\s*\w+\)",
            lambda m: m.group(0)[2:-1] if m.group(0).startswith("(?:") else m.group(0),
            step_pattern,
        )
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

    inventory.library_name = library_name
    return inventory


PYTHON_STEP_DEF_RE = re.compile(
    "@(given|when|then)\\(['\"](.+?)['\"]\\)"
    "\\s*def\\s+(\\w+)\\s*\\([^)]*\\)\\s*:\\s*\\n((?:[ \\t]+.+\\n)*)",
    re.DOTALL | re.IGNORECASE,
)


def extract_steps_from_python_step_defs(
    step_defs_file: Path,
    library_name: str = "",
) -> StepInventory:
    """Extract step patterns from a Python step definitions file.

    Two modes:
    1. If the file is ``lme_testing/step_library.py``, imports STEP_LIBRARY
       directly (which uses @step decorators with StepType enum).
    2. Otherwise, parses @given/@when/@then decorator patterns via regex.

    The step_text is the key for exact matching; step_pattern is derived
    via extract_pattern() for parameterized matching.
    """
    inventory = StepInventory()
    if not step_defs_file.exists():
        return inventory

    if not library_name:
        library_name = step_defs_file.stem.replace("_steps", "").replace("-", "_")

    # Mode 1: Import STEP_LIBRARY directly from lme_testing.step_library.
    # This handles @step-decorated files (like step_library.py itself).
    if step_defs_file.name == "step_library.py":
        try:
            from lme_testing.step_library import STEP_LIBRARY as _sl
            for _step_text, _entry in _sl.items():
                entry = StepEntry(
                    step_type=_entry.step_type,
                    step_text=_entry.step_text,
                    step_pattern=_entry.step_pattern,
                    code=_entry.code,
                    library_step_text=_entry.step_text,
                    library_name=library_name,
                    match_type="",
                    confidence=0.0,
                    source_scenario_ids=[],
                    suggestions=[],
                )
                if _entry.step_type == "given":
                    inventory.given_steps.append(entry)
                elif _entry.step_type == "when":
                    inventory.when_steps.append(entry)
                elif _entry.step_type == "then":
                    inventory.then_steps.append(entry)
            inventory.library_name = library_name
            return inventory
        except Exception:
            pass  # fall through to regex parsing

    # Mode 2: Parse @given/@when/@then decorated Python files
    from .step_library import extract_pattern

    text = step_defs_file.read_text(encoding="utf-8")

    for match in PYTHON_STEP_DEF_RE.finditer(text):
        keyword = match.group(1).lower()
        step_text = match.group(2)
        function_name = match.group(3)
        code_body = match.group(4).rstrip()

        step_pattern = extract_pattern(step_text)

        entry = StepEntry(
            step_type=keyword,
            step_text=step_text,
            step_pattern=step_pattern,
            code=code_body,
            library_step_text=step_text,
            library_name=library_name,
            match_type="",
            confidence=0.0,
            source_scenario_ids=[],
            suggestions=[],
        )

        if keyword == "given":
            inventory.given_steps.append(entry)
        elif keyword == "when":
            inventory.when_steps.append(entry)
        elif keyword == "then":
            inventory.then_steps.append(entry)

    inventory.library_name = library_name
    return inventory


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------


def render_step_visibility_report(
    inventory: StepInventory,
    report: GapReport | MatchReport,
    output_path: Path,
) -> None:
    """Write step visibility report as JSON.

    Handles both legacy GapReport and new MatchReport formats.
    """
    import json

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(report, MatchReport):
        # Deduplicate steps by pattern, keeping annotated entry
        seen_patterns: dict[str, StepEntry] = {}
        for step in inventory.all_steps():
            key = _step_key(step)
            if key not in seen_patterns:
                seen_patterns[key] = step

        def serialize_steps(steps: list[StepEntry]) -> list[dict]:
            result = []
            for s in steps:
                key = _step_key(s)
                if key in seen_patterns:
                    entry = seen_patterns.pop(key)
                    result.append({
                        "step_text": entry.step_text,
                        "step_pattern": entry.step_pattern,
                        "match_type": entry.match_type,
                        "library_step_text": entry.library_step_text,
                        "confidence": entry.confidence,
                        "source_scenario_ids": entry.source_scenario_ids,
                        "suggestions": entry.suggestions,
                    })
            return result

        gaps = [s for s in seen_patterns.values() if s.match_type == "unmatched"]

        rep: dict = {
            "total_steps": inventory.total_steps,
            "given_count": len(inventory.given_steps),
            "when_count": len(inventory.when_steps),
            "then_count": len(inventory.then_steps),
            "unique_bdd_patterns": report.unique_bdd_patterns,
            "exact_matches": report.exact_matches,
            "parameterized_matches": report.parameterized_matches,
            "candidates": report.candidates,
            "unmatched": report.unmatched,
            "reuse_scores": report.reuse_scores,
            "ownership": report.ownership,
            "given_steps": serialize_steps(inventory.given_steps),
            "when_steps": serialize_steps(inventory.when_steps),
            "then_steps": serialize_steps(inventory.then_steps),
            "gaps": [
                {
                    "step_text": g.step_text,
                    "step_pattern": g.step_pattern,
                    "step_type": g.step_type,
                    "source_scenario_ids": g.source_scenario_ids,
                }
                for g in gaps
            ],
        }
    else:
        # Legacy GapReport
        rep = {
            "total_steps": inventory.total_steps,
            "given_count": len(inventory.given_steps),
            "when_count": len(inventory.when_steps),
            "then_count": len(inventory.then_steps),
            "unique_patterns": report.unique_patterns,
            "matched_patterns": report.matched_patterns,
            "unmatched_patterns": report.unmatched_patterns,
            "gap_count": len(report.gaps),
            "reuse_candidates": report.reuse_candidates,
            "gaps": [
                {
                    "step_type": g.step_type,
                    "step_text": g.step_text,
                    "step_pattern": g.step_pattern,
                    "source_scenario_ids": g.source_scenario_ids,
                }
                for g in report.gaps
            ],
        }

    output_path.write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
