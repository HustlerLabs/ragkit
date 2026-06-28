from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ragkit.core.base import Document, SourceAdapter


class JsonSource(SourceAdapter):
    def __init__(self, path: str | Path, content_key: str = "content") -> None:
        self.path = Path(path)
        self.content_key = content_key

    def load(self) -> list[Document]:
        paths = [self.path] if self.path.is_file() else list(self.path.rglob("*.json"))
        docs = []
        for p in paths:
            data: Any = json.loads(p.read_text(encoding="utf-8"))
            items = data if isinstance(data, list) else [data]
            for item in items:
                if isinstance(item, dict):
                    content = item.get(self.content_key, json.dumps(item, ensure_ascii=False))
                    metadata = {k: v for k, v in item.items() if k != self.content_key}
                else:
                    content = str(item)
                    metadata = {}
                metadata["source"] = str(p)
                metadata["type"] = "json"
                docs.append(Document(content=content, metadata=metadata))
        return docs
