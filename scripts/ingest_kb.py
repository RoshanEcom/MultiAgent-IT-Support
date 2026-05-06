"""One-shot script to (re)build the Chroma index from the markdown runbooks.

Usage:
    python scripts/ingest_kb.py
    python scripts/ingest_kb.py --rebuild
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make `src` importable when running this script directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import SETTINGS  # noqa: E402
from src.rag.ingest import build_vectorstore  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Chroma vector index from markdown runbooks.")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Delete the existing index before rebuilding. Use after editing runbooks.",
    )
    args = parser.parse_args()

    print(f"Knowledge base directory: {SETTINGS.kb_dir}")
    print(f"Chroma directory:         {SETTINGS.chroma_dir}")
    print(f"Embedding model:          {SETTINGS.openai_embedding_model}")
    print()

    md_files = sorted(SETTINGS.kb_dir.glob("*.md"))
    if not md_files:
        print(f"ERROR: no markdown files found under {SETTINGS.kb_dir}")
        return 1
    print(f"Found {len(md_files)} runbook(s):")
    for f in md_files:
        print(f"  - {f.name}")
    print()

    print("Building index…")
    vs = build_vectorstore(force_rebuild=args.rebuild)
    count = vs._collection.count() if hasattr(vs, "_collection") else "?"
    print(f"Done. Index contains {count} chunks at {SETTINGS.chroma_dir}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
