# Plugin Development

RAGKit's plugin system lets you extend the framework and share reusable integrations with the community.

---

## What plugins can do

A plugin receives the `Agent` instance at registration time and can:

- Register hooks (`before_index`, `before_generate`, `after_generate`, `after_response`)
- Swap components (`set_model`, `set_embedder`, `set_store`)
- Add custom sources
- Wrap existing methods

---

## Writing a plugin

Implement the `Plugin` ABC from `ragkit.core.base`:

```python
from ragkit.core.base import Plugin

class LoggingPlugin(Plugin):
    def register(self, agent) -> None:
        agent.on("before_generate")(self._log_prompt)
        agent.on("after_response")(self._log_response)

    def _log_prompt(self, prompt: str) -> None:
        print(f"[LoggingPlugin] Prompt ({len(prompt)} chars)")

    def _log_response(self, response: str) -> None:
        print(f"[LoggingPlugin] Response ({len(response)} chars)")
```

Install it:

```python
from ragkit import Agent
from my_package import LoggingPlugin

agent = Agent()
agent.install(LoggingPlugin())
```

---

## Available hooks

| Event | When | Argument |
|---|---|---|
| `before_index` | Before indexing documents | `docs: list[Document]` |
| `before_generate` | Before calling the LLM | `prompt: str` |
| `after_generate` | After LLM returns a response | `response: str` |
| `after_response` | After cache write, final step | `response: str` |

---

## Distributing as a PyPI package

Structure your plugin as a standard Python package:

```
ragkit-logging/
├── pyproject.toml
└── ragkit_logging/
    └── __init__.py
```

**`pyproject.toml`:**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "ragkit-logging"
version = "0.1.0"
description = "Structured logging plugin for RAGKit"
dependencies = ["ragkit>=0.1.0"]

[project.entry-points."ragkit.plugins"]
logging = "ragkit_logging:LoggingPlugin"
```

The `[project.entry-points."ragkit.plugins"]` section lets RAGKit auto-discover your plugin.

---

## Auto-discovery

RAGKit scans the `ragkit.plugins` entry point group on startup. Plugins registered there are available via the `PluginRegistry`:

```python
from ragkit.core.registry import PluginRegistry

registry = PluginRegistry()
registry.discover()         # scans installed packages

for name, plugin_class in registry.plugins.items():
    print(f"Found plugin: {name}")
    agent.install(plugin_class())
```

Manual install (without auto-discovery):

```python
from ragkit_logging import LoggingPlugin
agent.install(LoggingPlugin())
```

---

## Example: custom source plugin

A plugin can register a source adapter from a third-party library:

```python
from ragkit.core.base import Plugin, SourceAdapter, Document

class NotionPlugin(Plugin):
    def __init__(self, database_id: str, token: str) -> None:
        self.database_id = database_id
        self.token = token

    def register(self, agent) -> None:
        agent.use(NotionSource(self.database_id, self.token))


class NotionSource(SourceAdapter):
    def __init__(self, database_id: str, token: str) -> None:
        self.database_id = database_id
        self.token = token

    def load(self) -> list[Document]:
        import httpx
        resp = httpx.get(
            f"https://api.notion.com/v1/databases/{self.database_id}/query",
            headers={"Authorization": f"Bearer {self.token}", "Notion-Version": "2022-06-28"},
        )
        resp.raise_for_status()
        pages = resp.json().get("results", [])
        return [
            Document(
                content=page["properties"]["content"]["rich_text"][0]["plain_text"],
                metadata={"id": page["id"], "source": "notion"},
            )
            for page in pages
            if page["properties"].get("content")
        ]
```

Usage:

```python
agent.install(NotionPlugin(database_id="abc123", token="secret-token"))
agent.index()
```

---

## Community plugins

| Package | Description |
|---|---|
| `ragkit-pdf` | PDF file source (requires `pypdf`) |
| `ragkit-docx` | Word document source (requires `python-docx`) |
| `ragkit-notion` | Notion database source |
| `ragkit-github` | GitHub repository loader |
| `ragkit-slack` | Slack channel history |

Install any plugin via pip and it's ready to use — no configuration required.
