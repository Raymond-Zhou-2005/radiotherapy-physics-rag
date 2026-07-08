#!/usr/bin/env python
"""List available PDFs, manifest entries, chunks, and indexed report ids."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List


def iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def list_corpus(root: Path) -> Dict[str, Any]:
    reports_dir = root / "reports" / "raw"
    manifest_path = root / "reports" / "manifest.jsonl"
    chunks_dir = root / "chunks"
    metadata_path = root / "index" / "metadata" / "chunk_metadata.jsonl"

    pdfs = sorted(str(path.relative_to(root)) for path in reports_dir.glob("*.pdf")) if reports_dir.exists() else []
    manifest = list(iter_jsonl(manifest_path)) if manifest_path.exists() else []
    indexed = list(iter_jsonl(metadata_path)) if metadata_path.exists() else []
    indexed_counts = Counter(str(item.get("doc_id", "")) for item in indexed if item.get("doc_id"))
    chunk_files = {}
    if chunks_dir.exists():
        for path in sorted(chunks_dir.glob("*.chunks.jsonl")):
            records = list(iter_jsonl(path))
            kinds = Counter(str(item.get("chunk_kind", "standard")) for item in records)
            chunk_files[path.name] = {"chunks": len(records), "chunk_kinds": dict(kinds)}

    return {
        "ok": True,
        "root": str(root),
        "pdf_count": len(pdfs),
        "pdfs": pdfs,
        "manifest_count": len(manifest),
        "manifest_doc_ids": [item.get("doc_id") for item in manifest],
        "chunk_files": chunk_files,
        "indexed_chunk_count": len(indexed),
        "indexed_report_ids": sorted(indexed_counts),
        "indexed_chunk_counts": dict(indexed_counts),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="List the current radiotherapy physics RAG corpus.")
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    print(json.dumps(list_corpus(args.root.resolve()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
