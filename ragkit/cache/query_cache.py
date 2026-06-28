from __future__ import annotations

import hashlib

import diskcache


class QueryCache:
    def __init__(self, cache_dir: str = ".ragkit_cache/queries", ttl: int = 3600) -> None:
        self._cache = diskcache.Cache(cache_dir)
        self.ttl = ttl

    def _key(self, query: str, context: str) -> str:
        return hashlib.sha256(f"{query}||{context}".encode()).hexdigest()

    def get(self, query: str, context: str) -> str | None:
        return self._cache.get(self._key(query, context))

    def set(self, query: str, context: str, response: str) -> None:
        self._cache.set(self._key(query, context), response, expire=self.ttl)

    def invalidate(self, query: str | None = None) -> None:
        if query is None:
            self._cache.clear()
        # Per-query invalidation not supported without index — clear all
