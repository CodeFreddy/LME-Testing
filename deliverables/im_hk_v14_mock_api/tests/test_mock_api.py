from __future__ import annotations

import os
import sys
import threading
import time
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

from mock_im_api.client import MockIMClient
from mock_im_api.server import MockIMHandler


class MockInitialMarginHKv14APITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        cls.server = ThreadingHTTPServer(("127.0.0.1", 8768), MockIMHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.client = MockIMClient("http://127.0.0.1:8768")
        for _ in range(30):
            try:
                if cls.client.get("/health").ok:
                    return
            except Exception:
                time.sleep(0.1)
        raise RuntimeError("mock API server did not start")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def test_health_and_rules_are_hkv14_labeled(self) -> None:
        health = self.client.get("/health")
        self.assertTrue(health.ok)
        self.assertEqual(health.body["service"], "mock-im-hk-v14-api")

        rules = self.client.get("/rules")
        self.assertEqual(rules.status_code, 200)
        rule_ids = {rule["rule_id"] for rule in rules.body["rules"]}
        self.assertIn("IM-HK14-FLAT-RATE", rule_ids)

    def test_flat_rate_margin_hkv14_poc_example(self) -> None:
        result = self.client.post(
            "/margin/flat-rate",
            {
                "positions": [
                    {"instrument_id": "658", "quantity": -10000000, "market_value": -60000000, "flat_rate_subcategory": "1"},
                    {"instrument_id": "3606", "quantity": 1000000, "market_value": 30000000, "flat_rate_subcategory": "1"},
                    {"instrument_id": "3456", "quantity": 10000, "market_value": 750000, "flat_rate_subcategory": "2"},
                    {"instrument_id": "3457", "quantity": -50000, "market_value": -300000, "flat_rate_subcategory": "3"},
                ],
                "flat_rates": {"3456": 0.30, "3457": 0.55, "658": 0.12, "3606": 0.12},
                "flat_rate_margin_multiplier": 2,
            },
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.body["pre_multiplier_margin"], 7590000)
        self.assertEqual(result.body["flat_rate_margin"], 15180000)

    def test_bdd_runner(self) -> None:
        old_cwd = Path.cwd()
        old_argv = sys.argv[:]
        try:
            os.chdir(self.root)
            sys.argv = ["run_bdd.py"]
            sys.path.insert(0, str(self.root))
            import run_bdd

            self.assertEqual(run_bdd.main(), 0)
        finally:
            os.chdir(old_cwd)
            sys.argv = old_argv


if __name__ == "__main__":
    unittest.main()
