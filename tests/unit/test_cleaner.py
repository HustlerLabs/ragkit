from ragkit.core.base import Document
from ragkit.pipeline.cleaner import Cleaner


def test_removes_extra_newlines():
    cleaner = Cleaner()
    doc = Document(content="hello\n\n\n\nworld", metadata={})
    result = cleaner.clean([doc])
    assert "\n\n\n" not in result[0].content


def test_strips_whitespace():
    cleaner = Cleaner()
    doc = Document(content="  hello  ", metadata={})
    result = cleaner.clean([doc])
    assert result[0].content == "hello"


def test_removes_extra_spaces():
    cleaner = Cleaner()
    doc = Document(content="hello   world", metadata={})
    result = cleaner.clean([doc])
    assert result[0].content == "hello world"
