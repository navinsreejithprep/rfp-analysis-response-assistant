"""Turns an uploaded RFP or reference document into plain text.

This is the one place LangChain document loaders earn their keep: PyPDFLoader
and Docx2txtLoader handle the binary-format parsing (page extraction, XML
unzipping) that would otherwise be a lot of fiddly, easy-to-get-wrong code for
very little product value. Everything downstream just works with plain text.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def parse_document_bytes(filename: str, content: bytes) -> str:
    """Write the upload to a temp file (loaders need a path) and extract text."""
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{suffix}'. Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        if suffix == ".pdf":
            loader = PyPDFLoader(tmp_path)
            docs = loader.load()
        elif suffix == ".docx":
            loader = Docx2txtLoader(tmp_path)
            docs = loader.load()
        else:  # .txt / .md
            loader = TextLoader(tmp_path, encoding="utf-8")
            docs = loader.load()

        text = "\n\n".join(d.page_content for d in docs).strip()
        if not text:
            raise ValueError(f"No extractable text found in '{filename}'.")
        return text
    finally:
        Path(tmp_path).unlink(missing_ok=True)
