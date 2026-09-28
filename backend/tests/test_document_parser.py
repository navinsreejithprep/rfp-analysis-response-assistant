import pytest

from app.parsing.document_parser import parse_document_bytes


def test_parses_plain_text():
    text = parse_document_bytes("notes.txt", b"Hello RFP world.")
    assert "Hello RFP world." in text


def test_parses_markdown_as_text():
    text = parse_document_bytes("doc.md", b"# Heading\n\nBody text.")
    assert "Body text." in text


def test_rejects_unsupported_extension():
    with pytest.raises(ValueError):
        parse_document_bytes("archive.zip", b"not a real zip")


def test_rejects_empty_text_file():
    with pytest.raises(ValueError):
        parse_document_bytes("empty.txt", b"   \n\n  ")
