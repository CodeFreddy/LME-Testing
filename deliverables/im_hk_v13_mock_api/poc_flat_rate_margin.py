"""Run the HKv13 section 3.2.4.2 Flat Rate Margin POC over HTTP."""

from __future__ import annotations

import json
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

from mock_im_api.client import MockIMClient
from mock_im_api.server import MockIMHandler


def main() -> int:
    root = Path(__file__).resolve().parent
    data = json.loads((root / "data" / "flat_rate_margin_poc.json").read_text(encoding="utf-8"))
    server = ThreadingHTTPServer(("127.0.0.1", 8767), MockIMHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        client = MockIMClient("http://127.0.0.1:8767")
        result = client.post("/margin/flat-rate", data["request"])
        expected = data["expected_response"]
        assert result.ok, result.body
        assert result.body["status"] == expected["status"], result.body
        assert result.body["pre_multiplier_margin"] == expected["pre_multiplier_margin"], result.body
        assert result.body["flat_rate_margin"] == expected["flat_rate_margin"], result.body
        print("Flat Rate Margin POC passed")
        print(json.dumps(result.body, indent=2))
        return 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())

