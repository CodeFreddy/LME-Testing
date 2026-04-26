"""Rule constants derived from Initial Margin Calculation Guide HKv13.

This mock is scoped to deterministic validation of executable BDD/script shape.
It is not a production margin engine and does not claim full HKEX/HKSCC fidelity.
"""

from __future__ import annotations


RULE_CATALOG = [
    {
        "rule_id": "IM-HK13-RPF",
        "title": "Initial Margin Risk Parameter File contains required global and FieldType records",
        "source": "Section 2.2, pages 6-8",
        "endpoint": "POST /rpf/validate",
    },
    {
        "rule_id": "IM-HK13-POS",
        "title": "Positions are normalized with market value equal to quantity times market price",
        "source": "Section 3.1.2, page 8",
        "endpoint": "POST /positions/normalize",
    },
    {
        "rule_id": "IM-HK13-MRC",
        "title": "Market risk components are derived from applicable instrument parameters",
        "source": "Sections 3.2.2-3.2.4, pages 10-19",
        "endpoint": "POST /margin/market-risk-components",
    },
    {
        "rule_id": "IM-HK13-FLAT-RATE",
        "title": "Flat rate margin includes the dominant long or short side per sub-category",
        "source": "Section 3.2.4.2, pages 15-16",
        "endpoint": "POST /margin/flat-rate",
    },
    {
        "rule_id": "IM-HK13-ROUND",
        "title": "Aggregated market risk component margin is rounded up",
        "source": "Section 3.2.5.1, page 20",
        "endpoint": "POST /margin/aggregate",
    },
    {
        "rule_id": "IM-HK13-MTM",
        "title": "Favorable MTM and MTM requirement are separated after netting",
        "source": "Sections 3.2.5.2 and 3.2.6.1, pages 20-21",
        "endpoint": "POST /margin/mtm",
    },
    {
        "rule_id": "IM-HK13-CA",
        "title": "Corporate action positions are adjusted before netting",
        "source": "Section 4.4, pages 28-33",
        "endpoint": "POST /corporate-actions/adjust",
    },
    {
        "rule_id": "IM-HK13-NET",
        "title": "Positions are cross-day netted at instrument level",
        "source": "Section 4.5, pages 33-34",
        "endpoint": "POST /positions/cross-day-net",
    },
    {
        "rule_id": "IM-HK13-FX",
        "title": "Cross-currency MTM netting applies FX haircut directionally",
        "source": "Section 4.6, pages 34-35",
        "endpoint": "POST /mtm/cross-currency-net",
    },
    {
        "rule_id": "IM-HK13-INTRADAY",
        "title": "Intraday MTM treats due positions differently at 11:00 and 14:00 HKT",
        "source": "Section 4.7, pages 35-38",
        "endpoint": "POST /mtm/intraday",
    },
]


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
