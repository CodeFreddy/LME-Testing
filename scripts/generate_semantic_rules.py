from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate first-pass semantic_rule records from atomic_rules.json."
    )
    parser.add_argument(
        "--input",
        default="artifacts/lme_rules_v2_2/atomic_rules.json",
        help="Path to atomic_rules.json.",
    )
    parser.add_argument(
        "--output",
        default="artifacts/lme_rules_v2_2/semantic_rules.json",
        help="Path to semantic_rules.json.",
    )
    parser.add_argument(
        "--metadata",
        default="",
        help="Optional path to extraction metadata.json. When provided, doc metadata is read from it.",
    )
    parser.add_argument("--doc-id", default="lme_matching_rules_v2_2", help="Document identifier.")
    parser.add_argument("--doc-title", default="LME Matching Rules", help="Document title.")
    parser.add_argument("--doc-version", default="2.2", help="Document version.")
    return parser.parse_args()


def normalize_text(text: str) -> str:
    text = text.replace("\\(", "(").replace("\\)", ")")
    text = text.replace('\\"', '"')
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_metadata(args: argparse.Namespace, output_path: Path) -> tuple[str, str, str, dict]:
    metadata_path = Path(args.metadata) if args.metadata else output_path.parent / "metadata.json"
    metadata: dict = {}
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    doc_id = metadata.get("doc_id", args.doc_id)
    doc_title = metadata.get("doc_title", args.doc_title)
    doc_version = metadata.get("doc_version", args.doc_version)
    return doc_id, doc_title, doc_version, metadata


def infer_actor(text: str, rule_type: str) -> tuple[str | None, str]:
    lowered = text.lower()
    if "executing member" in lowered:
        return "executing_member", "normalized"
    if "clearing member" in lowered:
        return "clearing_member", "normalized"
    if "rib" in lowered or "registered intermediating broker" in lowered:
        return "registered_intermediating_broker", "normalized"
    if re.match(r"^(the )?matching system\b", lowered):
        return "matching_system", "normalized"
    if re.match(r"^(the )?clearing house\b", lowered):
        return "clearing_house", "normalized"
    if re.match(r"^(the )?exchange\b", lowered):
        return "exchange", "normalized"
    if "members " in lowered or lowered.startswith("member ") or lowered.startswith("members "):
        return "member", "normalized"
    if rule_type == "enum_definition":
        return None, "explicit"
    return "unspecified_actor", "inferred"


def infer_action(text: str, rule_type: str) -> tuple[str | None, str]:
    lowered = text.lower()
    action_map = [
        ("retain", "retain_record"),
        ("submit", "submit_trade"),
        ("enter", "enter_trade_data"),
        ("register", "register_trade"),
        ("contact", "contact_exchange"),
        ("match", "match_trade"),
        ("reverse", "reverse_trade"),
        ("correct", "correct_trade"),
        ("cancel", "cancel_trade"),
        ("approve", "approve_trade"),
        ("reject", "reject_trade"),
        ("convert", "convert_contract"),
        ("include", "include_field"),
        ("use", "use_code"),
        ("generate", "generate_trade_half"),
        ("start", "start_workflow"),
        ("calculate", "calculate_value"),
        ("substitute", "substitute_value"),
    ]
    for token, action in action_map:
        if token in lowered:
            return action, "normalized"
    if rule_type == "enum_definition":
        return "define_enum_value", "normalized"
    if rule_type == "reference_only":
        return None, "explicit"
    return "unspecified_action", "inferred"


def infer_object(text: str, rule_type: str) -> tuple[str | None, str]:
    lowered = text.lower()
    object_map = [
        ("give-up clearer trade half", "give_up_clearer_trade_half"),
        ("give-up executor trade half", "give_up_executor_trade_half"),
        ("give-up trade", "give_up_trade"),
        ("trade half", "trade_half"),
        ("audit trail", "audit_trail"),
        ("trade time", "trade_time"),
        ("venue code", "venue_code"),
        ("price code", "short_price_code"),
        ("price type", "price_type"),
        ("trade category", "trade_category"),
        ("otc bring-on", "otc_bring_on_trade"),
        ("otc take off", "otc_take_off_trade"),
        ("client contract", "client_contract"),
        ("fpa", "fixed_price_auction"),
        ("trade", "trade"),
    ]
    for token, obj in object_map:
        if token in lowered:
            return obj, "normalized"
    if rule_type == "enum_definition":
        return "enum_value", "normalized"
    if rule_type == "reference_only":
        return None, "explicit"
    return "unspecified_object", "inferred"


def infer_rule_tags(rule: dict) -> list[str]:
    text = normalize_text(rule["raw_text"]).lower()
    tags: list[str] = []
    tag_checks = {
        "give_up": ["give-up", "give up", "una"],
        "venue": ["venue", "inter-office", "ring", "select"],
        "timing": ["deadline", "within", "prior to", "08:30", "10:00", "01:00"],
        "submission": ["submit", "submission", "enter", "register"],
        "audit_trail": ["audit trail"],
        "price": ["price", "pricing", "official", "closing", "short price"],
        "account": ["account", "gosa", "osa", "isa"],
        "trade_category": ["trade category", "category"],
        "reversal_correction": ["reversal", "correction", "cancel"],
        "otc_bring_on": ["otc bring-on", "otc bring on"],
        "otc_take_off": ["otc take off", "otc take-off"],
        "carry": ["carry", "leg"],
        "currency": ["usd", "dollars", "currency", "fx"],
        "rib": ["rib", "registered intermediating broker"],
        "fpa": ["fpa", "auction"],
        "compliance": ["rulebook", "mifid", "reportable", "abusive"],
        "matching": ["matching system", "matched", "matching"],
    }
    for tag, patterns in tag_checks.items():
        if any(pattern in text for pattern in patterns):
            tags.append(tag)
    if not tags:
        tags.append("matching")
    return tags


def infer_priority(rule_type: str, tags: list[str]) -> str:
    if rule_type in {"deadline", "prohibition", "state_transition", "workflow", "calculation", "data_constraint"}:
        return "high"
    if "give_up" in tags or "matching" in tags:
        return "high"
    if rule_type == "reference_only":
        return "low"
    return "medium"


def build_conditions(text: str) -> list[dict]:
    conditions: list[dict] = []
    lowered = text.lower()
    if lowered.startswith("where "):
        conditions.append({
            "id": "C1",
            "kind": "document_context",
            "field": "context_clause",
            "operator": "equals",
            "value": text.split(",", 1)[0],
            "source_type": "explicit",
        })
    if lowered.startswith("when "):
        conditions.append({
            "id": f"C{len(conditions) + 1}",
            "kind": "event",
            "field": "trigger_event",
            "operator": "occurred",
            "value": text.split(",", 1)[0][5:],
            "source_type": "explicit",
        })
    if lowered.startswith("if "):
        conditions.append({
            "id": f"C{len(conditions) + 1}",
            "kind": "document_context",
            "field": "if_condition",
            "operator": "equals",
            "value": text.split(",", 1)[0][3:],
            "source_type": "explicit",
        })
    return conditions


def build_constraints(text: str) -> list[dict]:
    constraints: list[dict] = []
    lowered = text.lower()
    if "must include" in lowered:
        constraints.append({
            "id": f"K{len(constraints) + 1}",
            "field": "required_content",
            "operator": "equals",
            "value": normalize_text(text.split("must include", 1)[1]),
            "source_type": "explicit",
        })
    if "must be entered as" in lowered:
        constraints.append({
            "id": f"K{len(constraints) + 1}",
            "field": "format",
            "operator": "matches_format",
            "value": normalize_text(text.split("must be entered as", 1)[1]),
            "source_type": "explicit",
        })
    if "may only" in lowered:
        constraints.append({
            "id": f"K{len(constraints) + 1}",
            "field": "allowed_usage",
            "operator": "equals",
            "value": normalize_text(text),
            "source_type": "explicit",
        })
    return constraints


def build_outcome(rule_type: str) -> dict:
    mapping = {
        "obligation": ("acceptance", "action_required"),
        "prohibition": ("rejection", "action_not_permitted"),
        "permission": ("acceptance", "action_allowed"),
        "deadline": ("timeliness_requirement", "deadline_must_be_met"),
        "state_transition": ("state_change", "state_transition_occurs"),
        "data_constraint": ("field_population", "field_constraint_satisfied"),
        "enum_definition": ("informational_only", "enum_value_defined"),
        "workflow": ("workflow_progression", "permitted_branch_completed"),
        "calculation": ("calculated_value", "calculated_value_available"),
        "reference_only": ("informational_only", None),
    }
    kind, state = mapping[rule_type]
    return {"kind": kind, "expected_state": state, "details": {}}


def build_type_payload(rule_type: str, text: str, tags: list[str]) -> dict:
    lowered = text.lower()
    if rule_type == "obligation":
        return {"obligation": {"mode": "must", "fulfillment": "required"}}
    if rule_type == "prohibition":
        return {"prohibition": {"mode": "must_not", "scope": "submission" if "submit" in lowered else "general"}}
    if rule_type == "permission":
        return {"permission": {"mode": "may", "optional": True}}
    if rule_type == "deadline":
        time_match = re.search(r"(\d{1,2}:\d{2})", text)
        relative_match = re.search(r"within\s+(\d+)\s+minutes?", lowered)
        return {"deadline": {
            "deadline_kind": "relative" if relative_match else "absolute_time" if time_match else "business_day_cutoff",
            "reference_event": "execution_event" if "execution" in lowered else "submission_event",
            "offset_iso8601": f"PT{relative_match.group(1)}M" if relative_match else None,
            "absolute_time_local": time_match.group(1) if time_match and not relative_match else None,
            "timezone": "Europe/London" if time_match else None,
            "business_day_offset": 1 if "t+1" in lowered or "following business day" in lowered else 0,
            "breach_outcome": "late_submission",
        }}
    if rule_type == "state_transition":
        return {"state_transition": {
            "trigger_event": "submission_event" if "submit" in lowered or "enter" in lowered else "workflow_event",
            "from_state": "submitted" if "submitted" in lowered else None,
            "to_state": "matched" if "matched" in lowered else "updated_state",
            "automatic": "automatically" in lowered or "will" in lowered,
        }}
    if rule_type == "data_constraint":
        return {"data_constraint": {
            "field": "trade_time" if "trade time" in lowered else "unspecified_field",
            "constraint_kind": "format" if "entered as" in lowered else "required_field" if "must include" in lowered else "value_restriction",
            "format": "HH:MM:SS" if "hh:mm:ss" in lowered else None,
            "allowed_values": ["US Dollars"] if "us dollars" in lowered and "may only be executed" in lowered else [],
            "applies_when": tags,
        }}
    if rule_type == "enum_definition":
        field = "venue_code" if "venue" in lowered else "trade_category" if "trade category" in lowered else "enum_field"
        value_match = re.search(r":\s*([A-Za-z\- /]+?)\s+is used", text)
        if not value_match:
            value_match = re.search(r":\s*([A-Za-z\- /]+?)\s+for all", text)
        return {"enum_definition": {
            "field": field,
            "value": normalize_text(value_match.group(1)) if value_match else "unspecified_value",
            "meaning": normalize_text(text),
            "applies_to": ["trade"],
        }}
    if rule_type == "workflow":
        return {"workflow": {
            "trigger": normalize_text(text.split(":", 1)[0]),
            "branches": [{"branch_id": "A", "branch_condition": "primary_path", "steps": [normalize_text(text)]}],
        }}
    if rule_type == "calculation":
        return {"calculation": {
            "calculation_kind": "substitution" if "substitute" in lowered else "weighted_average" if "average" in lowered else "other",
            "inputs": ["short_price_code", "published_absolute_value"] if "short price" in lowered else ["price_inputs"],
            "formula_description": normalize_text(text),
            "rounding_rule": None,
        }}
    return {"reference_only": {"reason": "contextual_explanation_only"}}


def build_execution_mapping(rule_type: str, tags: list[str], action: str | None, obj: str | None) -> dict:
    inputs = []
    if "timing" in tags:
        inputs.extend(["execution_time", "submission_time"])
    if "venue" in tags:
        inputs.append("venue_code")
    if "price" in tags:
        inputs.append("price")
    if "account" in tags:
        inputs.append("account")
    if obj:
        inputs.append(obj)

    if rule_type == "reference_only":
        outputs = []
    elif rule_type == "state_transition":
        outputs = ["state_change", "resulting_trade_state"]
    elif rule_type == "deadline":
        outputs = ["recorded_timestamp", "deadline_validation_result"]
    else:
        outputs = ["validation_result", "processing_result"]

    assertions = []
    if rule_type == "deadline":
        assertions.append({"target": "deadline_validation_result", "operator": "equals", "value": "pass"})
    elif rule_type == "prohibition":
        assertions.append({"target": "validation_result", "operator": "equals", "value": "reject"})
    elif rule_type != "reference_only":
        assertions.append({"target": "processing_result", "operator": "not_equals", "value": None})

    return {
        "business_inputs": sorted(dict.fromkeys(inputs)),
        "observable_outputs": outputs,
        "system_events": [action] if action else [],
        "preconditions_for_execution": [],
        "postconditions_for_execution": [rule_type],
        "dsl_assertions": assertions,
    }


def build_hints(rule_type: str, text: str, tags: list[str]) -> dict:
    return {
        "gherkin_intent": normalize_text(text),
        "positive_scenarios": [f"happy path for {rule_type}"],
        "negative_scenarios": ["invalid input path"] if rule_type in {"prohibition", "data_constraint", "deadline"} else [],
        "boundary_scenarios": ["boundary timing case"] if rule_type == "deadline" else [],
        "data_requirements": tags,
        "oracle_notes": ["First-pass machine-generated semantic rule."],
    }


def build_semantic_rule(rule: dict, doc_id: str, doc_title: str, doc_version: str) -> dict:
    text = normalize_text(rule["raw_text"])
    rule_type = rule["rule_type"]
    tags = infer_rule_tags(rule)
    actor_value, actor_source_type = infer_actor(text, rule_type)
    action_value, action_source_type = infer_action(text, rule_type)
    object_value, object_source_type = infer_object(text, rule_type)
    return {
        "semantic_rule_id": f"SR-{rule['rule_id']}",
        "version": "1.0",
        "source": {
            "doc_id": doc_id,
            "doc_title": doc_title,
            "doc_version": doc_version,
            "section": rule.get("section"),
            "clause_refs": [rule["clause_number"]],
            "atomic_rule_ids": [rule["rule_id"]],
            "pages": list(range(rule["start_page"], rule["end_page"] + 1)),
        },
        "classification": {
            "rule_type": rule_type,
            "rule_tags": tags,
            "testability": "non_testable" if rule_type == "reference_only" else rule.get("testability", "testable"),
            "priority": infer_priority(rule_type, tags),
            "coverage_eligible": rule_type != "reference_only",
        },
        "statement": {
            "actor": {"value": actor_value, "source_type": actor_source_type},
            "action": {"value": action_value, "source_type": action_source_type},
            "object": {"value": object_value, "source_type": object_source_type},
            "conditions": build_conditions(text),
            "constraints": build_constraints(text),
            "outcome": build_outcome(rule_type),
            "exceptions": [],
        },
        "type_payload": build_type_payload(rule_type, text, tags),
        "execution_mapping": build_execution_mapping(rule_type, tags, action_value, object_value),
        "evidence": [{
            "target": "statement",
            "quote": text,
            "page": rule["start_page"],
            "atomic_rule_id": rule["rule_id"],
        }],
        "review": {
            "confidence": 0.65 if rule_type != "reference_only" else 0.5,
            "inference_flags": ["first_pass_semantic_generation"],
            "ambiguities": [],
        },
        "test_design_hints": build_hints(rule_type, text, tags),
    }


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    doc_id, doc_title, doc_version, metadata = load_metadata(args, output_path)

    atomic_rules = json.loads(input_path.read_text(encoding="utf-8"))
    semantic_rules = [build_semantic_rule(rule, doc_id, doc_title, doc_version) for rule in atomic_rules]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(semantic_rules, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "semantic_rule_count": len(semantic_rules),
        "output": str(output_path),
        "doc_id": doc_id,
        "source_format": metadata.get("source_format"),
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
