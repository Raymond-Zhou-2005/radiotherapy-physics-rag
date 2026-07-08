#!/usr/bin/env python
"""Evaluate table/figure asset lookup behaviour.

This is an asset-proximity evaluation: it checks whether evidence retrieval
lands in the expected document and page neighborhood, and whether the skill
surfaces nearby asset metadata. It is not a visual question answering judge.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.evaluate import load_questions
from scripts.run_skill import SkillExecutionError, collect_evidence_with_backend, run_skill
from src.utils import write_json


def page_hit(evidence: List[Dict[str, Any]], doc_id: str, page: int, window: int) -> bool:
    low = page - window
    high = page + window
    for item in evidence[:5]:
        if item.get("doc_id") != doc_id:
            continue
        if int(item.get("page_start", -999)) <= high and int(item.get("page_end", -999)) >= low:
            return True
    return False


def asset_trace_hit(evidence: List[Dict[str, Any]], asset_id: str | None, asset_type: str | None) -> tuple[bool, bool]:
    exact = False
    type_match = False
    for item in evidence[:5]:
        for asset in item.get("nearby_assets", []) or []:
            if asset_id and asset.get("asset_id") == asset_id:
                exact = True
            if asset_type and asset.get("asset_type") == asset_type:
                type_match = True
    return exact, type_match


def flatten_raw_evidence(raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    flattened = []
    for item in raw:
        chunk = item.get("chunk", {})
        flattened.append(
            {
                "chunk_id": chunk.get("chunk_id"),
                "doc_id": chunk.get("doc_id"),
                "page_start": chunk.get("page_start"),
                "page_end": chunk.get("page_end"),
                "nearby_assets": [],
            }
        )
    return flattened


def evaluate_asset_qa(
    questions: List[Dict[str, Any]],
    index_dir: Path,
    retrieval_backend: str,
    evidence_top_k: int,
) -> Dict[str, Any]:
    counts = {
        "questions": len(questions),
        "skill_ok": 0,
        "doc_hit_at_5": 0,
        "page_hit_at_5": 0,
        "asset_id_trace_hit_at_5": 0,
        "asset_type_trace_hit_at_5": 0,
        "unexpected_errors": 0,
    }
    details = []

    for question in questions:
        expected_doc = question.get("report_id")
        expected_page = int(question.get("expected_page", -999))
        window = int(question.get("expected_page_window", 1))
        evidence: List[Dict[str, Any]] = []
        error_code = None
        actual_backend = retrieval_backend

        try:
            result = run_skill(
                mode="evidence",
                query=question["question"],
                index_dir=index_dir,
                retrieval_backend=retrieval_backend,
                evidence_top_k=evidence_top_k,
            )
            counts["skill_ok"] += 1
            evidence = result.get("evidence", [])
            actual_backend = result.get("rag_pipeline", {}).get("retrieval_backend", retrieval_backend)
        except SkillExecutionError as exc:
            error_code = exc.code
            try:
                raw, actual_backend, _ = collect_evidence_with_backend(
                    question["question"],
                    index_dir=index_dir,
                    retrieval_backend=retrieval_backend,
                    evidence_top_k=evidence_top_k,
                )
                evidence = flatten_raw_evidence(raw)
            except Exception:
                counts["unexpected_errors"] += 1

        doc_ids = [item.get("doc_id") for item in evidence[:5]]
        doc_ok = bool(expected_doc and expected_doc in doc_ids)
        page_ok = page_hit(evidence, str(expected_doc), expected_page, window)
        exact_asset_ok, type_asset_ok = asset_trace_hit(
            evidence,
            question.get("asset_id"),
            question.get("asset_type"),
        )

        counts["doc_hit_at_5"] += int(doc_ok)
        counts["page_hit_at_5"] += int(page_ok)
        counts["asset_id_trace_hit_at_5"] += int(exact_asset_ok)
        counts["asset_type_trace_hit_at_5"] += int(type_asset_ok)
        details.append(
            {
                "qid": question.get("qid"),
                "asset_id": question.get("asset_id"),
                "asset_type": question.get("asset_type"),
                "expected_doc_id": expected_doc,
                "expected_page": expected_page,
                "retrieved_doc_ids_at_5": doc_ids,
                "doc_hit_at_5": doc_ok,
                "page_hit_at_5": page_ok,
                "asset_id_trace_hit_at_5": exact_asset_ok,
                "asset_type_trace_hit_at_5": type_asset_ok,
                "error_code": error_code,
                "retrieval_backend": actual_backend,
            }
        )

    denom = max(1, len(questions))
    return {
        "questions": len(questions),
        "retrieval_backend": retrieval_backend,
        "skill_ok_rate": counts["skill_ok"] / denom,
        "doc_hit_rate@5": counts["doc_hit_at_5"] / denom,
        "page_hit_rate@5": counts["page_hit_at_5"] / denom,
        "asset_id_trace_hit_rate@5": counts["asset_id_trace_hit_at_5"] / denom,
        "asset_type_trace_hit_rate@5": counts["asset_type_trace_hit_at_5"] / denom,
        "unexpected_error_count": counts["unexpected_errors"],
        "counts": counts,
        "details": details,
    }


def write_markdown(summary: Dict[str, Any], output_path: Path) -> None:
    lines = [
        "# Asset QA Evaluation Results",
        "",
        f"- Questions: {summary['questions']}",
        f"- Retrieval backend: {summary['retrieval_backend']}",
        f"- Skill OK rate: {summary['skill_ok_rate']:.3f}",
        f"- Document Hit Rate@5: {summary['doc_hit_rate@5']:.3f}",
        f"- Page Hit Rate@5: {summary['page_hit_rate@5']:.3f}",
        f"- Asset ID Trace Hit Rate@5: {summary['asset_id_trace_hit_rate@5']:.3f}",
        f"- Asset Type Trace Hit Rate@5: {summary['asset_type_trace_hit_rate@5']:.3f}",
        f"- Unexpected errors: {summary['unexpected_error_count']}",
        "",
        "This evaluates table/figure metadata proximity, not visual interpretation.",
        "",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate table/figure asset lookup.")
    parser.add_argument("--questions", type=Path, default=Path("evaluation/radiotherapy_asset_questions.json"))
    parser.add_argument("--index-dir", type=Path, default=Path("index"))
    parser.add_argument("--retrieval-backend", choices=["auto", "hybrid", "sparse", "routed"], default="routed")
    parser.add_argument("--evidence-top-k", type=int, default=8)
    parser.add_argument("--output-json", type=Path, default=Path("evaluation/asset_qa_eval_results.json"))
    parser.add_argument("--output-md", type=Path, default=Path("evaluation/asset_qa_eval_results.md"))
    args = parser.parse_args()

    summary = evaluate_asset_qa(load_questions(args.questions), args.index_dir, args.retrieval_backend, args.evidence_top_k)
    write_json(args.output_json, summary)
    write_markdown(summary, args.output_md)
    print(json.dumps({k: v for k, v in summary.items() if k != "details"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
