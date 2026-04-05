from __future__ import annotations

from typing import Any

import httpx

from .json_utils import extract_json_object


class CompatibleAgentProvider:
    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str,
        timeout_seconds: float,
        temperature: float = 0.2,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature
        self.transport = transport

    def _extract_content(self, payload: dict[str, Any]) -> str:
        choices = payload.get("choices") or []
        if not choices:
            raise ValueError("Model response did not include any choices.")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") in {"text", "output_text"}:
                    parts.append(str(item.get("text", "")))
            if parts:
                return "\n".join(parts)
        raise ValueError("Model response content is missing or unsupported.")

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        if not self.base_url:
            raise RuntimeError("Agent model base URL is not configured.")
        if not self.model:
            raise RuntimeError("Agent model name is not configured.")
        if not self.api_key:
            raise RuntimeError("Agent model API key is not configured.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        with httpx.Client(
            transport=self.transport,
            timeout=self.timeout_seconds,
        ) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            content = self._extract_content(response.json())

        return extract_json_object(content)
