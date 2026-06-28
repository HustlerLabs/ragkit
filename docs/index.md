# RAGKit

**Universal RAG framework SDK for Python.**

RAGKit gives you a complete [Retrieval-Augmented Generation](https://en.wikipedia.org/wiki/Retrieval-augmented_generation) pipeline in a few lines of code. Plug in your data sources — RAGKit handles chunking, embedding, vector storage, retrieval, and LLM generation.

---

## Why RAGKit?

Building a RAG system from scratch means assembling a dozen libraries, writing the same boilerplate pipeline in every project, and debugging the gaps between them. RAGKit collapses that into a single, composable SDK.

```python
from ragkit import Agent, MarkdownSource

agent = Agent()
agent.use(MarkdownSource("./docs"))
agent.index()

print(agent.ask("How does authentication work?"))
```

---

## Architecture

```
Your Data Sources
      ↓
  Source Loader  →  Cleaner  →  Chunker  →  Embedder  →  Vector Store
                                                               ↓
Your Question  →  Embedder  →  Retriever  →  Prompt Builder  →  OpenRouter  →  Answer
```

Every component is replaceable. Swap the vector store, the embedder, the model — RAGKit's interfaces keep everything wired together.

---

## Key Features

| | |
|---|---|
| **Sources** | Markdown, TXT, JSON, CSV, REST API, Directory |
| **Embeddings** | Sentence Transformers (local), more via plugins |
| **Vector stores** | Chroma (default), Qdrant |
| **LLMs** | OpenRouter — 100+ models in a single API |
| **Streaming** | Async token streaming |
| **Cache** | Embedding cache + query cache (disk-based) |
| **Hooks** | `before_generate`, `after_generate`, `after_response` |
| **Plugins** | `pip install ragkit-pdf` pattern |
| **CLI** | `rag init / index / sync / ask / dev / serve` |

---

## Navigation

<div class="grid cards" markdown>

- :material-rocket-launch: **[Quick Start](quickstart.md)**

    Get your first agent running in 5 minutes.

- :material-cog: **[Configuration](configuration.md)**

    Full reference for `rag.yaml` and environment variables.

- :material-database: **[Sources](sources.md)**

    Connect Markdown, CSV, REST APIs, and more.

- :material-chip: **[Pipeline](pipeline.md)**

    How chunking, embedding, and indexing work.

- :material-robot: **[Models](models.md)**

    Configure OpenRouter and choose your LLM.

- :material-console: **[CLI](cli.md)**

    Complete CLI command reference.

- :material-puzzle: **[Plugins](plugins.md)**

    Build and publish your own RAGKit plugin.

- :material-code-tags: **[API Reference](api-reference.md)**

    Full Python API documentation.

</div>
