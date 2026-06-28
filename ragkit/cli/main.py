from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(name="rag", help="RAGKit CLI — universal RAG framework")


@app.command()
def init(
    name: str = typer.Option("my-rag-app", help="Project name"),
    directory: Path = typer.Argument(Path("."), help="Target directory"),
) -> None:
    """Initialize a new RAGKit project."""
    config_path = directory / "rag.yaml"
    if config_path.exists():
        typer.echo(f"rag.yaml already exists in {directory}")
        raise typer.Exit(1)

    config_path.write_text(
        f"""project:
  name: {name}

model:
  provider: openrouter
  model: openai/gpt-4o-mini

sources:
  - markdown

pipeline:
  chunk_size: 500
  overlap: 50

retrieval:
  top_k: 5
  method: vector

cache:
  enabled: true
  ttl: 3600
""",
        encoding="utf-8",
    )

    env_path = directory / ".env"
    if not env_path.exists():
        env_path.write_text("OPENROUTER_API_KEY=\n", encoding="utf-8")

    typer.echo(f"Initialized RAGKit project '{name}' in {directory}")
    typer.echo("Edit rag.yaml and set OPENROUTER_API_KEY in .env to get started.")


@app.command()
def sync(config: Path = typer.Option(Path("rag.yaml"), help="Config file")) -> None:
    """Sync all sources and re-index."""
    from ragkit.agent import Agent

    agent = Agent(config=config)
    typer.echo("Syncing sources...")
    chunks = agent.sync()
    typer.echo(f"Indexed {len(chunks)} chunks.")


@app.command()
def index(config: Path = typer.Option(Path("rag.yaml"), help="Config file")) -> None:
    """Index all configured sources."""
    from ragkit.agent import Agent

    agent = Agent(config=config)
    typer.echo("Indexing sources...")
    chunks = agent.index()
    typer.echo(f"Indexed {len(chunks)} chunks.")


@app.command()
def ask(
    query: str = typer.Argument(..., help="Question to ask"),
    config: Path = typer.Option(Path("rag.yaml"), help="Config file"),
) -> None:
    """Ask a question using the RAG pipeline."""
    from ragkit.agent import Agent

    agent = Agent(config=config)
    response = agent.ask(query)
    typer.echo(response)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Host"),
    port: int = typer.Option(8000, help="Port"),
    config: Path = typer.Option(Path("rag.yaml"), help="Config file"),
) -> None:
    """Start a simple HTTP server exposing /ask endpoint."""
    try:
        import uvicorn
        from fastapi import FastAPI
        from pydantic import BaseModel
    except ImportError:
        typer.echo("Install fastapi and uvicorn to use rag serve: pip install fastapi uvicorn")
        raise typer.Exit(1)

    from ragkit.agent import Agent

    agent = Agent(config=config)
    api = FastAPI(title="RAGKit Server")

    class AskRequest(BaseModel):
        query: str

    @api.post("/ask")
    def ask_endpoint(req: AskRequest):
        return {"response": agent.ask(req.query)}

    typer.echo(f"Starting RAGKit server on {host}:{port}")
    uvicorn.run(api, host=host, port=port)


@app.command()
def dev(config: Path = typer.Option(Path("rag.yaml"), help="Config file")) -> None:
    """Interactive REPL for development."""
    from ragkit.agent import Agent

    agent = Agent(config=config)
    typer.echo("RAGKit dev mode. Type 'exit' to quit.\n")
    while True:
        try:
            query = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            break
        if not query or query.lower() in ("exit", "quit"):
            break
        try:
            response = agent.ask(query)
            typer.echo(f"Agent: {response}\n")
        except Exception as e:
            typer.echo(f"Error: {e}\n")
