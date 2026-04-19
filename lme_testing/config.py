from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from string import Template
from typing import Any


class ConfigError(ValueError):
    """项目配置无效时抛出。"""


@dataclass(slots=True)
class RoleDefaults:
    # 角色级默认参数，后续可以用于动态覆盖 provider 上的通用设置。
    temperature: float = 0.1
    max_output_tokens: int = 4000
    timeout_seconds: int = 90
    max_retries: int = 3
    retry_backoff_seconds: float = 2.0


@dataclass(slots=True)
class ProviderConfig:
    # 对单个模型供应商调用所需的最小配置抽象。
    name: str
    provider_type: str
    model: str
    base_url: str
    api_key: str
    api_format: str = "openai_chat_completions"
    headers: dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 90
    temperature: float = 0.1
    max_output_tokens: int = 4000


@dataclass(slots=True)
class ProjectConfig:
    # 整个项目的模型配置：包括 provider 列表、maker/checker 角色绑定和默认输出目录。
    providers: dict[str, ProviderConfig]
    roles: dict[str, str]
    output_root: Path
    config_dir: Path = Path("config")
    maker_defaults: RoleDefaults = field(default_factory=RoleDefaults)
    checker_defaults: RoleDefaults = field(default_factory=RoleDefaults)

    def provider_for_role(self, role: str) -> ProviderConfig:
        provider_name = self.roles.get(role)
        if not provider_name:
            raise ConfigError(f"Role '{role}' is not configured.")
        provider = self.providers.get(provider_name)
        if not provider:
            raise ConfigError(
                f"Role '{role}' references missing provider '{provider_name}'."
            )
        return provider


# 读取 JSON 配置文件，并允许使用 ${ENV_NAME} 的方式做环境变量替换。
def _read_json(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError as exc:
        raise ConfigError(f"Config file not found: {path}") from exc
    return json.loads(Template(text).safe_substitute(os.environ))


# 兼容两种配置写法：
# 1. api_key_env = 环境变量名
# 2. api_key_env = 真实 key（当前你的配置就是这种写法）
def _resolve_api_key(data: dict[str, Any]) -> str:
    api_key = data.get("api_key")
    api_key_env = data.get("api_key_env")
    if api_key:
        return str(api_key)
    if not api_key_env:
        return ""
    env_value = os.getenv(str(api_key_env), "")
    if env_value:
        return env_value
    # 如果环境变量没有命中，但字段本身就像一个真实 key，则直接当作 key 使用。
    if str(api_key_env).startswith("sk-"):
        return str(api_key_env)
    return ""


# 把原始 provider 配置转成内部统一结构，并做最基本校验。
def _build_provider(name: str, data: dict[str, Any]) -> ProviderConfig:
    provider_type = data.get("type", "openai_compatible")
    api_key = _resolve_api_key(data)
    if not api_key:
        raise ConfigError(
            f"Provider '{name}' is missing api_key or unresolved api_key_env."
        )

    required = ["model", "base_url"]
    missing = [field_name for field_name in required if not data.get(field_name)]
    if missing:
        raise ConfigError(
            f"Provider '{name}' is missing required fields: {', '.join(missing)}"
        )

    return ProviderConfig(
        name=name,
        provider_type=provider_type,
        model=data["model"],
        base_url=data["base_url"].rstrip("/"),
        api_key=api_key,
        api_format=data.get("api_format", "openai_chat_completions"),
        headers=dict(data.get("headers", {})),
        timeout_seconds=int(data.get("timeout_seconds", 90)),
        temperature=float(data.get("temperature", 0.1)),
        max_output_tokens=int(data.get("max_output_tokens", 4000)),
    )


# 角色默认参数目前主要保留给后续扩展使用。
def _build_role_defaults(data: dict[str, Any] | None) -> RoleDefaults:
    data = data or {}
    return RoleDefaults(
        temperature=float(data.get("temperature", 0.1)),
        max_output_tokens=int(data.get("max_output_tokens", 4000)),
        timeout_seconds=int(data.get("timeout_seconds", 90)),
        max_retries=int(data.get("max_retries", 3)),
        retry_backoff_seconds=float(data.get("retry_backoff_seconds", 2.0)),
    )


# 加载项目配置的统一入口。
def load_project_config(path: Path) -> ProjectConfig:
    raw = _read_json(path)
    providers_data = raw.get("providers")
    roles = raw.get("roles", {})
    if not providers_data:
        raise ConfigError("Config must define at least one provider.")
    if "maker" not in roles or "checker" not in roles:
        raise ConfigError("Config must define 'maker' and 'checker' role bindings.")

    providers = {
        name: _build_provider(name, provider_data)
        for name, provider_data in providers_data.items()
    }

    output_root = Path(raw.get("output_root", "runs"))
    return ProjectConfig(
        providers=providers,
        roles=roles,
        output_root=output_root,
        config_dir=path.parent,
        maker_defaults=_build_role_defaults(raw.get("maker_defaults")),
        checker_defaults=_build_role_defaults(raw.get("checker_defaults")),
    )
