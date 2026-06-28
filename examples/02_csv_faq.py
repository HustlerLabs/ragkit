"""
Example 2 — CSV-based FAQ assistant with streaming.

Loads a CSV where each row is a Q&A pair, indexes it, and answers
questions with streaming output.

CSV format expected:
    question,answer
    "How do I reset my password?","Go to Settings > Security > Reset password."
    ...

Setup:
    pip install ragkit
    export OPENROUTER_API_KEY=your-key

Usage:
    python examples/02_csv_faq.py
"""

import asyncio
import csv
import tempfile
from pathlib import Path

from ragkit import Agent, CsvSource
from ragkit.core.config import ProjectConfig


def create_sample_faq(path: Path) -> None:
    rows = [
        ("question", "answer"),
        ("How do I reset my password?", "Go to Settings > Security > Reset password. You'll receive an email with a reset link."),
        ("What payment methods do you accept?", "We accept Visa, Mastercard, PayPal, and bank transfers."),
        ("How do I cancel my subscription?", "You can cancel anytime from your account dashboard under Billing > Cancel plan."),
        ("Is there a free trial?", "Yes, we offer a 14-day free trial with full access to all features."),
        ("How do I contact support?", "Email us at support@example.com or use the live chat in the bottom right corner."),
    ]
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


async def main() -> None:
    # Create a sample FAQ CSV
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        faq_path = Path(f.name)
    create_sample_faq(faq_path)

    # Configure agent
    config = ProjectConfig()
    config.cache.enabled = False  # disable cache for demo

    agent = Agent(config=config)
    agent.use(CsvSource(faq_path, content_column="answer"))
    agent.configure(top_k=3)

    # Add a hook to log retrieval
    @agent.on("before_generate")
    def log_context(prompt: str) -> None:
        lines = prompt.split("\n")
        context_lines = [l for l in lines if l.startswith("- ") or "Context:" in l]
        print(f"[retrieved {len(context_lines)} context chunks]")

    print("Indexing FAQ...")
    agent.index()
    print("Ready.\n")

    queries = [
        "How can I cancel?",
        "Do you have a trial period?",
        "I forgot my password, what do I do?",
    ]

    for query in queries:
        print(f"Q: {query}")
        print("A: ", end="", flush=True)
        async for token in agent.stream(query):
            print(token, end="", flush=True)
        print("\n")

    faq_path.unlink()


if __name__ == "__main__":
    asyncio.run(main())
