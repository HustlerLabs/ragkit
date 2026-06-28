# RAGKit

**Universal RAG (Retrieval-Augmented Generation) framework SDK for Python.**

Build AI-powered assistants, document search, and FAQ systems in minutes — without rewriting the pipeline for every project.

[![CI](https://github.com/HustlerLabs/ragkit/actions/workflows/ci.yml/badge.svg)](https://github.com/HustlerLabs/ragkit/actions)
[![Coverage](https://img.shields.io/badge/coverage-98%25-brightgreen)](https://github.com/HustlerLabs/ragkit)
[![PyPI](https://img.shields.io/pypi/v/ragkit)](https://pypi.org/project/ragkit/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

---

## What is RAGKit?

RAGKit is an open-source Python SDK that gives you a complete **Retrieval-Augmented Generation** pipeline in a few lines of code.

You plug in your data sources, RAGKit handles the rest: chunking, embedding, vector storage, retrieval, and LLM generation via [OpenRouter](https://openrouter.ai).

```
Your Data → RAGKit → Answer
```

---

## Quick Start

```bash
pip install ragkit
rag init
```

Add your API key to `.env`:

```env
OPENROUTER_API_KEY=your-key-here
```

Build your first agent:

```python
from ragkit import Agent, MarkdownSource

agent = Agent()
agent.use(MarkdownSource("./docs"))
agent.index()

print(agent.ask("How does authentication work?"))
```

That's it. **No vector database setup. No embedding model download configuration. No prompt engineering.**

---

## Features

- **6 built-in sources** — Markdown, TXT, JSON, CSV, REST API, Directory
- **Automatic pipeline** — load → clean → chunk → embed → index
- **Semantic search** — Chroma or Qdrant vector store
- **100+ LLMs** — via OpenRouter (GPT-4o, Claude, Gemini, Llama…)
- **Streaming** — async token-by-token output
- **Cache** — embeddings and query results cached on disk
- **Hooks** — intercept before/after generate and response
- **Plugin system** — `pip install ragkit-pdf` to add PDF support
- **CLI** — `rag init`, `rag index`, `rag ask`, `rag dev`, `rag serve`

---

## Installation

```bash
pip install ragkit
```

**Optional extras:**

```bash
pip install ragkit[serve]    # HTTP server (FastAPI + uvicorn)
pip install ragkit[qdrant]   # Qdrant vector store
```

---

## Usage Examples

### Multiple sources

```python
from ragkit import Agent, MarkdownSource, CsvSource, RestSource

agent = Agent()
agent.use(MarkdownSource("./docs"))
agent.use(CsvSource("./faq.csv", content_column="answer"))
agent.use(RestSource("https://api.example.com/kb", content_key="body"))

agent.index()
print(agent.ask("What is the return policy?"))
```

### Streaming

```python
import asyncio

async def main():
    agent = Agent()
    agent.use(MarkdownSource("./docs"))
    agent.index()

    async for token in agent.stream("Summarize the onboarding guide"):
        print(token, end="", flush=True)

asyncio.run(main())
```

### Custom model

```python
from ragkit import Agent
from ragkit.models import OpenRouterProvider

agent = Agent()
agent.set_model(OpenRouterProvider(
    model="anthropic/claude-sonnet-4-5",
    temperature=0.3,
))
```

### Hooks

```python
@agent.on("before_generate")
def log_prompt(prompt: str) -> None:
    print(f"Sending {len(prompt)} chars to LLM")

@agent.on("after_response")
def save_answer(response: str) -> None:
    with open("answers.log", "a") as f:
        f.write(response + "\n")
```

### Extend with a custom source

```python
from ragkit.core.base import SourceAdapter, Document

class NotionSource(SourceAdapter):
    def load(self) -> list[Document]:
        # fetch from Notion API
        ...

agent.use(NotionSource())
```

---

## CLI

```bash
rag init                        # Initialize a new project (rag.yaml + .env)
rag index                       # Index all configured sources
rag sync                        # Sync sources and re-index
rag ask "What is X?"            # One-shot question
rag dev                         # Interactive REPL
rag serve --host 0.0.0.0        # HTTP API on /ask
```

---

## Documentation

Full documentation: **[hustlerlabs.github.io/ragkit](https://hustlerlabs.github.io/ragkit)**

- [Quick Start](docs/quickstart.md)
- [Configuration reference](docs/configuration.md)
- [Sources guide](docs/sources.md)
- [API reference](docs/api-reference.md)
- [Plugin development](docs/plugins.md)

---

## Roadmap

| Version | Features |
|---|---|
| **V0.1** ✅ | Core pipeline, 6 sources, Chroma, OpenRouter, CLI, cache, hooks, plugins |
| **V0.2** | Hybrid search (BM25 + vector), streaming CLI, plugin PDF |
| **V0.3** | PostgreSQL, MongoDB sources |
| **V0.5** | Observability (cost tracking, latency dashboard) |
| **V1.0** | Stable API, full docs site |

---

## Contributing

Contributions are welcome. See [CONTRIBUTING](docs/contributing.md) for guidelines.

```bash
git clone https://github.com/HustlerLabs/ragkit
cd ragkit
pip install -e ".[dev]"
pytest tests/
```

---

## License

MIT — see [LICENSE](LICENSE).
