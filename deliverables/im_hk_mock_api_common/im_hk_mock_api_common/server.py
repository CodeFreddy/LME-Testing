"""Reusable HTTP server factory for Initial Margin mock APIs."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable

from . import domain


Route = Callable[[dict[str, Any]], dict[str, Any]]


POST_ROUTES: dict[str, Route] = {
    "/rpf/validate": domain.validate_rpf,
    "/positions/normalize": domain.normalize_positions,
    "/margin/market-risk-components": domain.calculate_market_risk_components,
    "/margin/flat-rate": domain.calculate_flat_rate_margin,
    "/margin/mtm": domain.calculate_mtm,
    "/margin/aggregate": domain.aggregate_margin,
    "/corporate-actions/adjust": domain.adjust_corporate_actions,
    "/positions/cross-day-net": domain.cross_day_net,
    "/mtm/cross-currency-net": domain.cross_currency_net,
    "/mtm/intraday": domain.intraday_mtm,
}


def make_handler(*, service_name: str, server_version: str, rule_catalog: list[dict[str, str]]):
    service = service_name
    version = server_version
    catalog = rule_catalog

    class MockIMHandler(BaseHTTPRequestHandler):
        server_version = version

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
                self._json_response(200, {"ok": True, "service": service})
                return
            if self.path == "/rules":
                self._json_response(200, {"rules": catalog})
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
            except Exception as exc:
                self._json_response(500, {"ok": False, "reason": "server_error", "detail": str(exc)})

        def log_message(self, fmt: str, *args: Any) -> None:
            print(f"[{service}] {self.address_string()} - {fmt % args}")

    return MockIMHandler


def run_handler(handler: type[BaseHTTPRequestHandler], label: str, host: str = "127.0.0.1", port: int = 8767) -> None:
    httpd = ThreadingHTTPServer((host, port), handler)
    print(f"{label} listening on http://{host}:{port}")
    print("Try: GET /health, GET /rules")
    httpd.serve_forever()
