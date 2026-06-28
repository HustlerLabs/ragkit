"""Tests for error handling and edge cases added for production readiness."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import httpx
import pytest

from ragkit.core.base import Document
from ragkit.models.openrouter import OpenRouterError, OpenRouterProvider
from ragkit.sources.rest import RestSource, RestSourceError


# ── OpenRouterProvider errors ────────────────────────────────────────────────

class TestOpenRouterErrors:
    def test_generate_raises_on_empty_api_key(self):
        provider = OpenRouterProvider(model="test/m", api_key="")
        with pytest.raises(OpenRouterError, match="OPENROUTER_API_KEY"):
            provider.generate("hello")

    def test_generate_raises_on_whitespace_api_key(self):
        provider = OpenRouterProvider(model="test/m", api_key="   ")
        with pytest.raises(OpenRouterError, match="OPENROUTER_API_KEY"):
            provider.generate("hello")

    def test_generate_raises_on_401(self):
        provider = OpenRouterProvider(model="test/m", api_key="bad-key")
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        http_error = httpx.HTTPStatusError("401", request=MagicMock(), response=mock_resp)

        with patch("httpx.Client") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value.__enter__.return_value = mock_client
            mock_client.post.return_value = MagicMock(
                raise_for_status=MagicMock(side_effect=http_error)
            )
            with pytest.raises(OpenRouterError, match="401"):
                provider.generate("hello")

    def test_generate_raises_on_429(self):
        provider = OpenRouterProvider(model="test/m", api_key="key")
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        http_error = httpx.HTTPStatusError("429", request=MagicMock(), response=mock_resp)

        with patch("httpx.Client") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value.__enter__.return_value = mock_client
            mock_client.post.return_value = MagicMock(
                raise_for_status=MagicMock(side_effect=http_error)
            )
            with pytest.raises(OpenRouterError, match="429"):
                provider.generate("hello")

    def test_generate_raises_on_timeout(self):
        provider = OpenRouterProvider(model="test/m", api_key="key")
        with patch("httpx.Client") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value.__enter__.return_value = mock_client
            mock_client.post.side_effect = httpx.TimeoutException("timed out")
            with pytest.raises(OpenRouterError, match="timed out"):
                provider.generate("hello")

    def test_generate_raises_on_network_error(self):
        provider = OpenRouterProvider(model="test/m", api_key="key")
        with patch("httpx.Client") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value.__enter__.return_value = mock_client
            mock_client.post.side_effect = httpx.ConnectError("connection refused")
            with pytest.raises(OpenRouterError, match="Network error"):
                provider.generate("hello")

    @pytest.mark.asyncio
    async def test_stream_raises_on_empty_api_key(self):
        provider = OpenRouterProvider(model="test/m", api_key="")
        with pytest.raises(OpenRouterError, match="OPENROUTER_API_KEY"):
            async for _ in provider.stream("hello"):
                pass


# ── RestSource errors ────────────────────────────────────────────────────────

class TestRestSourceErrors:
    def test_raises_on_timeout(self):
        source = RestSource("https://example.com")
        with patch("httpx.get", side_effect=httpx.TimeoutException("timeout")):
            with pytest.raises(RestSourceError, match="timed out"):
                source.load()

    def test_raises_on_http_error(self):
        source = RestSource("https://example.com")
        mock_resp = MagicMock()
        mock_resp.status_code = 503
        mock_resp.text = "Service Unavailable"
        err = httpx.HTTPStatusError("503", request=MagicMock(), response=mock_resp)
        with patch("httpx.get", side_effect=err):
            with pytest.raises(RestSourceError, match="503"):
                source.load()

    def test_raises_on_network_error(self):
        source = RestSource("https://example.com")
        with patch("httpx.get", side_effect=httpx.ConnectError("refused")):
            with pytest.raises(RestSourceError, match="Network error"):
                source.load()

    def test_raises_on_invalid_json(self):
        source = RestSource("https://example.com")
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.side_effect = ValueError("not JSON")
        with patch("httpx.get", return_value=mock_resp):
            with pytest.raises(RestSourceError, match="not valid JSON"):
                source.load()

    def test_custom_timeout_passed(self):
        source = RestSource("https://example.com", timeout=10)
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = [{"content": "x"}]
        with patch("httpx.get", return_value=mock_resp) as mock_get:
            source.load()
        assert mock_get.call_args[1]["timeout"] == 10


# ── Agent edge cases ─────────────────────────────────────────────────────────

class TestAgentEdgeCases:
    def test_index_without_source_returns_empty(self):
        from ragkit.agent import Agent
        from ragkit.core.config import ProjectConfig

        config = ProjectConfig()
        config.cache.enabled = False
        agent = Agent(config=config)
        # No .use() called
        result = agent.index()
        assert result == []

    def test_cache_paths_under_single_directory(self):
        from ragkit.agent import Agent
        from ragkit.core.config import ProjectConfig

        config = ProjectConfig()
        config.cache.enabled = True
        config.cache.directory = "/tmp/ragkit_test_paths"
        agent = Agent(config=config)

        # All cache-related paths should be under the same root
        assert "/tmp/ragkit_test_paths" in str(agent._store.persist_directory)
