from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from ragkit.sources.csv import CsvSource
from ragkit.sources.directory import DirectorySource
from ragkit.sources.json import JsonSource
from ragkit.sources.markdown import MarkdownSource
from ragkit.sources.txt import TxtSource


@pytest.fixture
def tmp(tmp_path):
    return tmp_path


# --- MarkdownSource ---

class TestMarkdownSource:
    def test_load_single_file(self, tmp):
        f = tmp / "doc.md"
        f.write_text("# Hello\nworld")
        docs = MarkdownSource(f).load()
        assert len(docs) == 1
        assert "Hello" in docs[0].content
        assert docs[0].metadata["type"] == "markdown"

    def test_load_directory(self, tmp):
        (tmp / "a.md").write_text("doc A")
        (tmp / "b.md").write_text("doc B")
        (tmp / "other.txt").write_text("ignored")
        docs = MarkdownSource(tmp).load()
        assert len(docs) == 2

    def test_metadata_has_source(self, tmp):
        f = tmp / "doc.md"
        f.write_text("content")
        docs = MarkdownSource(f).load()
        assert "source" in docs[0].metadata

    def test_empty_directory(self, tmp):
        docs = MarkdownSource(tmp).load()
        assert docs == []

    def test_transform_passthrough(self, tmp):
        f = tmp / "doc.md"
        f.write_text("hello")
        source = MarkdownSource(f)
        docs = source.load()
        result = source.transform(docs)
        assert result is docs

    def test_sync_noop(self, tmp):
        f = tmp / "doc.md"
        f.write_text("hello")
        MarkdownSource(f).sync()  # should not raise


# --- TxtSource ---

class TestTxtSource:
    def test_load_single_file(self, tmp):
        f = tmp / "file.txt"
        f.write_text("hello txt")
        docs = TxtSource(f).load()
        assert len(docs) == 1
        assert docs[0].content == "hello txt"
        assert docs[0].metadata["type"] == "txt"

    def test_load_directory(self, tmp):
        (tmp / "a.txt").write_text("A")
        (tmp / "b.txt").write_text("B")
        docs = TxtSource(tmp).load()
        assert len(docs) == 2

    def test_metadata_source(self, tmp):
        f = tmp / "f.txt"
        f.write_text("data")
        docs = TxtSource(f).load()
        assert str(f) == docs[0].metadata["source"]


# --- JsonSource ---

class TestJsonSource:
    def test_load_list_with_content_key(self, tmp):
        f = tmp / "data.json"
        f.write_text(json.dumps([{"content": "hello", "id": 1}, {"content": "world", "id": 2}]))
        docs = JsonSource(f, content_key="content").load()
        assert len(docs) == 2
        assert docs[0].content == "hello"
        assert docs[0].metadata["id"] == 1

    def test_load_dict_without_content_key(self, tmp):
        f = tmp / "data.json"
        f.write_text(json.dumps({"foo": "bar"}))
        docs = JsonSource(f).load()
        assert len(docs) == 1
        assert "foo" in docs[0].content

    def test_load_plain_list(self, tmp):
        f = tmp / "data.json"
        f.write_text(json.dumps(["item1", "item2"]))
        docs = JsonSource(f).load()
        assert len(docs) == 2
        assert docs[0].content == "item1"

    def test_metadata_type_is_json(self, tmp):
        f = tmp / "data.json"
        f.write_text(json.dumps({"content": "x"}))
        docs = JsonSource(f).load()
        assert docs[0].metadata["type"] == "json"

    def test_load_directory(self, tmp):
        (tmp / "a.json").write_text(json.dumps([{"content": "a"}]))
        (tmp / "b.json").write_text(json.dumps([{"content": "b"}]))
        docs = JsonSource(tmp).load()
        assert len(docs) == 2


# --- CsvSource ---

class TestCsvSource:
    def test_load_with_content_column(self, tmp):
        f = tmp / "data.csv"
        f.write_text("content,author\nhello world,alice\ngoodbye,bob\n")
        docs = CsvSource(f, content_column="content").load()
        assert len(docs) == 2
        assert docs[0].content == "hello world"
        assert docs[0].metadata["author"] == "alice"

    def test_load_without_content_column(self, tmp):
        f = tmp / "data.csv"
        f.write_text("name,age\nalice,30\n")
        docs = CsvSource(f).load()
        assert len(docs) == 1
        assert "name: alice" in docs[0].content

    def test_metadata_type_is_csv(self, tmp):
        f = tmp / "data.csv"
        f.write_text("col\nval\n")
        docs = CsvSource(f).load()
        assert docs[0].metadata["type"] == "csv"

    def test_load_directory(self, tmp):
        (tmp / "a.csv").write_text("col\nA\n")
        (tmp / "b.csv").write_text("col\nB\n")
        docs = CsvSource(tmp).load()
        assert len(docs) == 2


# --- DirectorySource ---

class TestDirectorySource:
    def test_loads_supported_extensions(self, tmp):
        (tmp / "a.md").write_text("md")
        (tmp / "b.txt").write_text("txt")
        (tmp / "c.json").write_text('"json"')
        (tmp / "ignored.py").write_text("python")
        docs = DirectorySource(tmp).load()
        assert len(docs) == 3

    def test_custom_extensions(self, tmp):
        (tmp / "file.md").write_text("md")
        (tmp / "file.py").write_text("py")
        docs = DirectorySource(tmp, extensions={".py"}).load()
        assert len(docs) == 1
        assert docs[0].metadata["type"] == "py"

    def test_recursive(self, tmp):
        sub = tmp / "sub"
        sub.mkdir()
        (sub / "nested.md").write_text("nested")
        docs = DirectorySource(tmp).load()
        assert len(docs) == 1

    def test_skips_unreadable_files(self, tmp):
        f = tmp / "binary.md"
        f.write_bytes(b"\xff\xfe")  # invalid UTF-8 for text read
        docs = DirectorySource(tmp).load()
        # Should not raise — silently skips unreadable files
        assert isinstance(docs, list)
