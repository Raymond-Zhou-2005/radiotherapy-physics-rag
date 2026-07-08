#!/usr/bin/env python
"""Build a filesystem navigator skill over indexed radiotherapy chunks.

The navigator is intentionally metadata-first: it writes topic summaries,
document counts, section/page pointers, and chunk IDs. Full evidence text stays
in the local chunk metadata and is retrieved through MCP/CLI tools.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_skill import format_citation_text, format_page_range
from src.utils import ensure_dir, iter_jsonl, write_jsonl


TAXONOMY: dict[str, dict[str, Any]] = {
    "reference-dosimetry": {
        "name": "Reference dosimetry and calibration",
        "description": "Absorbed dose, ionization chambers, beam quality, calibration coefficients, small fields, and reference dosimeters.",
        "keywords": [
            "dosimetry", "absorbed dose", "calibration", "ionization", "chamber",
            "beam quality", "reference dosimeter", "small field", "trs 398", "trs 469",
            "tg-51", "output factor",
        ],
    },
    "brachytherapy": {
        "name": "Brachytherapy physics and source calibration",
        "description": "Brachytherapy source calibration, dose calculation, QA, mesh, ocular plaque, and HDR/LDR workflow.",
        "keywords": ["brachytherapy", "source calibration", "hdr", "ldr", "ocular", "plaque", "mesh", "photon and beta"],
    },
    "treatment-planning": {
        "name": "Treatment planning systems and calculation QA",
        "description": "TPS commissioning, acceptance testing, beam models, monitor units, plan review, IMRT/VMAT QA, and calculation verification.",
        "keywords": [
            "treatment planning", "tps", "commissioning", "acceptance", "beam model",
            "dose calculation", "monitor unit", "mu", "imrt", "vmat", "plan review",
            "record and verify",
        ],
    },
    "imaging-and-localization": {
        "name": "Imaging, IGRT, registration, and localization",
        "description": "kV imaging, CT simulation, CBCT, image registration, fusion, localization, surface guidance, and imaging dose.",
        "keywords": ["imaging", "igrt", "ct", "cbct", "registration", "fusion", "localization", "setup", "surface guided", "image guidance"],
    },
    "quality-management-and-safety": {
        "name": "Quality management, audits, and safety",
        "description": "Radiotherapy QA/QC, FMEA, chart review, audit, QUATRO, risk analysis, event narratives, and programme safety.",
        "keywords": ["quality", "qa", "qc", "audit", "quatro", "fmea", "risk", "safety", "chart review", "failure mode", "process map"],
    },
    "equipment-and-facilities": {
        "name": "Equipment, facilities, and programme design",
        "description": "Linacs, radiotherapy equipment, facility design, shielding, staffing, infrastructure, and programme implementation.",
        "keywords": ["linac", "accelerator", "equipment", "facility", "shielding", "staffing", "programme", "infrastructure", "room"],
    },
    "nomenclature-and-data": {
        "name": "Nomenclature, data transfer, and interoperability",
        "description": "TG-263 style naming, data transfer, structure naming, electronic charting, and interoperability.",
        "keywords": ["nomenclature", "structure", "naming", "data transfer", "interoperability", "electronic chart", "tg263"],
    },
    "biological-models-and-response": {
        "name": "Biological models and response",
        "description": "TCP, NTCP, biological response models, RBE, radiobiology, and biologically based optimization QA.",
        "keywords": ["tcp", "ntcp", "biological", "biologically", "radiobiology", "rbe", "response model", "biophysical", "model qa", "optimization"],
    },
    "nontarget-dose-and-radiation-protection": {
        "name": "Nontarget dose and radiation protection",
        "description": "Out-of-field dose, imaging dose, induced activity, radiation protection, shielding, and safety of sources.",
        "keywords": ["nontarget", "out-of-field", "radiation protection", "induced", "safety of sources", "shielding", "imaging dose"],
    },
    "education-and-foundations": {
        "name": "Education and physics foundations",
        "description": "General radiation oncology physics foundations, residency training scope, definitions, and teaching reference material.",
        "keywords": ["handbook", "training", "resident", "education", "fundamentals", "half-life", "radioactive decay"],
    },
}


def _norm(text: Any) -> str:
    return str(text or "").lower()


def _score_topic(record: dict[str, Any], topic: dict[str, Any]) -> int:
    haystack = " ".join(
        _norm(record.get(key))
        for key in ("doc_id", "title", "section", "subsection", "chunk_kind")
    )
    haystack += " " + " ".join(_norm(tag) for tag in record.get("tags", []))
    score = 0
    for keyword in topic["keywords"]:
        if keyword in haystack:
            score += 3 if " " in keyword else 1
    return score


def assign_topic(record: dict[str, Any]) -> str:
    scored = [(_score_topic(record, topic), slug) for slug, topic in TAXONOMY.items()]
    scored.sort(reverse=True)
    if scored and scored[0][0] > 0:
        return scored[0][1]
    return "education-and-foundations"


def load_manifest(path: Path) -> dict[str, dict[str, Any]]:
    docs: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return docs
    for item in iter_jsonl(path):
        if item.get("doc_id"):
            docs[item["doc_id"]] = item
    return docs


def build_rows(metadata_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in iter_jsonl(metadata_path):
        topic = assign_topic(record)
        page_range = format_page_range(record.get("page_start", 0), record.get("page_end", 0))
        rows.append(
            {
                "topic": topic,
                "chunk_id": record.get("chunk_id"),
                "doc_id": record.get("doc_id"),
                "document": record.get("title"),
                "section": record.get("section"),
                "subsection": record.get("subsection"),
                "page_start": record.get("page_start"),
                "page_end": record.get("page_end"),
                "page_range": page_range,
                "chunk_kind": record.get("chunk_kind", "standard"),
                "tags": record.get("tags", []),
                "citation": format_citation_text(
                    evidence_id="NAV",
                    document=str(record.get("title") or ""),
                    section=str(record.get("section") or ""),
                    page_range=page_range,
                    chunk_id=str(record.get("chunk_id") or ""),
                ),
            }
        )
    return rows


def _safe_name(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text.strip("-") or "item"


def write_root_skill(root: Path, topic_counts: Counter[str], doc_counts: dict[str, int]) -> None:
    lines = [
        "---",
        "name: radiotherapy-physics-navigator",
        "description: >",
        "  Navigate the local radiotherapy physics evidence corpus by topic before retrieving full evidence chunks. Use when questions require corpus overview, multi-report synthesis, source triage, or agent-visible RAG navigation.",
        "---",
        "",
        "# Radiotherapy Physics Navigator",
        "",
        "This navigator is a metadata map over the local indexed corpus. Use it to decide where to look, then retrieve full evidence with `get_chunk` or `query_reports`.",
        "",
        "## Hard Rules",
        "",
        "- Treat this navigator as routing metadata, not as answer evidence.",
        "- Every factual answer must cite chunks returned by `get_chunk` or `query_reports`.",
        "- Scan at least two plausible topic branches for broad synthesis questions.",
        "- Use `entity_index.json` for report IDs, topic names, and recurring terms.",
        "",
        "## Topic Branches",
        "",
    ]
    for slug, meta in TAXONOMY.items():
        lines.append(f"- `topics/{slug}/INDEX.md` ({topic_counts.get(slug, 0)} chunks, {doc_counts.get(slug, 0)} docs): {meta['description']}")
    lines.extend(
        [
            "",
            "## Full Metadata Indexes",
            "",
            "- `topic_indexes/<topic>.jsonl`: chunk-level pointers for grep/search.",
            "- `all_chunks_index.jsonl`: all navigator rows.",
            "- `entity_index.json`: report IDs, topic paths, and high-frequency terms.",
        ]
    )
    (root / "SKILL.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_topic_index(topic_dir: Path, slug: str, rows: list[dict[str, Any]]) -> None:
    meta = TAXONOMY[slug]
    by_doc: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_doc[str(row["doc_id"])].append(row)

    lines = [
        "---",
        f"name: {slug}",
        "description: >",
        f"  {meta['description']}",
        "level: 1",
        f"num_documents: {len(by_doc)}",
        f"num_chunks: {len(rows)}",
        "---",
        "",
        f"# {meta['name']}",
        "",
        meta["description"],
        "",
        "## How To Use",
        "",
        f"1. Grep `../../topic_indexes/{slug}.jsonl` for report IDs, sections, or terms.",
        "2. Pick candidate `chunk_id` values.",
        "3. Retrieve full text through `get_chunk` or `query_reports` before answering.",
        "",
        "## Documents",
        "",
    ]
    for doc_id, doc_rows in sorted(by_doc.items(), key=lambda item: (-len(item[1]), item[0])):
        title = doc_rows[0].get("document") or doc_id
        sections = []
        seen = set()
        for row in doc_rows:
            sec = row.get("section") or "UNKNOWN"
            if sec in seen:
                continue
            seen.add(sec)
            sections.append(sec)
            if len(sections) >= 5:
                break
        example_ids = ", ".join(str(row["chunk_id"]) for row in doc_rows[:5])
        lines.append(f"- `{doc_id}` ({len(doc_rows)} chunks): {title}")
        lines.append(f"  - sections: {'; '.join(sections)}")
        lines.append(f"  - example chunk_ids: {example_ids}")
    lines.append("")
    topic_dir.mkdir(parents=True, exist_ok=True)
    (topic_dir / "INDEX.md").write_text("\n".join(lines), encoding="utf-8")


def build_entity_index(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_doc: dict[str, set[str]] = defaultdict(set)
    by_topic: dict[str, set[str]] = defaultdict(set)
    terms: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        doc_id = str(row.get("doc_id"))
        topic = str(row.get("topic"))
        by_doc[doc_id].add(topic)
        by_topic[topic].add(doc_id)
        for field in ("document", "section", "subsection"):
            text = _norm(row.get(field))
            for token in re.findall(r"[a-z][a-z0-9-]{2,}", text):
                if token in {"the", "and", "for", "with", "report", "radiotherapy", "radiation"}:
                    continue
                terms[topic][token] += 1
    return {
        "topics": {
            slug: {
                "path": f"topics/{slug}/INDEX.md",
                "description": TAXONOMY[slug]["description"],
                "doc_ids": sorted(by_topic.get(slug, [])),
                "top_terms": [term for term, _ in terms[slug].most_common(30)],
            }
            for slug in TAXONOMY
        },
        "documents": {
            doc_id: {"topics": sorted(topics)}
            for doc_id, topics in sorted(by_doc.items())
        },
    }


def build_navigator(index_dir: Path, manifest_path: Path, output_dir: Path, skill_dir: Path) -> dict[str, Any]:
    metadata_path = index_dir / "metadata" / "chunk_metadata.jsonl"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Missing chunk metadata: {metadata_path}")
    rows = build_rows(metadata_path)
    manifest = load_manifest(manifest_path)
    for row in rows:
        source = manifest.get(str(row.get("doc_id")))
        if source:
            row["organization"] = source.get("organization")
            row["source_url"] = source.get("source_url")

    ensure_dir(output_dir)
    ensure_dir(output_dir / "topics")
    ensure_dir(output_dir / "topic_indexes")
    write_jsonl(output_dir / "all_chunks_index.jsonl", rows)

    by_topic: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_topic[row["topic"]].append(row)

    topic_counts: Counter[str] = Counter()
    doc_counts: dict[str, int] = {}
    for slug in TAXONOMY:
        topic_rows = by_topic.get(slug, [])
        topic_counts[slug] = len(topic_rows)
        doc_counts[slug] = len({row.get("doc_id") for row in topic_rows})
        write_jsonl(output_dir / "topic_indexes" / f"{slug}.jsonl", topic_rows)
        write_topic_index(output_dir / "topics" / slug, slug, topic_rows)

    entity_index = build_entity_index(rows)
    (output_dir / "entity_index.json").write_text(json.dumps(entity_index, ensure_ascii=False, indent=2), encoding="utf-8")
    write_root_skill(output_dir, topic_counts, doc_counts)

    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_md = [
        "---",
        "name: radiotherapy-physics-navigator",
        "description: Use this skill when Codex needs to navigate the local radiotherapy physics RAG corpus by topic before retrieving evidence, especially for multi-report synthesis, source triage, or topic-tree agent navigation.",
        "---",
        "",
        "# Radiotherapy Physics Navigator",
        "",
        "Read `navigator/SKILL.md` in the project root first. Use navigator files only to choose candidate chunk IDs; retrieve full evidence through MCP `get_chunk` or `query_reports` before answering.",
    ]
    (skill_dir / "SKILL.md").write_text("\n".join(skill_md) + "\n", encoding="utf-8")

    return {
        "ok": True,
        "navigator_dir": str(output_dir),
        "skill_dir": str(skill_dir),
        "chunk_count": len(rows),
        "topic_counts": dict(topic_counts),
        "document_count": len({row.get("doc_id") for row in rows}),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a metadata navigator skill for the local radiotherapy corpus.")
    parser.add_argument("--index-dir", type=Path, default=Path("index"))
    parser.add_argument("--manifest", type=Path, default=Path("reports/manifest.jsonl"))
    parser.add_argument("--output-dir", type=Path, default=Path("navigator"))
    parser.add_argument("--skill-dir", type=Path, default=Path("skills/radiotherapy-physics-navigator"))
    args = parser.parse_args()
    result = build_navigator(args.index_dir, args.manifest, args.output_dir, args.skill_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
