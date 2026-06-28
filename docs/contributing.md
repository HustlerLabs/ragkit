# Contributing

RAGKit is open source under the MIT License. Contributions of all kinds are welcome.

---

## Quick start

```bash
git clone https://github.com/your-org/ragkit.git
cd ragkit
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

---

## Project structure

```
ragkit/
├── agent.py              # Agent facade (main entry point)
├── cli/
│   └── main.py           # Typer CLI commands
├── core/
│   ├── base.py           # ABCs: SourceAdapter, EmbeddingProvider, VectorStore, ModelProvider, Plugin
│   ├── config.py         # ProjectConfig (pydantic), Settings (pydantic-settings)
│   ├── hooks.py          # HookRegistry
│   └── registry.py       # PluginRegistry (entry_points discovery)
├── sources/              # Built-in source adapters
├── embeddings/           # Embedding providers
├── vectorstores/         # Vector store implementations
├── models/               # LLM providers
├── pipeline/             # Chunker, Cleaner
└── cache/                # CachedEmbedder, QueryCache
tests/
├── unit/                 # Unit tests (all dependencies mocked)
└── scripts/              # Bash smoke tests
docs/                     # MkDocs documentation source
```

---

## Running the tests

```bash
# All unit tests
pytest tests/unit/ -v

# With coverage
pytest tests/unit/ --cov=ragkit --cov-report=term-missing

# Bash smoke tests (CLI must be installed)
bash tests/scripts/test_cli_smoke.sh

# Embeddings smoke test (requires sentence-transformers)
bash tests/scripts/test_embeddings_smoke.sh
```

---

## Code style

We use `ruff` for linting and formatting:

```bash
# Check
ruff check .

# Auto-fix
ruff check . --fix

# Format
ruff format .
```

---

## Adding a source

1. Create `ragkit/sources/my_source.py`
2. Implement `SourceAdapter` from `ragkit.core.base`
3. Export from `ragkit/sources/__init__.py`
4. Export from `ragkit/__init__.py`
5. Add unit tests in `tests/unit/test_sources.py`
6. Document in `docs/sources.md`

Minimal example:

```python
from pathlib import Path
from ragkit.core.base import SourceAdapter, Document

class RstSource(SourceAdapter):
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def load(self) -> list[Document]:
        files = [self._path] if self._path.is_file() else list(self._path.rglob("*.rst"))
        docs = []
        for f in files:
            docs.append(Document(
                content=f.read_text(encoding="utf-8"),
                metadata={"source": str(f.resolve()), "type": "rst"},
            ))
        return docs
```

---

## Adding a model provider

1. Create `ragkit/models/my_provider.py`
2. Implement `ModelProvider` from `ragkit.core.base`
3. Export from `ragkit/models/__init__.py`
4. Add unit tests
5. Document in `docs/models.md`

---

## Pull request checklist

- [ ] Tests pass: `pytest tests/unit/ -v`
- [ ] Linter clean: `ruff check .`
- [ ] New code is covered by tests
- [ ] Public API documented in the relevant `docs/*.md` page
- [ ] Commit message is descriptive

---

## Reporting bugs

Open an issue on GitHub with:

- RAGKit version (`pip show ragkit`)
- Python version (`python --version`)
- Steps to reproduce
- Expected vs actual behavior

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
