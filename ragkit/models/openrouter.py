from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx

from ragkit.core.base import ModelProvider
from ragkit.core.config import settings


class OpenRouterError(Exception):
    pass


class OpenRouterProvider(ModelProvider):
    def __init__(
        self,
        model: str = "openai/gpt-4o-mini",
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> None:
        self.model = model
        self.api_key = api_key or settings.openrouter_api_key
        self.base_url = base_url or settings.openrouter_base_url
        self.temperature = temperature
        self.max_tokens = max_tokens

    def _validate_api_key(self) -> None:
        if not self.api_key or self.api_key.strip() == "":
            raise OpenRouterError(
                "OPENROUTER_API_KEY is not set. "
                "Add it to your .env file or pass api_key= to OpenRouterProvider()."
            )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/ragkit",
        }

    def _payload(self, prompt: str, stream: bool = False) -> dict:
        return {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": stream,
        }

    def _handle_http_error(self, e: httpx.HTTPStatusError) -> None:
        if e.response.status_code == 401:
            raise OpenRouterError(
                "Invalid API key (401). Check your OPENROUTER_API_KEY."
            ) from e
        if e.response.status_code == 429:
            raise OpenRouterError("Rate limit exceeded (429). Retry later.") from e
        raise OpenRouterError(
            f"OpenRouter error {e.response.status_code}: {e.response.text[:200]}"
        ) from e

    def generate(self, prompt: str) -> str:
        self._validate_api_key()
        try:
            with httpx.Client(timeout=60) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json=self._payload(prompt),
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            self._handle_http_error(e)
        except httpx.TimeoutException as e:
            raise OpenRouterError("Request timed out after 60s.") from e
        except httpx.RequestError as e:
            raise OpenRouterError(f"Network error: {e}") from e

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        self._validate_api_key()
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=self._headers(),
                    json=self._payload(prompt, stream=True),
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data["choices"][0]["delta"].get("content", "")
                            if delta:
                                yield delta
                        except (json.JSONDecodeError, KeyError):
                            continue
        except httpx.HTTPStatusError as e:
            self._handle_http_error(e)
        except httpx.TimeoutException as e:
            raise OpenRouterError("Stream timed out after 60s.") from e
        except httpx.RequestError as e:
            raise OpenRouterError(f"Network error during stream: {e}") from e
