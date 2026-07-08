#!/usr/bin/env python
"""Build the portable sparse BM25 retrieval index.

This command is useful when users want a no-model local RAG path or when dense
embedding models are not installed or cached yet.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.retrieval.sparse import SparseIndexer
from src.utils import ensure_dir, iter_jsonl, write_jsonl


def load_all_chunks(chunks_dir: Path) -> list[dict]:
    chunks: list[dict] = []
    for path in sorted(chunks_dir.glob("*.chunks.jsonl")):
        chunks.extend(iter_jsonl(path))
    return chunks


def build_sparse_index(chunks_dir: Path, index_dir: Path) -> dict:
    sparse_dir = index_dir / "sparse"
    metadata_dir = index_dir / "metadata"
    ensure_dir(sparse_dir)
    ensure_dir(metadata_dir)

    chunks = load_all_chunks(chunks_dir)
    if not chunks:
        raise ValueError("No chunk files found. Run parse_pdf.py and chunk_corpus.py first.")

    write_jsonl(metadata_dir / "chunk_metadata.jsonl", chunks)
    SparseIndexer().build(chunks, sparse_dir)
    return {
        "ok": True,
        "chunks_dir": str(chunks_dir),
        "index_dir": str(index_dir),
        "indexed_chunk_count": len(chunks),
        "backend": "sparse",
        "files": [
            str(metadata_dir / "chunk_metadata.jsonl"),
            str(sparse_dir / "bm25.pkl"),
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build only the local BM25 sparse retrieval index.")
    parser.add_argument("--chunks-dir", type=Path, default=Path("chunks"))
    parser.add_argument("--index-dir", type=Path, default=Path("index"))
    args = parser.parse_args()

    result = build_sparse_index(args.chunks_dir, args.index_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

