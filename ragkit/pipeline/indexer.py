from __future__ import annotations

from ragkit.core.base import Document, EmbeddingProvider, VectorStore
from ragkit.pipeline.chunker import Chunker
from ragkit.pipeline.cleaner import Cleaner


class Indexer:
    def __init__(
        self,
        embedder: EmbeddingProvider,
        store: VectorStore,
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> None:
        self.embedder = embedder
        self.store = store
        self.cleaner = Cleaner()
        self.chunker = Chunker(chunk_size=chunk_size, overlap=overlap)

    def index(self, docs: list[Document]) -> list[Document]:
        docs = self.cleaner.clean(docs)
        chunks = self.chunker.chunk(docs)
        texts = [c.content for c in chunks]
        embeddings = self.embedder.embed(texts)
        for chunk, vec in zip(chunks, embeddings):
            chunk.embedding = vec
        self.store.insert(chunks)
        return chunks
