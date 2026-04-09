from __future__ import annotations

import sys

from governance_checks import REPO_ROOT, check_docs_governance


def main() -> int:
    errors = check_docs_governance(REPO_ROOT)
    if errors:
        print("Docs governance check failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Docs governance check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
