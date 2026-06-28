from __future__ import annotations

from pathlib import Path

from ragkit.core.base import Document, SourceAdapter

SUPPORTED_EXTENSIONS = {".md", ".txt", ".json", ".csv"}


class DirectorySource(SourceAdapter):
    def __init__(self, path: str | Path, extensions: set[str] | None = None) -> None:
        self.path = Path(path)
        self.extensions = extensions or SUPPORTED_EXTENSIONS

    def load(self) -> list[Document]:
        docs = []
        for p in self.path.rglob("*"):
            if p.is_file() and p.suffix in self.extensions:
                try:
                    content = p.read_text(encoding="utf-8")
                    docs.append(Document(
                        content=content,
                        metadata={"source": str(p), "type": p.suffix.lstrip(".")},
                    ))
                except Exception:
                    pass
        return docs
