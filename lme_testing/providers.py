from __future__ import annotations

import http.client
import json
import logging
import socket
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

from .config import ProviderConfig


class ProviderError(RuntimeError):
    """?????????????"""


@dataclass(slots=True)
class ModelResponse:
    # content??????raw_response???????????????
    content: str
    raw_response: dict


# ????? OpenAI-compatible ?????????? MiniMax/GLM ???????????
class OpenAICompatibleProvider:
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{config.name}")

    # ??? OpenAI Chat Completions ????????
    def generate(self, system_prompt: str, user_prompt: str) -> ModelResponse:
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_output_tokens,
            "response_format": {"type": "json_object"},
        }
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            **self.config.headers,
        }
        url = f"{self.config.base_url}/chat/completions"
        request = urllib.request.Request(url=url, data=body, headers=headers, method="POST")

        max_attempts = max(1, self.config.max_retries + 1)
        raw: dict | None = None
        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            try:
                self.logger.info(
                    "Calling provider=%s model=%s attempt=%s/%s",
                    self.config.name,
                    self.config.model,
                    attempt,
                    max_attempts,
                )
                with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                    raw = json.loads(response.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="ignore")
                last_error = exc
                retryable = exc.code in {408, 409, 425, 429, 500, 502, 503, 504}
                self.logger.warning(
                    "Provider %s HTTP error attempt=%s/%s status=%s retryable=%s detail=%s",
                    self.config.name,
                    attempt,
                    max_attempts,
                    exc.code,
                    retryable,
                    detail,
                )
                if not retryable or attempt >= max_attempts:
                    raise ProviderError(f"Provider '{self.config.name}' HTTP {exc.code}: {detail}") from exc
            except (urllib.error.URLError, http.client.RemoteDisconnected, ConnectionResetError, TimeoutError, socket.timeout) as exc:
                last_error = exc
                reason = getattr(exc, 'reason', str(exc))
                self.logger.warning(
                    "Provider %s network error attempt=%s/%s reason=%s",
                    self.config.name,
                    attempt,
                    max_attempts,
                    reason,
                )
                if attempt >= max_attempts:
                    raise ProviderError(f"Provider '{self.config.name}' network error: {reason}") from exc

            sleep_seconds = self.config.retry_backoff_seconds * attempt
            self.logger.info("Retrying provider %s after %.1f seconds", self.config.name, sleep_seconds)
            time.sleep(sleep_seconds)

        if raw is None:  # pragma: no cover
            raise ProviderError(f"Provider '{self.config.name}' failed after retries: {last_error}")

        try:
            content = raw["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(
                f"Provider '{self.config.name}' returned an unexpected payload."
            ) from exc

        # ????????? content ?????????????
        if isinstance(content, list):
            content = "".join(
                item.get("text", "") if isinstance(item, dict) else str(item)
                for item in content
            )
        if not isinstance(content, str):
            raise ProviderError(
                f"Provider '{self.config.name}' returned non-text content."
            )
        self.logger.info("Provider %s call succeeded", self.config.name)
        return ModelResponse(content=content, raw_response=raw)


# ?? provider ??????????
def build_provider(config: ProviderConfig) -> OpenAICompatibleProvider:
    if config.provider_type != "openai_compatible":
        raise ProviderError(
            f"Unsupported provider type '{config.provider_type}' for '{config.name}'."
        )
    if config.api_format != "openai_chat_completions":
        raise ProviderError(
            f"Unsupported api_format '{config.api_format}' for '{config.name}'."
        )
    return OpenAICompatibleProvider(config)
