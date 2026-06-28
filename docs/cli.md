# CLI Reference

RAGKit ships with a full command-line interface. All commands read `rag.yaml` from the current directory by default.

```bash
rag --help
python -m ragkit --help   # equivalent
```

---

## `rag init`

Initialize a new RAGKit project in a directory.

```bash
rag init [DIRECTORY] [--name PROJECT_NAME]
```

**Arguments:**

| Argument | Default | Description |
|---|---|---|
| `DIRECTORY` | `.` (current dir) | Target directory |
| `--name` | `my-rag-app` | Project name written to `rag.yaml` |

**Creates:**

- `rag.yaml` — project configuration
- `.env` — environment variables file (if not already present)

**Example:**

```bash
mkdir my-app && rag init my-app --name my-app
```

---

## `rag index`

Load all sources and index them into the vector store.

```bash
rag index [--config PATH]
```

| Option | Default | Description |
|---|---|---|
| `--config` | `rag.yaml` | Path to config file |

Run this after adding new documents or changing sources.

```bash
rag index
# Indexing sources...
# Indexed 142 chunks.
```

---

## `rag sync`

Sync all sources (calls `source.sync()`) then re-index.

```bash
rag sync [--config PATH]
```

Use `sync` when your sources can pull new data (e.g. a REST API with new records). For static files, `sync` and `index` are equivalent.

---

## `rag ask`

Ask a one-shot question and print the answer.

```bash
rag ask "QUERY" [--config PATH]
```

**Example:**

```bash
rag ask "What is the refund policy?"
# You can request a refund within 30 days of purchase...
```

---

## `rag dev`

Start an interactive REPL.

```bash
rag dev [--config PATH]
```

```
RAGKit dev mode. Type 'exit' to quit.

You: How does authentication work?
Agent: Authentication uses Bearer tokens...

You: What models are supported?
Agent: RAGKit supports any model available on OpenRouter...

You: exit
```

Type `exit` or `quit` to stop. `Ctrl+C` or EOF also exits cleanly.

---

## `rag serve`

Start an HTTP server with a `/ask` endpoint.

```bash
rag serve [--host HOST] [--port PORT] [--config PATH]
```

| Option | Default | Description |
|---|---|---|
| `--host` | `127.0.0.1` | Bind address |
| `--port` | `8000` | Port |
| `--config` | `rag.yaml` | Config file |

**Requires the `serve` extra:**

```bash
pip install ragkit-sdk[serve]
```

**Usage:**

```bash
rag serve --host 0.0.0.0 --port 8080
# Starting RAGKit server on 0.0.0.0:8080
```

**Query the API:**

```bash
curl -X POST http://localhost:8080/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "How does authentication work?"}'

# {"response": "Authentication uses Bearer tokens..."}
```

---

## Global options

| Option | Description |
|---|---|
| `--help` | Show help and exit |
| `--install-completion` | Install shell tab completion |
| `--show-completion` | Show completion script |

---

## Using a custom config file

All commands accept `--config`:

```bash
rag index --config config/production.yaml
rag ask "hello" --config config/staging.yaml
```
