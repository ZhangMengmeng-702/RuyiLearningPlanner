# -*- coding: utf-8 -*-
"""Hermes HTTP Client for Learning Planner.

Connects to Hermes Agent via local OpenAI-compatible HTTP API.
Reference: RuyiDailyStockAnalysis/src/llm/hermes.py
"""

from __future__ import annotations

import os
import re
import json
from typing import Any, Dict, Generator, Optional, List
from urllib.parse import urlparse, urlunparse, quote, unquote


HERMES_DEFAULT_BASE_URL = "http://127.0.0.1:8642/v1"
HERMES_DEFAULT_MODEL = "hermes-agent"
HERMES_DEFAULT_API_KEY = "2a4bbfef528a0e2ae3478c56239c671f47c0df2cf4d53df52172252ea9352ff8"


class HermesClient:
    """HTTP client for Hermes Agent."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 60.0,
    ):
        self._api_key = api_key or os.getenv("HERMES_API_KEY", HERMES_DEFAULT_API_KEY)
        self._base_url = self._canonicalize_base_url(base_url or os.getenv("HERMES_BASE_URL", HERMES_DEFAULT_BASE_URL))
        self._model = model or os.getenv("HERMES_MODEL", HERMES_DEFAULT_MODEL)
        self._timeout = timeout
        self._client = None

    def _canonicalize_base_url(self, base_url: str) -> str:
        """Return canonical Hermes base URL."""
        raw = base_url.strip() or HERMES_DEFAULT_BASE_URL
        parsed = urlparse(raw)

        if parsed.scheme.lower() not in {"http", "https"}:
            raise ValueError("Hermes BASE_URL must use http or https")
        if not parsed.netloc or not parsed.hostname:
            raise ValueError("Hermes BASE_URL must include a host")

        hostname = parsed.hostname.strip().lower()
        if hostname == "localhost":
            hostname = "127.0.0.1"

        port = parsed.port or 8642
        netloc = f"[{hostname}]" if ":" in hostname else hostname
        netloc = f"{netloc}:{port}"

        return urlunparse(parsed._replace(netloc=netloc, path="/v1", params="", query="", fragment=""))

    @property
    def is_available(self) -> bool:
        """Check if Hermes Agent is available."""
        try:
            self._get_client()
            return True
        except Exception:
            return False

    def _get_client(self):
        """Get or create OpenAI client."""
        if self._client is None:
            import httpx
            from openai import OpenAI

            http_client = httpx.Client(
                trust_env=False,
                follow_redirects=False,
                timeout=self._timeout,
            )
            self._client = OpenAI(
                api_key=self._api_key,
                base_url=self._base_url,
                http_client=http_client,
            )
        return self._client

    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = None,
    ) -> Any:
        """Call Hermes Agent chat completion API."""
        client = self._get_client()
        params = {
            "model": model or self._model,
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens:
            params["max_tokens"] = max_tokens
        if stream:
            params["stream"] = stream
        if tools:
            params["tools"] = tools
        if tool_choice:
            params["tool_choice"] = tool_choice

        return client.chat.completions.create(**params)

    def chat(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Simple chat interface."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})

        response = self.chat_completion(messages, model, temperature, max_tokens, stream=False)
        return response.choices[0].message.content or ""

    def chat_stream(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Generator[str, None, None]:
        """Stream chat interface."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})

        stream = self.chat_completion(messages, model, temperature, max_tokens, stream=True, tools=tools)
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    def close(self):
        """Close the client."""
        if self._client:
            self._client.close()


def create_hermes_client(**kwargs) -> HermesClient:
    """Factory function for creating HermesClient."""
    return HermesClient(**kwargs)