from __future__ import annotations

import logging
import re
from collections import Counter, defaultdict
from pathlib import Path

from .config import ProjectConfig
from .prompts import (
    CHECKER_SYSTEM_PROMPT,
    MAKER_SYSTEM_PROMPT,
    REWRITE_SYSTEM_PROMPT,
    build_checker_user_prompt,
    build_maker_user_prompt,
    build_rewrite_user_prompt,
)
from .providers import build_provider
from .schemas import parse_json_object, validate_checker_payload, validate_human_review_payload, validate_maker_payload
from .storage import append_jsonl, ensure_dir, load_json, load_jsonl, timestamp_slug, write_json

logger = logging.getLogger(__name__)


RULE_TYPE_CASE_REQUIREMENTS = {
    "obligation": {"required": ["positive", "negative"], "optional": ["boundary", "exception"]},
    "prohibition": {"required": ["negative", "positive"], "optional": ["exception"]},
    "permission": {"required": ["positive"], "optional": ["negative", "exception"]},
    "deadline": {"required": ["positive", "boundary", "negative"], "optional": ["exception"]},
    "state_transition": {"required": ["positive", "state_transition"], "optional": ["negative", "exception"]},
    "data_constraint": {"required": ["positive", "negative", "data_validation"], "optional": ["boundary"]},
    "enum_definition": {"required": ["positive", "negative"], "optional": []},
    "workflow": {"required": ["positive", "negative", "exception"], "optional": ["state_transition"]},
    "calculation": {"required": ["positive", "boundary", "data_validation"], "optional": ["negative"]},
    "reference_only": {"required": [], "optional": []},
}
BLOCKING_CATEGORY_ALIASES = {
    "rule_mismatch": "rule_mismatch",
    "missing_required_case_type": "missing_required_case_type",
    "invalid_case_type_mapping": "invalid_case_type_mapping",
    "no_evidence_or_wrong_evidence": "no_evidence_or_wrong_evidence",
    "non_executable_scenario": "non_executable_scenario",
    "duplicate_case_covering_same_slot": "duplicate_case_covering_same_slot",
    "schema_or_traceability_break": "schema_or_traceability_break",
}


def _chunked(items: list[dict], size: int) -> list[list[dict]]:
    if size <= 0:
        raise ValueError("batch_size must be greater than zero.")
    return [items[index:index + size] for index in range(0, len(items), size)]


def _maker_record_from_result(result: dict, run_id: str) -> dict:
    return {
        "run_id": run_id,
        "semantic_rule_id": result["semantic_rule_id"],
        "requirement_ids": result.get("requirement_ids", []),
        "feature": result["feature"],
        "scenarios": result["scenarios"],
    }


def _required_case_types(rule: dict) -> dict:
    rule_type = rule.get("classification", {}).get("rule_type", "reference_only")
    mapping = RULE_TYPE_CASE_REQUIREMENTS.get(rule_type, {"required": ["positive"], "optional": []})
    return {
        "rule_type": rule_type,
        "required": list(mapping["required"]),
        "optional": list(mapping["optional"]),
    }


def _augment_rule_with_case_requirements(rule: dict) -> dict:
    # 将覆盖要求直接传给 maker，避免模型自行猜测该 rule 需要哪些场景类型。
    augmented_rule = dict(rule)
    case_requirements = _required_case_types(rule)
    augmented_rule["required_case_types"] = case_requirements["required"]
    augmented_rule["optional_case_types"] = case_requirements["optional"]
    return augmented_rule


def _normalize_blocking_category(value: str | None) -> str:
    if not value:
        return "none"
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    return BLOCKING_CATEGORY_ALIASES.get(normalized, "unspecified_block")


def _default_blocking_reason(result: dict) -> str:
    findings = result.get("findings", [])
    if findings:
        first = findings[0]
        summary = str(first.get("summary", "")).strip()
        if summary:
            return summary
    return str(result.get("coverage_assessment", {}).get("reason", "")).strip()


def _governance_defaults(result: dict) -> None:
    # Mirror checker blocking fields so downstream Decision logic can key off one place.
    result["checker_blocking"] = bool(result.get("is_blocking", False))
    result["checker_blocking_category"] = result.get("blocking_category", "none")
    result["checker_blocking_reason"] = result.get("blocking_reason", "")
    result["checker_confidence"] = float(result.get("checker_confidence", 0.5))
    result.setdefault(
        "block_recommendation_review",
        "pending_review" if result["checker_blocking"] else "not_applicable",
    )
    result.setdefault("human_comment", "")


def _review_governance_summary(reviews: list[dict]) -> dict:
    # Checker-stage metric only. Human/checker divergence lives in audit_trail.html.
    checker_block_count = sum(1 for item in reviews if item.get("checker_blocking") is True)
    return {"checker_block_count": checker_block_count}


def _load_semantic_rules(semantic_rules_path: Path, limit: int | None = None) -> list[dict]:
    semantic_rules = load_json(semantic_rules_path)
    if not isinstance(semantic_rules, list):
        raise ValueError("semantic_rules.json must contain a list.")
    if limit is not None:
        semantic_rules = semantic_rules[:limit]
    return semantic_rules


def run_maker_pipeline(
    config: ProjectConfig,
    semantic_rules_path: Path,
    output_dir: Path,
    limit: int | None,
    batch_size: int,
    resume_from: Path | None,
) -> dict:
    logger.info("Starting maker pipeline. input=%s output_dir=%s limit=%s batch_size=%s resume_from=%s", semantic_rules_path, output_dir, limit, batch_size, resume_from)
    semantic_rules = _load_semantic_rules(semantic_rules_path, limit=limit)

    completed_ids: set[str] = set()
    if resume_from and resume_from.exists():
        for record in load_jsonl(resume_from):
            semantic_rule_id = record.get("semantic_rule_id")
            if semantic_rule_id:
                completed_ids.add(semantic_rule_id)
        semantic_rules = [
            rule
            for rule in semantic_rules
            if rule.get("semantic_rule_id") not in completed_ids
        ]

    provider = build_provider(config.provider_for_role("maker"))
    run_id = timestamp_slug()
    run_dir = ensure_dir(output_dir / run_id)
    results_path = run_dir / "maker_cases.jsonl"
    raw_path = run_dir / "maker_raw_responses.jsonl"
    summary_path = run_dir / "summary.json"

    total_batches = 0
    total_cases = 0

    for batch in _chunked(semantic_rules, batch_size):
        logger.info("Maker batch start. run_id=%s batch_rule_ids=%s", run_id, [item["semantic_rule_id"] for item in batch])
        augmented_batch = [_augment_rule_with_case_requirements(item) for item in batch]
        response = provider.generate(
            system_prompt=MAKER_SYSTEM_PROMPT,
            user_prompt=build_maker_user_prompt(augmented_batch),
        )
        raw_record = {
            "run_id": run_id,
            "batch_semantic_rule_ids": [item["semantic_rule_id"] for item in batch],
            "response": response.raw_response,
        }
        append_jsonl(raw_path, [raw_record])

        payload = validate_maker_payload(
            parse_json_object(response.content),
            expected_rule_ids=[item["semantic_rule_id"] for item in batch],
            expected_required_case_types={
                item["semantic_rule_id"]: _required_case_types(item)["required"]
                for item in batch
            },
        )
        records = [_maker_record_from_result(item, run_id=run_id) for item in payload["results"]]
        append_jsonl(results_path, records)
        total_batches += 1
        total_cases += sum(len(item["scenarios"]) for item in payload["results"])
        logger.info("Maker batch done. run_id=%s batch_count=%s total_cases=%s", run_id, total_batches, total_cases)

    summary = {
        "run_id": run_id,
        "role": "maker",
        "input_path": str(semantic_rules_path),
        "output_dir": str(run_dir),
        "processed_rule_count": len(semantic_rules),
        "batch_count": total_batches,
        "scenario_count": total_cases,
        "results_path": str(results_path),
        "raw_path": str(raw_path),
    }
    write_json(summary_path, summary)
    logger.info("Maker pipeline completed. summary=%s", summary)
    return summary


def _calculate_coverage(semantic_rules: list[dict], reviews: list[dict]) -> dict:
    reviews_by_rule: dict[str, list[dict]] = defaultdict(list)
    for review in reviews:
        reviews_by_rule[review["semantic_rule_id"]].append(review)

    status_by_rule: dict[str, dict] = {}
    counts = Counter()

    for rule in semantic_rules:
        semantic_rule_id = rule["semantic_rule_id"]
        case_requirements = _required_case_types(rule)
        rule_type = case_requirements["rule_type"]
        required_case_types = case_requirements["required"]
        optional_case_types = case_requirements["optional"]
        relevant_reviews = reviews_by_rule.get(semantic_rule_id, [])

        if rule_type == "reference_only" or not rule.get("classification", {}).get("coverage_eligible", True):
            coverage_status = "not_applicable"
            pass_status = "not_applicable"
            present_case_types: list[str] = []
            accepted_case_types: list[str] = []
            missing_case_types: list[str] = []
        else:
            present_case_types = sorted({r.get("case_type") for r in relevant_reviews if r.get("case_type")})
            accepted_case_types = sorted({
                r.get("case_type")
                for r in relevant_reviews
                if r.get("case_type")
                and r.get("case_type_accepted") is True
                and r.get("coverage_relevance") == "direct"
                and r.get("is_blocking") is False
            })
            missing_case_types = sorted(set(required_case_types) - set(accepted_case_types))

            if not relevant_reviews:
                coverage_status = "uncovered"
                pass_status = "fail"
            elif not required_case_types:
                coverage_status = "fully_covered"
                pass_status = "pass"
            elif not missing_case_types:
                coverage_status = "fully_covered"
                pass_status = "pass"
            elif accepted_case_types:
                coverage_status = "partially_covered"
                pass_status = "fail"
            else:
                coverage_status = "uncovered"
                pass_status = "fail"

        status_by_rule[semantic_rule_id] = {
            "rule_type": rule_type,
            "required_case_types": required_case_types,
            "optional_case_types": optional_case_types,
            "present_case_types": present_case_types,
            "accepted_case_types": accepted_case_types,
            "missing_case_types": missing_case_types,
            "rule_coverage_status": coverage_status,
            "rule_pass_status": pass_status,
            "review_count": len(relevant_reviews),
        }
        counts[coverage_status] += 1

    total = len(status_by_rule)
    governance = _review_governance_summary(reviews)
    return {
        "total_requirements": total,
        "fully_covered": counts.get("fully_covered", 0),
        "partially_covered": counts.get("partially_covered", 0),
        "uncovered": counts.get("uncovered", 0),
        "not_applicable": counts.get("not_applicable", 0),
        "coverage_percent": round((counts.get("fully_covered", 0) / total) * 100, 2) if total else 0.0,
        **governance,
        "status_by_rule": status_by_rule,
    }


def _build_checker_items(rules_by_id: dict[str, dict], maker_records: list[dict]) -> list[dict]:
    items: list[dict] = []
    for maker_record in maker_records:
        semantic_rule_id = maker_record["semantic_rule_id"]
        rule = rules_by_id.get(semantic_rule_id)
        if not rule:
            raise ValueError(
                f"Maker record references missing semantic rule '{semantic_rule_id}'."
            )
        for scenario in maker_record.get("scenarios", []):
            items.append(
                {
                    "semantic_rule_id": semantic_rule_id,
                    "feature": maker_record.get("feature"),
                    "scenario": scenario,
                    "semantic_rule": rule,
                    "required_case_types": _required_case_types(rule)["required"],
                }
            )
    return items


def _normalize_case_id(case_id: str) -> str:
    return re.sub(r'[-_]+', '-', case_id.strip())


def _index_checker_batch(batch: list[dict]) -> dict[str, dict]:
    indexed: dict[str, dict] = {}
    for item in batch:
        scenario_id = item.get("scenario", {}).get("scenario_id")
        if scenario_id:
            indexed[scenario_id] = item
            indexed[_normalize_case_id(scenario_id)] = item
    return indexed


def run_checker_pipeline(
    config: ProjectConfig,
    semantic_rules_path: Path,
    maker_cases_path: Path,
    output_dir: Path,
    limit: int | None,
    batch_size: int,
    resume_from: Path | None,
    only_case_ids: set[str] | None = None,
    previous_reviews_path: Path | None = None,
) -> dict:
    logger.info("Starting checker pipeline. rules=%s cases=%s output_dir=%s limit=%s batch_size=%s resume_from=%s only_case_ids=%s", semantic_rules_path, maker_cases_path, output_dir, limit, batch_size, resume_from, only_case_ids)
    semantic_rules = _load_semantic_rules(semantic_rules_path)
    rules_by_id = {item["semantic_rule_id"]: item for item in semantic_rules if "semantic_rule_id" in item}

    maker_records = load_jsonl(maker_cases_path)
    if limit is not None:
        maker_records = maker_records[:limit]

    provider = build_provider(config.provider_for_role("checker"))
    run_id = timestamp_slug()
    run_dir = ensure_dir(output_dir / run_id)
    reviews_path = run_dir / "checker_reviews.jsonl"
    raw_path = run_dir / "checker_raw_responses.jsonl"
    summary_path = run_dir / "summary.json"
    coverage_path = run_dir / "coverage_report.json"

    review_items = _build_checker_items(rules_by_id, maker_records)

    inherited_reviews: dict[str, dict] = {}
    if only_case_ids is not None and previous_reviews_path and previous_reviews_path.exists():
        for record in load_jsonl(previous_reviews_path):
            prev_case_id = record.get("case_id")
            if prev_case_id and prev_case_id not in only_case_ids:
                inherited_reviews[prev_case_id] = record
        review_items = [
            item
            for item in review_items
            if item.get("scenario", {}).get("scenario_id") in only_case_ids
        ]
        logger.info("Checker incremental mode: only_case_ids=%s inherited=%s", len(only_case_ids), len(inherited_reviews))

    completed_case_ids: set[str] = set()
    if resume_from and resume_from.exists():
        for record in load_jsonl(resume_from):
            case_id = record.get("case_id")
            if case_id:
                completed_case_ids.add(case_id)
                completed_case_ids.add(_normalize_case_id(case_id))
        review_items = [
            item
            for item in review_items
            if item.get("scenario", {}).get("scenario_id") not in completed_case_ids
            and _normalize_case_id(item.get("scenario", {}).get("scenario_id", "")) not in completed_case_ids
        ]

    reviews: list[dict] = []

    for batch in _chunked(review_items, batch_size):
        logger.info("Checker batch start. run_id=%s scenario_ids=%s", run_id, [item.get("scenario", {}).get("scenario_id") for item in batch])
        response = provider.generate(
            system_prompt=CHECKER_SYSTEM_PROMPT,
            user_prompt=build_checker_user_prompt(batch),
        )
        raw_record = {
            "run_id": run_id,
            "batch_scenario_ids": [item.get("scenario", {}).get("scenario_id") for item in batch],
            "response": response.raw_response,
        }
        append_jsonl(raw_path, [raw_record])

        indexed_batch = _index_checker_batch(batch)
        expected_case_map = {
            item["scenario"]["scenario_id"]: item["semantic_rule_id"]
            for item in batch
        }

        normalized_payload = parse_json_object(response.content)
        if only_case_ids is not None and isinstance(normalized_payload.get("results"), list):
            expected_case_ids = set(expected_case_map)
            if len(expected_case_ids) == 1:
                expected_case_id = next(iter(expected_case_ids))
                for result in normalized_payload["results"]:
                    returned_case_id = str(result.get("case_id", ""))
                    if returned_case_id not in expected_case_ids and returned_case_id.startswith(expected_case_id):
                        result["case_id"] = expected_case_id
            normalized_payload["results"] = [
                result
                for result in normalized_payload["results"]
                if result.get("case_id") in expected_case_ids
            ]
        if isinstance(normalized_payload.get("results"), list):
            for result in normalized_payload["results"]:
                scenario_item = indexed_batch.get(result.get("case_id", "")) or indexed_batch.get(
                    _normalize_case_id(result.get("case_id", ""))
                )
                if scenario_item:
                    result["case_id"] = scenario_item["scenario"]["scenario_id"]
                    result["semantic_rule_id"] = scenario_item["semantic_rule_id"]
                    result.setdefault("case_type", scenario_item["scenario"].get("case_type") or scenario_item["scenario"].get("scenario_type"))
                    result.setdefault("case_type_accepted", True)
                    result.setdefault("coverage_relevance", "direct")
                    result.setdefault("blocking_findings_count", 0)
                    result.setdefault("is_blocking", False)
                    result.setdefault("blocking_category", "none")
                    result.setdefault("blocking_reason", "")
                    result.setdefault("checker_confidence", 0.5)
                    result["blocking_category"] = _normalize_blocking_category(result.get("blocking_category"))
                    if result.get("is_blocking") is False:
                        result["blocking_category"] = "none"
                        result["blocking_reason"] = ""
                    else:
                        result["blocking_reason"] = result.get("blocking_reason") or _default_blocking_reason(result)
                        if not result.get("checker_confidence"):
                            result["checker_confidence"] = 0.75
                    _governance_defaults(result)

        payload = validate_checker_payload(normalized_payload, expected_case_map=expected_case_map)
        for result in payload["results"]:
            result["run_id"] = run_id
            _governance_defaults(result)
            reviews.append(result)
            append_jsonl(reviews_path, [result])
        logger.info("Checker batch done. run_id=%s accumulated_reviews=%s", run_id, len(reviews))

    # New reviews were already written per-batch above; only write inherited ones here.
    all_reviews = list(inherited_reviews.values()) + reviews
    if inherited_reviews:
        append_jsonl(reviews_path, list(inherited_reviews.values()))
    coverage = _calculate_coverage(semantic_rules, all_reviews)
    write_json(coverage_path, coverage)
    governance = _review_governance_summary(all_reviews)

    summary = {
        "run_id": run_id,
        "role": "checker",
        "input_rules": str(semantic_rules_path),
        "input_cases": str(maker_cases_path),
        "output_dir": str(run_dir),
        "review_count": len(all_reviews),
        "new_review_count": len(reviews),
        "inherited_review_count": len(inherited_reviews),
        "remaining_after_resume": 0,
        "results_path": str(reviews_path),
        "coverage_report_path": str(coverage_path),
        "raw_path": str(raw_path),
        **governance,
    }
    write_json(summary_path, summary)
    logger.info("Checker pipeline completed. summary=%s", summary)
    return summary


def _case_map_from_maker_records(maker_records: list[dict]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for record in maker_records:
        semantic_rule_id = record.get("semantic_rule_id")
        for scenario in record.get("scenarios", []):
            scenario_id = scenario.get("scenario_id")
            if scenario_id and semantic_rule_id:
                mapping[scenario_id] = semantic_rule_id
    return mapping


def _rewrite_targets(human_payload: dict) -> dict[str, list[str]]:
    """Return {rule_id: [case_id, ...]} for all cases marked review_decision == 'rewrite'."""
    targets: dict[str, list[str]] = {}
    for item in human_payload.get("reviews", []):
        if item.get("review_decision") == "rewrite":
            rule_id = item.get("semantic_rule_id")
            case_id = item.get("case_id")
            if rule_id and case_id:
                if rule_id not in targets:
                    targets[rule_id] = []
                if case_id not in targets[rule_id]:
                    targets[rule_id].append(case_id)
    return targets


def _merge_rewritten_records(original_records: list[dict], rewritten_records: list[dict]) -> list[dict]:
    rewritten_by_rule = {item["semantic_rule_id"]: item for item in rewritten_records}
    merged: list[dict] = []
    replaced: set[str] = set()
    for record in original_records:
        semantic_rule_id = record.get("semantic_rule_id")
        if semantic_rule_id in rewritten_by_rule:
            merged.append(rewritten_by_rule[semantic_rule_id])
            replaced.add(semantic_rule_id)
        else:
            merged.append(record)
    for semantic_rule_id, record in rewritten_by_rule.items():
        if semantic_rule_id not in replaced:
            merged.append(record)
    return merged


def _merge_cases_in_records(
    original_records: list[dict],
    rewritten_scenarios_by_rule: dict[str, dict[str, dict]],
    rewritten_features_by_rule: dict[str, str] | None = None,
) -> list[dict]:
    """Replace only targeted scenarios (by case_id) in original records; leave all others byte-identical."""
    rewritten_features_by_rule = rewritten_features_by_rule or {}
    merged: list[dict] = []
    for record in original_records:
        rule_id = record.get("semantic_rule_id")
        case_map = rewritten_scenarios_by_rule.get(rule_id)
        if not case_map:
            merged.append(record)
        else:
            new_scenarios = []
            for scenario in record.get("scenarios", []):
                case_id = scenario.get("scenario_id")
                new_scenarios.append(case_map[case_id] if case_id and case_id in case_map else scenario)
            new_record = dict(record)
            if rule_id in rewritten_features_by_rule:
                new_record["feature"] = rewritten_features_by_rule[rule_id]
            new_record["scenarios"] = new_scenarios
            merged.append(new_record)
    return merged


def run_rewrite_pipeline(
    config: ProjectConfig,
    semantic_rules_path: Path,
    maker_cases_path: Path,
    checker_reviews_path: Path,
    human_reviews_path: Path,
    output_dir: Path,
    limit: int | None,
    batch_size: int,
) -> dict:
    semantic_rules = _load_semantic_rules(semantic_rules_path)
    rules_by_id = {item["semantic_rule_id"]: item for item in semantic_rules if "semantic_rule_id" in item}
    maker_records = load_jsonl(maker_cases_path)
    checker_reviews = load_jsonl(checker_reviews_path)
    case_map = _case_map_from_maker_records(maker_records)
    human_payload = validate_human_review_payload(load_json(human_reviews_path), expected_case_map=case_map)

    rewrite_targets = _rewrite_targets(human_payload)
    logger.info("Rewrite targets (rule->cases)=%s", rewrite_targets)

    target_rule_ids = list(rewrite_targets.keys())
    if limit is not None:
        target_rule_ids = target_rule_ids[:limit]
        rewrite_targets = {k: rewrite_targets[k] for k in target_rule_ids}

    provider = build_provider(config.provider_for_role("maker"))
    run_id = timestamp_slug()
    run_dir = ensure_dir(output_dir / run_id)
    rewritten_path = run_dir / "rewritten_cases.jsonl"
    merged_path = run_dir / "merged_cases.jsonl"
    raw_path = run_dir / "rewrite_raw_responses.jsonl"
    summary_path = run_dir / "summary.json"

    checker_reviews_by_rule: dict[str, list[dict]] = defaultdict(list)
    for review in checker_reviews:
        checker_reviews_by_rule[review["semantic_rule_id"]].append(review)

    human_reviews_by_rule: dict[str, list[dict]] = defaultdict(list)
    for review in human_payload.get("reviews", []):
        human_reviews_by_rule[review["semantic_rule_id"]].append(review)

    rewrite_items: list[dict] = []
    for semantic_rule_id in target_rule_ids:
        rule = rules_by_id.get(semantic_rule_id)
        current_cases = next((item for item in maker_records if item.get("semantic_rule_id") == semantic_rule_id), None)
        if not rule or not current_cases:
            continue
        target_case_ids = rewrite_targets.get(semantic_rule_id, [])
        target_case_id_set = set(target_case_ids)
        rewrite_items.append(
            {
                "semantic_rule": _augment_rule_with_case_requirements(rule),
                "current_maker_record": current_cases,
                "rewrite_target_case_ids": target_case_ids,
                "checker_reviews": [r for r in checker_reviews_by_rule.get(semantic_rule_id, []) if r.get("case_id") in target_case_id_set],
                "human_reviews": [r for r in human_reviews_by_rule.get(semantic_rule_id, []) if r.get("case_id") in target_case_id_set],
            }
        )

    rewritten_scenarios_by_rule: dict[str, dict[str, dict]] = {}
    rewritten_features_by_rule: dict[str, str] = {}
    all_rewritten_case_ids: list[str] = []
    total_scenarios = 0
    for batch in _chunked(rewrite_items, batch_size) if rewrite_items else []:
        response = provider.generate(
            system_prompt=REWRITE_SYSTEM_PROMPT,
            user_prompt=build_rewrite_user_prompt(batch),
        )
        raw_record = {
            "run_id": run_id,
            "batch_semantic_rule_ids": [item["semantic_rule"]["semantic_rule_id"] for item in batch],
            "response": response.raw_response,
        }
        append_jsonl(raw_path, [raw_record])
        raw_payload = parse_json_object(response.content)
        for result in raw_payload.get("results", []):
            if not isinstance(result, dict):
                continue
            rule_id = result.get("semantic_rule_id", "")
            if not rule_id:
                continue
            target_case_ids = rewrite_targets.get(rule_id, [])
            if isinstance(result.get("feature"), str):
                rewritten_features_by_rule[rule_id] = result["feature"]
            case_map: dict[str, dict] = {}
            scenarios = [item for item in result.get("scenarios", []) if isinstance(item, dict)]
            for index, scenario in enumerate(scenarios):
                if not isinstance(scenario, dict):
                    continue
                case_id = scenario.get("scenario_id")
                if case_id not in target_case_ids and len(scenarios) == len(target_case_ids):
                    case_id = target_case_ids[index]
                    scenario["scenario_id"] = case_id
                if case_id:
                    case_type = scenario.get("case_type") or scenario.get("scenario_type")
                    scenario["case_type"] = case_type
                    case_map[case_id] = scenario
                    all_rewritten_case_ids.append(case_id)
                    total_scenarios += 1
            rewritten_scenarios_by_rule[rule_id] = case_map

    merged_records = _merge_cases_in_records(maker_records, rewritten_scenarios_by_rule, rewritten_features_by_rule)
    if merged_records:
        append_jsonl(merged_path, merged_records)
    rewritten_records_for_log = [
        next((r for r in merged_records if r.get("semantic_rule_id") == rid), {})
        for rid in rewritten_scenarios_by_rule
    ]
    if rewritten_records_for_log:
        append_jsonl(rewritten_path, [r for r in rewritten_records_for_log if r])

    summary = {
        "run_id": run_id,
        "role": "maker_rewrite",
        "input_rules": str(semantic_rules_path),
        "input_maker_cases": str(maker_cases_path),
        "input_checker_reviews": str(checker_reviews_path),
        "input_human_reviews": str(human_reviews_path),
        "output_dir": str(run_dir),
        "target_rule_count": len(rewrite_items),
        "rewritten_rule_count": len(rewritten_scenarios_by_rule),
        "rewritten_scenario_count": total_scenarios,
        "rewritten_case_ids": all_rewritten_case_ids,
        "rewritten_cases_path": str(rewritten_path),
        "merged_cases_path": str(merged_path),
        "raw_path": str(raw_path),
    }
    write_json(summary_path, summary)
    logger.info("Rewrite pipeline completed. summary=%s", summary)
    return summary
