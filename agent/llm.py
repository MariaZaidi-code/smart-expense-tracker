"""Grok (xAI) LLM client.

The API key is read from ``grok_api_key.txt`` in the project root by default.
Environment variables take precedence, which is convenient for CI:

    GROK_API_KEY=xai-...
    XAI_API_KEY=xai-...
    GROK_MODEL=grok-4-fast
    GROK_BASE_URL=https://api.x.ai/v1

The client speaks the OpenAI-compatible chat-completions protocol, including
tool/function calling.  If no key is configured the agent automatically falls
back to a deterministic, grounded rule engine, so the app still works offline.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
KEY_FILE_CANDIDATES = (
    ROOT / "grok_api_key.txt",
    ROOT / "grok-api-key.txt",
    ROOT / "api_key.txt",
    ROOT / "config" / "grok_api_key.txt",
)
DEFAULT_BASE_URL = "https://api.x.ai/v1"
DEFAULT_MODEL = "grok-4-fast"
FALLBACK_MODELS = ("grok-4-fast", "grok-3-mini", "grok-4", "grok-beta")


class LLMUnavailable(RuntimeError):
    """Raised when the configured LLM cannot be reached."""


def _clean_key(value: str) -> str:
    value = (value or "").strip().strip('"').strip("'")
    if value.upper().startswith("GROK_API_KEY=") or value.upper().startswith("XAI_API_KEY="):
        value = value.split("=", 1)[1].strip()
    return value


def parse_key_text(text: str) -> str:
    """Read the first usable key from a text file.

    Supports a raw key, ``KEY=value`` lines, and ``#`` comments so the file can
    be self-documenting.
    """
    for line in (text or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key = _clean_key(line)
        if key and not key.lower().startswith(("paste", "your ", "<")):
            return key
    return ""


def load_api_key(key_file: str | Path | None = None) -> str:
    if key_file:
        path = Path(key_file)
        if path.exists():
            return parse_key_text(path.read_text(encoding="utf-8", errors="ignore"))

    for variable in ("GROK_API_KEY", "XAI_API_KEY", "XAI_KEY"):
        value = _clean_key(os.environ.get(variable, ""))
        if value:
            return value

    for path in KEY_FILE_CANDIDATES:
        if path.exists():
            value = parse_key_text(path.read_text(encoding="utf-8", errors="ignore"))
            if value:
                return value
    return ""


def provider_for_key(api_key: str) -> tuple[str, str]:
    """Return ``(base_url, default_model)`` for the Grok (xAI) API.

    The project is intentionally Grok-only.  A Groq key starts with ``gsk_`` and
    is rejected in ``GrokLLM.__init__`` rather than silently routed to a
    different provider.
    """
    return (
        os.environ.get("GROK_BASE_URL", DEFAULT_BASE_URL),
        os.environ.get("GROK_MODEL", DEFAULT_MODEL),
    )


@dataclass
class LLMResult:
    content: str = ""
    tool_calls: list[dict] = field(default_factory=list)
    model: str = ""
    raw: dict | None = None


class GrokLLM:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        key_file: str | Path | None = None,
        timeout: int = 45,
    ):
        self.api_key = api_key or load_api_key(key_file)
        self.invalid_key_reason: str | None = None
        if self.api_key.startswith("gsk_"):
            self.invalid_key_reason = (
                "That is a Groq key (gsk_...), not a Grok (xAI) key. "
                "Create a Grok key at https://console.x.ai and put it in grok_api_key.txt."
            )
            self.api_key = ""
        default_base, default_model = provider_for_key(self.api_key)
        self.base_url = (base_url or default_base).rstrip("/")
        self.model = model or default_model
        self.timeout = timeout
        self.last_error: str | None = self.invalid_key_reason
        self.last_model: str | None = None

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    @property
    def provider_name(self) -> str:
        if self.api_key.startswith("xai-"):
            return "Grok (xAI)"
        return "Grok (xAI compatible)"

    def status(self) -> dict:
        return {
            "available": self.available,
            "provider": self.provider_name if self.available else "Local fallback",
            "model": self.model,
            "base_url": self.base_url,
            "key_source": self._key_source(),
            "last_error": self.last_error,
        }

    def _key_source(self) -> str:
        if self.invalid_key_reason:
            return "invalid Groq key (expected xAI Grok)"
        if not self.api_key:
            return "no key configured"
        for variable in ("GROK_API_KEY", "XAI_API_KEY", "XAI_KEY"):
            if _clean_key(os.environ.get(variable, "")) == self.api_key:
                return f"environment ({variable})"
        for path in KEY_FILE_CANDIDATES:
            if path.exists() and parse_key_text(path.read_text(encoding="utf-8", errors="ignore")) == self.api_key:
                return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
        return "runtime argument"

    def _candidate_models(self) -> list[str]:
        candidates = [self.model]
        for model in FALLBACK_MODELS:
            if model not in candidates:
                candidates.append(model)
        return candidates

    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float = 0.2,
        max_tokens: int = 900,
    ) -> LLMResult:
        if not self.available:
            raise LLMUnavailable(
                "No Grok API key found. Put your key in grok_api_key.txt or set GROK_API_KEY."
            )

        last_error = None
        for model in self._candidate_models():
            payload: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if tools:
                payload["tools"] = tools
                payload["tool_choice"] = "auto"
            try:
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=self.timeout,
                )
            except requests.RequestException as exc:
                last_error = f"network error: {exc}"
                break

            if response.status_code == 401:
                last_error = "invalid or revoked API key (HTTP 401)"
                break
            if response.status_code in (400, 404):
                # Usually an unknown model name; try the next candidate.
                last_error = f"HTTP {response.status_code}: {response.text[:300]}"
                continue
            if response.status_code >= 400:
                last_error = f"HTTP {response.status_code}: {response.text[:300]}"
                break

            data = response.json()
            choice = (data.get("choices") or [{}])[0]
            message = choice.get("message") or {}
            self.last_model = model
            self.last_error = None
            return LLMResult(
                content=(message.get("content") or "").strip(),
                tool_calls=message.get("tool_calls") or [],
                model=model,
                raw=data,
            )

        self.last_error = last_error
        raise LLMUnavailable(last_error or "LLM request failed")
