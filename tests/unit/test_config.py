import tempfile
from pathlib import Path

from ragkit.core.config import load_config


def test_default_config():
    config = load_config("nonexistent.yaml")
    assert config.model.provider == "openrouter"
    assert config.pipeline.chunk_size == 500
    assert config.retrieval.top_k == 5


def test_load_from_yaml():
    yaml_content = """
project:
  name: test-project
model:
  provider: openrouter
  model: openai/gpt-4o
pipeline:
  chunk_size: 200
  overlap: 20
retrieval:
  top_k: 3
"""
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
        f.write(yaml_content)
        tmp_path = Path(f.name)

    try:
        config = load_config(tmp_path)
        assert config.name == "test-project"
        assert config.model.model == "openai/gpt-4o"
        assert config.pipeline.chunk_size == 200
        assert config.retrieval.top_k == 3
    finally:
        tmp_path.unlink()
