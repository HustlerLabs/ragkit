"""
Example 1 — Markdown documentation chatbot.

Index a folder of Markdown docs and answer questions about them.

Setup:
    pip install ragkit
    export OPENROUTER_API_KEY=your-key

Usage:
    python examples/01_markdown_chatbot.py
"""

from ragkit import Agent, MarkdownSource

# Point to a folder of Markdown files (or a single .md file)
DOCS_PATH = "./docs"

agent = Agent()
agent.use(MarkdownSource(DOCS_PATH))

print("Indexing docs...")
chunks = agent.index()
print(f"Indexed {len(chunks)} chunks from {DOCS_PATH}\n")

# Single question
answer = agent.ask("What is RAGKit?")
print(f"Answer: {answer}\n")

# Interactive loop
print("Chat mode — type 'exit' to quit.")
while True:
    query = input("You: ").strip()
    if not query or query.lower() in ("exit", "quit"):
        break
    response = agent.ask(query)
    print(f"Agent: {response}\n")
