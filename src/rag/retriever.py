"""Thin retrieval wrapper. Lazy-loads the Chroma collection on first call so module
import is cheap."""
from __future__ import annotations

from functools import lru_cache

from src.rag.ingest import load_vectorstore
from src.state import RetrievedDoc


@lru_cache(maxsize=1)
def _store():
    return load_vectorstore()


def retrieve(query: str, k: int = 5, category_hint: str | None = None) -> list[RetrievedDoc]:
    """Run a similarity search and return RetrievedDoc records.

    `category_hint` is currently unused for filtering but is reserved for a future
    metadata filter (e.g., when Intake is highly confident about category, restrict
    the search to a specific runbook)."""
    _ = category_hint  # reserved
    pairs = _store().similarity_search_with_score(query, k=k)
    out: list[RetrievedDoc] = []
    for doc, score in pairs:
        meta = doc.metadata or {}
        out.append(
            RetrievedDoc(
                source_file=meta.get("source_file", "unknown.md"),
                chunk_index=int(meta.get("chunk_index", 0)),
                snippet=doc.page_content.strip(),
                score=float(score),
                metadata={k: v for k, v in meta.items() if k not in {"source_file", "chunk_index"}},
            )
        )
    return out
