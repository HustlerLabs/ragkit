from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from ragkit.cli.main import app

runner = CliRunner()


class TestCliInit:
    def test_init_creates_rag_yaml(self, tmp_path):
        result = runner.invoke(app, ["init", "--name", "myapp", str(tmp_path)])
        assert result.exit_code == 0
        assert (tmp_path / "rag.yaml").exists()

    def test_init_creates_env_file(self, tmp_path):
        runner.invoke(app, ["init", str(tmp_path)])
        assert (tmp_path / ".env").exists()

    def test_init_yaml_contains_project_name(self, tmp_path):
        runner.invoke(app, ["init", "--name", "coolapp", str(tmp_path)])
        content = (tmp_path / "rag.yaml").read_text()
        assert "coolapp" in content

    def test_init_fails_if_yaml_already_exists(self, tmp_path):
        (tmp_path / "rag.yaml").write_text("existing")
        result = runner.invoke(app, ["init", str(tmp_path)])
        assert result.exit_code != 0

    def test_init_does_not_overwrite_existing_env(self, tmp_path):
        (tmp_path / ".env").write_text("EXISTING=1")
        runner.invoke(app, ["init", str(tmp_path)])
        assert "EXISTING=1" in (tmp_path / ".env").read_text()


class TestCliAsk:
    def test_ask_prints_response(self, tmp_path):
        config_path = tmp_path / "rag.yaml"
        config_path.write_text("project:\n  name: test\n")

        mock_agent = MagicMock()
        mock_agent.ask.return_value = "The answer is 42."

        with patch("ragkit.agent.Agent", return_value=mock_agent):
            result = runner.invoke(app, ["ask", "what is the answer?", "--config", str(config_path)])

        assert result.exit_code == 0
        assert "The answer is 42." in result.output

    def test_ask_passes_query_to_agent(self, tmp_path):
        config_path = tmp_path / "rag.yaml"
        config_path.write_text("project:\n  name: test\n")

        mock_agent = MagicMock()
        mock_agent.ask.return_value = "ok"

        with patch("ragkit.agent.Agent", return_value=mock_agent):
            runner.invoke(app, ["ask", "my specific query", "--config", str(config_path)])

        mock_agent.ask.assert_called_once_with("my specific query")


class TestCliIndex:
    def test_index_prints_chunk_count(self, tmp_path):
        config_path = tmp_path / "rag.yaml"
        config_path.write_text("project:\n  name: test\n")

        mock_agent = MagicMock()
        from ragkit.core.base import Document
        mock_agent.index.return_value = [Document(content="c", metadata={})] * 7

        with patch("ragkit.agent.Agent", return_value=mock_agent):
            result = runner.invoke(app, ["index", "--config", str(config_path)])

        assert "7" in result.output


class TestCliSync:
    def test_sync_calls_agent_sync(self, tmp_path):
        config_path = tmp_path / "rag.yaml"
        config_path.write_text("project:\n  name: test\n")

        mock_agent = MagicMock()
        mock_agent.sync.return_value = []

        with patch("ragkit.agent.Agent", return_value=mock_agent):
            result = runner.invoke(app, ["sync", "--config", str(config_path)])

        mock_agent.sync.assert_called_once()
        assert result.exit_code == 0


class TestCliServe:
    def test_serve_prints_error_when_deps_missing(self, tmp_path):
        config_path = tmp_path / "rag.yaml"
        config_path.write_text("project:\n  name: test\n")

        import sys
        modules_backup = {k: sys.modules.pop(k) for k in ["uvicorn", "fastapi"] if k in sys.modules}
        try:
            with patch.dict(sys.modules, {"uvicorn": None, "fastapi": None}):
                result = runner.invoke(app, ["serve", "--config", str(config_path)])
        finally:
            sys.modules.update(modules_backup)

        assert result.exit_code != 0
        assert "fastapi" in result.output.lower() or "uvicorn" in result.output.lower()

    def test_serve_starts_server_when_deps_present(self, tmp_path):
        config_path = tmp_path / "rag.yaml"
        config_path.write_text("project:\n  name: test\n")

        mock_uvicorn = MagicMock()
        mock_fastapi_cls = MagicMock()
        mock_fastapi_cls.return_value = MagicMock()
        mock_base_model = MagicMock()

        mock_agent = MagicMock()
        mock_agent.ask.return_value = "ok"

        with patch.dict("sys.modules", {
            "uvicorn": mock_uvicorn,
            "fastapi": MagicMock(FastAPI=mock_fastapi_cls),
            "pydantic": MagicMock(BaseModel=mock_base_model),
        }):
            with patch("ragkit.agent.Agent", return_value=mock_agent):
                result = runner.invoke(app, ["serve", "--config", str(config_path)])

        mock_uvicorn.run.assert_called_once()
        assert "127.0.0.1" in result.output


class TestCliDev:
    def test_dev_exits_on_eof(self, tmp_path):
        config_path = tmp_path / "rag.yaml"
        config_path.write_text("project:\n  name: test\n")

        mock_agent = MagicMock()

        with patch("ragkit.agent.Agent", return_value=mock_agent):
            with patch("builtins.input", side_effect=EOFError):
                result = runner.invoke(app, ["dev", "--config", str(config_path)])

        assert result.exit_code == 0
        assert "dev mode" in result.output.lower()

    def test_dev_exits_on_exit_command(self, tmp_path):
        config_path = tmp_path / "rag.yaml"
        config_path.write_text("project:\n  name: test\n")

        mock_agent = MagicMock()

        with patch("ragkit.agent.Agent", return_value=mock_agent):
            with patch("builtins.input", side_effect=["exit"]):
                result = runner.invoke(app, ["dev", "--config", str(config_path)])

        assert result.exit_code == 0

    def test_dev_shows_agent_response(self, tmp_path):
        config_path = tmp_path / "rag.yaml"
        config_path.write_text("project:\n  name: test\n")

        mock_agent = MagicMock()
        mock_agent.ask.return_value = "My answer"

        with patch("ragkit.agent.Agent", return_value=mock_agent):
            with patch("builtins.input", side_effect=["hello", EOFError]):
                result = runner.invoke(app, ["dev", "--config", str(config_path)])

        assert "My answer" in result.output

    def test_dev_handles_agent_error_gracefully(self, tmp_path):
        config_path = tmp_path / "rag.yaml"
        config_path.write_text("project:\n  name: test\n")

        mock_agent = MagicMock()
        mock_agent.ask.side_effect = RuntimeError("LLM unavailable")

        with patch("ragkit.agent.Agent", return_value=mock_agent):
            with patch("builtins.input", side_effect=["what?", EOFError]):
                result = runner.invoke(app, ["dev", "--config", str(config_path)])

        assert "Error" in result.output
        assert result.exit_code == 0
