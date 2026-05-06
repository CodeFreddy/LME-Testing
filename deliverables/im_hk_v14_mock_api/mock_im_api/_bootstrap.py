"""Import helper for the sibling shared Initial Margin mock package."""

from __future__ import annotations

import sys
from pathlib import Path


COMMON_ROOT = Path(__file__).resolve().parents[2] / "im_hk_mock_api_common"
if str(COMMON_ROOT) not in sys.path:
    sys.path.insert(0, str(COMMON_ROOT))
