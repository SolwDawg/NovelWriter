"""Minimal OpenRouter adapter for the V0 live-model benchmark.

Secrets are loaded from process environment variables or a local env file and
are never included in exceptions, result objects, or benchmark output.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import threading
import time
import urllib.error
import urllib.request
from email.utils import parsedate_to_datetime
from typing import Any, Iterable, Mapping

from .contracts import Usage


class OpenRouterConfigurationError(ValueError):
    """Raised when the local OpenRouter configuration is incomplete."""


class OpenRouterRequestError(RuntimeError):
    """Raised for a provider/network/API failure without exposing secrets."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        retry_after_seconds: float | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.retry_after_seconds = retry_after_seconds


@dataclass(frozen=True)
class OpenRouterConfig:
    api_key: str
    model: str
    base_url: str = "https://openrouter.ai/api/v1"
    referer: str | None = None
    title: str = "AI Short Story Platform V0"
    api_keys: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        keys = tuple(dict.fromkeys((*self.api_keys, self.api_key)))
        keys = tuple(key.strip() for key in keys if key and key.strip())
        if not keys or any(not key.startswith("sk-or-") for key in keys):
            raise OpenRouterConfigurationError(
                "OPENROUTER_API_KEY must contain one or more OpenRouter keys"
            )
        object.__setattr__(self, "api_keys", keys)
        object.__setattr__(self, "api_key", keys[0])
        if not self.model.strip():
            raise OpenRouterConfigurationError("OPENROUTER_MODEL is required")

    @property
    def key_count(self) -> int:
        return len(self.api_keys)

    @classmethod
    def from_environment(
        cls, env_file: str | Path | None = None
    ) -> "OpenRouterConfig":
        values: dict[str, str] = {}
        if env_file:
            values.update(_read_env_file(Path(env_file)))
        keys = _configured_keys(values)
        model = os.environ.get("OPENROUTER_MODEL") or values.get("OPENROUTER_MODEL")
        base_url = (
            os.environ.get("OPENROUTER_BASE_URL")
            or values.get("OPENROUTER_BASE_URL")
            or "https://openrouter.ai/api/v1"
        )
        referer = os.environ.get("OPENROUTER_HTTP_REFERER") or values.get(
            "OPENROUTER_HTTP_REFERER"
        )
        if not keys:
            raise OpenRouterConfigurationError("OPENROUTER_API_KEY is not configured")
        if not model:
            raise OpenRouterConfigurationError("OPENROUTER_MODEL is not configured")
        return cls(
            api_key=keys[0],
            model=model.strip(),
            base_url=base_url.rstrip("/"),
            referer=referer.strip() if referer else None,
            api_keys=tuple(keys),
        )


@dataclass(frozen=True)
class OpenRouterResponse:
    text: str
    usage: Usage
    request_id: str | None = None


def _read_env_file(path: Path) -> dict[str, str]:
    """Read key=value, key:value, or the project's raw-key + model format.

    Raw key lines are accumulated in ``OPENROUTER_API_KEYS`` so two-key local
    files remain usable without ever being printed.
    """

    if not path.exists():
        raise OpenRouterConfigurationError(f"env file not found: {path}")
    values: dict[str, str] = {}
    raw_keys: list[str] = []
    raw_key_pattern = re.compile(r"(sk-or-[A-Za-z0-9_-]+)")
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*[:=]\s*(.*?)\s*$", line)
        if match:
            name, raw_value = match.groups()
            value = raw_value.strip().strip('"').strip("'")
            if name == "model":
                name = "OPENROUTER_MODEL"
            elif name.lower() in {"base_url", "openrouter_base_url"}:
                name = "OPENROUTER_BASE_URL"
            elif name.lower() in {"api_key", "openrouter_api_key", "key"}:
                name = "OPENROUTER_API_KEY"
            elif name.lower() in {"api_keys", "openrouter_api_keys", "keys"}:
                name = "OPENROUTER_API_KEYS"
            key_values = raw_key_pattern.findall(value)
            if key_values:
                raw_keys.extend(key_values)
            values[name] = value
            continue
        key_values = raw_key_pattern.findall(line)
        if key_values:
            raw_keys.extend(key_values)
        elif "/" in line and ":" in line and "OPENROUTER_MODEL" not in values:
            values["OPENROUTER_MODEL"] = line
    if raw_keys:
        values["OPENROUTER_API_KEYS"] = ",".join(dict.fromkeys(raw_keys))
    return values


def _configured_keys(values: Mapping[str, str]) -> list[str]:
    """Resolve numbered/list keys from environment first, then local file."""

    candidates: list[str] = []
    environment_numbered = sorted(
        (
            name,
            value,
        )
        for name, value in os.environ.items()
        if re.fullmatch(r"OPENROUTER_API_KEY_\d+", name) and value.strip()
    )
    candidates.extend(value for _, value in environment_numbered)
    if os.environ.get("OPENROUTER_API_KEYS"):
        candidates.append(os.environ["OPENROUTER_API_KEYS"])
    if os.environ.get("OPENROUTER_API_KEY"):
        candidates.append(os.environ["OPENROUTER_API_KEY"])
    if not candidates:
        candidates.extend(
            value
            for name, value in values.items()
            if name == "OPENROUTER_API_KEYS" or name == "OPENROUTER_API_KEY"
        )
    keys: list[str] = []
    for candidate in candidates:
        keys.extend(re.findall(r"sk-or-[A-Za-z0-9_-]+", candidate))
    return list(dict.fromkeys(keys))


class OpenRouterProvider:
    """Synchronous chat-completions adapter used by smoke/eval commands."""

    def __init__(
        self,
        config: OpenRouterConfig,
        *,
        timeout_seconds: float = 120.0,
        max_key_attempts: int | None = None,
        cooldown_seconds: float = 30.0,
    ) -> None:
        self.config = config
        self.timeout_seconds = timeout_seconds
        self.max_key_attempts = max_key_attempts or min(2, config.key_count)
        self.max_key_attempts = max(1, min(self.max_key_attempts, config.key_count))
        self.cooldown_seconds = max(1.0, cooldown_seconds)
        self._lock = threading.Lock()
        self._next_key_index = 0
        self._cooldowns: dict[int, float] = {}

    def chat(
        self,
        messages: Iterable[Mapping[str, str]],
        *,
        max_tokens: int = 512,
        temperature: float = 0.2,
        response_format: Mapping[str, Any] | None = None,
    ) -> OpenRouterResponse:
        payload: dict[str, Any] = {
            "model": self.config.model,
            "messages": [dict(message) for message in messages],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if response_format is not None:
            payload["response_format"] = dict(response_format)
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
            "X-Title": self.config.title,
        }
        if self.config.referer:
            headers["HTTP-Referer"] = self.config.referer
        last_error: OpenRouterRequestError | None = None
        for key_slot in self._key_slots_for_request():
            headers["Authorization"] = f"Bearer {self.config.api_keys[key_slot]}"
            try:
                return self._request_once(body, headers, key_slot)
            except OpenRouterRequestError as error:
                last_error = error
                if error.status_code != 429:
                    raise
                self._cooldowns[key_slot] = time.monotonic() + max(
                    self.cooldown_seconds,
                    error.retry_after_seconds or 0.0,
                )
                # Try at most one other configured key. There is no unbounded
                # retry and no sleep-based rate-limit evasion.
        if last_error:
            raise last_error
        raise OpenRouterRequestError("OpenRouter request could not select a key")

    def _key_slots_for_request(self) -> list[int]:
        now = time.monotonic()
        with self._lock:
            start = self._next_key_index % self.config.key_count
            self._next_key_index = (start + 1) % self.config.key_count
            ordered = [
                (start + offset) % self.config.key_count
                for offset in range(self.config.key_count)
            ]
            available = [
                slot for slot in ordered if self._cooldowns.get(slot, 0.0) <= now
            ]
            selected = available or ordered
            return selected[: self.max_key_attempts]

    def _request_once(
        self, body: bytes, headers: Mapping[str, str], key_slot: int
    ) -> OpenRouterResponse:
        request = urllib.request.Request(
            f"{self.config.base_url}/chat/completions",
            data=body,
            headers=dict(headers),
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                response_body = response.read()
                request_id = response.headers.get("x-request-id")
        except urllib.error.HTTPError as error:
            # Do not include response bodies: provider errors can echo request
            # content and would violate the no-raw-story-logging rule.
            raise OpenRouterRequestError(
                f"OpenRouter HTTP {error.code}",
                status_code=error.code,
                retry_after_seconds=_retry_after_seconds(error.headers.get("Retry-After")),
            ) from None
        except urllib.error.URLError as error:
            raise OpenRouterRequestError(f"OpenRouter network error: {error.reason}") from None
        except TimeoutError:
            raise OpenRouterRequestError("OpenRouter request timed out") from None

        try:
            data = json.loads(response_body.decode("utf-8"))
            text = _extract_text(data)
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, IndexError) as error:
            raise OpenRouterRequestError("OpenRouter returned an invalid response") from error
        usage_data = data.get("usage") or {}
        provider_cost = usage_data.get("cost", usage_data.get("total_cost", 0.0)) or 0.0
        usage = Usage(
            input_tokens=int(usage_data.get("prompt_tokens", 0) or 0),
            output_tokens=int(usage_data.get("completion_tokens", 0) or 0),
            estimated_cost_usd=float(provider_cost),
        )
        return OpenRouterResponse(text=text, usage=usage, request_id=request_id)


def _retry_after_seconds(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        try:
            return max(0.0, (parsedate_to_datetime(value).timestamp() - time.time()))
        except (TypeError, ValueError, OverflowError):
            return None


def _extract_text(data: Mapping[str, Any]) -> str:
    choices = data["choices"]
    message = choices[0]["message"]
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [item.get("text", "") for item in content if isinstance(item, Mapping)]
        return "".join(parts)
    raise TypeError("unsupported OpenRouter content shape")
