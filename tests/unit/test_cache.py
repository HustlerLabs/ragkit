from __future__ import annotations

import pytest

from ragkit.cache.embedding_cache import CachedEmbedder
from ragkit.cache.query_cache import QueryCache
from ragkit.core.base import EmbeddingProvider


class _FakeEmbedder(EmbeddingProvider):
    def __init__(self):
        self.call_count = 0

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.call_count += 1
        return [[float(i)] * 4 for i in range(len(texts))]


class TestCachedEmbedder:
    def test_embed_calls_underlying(self, tmp_path):
        fake = _FakeEmbedder()
        embedder = CachedEmbedder(fake, cache_dir=str(tmp_path / "emb"))
        result = embedder.embed(["hello", "world"])
        assert len(result) == 2
        assert fake.call_count == 1

    def test_cache_hit_skips_underlying(self, tmp_path):
        fake = _FakeEmbedder()
        embedder = CachedEmbedder(fake, cache_dir=str(tmp_path / "emb"))
        embedder.embed(["hello"])
        embedder.embed(["hello"])
        assert fake.call_count == 1

    def test_new_text_calls_underlying_again(self, tmp_path):
        fake = _FakeEmbedder()
        embedder = CachedEmbedder(fake, cache_dir=str(tmp_path / "emb"))
        embedder.embed(["hello"])
        embedder.embed(["world"])
        assert fake.call_count == 2

    def test_partial_cache_hit(self, tmp_path):
        fake = _FakeEmbedder()
        embedder = CachedEmbedder(fake, cache_dir=str(tmp_path / "emb"))
        embedder.embed(["hello"])
        embedder.embed(["hello", "world"])
        # Second call should only compute 1 new embedding
        assert fake.call_count == 2

    def test_embed_one_delegate(self, tmp_path):
        fake = _FakeEmbedder()
        embedder = CachedEmbedder(fake, cache_dir=str(tmp_path / "emb"))
        result = embedder.embed_one("hello")
        assert isinstance(result, list)
        assert len(result) == 4


class TestQueryCache:
    def test_miss_returns_none(self, tmp_path):
        cache = QueryCache(cache_dir=str(tmp_path / "q"), ttl=60)
        assert cache.get("q", "ctx") is None

    def test_set_and_get(self, tmp_path):
        cache = QueryCache(cache_dir=str(tmp_path / "q"), ttl=60)
        cache.set("q", "ctx", "response")
        assert cache.get("q", "ctx") == "response"

    def test_different_queries_dont_collide(self, tmp_path):
        cache = QueryCache(cache_dir=str(tmp_path / "q"), ttl=60)
        cache.set("q1", "ctx", "r1")
        cache.set("q2", "ctx", "r2")
        assert cache.get("q1", "ctx") == "r1"
        assert cache.get("q2", "ctx") == "r2"

    def test_different_contexts_dont_collide(self, tmp_path):
        cache = QueryCache(cache_dir=str(tmp_path / "q"), ttl=60)
        cache.set("q", "ctx1", "r1")
        cache.set("q", "ctx2", "r2")
        assert cache.get("q", "ctx1") == "r1"
        assert cache.get("q", "ctx2") == "r2"

    def test_invalidate_clears_all(self, tmp_path):
        cache = QueryCache(cache_dir=str(tmp_path / "q"), ttl=60)
        cache.set("q", "ctx", "response")
        cache.invalidate()
        assert cache.get("q", "ctx") is None
