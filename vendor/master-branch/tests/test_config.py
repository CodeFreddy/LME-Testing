from __future__ import annotations

import os
import shutil
import unittest
from unittest.mock import patch
from pathlib import Path

from lme_testing.config import ConfigError, ProviderConfig, load_project_config
from lme_testing.providers import OpenAICompatibleProvider


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

    def test_provider_retries_remote_disconnect(self) -> None:
        provider = OpenAICompatibleProvider(
            ProviderConfig(
                name="demo",
                provider_type="openai_compatible",
                model="demo-model",
                base_url="https://example.com/v1",
                api_key="secret",
                max_retries=2,
                retry_backoff_seconds=0.0,
            )
        )

        class _Response:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self) -> bytes:
                return b'{"choices":[{"message":{"content":"ok"}}]}'

        calls = {"count": 0}

        def fake_urlopen(request, timeout=None):
            calls["count"] += 1
            if calls["count"] == 1:
                import http.client
                raise http.client.RemoteDisconnected("Remote end closed connection without response")
            return _Response()

        with patch('urllib.request.urlopen', side_effect=fake_urlopen):
            response = provider.generate('system', 'user')

        self.assertEqual(calls["count"], 2)
        self.assertIn('ok', response.content)


if __name__ == "__main__":
    unittest.main()
