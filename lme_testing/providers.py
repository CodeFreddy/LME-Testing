from __future__ import annotations

import hashlib
import json
import re
import time as _time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass, field
from urllib3.util.retry import Retry

import requests
from requests.adapters import HTTPAdapter

from .config import ProviderConfig


# Transient errors that should trigger retries
_TRANSIENT_ERROR_TYPES = frozenset((
    "ConnectionResetError",
    "ConnectionRefusedError",
    "ConnectionAbortedError",
    "BrokenPipeError",
    "TimeoutError",           # socket timeout
    "SSLError",                # SSL protocol violations
    "SSLSyscallError",         # SSL system call errors
    "SSLEOFError",             # SSL EOF violation
    "IncompleteRead",          # urllib3 internal
    "ProtocolError",           # HTTP protocol errors
    "RequestException",        # requests base class (covers most network errors)
    "ConnectionError",         # requests connection error
    "Timeout",                 # requests timeout
    "HTTPError",               # requests HTTP error (from raise_for_status)
))


def _is_transient_error(exc: Exception) -> bool:
    """Return True if this is a transient error that may succeed on retry."""
    exc_type = type(exc).__name__
    if exc_type in _TRANSIENT_ERROR_TYPES:
        return True
    # Recurse into chained exceptions
    if exc.__cause__ is not None and _is_transient_error(exc.__cause__):
        return True
    if isinstance(exc, requests.RequestException):
        # For requests exceptions, check the response too (5xx, 429, etc.)
        if exc.response is not None:
            return exc.response.status_code in (429, 500, 502, 503, 504)
        return True  # No response means network-level error, retry
    return False


# ---------------------------------------------------------------------------
# HTTP Connection Pool via requests + urllib3.
# Sessions are cached per host and shared across provider instances so that
# connections are reused across batches. This avoids SSL handshake overhead on
# every request and significantly improves reliability with flaky APIs.
# ---------------------------------------------------------------------------


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
        if "checker" in prompt_lower or "coverage_relevance" in prompt_lower:
            return "checker"
        # "maker" prompt contains "evidence-backed BDD" so check it before "bdd"
        if "maker" in prompt_lower or "scenario" in prompt_lower:
            return "maker"
        if "bdd" in prompt_lower or "given_steps" in prompt_lower or "normalized" in prompt_lower:
            return "bdd"
        return "maker"

    def _extract_semantic_rule_ids(self, user_prompt: str) -> list[str]:
        # Extract semantic_rule_id values from the INPUT section of the prompt only.
        # Different pipelines use different section markers:
        # - Planner/Maker/Checker: "Input semantic rules:"
        # - BDD: "Input maker test cases:"
        for marker in ("Input maker test cases:", "Input semantic rules:"):
            marker_pos = user_prompt.rfind(marker)
            if marker_pos != -1:
                input_section = user_prompt[marker_pos + len(marker):]
                break
        else:
            input_section = user_prompt

        ids: list[str] = []
        for match in re.finditer(r'"semantic_rule_id"\s*:\s*"([^"]+)"', input_section):
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
        # Extract required_case_types per semantic_rule_id from the user prompt.
        # The prompt contains: Expected required_case_types map: {...}
        req_ids: dict[str, list[str]] = {}
        case_type_map: dict[str, list[str]] = {}
        for match in re.finditer(r'"semantic_rule_id"\s*:\s*"([^"]+)"', user_prompt):
            sid = match.group(1)
            if sid not in req_ids:
                req_ids[sid] = [f"R-{sid}"]
                case_type_map[sid] = []

        # Try to extract required_case_types from the input section
        for marker in ("Input maker test cases:", "Input semantic rules:"):
            marker_pos = user_prompt.rfind(marker)
            if marker_pos != -1:
                input_section = user_prompt[marker_pos + len(marker):]
                break
        else:
            input_section = user_prompt

        for match in re.finditer(r'"required_case_types"\s*:\s*\[([^\]]*)\]', input_section):
            types_str = match.group(1)
            # Find which rule this belongs to by looking backwards
            before = input_section[:match.start()]
            sid_matches = list(re.finditer(r'"semantic_rule_id"\s*:\s*"([^"]+)"', before))
            if sid_matches:
                sid = sid_matches[-1].group(1)
                types = [t.strip().strip('"') for t in types_str.split(",") if t.strip()]
                case_type_map[sid] = types

        # Default case types if not found
        default_types = ["positive", "negative"]
        results = []
        for sid in rule_ids:
            required = case_type_map.get(sid, default_types)
            if not required:
                required = default_types
            scenarios = []
            for i, ct in enumerate(required):
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
    # Per-class session cache keyed by (host, port). Sessions are shared across
    # provider instances pointing to the same host so that connections are reused.
    _session_cache: dict[tuple[str, int], requests.Session] = {}
    _cache_lock = __import__("threading").Lock()

    def __init__(self, config: ProviderConfig):
        self.config = config
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._interrupted = False

        # Build a requests Session with connection pooling via HTTPAdapter.
        # The session is cached per host so that multiple provider instances
        # (e.g. maker + checker pointing to the same host) share the pool.
        parsed = urllib.parse.urlparse(config.base_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        cache_key = (host, port)

        with self._cache_lock:
            if cache_key not in self._session_cache:
                session = requests.Session()
                # Configure retry strategy via urllib3 beneath requests
                max_retries = Retry(
                    total=0,  # We handle retries ourselves for finer control
                    connect=3,
                    read=3,
                    redirect=3,
                    status_forcelist=(429, 500, 502, 503, 504),
                    allowed_methods=None,
                    raise_on_status=False,
                )
                adapter = HTTPAdapter(
                    max_retries=max_retries,
                    pool_connections=4,
                    pool_maxsize=4,
                )
                session.mount(f"{parsed.scheme}://", adapter)
                self._session_cache[cache_key] = session
            self._session = self._session_cache[cache_key]

    def shutdown(self) -> None:
        """Shut down the executor.

        Called by workflow_session when a KeyboardInterrupt aborts the pipeline,
        preventing Python's atexit from joining live-but-stuck threads and raising
        KeyboardInterrupt inside the atexit handler itself.
        Sessions are shared and intentionally left open for reuse by other providers.
        """
        self._interrupted = True
        self._executor.shutdown(wait=False, cancel_futures=True)

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
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            **self.config.headers,
        }
        url = f"{self.config.base_url}/chat/completions"

        # Use a thread so that Ctrl+C (KeyboardInterrupt / SIGINT) can break the
        # blocking requests call on Windows, where socket I/O is not signal-alertable.
        # The caller (pipelines) catches KeyboardInterrupt and aborts gracefully.
        timeout = getattr(self.config, "timeout_seconds", 300)
        max_retries = getattr(self.config, "max_retries", 3)
        retry_backoff = getattr(self.config, "retry_backoff_seconds", 2.0)

        last_exc: Exception = None

        for attempt in range(1, max_retries + 1):
            def _do_request() -> requests.Response:
                return self._session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=timeout,
                )

            future = self._executor.submit(_do_request)
            try:
                response: requests.Response = future.result(timeout=timeout + 5)
                break  # success
            except FuturesTimeoutError:
                future.cancel()
                last_exc = ProviderError(
                    f"Provider '{self.config.name}' request timed out after {timeout}s "
                    f"(attempt {attempt}/{max_retries})."
                )
                if attempt == max_retries:
                    raise last_exc
            except (KeyboardInterrupt, InterruptedError):
                future.cancel()
                raise KeyboardInterrupt("Request cancelled by user (Ctrl+C)")
            except Exception as exc:
                last_exc = exc
                if _is_transient_error(exc) and attempt < max_retries:
                    _time.sleep(retry_backoff * (2 ** attempt))
                    continue
                raise last_exc

        # Check for HTTP-level errors before parsing JSON
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise ProviderError(
                f"Provider '{self.config.name}' HTTP {response.status_code}: {response.text[:200]}"
            ) from exc

        try:
            raw = response.json()
        except ValueError as exc:
            raise ProviderError(
                f"Provider '{self.config.name}' returned non-JSON response: {response.text[:200]}"
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
