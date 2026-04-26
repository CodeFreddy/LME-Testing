import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from lme_testing.cli import main


if __name__ == "__main__":
    raise SystemExit(main())

