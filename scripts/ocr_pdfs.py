#!/usr/bin/env python
"""Run optional OCR on scanned PDFs when OCRmyPDF is installed."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List


def ocr_pdf(input_pdf: Path, output_pdf: Path, force: bool = False, language: str = "eng") -> Dict[str, Any]:
    executable = shutil.which("ocrmypdf")
    if executable is None:
        return {
            "ok": False,
            "input": str(input_pdf),
            "output": str(output_pdf),
            "error": {
                "code": "ocr_required",
                "message": "OCRmyPDF is not installed or not on PATH. Install OCRmyPDF plus its system dependencies, or OCR the PDF before indexing.",
                "details": {
                    "recommended_command": "ocrmypdf --skip-text input.pdf output.pdf",
                    "note": "On Windows this usually also requires Ghostscript and Tesseract.",
                },
            },
        }
    if output_pdf.exists() and not force:
        return {"ok": True, "input": str(input_pdf), "output": str(output_pdf), "status": "exists"}
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    command = [
        executable,
        "--skip-text",
        "--language",
        language,
        str(input_pdf),
        str(output_pdf),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    return {
        "ok": completed.returncode == 0,
        "input": str(input_pdf),
        "output": str(output_pdf),
        "status": "ocr_complete" if completed.returncode == 0 else "ocr_failed",
        "returncode": completed.returncode,
        "stdout": completed.stdout[-4000:],
        "stderr": completed.stderr[-4000:],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="OCR scanned PDFs using OCRmyPDF when available.")
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("reports/ocr"))
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--language", default="eng")
    args = parser.parse_args()

    results: List[Dict[str, Any]] = []
    for item in args.inputs:
        pdfs = sorted(item.glob("*.pdf")) if item.is_dir() else [item]
        for pdf in pdfs:
            if pdf.suffix.lower() != ".pdf":
                continue
            output = args.output_dir / pdf.name
            results.append(ocr_pdf(pdf, output, force=args.force, language=args.language))
    payload = {"ok": all(item.get("ok") for item in results), "results": results}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(0 if payload["ok"] else 1)


if __name__ == "__main__":
    main()
