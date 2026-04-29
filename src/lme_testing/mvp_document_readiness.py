from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .storage import atomic_write_json, ensure_dir, timestamp_slug


ALLOWED_DOCUMENT_ROLES = {
    "function_spec_previous",
    "function_spec_current",
    "test_plan",
    "regression_pack_index",
    "automation_feature_index",
}

ALLOWED_READINESS_STATES = {
    "ready",
    "placeholder",
    "blocked",
}

REQUIRED_DOCUMENT_FIELDS = {
    "document_id",
    "title",
    "version",
    "document_class",
    "document_role",
    "source_path",
    "source_exists",
    "owner_role",
    "status",
    "checksum",
    "supersedes",
    "readiness_state",
    "missing_required_fields",
    "notes",
}

TEST_PLAN_EXPECTATION_GROUPS = {
    "test_objective_or_scope": ("objective", "scope", "purpose"),
    "target_system_or_domain": ("system", "domain", "application"),
    "applicable_spec_version": ("spec", "specification", "function spec", "hkv13", "hkv14", "version"),
    "in_scope_test_levels_or_types": ("in scope", "in-scope", "test level", "test type", "regression", "functional"),
    "out_of_scope_or_exclusions": ("out of scope", "out-of-scope", "exclusion", "excluded"),
    "qa_owner_or_approver": ("qa", "owner", "approver", "approval"),
    "revision_or_version_marker": ("revision", "version", "baseline"),
}

REGRESSION_PACK_EXPECTATION_GROUPS = {
    "regression_pack_identifier": ("regression pack", "pack id", "suite", "identifier"),
    "target_system_or_domain": ("system", "domain", "application"),
    "applicable_spec_version_or_release": ("spec", "specification", "release", "baseline", "hkv13", "hkv14", "version"),
    "suite_scenario_script_or_case_list": ("suite", "scenario", "script", "case", "test id"),
    "owner_or_maintaining_role": ("owner", "maintainer", "automation lead", "automation"),
    "revision_or_version_marker": ("revision", "version", "baseline"),
    "automation_coverage_note": ("coverage", "partial", "unknown", "automated", "manual"),
}


class DocumentReadinessValidationError(ValueError):
    """Raised when the S2-F2 document readiness registry violates its contract."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_document_record(
    *,
    document_id: str,
    title: str,
    version: str,
    document_class: str,
    document_role: str,
    source_path: Path | None,
    owner_role: str,
    status: str,
    supersedes: str | None = None,
    readiness_state: str | None = None,
    notes: str = "",
) -> dict[str, Any]:
    source_text = source_path.as_posix() if source_path is not None else ""
    source_exists = bool(source_path and source_path.exists())
    missing_required_fields = []

    required_text = {
        "document_id": document_id,
        "title": title,
        "version": version,
        "document_class": document_class,
        "document_role": document_role,
        "owner_role": owner_role,
        "status": status,
    }
    for field, value in required_text.items():
        if not str(value).strip():
            missing_required_fields.append(field)
    if not source_text:
        missing_required_fields.append("source_path")

    state = readiness_state
    if state is None:
        state = "ready" if source_exists and not missing_required_fields else "blocked"

    checksum = sha256_file(source_path) if source_exists and source_path is not None else ""

    return {
        "document_id": document_id,
        "title": title,
        "version": version,
        "document_class": document_class,
        "document_role": document_role,
        "source_path": source_text,
        "source_exists": source_exists,
        "owner_role": owner_role,
        "status": status,
        "checksum": checksum,
        "supersedes": supersedes,
        "readiness_state": state,
        "missing_required_fields": sorted(set(missing_required_fields)),
        "notes": notes,
    }


def _read_text_source(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def _missing_content_expectations(text: str | None, expectation_groups: dict[str, tuple[str, ...]]) -> list[str]:
    if text is None:
        return ["utf8_text_source"]
    normalized = text.casefold()
    missing = []
    for expectation, keywords in expectation_groups.items():
        if not any(keyword.casefold() in normalized for keyword in keywords):
            missing.append(expectation)
    return sorted(missing)


def build_contract_document_record(
    *,
    document_id: str,
    title: str,
    version: str,
    document_class: str,
    document_role: str,
    source_path: Path,
    owner_role: str,
    notes: str,
    expectation_groups: dict[str, tuple[str, ...]],
) -> dict[str, Any]:
    source_exists = source_path.exists()
    content_missing = _missing_content_expectations(_read_text_source(source_path) if source_exists else "", expectation_groups)
    record = build_document_record(
        document_id=document_id,
        title=title,
        version=version,
        document_class=document_class,
        document_role=document_role,
        source_path=source_path,
        owner_role=owner_role,
        status="registered" if source_exists else "blocked",
        readiness_state="ready" if source_exists and not content_missing else "blocked",
        notes=notes if not content_missing else f"{notes} Missing minimum content expectations: {', '.join(content_missing)}.",
    )
    record["missing_required_fields"] = sorted(set(record["missing_required_fields"]) | set(content_missing))
    if record["missing_required_fields"]:
        record["readiness_state"] = "blocked"
        record["status"] = "blocked"
    return record


def build_test_plan_record(
    *,
    source_path: Path | None,
    title: str = "MVP Test Plan",
    version: str = "not_available",
) -> dict[str, Any]:
    if source_path is None:
        return build_document_record(
            document_id="mvp_test_plan_placeholder",
            title=title,
            version=version,
            document_class="Test Plan",
            document_role="test_plan",
            source_path=None,
            owner_role="QA Lead",
            status="placeholder",
            readiness_state="placeholder",
            notes="Placeholder only. No Test Plan source has been provided for S2-F2/S2-F3.",
        )
    return build_contract_document_record(
        document_id="mvp_test_plan",
        title=title or source_path.stem,
        version=version,
        document_class="Test Plan",
        document_role="test_plan",
        source_path=source_path,
        owner_role="QA Lead",
        notes="Real Test Plan input registered under the S2-F3 minimum input contract.",
        expectation_groups=TEST_PLAN_EXPECTATION_GROUPS,
    )


def build_regression_pack_index_record(
    *,
    source_path: Path | None,
    title: str = "MVP Regression Pack Index",
    version: str = "not_available",
) -> dict[str, Any]:
    if source_path is None:
        return build_document_record(
            document_id="mvp_regression_pack_index_placeholder",
            title=title,
            version=version,
            document_class="Regression Pack Index",
            document_role="regression_pack_index",
            source_path=None,
            owner_role="Automation Lead",
            status="placeholder",
            readiness_state="placeholder",
            notes="Placeholder only. No Regression Pack Index source has been provided for S2-F2/S2-F3.",
        )
    return build_contract_document_record(
        document_id="mvp_regression_pack_index",
        title=title or source_path.stem,
        version=version,
        document_class="Regression Pack Index",
        document_role="regression_pack_index",
        source_path=source_path,
        owner_role="Automation Lead",
        notes="Real Regression Pack Index input registered under the S2-F3 minimum input contract.",
        expectation_groups=REGRESSION_PACK_EXPECTATION_GROUPS,
    )


def build_hkv14_poc_registry(
    *,
    previous_spec_path: Path = Path("docs/materials/Initial Margin Calculation Guide HKv13.pdf"),
    current_spec_path: Path = Path("docs/materials/Initial Margin Calculation Guide HKv14.pdf"),
    test_plan_path: Path | None = None,
    test_plan_title: str = "MVP Test Plan",
    test_plan_version: str = "not_available",
    regression_pack_index_path: Path | None = None,
    regression_pack_index_title: str = "MVP Regression Pack Index",
    regression_pack_index_version: str = "not_available",
    generated_at: str | None = None,
) -> dict[str, Any]:
    timestamp = generated_at or timestamp_slug()
    documents = [
        build_document_record(
            document_id="im_hk_v13_function_spec",
            title="Initial Margin Calculation Guide HKv13",
            version="HKv13",
            document_class="Initial Margin calculation guide",
            document_role="function_spec_previous",
            source_path=previous_spec_path,
            owner_role="BA",
            status="registered",
            readiness_state="ready",
            notes="Repository-specific stand-in for the MVP Function Spec old version.",
        ),
        build_document_record(
            document_id="im_hk_v14_function_spec",
            title="Initial Margin Calculation Guide HKv14",
            version="HKv14",
            document_class="Initial Margin calculation guide",
            document_role="function_spec_current",
            source_path=current_spec_path,
            owner_role="BA",
            status="registered",
            supersedes="im_hk_v13_function_spec",
            readiness_state="ready",
            notes="Repository-specific stand-in for the MVP Function Spec new version.",
        ),
        build_test_plan_record(
            source_path=test_plan_path,
            title=test_plan_title,
            version=test_plan_version,
        ),
        build_regression_pack_index_record(
            source_path=regression_pack_index_path,
            title=regression_pack_index_title,
            version=regression_pack_index_version,
        ),
    ]

    relationships = [
        {
            "relationship_type": "supersedes",
            "source_document_id": "im_hk_v14_function_spec",
            "target_document_id": "im_hk_v13_function_spec",
            "notes": "HKv14 current function-spec stand-in supersedes HKv13 previous function-spec stand-in.",
        }
    ]
    blockers = derive_blockers(documents)
    registry = {
        "metadata": {
            "task_id": "S2-F2",
            "record_type": "mvp_document_readiness_registry",
            "generated_at": timestamp,
            "canonical": True,
            "generation_mode": "deterministic",
        },
        "workflow_instance": {
            "workflow_id": "im_hk_v14_poc_document_readiness",
            "scope": "HKv13/HKv14 Initial Margin POC document readiness",
            "status": "blocked" if blockers else "ready",
        },
        "documents": documents,
        "relationships": relationships,
        "readiness_summary": summarize_documents(documents),
        "blockers": blockers,
        "limitations": [
            "Initial Margin guides are repo-specific stand-ins for Function Spec old/new documents.",
            "Test Plan and Regression Pack Index are ready only when real source files meet the S2-F3 minimum input contract.",
            "This registry does not claim Stage 3 real execution readiness.",
        ],
    }
    validate_document_readiness(registry)
    return registry


def summarize_documents(documents: list[dict[str, Any]]) -> dict[str, Any]:
    by_state = {state: 0 for state in sorted(ALLOWED_READINESS_STATES)}
    by_role: dict[str, str] = {}
    existing_sources = 0
    for document in documents:
        state = str(document.get("readiness_state", ""))
        by_state[state] = by_state.get(state, 0) + 1
        by_role[str(document.get("document_role", ""))] = state
        if document.get("source_exists"):
            existing_sources += 1
    return {
        "document_count": len(documents),
        "existing_source_count": existing_sources,
        "missing_source_count": len(documents) - existing_sources,
        "by_readiness_state": by_state,
        "by_document_role": dict(sorted(by_role.items())),
        "overall_readiness": "ready" if by_state.get("blocked", 0) == 0 and by_state.get("placeholder", 0) == 0 else "blocked",
    }


def derive_blockers(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blockers = []
    for document in documents:
        state = document.get("readiness_state")
        if state == "ready":
            continue
        blockers.append(
            {
                "document_id": document.get("document_id"),
                "document_role": document.get("document_role"),
                "readiness_state": state,
                "missing_required_fields": document.get("missing_required_fields", []),
                "source_exists": document.get("source_exists"),
                "notes": document.get("notes", ""),
            }
        )
    return blockers


def validate_document_readiness(registry: dict[str, Any]) -> None:
    required_top = {"metadata", "workflow_instance", "documents", "relationships", "readiness_summary", "blockers", "limitations"}
    missing_top = required_top - set(registry)
    if missing_top:
        raise DocumentReadinessValidationError(f"Registry missing top-level fields: {sorted(missing_top)}")

    documents = registry.get("documents")
    if not isinstance(documents, list) or not documents:
        raise DocumentReadinessValidationError("Registry must contain at least one document.")

    seen: set[str] = set()
    for index, document in enumerate(documents):
        if not isinstance(document, dict):
            raise DocumentReadinessValidationError(f"Document {index} must be an object.")
        missing_fields = REQUIRED_DOCUMENT_FIELDS - set(document)
        if missing_fields:
            raise DocumentReadinessValidationError(f"Document {index} missing fields: {sorted(missing_fields)}")
        document_id = str(document["document_id"])
        if not document_id:
            raise DocumentReadinessValidationError(f"Document {index} has blank document_id.")
        if document_id in seen:
            raise DocumentReadinessValidationError(f"Duplicate document_id: {document_id}")
        seen.add(document_id)
        if document["document_role"] not in ALLOWED_DOCUMENT_ROLES:
            raise DocumentReadinessValidationError(f"Unsupported document_role for {document_id}: {document['document_role']}")
        if document["readiness_state"] not in ALLOWED_READINESS_STATES:
            raise DocumentReadinessValidationError(
                f"Unsupported readiness_state for {document_id}: {document['readiness_state']}"
            )
        if not isinstance(document["missing_required_fields"], list):
            raise DocumentReadinessValidationError(f"missing_required_fields must be a list for {document_id}.")
        if document["readiness_state"] == "ready":
            if document["missing_required_fields"]:
                raise DocumentReadinessValidationError(f"Ready document {document_id} has missing required fields.")
            if not document["source_exists"]:
                raise DocumentReadinessValidationError(f"Ready document {document_id} must have an existing source.")
            if not document["checksum"]:
                raise DocumentReadinessValidationError(f"Ready document {document_id} must have a checksum.")
        if document["source_exists"] and not document["checksum"]:
            raise DocumentReadinessValidationError(f"Existing source for {document_id} must have a checksum.")

    for relationship in registry.get("relationships", []):
        source = relationship.get("source_document_id")
        target = relationship.get("target_document_id")
        if source not in seen or target not in seen:
            raise DocumentReadinessValidationError(f"Relationship references unknown documents: {source} -> {target}")

    blockers = registry.get("blockers")
    if not isinstance(blockers, list):
        raise DocumentReadinessValidationError("blockers must be a list.")
    blocked_document_ids = {document["document_id"] for document in documents if document["readiness_state"] != "ready"}
    blocker_document_ids = {blocker.get("document_id") for blocker in blockers}
    missing_blockers = blocked_document_ids - blocker_document_ids
    if missing_blockers:
        raise DocumentReadinessValidationError(f"Missing blockers for non-ready documents: {sorted(missing_blockers)}")


def render_markdown_summary(registry: dict[str, Any]) -> str:
    validate_document_readiness(registry)
    metadata = registry["metadata"]
    summary = registry["readiness_summary"]
    lines = [
        "# MVP Document Readiness Summary",
        "",
        "This Markdown summary is derived from `document_readiness.json`; the JSON registry is canonical.",
        "",
        f"- Task ID: `{metadata['task_id']}`",
        f"- Generated at: `{metadata['generated_at']}`",
        f"- Workflow: `{registry['workflow_instance']['workflow_id']}`",
        f"- Overall readiness: `{summary['overall_readiness']}`",
        f"- Documents: {summary['document_count']}",
        f"- Existing sources: {summary['existing_source_count']}",
        f"- Missing sources: {summary['missing_source_count']}",
        "",
        "## Documents",
        "",
        "| Document ID | Role | Version | Source Exists | Readiness |",
        "| --- | --- | --- | --- | --- |",
    ]
    for document in registry["documents"]:
        lines.append(
            f"| `{document['document_id']}` | `{document['document_role']}` | "
            f"`{document['version']}` | `{document['source_exists']}` | `{document['readiness_state']}` |"
        )
    lines.extend(["", "## Blockers", ""])
    if registry["blockers"]:
        for blocker in registry["blockers"]:
            lines.append(f"- `{blocker['document_role']}` / `{blocker['document_id']}`: {blocker['notes']}")
    else:
        lines.append("- None.")
    lines.extend(["", "## Limitations", ""])
    for limitation in registry["limitations"]:
        lines.append(f"- {limitation}")
    lines.append("")
    return "\n".join(lines)


def write_document_readiness_package(
    *,
    output_dir: Path = Path("evidence/mvp_document_readiness"),
    previous_spec_path: Path = Path("docs/materials/Initial Margin Calculation Guide HKv13.pdf"),
    current_spec_path: Path = Path("docs/materials/Initial Margin Calculation Guide HKv14.pdf"),
    test_plan_path: Path | None = None,
    test_plan_title: str = "MVP Test Plan",
    test_plan_version: str = "not_available",
    regression_pack_index_path: Path | None = None,
    regression_pack_index_title: str = "MVP Regression Pack Index",
    regression_pack_index_version: str = "not_available",
    generated_at: str | None = None,
) -> dict[str, Any]:
    run_id = generated_at or timestamp_slug()
    run_dir = ensure_dir(output_dir / run_id)
    registry = build_hkv14_poc_registry(
        previous_spec_path=previous_spec_path,
        current_spec_path=current_spec_path,
        test_plan_path=test_plan_path,
        test_plan_title=test_plan_title,
        test_plan_version=test_plan_version,
        regression_pack_index_path=regression_pack_index_path,
        regression_pack_index_title=regression_pack_index_title,
        regression_pack_index_version=regression_pack_index_version,
        generated_at=run_id,
    )
    registry_path = run_dir / "document_readiness.json"
    summary_path = run_dir / "document_readiness_summary.md"
    atomic_write_json(registry_path, registry)
    summary_path.write_text(render_markdown_summary(registry), encoding="utf-8")
    return {
        "run_id": run_id,
        "document_readiness": str(registry_path),
        "document_readiness_summary": str(summary_path),
        "document_count": registry["readiness_summary"]["document_count"],
        "overall_readiness": registry["readiness_summary"]["overall_readiness"],
        "blocker_count": len(registry["blockers"]),
    }
