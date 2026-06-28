from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock

import numpy as np
import pytest

from ragkit.embeddings.sentence_transformers import SentenceTransformerEmbedder


@pytest.fixture(autouse=True)
def mock_sentence_transformers():
    """Inject a fake sentence_transformers module."""
    mock_st = MagicMock()

    fake_model = MagicMock()
    fake_model.encode.return_value = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
    mock_st.SentenceTransformer.return_value = fake_model

    sys.modules["sentence_transformers"] = mock_st
    yield mock_st
    sys.modules.pop("sentence_transformers", None)


class TestSentenceTransformerEmbedder:
    def test_lazy_loads_model_on_first_embed(self, mock_sentence_transformers):
        embedder = SentenceTransformerEmbedder("all-MiniLM-L6-v2")
        assert embedder._model is None
        embedder.embed(["hello"])
        assert embedder._model is not None

    def test_model_loaded_once(self, mock_sentence_transformers):
        embedder = SentenceTransformerEmbedder()
        embedder.embed(["a"])
        embedder.embed(["b"])
        mock_sentence_transformers.SentenceTransformer.assert_called_once()

    def test_embed_returns_list_of_vectors(self, mock_sentence_transformers):
        embedder = SentenceTransformerEmbedder()
        result = embedder.embed(["hello", "world"])
        assert len(result) == 2
        assert isinstance(result[0], list)
        assert result[0] == pytest.approx([0.1, 0.2, 0.3])

    def test_embed_calls_encode_with_correct_args(self, mock_sentence_transformers):
        embedder = SentenceTransformerEmbedder()
        embedder.embed(["test text"])
        model_instance = mock_sentence_transformers.SentenceTransformer.return_value
        model_instance.encode.assert_called_once_with(
            ["test text"],
            show_progress_bar=False,
            convert_to_numpy=True,
        )

    def test_custom_model_name_passed_to_constructor(self, mock_sentence_transformers):
        embedder = SentenceTransformerEmbedder("paraphrase-MiniLM-L3-v2")
        embedder.embed(["x"])
        mock_sentence_transformers.SentenceTransformer.assert_called_once_with("paraphrase-MiniLM-L3-v2")

    def test_embed_one_returns_single_vector(self, mock_sentence_transformers):
        mock_sentence_transformers.SentenceTransformer.return_value.encode.return_value = np.array([[0.1, 0.2]])
        embedder = SentenceTransformerEmbedder()
        result = embedder.embed_one("hello")
        assert isinstance(result, list)
        assert result == pytest.approx([0.1, 0.2])
