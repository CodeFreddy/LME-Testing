import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from lme_testing.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
