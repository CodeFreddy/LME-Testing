from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path

from .config import ProjectConfig
from .prompts import (
    BDD_SYSTEM_PROMPT,
    CHECKER_SYSTEM_PROMPT,
    MAKER_SYSTEM_PROMPT,
    build_bdd_user_prompt,
    build_checker_user_prompt,
    build_maker_user_prompt,
)
from .bdd_export import write_feature_files, write_feature_files_from_llm, write_step_definitions, write_step_definitions_from_llm
from .providers import build_provider
from .schemas import CASE_TYPES, parse_json_object, validate_checker_payload, validate_maker_payload
from .storage import append_jsonl, ensure_dir, load_json, load_jsonl, timestamp_slug, write_json


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


def run_maker_pipeline(
    config: ProjectConfig,
    semantic_rules_path: Path,
    output_dir: Path,
    limit: int | None,
    batch_size: int,
    resume_from: Path | None,
) -> dict:
    semantic_rules = load_json(semantic_rules_path)
    if not isinstance(semantic_rules, list):
        raise ValueError("semantic_rules.json must contain a list.")
    if limit is not None:
        semantic_rules = semantic_rules[:limit]

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
            present_case_types = sorted({r.get("case_type") for r in relevant_reviews if r.get("case_type") in CASE_TYPES})
            accepted_case_types = sorted({
                r.get("case_type")
                for r in relevant_reviews
                if r.get("case_type") in CASE_TYPES
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
    return {
        "total_requirements": total,
        "fully_covered": counts.get("fully_covered", 0),
        "partially_covered": counts.get("partially_covered", 0),
        "uncovered": counts.get("uncovered", 0),
        "not_applicable": counts.get("not_applicable", 0),
        "coverage_percent": round((counts.get("fully_covered", 0) / total) * 100, 2) if total else 0.0,
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
) -> dict:
    semantic_rules = load_json(semantic_rules_path)
    if not isinstance(semantic_rules, list):
        raise ValueError("semantic_rules.json must contain a list.")
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

        payload = validate_checker_payload(normalized_payload, expected_case_map=expected_case_map)
        for result in payload["results"]:
            result["run_id"] = run_id
            reviews.append(result)
            append_jsonl(reviews_path, [result])

    coverage = _calculate_coverage(semantic_rules, reviews)
    write_json(coverage_path, coverage)

    summary = {
        "run_id": run_id,
        "role": "checker",
        "input_rules": str(semantic_rules_path),
        "input_cases": str(maker_cases_path),
        "output_dir": str(run_dir),
        "review_count": len(reviews),
        "remaining_after_resume": 0,
        "results_path": str(reviews_path),
        "coverage_report_path": str(coverage_path),
        "raw_path": str(raw_path),
    }
    write_json(summary_path, summary)
    return summary


def run_bdd_pipeline(
    config: ProjectConfig,
    maker_cases_path: Path,
    output_dir: Path,
    limit: int | None,
    batch_size: int,
    resume_from: Path | None,
) -> dict:
    """Generate refined BDD/Gherkin from maker test cases."""
    maker_records = load_jsonl(maker_cases_path)
    if limit is not None:
        maker_records = maker_records[:limit]

    completed_ids: set[str] = set()
    if resume_from and resume_from.exists():
        for record in load_jsonl(resume_from):
            # BDD records have scenario_id inside scenarios array
            for s in record.get("scenarios", []):
                scenario_id = s.get("scenario_id")
                if scenario_id:
                    completed_ids.add(scenario_id)
        maker_records = [
            record
            for record in maker_records
            if not any(
                s.get("scenario_id") in completed_ids
                for s in record.get("scenarios", [])
            )
        ]

    provider = build_provider(config.provider_for_role("maker"))
    run_id = timestamp_slug()
    run_dir = ensure_dir(output_dir / run_id)
    results_path = run_dir / "bdd_cases.jsonl"
    raw_path = run_dir / "bdd_raw_responses.jsonl"
    summary_path = run_dir / "summary.json"

    # Flatten scenarios for batch processing
    all_scenarios: list[dict] = []
    for record in maker_records:
        for scenario in record.get("scenarios", []):
            all_scenarios.append({
                "semantic_rule_id": record["semantic_rule_id"],
                "feature": record.get("feature", ""),
                "scenario": scenario,
            })

    total_cases = 0

    for batch in _chunked(all_scenarios, batch_size):
        response = provider.generate(
            system_prompt=BDD_SYSTEM_PROMPT,
            user_prompt=build_bdd_user_prompt(batch),
        )
        raw_record = {
            "run_id": run_id,
            "batch_scenario_ids": [item.get("scenario", {}).get("scenario_id") for item in batch],
            "response": response.raw_response,
        }
        append_jsonl(raw_path, [raw_record])

        payload = parse_json_object(response.content)
        results = payload.get("results", [])
        for result in results:
            result["run_id"] = run_id
            append_jsonl(results_path, [result])
        total_cases += len(results)

    summary = {
        "run_id": run_id,
        "role": "bdd",
        "input_cases": str(maker_cases_path),
        "output_dir": str(run_dir),
        "processed_scenario_count": total_cases,
        "results_path": str(results_path),
        "raw_path": str(raw_path),
    }
    write_json(summary_path, summary)

    # Export feature files and step definitions from LLM output
    if results_path.exists():
        bdd_results = load_jsonl(results_path)
        if bdd_results:
            feature_files = write_feature_files_from_llm(bdd_results, run_dir)
            step_file = write_step_definitions_from_llm(bdd_results, run_dir)
            summary["feature_files_count"] = len(feature_files)
            summary["feature_files"] = [str(f) for f in feature_files]
            summary["step_definitions_file"] = str(step_file)
            write_json(summary_path, summary)

    return summary
