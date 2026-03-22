from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

from .config import ProviderConfig


class ProviderError(RuntimeError):
    """模型供应商调用失败时抛出。"""


@dataclass(slots=True)
class ModelResponse:
    # content：模型正文；raw_response：完整原始响应，便于回溯排错。
    content: str
    raw_response: dict


# 当前先实现 OpenAI-compatible 风格接口，后续如需接 MiniMax/GLM 原生协议，可继续扩展。
class OpenAICompatibleProvider:
    def __init__(self, config: ProviderConfig):
        self.config = config

    # 向兼容 OpenAI Chat Completions 的接口发起调用。
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

        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise ProviderError(
                f"Provider '{self.config.name}' HTTP {exc.code}: {detail}"
            ) from exc
        except urllib.error.URLError as exc:
            raise ProviderError(
                f"Provider '{self.config.name}' network error: {exc.reason}"
            ) from exc

        try:
            content = raw["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(
                f"Provider '{self.config.name}' returned an unexpected payload."
            ) from exc

        # 少数兼容接口会返回 content 数组，这里做一次兼容拼接。
        if isinstance(content, list):
            content = "".join(
                item.get("text", "") if isinstance(item, dict) else str(item)
                for item in content
            )
        if not isinstance(content, str):
            raise ProviderError(
                f"Provider '{self.config.name}' returned non-text content."
            )
        return ModelResponse(content=content, raw_response=raw)


# 根据 provider 配置构建具体适配器。
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
