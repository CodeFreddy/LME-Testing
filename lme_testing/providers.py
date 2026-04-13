from __future__ import annotations

import hashlib
import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from .config import ProviderConfig


class ProviderError(RuntimeError):
    """模型供应商调用失败时抛出。"""


@dataclass(slots=True)
class ModelResponse:
    # content：模型正文；raw_response：完整原始响应，便于回溯排错。
    content: str
    raw_response: dict


# ---------------------------------------------------------------------------
# Stub provider — returns deterministic, schema-valid JSON for CI smoke testing.
# Activated by setting provider_type="stub" in the config or by using the
# STUB_API_KEY sentinel value.
# ---------------------------------------------------------------------------


@dataclass
class StubProvider:
    """Deterministic stub that produces valid JSON for all pipeline stages.

    The stub extracts semantic rule IDs from the user prompt and generates
    one output record per ID, ensuring consistent and valid responses for
    smoke/CI runs without real LLM API calls.
    """

    config: ProviderConfig
    _role_hints: dict[str, bool] = field(default_factory=dict)

    def generate(self, system_prompt: str, user_prompt: str) -> ModelResponse:
        # Detect which pipeline stage this is from the system prompt.
        role = self._detect_role(system_prompt)
        semantic_rule_ids = self._extract_semantic_rule_ids(user_prompt)

        if role == "planner":
            payload = self._stub_planner_response(semantic_rule_ids)
        elif role == "bdd":
            payload = self._stub_bdd_response(semantic_rule_ids)
        elif role == "maker":
            payload = self._stub_maker_response(semantic_rule_ids, user_prompt)
        elif role == "checker":
            payload = self._stub_checker_response(semantic_rule_ids, user_prompt)
        else:
            payload = self._stub_maker_response(semantic_rule_ids, user_prompt)

        raw = {"stub": True, "role": role, "semantic_rule_ids": semantic_rule_ids}
        return ModelResponse(content=json.dumps(payload, ensure_ascii=False), raw_response=raw)

    def _detect_role(self, system_prompt: str) -> str:
        prompt_lower = system_prompt.lower()
        if "planner" in prompt_lower or "test_objective" in prompt_lower:
            return "planner"
        if "bdd" in prompt_lower or "given_steps" in prompt_lower or "normalized" in prompt_lower:
            return "bdd"
        if "checker" in prompt_lower or "coverage_relevance" in prompt_lower:
            return "checker"
        if "maker" in prompt_lower or "scenario" in prompt_lower:
            return "maker"
        return "maker"

    def _extract_semantic_rule_ids(self, user_prompt: str) -> list[str]:
        # Extract semantic_rule_id values from the prompt JSON.
        ids: list[str] = []
        for match in re.finditer(r'"semantic_rule_id"\s*:\s*"([^"]+)"', user_prompt):
            sid = match.group(1)
            if sid not in ids:
                ids.append(sid)
        return ids

    def _rule_hash(self, rule_id: str) -> str:
        h = hashlib.sha256(rule_id.encode()).hexdigest()
        return h

    def _pick(self, rule_id: str, options: list[str], seed_field: str = "") -> str:
        # Deterministically pick one option based on rule_id hash.
        h = int(self._rule_hash(rule_id + seed_field), 16)
        return options[h % len(options)]

    def _stub_planner_response(self, rule_ids: list[str]) -> dict:
        risk_levels = ["high", "medium", "low"]
        priorities = ["high", "medium", "low"]
        families = [
            "access_control",
            "data_validation",
            "session_management",
            "workflow_sequence",
            "permission_boundary",
            "state_transition",
            "deadline_validation",
        ]
        strategies = ["smoke", "regression", "boundary", "negative", "happy_path"]

        return {
            "results": [
                {
                    "semantic_rule_id": sid,
                    "test_objective": f"Validate {sid} behavior against specified requirements.",
                    "risk_level": self._pick(sid, risk_levels, "risk"),
                    "coverage_intent": f"Cover primary and edge cases for {sid}.",
                    "scenario_family": self._pick(sid, families, "family"),
                    "dependency_notes": [],
                    "recommended_validation_strategy": self._pick(sid, strategies, "strategy"),
                    "priority": self._pick(sid, priorities, "priority"),
                    "paragraph_ids": [f"p-{sid}"],
                    "atomic_rule_ids": [f"a-{sid}"],
                    "rule_type": "obligation",
                }
                for sid in rule_ids
            ]
        }

    def _stub_maker_response(self, rule_ids: list[str], user_prompt: str) -> dict:
        # Try to extract requirement_ids and case types from the prompt.
        req_ids: dict[str, list[str]] = {}
        for match in re.finditer(r'"semantic_rule_id"\s*:\s*"([^"]+)"', user_prompt):
            sid = match.group(1)
            if sid not in req_ids:
                req_ids[sid] = [f"R-{sid}"]

        case_types = ["positive", "negative", "boundary", "exception"]
        results = []
        for sid in rule_ids:
            scenarios = []
            for i, ct in enumerate(case_types[:2]):  # 2 scenarios per rule
                tc_id = f"TC-{sid}-{i+1}"
                scenarios.append(
                    {
                        "scenario_id": tc_id,
                        "title": f"{ct.title()} case for {sid}",
                        "intent": f"Validate {ct} behavior",
                        "priority": "high" if ct == "positive" else "medium",
                        "case_type": ct,
                        "given": [f"Given the system is in a valid state for {sid}"],
                        "when": [f"When action is taken for {sid}"],
                        "then": [f"Then outcome is as expected for {sid}"],
                        "assumptions": [],
                        "evidence": [
                            {"atomic_rule_id": f"R-{sid}", "quote": f"Evidence for {sid}."}
                        ],
                    }
                )
            results.append(
                {
                    "semantic_rule_id": sid,
                    "requirement_ids": req_ids.get(sid, [f"R-{sid}"]),
                    "feature": f"Feature: {sid}",
                    "scenarios": scenarios,
                }
            )
        return {"results": results}

    def _stub_checker_response(self, rule_ids: list[str], user_prompt: str) -> dict:
        # Extract case_ids and semantic_rule_id mappings from the prompt.
        case_map: dict[str, str] = {}  # case_id -> semantic_rule_id
        for match in re.finditer(r'"scenario_id"\s*:\s*"([^"]+)"', user_prompt):
            case_id = match.group(1)
            for sid in rule_ids:
                if sid in case_id:
                    case_map[case_id] = sid
                    break
            if case_id not in case_map:
                case_map[case_id] = rule_ids[0] if rule_ids else "SR-UNKNOWN"

        results = []
        for case_id, sid in case_map.items():
            results.append(
                {
                    "case_id": case_id,
                    "semantic_rule_id": sid,
                    "overall_status": "pass",
                    "scores": {
                        "evidence_consistency": 5,
                        "requirement_coverage": 4,
                        "test_design_quality": 4,
                        "non_hallucination": 5,
                    },
                    "case_type": "positive",
                    "case_type_accepted": True,
                    "coverage_relevance": "direct",
                    "blocking_findings_count": 0,
                    "is_blocking": False,
                    "findings": [],
                    "coverage_assessment": {
                        "status": "covered",
                        "reason": "Stub evaluation — structure valid",
                        "missing_aspects": [],
                    },
                }
            )
        return {"results": results}

    def _stub_bdd_response(self, rule_ids: list[str]) -> dict:
        families = [
            "access_control",
            "data_validation",
            "session_management",
            "workflow_sequence",
            "permission_boundary",
            "state_transition",
        ]
        case_types = ["positive", "negative"]

        return {
            "results": [
                {
                    "semantic_rule_id": sid,
                    "feature_title": f"Feature {sid}",
                    "feature_description": f"Validates behavior described in {sid}.",
                    "scenarios": [
                        {
                            "scenario_id": f"TC-{sid}-{i+1}",
                            "title": f"{ct.title()} scenario",
                            "case_type": ct,
                            "priority": "high" if ct == "positive" else "medium",
                            "given_steps": [
                                {
                                    "step_text": f"Given the system is ready for {sid}",
                                    "step_pattern": f"Given the system is ready for {sid}",
                                }
                            ],
                            "when_steps": [
                                {
                                    "step_text": f"When I perform action for {sid}",
                                    "step_pattern": f"When I perform action for {sid}",
                                }
                            ],
                            "then_steps": [
                                {
                                    "step_text": f"Then result is as expected for {sid}",
                                    "step_pattern": f"Then result is as expected for {sid}",
                                }
                            ],
                            "assumptions": [],
                            "paragraph_ids": [f"p-{sid}"],
                            "semantic_rule_ref": sid,
                            "required_case_types": [ct],
                        }
                        for i, ct in enumerate(case_types)
                    ],
                    "paragraph_ids": [f"p-{sid}"],
                    "metadata": {
                        "planner_run_id": "",
                        "maker_run_id": "",
                        "paragraph_ids": [f"p-{sid}"],
                    },
                    "scenario_family": self._pick(sid, families, "family"),
                    "risk_level": "medium",
                    "test_objective": f"Validate {sid}",
                }
                for sid in rule_ids
            ]
        }


# ---------------------------------------------------------------------------
# OpenAI-compatible provider
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Provider factory
# ---------------------------------------------------------------------------

STUB_API_KEY = "stub"


def build_provider(config: ProviderConfig) -> OpenAICompatibleProvider | StubProvider:
    if config.provider_type == "stub":
        return StubProvider(config)
    if config.provider_type != "openai_compatible":
        raise ProviderError(
            f"Unsupported provider type '{config.provider_type}' for '{config.name}'."
        )
    if config.api_key == STUB_API_KEY:
        return StubProvider(config)
    if config.api_format != "openai_chat_completions":
        raise ProviderError(
            f"Unsupported api_format '{config.api_format}' for '{config.name}'."
        )
    return OpenAICompatibleProvider(config)
