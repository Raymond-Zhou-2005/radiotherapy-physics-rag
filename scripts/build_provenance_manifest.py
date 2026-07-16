#!/usr/bin/env python
"""Create a local, auditable provenance manifest for a rebuilt corpus.

The manifest records observed local-file properties and curated source fields.
It intentionally leaves publisher license and access terms as ``null`` unless a
maintainer has verified and supplied them in the source catalog.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl_by_doc_id(path: Path) -> Dict[str, Dict[str, Any]]:
    if not path.exists():
        return {}
    records: Dict[str, Dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                record = json.loads(line)
                if record.get("doc_id"):
                    records[str(record["doc_id"])] = record
    return records


def build_provenance_manifest(
    sources_path: Path,
    reports_dir: Path,
    corpus_manifest_path: Path,
) -> Dict[str, Any]:
    sources: List[Dict[str, Any]] = load_json(sources_path)
    corpus_records = load_jsonl_by_doc_id(corpus_manifest_path)
    documents = []

    for source in sorted(sources, key=lambda item: str(item["doc_id"])):
        doc_id = str(source["doc_id"])
        local_file = reports_dir / Path(str(source["file"])).name
        corpus_record = corpus_records.get(doc_id, {})
        documents.append(
            {
                "doc_id": doc_id,
                "title": source.get("title"),
                "organization": source.get("organization"),
                "role": source.get("role"),
                "source_url": source.get("source_url"),
                "download_url": source.get("download_url"),
                "render_url": source.get("render_url"),
                "publisher_license": source.get("publisher_license"),
                "terms_url": source.get("terms_url"),
                "license_verification_status": source.get("license_verification_status", "not_verified"),
                "local_runtime": {
                    "present": local_file.exists(),
                    "relative_path": f"reports/raw/{local_file.name}",
                    "sha256": corpus_record.get("sha256"),
                    "num_pages": corpus_record.get("num_pages"),
                    "byte_size": local_file.stat().st_size if local_file.exists() else None,
                },
            }
        )

    present_count = sum(1 for item in documents if item["local_runtime"]["present"])
    return {
        "schema_version": "1.0.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_catalog": str(sources_path.as_posix()),
        "corpus_manifest": str(corpus_manifest_path.as_posix()),
        "summary": {
            "source_records": len(documents),
            "local_runtime_files_present": present_count,
            "license_verified_records": sum(
                1 for item in documents if item["license_verification_status"] == "verified"
            ),
        },
        "interpretation_boundary": (
            "This manifest proves the identity of observed local files and records declared source metadata. "
            "It does not itself establish redistribution rights or publisher-license compliance."
        ),
        "documents": documents,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a local corpus provenance manifest.")
    parser.add_argument("--sources", type=Path, default=Path("reports/starter_corpus_sources.json"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports/raw"))
    parser.add_argument("--corpus-manifest", type=Path, default=Path("reports/manifest.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("reports/provenance_manifest.json"))
    args = parser.parse_args()

    output = build_provenance_manifest(args.sources, args.reports_dir, args.corpus_manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
