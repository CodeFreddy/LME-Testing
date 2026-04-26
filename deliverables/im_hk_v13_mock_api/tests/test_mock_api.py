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


class MockInitialMarginAPITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = Path(__file__).resolve().parents[1]
        cls.server = ThreadingHTTPServer(("127.0.0.1", 8767), MockIMHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.client = MockIMClient("http://127.0.0.1:8767")
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

    def test_rpf_required_fields(self) -> None:
        accepted = self.client.post(
            "/rpf/validate",
            {
                "risk_parameter_file": {
                    "global_fields": {
                        "Valuation_DT": "01/04/2019",
                        "HVaR_WGT": 0.75,
                        "SVaR_WGT": 0.25,
                        "HVaR_Scen_Count": 1000,
                        "SVaR_Scen_Count": 1018,
                        "HVaR_CL": 0.994,
                        "SVaR_CL": 0.98,
                        "Rounding": 10000,
                    },
                    "records": [{"InstrumentID": "700", "FieldType": 1, "values": [0.01]}],
                }
            },
        )
        self.assertTrue(accepted.ok)
        self.assertEqual(accepted.status, "accepted")

        rejected = self.client.post(
            "/rpf/validate",
            {
                "risk_parameter_file": {
                    "global_fields": {"Valuation_DT": "01/04/2019"},
                    "records": [{"InstrumentID": "700", "FieldType": 1, "values": [0.01]}],
                }
            },
        )
        self.assertFalse(rejected.ok)
        self.assertEqual(rejected.reason, "missing_global_fields")

    def test_margin_rounding(self) -> None:
        result = self.client.post(
            "/margin/aggregate",
            {
                "market_risk_total": 123456,
                "rounding": 10000,
                "favorable_mtm": 3000,
                "margin_credit": 2000,
                "other_components": {"position_limit_add_on": 1000},
            },
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.body["rounded_market_risk"], 130000)
        self.assertEqual(result.body["total_margin_requirement"], 126000)

    def test_flat_rate_margin_hkv13_example(self) -> None:
        result = self.client.post(
            "/margin/flat-rate",
            {
                "positions": [
                    {"instrument_id": "3457", "quantity": -1, "market_value": -1000000, "flat_rate_subcategory": "1"},
                    {"instrument_id": "3456", "quantity": 10000, "market_value": 1300000, "flat_rate_subcategory": "1"},
                    {"instrument_id": "658", "quantity": -10000000, "market_value": -60000000, "flat_rate_subcategory": "2"},
                    {"instrument_id": "3606", "quantity": 1000000, "market_value": 30000000, "flat_rate_subcategory": "2"},
                ],
                "flat_rates": {"3456": 0.30, "3457": 0.30, "658": 0.12, "3606": 0.12},
                "flat_rate_margin_multiplier": 2,
            },
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.body["subcategories"]["1"]["included_side"], "long")
        self.assertEqual(result.body["subcategories"]["2"]["included_side"], "short")
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
