from __future__ import annotations

import os
import shutil
import unittest
from pathlib import Path

from lme_testing.config import ConfigError, load_project_config


WORK_TMP = Path('.tmp_test')


class ConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        WORK_TMP.mkdir(exist_ok=True)

    def tearDown(self) -> None:
        if WORK_TMP.exists():
            shutil.rmtree(WORK_TMP)

    def test_load_config_with_env_keys(self) -> None:
        os.environ["MAKER_API_KEY"] = "maker-secret"
        os.environ["CHECKER_API_KEY"] = "checker-secret"
        config_path = WORK_TMP / "config.json"
        config_path.write_text(
            """
            {
              "providers": {
                "maker": {
                  "type": "openai_compatible",
                  "base_url": "https://maker.example/v1",
                  "model": "m",
                  "api_key_env": "MAKER_API_KEY"
                },
                "checker": {
                  "type": "openai_compatible",
                  "base_url": "https://checker.example/v1",
                  "model": "c",
                  "api_key_env": "CHECKER_API_KEY"
                }
              },
              "roles": {
                "maker": "maker",
                "checker": "checker"
              }
            }
            """,
            encoding="utf-8",
        )
        config = load_project_config(config_path)
        self.assertEqual(config.provider_for_role("maker").api_key, "maker-secret")
        self.assertEqual(config.provider_for_role("checker").api_key, "checker-secret")

    def test_missing_key_raises(self) -> None:
        config_path = WORK_TMP / "config.json"
        config_path.write_text(
            """
            {
              "providers": {
                "maker": {
                  "type": "openai_compatible",
                  "base_url": "https://maker.example/v1",
                  "model": "m"
                },
                "checker": {
                  "type": "openai_compatible",
                  "base_url": "https://checker.example/v1",
                  "model": "c",
                  "api_key": "secret"
                }
              },
              "roles": {
                "maker": "maker",
                "checker": "checker"
              }
            }
            """,
            encoding="utf-8",
        )
        with self.assertRaises(ConfigError):
            load_project_config(config_path)


if __name__ == "__main__":
    unittest.main()
