from __future__ import annotations

import json


def _maker_result_schema_example() -> dict:
    return {
        "results": [
            {
                "semantic_rule_id": "SR-MR-000-00",
                "requirement_ids": ["MR-000-00"],
                "feature": "Short feature title",
                "scenarios": [
                    {
                        "scenario_id": "TC-SR-MR-000-00-positive-01",
                        "title": "Short scenario title",
                        "intent": "Why this scenario exists",
                        "priority": "high",
                        "scenario_type": "positive",
                        "case_type": "positive",
                        "given": ["precondition"],
                        "when": ["action"],
                        "then": ["expected outcome"],
                        "assumptions": [],
                        "evidence": [
                            {
                                "atomic_rule_id": "MR-000-00",
                                "page": 1,
                                "quote": "short literal quote"
                            }
                        ]
                    },
                    {
                        "scenario_id": "TC-SR-MR-000-00-negative-01",
                        "title": "Negative scenario title",
                        "intent": "Why this negative scenario exists",
                        "priority": "high",
                        "scenario_type": "negative",
                        "case_type": "negative",
                        "given": ["precondition"],
                        "when": ["invalid or missing action"],
                        "then": ["expected rejection or failure"],
                        "assumptions": [],
                        "evidence": [
                            {
                                "atomic_rule_id": "MR-000-00",
                                "page": 1,
                                "quote": "short literal quote"
                            }
                        ]
                    }
                ]
            }
        ]
    }


MAKER_SYSTEM_PROMPT = """You are the maker model for an LME test design workflow.
You transform semantic rules into evidence-backed BDD test cases.
Hard requirements:
- For every input semantic rule, return exactly one result object.
- Do not omit any input semantic_rule_id.
- Do not return extra semantic_rule_id values that were not in the batch.
- Keep every semantic_rule_id exactly unchanged.
- requirement_ids must map to the source atomic_rule_ids for that rule.
- Every scenario must include evidence entries that map directly to requirement_ids.
- Every scenario must include a case_type from this controlled set only: positive, negative, boundary, exception, state_transition, data_validation.
- For each semantic rule, generate a complete scenario set that covers every required_case_type exactly once.
- Do not omit any required_case_type.
- Do not duplicate required_case_type scenarios for the same semantic rule.
- Unless a rule is explicitly reference_only with an empty required_case_types list, do not return extra optional case types.
- Evidence quotes must be short, literal, and individually mapped. Do not merge multiple quotes into one long quote.
- Use only supplied semantic rules and evidence.
- Do not invent exchange behavior that is not grounded in the evidence.
- If something is uncertain, keep the scenario conservative and put the uncertainty into assumptions.
- Return JSON only.
"""


REWRITE_SYSTEM_PROMPT = """You are the maker revision model for an LME test design workflow.
You revise maker-generated test cases using checker feedback and human review feedback.
Hard requirements:
- For every input semantic rule, return exactly one revised result object.
- Output ONLY the cases listed in target_case_ids; do NOT regenerate cases that are not targeted.
- Fix the issues raised by checker findings and human review comments when they are grounded in the supplied rule and evidence.
- When human feedback conflicts with checker findings, human takes precedence.
- Preserve fidelity to the semantic rule and evidence; do not invent business behavior.
- Return JSON only.
"""


CHECKER_SYSTEM_PROMPT = """You are the checker model for an LME test design workflow.
You review maker-generated test cases against source semantic rules.
Hard requirements:
- Cover every input case_id in the batch exactly once.
- Do not omit any input case_id.
- Do not invent or return extra case_id values that were not provided.
- Keep every returned case_id exactly unchanged.
- Keep semantic_rule_id exactly aligned with the provided case_id mapping.
- Evaluate whether the maker-declared case_type is appropriate for the rule and the scenario.
- Judge evidence consistency, requirement coverage, test design quality, and hallucination risk.
- Use blocking only for objective, high-severity issues such as rule mismatch, missing required case type, invalid case type mapping, wrong or missing evidence, non-executable scenario, duplicate slot usage, or traceability/schema break.
- Treat blocking as a recommendation, not as a final human decision.
- If maker evidence is weak, say so explicitly in findings.
- Return structured JSON only.
- You do not receive human review feedback and must evaluate each case independently, based solely on the semantic rule, case content, and evidence.
"""


# 构建首轮 maker 提示词，强制模型按 required_case_types 生成完整场景组。
def build_maker_user_prompt(batch: list[dict]) -> str:
    expected_ids = [item["semantic_rule_id"] for item in batch]
    expected_requirement_map = {
        item["semantic_rule_id"]: item.get("source", {}).get("atomic_rule_ids", [])
        for item in batch
    }
    expected_case_type_map = {
        item["semantic_rule_id"]: item.get("required_case_types", [])
        for item in batch
    }
    schema = _maker_result_schema_example()
    return (
        "Generate BDD test cases for the following semantic rules.\n"
        "You must return exactly one result per semantic_rule_id.\n"
        f"Expected semantic_rule_id list: {json.dumps(expected_ids, ensure_ascii=False)}\n"
        f"Expected requirement_ids map: {json.dumps(expected_requirement_map, ensure_ascii=False)}\n"
        f"Expected required_case_types map: {json.dumps(expected_case_type_map, ensure_ascii=False)}\n"
        "For each semantic rule, generate exactly one scenario for each required_case_type.\n"
        "The set of scenario case_type values for a rule must exactly match its required_case_types list unless that list is empty.\n"
        "case_type must be one of: positive, negative, boundary, exception, state_transition, data_validation.\n"
        "Evidence rules: each quote must be short, literal, and directly tied to one atomic_rule_id.\n"
        "Return JSON matching this schema shape:\n"
        f"{json.dumps(schema, ensure_ascii=False, indent=2)}\n"
        "Input semantic rules:\n"
        f"{json.dumps(batch, ensure_ascii=False, indent=2)}"
    )


# 构建 case 级 rewrite 提示词，按结构化章节组织，每 rule 只重写 target_case_ids 指定的 case。
def build_rewrite_user_prompt(batch: list[dict]) -> str:
    schema = _maker_result_schema_example()
    parts: list[str] = [
        "Revise the maker outputs for the following semantic rules.",
        "For each rule, output a revised result whose scenarios array contains ONLY the target cases listed under target_case_ids.",
        "Do NOT output cases whose scenario_id is not in target_case_ids.",
        "Preserve scenario_id exactly; update given/when/then/evidence/assumptions/case_type as needed.",
        "If human feedback conflicts with checker, follow the human.",
        f"Return JSON matching this schema shape:\n{json.dumps(schema, ensure_ascii=False, indent=2)}",
        "",
    ]
    for item in batch:
        rule = item["semantic_rule"]
        rule_id = rule.get("semantic_rule_id", "")
        target_case_ids = item.get("rewrite_target_case_ids", [])
        current_maker_record = item.get("current_maker_record", {})
        checker_reviews = item.get("checker_reviews", [])
        human_reviews = item.get("human_reviews", [])
        parts.append(f"=== Rule: {rule_id} ===")
        parts.append(f"\n## Semantic rule\n{json.dumps(rule, ensure_ascii=False, indent=2)}")
        parts.append(f"\n## Cases you generated last iteration (full set for this rule)\n{json.dumps(current_maker_record, ensure_ascii=False, indent=2)}")
        parts.append(f"\n## Cases the human asked you to rewrite\ntarget_case_ids: {json.dumps(target_case_ids, ensure_ascii=False)}")
        parts.append(f"\n## Checker findings for target cases\n{json.dumps(checker_reviews, ensure_ascii=False, indent=2)}")
        parts.append(f"\n## Human reviewer feedback for target cases (authoritative; > checker)\n{json.dumps(human_reviews, ensure_ascii=False, indent=2)}")
        parts.append("")
    return "\n".join(parts)


# 构建 checker 提示词，要求逐 case 输出结构化审核结果和 blocking 建议。
def build_checker_user_prompt(batch: list[dict]) -> str:
    expected_case_ids = [item["scenario"]["scenario_id"] for item in batch]
    expected_case_rule_map = {
        item["scenario"]["scenario_id"]: item["semantic_rule_id"] for item in batch
    }
    schema = {
        "results": [
            {
                "case_id": "TC-SR-MR-000-00-01",
                "semantic_rule_id": "SR-MR-000-00",
                "case_type": "positive",
                "case_type_accepted": True,
                "coverage_relevance": "direct",
                "overall_status": "pass",
                "blocking_findings_count": 0,
                "is_blocking": False,
                "blocking_category": "none",
                "blocking_reason": "",
                "checker_confidence": 0.88,
                "scores": {
                    "evidence_consistency": 5,
                    "requirement_coverage": 4,
                    "test_design_quality": 4,
                    "non_hallucination": 5
                },
                "findings": [
                    {
                        "severity": "medium",
                        "category": "missing_constraint",
                        "summary": "Missing deadline detail",
                        "details": "Explain the issue",
                        "suggested_fix": "How maker should revise it"
                    }
                ],
                "coverage_assessment": {
                    "status": "covered",
                    "reason": "Scenario set covers the rule",
                    "missing_aspects": []
                }
            }
        ]
    }
    return (
        "Review the maker outputs against the supplied semantic rules.\n"
        "You must return exactly one review result per input case_id, with no omissions and no extras.\n"
        f"Expected case_id list: {json.dumps(expected_case_ids, ensure_ascii=False)}\n"
        f"Expected case_id -> semantic_rule_id map: {json.dumps(expected_case_rule_map, ensure_ascii=False)}\n"
        "For each result, preserve the incoming case_type and judge whether it is accepted.\n"
        "Use coverage_assessment.status only from this set: covered, partial, uncovered, not_applicable.\n"
        "Use blocking_category only from this set: none, rule_mismatch, missing_required_case_type, invalid_case_type_mapping, no_evidence_or_wrong_evidence, non_executable_scenario, duplicate_case_covering_same_slot, schema_or_traceability_break, unspecified_block.\n"
        "If is_blocking is false, set blocking_category to none and blocking_reason to an empty string.\n"
        "If is_blocking is true, you must provide a short blocking_reason and a checker_confidence between 0 and 1.\n"
        "If you think a case is poor, still return a result for that exact case_id instead of dropping it.\n"
        "Return JSON matching this schema shape:\n"
        f"{json.dumps(schema, ensure_ascii=False, indent=2)}\n"
        "Input review batch:\n"
        f"{json.dumps(batch, ensure_ascii=False, indent=2)}"
    )
