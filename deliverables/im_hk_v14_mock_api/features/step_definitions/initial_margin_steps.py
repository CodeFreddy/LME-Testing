from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


COMMON_ROOT = Path(__file__).resolve().parents[3] / "im_hk_mock_api_common"
if str(COMMON_ROOT) not in sys.path:
    sys.path.insert(0, str(COMMON_ROOT))

from im_hk_mock_api_common.steps import dispatch, step  # noqa: E402,F401
from mock_im_api.client import MockIMClient  # noqa: E402


@dataclass
class Context:
    client: MockIMClient = field(default_factory=lambda: MockIMClient("http://127.0.0.1:8768"))
    data: dict[str, Any] = field(default_factory=dict)
    last_response: Any = None

__all__ = ["Context", "dispatch", "step"]
