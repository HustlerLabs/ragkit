from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest

from ragkit.core.base import Document


@pytest.fixture(autouse=True)
def mock_chromadb():
    """Inject a fake chromadb module so ChromaStore can be imported and tested without the package."""
    fake = ModuleType("chromadb")
    fake.PersistentClient = MagicMock
    sys.modules.setdefault("chromadb", fake)
    yield fake
    # Don't remove — other tests may have imported it


def _make_store(tmp_path):
    from ragkit.vectorstores.chroma import ChromaStore

    mock_collection = MagicMock()
    mock_collection.count.return_value = 0

    mock_client = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection

    store = ChromaStore(collection_name="test", persist_directory=str(tmp_path / "chroma"))

    # Patch the PersistentClient on the injected fake module
    import chromadb
    chromadb.PersistentClient = MagicMock(return_value=mock_client)

    _ = store.collection  # trigger lazy init

    return store, mock_collection, mock_client


class TestChromaStore:
    def test_insert_calls_upsert(self, tmp_path):
        store, collection, _ = _make_store(tmp_path)
        docs = [Document(content="hello", metadata={"source": "test"}, id="id1", embedding=[0.1, 0.2])]
        store.insert(docs)
        collection.upsert.assert_called_once()

    def test_insert_empty_list_does_nothing(self, tmp_path):
        store, collection, _ = _make_store(tmp_path)
        store.insert([])
        collection.upsert.assert_not_called()

    def test_search_returns_documents(self, tmp_path):
        store, collection, _ = _make_store(tmp_path)
        collection.count.return_value = 2
        collection.query.return_value = {
            "documents": [["doc A", "doc B"]],
            "metadatas": [[{"source": "a"}, {"source": "b"}]],
            "ids": [["id1", "id2"]],
        }

        results = store.search([0.1, 0.2, 0.3], top_k=2)
        assert len(results) == 2
        assert results[0].content == "doc A"
        assert results[0].id == "id1"

    def test_search_respects_top_k(self, tmp_path):
        store, collection, _ = _make_store(tmp_path)
        collection.count.return_value = 10
        collection.query.return_value = {
            "documents": [["a"]],
            "metadatas": [[{}]],
            "ids": [["id1"]],
        }
        store.search([0.1], top_k=3)
        call_kwargs = collection.query.call_args[1]
        assert call_kwargs["n_results"] == 3

    def test_search_empty_store_uses_at_least_one(self, tmp_path):
        store, collection, _ = _make_store(tmp_path)
        collection.count.return_value = 0
        collection.query.return_value = {
            "documents": [[]],
            "metadatas": [[]],
            "ids": [[]],
        }
        store.search([0.1], top_k=5)
        call_kwargs = collection.query.call_args[1]
        assert call_kwargs["n_results"] == 1

    def test_clear_deletes_collection(self, tmp_path):
        store, collection, client = _make_store(tmp_path)
        store.clear()
        client.delete_collection.assert_called_once_with("test")
        assert store._collection is None

    def test_insert_assigns_fallback_id(self, tmp_path):
        store, collection, _ = _make_store(tmp_path)
        docs = [Document(content="no id", metadata={}, embedding=[0.1])]
        store.insert(docs)
        call_kwargs = collection.upsert.call_args[1]
        assert call_kwargs["ids"] == ["0"]

    def test_get_or_create_collection_called_with_name(self, tmp_path):
        store, _, client = _make_store(tmp_path)
        client.get_or_create_collection.assert_called_once()
        call_kwargs = client.get_or_create_collection.call_args[1]
        assert call_kwargs["name"] == "test"
