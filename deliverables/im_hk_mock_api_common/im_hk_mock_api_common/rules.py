"""Version-neutral rule catalog helpers for Initial Margin mock APIs."""

from __future__ import annotations


REQUIRED_RPF_GLOBAL_FIELDS = {
    "Valuation_DT",
    "HVaR_WGT",
    "SVaR_WGT",
    "HVaR_Scen_Count",
    "SVaR_Scen_Count",
    "HVaR_CL",
    "SVaR_CL",
    "Rounding",
}

SUPPORTED_FIELD_TYPES = {1, 2, 3, 4, 5, 6, 7}


def build_rule_catalog(version_label: str, rule_prefix: str) -> list[dict[str, str]]:
    return [
        {
            "rule_id": f"{rule_prefix}-RPF",
            "title": "Initial Margin Risk Parameter File contains required global and FieldType records",
            "source": f"{version_label} Section 2.2, pages 6-8",
            "endpoint": "POST /rpf/validate",
        },
        {
            "rule_id": f"{rule_prefix}-POS",
            "title": "Positions are normalized with market value equal to quantity times market price",
            "source": f"{version_label} Section 3.1.2, page 8",
            "endpoint": "POST /positions/normalize",
        },
        {
            "rule_id": f"{rule_prefix}-MRC",
            "title": "Market risk components are derived from applicable instrument parameters",
            "source": f"{version_label} Sections 3.2.2-3.2.4, pages 10-19",
            "endpoint": "POST /margin/market-risk-components",
        },
        {
            "rule_id": f"{rule_prefix}-FLAT-RATE",
            "title": "Flat rate margin includes the dominant long or short side per sub-category",
            "source": f"{version_label} Section 3.2.4.2, pages 15-16",
            "endpoint": "POST /margin/flat-rate",
        },
        {
            "rule_id": f"{rule_prefix}-ROUND",
            "title": "Aggregated market risk component margin is rounded up",
            "source": f"{version_label} Section 3.2.5.1, page 20",
            "endpoint": "POST /margin/aggregate",
        },
        {
            "rule_id": f"{rule_prefix}-MTM",
            "title": "Favorable MTM and MTM requirement are separated after netting",
            "source": f"{version_label} Sections 3.2.5.2 and 3.2.6.1, pages 20-21",
            "endpoint": "POST /margin/mtm",
        },
        {
            "rule_id": f"{rule_prefix}-CA",
            "title": "Corporate action positions are adjusted before netting",
            "source": f"{version_label} Section 4.4, pages 28-33",
            "endpoint": "POST /corporate-actions/adjust",
        },
        {
            "rule_id": f"{rule_prefix}-NET",
            "title": "Positions are cross-day netted at instrument level",
            "source": f"{version_label} Section 4.5, pages 33-34",
            "endpoint": "POST /positions/cross-day-net",
        },
        {
            "rule_id": f"{rule_prefix}-FX",
            "title": "Cross-currency MTM netting applies FX haircut directionally",
            "source": f"{version_label} Section 4.6, pages 34-35",
            "endpoint": "POST /mtm/cross-currency-net",
        },
        {
            "rule_id": f"{rule_prefix}-INTRADAY",
            "title": "Intraday MTM treats due positions differently at 11:00 and 14:00 HKT",
            "source": f"{version_label} Section 4.7/4.8, pages 35-38",
            "endpoint": "POST /mtm/intraday",
        },
    ]
