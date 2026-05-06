"""Build a Chroma vector index from the markdown runbooks under knowledge_base/."""
from __future__ import annotations

from pathlib import Path

from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from src.config import SETTINGS
from src.llm import get_embeddings

COLLECTION_NAME = "it_runbooks"


def _load_markdown_files(kb_dir: Path) -> list[Document]:
    docs: list[Document] = []
    for md_path in sorted(kb_dir.glob("*.md")):
        loader = TextLoader(str(md_path), encoding="utf-8")
        for d in loader.load():
            d.metadata["source_file"] = md_path.name
            docs.append(d)
    return docs


def _split_documents(docs: list[Document]) -> list[Document]:
    """Two-pass split: first by markdown headers, then char-based to keep chunks bounded."""
    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "h1"),
            ("##", "h2"),
            ("###", "h3"),
        ],
        strip_headers=False,
    )
    char_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    out: list[Document] = []
    for d in docs:
        for header_chunk in header_splitter.split_text(d.page_content):
            for sub in char_splitter.split_documents([header_chunk]):
                # Carry through the source file from the parent document
                sub.metadata = {**d.metadata, **sub.metadata}
                out.append(sub)
    # Stamp chunk indexes per source file so retrieval can cite "file.md – chunk 3"
    counters: dict[str, int] = {}
    for chunk in out:
        src = chunk.metadata.get("source_file", "unknown")
        counters[src] = counters.get(src, 0) + 1
        chunk.metadata["chunk_index"] = counters[src] - 1
    return out


def build_vectorstore(force_rebuild: bool = False) -> Chroma:
    """Build (or load) the persistent Chroma collection. Idempotent."""
    SETTINGS.chroma_dir.mkdir(parents=True, exist_ok=True)

    embeddings = get_embeddings()

    if force_rebuild and SETTINGS.chroma_dir.exists():
        import shutil
        shutil.rmtree(SETTINGS.chroma_dir)
        SETTINGS.chroma_dir.mkdir(parents=True, exist_ok=True)

    docs = _load_markdown_files(SETTINGS.kb_dir)
    if not docs:
        raise RuntimeError(
            f"No markdown files found under {SETTINGS.kb_dir}. "
            f"Add runbooks before running ingest."
        )
    chunks = _split_documents(docs)

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=str(SETTINGS.chroma_dir),
    )
    return vectorstore


def load_vectorstore() -> Chroma:
    """Load an already-built Chroma collection. Used by the retriever at request time."""
    embeddings = get_embeddings()
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(SETTINGS.chroma_dir),
    )
