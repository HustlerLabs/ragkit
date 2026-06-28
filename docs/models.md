# Models

RAGKit generates answers via **[OpenRouter](https://openrouter.ai)** — a unified API that gives access to 100+ LLMs from a single endpoint.

---

## Why OpenRouter?

- **One API key** for GPT-4o, Claude, Gemini, Llama, Mistral, and more
- **Competitive pricing** — pay per token, no subscriptions
- **Fallback routing** — automatic failover between providers
- **Free tier** — several models available at no cost

---

## Default model

RAGKit defaults to `openai/gpt-4o-mini` — a fast and affordable model suitable for most RAG use cases.

Change it in `rag.yaml`:

```yaml
model:
  provider: openrouter
  model: anthropic/claude-sonnet-4-5
```

Or in Python:

```python
from ragkit.models import OpenRouterProvider

agent.set_model(OpenRouterProvider(model="anthropic/claude-sonnet-4-5"))
```

---

## Configuration

```python
from ragkit.models import OpenRouterProvider

provider = OpenRouterProvider(
    model="openai/gpt-4o",
    api_key="sk-or-v1-...",    # or set OPENROUTER_API_KEY in .env
    temperature=0.3,            # 0.0 = deterministic, 1.0 = creative
    max_tokens=2048,            # max response length
)

agent.set_model(provider)
```

| Parameter | Default | Description |
|---|---|---|
| `model` | `openai/gpt-4o-mini` | Model slug |
| `api_key` | `$OPENROUTER_API_KEY` | API key |
| `temperature` | `0.7` | Creativity (0–1) |
| `max_tokens` | `2048` | Max response tokens |

---

## Recommended models

| Use case | Model | Notes |
|---|---|---|
| Default / budget | `openai/gpt-4o-mini` | Fast, cheap, reliable |
| Best quality | `anthropic/claude-sonnet-4-5` | Best for long context |
| Open source | `meta-llama/llama-3.3-70b-instruct` | Free on many providers |
| Coding | `openai/gpt-4o` | Strong reasoning |
| Multilingual | `google/gemini-2.0-flash-exp` | 100+ languages |
| Free | `mistralai/mistral-7b-instruct:free` | No cost, limited rate |

Browse the full catalog at [openrouter.ai/models](https://openrouter.ai/models).

---

## Streaming

```python
import asyncio

async def main():
    agent = Agent()
    agent.use(MarkdownSource("./docs"))
    agent.index()

    print("Answer: ", end="", flush=True)
    async for token in agent.stream("Explain the architecture"):
        print(token, end="", flush=True)
    print()

asyncio.run(main())
```

---

## Error handling

`OpenRouterProvider` raises `OpenRouterError` for actionable failures:

```python
from ragkit.models.openrouter import OpenRouterError

try:
    response = agent.ask("hello")
except OpenRouterError as e:
    print(f"LLM error: {e}")
```

| Situation | Error message |
|---|---|
| Empty API key | `OPENROUTER_API_KEY is not set.` |
| Invalid key (401) | `Invalid API key (401).` |
| Rate limit (429) | `Rate limit exceeded (429). Retry later.` |
| Timeout | `Request timed out after 60s.` |
| Network down | `Network error: ...` |

---

## Custom model provider

Implement `ModelProvider` to use any LLM:

```python
from ragkit.core.base import ModelProvider
from typing import AsyncIterator

class MyProvider(ModelProvider):
    def generate(self, prompt: str) -> str:
        # call your LLM
        return my_llm.complete(prompt)

    async def stream(self, prompt: str) -> AsyncIterator[str]:
        async for token in my_llm.stream(prompt):
            yield token

agent.set_model(MyProvider())
```
