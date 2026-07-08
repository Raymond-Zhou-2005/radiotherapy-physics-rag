#!/usr/bin/env python
"""Parse report PDFs into structured JSONL blocks.

Example
-------
python scripts/parse_pdf.py --manifest reports/manifest.jsonl --parsed-dir parsed
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

from src.pdf_processing.extractor import PDFStructuredParser
from src.utils import ensure_dir, read_jsonl, write_jsonl



def parse_all(manifest_path: Path, parsed_dir: Path) -> None:
    ensure_dir(parsed_dir)
    manifest = read_jsonl(manifest_path)
    parser = PDFStructuredParser()
    manifest_root = manifest_path.resolve().parents[1]

    for record in manifest:
        source_path = str(record["source_path"])
        pdf_path = Path(source_path)
        if not pdf_path.is_absolute():
            pdf_path = manifest_root / pdf_path
        doc_id = record["doc_id"]
        title = record["title"]
        blocks = parser.parse(pdf_path=pdf_path, doc_id=doc_id, title=title, source_path=source_path)
        out_path = parsed_dir / f"{doc_id}.parsed.jsonl"
        write_jsonl(out_path, [b.to_dict() for b in blocks])
        print(f"Parsed {doc_id}: {len(blocks)} block(s) -> {out_path}")



def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("reports/manifest.jsonl"))
    parser.add_argument("--parsed-dir", type=Path, default=Path("parsed"))
    args = parser.parse_args()
    parse_all(args.manifest, args.parsed_dir)


if __name__ == "__main__":
    main()
