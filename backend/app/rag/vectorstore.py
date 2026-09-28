"""Knowledge-base vector store.

LangChain earns its place here too: RecursiveCharacterTextSplitter for
chunking, OpenAIEmbeddings for the embedding call, and Chroma as a small
local vector store. None of this is buzzword-driven — swapping in pgvector
later is a matter of changing this one module (see README "Future
improvements"), because nothing above this layer knows or cares that Chroma
is the backing store.
"""

from __future__ import annotations

from pathlib import Path

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app import config

_embeddings = None
_vectorstore: Chroma | None = None

COLLECTION_NAME = "company_knowledge_base"

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=900,
    chunk_overlap=150,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def get_embeddings() -> OpenAIEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings(
            model=config.OPENAI_EMBEDDING_MODEL,
            api_key=config.OPENAI_API_KEY,
        )
    return _embeddings


def get_vectorstore() -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = Chroma(
            collection_name=COLLECTION_NAME,
            embedding_function=get_embeddings(),
            persist_directory=str(config.CHROMA_DIR),
            # Chroma defaults new collections to L2 distance, under which
            # similarity_search_with_relevance_scores() produces scores
            # outside [0, 1] (including negative ones) — cosine space keeps
            # the similarity_score shown in the UI meaningful.
            collection_metadata={"hnsw:space": "cosine"},
        )
    return _vectorstore


def add_document(source_document: str, text: str) -> int:
    """Chunk `text` and add it to the vector store, tagged with its filename."""
    chunks = _splitter.split_text(text)
    if not chunks:
        return 0
    vs = get_vectorstore()
    vs.add_texts(
        texts=chunks,
        metadatas=[{"source_document": source_document} for _ in chunks],
    )
    return len(chunks)


def list_indexed_documents() -> list[str]:
    vs = get_vectorstore()
    data = vs.get(include=["metadatas"])
    seen: set[str] = set()
    for meta in data.get("metadatas", []) or []:
        if meta and "source_document" in meta:
            seen.add(meta["source_document"])
    return sorted(seen)


def retrieve(query: str, k: int) -> list[dict]:
    vs = get_vectorstore()
    results = vs.similarity_search_with_relevance_scores(query, k=k)
    evidence = []
    for doc, score in results:
        evidence.append(
            {
                "source_document": doc.metadata.get("source_document", "unknown"),
                "content": doc.page_content,
                "similarity_score": round(float(score), 4),
            }
        )
    return evidence


def seed_knowledge_base_if_empty() -> int:
    """Index the bundled synthetic company documents on first run."""
    vs = get_vectorstore()
    existing = vs.get(include=[])
    if existing.get("ids"):
        return 0

    total_chunks = 0
    for path in sorted(config.KNOWLEDGE_BASE_DIR.glob("*.md")):
        text = Path(path).read_text(encoding="utf-8")
        total_chunks += add_document(path.name, text)
    return total_chunks


def reset_knowledge_base() -> None:
    global _vectorstore
    vs = get_vectorstore()
    ids = vs.get(include=[]).get("ids", [])
    if ids:
        vs.delete(ids=ids)
    _vectorstore = None
