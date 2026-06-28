from __future__ import annotations

import json
from typing import Any

import httpx

from ragkit.core.base import Document, SourceAdapter
from ragkit.utils.logger import get_logger

logger = get_logger("ragkit.sources.rest")


class RestSourceError(Exception):
    pass


class RestSource(SourceAdapter):
    def __init__(
        self,
        url: str,
        content_key: str = "content",
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        timeout: int = 30,
    ) -> None:
        self.url = url
        self.content_key = content_key
        self.headers = headers or {}
        self.params = params or {}
        self.timeout = timeout

    def load(self) -> list[Document]:
        try:
            response = httpx.get(
                self.url,
                headers=self.headers,
                params=self.params,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.TimeoutException as e:
            raise RestSourceError(f"Request timed out after {self.timeout}s: {self.url}") from e
        except httpx.HTTPStatusError as e:
            raise RestSourceError(
                f"HTTP {e.response.status_code} from {self.url}: {e.response.text[:200]}"
            ) from e
        except httpx.RequestError as e:
            raise RestSourceError(f"Network error reaching {self.url}: {e}") from e

        try:
            data: Any = response.json()
        except Exception as e:
            raise RestSourceError(f"Response from {self.url} is not valid JSON") from e

        items = data if isinstance(data, list) else [data]
        docs = []
        for item in items:
            if isinstance(item, dict):
                content = item.get(self.content_key, json.dumps(item, ensure_ascii=False))
                metadata = {k: v for k, v in item.items() if k != self.content_key}
            else:
                content = str(item)
                metadata = {}
            metadata["source"] = self.url
            metadata["type"] = "rest"
            docs.append(Document(content=content, metadata=metadata))

        logger.info("rest_source_loaded", url=self.url, docs=len(docs))
        return docs
