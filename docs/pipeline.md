# Pipeline

The RAGKit pipeline transforms raw documents into searchable vector chunks, then retrieves and generates answers at query time.

---

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  INDEXING  (runs once, or on sync)                              │
│                                                                 │
│  Source.load() → Cleaner → Chunker → Embedder → VectorStore    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  QUERYING  (runs on every ask())                                │
│                                                                 │
│  Query → Embedder → VectorStore.search() → PromptBuilder → LLM │
└─────────────────────────────────────────────────────────────────┘
```

---

## Indexing

### 1. Load

Each source's `load()` method returns a list of `Document` objects with raw text and metadata.

### 2. Clean

The `Cleaner` normalizes text before chunking:

- Collapses 3+ consecutive newlines into 2
- Collapses multiple spaces into one
- Strips leading/trailing whitespace

### 3. Chunk

The `Chunker` splits long documents into overlapping segments.

```python
agent.configure(
    chunk_size=500,   # max characters per chunk
    overlap=50,       # overlap between consecutive chunks
)
```

**Chunking strategy:** RAGKit tries to break at sentence (`. `) or paragraph (`\n`) boundaries. If no natural boundary is found, it breaks at the last space.

**Example:** A 1200-character document with `chunk_size=500, overlap=50` produces:

```
Chunk 1: chars 0–500
Chunk 2: chars 450–950    (50 char overlap)
Chunk 3: chars 900–1200
```

Each chunk carries the source document's metadata plus a `chunk_index`.

### 4. Embed

The `Embedder` converts each chunk's text into a dense vector.

Default: `SentenceTransformerEmbedder("all-MiniLM-L6-v2")` — a lightweight local model (~90MB, 384-dimensional embeddings).

```python
from ragkit.embeddings import SentenceTransformerEmbedder

agent.set_embedder(SentenceTransformerEmbedder("paraphrase-multilingual-MiniLM-L12-v2"))
```

The model is **lazy-loaded** on first use and cached in memory for subsequent calls.

### 5. Store

Embedded chunks are upserted into the vector store with their text and metadata.

```python
from ragkit.vectorstores import ChromaStore

agent.set_store(ChromaStore(
    collection_name="my-project",
    persist_directory=".ragkit/chroma",
))
```

---

## Querying

### 1. Embed the query

The user's question is embedded with the same model used at index time.

### 2. Retrieve

Top-k most similar chunks are retrieved by cosine similarity.

```python
agent.configure(top_k=5)   # retrieve 5 chunks
```

### 3. Build the prompt

RAGKit constructs a prompt with the retrieved context:

```
Use the following context to answer the question.

Context:
[chunk 1 content]

---

[chunk 2 content]

---

[chunk 3 content]

Question: <your question>

Answer:
```

### 4. Generate

The prompt is sent to OpenRouter. The response is returned as a string or streamed token by token.

---

## Cache

Two caching layers reduce latency and cost:

| Cache | What it stores | Key |
|---|---|---|
| **Embedding cache** | Vector for a given text | SHA-256 of text |
| **Query cache** | LLM response for a query + context | SHA-256 of query + context |

Both caches are disk-based (`diskcache` SQLite), persistent across runs, and stored under `cache.directory`.

```python
# Disable cache
from ragkit.core.config import ProjectConfig
config = ProjectConfig()
config.cache.enabled = False
agent = Agent(config=config)
```

---

## Hooks

Intercept any stage of the pipeline:

```python
@agent.on("before_index")
def on_before_index(docs):
    print(f"About to index {len(docs)} documents")

@agent.on("before_generate")
def on_before_generate(prompt):
    print(f"Prompt length: {len(prompt)} chars")

@agent.on("after_generate")
def on_after_generate(response):
    print(f"Response: {response[:80]}...")

@agent.on("after_response")
def on_after_response(response):
    # Final hook — after cache write
    save_to_db(response)
```

Available hooks:

| Hook | When | Arguments |
|---|---|---|
| `before_index` | Before indexing starts | `docs: list[Document]` |
| `before_generate` | Before LLM call | `prompt: str` |
| `after_generate` | After LLM returns | `response: str` |
| `after_response` | After cache write | `response: str` |
