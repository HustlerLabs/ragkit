from ragkit.core.base import Document
from ragkit.pipeline.chunker import Chunker


def test_short_text_no_split():
    chunker = Chunker(chunk_size=500, overlap=50)
    doc = Document(content="Short text.", metadata={"source": "test"})
    chunks = chunker.chunk([doc])
    assert len(chunks) == 1
    assert chunks[0].content == "Short text."


def test_long_text_splits():
    chunker = Chunker(chunk_size=50, overlap=10)
    content = "word " * 100
    doc = Document(content=content, metadata={"source": "test"})
    chunks = chunker.chunk([doc])
    assert len(chunks) > 1


def test_chunk_has_id():
    chunker = Chunker(chunk_size=500, overlap=50)
    doc = Document(content="Hello world.", metadata={"source": "test.md"})
    chunks = chunker.chunk([doc])
    assert chunks[0].id is not None


def test_chunk_metadata_preserved():
    chunker = Chunker(chunk_size=500, overlap=50)
    doc = Document(content="Hello.", metadata={"source": "test.md", "type": "markdown"})
    chunks = chunker.chunk([doc])
    assert chunks[0].metadata["source"] == "test.md"
    assert chunks[0].metadata["type"] == "markdown"
