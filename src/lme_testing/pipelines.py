from __future__ import annotations

import hashlib
import json
import logging
import re
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

logger = logging.getLogger(__name__)

from .config import ConfigError, ProjectConfig, ProviderConfig
from .prompts import (
    BDD_SYSTEM_PROMPT,
    CHECKER_SYSTEM_PROMPT,
    MAKER_SYSTEM_PROMPT,
    PLANNER_SYSTEM_PROMPT,
    REWRITE_SYSTEM_PROMPT,
    BDD_PROMPT_VERSION,
    CHECKER_PROMPT_VERSION,
    MAKER_PROMPT_VERSION,
    PLANNER_PROMPT_VERSION,
    PIPELINE_VERSION,
    REWRITE_PROMPT_VERSION,
    build_bdd_user_prompt,
    build_checker_user_prompt,
    build_maker_user_prompt,
    build_planner_user_prompt,
    build_rewrite_user_prompt,
)
from .bdd_export import (
    apply_human_step_edits,
    render_gherkin_from_normalized_bdd,
    render_steps_from_normalized_bdd,
    write_feature_files,
    write_step_definitions,
)
from .providers import build_provider
from .schemas import (
    CASE_TYPES,
    SchemaError,
    normalize_human_review_decision,
    parse_json_object,
    validate_checker_payload,
    validate_human_review_payload,
    validate_maker_payload,
    validate_normalized_bdd_payload,
    validate_planner_payload,
)
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

BDD_GENERATION_MODES = {"llm", "llm-with-fallback", "deterministic"}


def _bdd_provider_config(config: ProjectConfig) -> tuple[str, ProviderConfig]:
    try:
        return "bdd", config.provider_for_role("bdd")
    except ConfigError:
        return "maker", config.provider_for_role("maker")


def _finish_reason(raw_response: dict) -> str | None:
    try:
        return raw_response["choices"][0].get("finish_reason")
    except (KeyError, IndexError, TypeError, AttributeError):
        return None


def _bdd_failure_reason(exc: SchemaError, raw_response: dict | None) -> str:
    finish_reason = _finish_reason(raw_response or {})
    if finish_reason == "length":
        return f"truncated_output: {exc}"
    return str(exc)


def _artifact_hash(path: Path) -> str:
    """Return a short SHA256 hex digest of a file, for source artifact traceability."""
    if path.exists():
        return hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    return "unknown"


def run_planner_pipeline(
    config: ProjectConfig,
    semantic_rules_path: Path,
    output_dir: Path,
    limit: int | None,
    batch_size: int,
    resume_from: Path | None,
) -> dict:
    """Generate test planning artifacts from semantic rules."""
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

    provider_cfg = config.provider_for_role("planner")
    provider = build_provider(provider_cfg)
    run_id = timestamp_slug()
    run_dir = ensure_dir(output_dir / run_id)
    results_path = run_dir / "planner_results.jsonl"
    raw_path = run_dir / "planner_raw_responses.jsonl"
    summary_path = run_dir / "summary.json"

    total_batches = 0

    for batch in _chunked(semantic_rules, batch_size):
        response = provider.generate(
            system_prompt=PLANNER_SYSTEM_PROMPT,
            user_prompt=build_planner_user_prompt(batch),
        )
        raw_record = {
            "run_id": run_id,
            "batch_semantic_rule_ids": [item["semantic_rule_id"] for item in batch],
            "response": response.raw_response,
        }
        append_jsonl(raw_path, [raw_record])

        payload = validate_planner_payload(
            parse_json_object(response.content),
            expected_rule_ids=[item["semantic_rule_id"] for item in batch],
        )
        for item in payload["results"]:
            item["run_id"] = run_id
            # Carry through paragraph_ids and atomic_rule_ids from source rule
            source_rule = next(
                (r for r in batch if r.get("semantic_rule_id") == item.get("semantic_rule_id")), {}
            )
            if "paragraph_ids" not in item:
                item["paragraph_ids"] = source_rule.get("source", {}).get("paragraph_ids", [])
            if "atomic_rule_ids" not in item:
                item["atomic_rule_ids"] = source_rule.get("source", {}).get("atomic_rule_ids", [])
            if "rule_type" not in item:
                item["rule_type"] = source_rule.get("classification", {}).get("rule_type", "unknown")
            append_jsonl(results_path, [item])
        total_batches += 1

    summary = {
        "run_id": run_id,
        "role": "planner",
        "pipeline_version": PIPELINE_VERSION,
        "prompt_version": PLANNER_PROMPT_VERSION,
        "provider": provider_cfg.name,
        "model": provider_cfg.model,
        "input_path": str(semantic_rules_path),
        "source_artifact_hash": _artifact_hash(semantic_rules_path),
        "output_dir": str(run_dir),
        "processed_rule_count": len(semantic_rules),
        "batch_count": total_batches,
        "results_path": str(results_path),
        "raw_path": str(raw_path),
    }
    write_json(summary_path, summary)
    return summary


def _chunked(items: list[dict], size: int) -> list[list[dict]]:
    if size <= 0:
        raise ValueError("batch_size must be greater than zero.")
    return [items[index:index + size] for index in range(0, len(items), size)]


def _maker_record_from_result(result: dict, run_id: str, source_rule: dict | None = None) -> dict:
    record = {
        "run_id": run_id,
        "semantic_rule_id": result["semantic_rule_id"],
        "requirement_ids": result.get("requirement_ids", []),
        "feature": result["feature"],
        "scenarios": result["scenarios"],
    }
    if source_rule:
        record["paragraph_ids"] = source_rule.get("source", {}).get("paragraph_ids", [])
    return record


def _required_case_types(rule: dict) -> dict:
    rule_type = rule.get("classification", {}).get("rule_type", "reference_only")
    mapping = RULE_TYPE_CASE_REQUIREMENTS.get(rule_type, {"required": ["positive"], "optional": []})
    return {
        "rule_type": rule_type,
        "required": list(mapping["required"]),
        "optional": list(mapping["optional"]),
    }


def _is_maker_testable(rule: dict) -> bool:
    classification = rule.get("classification", {})
    rule_type = classification.get("rule_type")
    if rule_type == "reference_only":
        return False
    if classification.get("coverage_eligible") is False:
        return False
    return True


def analyze_maker_input_quality(semantic_rules: list[dict]) -> dict:
    """Return deterministic quality signals for maker input rules."""
    rule_type_counts = Counter()
    testability_counts = Counter()
    priority_counts = Counter()
    total_required_case_types = 0
    testable_rule_ids: list[str] = []
    excluded_rule_ids: list[str] = []

    for rule in semantic_rules:
        classification = rule.get("classification", {})
        rule_type = classification.get("rule_type", "unknown")
        rule_type_counts[rule_type] += 1
        testability_counts[classification.get("testability", "unknown")] += 1
        priority_counts[classification.get("priority", "unknown")] += 1
        total_required_case_types += len(_required_case_types(rule)["required"])
        semantic_rule_id = rule.get("semantic_rule_id")
        if _is_maker_testable(rule):
            if semantic_rule_id:
                testable_rule_ids.append(semantic_rule_id)
        elif semantic_rule_id:
            excluded_rule_ids.append(semantic_rule_id)

    total_rules = len(semantic_rules)
    reference_only_count = rule_type_counts.get("reference_only", 0)
    maker_testable_count = len(testable_rule_ids)
    return {
        "total_rules": total_rules,
        "maker_testable_count": maker_testable_count,
        "maker_excluded_count": len(excluded_rule_ids),
        "reference_only_count": reference_only_count,
        "reference_only_ratio": round(reference_only_count / total_rules, 4) if total_rules else 0.0,
        "total_required_case_types": total_required_case_types,
        "rule_type_counts": dict(sorted(rule_type_counts.items())),
        "testability_counts": dict(sorted(testability_counts.items())),
        "priority_counts": dict(sorted(priority_counts.items())),
        "testable_rule_ids": testable_rule_ids,
        "excluded_rule_ids": excluded_rule_ids,
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
    concurrency: int = 1,
    provider_out: list | None = None,
) -> dict:
    semantic_rules = load_json(semantic_rules_path)
    if not isinstance(semantic_rules, list):
        raise ValueError("semantic_rules.json must contain a list.")
    if limit is not None:
        semantic_rules = semantic_rules[:limit]

    # Build completed set from resume file
    completed_ids: set[str] = set()
    if resume_from and resume_from.exists():
        for record in load_jsonl(resume_from):
            semantic_rule_id = record.get("semantic_rule_id")
            if semantic_rule_id:
                completed_ids.add(semantic_rule_id)

    # Deduplicate by semantic_rule_id (artifacts may contain duplicate entries)
    seen_ids: set[str] = set()
    unique_rules: list[dict] = []
    for rule in semantic_rules:
        sid = rule.get("semantic_rule_id")
        if sid and sid not in seen_ids:
            seen_ids.add(sid)
            unique_rules.append(rule)
    candidate_rules = [
        rule for rule in unique_rules
        if rule.get("semantic_rule_id") not in completed_ids
    ]
    quality_report = analyze_maker_input_quality(candidate_rules)
    excluded_rules = [rule for rule in candidate_rules if not _is_maker_testable(rule)]
    semantic_rules = [rule for rule in candidate_rules if _is_maker_testable(rule)]

    provider_cfg = config.provider_for_role("maker")
    provider = build_provider(provider_cfg)
    if provider_out is not None:
        provider_out.append(provider)
    run_id = timestamp_slug()
    run_dir = ensure_dir(output_dir / run_id)
    results_path = run_dir / "maker_cases.jsonl"
    raw_path = run_dir / "maker_raw_responses.jsonl"
    summary_path = run_dir / "summary.json"
    quality_report_path = run_dir / "maker_input_quality.json"
    excluded_rules_path = run_dir / "maker_excluded_rules.json"
    write_json(quality_report_path, quality_report)
    write_json(excluded_rules_path, excluded_rules)

    total_batches = 0
    total_cases = 0
    batches = list(_chunked(semantic_rules, batch_size))
    total_batch_count = len(batches)
    total_rule_count = len(semantic_rules)
    if concurrency <= 0:
        raise ValueError("concurrency must be greater than zero.")
    effective_concurrency = min(concurrency, total_batch_count or 1)
    print(
        f"[maker] Input quality: {quality_report['maker_testable_count']} testable, "
        f"{quality_report['maker_excluded_count']} excluded, "
        f"reference_only_ratio={quality_report['reference_only_ratio']}",
        flush=True,
    )
    print(
        f"[maker] Starting: {total_rule_count} rules in {total_batch_count} batches "
        f"(batch_size={batch_size}, concurrency={effective_concurrency})",
        flush=True,
    )

    def _run_batch(batch_num: int, batch: list[dict]) -> dict:
        batch_rule_ids = [item["semantic_rule_id"] for item in batch]
        print(f"[maker] Batch {batch_num}/{total_batch_count}: calling API for rules {batch_rule_ids}...", flush=True)
        augmented_batch = [_augment_rule_with_case_requirements(item) for item in batch]

        # Retry once on JSON parse/validation errors
        for attempt in range(2):
            response = provider.generate(
                system_prompt=MAKER_SYSTEM_PROMPT,
                user_prompt=build_maker_user_prompt(augmented_batch),
            )
            raw_record = {
                "run_id": run_id,
                "batch_semantic_rule_ids": batch_rule_ids,
                "response": response.raw_response,
            }

            reference_only_rules = {
                item["semantic_rule_id"]
                for item in batch
                if not _is_maker_testable(item)
            }
            try:
                payload = validate_maker_payload(
                    parse_json_object(response.content),
                    expected_rule_ids=batch_rule_ids,
                    expected_required_case_types={
                        item["semantic_rule_id"]: _required_case_types(item)["required"]
                        for item in batch
                    },
                    reference_only_rules=reference_only_rules,
                )
                break  # Success
            except SchemaError as exc:
                if attempt == 0 and "not valid JSON" in str(exc):
                    print(f"[maker] Batch {batch_num}: JSON error, retrying once...", flush=True)
                    continue  # Retry
                raise

        source_by_id = {item["semantic_rule_id"]: item for item in batch}
        records = [
            _maker_record_from_result(item, run_id=run_id, source_rule=source_by_id.get(item["semantic_rule_id"]))
            for item in payload["results"]
        ]
        batch_case_count = sum(len(item["scenarios"]) for item in payload["results"])
        return {
            "batch_num": batch_num,
            "raw_record": raw_record,
            "records": records,
            "case_count": batch_case_count,
            "result_count": len(records),
        }

    def _write_batch_result(batch_num: int, result: dict) -> None:
        nonlocal total_batches, total_cases
        append_jsonl(raw_path, [result["raw_record"]])
        append_jsonl(results_path, result["records"])
        total_batches += 1
        total_cases += result["case_count"]
        print(f"[maker] Batch {batch_num}/{total_batch_count} done: generated {result['case_count']} scenarios", flush=True)

    if effective_concurrency == 1:
        for batch_num, batch in enumerate(batches, start=1):
            _write_batch_result(batch_num, _run_batch(batch_num, batch))
    else:
        batch_results: dict[int, dict] = {}
        first_error: Exception | None = None
        with ThreadPoolExecutor(max_workers=effective_concurrency) as executor:
            futures = {
                executor.submit(_run_batch, batch_num, batch): batch_num
                for batch_num, batch in enumerate(batches, start=1)
            }
            for future in as_completed(futures):
                batch_num = futures[future]
                try:
                    batch_results[batch_num] = future.result()
                except Exception as exc:
                    if first_error is None:
                        first_error = exc
        for batch_num in sorted(batch_results):
            _write_batch_result(batch_num, batch_results[batch_num])
        if first_error is not None:
            raise first_error

    summary = {
        "run_id": run_id,
        "role": "maker",
        "pipeline_version": PIPELINE_VERSION,
        "prompt_version": MAKER_PROMPT_VERSION,
        "provider": provider_cfg.name,
        "model": provider_cfg.model,
        "input_path": str(semantic_rules_path),
        "source_artifact_hash": _artifact_hash(semantic_rules_path),
        "output_dir": str(run_dir),
        "processed_rule_count": len(semantic_rules),
        "input_rule_count": len(candidate_rules),
        "excluded_rule_count": len(excluded_rules),
        "batch_count": total_batches,
        "scenario_count": total_cases,
        "results_path": str(results_path),
        "raw_path": str(raw_path),
        "quality_report_path": str(quality_report_path),
        "excluded_rules_path": str(excluded_rules_path),
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
            "paragraph_ids": rule.get("source", {}).get("paragraph_ids", []),
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


def _coverage_status_weight(status: str) -> int:
    """Weight for coverage status, used in drift calculation."""
    return {"fully_covered": 3, "partially_covered": 2, "uncovered": 1, "not_applicable": 0}.get(status, 0)


def calculate_drift(current_coverage: dict, previous_coverage: dict) -> dict:
    """Calculate drift between two coverage reports.

    Returns a drift report showing which rules improved, regressed, or are new.
    """
    current_status = current_coverage.get("status_by_rule", {})
    previous_status = previous_coverage.get("status_by_rule", {})

    rules_improved: list[str] = []
    rules_regressed: list[str] = []
    rules_unchanged: list[str] = []
    new_rules: list[str] = []

    all_rules = set(current_status.keys())

    for rule_id in sorted(all_rules):
        current = current_status.get(rule_id, {})
        previous = previous_status.get(rule_id, {})

        current_cov = current.get("rule_coverage_status", "")
        previous_cov = previous.get("rule_coverage_status", "")

        if rule_id not in previous_status:
            new_rules.append(rule_id)
        elif _coverage_status_weight(current_cov) > _coverage_status_weight(previous_cov):
            rules_improved.append(rule_id)
        elif _coverage_status_weight(current_cov) < _coverage_status_weight(previous_cov):
            rules_regressed.append(rule_id)
        else:
            rules_unchanged.append(rule_id)

    current_pct = current_coverage.get("coverage_percent", 0)
    previous_pct = previous_coverage.get("coverage_percent", 0)

    return {
        "current_coverage_percent": current_pct,
        "previous_coverage_percent": previous_pct,
        "coverage_delta": round(current_pct - previous_pct, 2),
        "rules_improved": rules_improved,
        "rules_regressed": rules_regressed,
        "rules_unchanged": rules_unchanged,
        "new_rules": new_rules,
        "improved_count": len(rules_improved),
        "regressed_count": len(rules_regressed),
        "unchanged_count": len(rules_unchanged),
        "new_count": len(new_rules),
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


def write_jsonl(path: Path, records: list[dict]) -> None:
    """Write a list of dicts as JSONL."""
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def run_checker_pipeline(
    config: ProjectConfig,
    semantic_rules_path: Path,
    maker_cases_path: Path,
    output_dir: Path,
    limit: int | None,
    batch_size: int,
    resume_from: Path | None,
    concurrency: int = 1,
    only_case_ids: set[str] | None = None,
    previous_reviews_path: Path | None = None,
    provider_out: list | None = None,
) -> dict:
    semantic_rules = load_json(semantic_rules_path)
    if not isinstance(semantic_rules, list):
        raise ValueError("semantic_rules.json must contain a list.")
    rules_by_id = {item["semantic_rule_id"]: item for item in semantic_rules if "semantic_rule_id" in item}

    maker_records = load_jsonl(maker_cases_path)
    if limit is not None:
        maker_records = maker_records[:limit]

    provider_cfg = config.provider_for_role("checker")
    provider = build_provider(provider_cfg)
    if provider_out is not None:
        provider_out.append(provider)
    run_id = timestamp_slug()
    run_dir = ensure_dir(output_dir / run_id)
    reviews_path = run_dir / "checker_reviews.jsonl"
    raw_path = run_dir / "checker_raw_responses.jsonl"
    summary_path = run_dir / "summary.json"
    coverage_path = run_dir / "coverage_report.json"

    review_items = _build_checker_items(rules_by_id, maker_records)
    inherited_reviews: dict[str, dict] = {}
    if only_case_ids is not None:
        target_case_ids = {str(case_id) for case_id in only_case_ids}
        if previous_reviews_path and previous_reviews_path.exists():
            for review in load_jsonl(previous_reviews_path):
                case_id = str(review.get("case_id", ""))
                if case_id and case_id not in target_case_ids:
                    inherited_reviews[case_id] = review
        review_items = [
            item for item in review_items
            if str(item.get("scenario", {}).get("scenario_id", "")) in target_case_ids
        ]

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
    batches = list(_chunked(review_items, batch_size))
    total_batch_count = len(batches)
    total_item_count = len(review_items)
    if concurrency <= 0:
        raise ValueError("concurrency must be greater than zero.")
    effective_concurrency = min(concurrency, total_batch_count or 1)
    print(
        f"[checker] Starting: {total_item_count} cases in {total_batch_count} batches "
        f"(batch_size={batch_size}, concurrency={effective_concurrency})",
        flush=True,
    )

    batches_processed = 0
    failed_batch_num = None
    failed_batch_nums: list[int] = []
    remaining_after_failure = 0

    def _run_batch(batch_num: int, batch: list[dict]) -> dict:
        batch_case_ids = [item.get("scenario", {}).get("scenario_id") for item in batch]
        print(f"[checker] Batch {batch_num}/{total_batch_count}: calling API for cases {batch_case_ids}...", flush=True)
        response = provider.generate(
            system_prompt=CHECKER_SYSTEM_PROMPT,
            user_prompt=build_checker_user_prompt(batch),
        )
        raw_record = {
            "run_id": run_id,
            "batch_scenario_ids": batch_case_ids,
            "response": response.raw_response,
        }

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
                if str(result.get("case_id", "")) in expected_case_ids
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

        payload = validate_checker_payload(normalized_payload, expected_case_map=expected_case_map)
        batch_reviews = []
        for result in payload["results"]:
            result["run_id"] = run_id
            batch_reviews.append(result)
        return {"batch_num": batch_num, "raw_record": raw_record, "reviews": batch_reviews}

    def _write_batch_result(batch_num: int, result: dict) -> None:
        nonlocal batches_processed
        append_jsonl(raw_path, [result["raw_record"]])
        for review in result["reviews"]:
            reviews.append(review)
            append_jsonl(reviews_path, [review])
        print(f"[checker] Batch {batch_num}/{total_batch_count} done: processed {len(result['reviews'])} reviews", flush=True)
        batches_processed += 1

    try:
        if effective_concurrency == 1:
            for batch_num, batch in enumerate(batches, start=1):
                _write_batch_result(batch_num, _run_batch(batch_num, batch))
        else:
            batch_results: dict[int, dict] = {}
            batch_errors: dict[int, Exception] = {}
            with ThreadPoolExecutor(max_workers=effective_concurrency) as executor:
                futures = {
                    executor.submit(_run_batch, batch_num, batch): batch_num
                    for batch_num, batch in enumerate(batches, start=1)
                }
                for future in as_completed(futures):
                    batch_num = futures[future]
                    try:
                        batch_results[batch_num] = future.result()
                    except Exception as exc:
                        batch_errors[batch_num] = exc
            for batch_num in sorted(batch_results):
                _write_batch_result(batch_num, batch_results[batch_num])
            if batch_errors:
                failed_batch_nums = sorted(batch_errors)
                first_failed = failed_batch_nums[0]
                raise batch_errors[first_failed]
    except Exception as e:
        failed_batch_num = failed_batch_nums[0] if failed_batch_nums else batches_processed + 1
        remaining_after_failure = (
            sum(len(batches[num - 1]) for num in failed_batch_nums)
            if failed_batch_nums
            else sum(len(b) for b in batches[failed_batch_num - 1:])
        )
        print(f"[checker] Exception during batch processing: {e}", flush=True)
        print(f"[checker] Batches processed: {batches_processed}/{total_batch_count}; remaining cases: {remaining_after_failure}", flush=True)

    all_reviews = list(inherited_reviews.values()) + reviews

    # Always write reviews file (even if empty) so downstream consumers can read it.
    write_jsonl(reviews_path, all_reviews)

    coverage = _calculate_coverage(semantic_rules, all_reviews)
    write_json(coverage_path, coverage)

    summary = {
        "run_id": run_id,
        "role": "checker",
        "pipeline_version": PIPELINE_VERSION,
        "prompt_version": CHECKER_PROMPT_VERSION,
        "provider": provider_cfg.name,
        "model": provider_cfg.model,
        "input_rules": str(semantic_rules_path),
        "source_rules_hash": _artifact_hash(semantic_rules_path),
        "input_cases": str(maker_cases_path),
        "output_dir": str(run_dir),
        "review_count": len(all_reviews),
        "new_review_count": len(reviews),
        "inherited_review_count": len(inherited_reviews),
        "remaining_after_resume": remaining_after_failure if failed_batch_num else 0,
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
    human_scripts_edits_path: Path | None = None,
    deterministic_fallback_only: bool = False,
    bdd_generation_mode: str = "llm-with-fallback",
    concurrency: int = 1,
) -> dict:
    """Generate normalized BDD artifacts from maker test cases.

    The BDD pipeline normalizes maker scenarios into a governed intermediate
    BDD representation (not Gherkin text). Gherkin rendering and step-definition
    generation are downstream renderers that consume this normalized output.
    """
    maker_records = load_jsonl(maker_cases_path)
    if limit is not None:
        maker_records = maker_records[:limit]

    completed_ids: set[str] = set()
    if resume_from and resume_from.exists():
        for record in load_jsonl(resume_from):
            semantic_rule_id = record.get("semantic_rule_id")
            if semantic_rule_id:
                completed_ids.add(semantic_rule_id)
        maker_records = [
            record
            for record in maker_records
            if record.get("semantic_rule_id") not in completed_ids
        ]

    if deterministic_fallback_only:
        bdd_generation_mode = "deterministic"
    if bdd_generation_mode not in BDD_GENERATION_MODES:
        raise ValueError(
            "bdd_generation_mode must be one of: "
            + ", ".join(sorted(BDD_GENERATION_MODES))
        )

    provider_role, provider_cfg = _bdd_provider_config(config)
    provider = None if bdd_generation_mode == "deterministic" else build_provider(provider_cfg)
    run_id = timestamp_slug()
    run_dir = ensure_dir(output_dir / run_id)
    results_path = run_dir / "normalized_bdd.jsonl"
    raw_path = run_dir / "bdd_raw_responses.jsonl"
    summary_path = run_dir / "summary.json"
    fallback_path = run_dir / "bdd_fallbacks.json"

    total_batches = 0
    fallback_records: list[dict] = []

    batches = list(_chunked(maker_records, batch_size))
    total_batch_count = len(batches)
    if concurrency <= 0:
        raise ValueError("concurrency must be greater than zero.")
    effective_concurrency = min(concurrency, total_batch_count or 1)
    print(
        f"[bdd] Starting: {len(maker_records)} maker records in {total_batch_count} batches "
        f"(batch_size={batch_size}, concurrency={effective_concurrency}, mode={bdd_generation_mode}, "
        f"provider_role={provider_role}, model={provider_cfg.model})",
        flush=True,
    )

    def _run_bdd_batch(batch_num: int, batch: list[dict]) -> dict:
        batch_rule_ids = [item["semantic_rule_id"] for item in batch]
        payload = None
        last_error = ""
        raw_records: list[dict] = []
        fallback_record: dict | None = None
        if bdd_generation_mode == "deterministic":
            fallback_results = _maker_records_to_normalized_bdd(batch)
            payload = validate_normalized_bdd_payload(
                {"results": fallback_results},
                expected_rule_ids=batch_rule_ids,
            )
            fallback_record = {
                "batch_num": batch_num,
                "batch_semantic_rule_ids": batch_rule_ids,
                "reason": "deterministic",
            }
            print(
                f"[bdd] Batch {batch_num}/{total_batch_count}: using deterministic fallback from maker cases.",
                flush=True,
            )
        else:
            assert provider is not None
            print(f"[bdd] Batch {batch_num}/{total_batch_count}: calling API for rules {batch_rule_ids}...", flush=True)
            for attempt in range(1, 3):
                response = provider.generate(
                    system_prompt=BDD_SYSTEM_PROMPT,
                    user_prompt=build_bdd_user_prompt(batch),
                )
                raw_records.append(
                    {
                        "run_id": run_id,
                        "batch_semantic_rule_ids": batch_rule_ids,
                        "attempt": attempt,
                        "response": response.raw_response,
                    }
                )
                try:
                    payload = validate_normalized_bdd_payload(
                        parse_json_object(response.content),
                        expected_rule_ids=batch_rule_ids,
                    )
                    break
                except SchemaError as exc:
                    last_error = _bdd_failure_reason(exc, response.raw_response)
                    if attempt == 1:
                        if last_error.startswith("truncated_output:"):
                            print(f"[bdd] Batch {batch_num}: model output was truncated, retrying once...", flush=True)
                        else:
                            print(f"[bdd] Batch {batch_num}: invalid JSON/schema output, retrying once...", flush=True)
                        continue
                    if bdd_generation_mode == "llm":
                        raise SchemaError(f"BDD batch {batch_num} failed: {last_error}") from exc
                    fallback_results = _maker_records_to_normalized_bdd(batch)
                    payload = validate_normalized_bdd_payload(
                        {"results": fallback_results},
                        expected_rule_ids=batch_rule_ids,
                    )
                    fallback_record = {
                        "batch_num": batch_num,
                        "batch_semantic_rule_ids": batch_rule_ids,
                        "reason": last_error,
                    }
                    print(
                        f"[bdd] Batch {batch_num}/{total_batch_count}: using deterministic fallback from maker cases after invalid model output.",
                        flush=True,
                    )
        if payload is None:
            raise SchemaError(f"BDD batch {batch_num} did not produce a payload.")
        records: list[dict] = []
        for item in payload["results"]:
            item["run_id"] = run_id
            # Carry planner/maker traceability from source records
            source_record = next(
                (r for r in batch if r.get("semantic_rule_id") == item.get("semantic_rule_id")), {}
            )
            if "paragraph_ids" not in item or not item["paragraph_ids"]:
                item["paragraph_ids"] = source_record.get("paragraph_ids", [])
            # Propagate paragraph_ids into each scenario
            for scenario in item.get("scenarios", []):
                if "paragraph_ids" not in scenario or not scenario.get("paragraph_ids"):
                    scenario["paragraph_ids"] = item.get("paragraph_ids", [])
                if "semantic_rule_ref" not in scenario:
                    scenario["semantic_rule_ref"] = item.get("semantic_rule_id")
            # Set metadata
            item.setdefault("metadata", {})
            item["metadata"]["maker_run_id"] = source_record.get("run_id", "")
            item["metadata"]["paragraph_ids"] = item.get("paragraph_ids", [])
            records.append(item)
        return {
            "batch_num": batch_num,
            "raw_records": raw_records,
            "records": records,
            "fallback_record": fallback_record,
        }

    def _write_bdd_batch(batch_num: int, result: dict) -> None:
        nonlocal total_batches
        if result["raw_records"]:
            append_jsonl(raw_path, result["raw_records"])
        append_jsonl(results_path, result["records"])
        if result.get("fallback_record"):
            fallback_records.append(result["fallback_record"])
        total_batches += 1
        print(
            f"[bdd] Batch {batch_num}/{total_batch_count} done: normalized {len(result['records'])} rules",
            flush=True,
        )

    if effective_concurrency == 1:
        for batch_num, batch in enumerate(batches, start=1):
            _write_bdd_batch(batch_num, _run_bdd_batch(batch_num, batch))
    else:
        batch_results: dict[int, dict] = {}
        first_error: Exception | None = None
        with ThreadPoolExecutor(max_workers=effective_concurrency) as executor:
            futures = {
                executor.submit(_run_bdd_batch, batch_num, batch): batch_num
                for batch_num, batch in enumerate(batches, start=1)
            }
            for future in as_completed(futures):
                batch_num = futures[future]
                try:
                    batch_results[batch_num] = future.result()
                except Exception as exc:
                    if first_error is None:
                        first_error = exc
        for batch_num in sorted(batch_results):
            _write_bdd_batch(batch_num, batch_results[batch_num])
        if first_error is not None:
            raise first_error

    # Render Gherkin feature files and step definitions from normalized BDD
    processed_rule_count = 0
    feature_files: list[Path] = []
    step_files: list[Path] = []
    if results_path.exists():
        bdd_results = load_jsonl(results_path)
        processed_rule_count = len(bdd_results)
        if bdd_results:
            # Apply human edits before Gherkin rendering so scenario step text is updated
            if human_scripts_edits_path:
                bdd_results = apply_human_step_edits(bdd_results, human_scripts_edits_path)
            feature_files = render_gherkin_from_normalized_bdd(bdd_results, run_dir)
            step_files = render_steps_from_normalized_bdd(
                bdd_results, run_dir, human_scripts_edits_path=human_scripts_edits_path
            )
            print(
                f"[bdd] Rendered {len(feature_files)} feature files and {len(step_files)} step definition files.",
                flush=True,
            )

    summary = {
        "run_id": run_id,
        "role": "bdd",
        "pipeline_version": PIPELINE_VERSION,
        "prompt_version": BDD_PROMPT_VERSION,
        "provider": provider_cfg.name,
        "model": provider_cfg.model,
        "input_cases": str(maker_cases_path),
        "output_dir": str(run_dir),
        "processed_rule_count": processed_rule_count,
        "batch_count": total_batches,
        "concurrency": effective_concurrency,
        "fallback_batch_count": len(fallback_records),
        "fallback_reasons_path": str(fallback_path) if fallback_records else None,
        "bdd_generation_mode": bdd_generation_mode,
        "bdd_provider_role": provider_role,
        "deterministic_fallback_only": bdd_generation_mode == "deterministic",
        "results_path": str(results_path),
        "raw_path": str(raw_path),
        "feature_files_count": len(feature_files),
        "feature_files": [str(f) for f in feature_files],
        "step_definitions_files": [str(f) for f in step_files],
        "step_definitions_count": len(step_files),
    }
    if fallback_records:
        write_json(fallback_path, fallback_records)
    write_json(summary_path, summary)
    return summary


def _case_map_from_maker_records(maker_records: list[dict]) -> dict[str, str]:
    """Build a case_id -> semantic_rule_id mapping from maker records."""
    return {
        scenario["scenario_id"]: record["semantic_rule_id"]
        for record in maker_records
        for scenario in record.get("scenarios", [])
    }


def _load_human_reviews(path: Path) -> list[dict]:
    """Load human reviews from either JSON (object with reviews list) or JSONL format."""
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    first_char = text[0]
    if first_char == "{":
        # JSON object format: {"reviews": [...]}
        data = load_json(path)
        if isinstance(data, dict) and "reviews" in data:
            return data["reviews"]
        return []
    elif first_char == "[":
        # JSONL format: one JSON object per line
        return load_jsonl(path)
    return []


def _maker_records_to_normalized_bdd(maker_records: list[dict]) -> list[dict]:
    """Convert maker_records (list of {semantic_rule_id, feature, scenarios}) to
    normalized BDD format.

    This allows apply_human_step_edits and render_steps_from_normalized_bdd to
    be used with the output of the rewrite pipeline.
    """
    results: list[dict] = []
    for record in maker_records:
        semantic_rule_id = record.get("semantic_rule_id", "unknown")
        feature_title = record.get("feature", "Unnamed Feature")
        scenarios = record.get("scenarios", [])

        # Build step_definitions by flattening all scenarios' steps
        step_definitions: dict[str, list[dict]] = {"given": [], "when": [], "then": []}
        seen: dict[str, set[str]] = {"given": set(), "when": set(), "then": set()}
        normalized_scenarios: list[dict] = []

        for scenario in scenarios:
            normalized_scenario = {
                "scenario_id": str(scenario.get("scenario_id", "unknown")),
                "title": str(scenario.get("title") or scenario.get("name") or "Unnamed scenario"),
                "case_type": scenario.get("case_type", "positive"),
                "priority": scenario.get("priority", "medium"),
                "given_steps": [],
                "when_steps": [],
                "then_steps": [],
                "assumptions": scenario.get("assumptions", []),
                "semantic_rule_ref": semantic_rule_id,
            }
            for step_type in ("given", "when", "then"):
                steps = scenario.get(step_type, [])
                for step_text in steps:
                    if isinstance(step_text, dict):
                        step_str = str(step_text.get("step_text") or step_text.get("text") or "")
                        step_pattern = str(step_text.get("step_pattern") or step_str)
                    else:
                        step_str = step_text if isinstance(step_text, str) else ""
                        step_pattern = step_str
                    if not step_str:
                        continue
                    normalized_scenario[f"{step_type}_steps"].append({
                        "step_text": step_str,
                        "step_pattern": step_pattern,
                    })
                    # Deduplicate by step_text within each type
                    if step_str not in seen[step_type]:
                        seen[step_type].add(step_str)
                        step_definitions[step_type].append({
                            "step_text": step_str,
                            "step_pattern": step_pattern,
                            "code": "",
                        })
            normalized_scenarios.append(normalized_scenario)

        results.append({
            "semantic_rule_id": semantic_rule_id,
            "feature_title": feature_title,
            "feature_description": record.get("intent", ""),
            "paragraph_ids": record.get("paragraph_ids", []),
            "scenarios": normalized_scenarios,
            "step_definitions": step_definitions,
        })
    return results


def _rewrite_targets(human_payload: dict) -> dict[str, list[str]]:
    targets: dict[str, list[str]] = defaultdict(list)
    for review in human_payload.get("reviews", []):
        decision = normalize_human_review_decision(
            review.get("review_decision", "") or review.get("decision", "")
        )
        if decision != "rewrite":
            continue
        semantic_rule_id = str(review.get("semantic_rule_id", ""))
        case_id = str(review.get("case_id", ""))
        if semantic_rule_id and case_id:
            targets[semantic_rule_id].append(case_id)
    return dict(targets)


def _merge_cases_in_records(
    original_records: list[dict],
    rewritten_scenarios_by_rule: dict[str, dict[str, dict]],
    rewritten_features_by_rule: dict[str, str] | None = None,
) -> list[dict]:
    rewritten_features_by_rule = rewritten_features_by_rule or {}
    merged_records: list[dict] = []
    for record in original_records:
        semantic_rule_id = record.get("semantic_rule_id", "")
        rewritten_for_rule = rewritten_scenarios_by_rule.get(semantic_rule_id, {})
        merged_record = dict(record)
        if semantic_rule_id in rewritten_features_by_rule:
            merged_record["feature"] = rewritten_features_by_rule[semantic_rule_id]
        merged_scenarios = []
        for scenario in record.get("scenarios", []):
            case_id = scenario.get("scenario_id", "")
            merged_scenarios.append(rewritten_for_rule.get(case_id, scenario))
        merged_record["scenarios"] = merged_scenarios
        merged_records.append(merged_record)
    return merged_records


def run_rewrite_pipeline(
    config: ProjectConfig,
    semantic_rules_path: Path,
    maker_cases_path: Path,
    checker_reviews_path: Path,
    human_reviews_path: Path,
    output_dir: Path,
    limit: int | None,
    batch_size: int,
    concurrency: int = 1,
    human_scripts_edits_path: Path | None = None,
) -> dict:
    """Rewrite only cases marked ``review_decision = rewrite``."""
    semantic_rules = load_json(semantic_rules_path)
    if not isinstance(semantic_rules, list):
        raise ValueError("semantic_rules_path must contain a JSON list.")
    rules_by_id = {rule["semantic_rule_id"]: rule for rule in semantic_rules if "semantic_rule_id" in rule}
    maker_records = load_jsonl(maker_cases_path)
    checker_reviews = load_jsonl(checker_reviews_path)

    if limit is not None:
        maker_records = maker_records[:limit]

    case_map = _case_map_from_maker_records(maker_records)
    human_payload = validate_human_review_payload(load_json(human_reviews_path), expected_case_map=case_map)
    targets_by_rule = _rewrite_targets(human_payload)
    target_case_ids = {case_id for case_ids in targets_by_rule.values() for case_id in case_ids}

    provider_cfg = config.provider_for_role("maker")
    provider = build_provider(provider_cfg)
    run_id = timestamp_slug()
    run_dir = ensure_dir(output_dir / run_id)
    rewritten_cases_path = run_dir / "rewritten_cases.jsonl"
    merged_path = run_dir / "merged_cases.jsonl"
    raw_path = run_dir / "rewrite_raw_responses.jsonl"
    summary_path = run_dir / "summary.json"

    maker_records_by_rule = {record.get("semantic_rule_id", ""): record for record in maker_records}
    checker_reviews_by_rule: dict[str, list[dict]] = defaultdict(list)
    for review in checker_reviews:
        semantic_rule_id = str(review.get("semantic_rule_id") or case_map.get(str(review.get("case_id", "")), ""))
        checker_reviews_by_rule[semantic_rule_id].append(review)
    human_reviews_by_rule: dict[str, list[dict]] = defaultdict(list)
    for review in human_payload.get("reviews", []):
        human_reviews_by_rule[str(review.get("semantic_rule_id", ""))].append(review)

    rewrite_items: list[dict] = []
    for semantic_rule_id, case_ids in targets_by_rule.items():
        rule = rules_by_id.get(semantic_rule_id)
        maker_record = maker_records_by_rule.get(semantic_rule_id)
        if not rule or not maker_record:
            continue
        case_id_set = set(case_ids)
        rewrite_items.append(
            {
                "semantic_rule": _augment_rule_with_case_requirements(rule),
                "current_maker_record": maker_record,
                "target_case_ids": case_ids,
                "checker_reviews": [
                    review
                    for review in checker_reviews_by_rule.get(semantic_rule_id, [])
                    if str(review.get("case_id", "")) in case_id_set
                ],
                "human_reviews": [
                    review
                    for review in human_reviews_by_rule.get(semantic_rule_id, [])
                    if str(review.get("case_id", "")) in case_id_set
                ],
            }
        )

    if concurrency <= 0:
        raise ValueError("concurrency must be greater than zero.")

    rewritten_scenarios_by_rule: dict[str, dict[str, dict]] = defaultdict(dict)
    rewritten_features_by_rule: dict[str, str] = {}
    rewritten_records: list[dict] = []
    all_rewritten_case_ids: list[str] = []
    batches = list(_chunked(rewrite_items, batch_size))
    total_batch_count = len(batches)
    effective_concurrency = min(concurrency, total_batch_count or 1)

    def _run_batch(batch_num: int, batch: list[dict]) -> dict:
        batch_rule_ids = [item["semantic_rule"]["semantic_rule_id"] for item in batch]
        print(f"[rewrite] Batch {batch_num}/{total_batch_count}: calling API for rules {batch_rule_ids}...", flush=True)
        response = provider.generate(
            system_prompt=REWRITE_SYSTEM_PROMPT,
            user_prompt=build_rewrite_user_prompt(batch),
        )
        raw_record = {
            "run_id": run_id,
            "batch_semantic_rule_ids": batch_rule_ids,
            "target_case_ids": [case_id for item in batch for case_id in item.get("target_case_ids", [])],
            "response": response.raw_response,
        }
        payload = validate_maker_payload(
            parse_json_object(response.content),
            expected_rule_ids=batch_rule_ids,
        )
        source_by_id = {item["semantic_rule"]["semantic_rule_id"]: item for item in batch}
        records: list[dict] = []
        for item in payload["results"]:
            semantic_rule_id = item["semantic_rule_id"]
            rewrite_item = source_by_id[semantic_rule_id]
            target_ids = list(rewrite_item.get("target_case_ids", []))
            target_id_set = set(target_ids)
            scenarios = item.get("scenarios", [])
            if len(scenarios) == len(target_ids):
                for index, scenario in enumerate(scenarios):
                    if str(scenario.get("scenario_id", "")) not in target_id_set:
                        scenario["scenario_id"] = target_ids[index]
            item["scenarios"] = [
                scenario
                for scenario in scenarios
                if str(scenario.get("scenario_id", "")) in target_id_set
            ]
            records.append(
                _maker_record_from_result(
                    item,
                    run_id=run_id,
                    source_rule=rewrite_item.get("semantic_rule"),
                )
            )
        return {"batch_num": batch_num, "raw_record": raw_record, "records": records}

    def _write_batch_result(batch_num: int, result: dict) -> None:
        append_jsonl(raw_path, [result["raw_record"]])
        for record in result["records"]:
            semantic_rule_id = record.get("semantic_rule_id", "")
            if record.get("feature"):
                rewritten_features_by_rule[semantic_rule_id] = record["feature"]
            for scenario in record.get("scenarios", []):
                case_id = str(scenario.get("scenario_id", ""))
                if not case_id:
                    continue
                rewritten_scenarios_by_rule[semantic_rule_id][case_id] = scenario
                all_rewritten_case_ids.append(case_id)
            rewritten_records.append(record)
        print(f"[rewrite] Batch {batch_num}/{total_batch_count} done: rewritten {sum(len(r.get('scenarios', [])) for r in result['records'])} cases", flush=True)

    if batches:
        if effective_concurrency == 1:
            for batch_num, batch in enumerate(batches, start=1):
                _write_batch_result(batch_num, _run_batch(batch_num, batch))
        else:
            batch_results: dict[int, dict] = {}
            first_error: Exception | None = None
            with ThreadPoolExecutor(max_workers=effective_concurrency) as executor:
                futures = {
                    executor.submit(_run_batch, batch_num, batch): batch_num
                    for batch_num, batch in enumerate(batches, start=1)
                }
                for future in as_completed(futures):
                    batch_num = futures[future]
                    try:
                        batch_results[batch_num] = future.result()
                    except Exception as exc:
                        if first_error is None:
                            first_error = exc
            for batch_num in sorted(batch_results):
                _write_batch_result(batch_num, batch_results[batch_num])
            if first_error is not None:
                raise first_error

    merged_records = _merge_cases_in_records(
        maker_records,
        rewritten_scenarios_by_rule,
        rewritten_features_by_rule=rewritten_features_by_rule,
    )
    write_jsonl(rewritten_cases_path, rewritten_records)
    write_jsonl(merged_path, merged_records)

    # If human scripts edits are provided, convert merged records to normalized BDD
    # and apply human step edits before rendering step definitions
    _edits_path = Path(human_scripts_edits_path) if human_scripts_edits_path else None
    if _edits_path and _edits_path.name not in ("", ".", "..") and _edits_path.exists():
        normalized_bdd = _maker_records_to_normalized_bdd(merged_records)
        normalized_bdd = apply_human_step_edits(normalized_bdd, _edits_path)
        ensure_dir(run_dir / "bdd")
        step_files = render_steps_from_normalized_bdd(normalized_bdd, run_dir / "bdd")
        logger.info("Rewritten step definitions with human edits. count=%s files=%s", len(step_files), step_files)

    summary = {
        "run_id": run_id,
        "role": "maker_rewrite",
        "pipeline_version": PIPELINE_VERSION,
        "prompt_version": REWRITE_PROMPT_VERSION,
        "provider": provider_cfg.name,
        "model": provider_cfg.model,
        "semantic_rules_path": str(semantic_rules_path),
        "maker_cases_path": str(maker_cases_path),
        "checker_reviews_path": str(checker_reviews_path),
        "human_reviews_path": str(human_reviews_path),
        "output_dir": str(run_dir),
        "merged_cases_path": str(merged_path),
        "rewritten_cases_path": str(rewritten_cases_path),
        "raw_path": str(raw_path),
        "target_rule_count": len(targets_by_rule),
        "target_case_count": len(target_case_ids),
        "rewritten_rule_count": len(rewritten_scenarios_by_rule),
        "rewritten_scenario_count": len(all_rewritten_case_ids),
        "rewritten_case_ids": all_rewritten_case_ids,
        "processed_rule_count": len(merged_records),
        "merged_rule_count": len(merged_records),
        "scenario_count": sum(len(record.get("scenarios", [])) for record in merged_records),
        "merged_case_count": sum(len(record.get("scenarios", [])) for record in merged_records),
        "rewrite_count": len(all_rewritten_case_ids),
        "kept_count": sum(
            1
            for record in merged_records
            for scenario in record.get("scenarios", [])
            if scenario.get("scenario_id") not in set(all_rewritten_case_ids)
        ),
    }
    write_json(summary_path, summary)
    return summary

