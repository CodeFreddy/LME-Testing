"""Rule constants derived from LME_Matching_Rules_Aug_2022.md.

This mock is deliberately scoped to executable behaviours needed by generated
BDD/script validation. It is not a market system and does not claim production
coverage of the LME rules.
"""

from __future__ import annotations


RULE_CATALOG = [
    {
        "rule_id": "MR-001",
        "title": "Capitalised terms use LME Rulebook meaning",
        "source": "Page 2, paragraph 1",
        "endpoint": "POST /terminology/validate",
    },
    {
        "rule_id": "MR-002",
        "title": "All Exchange business is subject to price validation",
        "source": "Page 2, paragraph 2",
        "endpoint": "POST /trades/validate-price",
    },
    {
        "rule_id": "MR-003",
        "title": "Members contact the Exchange after price validation failure",
        "source": "Page 2, paragraph 3",
        "endpoint": "POST /trades/contact-exchange",
    },
    {
        "rule_id": "MR-004",
        "title": "Post-trade deadline extension requests are at least 15 minutes before deadline",
        "source": "Page 3, paragraph 4",
        "endpoint": "POST /deadlines/validate",
    },
    {
        "rule_id": "MR-007",
        "title": "Asian business hours Client Contracts are submitted by 08:30",
        "source": "Page 4, paragraph 7",
        "endpoint": "POST /trades/submit",
    },
    {
        "rule_id": "MR-008",
        "title": "Members retain a complete audit trail",
        "source": "Page 4, paragraph 8",
        "endpoint": "POST /audit/validate",
    },
    {
        "rule_id": "MR-046",
        "title": "Give-Up trades use Inter-office venue within 10 minutes",
        "source": "Page 15, paragraph 46",
        "endpoint": "POST /giveups/submit",
    },
    {
        "rule_id": "MR-064",
        "title": "OTC Bring-On validates pre-existing OTC transaction evidence",
        "source": "Page 19, paragraph 64",
        "endpoint": "POST /otc-bring-ons/validate",
    },
    {
        "rule_id": "MR-071",
        "title": "Auction bids reject invalid IDs, parameters, or category tuple",
        "source": "Page 20, paragraph 71",
        "endpoint": "POST /auctions/bids",
    },
    {
        "rule_id": "MR-075",
        "title": "OTC Bring-On cannot be misused to avoid PTT",
        "source": "Page 21, paragraph 75",
        "endpoint": "POST /ptt/validate",
    },
]


VALID_ACCOUNTS = {"H", "U", "C", "G", "S"}
VALID_TRADE_CATEGORIES = {
    "Normal",
    "Give-Up Executor",
    "Give-Up Clearer",
    "OTC Bring-On",
    "OTC Take Off",
    "Financing",
    "Exception Reportable",
    "Exception Non-Reportable",
    "Transfer",
    "Reversal/Correction",
}
VALID_VENUES = {"Select", "Ring", "Basis Ring", "Inter-office"}
VALID_PRICE_TYPES = {"Current", "Historic"}
VALID_AUCTION_TUPLE = {
    "category": "Normal",
    "price_type": "Current",
    "venue": "Inter-office",
}

