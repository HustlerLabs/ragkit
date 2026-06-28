"""Demo rapide — indexe les docs et pose 3 questions."""

from ragkit import Agent, MarkdownSource
from ragkit.models import OpenRouterProvider

agent = Agent()
agent.set_model(OpenRouterProvider(model="cohere/north-mini-code:free"))
agent.use(MarkdownSource("./docs"))

print("Indexing docs...")
chunks = agent.index()
print(f"Indexed {len(chunks)} chunks\n")

questions = [
    "What is RAGKit?",
    "How do I add a custom source?",
    "What CLI commands are available?",
]

for q in questions:
    print(f"Q: {q}")
    answer = agent.ask(q)
    print(f"A: {answer}\n{'-'*60}\n")
