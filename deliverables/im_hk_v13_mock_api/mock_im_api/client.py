"""Small HTTP client used by executable Initial Margin BDD steps."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen


@dataclass
class APIResult:
    status_code: int
    body: dict[str, Any]

    @property
    def ok(self) -> bool:
        return bool(self.body.get("ok"))

    @property
    def status(self) -> str:
        return str(self.body.get("status", ""))

    @property
    def reason(self) -> str | None:
        value = self.body.get("reason")
        return str(value) if value is not None else None


class MockIMClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or os.environ.get("MOCK_IM_API_URL") or "http://127.0.0.1:8767").rstrip("/")

    def get(self, path: str) -> APIResult:
        return self._request("GET", path)

    def post(self, path: str, payload: dict[str, Any]) -> APIResult:
        return self._request("POST", path, payload)

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> APIResult:
        data = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(self.base_url + path, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=10) as response:
                body = json.loads(response.read().decode("utf-8"))
                return APIResult(response.status, body)
        except HTTPError as exc:
            body = json.loads(exc.read().decode("utf-8"))
            exc.close()
            return APIResult(exc.code, body)
