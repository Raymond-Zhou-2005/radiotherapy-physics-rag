#!/usr/bin/env python
"""Build a lightweight ChatGPT Knowledge package from local chunk files."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "document"


def load_starter_titles(root: Path) -> Dict[str, str]:
    path = root / "reports" / "starter_corpus_sources.json"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return {str(item.get("doc_id")): str(item.get("title")) for item in json.load(handle) if item.get("doc_id") and item.get("title")}


def write_report_markdown(doc_id: str, records: List[Dict[str, Any]], output_dir: Path, title_overrides: Dict[str, str]) -> Dict[str, Any]:
    records = sorted(records, key=lambda item: (int(item.get("page_start") or 0), str(item.get("chunk_id", ""))))
    first = records[0]
    title = title_overrides.get(doc_id) or str(first.get("title") or doc_id)
    target = output_dir / f"{slugify(doc_id)}.md"
    lines = [
        f"# {title}",
        "",
        f"- doc_id: `{doc_id}`",
        f"- source_file: `{first.get('source_path', '')}`",
        "- package: ChatGPT Knowledge lightweight corpus",
        "",
        "Use chunk IDs and page ranges when citing this file. Each chunk is an evidence unit generated from the local RAG corpus.",
        "",
    ]
    for item in records:
        chunk_id = item.get("chunk_id", "")
        section = item.get("section", "UNKNOWN")
        subsection = item.get("subsection", "UNKNOWN")
        page_start = item.get("page_start", "")
        page_end = item.get("page_end", "")
        kind = item.get("chunk_kind", "standard")
        tags = ", ".join(item.get("tags", []) or [])
        text = " ".join(str(item.get("text", "")).split())
        lines.extend(
            [
                f"## Chunk {chunk_id}",
                "",
                f"- section: {section}",
                f"- subsection: {subsection}",
                f"- pages: {page_start}-{page_end}",
                f"- chunk_kind: {kind}",
                f"- tags: {tags or 'none'}",
                "",
                text,
                "",
            ]
        )
    target.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return {"doc_id": doc_id, "title": title, "file": target.relative_to(output_dir).as_posix(), "chunks": len(records)}


def build(root: Path, output_dir: Path) -> Dict[str, Any]:
    root = root.resolve()
    output_dir = output_dir.resolve()
    upload_dir = output_dir / "upload_files"
    upload_dir.mkdir(parents=True, exist_ok=True)

    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    title_overrides = load_starter_titles(root)
    for chunk_file in sorted((root / "chunks").glob("*.chunks.jsonl")):
        for record in iter_jsonl(chunk_file):
            grouped[str(record.get("doc_id") or chunk_file.stem.replace(".chunks", ""))].append(record)

    report_entries = []
    for doc_id, records in sorted(grouped.items()):
        if records:
            report_entries.append(write_report_markdown(doc_id, records, upload_dir, title_overrides))

    upload_manifest = {
        "package": "radiotherapy-physics-rag ChatGPT Knowledge",
        "generated_from": "local chunks/",
        "upload_files": report_entries,
        "instructions_file": "custom_gpt_instructions.md",
        "notes": [
            "Upload the Markdown files in upload_files/ to a Custom GPT Knowledge section.",
            "Paste custom_gpt_instructions.md into the GPT Instructions field.",
            "Use starter_questions.md for a quick check that each report is searchable.",
        ],
    }
    (output_dir / "upload_manifest.json").write_text(json.dumps(upload_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_supporting_docs(output_dir, report_entries)
    return {"ok": True, "output_dir": str(output_dir), "upload_file_count": len(report_entries), "upload_files": report_entries}


def write_supporting_docs(output_dir: Path, report_entries: List[Dict[str, Any]]) -> None:
    readme = """# ChatGPT Knowledge Lightweight Package

This folder contains instructions for generating a Custom GPT Knowledge package from the local radiotherapy physics corpus. Generated upload files preserve chunk IDs, report titles, sections, page ranges, and source file metadata so the GPT can answer with traceable report evidence.

Use it in GPT Builder:

1. Build the local corpus from the repository root.
2. Run `python scripts/build_chatgpt_knowledge.py --root .`.
3. Create or edit a Custom GPT.
4. Upload every generated Markdown file in `upload_files/` to Knowledge.
5. Paste `custom_gpt_instructions.md` into Instructions.
6. Start with the questions in `starter_questions.md`.

`upload_manifest.json` is generated locally with the report files and chunk counts.
"""
    instructions = """You are a radiotherapy physics report evidence assistant. Use only the uploaded Knowledge files for claims about report content. Prefer direct evidence from chunk IDs, sections, and page ranges. If the uploaded files do not contain enough evidence, say that the evidence is insufficient and ask for the relevant report to be uploaded.

When answering:
- Start with a concise answer.
- Then list evidence bullets with document title, section, page range, and chunk ID.
- Do not provide medical advice or patient-specific clinical recommendations.
- Do not invent report numbers, page ranges, tolerances, definitions, or recommendations.
- If sources conflict, describe the conflict and cite both chunks.
"""
    starter = """# Starter Questions

- What does the corpus say about in-room kV imaging for patient setup and target localization?
- What responsibilities and QA activities are described for physics support in multi-institutional radiotherapy clinical trials?
- What quality assurance issues arise when biologically related models such as TCP or NTCP are used in treatment planning?
- What should a comprehensive quality assurance programme in radiation oncology include for machines, treatment planning, records, and chart review?
- What essential medical physics topics should a resident learn for external beam radiotherapy?
- How are process mapping, FMEA, and fault-tree analysis used in radiation therapy quality management?
- Why is standardized naming of targets and organs at risk important for radiation oncology data exchange, planning, and clinical trials?
- What staffing, equipment, radiation protection, and safety elements are important when designing a radiotherapy programme?
- How is absorbed dose to water determined for external beam radiotherapy reference dosimetry?
- What commissioning tests are recommended for computerized treatment planning systems used in radiation therapy?
- What physics concepts connect percent depth dose, tissue-air ratio, tissue-phantom ratio, scatter-air ratio, and output factors in external beam radiotherapy?
- How are reference dosimeters calibrated for external beam radiotherapy?
- What should medical physicists review during an on-site visit or quality audit of a radiotherapy centre?
- What elements should an image guided radiotherapy QA programme include for imaging systems, registration, workflow, and safety?
- What types of independent dosimetry audits are used in radiotherapy, and how are audit results interpreted?
- How should nontarget and out-of-field dose be measured, calculated, reduced, and reported?
"""

    (output_dir / "README.md").write_text(readme, encoding="utf-8")
    (output_dir / "custom_gpt_instructions.md").write_text(instructions, encoding="utf-8")
    (output_dir / "starter_questions.md").write_text(starter, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build ChatGPT Knowledge upload files from local chunks.")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "chatgpt_knowledge")
    args = parser.parse_args()

    result = build(args.root, args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
