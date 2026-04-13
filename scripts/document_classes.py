"""Document class registry for multi-document ingestion (Phase 2 Gate 1).

This module defines document classes and their associated parsing strategies,
enabling the extraction pipeline to handle different document types with
class-specific rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class DocumentClass(str, Enum):
    """Supported document classes for ingestion."""

    RULEBOOK = "rulebook"
    API_SPEC = "api_spec"
    POLICY = "policy"
    WORKFLOW = "workflow"


# ---------------------------------------------------------------------------
# Rule type hints per document class
# ---------------------------------------------------------------------------

RULEBOOK_RULE_TYPE_HINTS = {
    "shall": "obligation",
    "must": "obligation",
    "will": "obligation",
    "may not": "prohibition",
    "prohibited": "prohibition",
    "shall not": "prohibition",
    "may": "permission",
    "can": "permission",
    "within": "deadline",
    "deadline": "deadline",
    "by ": "deadline",
    "transition": "state_transition",
    "data": "data_constraint",
    "field": "data_constraint",
    "value": "data_constraint",
    "calculate": "calculation",
    "workflow": "workflow",
    "enum": "enum_definition",
    "see": "reference_only",
    "refer to": "reference_only",
    "as defined": "reference_only",
}

API_SPEC_RULE_TYPE_HINTS = {
    "required": "obligation",
    "must not": "prohibition",
    "disallowed": "prohibition",
    "optional": "permission",
    "constraint": "data_constraint",
    "calculation": "calculation",
    "state": "state_transition",
    "workflow": "workflow",
    "enum": "enum_definition",
}

POLICY_RULE_TYPE_HINTS = {
    "must": "obligation",
    "prohibited": "prohibition",
    "permitted": "permission",
    "procedure": "workflow",
    "data": "data_constraint",
    "deadline": "deadline",
}


# ---------------------------------------------------------------------------
# Parsing strategies
# ---------------------------------------------------------------------------

@dataclass
class ParsingStrategy:
    """Parsing strategy for a document class."""

    document_class: DocumentClass
    clause_pattern: str  # Regex pattern for clause detection
    section_header_pattern: str  # Regex pattern for section headers
    rule_hint_keywords: dict[str, str]  # keyword -> rule_type mapping
    source_anchor_type: str  # e.g., "paragraph_id", "endpoint_id"
    default_rule_type: str = "reference_only"
    split_strategy: str = "clause"  # How to split into atomic rules


RULEBOOK_STRATEGY = ParsingStrategy(
    document_class=DocumentClass.RULEBOOK,
    clause_pattern=r"(?<![\d:?+\-])([1-9]\d{0,2})\.\s",
    section_header_pattern=r"^##\s+(.+?)\s*$",
    rule_hint_keywords=RULEBOOK_RULE_TYPE_HINTS,
    source_anchor_type="paragraph_id",
    default_rule_type="obligation",
    split_strategy="clause",
)

API_SPEC_STRATEGY = ParsingStrategy(
    document_class=DocumentClass.API_SPEC,
    clause_pattern=r"(GET|POST|PUT|DELETE|PATCH)\s+",
    section_header_pattern=r"^###?\s+(.+?)\s*$",
    rule_hint_keywords=API_SPEC_RULE_TYPE_HINTS,
    source_anchor_type="endpoint_id",
    default_rule_type="obligation",
    split_strategy="endpoint",
)

POLICY_STRATEGY = ParsingStrategy(
    document_class=DocumentClass.POLICY,
    clause_pattern=r"^\d+\.\s+",
    section_header_pattern=r"^#+\s+(.+?)\s*$",
    rule_hint_keywords=POLICY_RULE_TYPE_HINTS,
    source_anchor_type="section_id",
    default_rule_type="workflow",
    split_strategy="section",
)

WORKFLOW_STRATEGY = ParsingStrategy(
    document_class=DocumentClass.WORKFLOW,
    clause_pattern=r"^\d+\.\s+[A-Z]",
    section_header_pattern=r"^#+\s+(.+?)\s*$",
    rule_hint_keywords={},
    source_anchor_type="step_id",
    default_rule_type="workflow",
    split_strategy="step",
)


STRATEGY_BY_CLASS: dict[DocumentClass, ParsingStrategy] = {
    DocumentClass.RULEBOOK: RULEBOOK_STRATEGY,
    DocumentClass.API_SPEC: API_SPEC_STRATEGY,
    DocumentClass.POLICY: POLICY_STRATEGY,
    DocumentClass.WORKFLOW: WORKFLOW_STRATEGY,
}


def strategy_for(document_class: DocumentClass) -> ParsingStrategy:
    """Return the parsing strategy for a document class."""
    return STRATEGY_BY_CLASS.get(document_class, RULEBOOK_STRATEGY)


def infer_rule_type(text: str, document_class: DocumentClass) -> str:
    """Infer rule type from text content using class-specific hints."""
    strategy = strategy_for(document_class)
    text_lower = text.lower()
    for keyword, rule_type in strategy.rule_hint_keywords.items():
        if keyword in text_lower:
            return rule_type
    return strategy.default_rule_type


@dataclass
class ExtractionConfig:
    """Configuration for document extraction."""

    document_class: DocumentClass
    doc_id: str
    doc_title: str
    doc_version: str
    output_dir: str
    strategy: ParsingStrategy = field(init=False)

    def __post_init__(self):
        self.strategy = strategy_for(self.document_class)

    @classmethod
    def from_args(cls, document_class: DocumentClass, doc_id: str, doc_title: str,
                  doc_version: str, output_dir: str) -> "ExtractionConfig":
        return cls(
            document_class=document_class,
            doc_id=doc_id,
            doc_title=doc_title,
            doc_version=doc_version,
            output_dir=output_dir,
        )
