#!/usr/bin/env python
"""Inspect PDFs for text extraction readiness before indexing."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def inspect_pdf(path: Path, low_text_chars_per_page: int = 80) -> Dict[str, Any]:
    try:
        import fitz
    except Exception as exc:  # pragma: no cover - dependency boundary
        return {
            "file": str(path),
            "ok": False,
            "error": {
                "code": "runtime_failure",
                "message": "PyMuPDF/fitz is required to inspect PDFs.",
                "details": {"exception": str(exc)},
            },
        }

    try:
        doc = fitz.open(path)
        page_stats = []
        total_chars = 0
        low_text_pages = 0
        empty_pages = 0
        for index, page in enumerate(doc, start=1):
            text = page.get_text("text") or ""
            chars = len(text.strip())
            total_chars += chars
            if chars == 0:
                empty_pages += 1
            if chars < low_text_chars_per_page:
                low_text_pages += 1
            page_stats.append({"page": index, "text_chars": chars, "low_text": chars < low_text_chars_per_page})
        page_count = len(doc)
        avg_chars = total_chars / page_count if page_count else 0.0
        scanned_likely = page_count > 0 and (
            avg_chars < low_text_chars_per_page or low_text_pages / page_count >= 0.5
        )
        return {
            "file": str(path),
            "ok": True,
            "page_count": page_count,
            "total_text_chars": total_chars,
            "avg_text_chars_per_page": round(avg_chars, 2),
            "low_text_pages": low_text_pages,
            "empty_pages": empty_pages,
            "scanned_or_ocr_likely_needed": scanned_likely,
            "low_text_threshold_chars_per_page": low_text_chars_per_page,
            "pages": page_stats,
        }
    except Exception as exc:
        return {
            "file": str(path),
            "ok": False,
            "error": {
                "code": "runtime_failure",
                "message": "Failed to inspect PDF.",
                "details": {"exception_type": exc.__class__.__name__, "exception": str(exc)},
            },
        }


def inspect_paths(paths: List[Path], low_text_chars_per_page: int = 80) -> Dict[str, Any]:
    pdfs: List[Path] = []
    for path in paths:
        if path.is_dir():
            pdfs.extend(sorted(path.glob("*.pdf")))
        elif path.suffix.lower() == ".pdf":
            pdfs.append(path)
    results = [inspect_pdf(path, low_text_chars_per_page=low_text_chars_per_page) for path in sorted(set(pdfs))]
    return {
        "ok": all(item.get("ok") for item in results),
        "pdf_count": len(results),
        "scanned_or_ocr_likely_needed_count": sum(1 for item in results if item.get("scanned_or_ocr_likely_needed")),
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect PDFs for low-text/scanned-page risk before indexing.")
    parser.add_argument("paths", nargs="*", type=Path, default=[Path("reports/raw")])
    parser.add_argument("--low-text-chars-per-page", type=int, default=80)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    result = inspect_paths(args.paths, low_text_chars_per_page=args.low_text_chars_per_page)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text)
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
