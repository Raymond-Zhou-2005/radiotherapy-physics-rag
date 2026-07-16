#!/usr/bin/env python
"""Compare frozen PyMuPDF outputs with a rebuilt OpenDataLoader runtime.

The script only summarizes already-produced artifacts.  It never opens answer
keys while the RAG system is running, and it does not modify the corpus.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def current_runtime_snapshot(root: Path) -> dict[str, int]:
    manifest = root / "reports" / "manifest.jsonl"
    asset_manifest = read_json(root / "assets" / "extracted" / "asset_manifest.json")
    asset_documents = asset_manifest.get("documents") or []
    return {
        "source_records": count_jsonl(manifest),
        "parsed_files": len(list((root / "parsed").glob("*.jsonl"))),
        "parsed_blocks": sum(count_jsonl(path) for path in (root / "parsed").glob("*.jsonl")),
        "chunk_files": len(list((root / "chunks").glob("*.jsonl"))),
        "indexed_chunks": count_jsonl(root / "index" / "metadata" / "chunk_metadata.jsonl"),
        "asset_documents": len(asset_documents),
        "asset_tables": sum(int(row.get("table_count") or 0) for row in asset_documents),
        "asset_images": sum(int(row.get("image_count") or 0) for row in asset_documents),
    }


def metric_summary(payload: dict[str, Any]) -> dict[str, float | int | None]:
    return {
        "questions": payload.get("questions"),
        "skill_ok_rate": payload.get("skill_ok_rate"),
        "citation_present_rate": payload.get("citation_present_rate"),
        "evidence_contains_gold_option_rate": payload.get("evidence_contains_gold_option_rate"),
        "mcq_option_accuracy": payload.get("mcq_option_accuracy"),
        "mean_total_latency_seconds": payload.get("mean_total_latency_seconds"),
    }


def classify_question_changes(old_payload: dict[str, Any], new_payload: dict[str, Any]) -> dict[str, list[str]]:
    old_by_qid = {str(item["qid"]): item for item in old_payload.get("details") or []}
    new_by_qid = {str(item["qid"]): item for item in new_payload.get("details") or []}
    if set(old_by_qid) != set(new_by_qid):
        raise ValueError("Parser comparison requires identical question IDs in both MCQ results.")

    groups = {"improved": [], "regressed": [], "both_correct": [], "both_incorrect": []}
    for qid in sorted(new_by_qid):
        old_correct = bool(old_by_qid[qid].get("selected_correct"))
        new_correct = bool(new_by_qid[qid].get("selected_correct"))
        if not old_correct and new_correct:
            groups["improved"].append(qid)
        elif old_correct and not new_correct:
            groups["regressed"].append(qid)
        elif new_correct:
            groups["both_correct"].append(qid)
        else:
            groups["both_incorrect"].append(qid)
    return groups


def build_comparison(root: Path, old_snapshot_path: Path, old_mcq_path: Path, new_mcq_path: Path) -> dict[str, Any]:
    old_snapshot = read_json(old_snapshot_path)
    old_mcq = read_json(old_mcq_path)
    new_mcq = read_json(new_mcq_path)
    current_snapshot = current_runtime_snapshot(root)
    changes = classify_question_changes(old_mcq, new_mcq)

    old_metrics = metric_summary(old_mcq)
    new_metrics = metric_summary(new_mcq)
    metric_delta = {
        key: (
            None
            if old_metrics.get(key) is None or new_metrics.get(key) is None
            else float(new_metrics[key]) - float(old_metrics[key])
        )
        for key in old_metrics
        if key != "questions"
    }
    artifact_delta = {
        key: current_snapshot.get(key, 0) - int(old_snapshot.get(key) or 0)
        for key in current_snapshot
    }
    return {
        "comparison_design": {
            "old_parser": "PyMuPDF historical runtime snapshot",
            "new_parser": "OpenDataLoader rebuilt runtime",
            "held_constant": [
                "49 runtime source PDFs",
                "100-question public external MCQ file",
                "auto retrieval configuration",
                "BAAI/bge-reranker-base cross-encoder option selector",
                "top-6 evidence and evidence-only skill mode",
            ],
            "interpretation_boundary": (
                "This is a public answer-keyed development comparison, not a hidden test, "
                "a Codex-host evaluation, expert grading, or clinical validation."
            ),
        },
        "old_runtime_snapshot": old_snapshot,
        "opendataloader_runtime_snapshot": current_snapshot,
        "runtime_artifact_delta": artifact_delta,
        "old_mcq_metrics": old_metrics,
        "opendataloader_mcq_metrics": new_metrics,
        "mcq_metric_delta": metric_delta,
        "question_outcome_changes": {key: {"count": len(value), "qids": value} for key, value in changes.items()},
    }


def write_markdown(result: dict[str, Any], output_path: Path) -> None:
    old = result["old_runtime_snapshot"]
    new = result["opendataloader_runtime_snapshot"]
    old_metrics = result["old_mcq_metrics"]
    new_metrics = result["opendataloader_mcq_metrics"]
    changes = result["question_outcome_changes"]
    lines = [
        "# PyMuPDF vs OpenDataLoader Comparison",
        "",
        "## Design",
        "",
        "- Old parser: PyMuPDF historical runtime snapshot.",
        "- New parser: OpenDataLoader rebuilt runtime.",
        "- Held constant: 49 runtime PDFs, the 100-question public MCQ set, auto retrieval, cross-encoder option selection, top-6 evidence, and evidence mode.",
        "- Boundary: this is public answer-keyed development evidence, not a hidden test, Codex-host run, expert grade, or clinical validation.",
        "",
        "## Runtime Artifacts",
        "",
        "| Measure | PyMuPDF | OpenDataLoader | Delta |",
        "|---|---:|---:|---:|",
    ]
    for key in ("source_records", "parsed_files", "parsed_blocks", "chunk_files", "indexed_chunks", "asset_documents", "asset_tables", "asset_images"):
        lines.append(f"| {key} | {old.get(key, 0)} | {new.get(key, 0)} | {new.get(key, 0) - int(old.get(key) or 0):+d} |")

    lines.extend(
        [
            "",
            "## Public MCQ Result",
            "",
            "| Metric | PyMuPDF | OpenDataLoader | Delta |",
            "|---|---:|---:|---:|",
        ]
    )
    for key in ("skill_ok_rate", "citation_present_rate", "evidence_contains_gold_option_rate", "mcq_option_accuracy", "mean_total_latency_seconds"):
        old_value = old_metrics.get(key)
        new_value = new_metrics.get(key)
        delta = result["mcq_metric_delta"].get(key)
        lines.append(f"| {key} | {old_value:.3f} | {new_value:.3f} | {delta:+.3f} |")

    lines.extend(
        [
            "",
            "## Per-question Outcome Changes",
            "",
            f"- Improved: {changes['improved']['count']}",
            f"- Regressed: {changes['regressed']['count']}",
            f"- Correct in both: {changes['both_correct']['count']}",
            f"- Incorrect in both: {changes['both_incorrect']['count']}",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare frozen PyMuPDF and rebuilt OpenDataLoader artifacts.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--old-snapshot", type=Path, default=Path("evaluation/parser_comparison/pymupdf_baseline/runtime_snapshot.json"))
    parser.add_argument("--old-mcq", type=Path, default=Path("evaluation/parser_comparison/pymupdf_baseline/public_mcq_eval_results.json"))
    parser.add_argument("--new-mcq", type=Path, default=Path("evaluation/parser_comparison/opendataloader/public_mcq_eval_results.json"))
    parser.add_argument("--output-json", type=Path, default=Path("evaluation/parser_comparison/opendataloader_vs_pymupdf.json"))
    parser.add_argument("--output-md", type=Path, default=Path("evaluation/parser_comparison/opendataloader_vs_pymupdf.md"))
    args = parser.parse_args()

    result = build_comparison(args.root, args.old_snapshot, args.old_mcq, args.new_mcq)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(result, args.output_md)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
