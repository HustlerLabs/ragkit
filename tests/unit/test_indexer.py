from __future__ import annotations

import pytest

from ragkit.core.base import Document, EmbeddingProvider, VectorStore
from ragkit.pipeline.indexer import Indexer


class _FakeEmbedder(EmbeddingProvider):
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


class _FakeStore(VectorStore):
    def __init__(self):
        self.inserted: list[Document] = []

    def insert(self, docs: list[Document]) -> None:
        self.inserted.extend(docs)

    def search(self, query_vec: list[float], top_k: int = 5) -> list[Document]:
        return self.inserted[:top_k]


class TestIndexer:
    def test_indexes_documents(self):
        store = _FakeStore()
        indexer = Indexer(_FakeEmbedder(), store, chunk_size=500, overlap=50)
        docs = [Document(content="hello world", metadata={"source": "test"})]
        chunks = indexer.index(docs)
        assert len(chunks) >= 1
        assert len(store.inserted) >= 1

    def test_chunks_have_embeddings(self):
        store = _FakeStore()
        indexer = Indexer(_FakeEmbedder(), store)
        docs = [Document(content="some content here", metadata={})]
        chunks = indexer.index(docs)
        for chunk in chunks:
            assert chunk.embedding == [0.1, 0.2, 0.3]

    def test_empty_docs_list(self):
        store = _FakeStore()
        indexer = Indexer(_FakeEmbedder(), store)
        chunks = indexer.index([])
        assert chunks == []
        assert store.inserted == []

    def test_long_document_splits_into_multiple_chunks(self):
        store = _FakeStore()
        indexer = Indexer(_FakeEmbedder(), store, chunk_size=20, overlap=5)
        content = "word " * 50
        docs = [Document(content=content, metadata={"source": "big.md"})]
        chunks = indexer.index(docs)
        assert len(chunks) > 1

    def test_metadata_preserved_through_pipeline(self):
        store = _FakeStore()
        indexer = Indexer(_FakeEmbedder(), store)
        docs = [Document(content="hello", metadata={"source": "test.md", "lang": "fr"})]
        chunks = indexer.index(docs)
        assert chunks[0].metadata["lang"] == "fr"
        assert chunks[0].metadata["source"] == "test.md"
