#!/usr/bin/env python
"""Download the starter corpus PDFs listed in reports/starter_corpus_sources.json."""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path
from typing import Any, Dict, List


def load_sources(path: Path) -> List[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def download_sources(
    sources_path: Path,
    reports_dir: Path,
    force: bool = False,
    allow_manual_missing: bool = False,
) -> Dict[str, Any]:
    sources = load_sources(sources_path)
    reports_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for source in sources:
        target = reports_dir / Path(source["file"]).name
        if target.exists() and not force:
            results.append({"doc_id": source["doc_id"], "status": "exists", "file": str(target)})
            continue
        try:
            download_url = source.get("download_url") or source["source_url"]
            if not str(download_url).lower().split("?", 1)[0].endswith(".pdf"):
                if target.exists():
                    results.append(
                        {
                            "doc_id": source["doc_id"],
                            "status": "manual_source_retained",
                            "file": str(target),
                            "source_url": source["source_url"],
                            "message": "No direct PDF download URL is recorded; retain or provide this PDF locally.",
                        }
                    )
                    continue
                if allow_manual_missing:
                    results.append(
                        {
                            "doc_id": source["doc_id"],
                            "status": "manual_required",
                            "file": str(target),
                            "source_url": source["source_url"],
                            "message": "No direct PDF download URL is recorded; provide this PDF locally to include it in runtime indexing.",
                        }
                    )
                    continue
                raise ValueError(
                    f"No direct PDF download URL is recorded for {source['doc_id']}; visit {source['source_url']} manually."
                )
            request = urllib.request.Request(download_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310 - curated corpus bootstrap
                target.write_bytes(response.read())
            header = target.read_bytes()[:5]
            if header != b"%PDF-":
                target.unlink(missing_ok=True)
                raise ValueError(f"Downloaded content from {download_url} is not a PDF.")
            results.append({"doc_id": source["doc_id"], "status": "downloaded", "file": str(target), "url": download_url})
        except Exception as exc:
            results.append(
                {
                    "doc_id": source.get("doc_id"),
                    "status": "failed",
                    "file": str(target),
                    "error": f"{exc.__class__.__name__}: {exc}",
                }
            )

    ok_statuses = {"exists", "downloaded", "manual_source_retained"}
    if allow_manual_missing:
        ok_statuses.add("manual_required")
    ok = all(item["status"] in ok_statuses for item in results)
    return {"ok": ok, "sources": str(sources_path), "reports_dir": str(reports_dir), "results": results}


def main() -> None:
    parser = argparse.ArgumentParser(description="Download the radiotherapy physics starter corpus.")
    parser.add_argument("--sources", type=Path, default=Path("reports/starter_corpus_sources.json"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports/raw"))
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--allow-manual-missing",
        action="store_true",
        help="Do not fail when source metadata has no direct PDF URL and the PDF has not been supplied locally.",
    )
    args = parser.parse_args()
    result = download_sources(
        args.sources,
        args.reports_dir,
        force=args.force,
        allow_manual_missing=args.allow_manual_missing,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
