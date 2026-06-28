from __future__ import annotations

import csv as csv_module
from pathlib import Path

from ragkit.core.base import Document, SourceAdapter


class CsvSource(SourceAdapter):
    def __init__(self, path: str | Path, content_column: str | None = None) -> None:
        self.path = Path(path)
        self.content_column = content_column

    def load(self) -> list[Document]:
        paths = [self.path] if self.path.is_file() else list(self.path.rglob("*.csv"))
        docs = []
        for p in paths:
            with p.open(encoding="utf-8") as f:
                reader = csv_module.DictReader(f)
                for row in reader:
                    if self.content_column and self.content_column in row:
                        content = row[self.content_column]
                        metadata = {k: v for k, v in row.items() if k != self.content_column}
                    else:
                        content = " | ".join(f"{k}: {v}" for k, v in row.items())
                        metadata = {}
                    metadata["source"] = str(p)
                    metadata["type"] = "csv"
                    docs.append(Document(content=content, metadata=metadata))
        return docs
