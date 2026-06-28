# Configuration

RAGKit is configured via two files: `rag.yaml` for project settings and `.env` for secrets.

---

## rag.yaml

Full reference with all available options:

```yaml
project:
  name: my-app              # Project name (used in logs)

model:
  provider: openrouter      # Only supported provider (required)
  model: openai/gpt-4o-mini # Model slug from OpenRouter catalog

pipeline:
  chunk_size: 500           # Max characters per chunk
  overlap: 50               # Overlap between consecutive chunks

retrieval:
  top_k: 5                  # Number of chunks retrieved per query
  method: vector            # "vector" (default) | "hybrid" (coming V0.2)

cache:
  enabled: true             # Enable embedding + query cache
  ttl: 3600                 # Cache TTL in seconds (1 hour default)
  directory: .ragkit        # Root directory for all cache data
```

### Defaults

If `rag.yaml` is absent or a key is omitted, RAGKit uses these defaults:

| Key | Default |
|---|---|
| `model.model` | `openai/gpt-4o-mini` |
| `pipeline.chunk_size` | `500` |
| `pipeline.overlap` | `50` |
| `retrieval.top_k` | `5` |
| `cache.enabled` | `true` |
| `cache.ttl` | `3600` |
| `cache.directory` | `.ragkit` |

---

## Environment variables (.env)

| Variable | Required | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | **Yes** | Your OpenRouter API key |
| `OPENROUTER_BASE_URL` | No | Override the API base URL (default: `https://openrouter.ai/api/v1`) |

RAGKit automatically loads `.env` from the current directory via `pydantic-settings`. You can also export variables directly in your shell.

```bash
export OPENROUTER_API_KEY=sk-or-v1-...
```

---

## Programmatic configuration

You can bypass `rag.yaml` entirely and configure the agent in Python:

```python
from ragkit import Agent
from ragkit.core.config import ProjectConfig

config = ProjectConfig()
config.model.model = "anthropic/claude-sonnet-4-5"
config.pipeline.chunk_size = 300
config.retrieval.top_k = 8
config.cache.enabled = False

agent = Agent(config=config)
```

Or load a custom config file:

```python
agent = Agent(config="path/to/my-config.yaml")
```

---

## Cache directory layout

All cache and index data is stored under `cache.directory` (default `.ragkit`):

```
.ragkit/
├── chroma/         ← Chroma vector store (persisted)
├── embeddings/     ← Embedding cache (diskcache SQLite)
└── queries/        ← Query response cache (diskcache SQLite)
```

To reset completely:

```bash
rm -rf .ragkit/
rag index
```

---

## Multiple environments

Use different config files per environment:

```bash
rag index --config rag.prod.yaml
rag ask "..." --config rag.staging.yaml
```
