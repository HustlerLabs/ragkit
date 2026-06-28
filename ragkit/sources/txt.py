from __future__ import annotations

from pathlib import Path

from ragkit.core.base import Document, SourceAdapter


class TxtSource(SourceAdapter):
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> list[Document]:
        paths = [self.path] if self.path.is_file() else list(self.path.rglob("*.txt"))
        return [
            Document(
                content=p.read_text(encoding="utf-8"),
                metadata={"source": str(p), "type": "txt"},
            )
            for p in paths
        ]
