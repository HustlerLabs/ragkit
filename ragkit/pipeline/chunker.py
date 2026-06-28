from __future__ import annotations

import hashlib

from ragkit.core.base import Document


class Chunker:
    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, docs: list[Document]) -> list[Document]:
        chunks = []
        for doc in docs:
            for i, chunk_text in enumerate(self._split(doc.content)):
                chunk_id = hashlib.md5(f"{doc.metadata.get('source', '')}-{i}".encode()).hexdigest()
                chunks.append(Document(
                    content=chunk_text,
                    metadata={**doc.metadata, "chunk_index": i},
                    id=chunk_id,
                ))
        return chunks

    def _split(self, text: str) -> list[str]:
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]

            # Try to break on a sentence or word boundary
            if end < len(text):
                boundary = max(
                    chunk.rfind(". "),
                    chunk.rfind("\n"),
                    chunk.rfind(" "),
                )
                if boundary > self.chunk_size // 2:
                    end = start + boundary + 1
                    chunk = text[start:end]

            chunks.append(chunk.strip())
            start = end - self.overlap

        return [c for c in chunks if c]
