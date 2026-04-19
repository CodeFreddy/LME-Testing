from __future__ import annotations

import json
import re
from pathlib import Path


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
BLOCKING_CATEGORIES = {
    "none",
    "rule_mismatch",
    "missing_required_case_type",
    "invalid_case_type_mapping",
    "no_evidence_or_wrong_evidence",
    "non_executable_scenario",
    "duplicate_case_covering_same_slot",
    "schema_or_traceability_break",
    "unspecified_block",
}
HUMAN_REVIEW_DECISIONS = {"pending", "approve", "rewrite"}
ISSUE_TYPE_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "human_review_options.json"


# 统一从配置文件读取 issue type，保证页面选项、回流校验和统计口径一致。
def load_issue_type_options() -> list[dict]:
    payload = json.loads(ISSUE_TYPE_CONFIG_PATH.read_text(encoding="utf-8-sig"))
    items = payload.get("issue_types", [])
    if not isinstance(items, list):
        raise SchemaError("human_review_options.json must contain an 'issue_types' list.")
    normalized: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            raise SchemaError("Each issue type option must be an object.")
        code = item.get("code")
        label = item.get("label")
        description = item.get("description")
        if not all(isinstance(value, str) and value.strip() for value in (code, label, description)):
            raise SchemaError("Each issue type option must include non-empty code/label/description.")
        normalized.append({
            "code": code.strip(),
            "label": label.strip(),
            "description": description.strip(),
        })
    return normalized


def allowed_issue_type_codes() -> set[str]:
    return {item["code"] for item in load_issue_type_options()}


# 兼容旧版 human review JSON。老字段 block_recommendation_review/human_block_decision 整体丢弃；
# 老 decision 值 approved/needs_rewrite/rejected 归一到新三态，且 reject → rewrite。
def normalize_human_review_item(item: dict) -> dict:
    normalized = dict(item)

    review_decision = normalized.get("review_decision")
    legacy_review_map = {
        "approved": "approve",
        "needs_rewrite": "rewrite",
        "rejected": "rewrite",
        "reject": "rewrite",
    }
    if review_decision in legacy_review_map:
        normalized["review_decision"] = legacy_review_map[review_decision]

    normalized.pop("human_block_decision", None)
    normalized.pop("block_recommendation_review", None)
    return normalized


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
                if len(quote.strip()) > MAX_QUOTE_LENGTH:
                    raise SchemaError("Evidence quote is too long; quotes must stay short.")
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
            "blocking_category",
            "blocking_reason",
            "checker_confidence",
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
        if item["blocking_category"] not in BLOCKING_CATEGORIES:
            raise SchemaError("Invalid blocking_category value.")
        if not isinstance(item["blocking_reason"], str):
            raise SchemaError("blocking_reason must be string.")
        if not isinstance(item["checker_confidence"], (int, float)):
            raise SchemaError("checker_confidence must be numeric.")
        if item["checker_confidence"] < 0 or item["checker_confidence"] > 1:
            raise SchemaError("checker_confidence must be between 0 and 1.")
        if item["is_blocking"]:
            if item["blocking_category"] == "none":
                raise SchemaError("Blocking checker result must include a non-none blocking_category.")
            if not item["blocking_reason"].strip():
                raise SchemaError("Blocking checker result must include blocking_reason.")
        else:
            if item["blocking_category"] != "none":
                raise SchemaError("Non-blocking checker result must use blocking_category='none'.")
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


# 校验人工审核页面导出的 JSON，保证回流给 maker 的输入是结构化、可追溯的。
def validate_human_review_payload(payload: dict, expected_case_map: dict[str, str] | None = None) -> dict:
    reviews = payload.get("reviews")
    if not isinstance(reviews, list):
        raise SchemaError("Human review payload must contain a 'reviews' list.")

    actual_case_ids: list[str] = []
    allowed_issue_codes = allowed_issue_type_codes()
    normalized_reviews: list[dict] = []
    for raw_item in reviews:
        if not isinstance(raw_item, dict):
            raise SchemaError("Each human review item must be an object.")
        item = normalize_human_review_item(raw_item)
        case_id = item.get("case_id")
        semantic_rule_id = item.get("semantic_rule_id")
        if not isinstance(case_id, str) or not case_id:
            raise SchemaError("Each human review item must include case_id.")
        if not isinstance(semantic_rule_id, str) or not semantic_rule_id:
            raise SchemaError("Each human review item must include semantic_rule_id.")
        if item.get("review_decision") not in HUMAN_REVIEW_DECISIONS:
            raise SchemaError("Invalid human review_decision value.")
        if not isinstance(item.get("human_comment", ""), str):
            raise SchemaError("human_comment must be string.")
        issue_types = item.get("issue_types", [])
        if not isinstance(issue_types, list) or any(not isinstance(value, str) for value in issue_types):
            raise SchemaError("issue_types must be a list of strings.")
        if any(value not in allowed_issue_codes for value in issue_types):
            raise SchemaError("issue_types contains values outside configured options.")
        normalized_reviews.append(item)
        actual_case_ids.append(case_id)

    payload["reviews"] = normalized_reviews
    if expected_case_map is not None:
        expected_case_ids = list(expected_case_map.keys())
        if set(actual_case_ids) - set(expected_case_ids):
            raise SchemaError("Human review payload contains extra case_id values.")
        for item in normalized_reviews:
            expected_rule_id = expected_case_map.get(item["case_id"])
            if expected_rule_id and item["semantic_rule_id"] != expected_rule_id:
                raise SchemaError("Human review semantic_rule_id does not match the input case mapping.")
    return payload
