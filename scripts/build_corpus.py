#!/usr/bin/env python
"""Build a manifest for all PDFs in the reports directory.

Example
-------
python scripts/build_corpus.py --reports-dir reports/raw --output reports/manifest.jsonl
"""

from __future__ import annotations

import sys
from pathlib import Path as _PathBootstrap

# Allow `python scripts/<name>.py` to import the local src package.
PROJECT_ROOT = _PathBootstrap(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
import json
from pathlib import Path

import fitz

from src.schemas import DocumentRecord
from src.utils import sha256_file, slugify_filename, write_jsonl


PROJECT_ROOT = _PathBootstrap(__file__).resolve().parents[1]


def portable_path(path: Path) -> str:
    """Return a project-relative path when the PDF is inside the repository."""
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def load_source_metadata(reports_dir: Path) -> dict[str, dict]:
    """Load curated source metadata when the starter source file exists."""
    sources_path = reports_dir.parent / "starter_corpus_sources.json"
    if not sources_path.exists():
        return {}
    with sources_path.open("r", encoding="utf-8") as handle:
        sources = json.load(handle)
    metadata = {}
    for source in sources:
        file_name = Path(source.get("file", "")).name
        if file_name:
            metadata[file_name] = source
        if source.get("doc_id"):
            metadata[source["doc_id"]] = source
    return metadata


def infer_title_from_pdf(pdf_path: Path) -> str:
    """Infer a title from metadata or from the file stem.

    This function keeps the logic deliberately conservative. It first checks the
    PDF metadata title, then falls back to the filename.
    """
    doc = fitz.open(pdf_path)
    meta_title = (doc.metadata or {}).get("title", "")
    if meta_title and meta_title.strip():
        return meta_title.strip()
    return pdf_path.stem



def build_manifest(reports_dir: Path, output_path: Path) -> None:
    records = []
    source_metadata = load_source_metadata(reports_dir)
    for pdf_path in sorted(reports_dir.glob("*.pdf")):
        doc = fitz.open(pdf_path)
        source = source_metadata.get(pdf_path.name) or source_metadata.get(slugify_filename(pdf_path.stem)) or {}
        title = source.get("title") or infer_title_from_pdf(pdf_path)
        doc_id = source.get("doc_id") or slugify_filename(pdf_path.stem)
        record = DocumentRecord(
            doc_id=doc_id,
            title=title,
            year=None,
            source_path=portable_path(pdf_path),
            authors=[],
            venue=None,
            topic_tags=[],
            organization=source.get("organization"),
            source_url=source.get("source_url"),
            role=source.get("role"),
            sha256=sha256_file(pdf_path),
            num_pages=len(doc),
            language="en",
        )
        records.append(record.to_dict())

    write_jsonl(output_path, records)
    print(f"Wrote manifest with {len(records)} document(s) to {output_path}")



def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports-dir", type=Path, default=Path("reports/raw"))
    parser.add_argument("--output", type=Path, default=Path("reports/manifest.jsonl"))
    args = parser.parse_args()
    build_manifest(args.reports_dir, args.output)


if __name__ == "__main__":
    main()
