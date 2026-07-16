#!/usr/bin/env python
"""Evaluate answer-mode behavior against evidence and bundle upper bounds.

This script does not call a hosted LLM. It compares three local skill outputs
on the same public answer-target questions:

- extractive answer mode
- evidence-only retrieval
- bundle prompt construction for downstream answer models

The goal is to quantify whether failures are due to retrieval/evidence absence
or due to the conservative extractive answer not synthesizing an answer target.
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
from src.generation.prompting import build_grounded_prompt
from src.utils import write_json

SPACE_RE = re.compile(r"\s+")
METRIC_KEYS = (
    "answer_ok",
    "evidence_ok",
    "bundle_ok",
    "extractive_answer_value_hit",
    "extractive_evidence_value_hit",
    "evidence_only_value_hit",
    "bundle_prompt_value_hit",
    "citation_present",
    "answer_synthesis_gap",
    "retrieval_gap",
    "unexpected_errors",
)


def normalize(text: str) -> str:
    text = text.lower()
    text = text.replace("\u2013", "-").replace("\u2014", "-").replace("\u00a0", " ")
    return SPACE_RE.sub(" ", text).strip()


def group_hit(text: str, groups: List[List[str]]) -> bool:
    if not groups:
        return False
    haystack = normalize(text)
    for group in groups:
        if not any(normalize(alias) in haystack for alias in group):
            return False
    return True


def empty_counts() -> Dict[str, int]:
    return {"questions": 0, **{key: 0 for key in METRIC_KEYS}}


def summarize_counts(counts: Dict[str, int]) -> Dict[str, Any]:
    denom = max(1, counts["questions"])
    return {
        "questions": counts["questions"],
        "answer_ok_rate": counts["answer_ok"] / denom,
        "evidence_ok_rate": counts["evidence_ok"] / denom,
        "bundle_ok_rate": counts["bundle_ok"] / denom,
        "extractive_answer_value_hit_rate": counts["extractive_answer_value_hit"] / denom,
        "extractive_evidence_value_hit_rate": counts["extractive_evidence_value_hit"] / denom,
        "evidence_only_value_hit_rate": counts["evidence_only_value_hit"] / denom,
        "bundle_prompt_value_hit_rate": counts["bundle_prompt_value_hit"] / denom,
        "citation_present_rate": counts["citation_present"] / denom,
        "answer_synthesis_gap_rate": counts["answer_synthesis_gap"] / denom,
        "retrieval_gap_rate": counts["retrieval_gap"] / denom,
        "unexpected_error_count": counts["unexpected_errors"],
        "counts": counts,
    }


def result_text(
    result: Dict[str, Any],
    include_answer: bool = True,
    include_prompt: bool = True,
    prompt_text: str = "",
) -> str:
    parts: List[str] = []
    if include_answer:
        parts.append(str(result.get("answer", "") or ""))
    if include_prompt:
        parts.append(str(result.get("prompt_for_medgemma", "") or ""))
        parts.append(prompt_text)
    for item in result.get("evidence", []) or []:
        parts.extend(
            [
                str(item.get("document", "") or ""),
                str(item.get("section", "") or ""),
                str(item.get("citation", "") or ""),
                str(item.get("text", "") or ""),
            ]
        )
        for asset in item.get("nearby_assets", []) or []:
            parts.append(str(asset.get("caption", "") or ""))
            parts.append(str(asset.get("text_preview", "") or ""))
    return "\n".join(parts)


def safe_answer_run(
    question: str,
    index_dir: Path,
    retrieval_backend: str,
    evidence_top_k: int,
    extractive_selector: str,
) -> tuple[Dict[str, Any], str | None]:
    try:
        return (
            run_skill(
                mode="answer",
                query=question,
                index_dir=index_dir,
                retrieval_backend=retrieval_backend,
                evidence_top_k=evidence_top_k,
                answer_engine="extractive",
                extractive_selector=extractive_selector,
            ),
            None,
        )
    except SkillExecutionError as exc:
        return {}, exc.code


def evaluate_answer_generation(
    questions: List[Dict[str, Any]],
    index_dir: Path,
    retrieval_backend: str,
    evidence_top_k: int,
    extractive_selector: str = "auto",
    max_questions: int | None = None,
) -> Dict[str, Any]:
    selected = questions[:max_questions] if max_questions else questions
    counts = empty_counts()
    profile_counts: Dict[str, Dict[str, int]] = {}
    details: List[Dict[str, Any]] = []

    for question in selected:
        profile = str(question.get("benchmark_profile", "unspecified") or "unspecified")
        profile_count = profile_counts.setdefault(profile, empty_counts())
        expected_groups = question.get("expected_answer_groups", []) or []
        answer_result, answer_error = safe_answer_run(
            question["question"], index_dir, retrieval_backend, evidence_top_k, extractive_selector
        )
        evidence_items = answer_result.get("evidence", []) or []
        prompt_text = ""
        if evidence_items:
            prompt_text = build_grounded_prompt(
                question["question"],
                [{"chunk": item} for item in _flattened_to_chunk_like(evidence_items)],
            )

        answer_ok = bool(answer_result.get("ok"))
        evidence_ok = answer_ok
        bundle_ok = answer_ok and bool(prompt_text)
        answer_hit = group_hit(str(answer_result.get("answer", "") or ""), expected_groups)
        answer_evidence_hit = group_hit(result_text(answer_result), expected_groups)
        evidence_hit = group_hit(result_text(answer_result, include_answer=False, include_prompt=False), expected_groups)
        bundle_hit = group_hit(result_text(answer_result, include_answer=False, include_prompt=True, prompt_text=prompt_text), expected_groups)
        citation_present = bool(answer_result.get("citations"))

        answer_synthesis_gap = bool((answer_evidence_hit or evidence_hit or bundle_hit) and not answer_hit)
        retrieval_gap = bool(not answer_evidence_hit and not evidence_hit and not bundle_hit)
        values = {
            "answer_ok": int(answer_ok),
            "evidence_ok": int(evidence_ok),
            "bundle_ok": int(bundle_ok),
            "extractive_answer_value_hit": int(answer_hit),
            "extractive_evidence_value_hit": int(answer_evidence_hit),
            "evidence_only_value_hit": int(evidence_hit),
            "bundle_prompt_value_hit": int(bundle_hit),
            "citation_present": int(citation_present),
            "answer_synthesis_gap": int(answer_synthesis_gap),
            "retrieval_gap": int(retrieval_gap),
            "unexpected_errors": int(bool(answer_error) and not question.get("expected_abstain")),
        }
        for target_counts in (counts, profile_count):
            target_counts["questions"] += 1
            for key, value in values.items():
                target_counts[key] += value

        details.append(
            {
                "qid": question.get("qid"),
                "benchmark_profile": profile,
                "answer_ok": answer_ok,
                "evidence_ok": evidence_ok,
                "bundle_ok": bundle_ok,
                "answer_error": answer_error,
                "evidence_error": answer_error,
                "bundle_error": answer_error,
                "extractive_answer_value_hit": answer_hit,
                "extractive_evidence_value_hit": answer_evidence_hit,
                "evidence_only_value_hit": evidence_hit,
                "bundle_prompt_value_hit": bundle_hit,
                "citation_present": citation_present,
                "answer_synthesis_gap": answer_synthesis_gap,
                "retrieval_gap": retrieval_gap,
                "retrieved_doc_ids_at_5": [
                    item.get("doc_id") for item in (answer_result.get("evidence", []) or [])[:5]
                ],
            }
        )

    summary = summarize_counts(counts)
    return {
        **summary,
        "retrieval_backend": retrieval_backend,
        "evidence_top_k": evidence_top_k,
        "answer_engine": "extractive",
        "extractive_selector": extractive_selector,
        "by_benchmark_profile": {
            profile: summarize_counts(profile_count)
            for profile, profile_count in sorted(profile_counts.items())
        },
        "details": details,
        "metric_note": (
            "This local evaluation separates retrieval/evidence availability from extractive answer synthesis. "
            "It is not expert answer grading and does not use hosted LLMs."
        ),
    }


def _flattened_to_chunk_like(evidence_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert flattened script output evidence back to prompt builder shape."""
    chunks: List[Dict[str, Any]] = []
    for item in evidence_items:
        chunks.append(
            {
                "chunk_id": item.get("chunk_id"),
                "doc_id": item.get("doc_id"),
                "title": item.get("document"),
                "section": item.get("section"),
                "subsection": item.get("subsection"),
                "page_start": item.get("page_start"),
                "page_end": item.get("page_end"),
                "text": item.get("text", ""),
            }
        )
    return chunks


def write_markdown(summary: Dict[str, Any], output_path: Path) -> None:
    lines = [
        "# Answer Generation Mode Evaluation",
        "",
        f"- Questions: {summary['questions']}",
        f"- Retrieval backend: {summary['retrieval_backend']}",
        f"- Evidence top-k: {summary['evidence_top_k']}",
        f"- Answer engine: {summary['answer_engine']}",
        f"- Extractive selector: {summary['extractive_selector']}",
        f"- Extractive answer value hit rate: {summary['extractive_answer_value_hit_rate']:.3f}",
        f"- Extractive evidence value hit rate: {summary['extractive_evidence_value_hit_rate']:.3f}",
        f"- Evidence-only value hit rate: {summary['evidence_only_value_hit_rate']:.3f}",
        f"- Bundle prompt value hit rate: {summary['bundle_prompt_value_hit_rate']:.3f}",
        f"- Citation present rate: {summary['citation_present_rate']:.3f}",
        f"- Answer synthesis gap rate: {summary['answer_synthesis_gap_rate']:.3f}",
        f"- Retrieval gap rate: {summary['retrieval_gap_rate']:.3f}",
        f"- Unexpected errors: {summary['unexpected_error_count']}",
        "",
        summary["metric_note"],
        "",
        "## Results By Benchmark Profile",
        "",
        "| Profile | Questions | Answer value hit | Evidence-only value hit | Synthesis gap | Retrieval gap |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for profile, metrics in summary.get("by_benchmark_profile", {}).items():
        lines.append(
            "| {profile} | {questions} | {answer:.3f} | {evidence:.3f} | {synthesis:.3f} | {retrieval:.3f} |".format(
                profile=profile,
                questions=metrics["questions"],
                answer=metrics["extractive_answer_value_hit_rate"],
                evidence=metrics["evidence_only_value_hit_rate"],
                synthesis=metrics["answer_synthesis_gap_rate"],
                retrieval=metrics["retrieval_gap_rate"],
            )
        )
    lines.extend(
        [
            "",
        "## Gap Cases",
        "",
        ]
    )
    gap_cases = [item for item in summary["details"] if item["answer_synthesis_gap"] or item["retrieval_gap"]]
    if not gap_cases:
        lines.append("None.")
    for item in gap_cases[:60]:
        label = "retrieval_gap" if item["retrieval_gap"] else "answer_synthesis_gap"
        lines.extend(
            [
                f"### {item['qid']} ({label})",
                f"- Retrieved doc_ids@5: {', '.join(str(x) for x in item['retrieved_doc_ids_at_5'])}",
                f"- Hit flags: answer={item['extractive_answer_value_hit']}, answer_evidence={item['extractive_evidence_value_hit']}, evidence={item['evidence_only_value_hit']}, bundle={item['bundle_prompt_value_hit']}",
                "",
            ]
        )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate answer generation modes without hosted LLM calls.")
    parser.add_argument("--questions", type=Path, default=Path("evaluation/radiotherapy_gold_answer_questions.json"))
    parser.add_argument("--index-dir", type=Path, default=Path("index"))
    parser.add_argument("--retrieval-backend", choices=["auto", "hybrid", "sparse", "routed"], default="auto")
    parser.add_argument("--evidence-top-k", type=int, default=8)
    parser.add_argument("--extractive-selector", choices=["auto", "lexical", "semantic_coverage"], default="auto")
    parser.add_argument("--max-questions", type=int, default=0)
    parser.add_argument("--output-json", type=Path, default=Path("evaluation/answer_generation_eval_results.json"))
    parser.add_argument("--output-md", type=Path, default=Path("evaluation/answer_generation_eval_results.md"))
    args = parser.parse_args()

    summary = evaluate_answer_generation(
        load_questions(args.questions),
        args.index_dir,
        args.retrieval_backend,
        args.evidence_top_k,
        extractive_selector=args.extractive_selector,
        max_questions=args.max_questions or None,
    )
    write_json(args.output_json, summary)
    write_markdown(summary, args.output_md)
    print(json.dumps({k: v for k, v in summary.items() if k != "details"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
