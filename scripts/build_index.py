#!/usr/bin/env python
"""Build dense and sparse retrieval indices.

Example
-------
python scripts/build_index.py --chunks-dir chunks --index-dir index
"""

from __future__ import annotations

import sys
from pathlib import Path as _PathBootstrap

# Allow `python scripts/<name>.py` to import the local src package.
PROJECT_ROOT = _PathBootstrap(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
from pathlib import Path

from src.config import MODELS
from src.retrieval.dense import DenseIndexer
from src.retrieval.embedder import TextEmbedder
from src.retrieval.sparse import SparseIndexer
from src.utils import ensure_dir, iter_jsonl, write_jsonl



def load_all_chunks(chunks_dir: Path):
    chunks = []
    for path in sorted(chunks_dir.glob("*.chunks.jsonl")):
        chunks.extend(list(iter_jsonl(path)))
    return chunks



def build_indices(chunks_dir: Path, index_dir: Path) -> None:
    dense_dir = index_dir / "dense"
    sparse_dir = index_dir / "sparse"
    metadata_dir = index_dir / "metadata"
    ensure_dir(dense_dir)
    ensure_dir(sparse_dir)
    ensure_dir(metadata_dir)

    chunks = load_all_chunks(chunks_dir)
    if not chunks:
        raise ValueError("No chunk files found. Run parse_pdf.py and chunk_corpus.py first.")

    write_jsonl(metadata_dir / "chunk_metadata.jsonl", chunks)

    embedder = TextEmbedder(
        MODELS.embedding_model_name,
        query_prefix=MODELS.embedding_query_prefix,
        document_prefix=MODELS.embedding_document_prefix,
    )
    dense_indexer = DenseIndexer(embedder)
    dense_indexer.build(chunks, dense_dir)

    sparse_indexer = SparseIndexer()
    sparse_indexer.build(chunks, sparse_dir)

    print(f"Built dense and sparse indices for {len(chunks)} chunk(s) under {index_dir}")



def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunks-dir", type=Path, default=Path("chunks"))
    parser.add_argument("--index-dir", type=Path, default=Path("index"))
    args = parser.parse_args()
    build_indices(args.chunks_dir, args.index_dir)


if __name__ == "__main__":
    main()
