from __future__ import annotations

import json
import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
ABSOLUTE_LOCAL_LINK_RE = re.compile(r"^(?:/[A-Za-z]:/|[A-Za-z]:[/\\\\]|file://|vscode://)")
ALLOWED_RULE_TYPES = {
    "obligation",
    "prohibition",
    "permission",
    "deadline",
    "state_transition",
    "data_constraint",
    "enum_definition",
    "workflow",
    "calculation",
    "reference_only",
}


def _normalize_markdown_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    if " " in target and not target.startswith(("http://", "https://", "mailto:", "#")):
        target = target.split(" ", 1)[0]
    return target


def _is_local_link(target: str) -> bool:
    return not target.startswith(("http://", "https://", "mailto:", "#"))


def find_absolute_local_markdown_links(repo_root: Path) -> list[str]:
    violations: list[str] = []
    for path in sorted(repo_root.rglob("*.md")):
        rel_path = path.relative_to(repo_root).as_posix()
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in MARKDOWN_LINK_RE.finditer(line):
                target = _normalize_markdown_target(match.group(1))
                if not target or not _is_local_link(target):
                    continue
                if ABSOLUTE_LOCAL_LINK_RE.match(target):
                    violations.append(f"{rel_path}:{line_number}: absolute local link not allowed: {target}")
    return violations


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _check_list_artifact(path: Path, required_keys: set[str]) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"missing artifact: {path.relative_to(REPO_ROOT).as_posix()}"]
    payload = _load_json(path)
    if not isinstance(payload, list) or not payload:
        return [f"artifact must be a non-empty JSON list: {path.relative_to(REPO_ROOT).as_posix()}"]
    first = payload[0]
    if not isinstance(first, dict):
        return [f"artifact entries must be JSON objects: {path.relative_to(REPO_ROOT).as_posix()}"]
    missing = sorted(required_keys - set(first.keys()))
    if missing:
        errors.append(
            f"artifact missing required keys {missing}: {path.relative_to(REPO_ROOT).as_posix()}"
        )
    return errors


def _check_atomic_rules(path: Path) -> list[str]:
    errors = _check_list_artifact(path, {"rule_id", "clause_id", "raw_text"})
    if errors:
        return errors
    payload = _load_json(path)
    assert isinstance(payload, list)
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            continue
        raw_text = item.get("raw_text")
        if not isinstance(raw_text, str) or not raw_text.strip():
            errors.append(
                f"atomic_rules entry {index} has empty raw_text: {path.relative_to(REPO_ROOT).as_posix()}"
            )
        rule_id = item.get("rule_id")
        clause_id = item.get("clause_id")
        if not isinstance(rule_id, str) or not rule_id.strip():
            errors.append(
                f"atomic_rules entry {index} has invalid rule_id: {path.relative_to(REPO_ROOT).as_posix()}"
            )
        if not isinstance(clause_id, str) or not clause_id.strip():
            errors.append(
                f"atomic_rules entry {index} has invalid clause_id: {path.relative_to(REPO_ROOT).as_posix()}"
            )
    return errors


def _check_semantic_rules(path: Path) -> list[str]:
    errors = _check_list_artifact(path, {"semantic_rule_id", "source", "classification", "evidence"})
    if errors:
        return errors
    payload = _load_json(path)
    assert isinstance(payload, list)
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            continue
        semantic_rule_id = item.get("semantic_rule_id")
        if not isinstance(semantic_rule_id, str) or not semantic_rule_id.strip():
            errors.append(
                f"semantic_rules entry {index} has invalid semantic_rule_id: {path.relative_to(REPO_ROOT).as_posix()}"
            )

        source = item.get("source")
        if not isinstance(source, dict):
            errors.append(
                f"semantic_rules entry {index} has invalid source object: {path.relative_to(REPO_ROOT).as_posix()}"
            )
        else:
            source_missing = sorted({"doc_id", "doc_title", "doc_version", "atomic_rule_ids", "pages"} - set(source.keys()))
            if source_missing:
                errors.append(
                    f"semantic_rules entry {index} source missing keys {source_missing}: {path.relative_to(REPO_ROOT).as_posix()}"
                )
            if not isinstance(source.get("atomic_rule_ids"), list) or not source.get("atomic_rule_ids"):
                errors.append(
                    f"semantic_rules entry {index} has empty source.atomic_rule_ids: {path.relative_to(REPO_ROOT).as_posix()}"
                )
            if not isinstance(source.get("pages"), list) or not source.get("pages"):
                errors.append(
                    f"semantic_rules entry {index} has empty source.pages: {path.relative_to(REPO_ROOT).as_posix()}"
                )

        classification = item.get("classification")
        if not isinstance(classification, dict):
            errors.append(
                f"semantic_rules entry {index} has invalid classification object: {path.relative_to(REPO_ROOT).as_posix()}"
            )
        else:
            class_missing = sorted({"rule_type", "coverage_eligible"} - set(classification.keys()))
            if class_missing:
                errors.append(
                    f"semantic_rules entry {index} classification missing keys {class_missing}: {path.relative_to(REPO_ROOT).as_posix()}"
                )
            rule_type = classification.get("rule_type")
            if rule_type not in ALLOWED_RULE_TYPES:
                errors.append(
                    f"semantic_rules entry {index} has invalid classification.rule_type '{rule_type}': {path.relative_to(REPO_ROOT).as_posix()}"
                )

        evidence = item.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(
                f"semantic_rules entry {index} has empty evidence list: {path.relative_to(REPO_ROOT).as_posix()}"
            )
        elif isinstance(evidence[0], dict):
            evidence_missing = sorted({"atomic_rule_id", "page", "quote"} - set(evidence[0].keys()))
            if evidence_missing:
                errors.append(
                    f"semantic_rules entry {index} first evidence item missing keys {evidence_missing}: {path.relative_to(REPO_ROOT).as_posix()}"
                )
    return errors


def _check_metadata_artifact(path: Path) -> list[str]:
    if not path.exists():
        return [f"missing artifact: {path.relative_to(REPO_ROOT).as_posix()}"]
    payload = _load_json(path)
    if not isinstance(payload, dict):
        return [f"metadata artifact must be a JSON object: {path.relative_to(REPO_ROOT).as_posix()}"]
    required = {"doc_id", "doc_title", "doc_version"}
    missing = sorted(required - set(payload.keys()))
    if missing:
        return [f"metadata artifact missing required keys {missing}: {path.relative_to(REPO_ROOT).as_posix()}"]
    return []


def check_docs_governance(repo_root: Path) -> list[str]:
    return find_absolute_local_markdown_links(repo_root)


def check_artifact_governance(repo_root: Path) -> list[str]:
    errors: list[str] = []
    errors.extend(
        _check_atomic_rules(
            repo_root / "artifacts" / "poc_two_rules" / "atomic_rules.json"
        )
    )
    errors.extend(
        _check_semantic_rules(
            repo_root / "artifacts" / "poc_two_rules" / "semantic_rules.json"
        )
    )
    lme_dir = repo_root / "artifacts" / "lme_rules_v2_2"
    errors.extend(_check_metadata_artifact(lme_dir / "metadata.json"))
    errors.extend(_check_atomic_rules(lme_dir / "atomic_rules.json"))
    errors.extend(_check_semantic_rules(lme_dir / "semantic_rules.json"))
    return errors
