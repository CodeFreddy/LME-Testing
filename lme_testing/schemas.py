from __future__ import annotations

import json
import re


class SchemaError(ValueError):
    """模型输出不符合预期 JSON 结构时抛出。"""


MAX_QUOTE_LENGTH = 220
CASE_TYPES = {
    "positive",
    "negative",
    "boundary",
    "exception",
    "state_transition",
    "data_validation",
}
COVERAGE_STATUSES = {"covered", "partial", "uncovered", "not_applicable"}
COVERAGE_RELEVANCE = {"direct", "indirect", "not_relevant"}


def _strip_markdown_fence(text: str) -> str:
    cleaned = text.strip()
    fenced = re.match(r"^```(?:json)?\s*(.*?)\s*```$", cleaned, re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()
    return cleaned


def parse_json_object(text: str) -> dict:
    normalized = _strip_markdown_fence(text)
    try:
        data = json.loads(normalized)
    except json.JSONDecodeError as exc:
        raise SchemaError(f"Model output is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SchemaError("Model output must be a JSON object.")
    return data


def validate_maker_payload(
    payload: dict,
    expected_rule_ids: list[str] | None = None,
    expected_required_case_types: dict[str, list[str]] | None = None,
) -> dict:
    results = payload.get("results")
    if not isinstance(results, list):
        raise SchemaError("Maker payload must contain a 'results' list.")

    actual_rule_ids: list[str] = []
    for item in results:
        if not isinstance(item, dict):
            raise SchemaError("Each maker result must be an object.")
        semantic_rule_id = item.get("semantic_rule_id")
        if not isinstance(semantic_rule_id, str):
            raise SchemaError("Each maker result must include semantic_rule_id.")
        actual_rule_ids.append(semantic_rule_id)
        if not isinstance(item.get("feature"), str):
            raise SchemaError("Each maker result must include feature.")
        requirement_ids = item.get("requirement_ids")
        if not isinstance(requirement_ids, list) or not requirement_ids:
            raise SchemaError("Each maker result must include non-empty requirement_ids.")
        if any(not isinstance(value, str) for value in requirement_ids):
            raise SchemaError("requirement_ids must be a list of strings.")

        scenarios = item.get("scenarios")
        if not isinstance(scenarios, list) or not scenarios:
            raise SchemaError("Each maker result must include non-empty scenarios.")

        evidence_rule_ids: set[str] = set()
        scenario_ids: set[str] = set()
        scenario_case_types: list[str] = []
        for scenario in scenarios:
            scenario_id = scenario.get("scenario_id")
            if not isinstance(scenario_id, str):
                raise SchemaError("Each scenario must include scenario_id.")
            if scenario_id in scenario_ids:
                raise SchemaError(f"Duplicate scenario_id in maker result {semantic_rule_id}: {scenario_id}")
            scenario_ids.add(scenario_id)
            case_type = scenario.get("case_type") or scenario.get("scenario_type")
            if case_type not in CASE_TYPES:
                raise SchemaError(f"Invalid case_type: {case_type}")
            scenario["case_type"] = case_type
            scenario_case_types.append(case_type)
            for key in ("given", "when", "then", "assumptions"):
                if not isinstance(scenario.get(key), list):
                    raise SchemaError(f"Scenario field '{key}' must be a list.")
            evidence = scenario.get("evidence")
            if not isinstance(evidence, list) or not evidence:
                raise SchemaError("Each scenario must include evidence.")
            for evidence_item in evidence:
                if not isinstance(evidence_item, dict):
                    raise SchemaError("Each evidence item must be an object.")
                atomic_rule_id = evidence_item.get("atomic_rule_id")
                quote = evidence_item.get("quote")
                if not isinstance(atomic_rule_id, str):
                    raise SchemaError("Each evidence item must include atomic_rule_id.")
                if not isinstance(quote, str) or not quote.strip():
                    raise SchemaError("Each evidence item must include a non-empty quote.")
                # Truncate long quotes instead of failing
                if len(quote.strip()) > MAX_QUOTE_LENGTH:
                    evidence_item["quote"] = quote.strip()[:MAX_QUOTE_LENGTH] + "..."
                quote = evidence_item["quote"]
                if "\n" in quote:
                    raise SchemaError("Evidence quote must be a single short line.")
                evidence_rule_ids.add(atomic_rule_id)
        if not set(requirement_ids).issubset(evidence_rule_ids):
            raise SchemaError(
                f"Maker result {semantic_rule_id} does not provide evidence for every requirement_id."
            )
        if expected_required_case_types is not None:
            required_case_types = expected_required_case_types.get(semantic_rule_id, [])
            if required_case_types:
                if set(scenario_case_types) != set(required_case_types):
                    raise SchemaError(
                        f"Maker result {semantic_rule_id} must cover exactly required case types: {required_case_types}."
                    )
                if len(scenario_case_types) != len(required_case_types):
                    raise SchemaError(
                        f"Maker result {semantic_rule_id} must return exactly one scenario per required case type."
                    )
            elif len(scenario_case_types) != 1:
                raise SchemaError(
                    f"Maker result {semantic_rule_id} with no required_case_types must return exactly one conservative scenario."
                )

    if expected_rule_ids is not None:
        if len(actual_rule_ids) != len(expected_rule_ids):
            raise SchemaError("Maker must return exactly one result for each input rule.")
        if set(actual_rule_ids) != set(expected_rule_ids):
            raise SchemaError("Maker returned missing or extra semantic_rule_id values.")
        if len(set(actual_rule_ids)) != len(actual_rule_ids):
            raise SchemaError("Maker returned duplicate semantic_rule_id values.")
    return payload


RISK_LEVELS = {"high", "medium", "low"}
PLANNER_RISK_LEVELS = {"high", "medium", "low"}
SCENARIO_FAMILIES: set[str] = set()  # Unrestricted; populated from data


def validate_planner_payload(payload: dict, expected_rule_ids: list[str] | None = None) -> dict:
    results = payload.get("results")
    if not isinstance(results, list):
        raise SchemaError("Planner payload must contain a 'results' list.")

    actual_rule_ids: list[str] = []
    for item in results:
        if not isinstance(item, dict):
            raise SchemaError("Each planner result must be an object.")
        semantic_rule_id = item.get("semantic_rule_id")
        if not isinstance(semantic_rule_id, str):
            raise SchemaError("Each planner result must include semantic_rule_id.")
        actual_rule_ids.append(semantic_rule_id)

        if item.get("risk_level") not in PLANNER_RISK_LEVELS:
            raise SchemaError(f"Invalid risk_level: {item.get('risk_level')}")
        if item.get("priority") not in PLANNER_RISK_LEVELS:
            raise SchemaError(f"Invalid priority: {item.get('priority')}")
        if not isinstance(item.get("test_objective", ""), str):
            raise SchemaError("test_objective must be a string.")
        if not isinstance(item.get("scenario_family", ""), str):
            raise SchemaError("scenario_family must be a string.")

        dep_notes = item.get("dependency_notes", [])
        if not isinstance(dep_notes, list):
            raise SchemaError("dependency_notes must be a list.")
        for note in dep_notes:
            if not isinstance(note, str):
                raise SchemaError("dependency_notes items must be strings.")

        if expected_rule_ids is not None:
            if len(actual_rule_ids) != len(expected_rule_ids):
                raise SchemaError("Planner must return exactly one result for each input rule.")
            if set(actual_rule_ids) != set(expected_rule_ids):
                raise SchemaError("Planner returned missing or extra semantic_rule_id values.")
            if len(set(actual_rule_ids)) != len(actual_rule_ids):
                raise SchemaError("Planner returned duplicate semantic_rule_id values.")
    return payload


def validate_normalized_bdd_payload(payload: dict, expected_rule_ids: list[str] | None = None) -> dict:
    results = payload.get("results")
    if not isinstance(results, list):
        raise SchemaError("Normalized BDD payload must contain a 'results' list.")

    actual_rule_ids: list[str] = []
    for item in results:
        if not isinstance(item, dict):
            raise SchemaError("Each BDD result must be an object.")
        semantic_rule_id = item.get("semantic_rule_id")
        if not isinstance(semantic_rule_id, str):
            raise SchemaError("Each BDD result must include semantic_rule_id.")
        actual_rule_ids.append(semantic_rule_id)

        if not isinstance(item.get("feature_title"), str):
            raise SchemaError("feature_title must be a string.")

        scenarios = item.get("scenarios")
        if not isinstance(scenarios, list) or not scenarios:
            raise SchemaError("Each BDD result must include non-empty scenarios.")

        scenario_ids: set[str] = set()
        for scenario in scenarios:
            scenario_id = scenario.get("scenario_id")
            if not isinstance(scenario_id, str):
                raise SchemaError("Each scenario must include scenario_id.")
            if scenario_id in scenario_ids:
                raise SchemaError(f"Duplicate scenario_id: {scenario_id}")
            scenario_ids.add(scenario_id)

            case_type = scenario.get("case_type")
            if case_type not in CASE_TYPES:
                raise SchemaError(f"Invalid case_type in BDD scenario: {case_type}")

            for step_key in ("given_steps", "when_steps", "then_steps"):
                steps = scenario.get(step_key)
                if not isinstance(steps, list):
                    raise SchemaError(f"{step_key} must be a list.")
                for step in steps:
                    if not isinstance(step, dict):
                        raise SchemaError(f"Each step in {step_key} must be an object.")
                    if not isinstance(step.get("step_text"), str):
                        raise SchemaError("step_text must be a string.")
                    if not isinstance(step.get("step_pattern"), str):
                        raise SchemaError("step_pattern must be a string.")

            assumptions = scenario.get("assumptions", [])
            if not isinstance(assumptions, list):
                raise SchemaError("assumptions must be a list.")

        step_defs = item.get("step_definitions", {})
        if not isinstance(step_defs, dict):
            raise SchemaError("step_definitions must be an object.")

    if expected_rule_ids is not None:
        if len(actual_rule_ids) != len(expected_rule_ids):
            raise SchemaError("BDD must return exactly one result for each input rule.")
        if set(actual_rule_ids) != set(expected_rule_ids):
            raise SchemaError("BDD returned missing or extra semantic_rule_id values.")
    return payload


def validate_checker_payload(payload: dict, expected_case_map: dict[str, str] | None = None) -> dict:
    results = payload.get("results")
    if not isinstance(results, list):
        raise SchemaError("Checker payload must contain a 'results' list.")

    actual_case_ids: list[str] = []
    for item in results:
        required = (
            "case_id",
            "semantic_rule_id",
            "case_type",
            "case_type_accepted",
            "coverage_relevance",
            "overall_status",
            "blocking_findings_count",
            "is_blocking",
            "scores",
            "coverage_assessment",
        )
        for key in required:
            if key not in item:
                raise SchemaError(f"Checker payload missing '{key}'.")
        if item["case_type"] not in CASE_TYPES:
            raise SchemaError(f"Invalid checker case_type: {item['case_type']}")
        if not isinstance(item["case_type_accepted"], bool):
            raise SchemaError("case_type_accepted must be boolean.")
        if item["coverage_relevance"] not in COVERAGE_RELEVANCE:
            raise SchemaError("Invalid coverage_relevance value.")
        if not isinstance(item["blocking_findings_count"], int):
            raise SchemaError("blocking_findings_count must be int.")
        if not isinstance(item["is_blocking"], bool):
            raise SchemaError("is_blocking must be boolean.")
        if not isinstance(item["scores"], dict):
            raise SchemaError("Checker scores must be an object.")
        if not isinstance(item.get("findings", []), list):
            raise SchemaError("Checker findings must be a list.")
        if not isinstance(item["coverage_assessment"], dict):
            raise SchemaError("coverage_assessment must be an object.")
        if item["coverage_assessment"].get("status") not in COVERAGE_STATUSES:
            raise SchemaError("Invalid coverage_assessment.status value.")
        if not isinstance(item["case_id"], str):
            raise SchemaError("Checker case_id must be a string.")
        actual_case_ids.append(item["case_id"])

    if expected_case_map is not None:
        expected_case_ids = list(expected_case_map.keys())
        if len(actual_case_ids) != len(expected_case_ids):
            raise SchemaError("Checker must return exactly one result for each input case_id.")
        if set(actual_case_ids) != set(expected_case_ids):
            raise SchemaError("Checker returned missing or extra case_id values.")
        if len(set(actual_case_ids)) != len(actual_case_ids):
            raise SchemaError("Checker returned duplicate case_id values.")
        for item in results:
            expected_rule_id = expected_case_map[item["case_id"]]
            if item["semantic_rule_id"] != expected_rule_id:
                raise SchemaError("Checker returned a semantic_rule_id that does not match the input case.")
    return payload
