"""HTTP server for the standalone LME Matching Rules mock API."""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable

from . import domain
from .rules import RULE_CATALOG


Route = Callable[[dict[str, Any]], dict[str, Any]]


POST_ROUTES: dict[str, Route] = {
    "/terminology/validate": domain.validate_terminology,
    "/trades/validate-price": domain.validate_price,
    "/trades/contact-exchange": domain.contact_exchange,
    "/failed-checks/resubmission": domain.validate_resubmission,
    "/deadlines/validate": domain.validate_deadline,
    "/trades/submit": domain.submit_trade,
    "/audit/validate": domain.validate_audit,
    "/giveups/submit": domain.submit_giveup,
    "/otc-bring-ons/validate": domain.validate_otc_bring_on,
    "/auctions/bids": domain.submit_auction_bid,
    "/ptt/validate": domain.validate_ptt,
}


class MockLMEHandler(BaseHTTPRequestHandler):
    server_version = "MockLME/1.0"

    def _json_response(self, status: int, payload: dict[str, Any] | list[Any]) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if self.path == "/health":
            self._json_response(200, {"ok": True, "service": "mock-lme-api"})
            return
        if self.path == "/rules":
            self._json_response(200, {"rules": RULE_CATALOG})
            return
        self._json_response(404, {"ok": False, "reason": "not_found", "path": self.path})

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        route = POST_ROUTES.get(self.path)
        if not route:
            self._json_response(404, {"ok": False, "reason": "not_found", "path": self.path})
            return
        try:
            payload = self._read_json()
            result = route(payload)
            status = 200 if result.get("ok") else 422
            self._json_response(status, result)
        except Exception as exc:  # Keep mock failures visible to test scripts.
            self._json_response(500, {"ok": False, "reason": "server_error", "detail": str(exc)})

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[mock-lme-api] {self.address_string()} - {fmt % args}")


def run(host: str = "127.0.0.1", port: int = 8766) -> None:
    httpd = ThreadingHTTPServer((host, port), MockLMEHandler)
    print(f"Mock LME API listening on http://{host}:{port}")
    print("Try: GET /health, GET /rules")
    httpd.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the LME Matching Rules mock API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    run(args.host, args.port)


if __name__ == "__main__":
    main()

