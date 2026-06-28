from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from ragkit.sources.rest import RestSource


def _mock_http_response(data) -> MagicMock:
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = data
    return resp


class TestRestSource:
    def test_load_list_response(self):
        source = RestSource("https://api.example.com/data", content_key="text")
        payload = [{"text": "hello", "id": 1}, {"text": "world", "id": 2}]

        with patch("httpx.get", return_value=_mock_http_response(payload)):
            docs = source.load()

        assert len(docs) == 2
        assert docs[0].content == "hello"
        assert docs[0].metadata["id"] == 1

    def test_load_dict_response(self):
        source = RestSource("https://api.example.com/item", content_key="body")
        payload = {"body": "single item", "author": "alice"}

        with patch("httpx.get", return_value=_mock_http_response(payload)):
            docs = source.load()

        assert len(docs) == 1
        assert docs[0].content == "single item"
        assert docs[0].metadata["author"] == "alice"

    def test_load_non_dict_items(self):
        source = RestSource("https://api.example.com/list")
        payload = ["item1", "item2", "item3"]

        with patch("httpx.get", return_value=_mock_http_response(payload)):
            docs = source.load()

        assert len(docs) == 3
        assert docs[0].content == "item1"

    def test_metadata_type_is_rest(self):
        source = RestSource("https://api.example.com/data")

        with patch("httpx.get", return_value=_mock_http_response([{"content": "x"}])):
            docs = source.load()

        assert docs[0].metadata["type"] == "rest"

    def test_metadata_source_is_url(self):
        url = "https://api.example.com/items"
        source = RestSource(url)

        with patch("httpx.get", return_value=_mock_http_response([{"content": "x"}])):
            docs = source.load()

        assert docs[0].metadata["source"] == url

    def test_passes_headers_and_params(self):
        source = RestSource(
            "https://api.example.com/data",
            headers={"Authorization": "Bearer token"},
            params={"page": "1"},
        )

        mock_get = MagicMock(return_value=_mock_http_response([{"content": "x"}]))
        with patch("httpx.get", mock_get):
            source.load()

        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["headers"]["Authorization"] == "Bearer token"
        assert call_kwargs["params"]["page"] == "1"

    def test_missing_content_key_falls_back_to_json(self):
        source = RestSource("https://api.example.com/data", content_key="missing_key")
        payload = [{"foo": "bar"}]

        with patch("httpx.get", return_value=_mock_http_response(payload)):
            docs = source.load()

        assert "foo" in docs[0].content
