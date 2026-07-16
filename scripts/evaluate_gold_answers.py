#!/usr/bin/env python
"""Evaluate public gold-answer seed questions against the local skill.

This is not expert grading. It checks whether the skill can retrieve evidence
and whether the extractive answer/evidence contains the short public answer
target.
"""

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
METRIC_KEYS = (
    "skill_ok",
    "citation_present",
    "answer_value_hit",
    "evidence_value_hit",
    "gold_answer_success",
    "unexpected_errors",
)


def normalize(text: str) -> str:
    text = text.lower()
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = text.replace("\u00a0", " ")
    text = SPACE_RE.sub(" ", text)
    return text.strip()


def group_hit(text: str, groups: List[List[str]]) -> bool:
    haystack = normalize(text)
    for group in groups:
        if not any(normalize(alias) in haystack for alias in group):
            return False
    return True


def evidence_text(result: Dict[str, Any]) -> str:
    parts = [str(result.get("answer", "") or "")]
    for item in result.get("evidence", []) or []:
        parts.append(str(item.get("text", "") or ""))
        for asset in item.get("nearby_assets", []) or []:
            parts.append(str(asset.get("caption", "") or ""))
            parts.append(str(asset.get("text_preview", "") or ""))
    return "\n".join(parts)


def empty_counts() -> Dict[str, int]:
    return {"questions": 0, **{key: 0 for key in METRIC_KEYS}}


def summarize_counts(counts: Dict[str, int]) -> Dict[str, Any]:
    denom = max(1, counts["questions"])
    return {
        "questions": counts["questions"],
        "skill_ok_rate": counts["skill_ok"] / denom,
        "citation_present_rate": counts["citation_present"] / denom,
        "answer_value_hit_rate": counts["answer_value_hit"] / denom,
        "evidence_value_hit_rate": counts["evidence_value_hit"] / denom,
        "gold_answer_success_rate": counts["gold_answer_success"] / denom,
        "unexpected_error_count": counts["unexpected_errors"],
        "counts": counts,
    }


def evaluate_gold_answers(
    questions: List[Dict[str, Any]],
    index_dir: Path,
    retrieval_backend: str,
    evidence_top_k: int,
    extractive_selector: str = "auto",
) -> Dict[str, Any]:
    counts = empty_counts()
    profile_counts: Dict[str, Dict[str, int]] = {}
    details = []

    for question in questions:
        profile = str(question.get("benchmark_profile", "unspecified") or "unspecified")
        profile_count = profile_counts.setdefault(profile, empty_counts())
        error_code = None
        result: Dict[str, Any] = {}
        try:
            result = run_skill(
                mode="answer",
                query=question["question"],
                index_dir=index_dir,
                retrieval_backend=retrieval_backend,
                evidence_top_k=evidence_top_k,
                answer_engine="extractive",
                extractive_selector=extractive_selector,
            )
        except SkillExecutionError as exc:
            error_code = exc.code

        answer = str(result.get("answer", "") or "")
        combined = evidence_text(result)
        expected_groups = question.get("expected_answer_groups", [])
        answer_hit = group_hit(answer, expected_groups) if expected_groups else False
        evidence_hit = group_hit(combined, expected_groups) if expected_groups else False
        citations = result.get("citations", []) or []
        citation_present = bool(citations)
        success = bool(evidence_hit and citation_present)

        values = {
            "skill_ok": int(bool(result.get("ok"))),
            "citation_present": int(citation_present),
            "answer_value_hit": int(answer_hit),
            "evidence_value_hit": int(evidence_hit),
            "gold_answer_success": int(success),
            "unexpected_errors": int(error_code is not None),
        }
        for target_counts in (counts, profile_count):
            target_counts["questions"] += 1
            for key, value in values.items():
                target_counts[key] += value

        details.append(
            {
                "qid": question.get("qid"),
                "question": question.get("question"),
                "benchmark_profile": profile,
                "answer_type": question.get("answer_type"),
                "source_basis": question.get("source_basis"),
                "source_urls": question.get("source_urls", []),
                "ok": bool(result.get("ok")),
                "error_code": error_code,
                "answer_value_hit": answer_hit,
                "evidence_value_hit": evidence_hit,
                "gold_answer_success": success,
                "citation_present": citation_present,
                "retrieved_doc_ids_at_5": [item.get("doc_id") for item in (result.get("evidence", []) or [])[:5]],
                "retrieval_backend": result.get("rag_pipeline", {}).get("retrieval_backend", retrieval_backend),
                "reranker_backends": result.get("rag_pipeline", {}).get("reranker_backends", []),
                "extractive_selector": result.get("extractive_selector", extractive_selector),
                "extractive_selector_backend": result.get("extractive_selector_backend", "not_run"),
            }
        )

    summary = summarize_counts(counts)
    return {
        **summary,
        "retrieval_backend": retrieval_backend,
        "evidence_top_k": evidence_top_k,
        "extractive_selector": extractive_selector,
        "by_benchmark_profile": {
            profile: summarize_counts(profile_count)
            for profile, profile_count in sorted(profile_counts.items())
        },
        "details": details,
        "metric_note": (
            "Gold-answer seed evaluation checks short answer targets from public answer keys. "
            "It does not replace expert grading and may penalize extractive-only answers on calculation questions."
        ),
    }


def write_markdown(summary: Dict[str, Any], output_path: Path) -> None:
    lines = [
        "# Gold-Answer Seed Evaluation Results",
        "",
        f"- Questions: {summary['questions']}",
        f"- Retrieval backend: {summary['retrieval_backend']}",
        f"- Evidence top-k: {summary['evidence_top_k']}",
        f"- Extractive selector: {summary['extractive_selector']}",
        f"- Skill OK rate: {summary['skill_ok_rate']:.3f}",
        f"- Citation present rate: {summary['citation_present_rate']:.3f}",
        f"- Answer value hit rate: {summary['answer_value_hit_rate']:.3f}",
        f"- Evidence value hit rate: {summary['evidence_value_hit_rate']:.3f}",
        f"- Gold-answer success rate: {summary['gold_answer_success_rate']:.3f}",
        f"- Unexpected errors: {summary['unexpected_error_count']}",
        "",
        summary["metric_note"],
        "",
        "## Results By Benchmark Profile",
        "",
        "| Profile | Questions | Answer value hit | Evidence value hit | Gold-answer success |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for profile, metrics in summary.get("by_benchmark_profile", {}).items():
        lines.append(
            "| {profile} | {questions} | {answer:.3f} | {evidence:.3f} | {success:.3f} |".format(
                profile=profile,
                questions=metrics["questions"],
                answer=metrics["answer_value_hit_rate"],
                evidence=metrics["evidence_value_hit_rate"],
                success=metrics["gold_answer_success_rate"],
            )
        )
    lines.extend(
        [
            "",
        "## Misses",
        "",
        ]
    )
    misses = [item for item in summary["details"] if not item["gold_answer_success"]]
    if not misses:
        lines.append("None.")
    for item in misses:
        lines.extend(
            [
                f"### {item['qid']}",
                f"- Answer value hit: {item['answer_value_hit']}",
                f"- Evidence value hit: {item['evidence_value_hit']}",
                f"- Error code: {item['error_code']}",
                f"- Retrieved doc_ids@5: {', '.join(str(x) for x in item['retrieved_doc_ids_at_5'])}",
                "",
            ]
        )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate external public gold-answer seed questions.")
    parser.add_argument("--questions", type=Path, default=Path("evaluation/radiotherapy_gold_answer_questions.json"))
    parser.add_argument("--index-dir", type=Path, default=Path("index"))
    parser.add_argument("--retrieval-backend", choices=["auto", "hybrid", "sparse", "routed"], default="routed")
    parser.add_argument("--evidence-top-k", type=int, default=8)
    parser.add_argument("--extractive-selector", choices=["auto", "lexical", "semantic_coverage"], default="auto")
    parser.add_argument("--max-questions", type=int, default=0)
    parser.add_argument("--output-json", type=Path, default=Path("evaluation/gold_answer_eval_results.json"))
    parser.add_argument("--output-md", type=Path, default=Path("evaluation/gold_answer_eval_results.md"))
    args = parser.parse_args()

    summary = evaluate_gold_answers(
        load_questions(args.questions)[: args.max_questions or None],
        args.index_dir,
        args.retrieval_backend,
        args.evidence_top_k,
        extractive_selector=args.extractive_selector,
    )
    write_json(args.output_json, summary)
    write_markdown(summary, args.output_md)
    print(json.dumps({k: v for k, v in summary.items() if k != "details"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
