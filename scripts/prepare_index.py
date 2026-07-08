#!/usr/bin/env python
"""Run the offline corpus preparation and indexing pipeline in order."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow `python scripts/<name>.py` to import the local src package.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def prepare_index(
    reports_dir: Path,
    manifest: Path,
    parsed_dir: Path,
    chunks_dir: Path,
    index_dir: Path,
    index_backend: str = "both",
) -> None:
    pdfs = sorted(reports_dir.glob("*.pdf"))
    if not pdfs:
        reports_dir.mkdir(parents=True, exist_ok=True)
        manifest.parent.mkdir(parents=True, exist_ok=True)
        if not manifest.exists():
            manifest.write_text("", encoding="utf-8")
        result = {
            "ok": False,
            "error": {
                "code": "empty_corpus",
                "message": "No PDF files were found. Add PDFs to the reports directory before building a RAG index.",
                "details": {
                    "reports_dir": str(reports_dir),
                    "manifest": str(manifest),
                    "next_step": "Copy PDFs into reports/raw or pass --reports-dir to a directory containing PDFs.",
                },
            },
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        raise SystemExit(2)

    from scripts.build_corpus import build_manifest
    from scripts.build_index import build_indices
    from scripts.build_sparse_index import build_sparse_index
    from scripts.chunk_corpus import chunk_all
    from scripts.parse_pdf import parse_all

    build_manifest(reports_dir, manifest)
    parse_all(manifest, parsed_dir)
    chunk_all(parsed_dir, chunks_dir)
    if index_backend == "sparse":
        build_sparse_index(chunks_dir, index_dir)
    else:
        build_indices(chunks_dir, index_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare report corpus artifacts and retrieval indices.")
    parser.add_argument("--reports-dir", type=Path, default=Path("reports/raw"))
    parser.add_argument("--manifest", type=Path, default=Path("reports/manifest.jsonl"))
    parser.add_argument("--parsed-dir", type=Path, default=Path("parsed"))
    parser.add_argument("--chunks-dir", type=Path, default=Path("chunks"))
    parser.add_argument("--index-dir", type=Path, default=Path("index"))
    parser.add_argument(
        "--index-backend",
        choices=["both", "sparse"],
        default="both",
        help="Use sparse for the no-model BM25-only path; both builds dense and sparse indexes.",
    )
    args = parser.parse_args()
    prepare_index(
        args.reports_dir,
        args.manifest,
        args.parsed_dir,
        args.chunks_dir,
        args.index_dir,
        index_backend=args.index_backend,
    )


if __name__ == "__main__":
    main()
