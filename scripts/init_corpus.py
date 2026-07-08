#!/usr/bin/env python
"""Create an empty corpus workspace for report RAG indexing."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def touch_keep(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    keep = path / ".gitkeep"
    if not keep.exists():
        keep.write_text("", encoding="utf-8")


def init_corpus(root: Path, force_manifest: bool = False) -> dict:
    root = root.resolve()
    reports_raw = root / "reports" / "raw"
    parsed = root / "parsed"
    chunks = root / "chunks"
    index_dense = root / "index" / "dense"
    index_sparse = root / "index" / "sparse"
    index_metadata = root / "index" / "metadata"

    for path in [reports_raw, parsed, chunks, index_dense, index_sparse, index_metadata]:
        touch_keep(path)

    manifest = root / "reports" / "manifest.jsonl"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    if force_manifest or not manifest.exists():
        manifest.write_text("", encoding="utf-8")

    return {
        "ok": True,
        "root": str(root),
        "created_or_verified": [
            "reports/raw",
            "parsed",
            "chunks",
            "index/dense",
            "index/sparse",
            "index/metadata",
            "reports/manifest.jsonl",
        ],
        "next_step": "Place PDF reports in reports/raw, then run scripts/prepare_index.py.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize an empty report RAG corpus workspace.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--force-manifest", action="store_true", help="Overwrite reports/manifest.jsonl with an empty file.")
    args = parser.parse_args()
    print(json.dumps(init_corpus(args.root, force_manifest=args.force_manifest), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
