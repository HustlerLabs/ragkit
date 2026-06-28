from __future__ import annotations

from typing import AsyncIterator
from unittest.mock import MagicMock

import pytest

from ragkit.core.base import Document, EmbeddingProvider, ModelProvider, Plugin, SourceAdapter, VectorStore
from ragkit.core.config import ProjectConfig


class _FakeEmbedder(EmbeddingProvider):
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2] for _ in texts]


class _FakeStore(VectorStore):
    def __init__(self, search_results: list[Document] | None = None):
        self.inserted: list[Document] = []
        self._results = search_results or [Document(content="context chunk", metadata={})]

    def insert(self, docs: list[Document]) -> None:
        self.inserted.extend(docs)

    def search(self, query_vec: list[float], top_k: int = 5) -> list[Document]:
        return self._results


class _FakeModel(ModelProvider):
    def __init__(self, response: str = "fake response"):
        self._response = response

    def generate(self, prompt: str) -> str:
        return self._response

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        for word in self._response.split():
            yield word


class _FakeSource(SourceAdapter):
    def __init__(self, docs: list[Document]):
        self._docs = docs

    def load(self) -> list[Document]:
        return self._docs


def _make_agent(docs=None, response="fake answer"):
    from ragkit.agent import Agent

    config = ProjectConfig()
    config.cache.enabled = False
    agent = Agent(config=config)
    agent._embedder = _FakeEmbedder()
    agent._store = _FakeStore()
    agent._model = _FakeModel(response)

    from ragkit.pipeline.indexer import Indexer
    agent._indexer = Indexer(agent._embedder, agent._store, chunk_size=500, overlap=50)

    if docs:
        agent.use(_FakeSource(docs))
    return agent


class TestAgent:
    def test_ask_returns_model_response(self):
        agent = _make_agent()
        result = agent.ask("what is X?")
        assert result == "fake answer"

    def test_index_processes_all_sources(self):
        docs = [Document(content="doc1", metadata={}), Document(content="doc2", metadata={})]
        agent = _make_agent(docs=docs)
        chunks = agent.index()
        assert len(chunks) >= 1
        assert len(agent._store.inserted) >= 1

    def test_use_adds_source(self):
        agent = _make_agent()
        source = _FakeSource([Document(content="x", metadata={})])
        agent.use(source)
        assert source in agent._sources

    def test_configure_updates_chunk_size(self):
        agent = _make_agent()
        agent.configure(chunk_size=200, overlap=20)
        assert agent._config.pipeline.chunk_size == 200
        assert agent._config.pipeline.overlap == 20

    def test_configure_updates_top_k(self):
        agent = _make_agent()
        agent.configure(top_k=10)
        assert agent._config.retrieval.top_k == 10

    def test_set_model_replaces_model(self):
        agent = _make_agent()
        new_model = _FakeModel("new response")
        agent.set_model(new_model)
        assert agent._model is new_model
        assert agent.ask("q") == "new response"

    def test_set_store_replaces_store(self):
        agent = _make_agent()
        new_store = _FakeStore()
        agent.set_store(new_store)
        assert agent._store is new_store

    def test_set_embedder_replaces_embedder(self):
        agent = _make_agent()
        new_embedder = _FakeEmbedder()
        agent.set_embedder(new_embedder)
        assert agent._embedder is new_embedder

    def test_hook_before_generate_fires(self):
        agent = _make_agent()
        calls = []

        @agent.on("before_generate")
        def capture(prompt):
            calls.append(prompt)

        agent.ask("hello")
        assert len(calls) == 1

    def test_hook_after_generate_fires(self):
        agent = _make_agent()
        calls = []

        @agent.on("after_generate")
        def capture(response):
            calls.append(response)

        agent.ask("hello")
        assert calls == ["fake answer"]

    def test_hook_after_response_fires(self):
        agent = _make_agent()
        seen = []
        agent.on("after_response")(lambda response: seen.append(response))
        agent.ask("q")
        assert seen == ["fake answer"]

    def test_install_plugin_calls_register(self):
        agent = _make_agent()

        class _P(Plugin):
            registered = False
            def register(self, ag) -> None:
                _P.registered = True

        agent.install(_P())
        assert _P.registered

    @pytest.mark.asyncio
    async def test_stream_yields_tokens(self):
        agent = _make_agent(response="hello world")
        tokens = []
        async for token in agent.stream("q"):
            tokens.append(token)
        assert tokens == ["hello", "world"]

    def test_ask_uses_query_cache(self):
        from ragkit.core.config import ProjectConfig
        from ragkit.agent import Agent

        config = ProjectConfig()
        config.cache.enabled = True
        config.cache.directory = "/tmp/ragkit_test_cache"
        agent = Agent(config=config)
        agent._embedder = _FakeEmbedder()
        agent._store = _FakeStore()
        agent._model = _FakeModel("cached answer")
        from ragkit.pipeline.indexer import Indexer
        agent._indexer = Indexer(agent._embedder, agent._store)

        r1 = agent.ask("same question")
        r2 = agent.ask("same question")
        assert r1 == r2 == "cached answer"

    def test_agent_loads_config_from_yaml_path(self, tmp_path):
        config_file = tmp_path / "rag.yaml"
        config_file.write_text("project:\n  name: yaml-test\n")
        from ragkit.agent import Agent
        agent = Agent(config=str(config_file))
        assert agent._config.name == "yaml-test"

    def test_sync_calls_source_sync_and_indexes(self):
        synced = []

        class _SyncSource(_FakeSource):
            def sync(self):
                synced.append(True)

        agent = _make_agent()
        agent.use(_SyncSource([Document(content="data", metadata={})]))
        chunks = agent.sync()
        assert synced == [True]
        assert len(chunks) >= 1
