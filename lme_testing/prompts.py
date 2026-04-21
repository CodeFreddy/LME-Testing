from __future__ import annotations

import json


# ---------------------------------------------------------------------------
# Prompt and pipeline versioning
# ---------------------------------------------------------------------------
# Increment MAKER_PROMPT_VERSION when MAKER_SYSTEM_PROMPT or
# build_maker_user_prompt changes in a way that affects output quality.
MAKER_PROMPT_VERSION = "1.3"

# Increment CHECKER_PROMPT_VERSION when CHECKER_SYSTEM_PROMPT or
# build_checker_user_prompt changes in a way that affects output quality.
CHECKER_PROMPT_VERSION = "1.1"

# Increment BDD_PROMPT_VERSION when BDD_SYSTEM_PROMPT or
# build_bdd_user_prompt changes in a way that affects output quality.
BDD_PROMPT_VERSION = "3.0"

# Increment PLANNER_PROMPT_VERSION when PLANNER_SYSTEM_PROMPT or
# build_planner_user_prompt changes in a way that affects output quality.
PLANNER_PROMPT_VERSION = "1.0"

# Pipeline version tracks the overall pipelines.py schema.
# Increment when summary fields or coverage logic change in a breaking way.
PIPELINE_VERSION = "2.0"


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
Case-type specific guidance:
- PROHIBITION positive case: describe the actor attempting the prohibited action from the rule's evidence. The positive case for a prohibition tests whether the prohibition is enforced — the GIVEN/WHEN steps describe the specific forbidden behavior, and the THEN clause expects rejection/reversal. This directly validates that the rule blocks the forbidden action. Do NOT describe a permitted action as the positive case — testing what is allowed is an indirect test of the prohibition and will be rated as coverage_relevance=indirect.
- PROHIBITION negative case: describe the actor performing a valid alternative action that is not prohibited. The negative case confirms that the prohibition does not block lawful behavior.
- WORKFLOW exception case: derive the exception scenario directly from the evidence — if the rule text explicitly mentions an exceptional circumstance (e.g., "in circumstances other than X", "except when Y"), test that specific exception. Do NOT infer an exception scenario that is not mentioned in the evidence — the checker will rate evidence_consistency=1 and mark it not_relevant.
- DEADLINE boundary case: the boundary must be derived from a specific value in the evidence (an exact time, a specific business_day_offset, a named deadline_kind). If the evidence does not define a specific boundary value, do not invent one. Instead, set the case_type to "exception" and test the exceptional-circumstances scenario. The boundary THEN step must assert the deadline validation result (accepted/rejected) — do not assert a specific time in the then clause.
- BOUNDARY case: must test the edge condition explicitly. Use specific values from the evidence when available. If no explicit edge value exists in the evidence, do not generate a boundary case — flag this in the scenario's assumptions and use case_type "exception" instead.
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
- If maker evidence is weak, say so explicitly in findings.
- Return structured JSON only.
"""


PLANNER_SYSTEM_PROMPT = """You are the planner model for an LME test design workflow.
You transform semantic rules into structured test planning artifacts.
Hard requirements:
- Return exactly one result per input semantic_rule_id.
- Do not omit any input semantic_rule_id.
- Do not return extra semantic_rule_id values that were not in the batch.
- Keep every semantic_rule_id exactly unchanged.
- test_objective must be concise and specific to what this test plan validates.
- risk_level must be one of: high, medium, low. Infer from rule complexity, financial impact, and ambiguity.
- scenario_family must be a short categorical name grouping related scenarios (e.g., price_validation, session_management, order_routing).
- coverage_intent describes what the scenario set should collectively cover.
- priority follows: high (blocking/obligation/deadline), medium (prohibition/state_transition), low (permission/reference_only).
- dependency_notes capture prerequisites, cross-rule dependencies, or setup requirements.
- recommended_validation_strategy suggests validation approach: smoke, regression, boundary, or exception.
- Return JSON only.
"""


def build_planner_user_prompt(batch: list[dict]) -> str:
    """Build user prompt for planner stage from semantic rules."""
    schema = {
        "results": [
            {
                "semantic_rule_id": "SR-MR-000-00",
                "test_objective": "Validate that [specific behavior]",
                "risk_level": "high",
                "coverage_intent": "Cover positive, negative, and boundary cases for [rule subject]",
                "scenario_family": "price_validation",
                "dependency_notes": [],
                "recommended_validation_strategy": "regression",
                "priority": "high",
                "paragraph_ids": ["MR-000-00"],
                "atomic_rule_ids": ["MR-000-00"],
                "rule_type": "obligation"
            }
        ]
    }
    return (
        "Generate a test planning artifact for each semantic rule.\n"
        "Return one result per semantic_rule_id.\n"
        "Each result must include: semantic_rule_id, test_objective, risk_level, scenario_family, priority.\n"
        "Optionally include: coverage_intent, dependency_notes, recommended_validation_strategy.\n"
        "risk_level: high = complex/high-impact, medium = moderate risk, low = straightforward/rare.\n"
        "priority: high = blocking rules (obligation/deadline), medium = prohibitions, low = permissions.\n"
        "scenario_family: short category name for grouping (e.g., price_validation, session_management).\n"
        "Return JSON matching this schema shape:\n"
        f"{json.dumps(schema, ensure_ascii=False, indent=2)}\n"
        "Input semantic rules:\n"
        f"{json.dumps(batch, ensure_ascii=False, indent=2)}"
    )


BDD_SYSTEM_PROMPT = """You are the BDD normalization model for an LME test design workflow.
You transform structured test cases into a normalized BDD representation that is independent of final Gherkin syntax.
This normalized output is the governed intermediate artifact consumed by Gherkin renderers and step-definition mappers.
Hard requirements:
- Return exactly one result per input semantic_rule_id.
- Do not omit any input semantic_rule_id.
- Preserve all traceability links (semantic_rule_id, atomic_rule_ids, paragraph_ids).
- Keep Given/When/Then steps concise and declarative.
- step_text is the natural-language step (e.g., "a member with valid LME session").
- step_pattern is the regex-extracted pattern for step binding (copy step_text as-is for simple patterns).
- Use tags derived from case_type and priority (e.g., @positive, @high).
- Do not invent additional steps beyond what is in the input.
- step_definitions code should use Python with LME.Client, LME.API, LME.PostTrade patterns.
- Return structured JSON only.
"""


def build_bdd_user_prompt(batch: list[dict]) -> str:
    """Build user prompt for normalized BDD from maker test cases."""
    schema = {
        "results": [
            {
                "semantic_rule_id": "SR-MR-000-00",
                "feature_title": "LME Rulebook Terminology Compliance",
                "feature_description": "Validates that capitalized terms resolve to LME Rulebook definitions.",
                "paragraph_ids": ["MR-000-00"],
                "scenarios": [
                    {
                        "scenario_id": "TC-SR-MR-000-00-positive-01",
                        "title": "Capitalised terms resolve to LME Rulebook definitions",
                        "case_type": "positive",
                        "priority": "high",
                        "given_steps": [
                            {"step_text": "a registered_intermediating_broker submits a document containing capitalised terms", "step_pattern": "a registered_intermediating_broker submits a document containing capitalised terms"}
                        ],
                        "when_steps": [
                            {"step_text": "the system processes the document terminology", "step_pattern": "the system processes the document terminology"}
                        ],
                        "then_steps": [
                            {"step_text": "the terms are assigned the meaning ascribed in the LME Rulebook", "step_pattern": "the terms are assigned the meaning ascribed in the LME Rulebook"},
                            {"step_text": "the obligation is fulfilled", "step_pattern": "the obligation is fulfilled"}
                        ],
                        "assumptions": [],
                        "paragraph_ids": ["MR-000-00"],
                        "semantic_rule_ref": "SR-MR-000-00",
                        "required_case_types": ["positive"]
                    }
                ],
                "step_definitions": {
                    "given": [
                        {
                            "step_text": "a registered_intermediating_broker submits a document containing capitalised terms",
                            "step_pattern": "a registered_intermediating_broker submits a document containing capitalised terms",
                            "code": "@given(\"a registered_intermediating_broker submits a document containing capitalised terms\")\ndef step_broker_submits_document():\n    broker = LME.Client.registered_intermediary\n    document = LME.API.create_document(broker=broker, terms='capitalised')"
                        }
                    ],
                    "when": [
                        {
                            "step_text": "the system processes the document terminology",
                            "step_pattern": "the system processes the document terminology",
                            "code": "@when(\"the system processes the document terminology\")\ndef step_system_processes_terminology():\n    response = LME.API.process_terminology(document)"
                        }
                    ],
                    "then": [
                        {
                            "step_text": "the terms are assigned the meaning ascribed in the LME Rulebook",
                            "step_pattern": "the terms are assigned the meaning ascribed in the LME Rulebook",
                            "code": "@then(\"the terms are assigned the meaning ascribed in the LME Rulebook\")\ndef step_terms_assigned_rulebook():\n    assert response.meaning_source == 'LME_Rulebook'"
                        }
                    ]
                }
            }
        ]
    }
    return (
        "Transform the following maker test cases into a normalized BDD representation.\n"
        "The normalized BDD is a governed intermediate artifact, NOT final Gherkin text.\n"
        "Return JSON matching this schema shape:\n"
        f"{json.dumps(schema, ensure_ascii=False, indent=2)}\n"
        "Input maker test cases:\n"
        f"{json.dumps(batch, ensure_ascii=False, indent=2)}"
    )


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
    schema = {
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


def build_checker_user_prompt(batch: list[dict]) -> str:
    expected_case_ids = [item["scenario"]["scenario_id"] for item in batch]
    expected_case_rule_map = {
        item["scenario"]["scenario_id"]: item["semantic_rule_id"] for item in batch
    }
    schema = {
        "results": [{
            "case_id": "TC-SR-MR-000-00-01",
            "case_type_accepted": True,
            "coverage_relevance": "direct",
            "is_blocking": False,
            "scores": {"evidence_consistency": 5, "requirement_coverage": 4, "test_design_quality": 4},
            "findings": [],
            "coverage_assessment": {"status": "covered"}
        }]
    }
    return (
        "Review maker outputs against semantic rules.\n"
        "Return one result per case_id.\n"
        f"case_id -> rule: {json.dumps(expected_case_rule_map, ensure_ascii=False)}\n"
        "coverage_relevance: direct | indirect | not_relevant\n"
        "coverage_assessment.status: covered | partial | uncovered | not_applicable\n"
        "\n"
        "coverage_relevance guidelines:\n"
        "- direct: the scenario directly tests a required aspect of the rule's core requirement\n"
        "- indirect: the scenario tests a related but non-core aspect; use for supplementary coverage\n"
        "- not_relevant: the scenario does not test this rule at all\n"
        "\n"
        "IMPORTANT — rule-type-specific rules:\n"
        "- For rule_type=workflow, case_type=exception is DIRECT (exception handling is core to workflow completeness)\n"
        "- For rule_type=deadline, case_type=boundary is DIRECT (boundary testing validates deadline boundary conditions)\n"
        "- For rule_type=prohibition, case_type=positive is DIRECT (positive case tests that the prohibited action is indeed blocked)\n"
        "- For rule_type=enum_definition, case_type=negative is DIRECT (negative case tests invalid enum values are rejected)\n"
        "\n"
        "Schema:\n"
        f"{json.dumps(schema, ensure_ascii=False, indent=2)}\n"
        "Batch:\n"
        f"{json.dumps(batch, ensure_ascii=False, indent=2)}"
    )
