from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ragkit.models.openrouter import OpenRouterProvider


def _mock_response(content: str) -> MagicMock:
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "choices": [{"message": {"content": content}}]
    }
    return response


def _sse_lines(chunks: list[str]) -> list[str]:
    lines = []
    for chunk in chunks:
        data = {"choices": [{"delta": {"content": chunk}}]}
        lines.append(f"data: {json.dumps(data)}")
    lines.append("data: [DONE]")
    return lines


class TestOpenRouterProvider:
    def test_generate_returns_content(self):
        provider = OpenRouterProvider(model="test/model", api_key="fake-key")
        mock_resp = _mock_response("Paris")

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value.__enter__.return_value = mock_client
            mock_client.post.return_value = mock_resp

            result = provider.generate("What is the capital of France?")

        assert result == "Paris"

    def test_generate_calls_correct_endpoint(self):
        provider = OpenRouterProvider(model="test/model", api_key="fake-key")
        mock_resp = _mock_response("ok")

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value.__enter__.return_value = mock_client
            mock_client.post.return_value = mock_resp

            provider.generate("hello")

        call_args = mock_client.post.call_args
        assert "/chat/completions" in call_args[0][0]

    def test_generate_sends_model_in_payload(self):
        provider = OpenRouterProvider(model="openai/gpt-4o", api_key="fake-key")
        mock_resp = _mock_response("ok")

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value.__enter__.return_value = mock_client
            mock_client.post.return_value = mock_resp

            provider.generate("hello")

        payload = mock_client.post.call_args[1]["json"]
        assert payload["model"] == "openai/gpt-4o"

    def test_generate_sends_auth_header(self):
        provider = OpenRouterProvider(model="test/m", api_key="my-secret-key")
        mock_resp = _mock_response("ok")

        with patch("httpx.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client_cls.return_value.__enter__.return_value = mock_client
            mock_client.post.return_value = mock_resp

            provider.generate("hello")

        headers = mock_client.post.call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer my-secret-key"

    @pytest.mark.asyncio
    async def test_stream_yields_chunks(self):
        provider = OpenRouterProvider(model="test/model", api_key="fake-key")
        sse_lines = _sse_lines(["Hello", " world"])

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        async def fake_aiter_lines():
            for line in sse_lines:
                yield line

        mock_response.aiter_lines = fake_aiter_lines

        stream_cm = MagicMock()
        stream_cm.__aenter__ = AsyncMock(return_value=mock_response)
        stream_cm.__aexit__ = AsyncMock(return_value=False)

        mock_client = MagicMock()
        mock_client.stream = MagicMock(return_value=stream_cm)

        mock_client_cls = MagicMock()
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("ragkit.models.openrouter.httpx.AsyncClient", mock_client_cls):
            chunks = []
            async for chunk in provider.stream("hello"):
                chunks.append(chunk)

        assert chunks == ["Hello", " world"]

    @pytest.mark.asyncio
    async def test_stream_skips_non_data_lines(self):
        provider = OpenRouterProvider(model="test/model", api_key="fake-key")

        lines = [
            "event: ping",           # no "data: " prefix → skipped
            ": keep-alive",          # comment → skipped
            'data: {"choices": [{"delta": {"content": "hello"}}]}',
            "data: [DONE]",
        ]

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        async def fake_aiter_lines():
            for line in lines:
                yield line

        mock_response.aiter_lines = fake_aiter_lines

        stream_cm = MagicMock()
        stream_cm.__aenter__ = AsyncMock(return_value=mock_response)
        stream_cm.__aexit__ = AsyncMock(return_value=False)

        mock_client = MagicMock()
        mock_client.stream = MagicMock(return_value=stream_cm)

        mock_client_cls = MagicMock()
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("ragkit.models.openrouter.httpx.AsyncClient", mock_client_cls):
            chunks = []
            async for chunk in provider.stream("hello"):
                chunks.append(chunk)

        assert chunks == ["hello"]

    @pytest.mark.asyncio
    async def test_stream_skips_malformed_json(self):
        provider = OpenRouterProvider(model="test/model", api_key="fake-key")

        lines = [
            "data: {invalid json}",                                              # JSON decode error → skipped
            'data: {"no_choices": true}',                                        # KeyError → skipped
            'data: {"choices": [{"delta": {"content": "ok"}}]}',
            "data: [DONE]",
        ]

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        async def fake_aiter_lines():
            for line in lines:
                yield line

        mock_response.aiter_lines = fake_aiter_lines

        stream_cm = MagicMock()
        stream_cm.__aenter__ = AsyncMock(return_value=mock_response)
        stream_cm.__aexit__ = AsyncMock(return_value=False)

        mock_client = MagicMock()
        mock_client.stream = MagicMock(return_value=stream_cm)

        mock_client_cls = MagicMock()
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("ragkit.models.openrouter.httpx.AsyncClient", mock_client_cls):
            chunks = []
            async for chunk in provider.stream("hello"):
                chunks.append(chunk)

        assert chunks == ["ok"]

    @pytest.mark.asyncio
    async def test_stream_skips_empty_delta(self):
        provider = OpenRouterProvider(model="test/model", api_key="fake-key")

        lines = [
            'data: {"choices": [{"delta": {"content": ""}}]}',
            'data: {"choices": [{"delta": {"content": "hi"}}]}',
            "data: [DONE]",
        ]

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        async def fake_aiter_lines():
            for line in lines:
                yield line

        mock_response.aiter_lines = fake_aiter_lines

        stream_cm = MagicMock()
        stream_cm.__aenter__ = AsyncMock(return_value=mock_response)
        stream_cm.__aexit__ = AsyncMock(return_value=False)

        mock_client = MagicMock()
        mock_client.stream = MagicMock(return_value=stream_cm)

        mock_client_cls = MagicMock()
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("ragkit.models.openrouter.httpx.AsyncClient", mock_client_cls):
            chunks = []
            async for chunk in provider.stream("hello"):
                chunks.append(chunk)

        assert chunks == ["hi"]
