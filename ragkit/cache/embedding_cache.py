from __future__ import annotations

import hashlib

import diskcache

from ragkit.core.base import EmbeddingProvider


class CachedEmbedder(EmbeddingProvider):
    def __init__(self, embedder: EmbeddingProvider, cache_dir: str = ".ragkit_cache/embeddings") -> None:
        self._embedder = embedder
        self._cache = diskcache.Cache(cache_dir)

    def embed(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float]] = []
        uncached_indices: list[int] = []
        uncached_texts: list[str] = []

        for i, text in enumerate(texts):
            key = hashlib.sha256(text.encode()).hexdigest()
            cached = self._cache.get(key)
            if cached is not None:
                results.append(cached)
            else:
                results.append([])
                uncached_indices.append(i)
                uncached_texts.append(text)

        if uncached_texts:
            new_embeddings = self._embedder.embed(uncached_texts)
            for idx, embedding in zip(uncached_indices, new_embeddings):
                key = hashlib.sha256(texts[idx].encode()).hexdigest()
                self._cache[key] = embedding
                results[idx] = embedding

        return results
