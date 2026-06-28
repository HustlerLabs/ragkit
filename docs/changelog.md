# Changelog

All notable changes to RAGKit are documented here.

---

## [0.1.0] — 2026-06-27

Initial public release.

### Added

**Core**

- `Agent` facade with fluent API: `.use()`, `.configure()`, `.set_model()`, `.set_embedder()`, `.set_store()`, `.install()`, `.on()`
- `index()` — load, clean, chunk, embed, store
- `sync()` — pull fresh data, then re-index
- `ask()` — retrieve context and generate answer
- `stream()` — async token streaming via `AsyncIterator[str]`

**Sources**

- `MarkdownSource` — `.md` files and directories (recursive)
- `TxtSource` — `.txt` files and directories
- `JsonSource` — `.json` files, configurable `content_key`
- `CsvSource` — `.csv` files, configurable `content_column`
- `RestSource` — HTTP/JSON APIs with headers, params, timeout
- `DirectorySource` — multi-format directory scanner

**Pipeline**

- `Cleaner` — whitespace normalization
- `Chunker` — boundary-aware splitting with configurable size and overlap

**Embeddings**

- `SentenceTransformerEmbedder` — local model, lazy-loaded on first use
- `CachedEmbedder` — disk-backed SHA-256 cache via `diskcache`

**Vector stores**

- `ChromaStore` — persistent local Chroma collection, lazy client init

**Models**

- `OpenRouterProvider` — OpenRouter API with sync generate and async streaming
- Typed `OpenRouterError` for all HTTP and network failure modes

**Cache**

- `QueryCache` — disk-backed LLM response cache with configurable TTL

**Hooks**

- `HookRegistry` with `@agent.on(event)` decorator
- Events: `before_index`, `before_generate`, `after_generate`, `after_response`

**Plugin system**

- `Plugin` ABC
- `PluginRegistry` with `importlib.metadata` entry_point discovery

**Configuration**

- `ProjectConfig` (pydantic v2) with `ModelConfig`, `PipelineConfig`, `RetrievalConfig`, `CacheConfig`
- `pydantic-settings` environment variable loading (`.env` + shell env)
- `rag init` generates a `rag.yaml` starter config

**CLI** (via Typer)

- `rag init` — scaffold a new project
- `rag index` — index all sources
- `rag sync` — sync sources and re-index
- `rag ask` — one-shot query
- `rag dev` — interactive REPL
- `rag serve` — FastAPI HTTP server (`/ask` endpoint, requires `ragkit[serve]`)
- `python -m ragkit` entrypoint

**Observability**

- `structlog` structured logging throughout the pipeline
- Log events: `index_called_without_sources`, embedding hits/misses, query cache hits

**CI**

- GitHub Actions: test matrix (Python 3.10/3.11/3.12), ruff lint, CLI smoke tests

**Documentation**

- MkDocs Material site with dark mode, code copy, navigation tabs
- Pages: Quickstart, Configuration, Sources, Pipeline, Models, CLI, Plugins, API Reference, Contributing

---

## Roadmap

### [0.2.0] — planned

- Hybrid search (BM25 + vector)
- Re-ranking (cross-encoder)
- `PineconeStore` adapter
- `OpenAIEmbedder` adapter
- Web source (`WebSource` with HTML extraction)
- Async `index()` for large corpora

### [0.3.0] — planned

- Multi-agent support (parallel indexing)
- Evaluation harness (RAGAS integration)
- REST API authentication
- Streaming via SSE in `rag serve`
