#!/usr/bin/env python
"""Convert parsed blocks into section-aware chunks.

Example
-------
python scripts/chunk_corpus.py --parsed-dir parsed --chunks-dir chunks
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

from src.chunking.splitter import SectionAwareChunker
from src.config import CHUNKING
from src.utils import ensure_dir, read_jsonl, write_jsonl


def chunk_all(parsed_dir: Path, chunks_dir: Path) -> None:
    ensure_dir(chunks_dir)
    chunker = SectionAwareChunker(
        chunk_size_tokens=CHUNKING.chunk_size_tokens,
        chunk_overlap_tokens=CHUNKING.chunk_overlap_tokens,
        min_chunk_tokens=CHUNKING.min_chunk_tokens,
        definitional_microchunk_max_tokens=CHUNKING.definitional_microchunk_max_tokens,
    )

    for parsed_path in sorted(parsed_dir.glob("*.parsed.jsonl")):
        parsed_records = read_jsonl(parsed_path)
        chunks = chunker.chunk_document(parsed_records)
        doc_id = parsed_path.name.replace(".parsed.jsonl", "")
        out_path = chunks_dir / f"{doc_id}.chunks.jsonl"
        write_jsonl(out_path, [c.to_dict() for c in chunks])
        print(f"Chunked {doc_id}: {len(chunks)} chunk(s) -> {out_path}")



def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parsed-dir", type=Path, default=Path("parsed"))
    parser.add_argument("--chunks-dir", type=Path, default=Path("chunks"))
    args = parser.parse_args()
    chunk_all(args.parsed_dir, args.chunks_dir)


if __name__ == "__main__":
    main()
