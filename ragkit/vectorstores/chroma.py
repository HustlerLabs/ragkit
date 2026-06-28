from __future__ import annotations

from ragkit.core.base import Document, VectorStore


class ChromaStore(VectorStore):
    def __init__(self, collection_name: str = "ragkit", persist_directory: str = ".ragkit_chroma") -> None:
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self._client = None
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            import chromadb
            self._client = chromadb.PersistentClient(path=self.persist_directory)
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def insert(self, docs: list[Document]) -> None:
        if not docs:
            return
        ids = [d.id or str(i) for i, d in enumerate(docs)]
        embeddings = [d.embedding for d in docs if d.embedding is not None]
        documents = [d.content for d in docs]
        metadatas = [d.metadata for d in docs]
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def search(self, query_vec: list[float], top_k: int = 5) -> list[Document]:
        results = self.collection.query(
            query_embeddings=[query_vec],
            n_results=min(top_k, self.collection.count() or 1),
        )
        docs = []
        for i, content in enumerate(results["documents"][0]):
            docs.append(Document(
                content=content,
                metadata=results["metadatas"][0][i],
                id=results["ids"][0][i],
            ))
        return docs

    def clear(self) -> None:
        if self._client and self._collection:
            self._client.delete_collection(self.collection_name)
            self._collection = None
