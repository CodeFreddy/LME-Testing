"""HTTP server for the Initial Margin HKv14 mock API wrapper."""

from __future__ import annotations

import argparse

from . import _bootstrap  # noqa: F401
from .rules import RULE_CATALOG
from im_hk_mock_api_common.server import make_handler, run_handler


MockIMHandler = make_handler(
    service_name="mock-im-hk-v14-api",
    server_version="MockIMHKv14/1.0",
    rule_catalog=RULE_CATALOG,
)


def run(host: str = "127.0.0.1", port: int = 8768) -> None:
    run_handler(MockIMHandler, "Mock Initial Margin HKv14 API", host=host, port=port)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Initial Margin HKv14 mock API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8768)
    args = parser.parse_args()
    run(args.host, args.port)


if __name__ == "__main__":
    main()
