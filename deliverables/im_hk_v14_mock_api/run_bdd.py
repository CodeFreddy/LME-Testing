"""Minimal Gherkin runner for the included Initial Margin HKv14 feature files."""

from __future__ import annotations

import sys
from pathlib import Path


COMMON_ROOT = Path(__file__).resolve().parent.parent / "im_hk_mock_api_common"
if str(COMMON_ROOT) not in sys.path:
    sys.path.insert(0, str(COMMON_ROOT))

from features.step_definitions.initial_margin_steps import Context, dispatch  # noqa: E402
from im_hk_mock_api_common.runner import main as run_main  # noqa: E402


def main() -> int:
    return run_main(
        description="Run Initial Margin HKv14 BDD feature files",
        default_feature_dir=str(Path("features") / "initial_margin"),
        context_factory=Context,
        dispatch=dispatch,
    )


if __name__ == "__main__":
    sys.exit(main())
