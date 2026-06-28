# API Reference

Complete Python API reference for RAGKit.

---

## `Agent`

The main entry point. Orchestrates sources, pipeline, retrieval, and generation.

```python
from ragkit import Agent

agent = Agent(config="rag.yaml")
```

### Constructor

```python
Agent(config: str | Path | ProjectConfig = "rag.yaml")
```

| Parameter | Type | Description |
|---|---|---|
| `config` | `str`, `Path`, or `ProjectConfig` | Config file path or config object |

---

### `.use(source)` → `Agent`

Add a data source. Returns `self` for chaining.

```python
agent.use(MarkdownSource("./docs"))
      .use(CsvSource("./faq.csv"))
```

---

### `.configure(...)` → `Agent`

Update pipeline and retrieval settings. Returns `self`.

```python
agent.configure(
    chunk_size=300,   # int | None
    overlap=30,       # int | None
    top_k=10,         # int | None
)
```

---

### `.set_model(provider)` → `Agent`

Replace the LLM provider. Returns `self`.

```python
from ragkit.models import OpenRouterProvider
agent.set_model(OpenRouterProvider(model="anthropic/claude-sonnet-4-5"))
```

---

### `.set_embedder(embedder)` → `Agent`

Replace the embedding provider. Returns `self`.

```python
from ragkit.embeddings import SentenceTransformerEmbedder
agent.set_embedder(SentenceTransformerEmbedder("paraphrase-multilingual-MiniLM-L12-v2"))
```

---

### `.set_store(store)` → `Agent`

Replace the vector store. Returns `self`.

```python
from ragkit.vectorstores import ChromaStore
agent.set_store(ChromaStore(collection_name="prod", persist_directory=".ragkit/chroma"))
```

---

### `.install(plugin)` → `Agent`

Register and activate a plugin.

```python
from ragkit_observability import ObservabilityPlugin
agent.install(ObservabilityPlugin())
```

---

### `.on(event)` → decorator

Register a hook function for a lifecycle event.

```python
@agent.on("before_generate")
def my_hook(prompt: str) -> None:
    ...
```

Available events: `before_index`, `before_generate`, `after_generate`, `after_response`.

---

### `.index()` → `list[Document]`

Load all sources, clean, chunk, embed, and store. Returns the list of indexed chunks.

```python
chunks = agent.index()
print(f"Indexed {len(chunks)} chunks")
```

!!! warning
    Calling `index()` without any `.use()` source returns an empty list and logs a warning.

---

### `.sync()` → `list[Document]`

Call `source.sync()` on all sources, then re-index. Returns chunks.

```python
agent.sync()
```

---

### `.ask(query)` → `str`

Embed the query, retrieve context, build a prompt, and return the LLM's answer.

```python
response = agent.ask("What is the refund policy?")
```

---

### `.stream(query)` → `AsyncIterator[str]`

Same as `ask()` but yields tokens as they stream from the LLM.

```python
async for token in agent.stream("Explain the onboarding flow"):
    print(token, end="", flush=True)
```

---

## `Document`

The core data object passed through the pipeline.

```python
from ragkit.core.base import Document

doc = Document(
    content="The text content.",
    metadata={"source": "file.md", "type": "markdown"},
    id=None,          # str | None — auto-generated during indexing
    embedding=None,   # list[float] | None — filled during indexing
)
```

---

## Sources

### `MarkdownSource(path)`

```python
MarkdownSource(path: str | Path)
```

### `TxtSource(path)`

```python
TxtSource(path: str | Path)
```

### `JsonSource(path, content_key="content")`

```python
JsonSource(path: str | Path, content_key: str = "content")
```

### `CsvSource(path, content_column=None)`

```python
CsvSource(path: str | Path, content_column: str | None = None)
```

### `RestSource(url, ...)`

```python
RestSource(
    url: str,
    content_key: str = "content",
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    timeout: int = 30,
)
```

Raises `RestSourceError` on network failure, HTTP error, or invalid JSON.

### `DirectorySource(path, extensions=None)`

```python
DirectorySource(
    path: str | Path,
    extensions: set[str] | None = None,  # default: {".md", ".txt", ".json", ".csv"}
)
```

---

## Embeddings

### `SentenceTransformerEmbedder(model_name)`

```python
from ragkit.embeddings import SentenceTransformerEmbedder

embedder = SentenceTransformerEmbedder(
    model_name: str = "all-MiniLM-L6-v2"
)
```

Model is lazy-loaded on first call to `.embed()`.

---

## Vector Stores

### `ChromaStore(collection_name, persist_directory)`

```python
from ragkit.vectorstores import ChromaStore

store = ChromaStore(
    collection_name: str = "ragkit",
    persist_directory: str = ".ragkit/chroma",
)
```

---

## Models

### `OpenRouterProvider(...)`

```python
from ragkit.models import OpenRouterProvider

provider = OpenRouterProvider(
    model: str = "openai/gpt-4o-mini",
    api_key: str | None = None,       # falls back to $OPENROUTER_API_KEY
    base_url: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
)
```

Raises `OpenRouterError` on API key issues, HTTP errors, or network failures.

---

## Base classes

Implement these to create custom components:

### `SourceAdapter`

```python
from ragkit.core.base import SourceAdapter, Document

class MySource(SourceAdapter):
    def load(self) -> list[Document]: ...
    def transform(self, docs: list[Document]) -> list[Document]: ...  # optional
    def sync(self) -> None: ...                                        # optional
```

### `EmbeddingProvider`

```python
from ragkit.core.base import EmbeddingProvider

class MyEmbedder(EmbeddingProvider):
    def embed(self, texts: list[str]) -> list[list[float]]: ...
```

### `VectorStore`

```python
from ragkit.core.base import VectorStore, Document

class MyStore(VectorStore):
    def insert(self, docs: list[Document]) -> None: ...
    def search(self, query_vec: list[float], top_k: int = 5) -> list[Document]: ...
    def clear(self) -> None: ...  # optional
```

### `ModelProvider`

```python
from ragkit.core.base import ModelProvider
from typing import AsyncIterator

class MyProvider(ModelProvider):
    def generate(self, prompt: str) -> str: ...
    async def stream(self, prompt: str) -> AsyncIterator[str]: ...
```

### `Plugin`

```python
from ragkit.core.base import Plugin

class MyPlugin(Plugin):
    def register(self, agent) -> None:
        agent.on("before_generate")(self.my_hook)
```

---

## `ProjectConfig`

```python
from ragkit.core.config import ProjectConfig, ModelConfig, PipelineConfig, RetrievalConfig, CacheConfig

config = ProjectConfig(
    name="my-app",
    model=ModelConfig(provider="openrouter", model="openai/gpt-4o-mini"),
    pipeline=PipelineConfig(chunk_size=500, overlap=50),
    retrieval=RetrievalConfig(top_k=5, method="vector"),
    cache=CacheConfig(enabled=True, ttl=3600, directory=".ragkit"),
)
```
