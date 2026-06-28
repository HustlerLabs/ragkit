from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

from ragkit.cache.embedding_cache import CachedEmbedder
from ragkit.cache.query_cache import QueryCache
from ragkit.core.base import (
    Document,
    EmbeddingProvider,
    ModelProvider,
    Plugin,
    SourceAdapter,
    VectorStore,
)
from ragkit.core.config import ProjectConfig, load_config
from ragkit.core.hooks import HookRegistry
from ragkit.core.registry import PluginRegistry
from ragkit.embeddings.sentence_transformers import SentenceTransformerEmbedder
from ragkit.models.openrouter import OpenRouterProvider
from ragkit.pipeline.indexer import Indexer
from ragkit.utils.logger import get_logger
from ragkit.utils.telemetry import Telemetry, timer
from ragkit.vectorstores.chroma import ChromaStore

logger = get_logger("ragkit.agent")


def _build_prompt(query: str, context_docs: list[Document]) -> str:
    context = "\n\n---\n\n".join(d.content for d in context_docs)
    return (
        f"Use the following context to answer the question.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {query}\n\n"
        f"Answer:"
    )


class Agent:
    def __init__(self, config: str | Path | ProjectConfig = "rag.yaml") -> None:
        if isinstance(config, ProjectConfig):
            self._config = config
        else:
            self._config = load_config(config)

        self.hooks = HookRegistry()
        self.plugins = PluginRegistry()
        self.telemetry = Telemetry()

        cache_dir = self._config.cache.directory

        self._sources: list[SourceAdapter] = []
        self._embedder: EmbeddingProvider = SentenceTransformerEmbedder()
        self._store: VectorStore = ChromaStore(persist_directory=f"{cache_dir}/chroma")
        self._model: ModelProvider = OpenRouterProvider(model=self._config.model.model)
        self._query_cache: QueryCache | None = None

        if self._config.cache.enabled:
            self._embedder = CachedEmbedder(
                self._embedder,
                cache_dir=f"{cache_dir}/embeddings",
            )
            self._query_cache = QueryCache(
                cache_dir=f"{cache_dir}/queries",
                ttl=self._config.cache.ttl,
            )

        self._indexer = Indexer(
            embedder=self._embedder,
            store=self._store,
            chunk_size=self._config.pipeline.chunk_size,
            overlap=self._config.pipeline.overlap,
        )

    # --- Configuration fluent API ---

    def use(self, source: SourceAdapter) -> Agent:
        self._sources.append(source)
        return self

    def set_embedder(self, embedder: EmbeddingProvider) -> Agent:
        self._embedder = embedder
        self._indexer = Indexer(
            embedder=self._embedder,
            store=self._store,
            chunk_size=self._config.pipeline.chunk_size,
            overlap=self._config.pipeline.overlap,
        )
        return self

    def set_store(self, store: VectorStore) -> Agent:
        self._store = store
        self._indexer = Indexer(
            embedder=self._embedder,
            store=self._store,
            chunk_size=self._config.pipeline.chunk_size,
            overlap=self._config.pipeline.overlap,
        )
        return self

    def set_model(self, provider: ModelProvider) -> Agent:
        self._model = provider
        return self

    def configure(
        self,
        chunk_size: int | None = None,
        overlap: int | None = None,
        top_k: int | None = None,
    ) -> Agent:
        if chunk_size is not None:
            self._config.pipeline.chunk_size = chunk_size
        if overlap is not None:
            self._config.pipeline.overlap = overlap
        if top_k is not None:
            self._config.retrieval.top_k = top_k
        self._indexer = Indexer(
            embedder=self._embedder,
            store=self._store,
            chunk_size=self._config.pipeline.chunk_size,
            overlap=self._config.pipeline.overlap,
        )
        return self

    def install(self, plugin: Plugin) -> Agent:
        plugin.register(self)
        return self

    def on(self, event: str):
        return self.hooks.on(event)

    # --- Core operations ---

    def index(self) -> list[Document]:
        if not self._sources:
            logger.warning(
                "index_called_without_sources",
                hint="Call agent.use(source) before agent.index()",
            )
            return []

        all_docs: list[Document] = []
        for source in self._sources:
            docs = source.load()
            docs = source.transform(docs)
            all_docs.extend(docs)

        self.hooks.fire("before_index", docs=all_docs)

        with timer("indexing", self.telemetry):
            chunks = self._indexer.index(all_docs)

        self.telemetry.indexing_time = self.telemetry.events[-1].get("duration_s", 0)
        logger.info("indexed", chunks=len(chunks), sources=len(self._sources))
        return chunks

    def ask(self, query: str) -> str:
        query_vec = self._embedder.embed_one(query)
        context_docs = self._store.search(query_vec, top_k=self._config.retrieval.top_k)
        prompt = _build_prompt(query, context_docs)

        if self._query_cache:
            context_str = "".join(d.content for d in context_docs)
            cached = self._query_cache.get(query, context_str)
            if cached:
                return cached

        self.hooks.fire("before_generate", prompt=prompt)

        with timer("llm_generate", self.telemetry):
            response = self._model.generate(prompt)

        self.hooks.fire("after_generate", response=response)

        if self._query_cache:
            context_str = "".join(d.content for d in context_docs)
            self._query_cache.set(query, context_str, response)

        self.hooks.fire("after_response", response=response)
        return response

    async def stream(self, query: str) -> AsyncIterator[str]:
        query_vec = self._embedder.embed_one(query)
        context_docs = self._store.search(query_vec, top_k=self._config.retrieval.top_k)
        prompt = _build_prompt(query, context_docs)

        self.hooks.fire("before_generate", prompt=prompt)
        async for chunk in self._model.stream(prompt):
            yield chunk

    def sync(self) -> list[Document]:
        for source in self._sources:
            source.sync()
        return self.index()
