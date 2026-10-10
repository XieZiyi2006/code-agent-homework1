"""Optional LLM providers. The project remains fully functional offline."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Dict, List, Optional


class ProviderError(RuntimeError):
    """Raised when an LLM provider cannot produce a response."""


class Provider:
    """Abstract text-generation provider used by the Agent."""

    def complete(self, messages: List[Dict[str, str]]) -> str:
        raise NotImplementedError


class OpenAICompatibleProvider(Provider):
    """Minimal standard-library client for Chat Completions-compatible APIs."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "gpt-4o-mini",
        timeout: float = 60.0,
        retries: int = 2,
        max_tokens: int = 600,
    ) -> None:
        self.api_key = api_key or os.getenv("CODE_AGENT_API_KEY", "")
        self.base_url = (base_url or os.getenv("CODE_AGENT_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.model = model
        self.timeout = timeout
        self.retries = max(0, retries)
        self.max_tokens = max(1, max_tokens)

    def complete(self, messages: List[Dict[str, str]]) -> str:
        if not self.api_key:
            raise ProviderError("未设置 CODE_AGENT_API_KEY，已无法启用远程 LLM")
        payload = json.dumps(
            {
                "model": self.model,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": self.max_tokens,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        last_error: Optional[Exception] = None
        for attempt in range(self.retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    data = json.loads(response.read().decode("utf-8"))
                content = data["choices"][0]["message"]["content"]
                if not isinstance(content, str):
                    raise ValueError("provider content is not text")
                if not content.strip():
                    raise ValueError("provider returned empty content")
                return content
            except urllib.error.HTTPError as exc:
                details = exc.read().decode("utf-8", errors="replace").strip()
                last_error = RuntimeError(f"HTTP {exc.code}: {details or exc.reason}")
                if 400 <= exc.code < 500 and exc.code not in {408, 429}:
                    break
                if attempt < self.retries:
                    time.sleep(0.25 * (2**attempt))
            except (urllib.error.URLError, TimeoutError, ValueError, KeyError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt < self.retries:
                    time.sleep(0.25 * (2**attempt))
        raise ProviderError(f"LLM 请求失败（已重试 {self.retries} 次）: {last_error}")

