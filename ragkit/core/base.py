from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Document:
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    embedding: list[float] | None = None
    id: str | None = None


class SourceAdapter(ABC):
    @abstractmethod
    def load(self) -> list[Document]: ...

    def transform(self, docs: list[Document]) -> list[Document]:
        return docs

    def sync(self) -> None:
        pass


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]: ...

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]


class VectorStore(ABC):
    @abstractmethod
    def insert(self, docs: list[Document]) -> None: ...

    @abstractmethod
    def search(self, query_vec: list[float], top_k: int = 5) -> list[Document]: ...

    def clear(self) -> None:
        pass


class ModelProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str: ...

    @abstractmethod
    async def stream(self, prompt: str) -> AsyncIterator[str]: ...


class Plugin(ABC):
    @abstractmethod
    def register(self, agent: Any) -> None: ...
