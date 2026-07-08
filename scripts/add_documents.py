#!/usr/bin/env python
"""Copy user PDFs into the corpus and optionally rebuild the RAG index."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List

# Allow `python scripts/<name>.py` to import local scripts.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.prepare_index import prepare_index


def add_documents(
    inputs: List[Path],
    reports_dir: Path,
    rebuild: bool = False,
    manifest: Path = Path("reports/manifest.jsonl"),
    parsed_dir: Path = Path("parsed"),
    chunks_dir: Path = Path("chunks"),
    index_dir: Path = Path("index"),
) -> Dict[str, Any]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    errors = []

    for item in inputs:
        matches = sorted(item.glob("*.pdf")) if item.is_dir() else [item]
        for path in matches:
            if path.suffix.lower() != ".pdf":
                errors.append({"input": str(path), "error": "Only PDF files are supported."})
                continue
            if not path.exists():
                errors.append({"input": str(path), "error": "File does not exist."})
                continue
            target = reports_dir / path.name
            if path.resolve() != target.resolve():
                shutil.copy2(path, target)
            copied.append(str(target))

    result: Dict[str, Any] = {"ok": not errors, "copied": copied, "errors": errors, "rebuilt": False}
    if rebuild and copied and not errors:
        prepare_index(reports_dir, manifest, parsed_dir, chunks_dir, index_dir)
        result["rebuilt"] = True
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Add PDFs to the local corpus.")
    parser.add_argument("inputs", nargs="+", type=Path, help="PDF files or directories containing PDFs.")
    parser.add_argument("--reports-dir", type=Path, default=Path("reports/raw"))
    parser.add_argument("--rebuild", action="store_true", help="Run prepare_index.py after copying PDFs.")
    parser.add_argument("--manifest", type=Path, default=Path("reports/manifest.jsonl"))
    parser.add_argument("--parsed-dir", type=Path, default=Path("parsed"))
    parser.add_argument("--chunks-dir", type=Path, default=Path("chunks"))
    parser.add_argument("--index-dir", type=Path, default=Path("index"))
    args = parser.parse_args()

    result = add_documents(
        args.inputs,
        reports_dir=args.reports_dir,
        rebuild=args.rebuild,
        manifest=args.manifest,
        parsed_dir=args.parsed_dir,
        chunks_dir=args.chunks_dir,
        index_dir=args.index_dir,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
