#!/usr/bin/env python
"""Extract table and image metadata from report PDFs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pdf_processing.assets import extract_pdf_assets, write_jsonl


def iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    if not path.exists():
        return []
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def manifest_lookup(manifest_path: Path) -> Dict[str, Dict[str, Any]]:
    return {str(item["source_path"]): item for item in iter_jsonl(manifest_path)}


def discover_pdfs(paths: List[Path]) -> List[Path]:
    pdfs: List[Path] = []
    for path in paths:
        if path.is_dir():
            pdfs.extend(sorted(path.glob("*.pdf")))
        elif path.suffix.lower() == ".pdf":
            pdfs.append(path)
    return sorted({path.resolve() for path in pdfs})


def fallback_doc_id(pdf_path: Path) -> str:
    return pdf_path.stem.lower().replace(" ", "_").replace("-", "_")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract table and image metadata from report PDFs.")
    parser.add_argument("paths", nargs="*", type=Path, default=[PROJECT_ROOT / "reports" / "raw"])
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--manifest", type=Path, default=PROJECT_ROOT / "reports" / "manifest.jsonl")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "assets" / "extracted")
    parser.add_argument("--save-images", action="store_true", help="Also export embedded image binaries.")
    args = parser.parse_args()

    root = args.root.resolve()
    output_dir = args.output_dir.resolve()
    lookup = manifest_lookup(args.manifest)
    results = []

    for pdf_path in discover_pdfs(args.paths):
        rel = pdf_path.resolve().relative_to(root).as_posix() if str(pdf_path.resolve()).startswith(str(root)) else pdf_path.as_posix()
        meta = lookup.get(rel, {})
        doc_id = str(meta.get("doc_id") or fallback_doc_id(pdf_path))
        title = str(meta.get("title") or doc_id)
        records = extract_pdf_assets(
            pdf_path=pdf_path,
            doc_id=doc_id,
            title=title,
            root=root,
            save_images=args.save_images,
            image_output_dir=output_dir / "images",
        )
        target = output_dir / f"{doc_id}.assets.jsonl"
        write_jsonl(target, records)
        results.append(
            {
                "doc_id": doc_id,
                "source_path": rel,
                "output": target.relative_to(root).as_posix(),
                "asset_count": len(records),
                "table_count": sum(1 for item in records if item["asset_type"] == "table"),
                "image_count": sum(1 for item in records if item["asset_type"] == "image"),
            }
        )

    manifest = {"ok": True, "output_dir": output_dir.relative_to(root).as_posix(), "documents": results}
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "asset_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
