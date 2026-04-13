#!/usr/bin/env python
"""Model Governance Check Script (Phase 2 Gate 7)

Validates that:
- All pipeline run summaries have required model/prompt metadata.

Usage:
    python scripts/check_model_governance.py
    python scripts/check_model_governance.py --repo-root /path/to/repo
"""

from __future__ import annotations

import argparse
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from governance_checks import check_model_governance


def main() -> int:
    parser = argparse.ArgumentParser(description="Run model governance checks.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Path to the repository root.",
    )
    args = parser.parse_args()

    errors = check_model_governance(args.repo_root)
    if errors:
        print("Model governance check FAILED:")
        for error in errors:
            print(f"  {error}")
        return 1
    print("Model governance check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
