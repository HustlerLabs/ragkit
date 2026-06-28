# Quick Start

Get your first RAGKit agent running in under 5 minutes.

---

## Prerequisites

- Python 3.10+
- An [OpenRouter](https://openrouter.ai) API key (free tier available)

---

## 1. Install

```bash
pip install ragkit
```

---

## 2. Initialize a project

```bash
mkdir my-rag-app
cd my-rag-app
rag init
```

This creates two files:

```
my-rag-app/
├── rag.yaml    ← project configuration
└── .env        ← your API keys (never commit this)
```

---

## 3. Add your API key

Open `.env` and set your OpenRouter key:

```env
OPENROUTER_API_KEY=sk-or-v1-...
```

Get a free key at [openrouter.ai/keys](https://openrouter.ai/keys).

---

## 4. Add your data

Create a `docs/` folder and drop in some Markdown files:

```bash
mkdir docs
echo "# Authentication\nUse Bearer tokens in the Authorization header." > docs/auth.md
echo "# Pricing\nFree tier: 1000 requests/month. Pro: unlimited." > docs/pricing.md
```

---

## 5. Index your data

```bash
rag index
```

RAGKit will:

1. Load all Markdown files from `docs/`
2. Clean and chunk the text
3. Generate embeddings (downloads a small model on first run, ~100MB)
4. Store vectors in `.ragkit/chroma/`

---

## 6. Ask a question

```bash
rag ask "How do I authenticate?"
```

Or start an interactive session:

```bash
rag dev
```

```
RAGKit dev mode. Type 'exit' to quit.

You: How do I authenticate?
Agent: Use Bearer tokens in the Authorization header.

You: What's the pricing?
Agent: The free tier includes 1000 requests per month. The Pro plan offers unlimited requests.

You: exit
```

---

## 7. Use the Python API

```python
from ragkit import Agent, MarkdownSource

agent = Agent()
agent.use(MarkdownSource("./docs"))
agent.index()

response = agent.ask("How do I authenticate?")
print(response)
```

---

## Next steps

- [Configuration](configuration.md) — customize `rag.yaml`
- [Sources](sources.md) — add CSV, REST APIs, JSON data
- [Models](models.md) — switch to GPT-4o, Claude, or Llama
- [CLI](cli.md) — full CLI reference

---

## Troubleshooting

??? question "The model download takes too long"
    On the first run, RAGKit downloads the `all-MiniLM-L6-v2` embedding model (~90MB).
    This only happens once. Subsequent runs use the cached version.

??? question "I get a 401 error"
    Your `OPENROUTER_API_KEY` is missing or invalid.
    Check that your `.env` file contains the key and that it is correct.

??? question "`rag: command not found`"
    Make sure you installed RAGKit in an active virtual environment:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install ragkit
    rag --help
    ```
    Or run via Python: `python -m ragkit --help`
