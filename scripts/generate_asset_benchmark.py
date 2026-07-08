#!/usr/bin/env python
"""Generate a local table/figure asset benchmark from extracted PDF metadata.

The questions use document titles, asset type, page number, and table shape.
They do not copy table cell contents or figure captions into the benchmark file,
so the file can be shared as metadata-derived evaluation scaffolding.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Dict, Iterable, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils import iter_jsonl, write_json


def load_sources(path: Path) -> Dict[str, Dict[str, Any]]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return {record["doc_id"]: record for record in json.load(handle)}


def load_assets(assets_dir: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for path in sorted(assets_dir.glob("*.assets.jsonl")):
        records.extend(iter_jsonl(path))
    return records


def choose_round_robin(records: Iterable[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    by_doc: Dict[str, deque] = defaultdict(deque)
    for record in sorted(
        records,
        key=lambda item: (
            str(item.get("doc_id", "")),
            int(item.get("page", 0)),
            str(item.get("asset_id", "")),
        ),
    ):
        by_doc[str(record.get("doc_id", ""))].append(record)

    selected: List[Dict[str, Any]] = []
    doc_ids = sorted(by_doc)
    while len(selected) < limit:
        made_progress = False
        for doc_id in doc_ids:
            if by_doc[doc_id]:
                selected.append(by_doc[doc_id].popleft())
                made_progress = True
                if len(selected) >= limit:
                    break
        if not made_progress:
            break
    return selected


def asset_label(record: Dict[str, Any]) -> str:
    if record.get("asset_type") == "table":
        rows = record.get("rows")
        columns = record.get("columns")
        if rows is not None and columns is not None:
            return f"detected table with {rows} rows and {columns} columns"
        return "detected table"
    return "detected figure or image"


def build_questions(
    assets: List[Dict[str, Any]],
    sources: Dict[str, Dict[str, Any]],
    max_tables: int,
    max_images: int,
) -> List[Dict[str, Any]]:
    table_records = [
        record for record in assets
        if record.get("asset_type") == "table" and (record.get("rows") or 0) >= 2
    ]
    image_records = [
        record for record in assets
        if record.get("asset_type") == "image"
    ]

    selected = choose_round_robin(table_records, max_tables) + choose_round_robin(image_records, max_images)
    questions: List[Dict[str, Any]] = []
    for record in selected:
        doc_id = str(record.get("doc_id"))
        source = sources.get(doc_id, {})
        title = str(record.get("title") or source.get("title") or doc_id)
        page = int(record.get("page"))
        label = asset_label(record)
        asset_type = str(record.get("asset_type"))
        qid = f"asset_q{len(questions) + 1:04d}"
        questions.append(
            {
                "qid": qid,
                "question": (
                    f"Which indexed evidence is closest to the {label} in {title} on page {page}, "
                    "and what nearby asset metadata should be reported?"
                ),
                "type": f"{asset_type}_asset_lookup",
                "report_id": doc_id,
                "expected_page": page,
                "expected_page_window": 1,
                "asset_id": record.get("asset_id"),
                "asset_type": asset_type,
                "expected_abstain": False,
                "source_basis": "Local PDF asset metadata extracted from public source PDFs; question text uses title, asset type, page, and table shape only.",
                "source_urls": [source.get("source_url")] if source.get("source_url") else [],
                "source_note": "Asset benchmark checks retrieval to the correct document/page neighborhood and whether nearby asset metadata is surfaced.",
                "benchmark_profile": "asset_metadata",
            }
        )
    return questions


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate table/figure asset benchmark questions.")
    parser.add_argument("--assets-dir", type=Path, default=Path("assets/extracted"))
    parser.add_argument("--sources", type=Path, default=Path("reports/starter_corpus_sources.json"))
    parser.add_argument("--output", type=Path, default=Path("evaluation/radiotherapy_asset_questions.json"))
    parser.add_argument("--max-tables", type=int, default=60)
    parser.add_argument("--max-images", type=int, default=60)
    args = parser.parse_args()

    questions = build_questions(
        assets=load_assets(args.assets_dir),
        sources=load_sources(args.sources),
        max_tables=args.max_tables,
        max_images=args.max_images,
    )
    write_json(args.output, questions)
    print(json.dumps({"ok": True, "questions": len(questions), "output": str(args.output)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
