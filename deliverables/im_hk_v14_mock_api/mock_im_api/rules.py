"""Rule catalog for the Initial Margin HKv14 mock API wrapper."""

from __future__ import annotations

from . import _bootstrap  # noqa: F401
from im_hk_mock_api_common.rules import REQUIRED_RPF_GLOBAL_FIELDS, SUPPORTED_FIELD_TYPES, build_rule_catalog


RULE_CATALOG = build_rule_catalog("HKv14", "IM-HK14")

__all__ = ["RULE_CATALOG", "REQUIRED_RPF_GLOBAL_FIELDS", "SUPPORTED_FIELD_TYPES"]
