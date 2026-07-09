#!/usr/bin/env python
"""Evaluate realistic agent-facing skill tasks."""

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
    text = text.lower().replace("\u2013", "-").replace("\u2014", "-")
    return SPACE_RE.sub(" ", text).strip()


def group_hit(text: str, groups: List[List[str]]) -> bool:
    if not groups:
        return True
    haystack = normalize(text)
    for group in groups:
        if not any(normalize(alias) in haystack for alias in group):
            return False
    return True


def combined_text(result: Dict[str, Any]) -> str:
    parts = [str(result.get("answer", "") or "")]
    for item in result.get("evidence", []) or []:
        parts.append(str(item.get("text", "") or ""))
        for asset in item.get("nearby_assets", []) or []:
            parts.append(str(asset.get("caption", "") or ""))
            parts.append(str(asset.get("text_preview", "") or ""))
    return "\n".join(parts)


def asset_trace_hit(evidence: List[Dict[str, Any]], asset_id: str | None) -> bool:
    if not asset_id:
        return True
    for item in evidence[:5]:
        for asset in item.get("nearby_assets", []) or []:
            if asset.get("asset_id") == asset_id:
                return True
    return False


def evaluate_agent_tasks(
    tasks: List[Dict[str, Any]],
    index_dir: Path,
    retrieval_backend: str,
    evidence_top_k: int,
) -> Dict[str, Any]:
    counts = {
        "tasks": len(tasks),
        "in_scope": 0,
        "ood": 0,
        "structured_success": 0,
        "doc_hit_at_5": 0,
        "citation_success": 0,
        "bundle_prompt_success": 0,
        "asset_trace_success": 0,
        "answer_value_success": 0,
        "abstention_success": 0,
        "task_success": 0,
        "unexpected_errors": 0,
    }
    details = []

    for task in tasks:
        expected_abstain = bool(task.get("expected_abstain"))
        counts["ood" if expected_abstain else "in_scope"] += 1
        result: Dict[str, Any] = {}
        error_code = None
        structured_success = False
        abstention_success = False

        try:
            result = run_skill(
                mode=task.get("mode", "evidence"),
                query=task["question"],
                index_dir=index_dir,
                retrieval_backend=retrieval_backend,
                evidence_top_k=evidence_top_k,
                answer_engine="extractive",
            )
            structured_success = bool(result.get("ok"))
            if expected_abstain:
                error_code = "answered_expected_abstain"
        except SkillExecutionError as exc:
            error_code = exc.code
            abstention_success = expected_abstain and exc.code in {"insufficient_evidence", "out_of_scope"}
            if not abstention_success:
                counts["unexpected_errors"] += 1

        evidence = result.get("evidence", []) or []
        retrieved_docs = [item.get("doc_id") for item in evidence[:5]]
        expected_docs = task.get("expected_doc_ids", []) or []
        doc_hit = bool(not expected_docs or any(doc in retrieved_docs for doc in expected_docs))
        citation_success = bool(not task.get("expected_citations") or result.get("citations"))
        bundle_success = bool(not task.get("expected_bundle_prompt") or result.get("prompt_for_medgemma"))
        asset_success = asset_trace_hit(evidence, task.get("expected_asset_id"))
        answer_success = group_hit(combined_text(result), task.get("expected_answer_groups", []))

        if expected_abstain:
            task_success = abstention_success
        else:
            task_success = bool(
                structured_success and doc_hit and citation_success and bundle_success and asset_success and answer_success
            )

        counts["structured_success"] += int(structured_success)
        counts["doc_hit_at_5"] += int(doc_hit and not expected_abstain)
        counts["citation_success"] += int(citation_success and not expected_abstain)
        counts["bundle_prompt_success"] += int(bundle_success and not expected_abstain)
        counts["asset_trace_success"] += int(asset_success and not expected_abstain)
        counts["answer_value_success"] += int(answer_success and not expected_abstain)
        counts["abstention_success"] += int(abstention_success)
        counts["task_success"] += int(task_success)

        details.append(
            {
                "qid": task.get("qid"),
                "task": task.get("task"),
                "mode": task.get("mode"),
                "expected_abstain": expected_abstain,
                "ok": bool(result.get("ok")),
                "error_code": error_code,
                "retrieved_doc_ids_at_5": retrieved_docs,
                "doc_hit_at_5": doc_hit,
                "citation_success": citation_success,
                "bundle_prompt_success": bundle_success,
                "asset_trace_success": asset_success,
                "answer_value_success": answer_success,
                "abstention_success": abstention_success,
                "task_success": task_success,
                "retrieval_backend": result.get("rag_pipeline", {}).get("retrieval_backend", retrieval_backend),
                "reranker_backends": result.get("rag_pipeline", {}).get("reranker_backends", []),
            }
        )

    denom = max(1, len(tasks))
    in_scope = max(1, counts["in_scope"])
    ood = max(1, counts["ood"])
    return {
        "tasks": len(tasks),
        "retrieval_backend": retrieval_backend,
        "evidence_top_k": evidence_top_k,
        "task_success_rate": counts["task_success"] / denom,
        "structured_success_rate": counts["structured_success"] / denom,
        "doc_hit_rate@5": counts["doc_hit_at_5"] / in_scope,
        "citation_success_rate": counts["citation_success"] / in_scope,
        "bundle_prompt_success_rate": counts["bundle_prompt_success"] / in_scope,
        "asset_trace_success_rate": counts["asset_trace_success"] / in_scope,
        "answer_value_success_rate": counts["answer_value_success"] / in_scope,
        "ood_abstention_success_rate": counts["abstention_success"] / ood,
        "unexpected_error_count": counts["unexpected_errors"],
        "counts": counts,
        "details": details,
        "metric_note": "Agent-task evaluation checks reusable skill contract behaviour, not only retrieval recall.",
    }


def write_markdown(summary: Dict[str, Any], output_path: Path) -> None:
    lines = [
        "# Agent Task Evaluation Results",
        "",
        f"- Tasks: {summary['tasks']}",
        f"- Retrieval backend: {summary['retrieval_backend']}",
        f"- Task success rate: {summary['task_success_rate']:.3f}",
        f"- Structured success rate: {summary['structured_success_rate']:.3f}",
        f"- Document Hit Rate@5: {summary['doc_hit_rate@5']:.3f}",
        f"- Citation success rate: {summary['citation_success_rate']:.3f}",
        f"- Bundle prompt success rate: {summary['bundle_prompt_success_rate']:.3f}",
        f"- Asset trace success rate: {summary['asset_trace_success_rate']:.3f}",
        f"- Answer value success rate: {summary['answer_value_success_rate']:.3f}",
        f"- OOD abstention success rate: {summary['ood_abstention_success_rate']:.3f}",
        f"- Unexpected errors: {summary['unexpected_error_count']}",
        "",
        summary["metric_note"],
        "",
        "## Failed Tasks",
        "",
    ]
    failures = [item for item in summary["details"] if not item["task_success"]]
    if not failures:
        lines.append("None.")
    for item in failures:
        lines.extend(
            [
                f"### {item['qid']}",
                f"- Error code: {item['error_code']}",
                f"- Retrieved doc_ids@5: {', '.join(str(x) for x in item['retrieved_doc_ids_at_5'])}",
                f"- Contract flags: doc={item['doc_hit_at_5']}, citation={item['citation_success']}, bundle={item['bundle_prompt_success']}, asset={item['asset_trace_success']}, answer={item['answer_value_success']}, abstain={item['abstention_success']}",
                "",
            ]
        )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate realistic agent-facing tasks.")
    parser.add_argument("--tasks", type=Path, default=Path("evaluation/radiotherapy_agent_tasks.json"))
    parser.add_argument("--index-dir", type=Path, default=Path("index"))
    parser.add_argument("--retrieval-backend", choices=["auto", "hybrid", "sparse", "routed"], default="routed")
    parser.add_argument("--evidence-top-k", type=int, default=8)
    parser.add_argument("--output-json", type=Path, default=Path("evaluation/agent_task_eval_results.json"))
    parser.add_argument("--output-md", type=Path, default=Path("evaluation/agent_task_eval_results.md"))
    args = parser.parse_args()

    summary = evaluate_agent_tasks(load_questions(args.tasks), args.index_dir, args.retrieval_backend, args.evidence_top_k)
    write_json(args.output_json, summary)
    write_markdown(summary, args.output_md)
    print(json.dumps({k: v for k, v in summary.items() if k != "details"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
