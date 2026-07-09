#!/usr/bin/env python
"""Evaluate cell-value table QA behaviour."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.evaluate import load_questions
from scripts.run_skill import SkillExecutionError, run_skill
from src.utils import write_json


SPACE_RE = re.compile(r"\s+")


def normalize(text: str) -> str:
    text = text.lower()
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = text.replace("\u00a0", " ")
    return SPACE_RE.sub(" ", text).strip()


def group_hit(text: str, groups: List[List[str]]) -> bool:
    haystack = normalize(text)
    for group in groups:
        if not any(normalize(alias) in haystack for alias in group):
            return False
    return True


def combined_text(result: Dict[str, Any], include_answer: bool = True) -> str:
    parts = []
    if include_answer:
        parts.append(str(result.get("answer", "") or ""))
    for item in result.get("evidence", []) or []:
        parts.append(str(item.get("text", "") or ""))
        for asset in item.get("nearby_assets", []) or []:
            parts.append(str(asset.get("caption", "") or ""))
            parts.append(str(asset.get("text_preview", "") or ""))
    return "\n".join(parts)


def page_hit(evidence: List[Dict[str, Any]], doc_id: str, page: int, window: int) -> bool:
    low = page - window
    high = page + window
    for item in evidence[:5]:
        if item.get("doc_id") != doc_id:
            continue
        if int(item.get("page_start", -999)) <= high and int(item.get("page_end", -999)) >= low:
            return True
    return False


def asset_trace_hit(evidence: List[Dict[str, Any]], asset_id: str | None) -> bool:
    for item in evidence[:5]:
        for asset in item.get("nearby_assets", []) or []:
            if asset_id and asset.get("asset_id") == asset_id:
                return True
    return False


def evaluate_table_cell_qa(
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
        "asset_trace_hit_at_5": 0,
        "answer_cell_value_hit": 0,
        "evidence_cell_value_hit": 0,
        "cell_qa_success": 0,
        "unexpected_errors": 0,
    }
    details = []

    for question in questions:
        result: Dict[str, Any] = {}
        error_code = None
        try:
            result = run_skill(
                mode="answer",
                query=question["question"],
                index_dir=index_dir,
                retrieval_backend=retrieval_backend,
                evidence_top_k=evidence_top_k,
                answer_engine="extractive",
            )
            counts["skill_ok"] += int(bool(result.get("ok")))
        except SkillExecutionError as exc:
            error_code = exc.code
            counts["unexpected_errors"] += 1

        evidence = result.get("evidence", []) or []
        expected_doc = str(question.get("report_id", ""))
        doc_ids = [item.get("doc_id") for item in evidence[:5]]
        doc_ok = expected_doc in doc_ids
        page_ok = page_hit(
            evidence,
            expected_doc,
            int(question.get("expected_page", -999)),
            int(question.get("expected_page_window", 1)),
        )
        asset_ok = asset_trace_hit(evidence, question.get("asset_id"))
        answer_hit = group_hit(str(result.get("answer", "") or ""), question.get("expected_answer_groups", []))
        evidence_hit = group_hit(combined_text(result), question.get("expected_answer_groups", []))
        citation_present = bool(result.get("citations", []))
        success = bool(doc_ok and page_ok and asset_ok and evidence_hit and citation_present)

        counts["doc_hit_at_5"] += int(doc_ok)
        counts["page_hit_at_5"] += int(page_ok)
        counts["asset_trace_hit_at_5"] += int(asset_ok)
        counts["answer_cell_value_hit"] += int(answer_hit)
        counts["evidence_cell_value_hit"] += int(evidence_hit)
        counts["cell_qa_success"] += int(success)

        details.append(
            {
                "qid": question.get("qid"),
                "asset_id": question.get("asset_id"),
                "expected_doc_id": expected_doc,
                "expected_page": question.get("expected_page"),
                "ok": bool(result.get("ok")),
                "error_code": error_code,
                "retrieved_doc_ids_at_5": doc_ids,
                "doc_hit_at_5": doc_ok,
                "page_hit_at_5": page_ok,
                "asset_trace_hit_at_5": asset_ok,
                "answer_cell_value_hit": answer_hit,
                "evidence_cell_value_hit": evidence_hit,
                "cell_qa_success": success,
                "retrieval_backend": result.get("rag_pipeline", {}).get("retrieval_backend", retrieval_backend),
                "reranker_backends": result.get("rag_pipeline", {}).get("reranker_backends", []),
            }
        )

    denom = max(1, len(questions))
    return {
        "questions": len(questions),
        "retrieval_backend": retrieval_backend,
        "evidence_top_k": evidence_top_k,
        "skill_ok_rate": counts["skill_ok"] / denom,
        "doc_hit_rate@5": counts["doc_hit_at_5"] / denom,
        "page_hit_rate@5": counts["page_hit_at_5"] / denom,
        "asset_trace_hit_rate@5": counts["asset_trace_hit_at_5"] / denom,
        "answer_cell_value_hit_rate": counts["answer_cell_value_hit"] / denom,
        "evidence_cell_value_hit_rate": counts["evidence_cell_value_hit"] / denom,
        "cell_qa_success_rate": counts["cell_qa_success"] / denom,
        "unexpected_error_count": counts["unexpected_errors"],
        "counts": counts,
        "details": details,
        "metric_note": (
            "Cell-level table QA checks exact short values in extracted table text previews. "
            "It is stricter than page-level asset proximity but still not human visual QA."
        ),
    }


def write_markdown(summary: Dict[str, Any], output_path: Path) -> None:
    lines = [
        "# Table Cell QA Evaluation Results",
        "",
        f"- Questions: {summary['questions']}",
        f"- Retrieval backend: {summary['retrieval_backend']}",
        f"- Evidence top-k: {summary['evidence_top_k']}",
        f"- Skill OK rate: {summary['skill_ok_rate']:.3f}",
        f"- Document Hit Rate@5: {summary['doc_hit_rate@5']:.3f}",
        f"- Page Hit Rate@5: {summary['page_hit_rate@5']:.3f}",
        f"- Asset Trace Hit Rate@5: {summary['asset_trace_hit_rate@5']:.3f}",
        f"- Answer Cell Value Hit Rate: {summary['answer_cell_value_hit_rate']:.3f}",
        f"- Evidence Cell Value Hit Rate: {summary['evidence_cell_value_hit_rate']:.3f}",
        f"- Cell QA Success Rate: {summary['cell_qa_success_rate']:.3f}",
        f"- Unexpected errors: {summary['unexpected_error_count']}",
        "",
        summary["metric_note"],
        "",
        "## Misses",
        "",
    ]
    misses = [item for item in summary["details"] if not item["cell_qa_success"]]
    if not misses:
        lines.append("None.")
    for item in misses:
        lines.extend(
            [
                f"### {item['qid']}",
                f"- Expected asset: {item['asset_id']}",
                f"- Error code: {item['error_code']}",
                f"- Retrieved doc_ids@5: {', '.join(str(x) for x in item['retrieved_doc_ids_at_5'])}",
                f"- Doc/Page/Asset/Cell: {item['doc_hit_at_5']}/{item['page_hit_at_5']}/{item['asset_trace_hit_at_5']}/{item['evidence_cell_value_hit']}",
                "",
            ]
        )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate table cell-value QA.")
    parser.add_argument("--questions", type=Path, default=Path("evaluation/radiotherapy_table_cell_questions.json"))
    parser.add_argument("--index-dir", type=Path, default=Path("index"))
    parser.add_argument("--retrieval-backend", choices=["auto", "hybrid", "sparse", "routed"], default="routed")
    parser.add_argument("--evidence-top-k", type=int, default=8)
    parser.add_argument("--output-json", type=Path, default=Path("evaluation/table_cell_qa_eval_results.json"))
    parser.add_argument("--output-md", type=Path, default=Path("evaluation/table_cell_qa_eval_results.md"))
    args = parser.parse_args()

    summary = evaluate_table_cell_qa(load_questions(args.questions), args.index_dir, args.retrieval_backend, args.evidence_top_k)
    write_json(args.output_json, summary)
    write_markdown(summary, args.output_md)
    print(json.dumps({k: v for k, v in summary.items() if k != "details"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
