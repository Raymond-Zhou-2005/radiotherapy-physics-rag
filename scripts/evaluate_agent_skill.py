#!/usr/bin/env python
"""Evaluate the agent-facing skill contract end to end without an LLM API."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.evaluate import load_questions
from scripts.run_skill import SkillExecutionError, run_skill


def evaluate_agent_skill(
    questions: List[Dict],
    index_dir: Path,
    retrieval_backend: str = "routed",
    evidence_top_k: int = 5,
) -> Dict:
    details = []
    counts = {
        "tool_success": 0,
        "in_scope": 0,
        "ood": 0,
        "doc_hit_at_5": 0,
        "citation_present": 0,
        "expected_abstain_success": 0,
        "unexpected_error": 0,
    }

    for question in questions:
        expected_doc_id = question.get("report_id")
        expected_abstain = bool(question.get("expected_abstain"))
        if expected_abstain:
            counts["ood"] += 1
        else:
            counts["in_scope"] += 1

        try:
            result = run_skill(
                mode="evidence",
                query=question["question"],
                index_dir=index_dir,
                retrieval_backend=retrieval_backend,
                evidence_top_k=evidence_top_k,
            )
            ok = bool(result.get("ok"))
            counts["tool_success"] += 1 if ok else 0
            evidence = result.get("evidence", [])
            citations = result.get("citations", [])
            retrieved_docs = [item.get("doc_id") for item in evidence]
            doc_hit = bool(expected_doc_id and expected_doc_id in retrieved_docs[:5])
            citation_present = bool(citations)
            abstain_success = expected_abstain and result.get("error", {}).get("code") == "insufficient_evidence"

            if doc_hit:
                counts["doc_hit_at_5"] += 1
            if citation_present and not expected_abstain:
                counts["citation_present"] += 1
            if abstain_success:
                counts["expected_abstain_success"] += 1

            details.append(
                {
                    "qid": question["qid"],
                    "question": question["question"],
                    "expected_doc_id": expected_doc_id,
                    "expected_abstain": expected_abstain,
                    "ok": ok,
                    "error_code": result.get("error", {}).get("code"),
                    "retrieved_doc_ids": retrieved_docs,
                    "doc_hit_at_5": doc_hit,
                    "citation_present": citation_present,
                    "retrieval_backend": result.get("rag_pipeline", {}).get("retrieval_backend"),
                }
            )
        except SkillExecutionError as exc:
            abstain_success = expected_abstain and exc.code == "insufficient_evidence"
            if abstain_success:
                counts["expected_abstain_success"] += 1
            else:
                counts["unexpected_error"] += 1
            details.append(
                {
                    "qid": question["qid"],
                    "question": question["question"],
                    "expected_doc_id": expected_doc_id,
                    "expected_abstain": expected_abstain,
                    "ok": False,
                    "error_code": exc.code,
                    "retrieved_doc_ids": [],
                    "doc_hit_at_5": False,
                    "citation_present": False,
                    "retrieval_backend": retrieval_backend,
                }
            )

    in_scope = counts["in_scope"]
    ood = counts["ood"]
    summary = {
        "questions": len(questions),
        "retrieval_backend": retrieval_backend,
        "tool_success_rate": counts["tool_success"] / len(questions) if questions else 0.0,
        "document_hit_rate@5": counts["doc_hit_at_5"] / in_scope if in_scope else 0.0,
        "citation_present_rate": counts["citation_present"] / in_scope if in_scope else 0.0,
        "ood_abstention_success_rate": counts["expected_abstain_success"] / ood if ood else 0.0,
        "unexpected_error_count": counts["unexpected_error"],
        "counts": counts,
        "details": details,
    }
    return summary


def write_markdown(summary: Dict, output_path: Path) -> None:
    lines = [
        "# Agent Skill Evaluation Results",
        "",
        f"- Questions: {summary['questions']}",
        f"- Retrieval backend: {summary['retrieval_backend']}",
        f"- Tool success rate: {summary['tool_success_rate']:.3f}",
        f"- Document Hit Rate@5: {summary['document_hit_rate@5']:.3f}",
        f"- Citation present rate: {summary['citation_present_rate']:.3f}",
        f"- OOD abstention success rate: {summary['ood_abstention_success_rate']:.3f}",
        f"- Unexpected errors: {summary['unexpected_error_count']}",
        "",
        "## Failed In-Scope Document@5 Cases",
        "",
    ]
    failures = [
        item
        for item in summary["details"]
        if not item["expected_abstain"] and not item["doc_hit_at_5"]
    ]
    if not failures:
        lines.append("None.")
    for item in failures[:100]:
        lines.extend(
            [
                f"### {item['qid']}",
                f"- Expected doc_id: {item['expected_doc_id']}",
                f"- Error code: {item['error_code']}",
                f"- Retrieved doc_ids: {', '.join(item['retrieved_doc_ids'])}",
                "",
            ]
        )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate agent-facing skill behaviour.")
    parser.add_argument("--questions", type=Path, default=Path("evaluation/public_credible_questions.json"))
    parser.add_argument("--index-dir", type=Path, default=Path("index"))
    parser.add_argument("--retrieval-backend", choices=["auto", "hybrid", "sparse", "routed"], default="routed")
    parser.add_argument("--output-json", type=Path, default=Path("evaluation/agent_skill_eval_results.json"))
    parser.add_argument("--output-md", type=Path, default=Path("evaluation/agent_skill_eval_results.md"))
    args = parser.parse_args()

    summary = evaluate_agent_skill(load_questions(args.questions), args.index_dir, args.retrieval_backend)
    args.output_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(summary, args.output_md)
    print(json.dumps({k: v for k, v in summary.items() if k != "details"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
