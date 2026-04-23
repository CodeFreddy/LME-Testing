from __future__ import annotations

import subprocess
import sys
import time
import unittest
from pathlib import Path

from mock_lme_api.client import MockLMEClient


class MockAPITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        cls.proc = subprocess.Popen(
            [sys.executable, "-m", "mock_lme_api.server", "--port", "8766"],
            cwd=cls.root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        cls.client = MockLMEClient("http://127.0.0.1:8766")
        for _ in range(30):
            try:
                if cls.client.get("/health").ok:
                    return
            except Exception:
                time.sleep(0.1)
        raise RuntimeError("mock API server did not start")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.proc.terminate()
        cls.proc.wait(timeout=5)

    def test_deadline_boundary(self) -> None:
        ok = self.client.post(
            "/deadlines/validate",
            {
                "deadline_at": "2026-04-23T20:00:00+00:00",
                "submitted_at": "2026-04-23T19:45:00+00:00",
            },
        )
        self.assertTrue(ok.ok)
        self.assertEqual(ok.status, "accepted")

        late = self.client.post(
            "/deadlines/validate",
            {
                "deadline_at": "2026-04-23T20:00:00+00:00",
                "submitted_at": "2026-04-23T19:46:00+00:00",
            },
        )
        self.assertFalse(late.ok)
        self.assertEqual(late.reason, "late_submission")

    def test_bdd_runner(self) -> None:
        result = subprocess.run(
            [sys.executable, "run_bdd.py"],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("0 failed", result.stdout)


if __name__ == "__main__":
    unittest.main()

