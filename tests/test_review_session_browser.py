from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import socket
import struct
import subprocess
import threading
import time
import unittest
import urllib.request
from pathlib import Path

from lme_testing.review_session import serve_review_session
import tests.test_review_session as review_session_fixtures


def _find_chromium() -> str | None:
    env_path = os.environ.get("LME_BROWSER_E2E_CHROME")
    if env_path and Path(env_path).is_file():
        return env_path
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "google-chrome",
        "chromium",
        "chromium-browser",
        "msedge",
    ]
    for candidate in candidates:
        resolved = shutil.which(candidate) if "\\" not in candidate else candidate
        if resolved and Path(resolved).is_file():
            return resolved
    return None


class ChromeCdp:
    def __init__(self, chrome_path: str, url: str, work_dir: Path):
        self.chrome_path = chrome_path
        self.url = url
        self.work_dir = work_dir
        self.proc: subprocess.Popen | None = None
        self.sock: socket.socket | None = None
        self.next_id = 1

    def __enter__(self) -> "ChromeCdp":
        user_data_dir = self.work_dir / "chrome-profile"
        user_data_dir.mkdir(parents=True, exist_ok=True)
        self.proc = subprocess.Popen(
            [
                self.chrome_path,
                "--headless=new",
                "--disable-gpu",
                "--disable-background-networking",
                "--disable-default-apps",
                "--no-first-run",
                "--no-default-browser-check",
                "--remote-debugging-port=0",
                f"--user-data-dir={user_data_dir}",
                self.url,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        port = self._read_debug_port(user_data_dir)
        ws_url = self._page_ws_url(port)
        self._connect_ws(ws_url)
        self.call("Page.enable")
        self.call("Runtime.enable")
        self.wait_for("document.readyState === 'complete'")
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.sock:
            self.sock.close()
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()

    def call(self, method: str, params: dict | None = None) -> dict:
        message_id = self.next_id
        self.next_id += 1
        self._send_json({"id": message_id, "method": method, "params": params or {}})
        deadline = time.time() + 10
        while time.time() < deadline:
            message = self._recv_json()
            if message.get("id") == message_id:
                if "error" in message:
                    raise AssertionError(f"CDP {method} failed: {message['error']}")
                return message.get("result", {})
        raise TimeoutError(f"Timed out waiting for CDP response to {method}")

    def eval(self, expression: str):
        result = self.call(
            "Runtime.evaluate",
            {
                "expression": expression,
                "awaitPromise": True,
                "returnByValue": True,
            },
        )
        if "exceptionDetails" in result:
            raise AssertionError(result["exceptionDetails"])
        return result.get("result", {}).get("value")

    def wait_for(self, expression: str, timeout: float = 5.0):
        deadline = time.time() + timeout
        last_value = None
        while time.time() < deadline:
            last_value = self.eval(expression)
            if last_value:
                return last_value
            time.sleep(0.1)
        raise TimeoutError(f"Timed out waiting for browser expression: {expression}; last={last_value!r}")

    def _read_debug_port(self, user_data_dir: Path) -> int:
        active_port = user_data_dir / "DevToolsActivePort"
        deadline = time.time() + 10
        while time.time() < deadline:
            if active_port.exists():
                lines = active_port.read_text(encoding="utf-8").splitlines()
                if lines:
                    return int(lines[0])
            if self.proc and self.proc.poll() is not None:
                raise RuntimeError("Chrome exited before DevTools became available")
            time.sleep(0.1)
        raise TimeoutError("Timed out waiting for Chrome DevTools port")

    def _page_ws_url(self, port: int) -> str:
        deadline = time.time() + 10
        last_payload = []
        while time.time() < deadline:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=2) as response:
                last_payload = json.loads(response.read().decode("utf-8"))
            for item in last_payload:
                if item.get("type") == "page" and item.get("webSocketDebuggerUrl"):
                    return item["webSocketDebuggerUrl"]
            time.sleep(0.1)
        raise TimeoutError(f"No page DevTools target found: {last_payload!r}")

    def _connect_ws(self, ws_url: str) -> None:
        if not ws_url.startswith("ws://"):
            raise ValueError(ws_url)
        host_port_path = ws_url[len("ws://"):]
        host_port, path = host_port_path.split("/", 1)
        host, port_text = host_port.rsplit(":", 1)
        sock = socket.create_connection((host, int(port_text)), timeout=5)
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (
            f"GET /{path} HTTP/1.1\r\n"
            f"Host: {host_port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        sock.sendall(request.encode("ascii"))
        response = sock.recv(4096)
        if b" 101 " not in response:
            raise RuntimeError(f"WebSocket handshake failed: {response!r}")
        accept = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")).digest())
        if accept not in response:
            raise RuntimeError("WebSocket handshake accept key mismatch")
        self.sock = sock

    def _send_json(self, payload: dict) -> None:
        data = json.dumps(payload).encode("utf-8")
        header = bytearray([0x81])
        if len(data) < 126:
            header.append(0x80 | len(data))
        elif len(data) < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", len(data)))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", len(data)))
        mask = os.urandom(4)
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(data))
        assert self.sock is not None
        self.sock.sendall(bytes(header) + mask + masked)

    def _recv_json(self) -> dict:
        while True:
            payload = self._recv_frame()
            if payload is not None:
                return json.loads(payload.decode("utf-8"))

    def _recv_frame(self) -> bytes | None:
        assert self.sock is not None
        first_two = self._recv_exact(2)
        first, second = first_two
        opcode = first & 0x0F
        masked = bool(second & 0x80)
        length = second & 0x7F
        if length == 126:
            length = struct.unpack("!H", self._recv_exact(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", self._recv_exact(8))[0]
        mask = self._recv_exact(4) if masked else b""
        payload = self._recv_exact(length) if length else b""
        if masked:
            payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        if opcode == 0x8:
            raise RuntimeError("WebSocket closed")
        if opcode == 0x9:
            self._send_pong(payload)
            return None
        if opcode != 0x1:
            return None
        return payload

    def _send_pong(self, payload: bytes) -> None:
        assert self.sock is not None
        header = bytearray([0x8A, 0x80 | len(payload)])
        mask = os.urandom(4)
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        self.sock.sendall(bytes(header) + mask + masked)

    def _recv_exact(self, length: int) -> bytes:
        assert self.sock is not None
        chunks = bytearray()
        while len(chunks) < length:
            chunk = self.sock.recv(length - len(chunks))
            if not chunk:
                raise RuntimeError("Socket closed while reading WebSocket frame")
            chunks.extend(chunk)
        return bytes(chunks)


@unittest.skipIf(_find_chromium() is None, "Chrome/Edge not available for browser E2E tests")
class ReviewSessionBrowserE2ETests(unittest.TestCase):
    def setUp(self) -> None:
        self.work_tmp = review_session_fixtures.WORK_TMP
        if self.work_tmp.exists():
            shutil.rmtree(self.work_tmp)
        self.work_tmp.mkdir(exist_ok=True)
        self.browser_tmp = Path(".tmp_browser_e2e").resolve()
        if self.browser_tmp.exists():
            shutil.rmtree(self.browser_tmp)
        self.browser_tmp.mkdir(parents=True)

    def tearDown(self) -> None:
        if self.work_tmp.exists():
            shutil.rmtree(self.work_tmp)
        if self.browser_tmp.exists():
            shutil.rmtree(self.browser_tmp)

    def test_bdd_and_scripts_tabs_save_and_refresh_visible_metrics(self) -> None:
        manager = review_session_fixtures.ReviewSessionTests(methodName="test_finalize_locks_session")._build_manager(include_bdd=True)
        server, url = serve_review_session(manager, "127.0.0.1", 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with ChromeCdp(_find_chromium() or "", url, self.browser_tmp) as browser:
                browser.wait_for("!!document.querySelector('#reviewRows tr')")
                browser.eval("document.querySelector('[data-tab=\"bdd\"]').click()")
                browser.wait_for("!!document.querySelector('#bddContent textarea[data-scenario]')")

                unsaved_text = "unsaved browser BDD edit"
                browser.eval(
                    f"""(() => {{
                      const ta = document.querySelector('#bddContent textarea[data-scenario]');
                      ta.value = {json.dumps(unsaved_text)};
                      ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
                      return ta.value;
                    }})()"""
                )
                browser.eval("document.querySelector('[data-tab=\"review\"]').click()")
                browser.eval("document.querySelector('[data-tab=\"bdd\"]').click()")
                self.assertEqual(
                    browser.eval("document.querySelector('#bddContent textarea[data-scenario]').value"),
                    unsaved_text,
                )

                exact_text = "business is transacted on the Exchange"
                browser.eval(
                    f"""(() => {{
                      const ta = document.querySelector('#bddContent textarea[data-scenario]');
                      ta.value = {json.dumps(exact_text)};
                      ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    }})()"""
                )
                browser.eval("document.getElementById('saveBddBtn').click()")
                browser.wait_for("document.getElementById('bddStatus').textContent.includes('reviewed BDD')")
                browser.wait_for("!document.querySelector('[data-tab=\"scripts\"]').disabled")

                browser.eval("document.querySelector('[data-tab=\"scripts\"]').click()")
                browser.wait_for("document.querySelector('#scriptsContent .scripts-metrics') !== null")
                browser.eval(
                    """(() => {
                      window._e2eMetric = (label) => {
                        const metrics = Array.from(document.querySelectorAll('.scripts-metric'));
                        const item = metrics.find(el => el.innerText.includes(label));
                        return item ? Number(item.querySelector('strong').textContent) : -1;
                      };
                    })()"""
                )
                self.assertEqual(browser.eval("_e2eMetric('Unmatched (Gaps)')"), 0)
                self.assertGreaterEqual(browser.eval("_e2eMetric('Exact Matches')"), 1)

                browser.eval(
                    """(() => {
                      const ta = document.querySelector('#scriptsContent textarea[data-step-type]:not([data-gap-index])');
                      ta.value = 'custom unmatched setup';
                      ta.dispatchEvent(new Event('input', { bubbles: true }));
                    })()"""
                )
                browser.eval("document.getElementById('saveScriptsBtn').click()")
                browser.wait_for("document.getElementById('scriptsStatus').textContent.includes('匹配报告')")
                browser.wait_for("_e2eMetric('Unmatched (Gaps)') === 1")
                self.assertEqual(browser.eval("_e2eMetric('Exact Matches')"), 0)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
