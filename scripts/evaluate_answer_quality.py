#!/usr/bin/env python
"""Evaluate automatic answer-quality proxy metrics for extractive answers.

These metrics are reproducible proxies: citation validity, evidence grounding,
unsupported-number checks, OOD abstention, and overclaim flags. They are not a
substitute for expert grading of clinical correctness.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.evaluate import load_questions
from scripts.run_skill import SkillExecutionError, run_skill
from src.utils import simple_tokenize, write_json


EVIDENCE_ID_RE = re.compile(r"\[E\d+\]")
NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?(?:-\d+(?:\.\d+)?)?%?\b")
OVERCLAIM_PATTERNS = [
    re.compile(r"\b(this patient should|you should|your doctor should|prescribe|diagnose|cure)\b", re.I),
    re.compile(r"\b(clinical recommendation is|medical advice|treatment decision)\b", re.I),
]


def extract_numbers(text: str) -> Set[str]:
    cleaned = EVIDENCE_ID_RE.sub(" ", text)
    return set(NUMBER_RE.findall(cleaned))


def grounded_token_overlap(answer: str, evidence_items: List[Dict[str, Any]]) -> float:
    evidence_text = " ".join(str(item.get("text", "")) for item in evidence_items)
    evidence_terms = set(simple_tokenize(evidence_text))
    answer_terms = {
        token for token in simple_tokenize(EVIDENCE_ID_RE.sub(" ", answer))
        if len(token) >= 3 and token not in {"based", "only", "retrieved", "evidence"}
    }
    if not answer_terms:
        return 0.0
    return len(answer_terms & evidence_terms) / len(answer_terms)


def has_overclaim(answer: str) -> bool:
    return any(pattern.search(answer) for pattern in OVERCLAIM_PATTERNS)


def evaluate_answer_quality(
    questions: List[Dict[str, Any]],
    index_dir: Path,
    retrieval_backend: str,
    max_questions: int | None = None,
) -> Dict[str, Any]:
    selected = questions[:max_questions] if max_questions else questions
    counts = {
        "questions": len(selected),
        "in_scope": 0,
        "ood": 0,
        "in_scope_ok": 0,
        "answer_present": 0,
        "citation_marker_present": 0,
        "used_evidence_ids_valid": 0,
        "unsupported_number_cases": 0,
        "overclaim_cases": 0,
        "ood_abstention_success": 0,
        "unexpected_errors": 0,
    }
    overlaps: List[float] = []
    details = []

    for question in selected:
        expected_abstain = bool(question.get("expected_abstain"))
        if expected_abstain:
            counts["ood"] += 1
        else:
            counts["in_scope"] += 1

        detail = {
            "qid": question.get("qid"),
            "expected_abstain": expected_abstain,
            "ok": False,
            "error_code": None,
            "answer_present": False,
            "citation_marker_present": False,
            "used_evidence_ids_valid": False,
            "grounded_token_overlap": 0.0,
            "unsupported_numbers": [],
            "overclaim_flag": False,
            "retrieval_backend": retrieval_backend,
        }

        try:
            result = run_skill(
                mode="answer",
                query=question["question"],
                index_dir=index_dir,
                retrieval_backend=retrieval_backend,
                answer_engine="extractive",
            )
            detail["ok"] = bool(result.get("ok"))
            detail["retrieval_backend"] = result.get("rag_pipeline", {}).get("retrieval_backend", retrieval_backend)
            if expected_abstain:
                counts["unexpected_errors"] += 1
                detail["error_code"] = "answered_expected_abstain"
            else:
                counts["in_scope_ok"] += 1

            answer = str(result.get("answer", "") or "")
            evidence = result.get("evidence", [])
            citations = result.get("citations", [])
            citation_ids = {str(item.get("evidence_id")) for item in citations}
            used_ids = {str(item) for item in result.get("used_evidence_ids", [])}
            bracket_ids = {marker.strip("[]") for marker in EVIDENCE_ID_RE.findall(answer)}
            valid_ids = (used_ids | bracket_ids).issubset(citation_ids) and bool(used_ids or bracket_ids)
            answer_numbers = extract_numbers(answer)
            evidence_numbers = extract_numbers(" ".join(str(item.get("text", "")) for item in evidence))
            unsupported = sorted(answer_numbers - evidence_numbers)
            overlap = grounded_token_overlap(answer, evidence)
            overclaim = has_overclaim(answer)

            detail["answer_present"] = bool(answer.strip())
            detail["citation_marker_present"] = bool(bracket_ids)
            detail["used_evidence_ids_valid"] = valid_ids
            detail["grounded_token_overlap"] = round(overlap, 4)
            detail["unsupported_numbers"] = unsupported
            detail["overclaim_flag"] = overclaim
            overlaps.append(overlap)

            counts["answer_present"] += int(detail["answer_present"])
            counts["citation_marker_present"] += int(detail["citation_marker_present"])
            counts["used_evidence_ids_valid"] += int(valid_ids)
            counts["unsupported_number_cases"] += int(bool(unsupported))
            counts["overclaim_cases"] += int(overclaim)
        except SkillExecutionError as exc:
            detail["error_code"] = exc.code
            if expected_abstain and exc.code == "insufficient_evidence":
                counts["ood_abstention_success"] += 1
            elif not expected_abstain:
                counts["unexpected_errors"] += 1
        details.append(detail)

    in_scope = max(1, counts["in_scope"])
    ood = max(1, counts["ood"])
    answered = max(1, counts["in_scope_ok"])
    return {
        "questions": len(selected),
        "retrieval_backend": retrieval_backend,
        "answer_engine": "extractive",
        "in_scope_ok_rate": counts["in_scope_ok"] / in_scope,
        "answer_present_rate": counts["answer_present"] / answered,
        "citation_marker_rate": counts["citation_marker_present"] / answered,
        "used_evidence_id_valid_rate": counts["used_evidence_ids_valid"] / answered,
        "mean_grounded_token_overlap": sum(overlaps) / len(overlaps) if overlaps else 0.0,
        "unsupported_number_case_rate": counts["unsupported_number_cases"] / answered,
        "overclaim_flag_rate": counts["overclaim_cases"] / answered,
        "ood_abstention_success_rate": counts["ood_abstention_success"] / ood,
        "unexpected_error_count": counts["unexpected_errors"],
        "counts": counts,
        "details": details,
        "metric_note": "Automatic proxy metrics only; they do not replace expert answer grading.",
    }


def write_markdown(summary: Dict[str, Any], output_path: Path) -> None:
    lines = [
        "# Answer Quality Evaluation Results",
        "",
        f"- Questions: {summary['questions']}",
        f"- Retrieval backend: {summary['retrieval_backend']}",
        f"- Answer engine: {summary['answer_engine']}",
        f"- In-scope OK rate: {summary['in_scope_ok_rate']:.3f}",
        f"- Answer present rate: {summary['answer_present_rate']:.3f}",
        f"- Citation marker rate: {summary['citation_marker_rate']:.3f}",
        f"- Used evidence ID valid rate: {summary['used_evidence_id_valid_rate']:.3f}",
        f"- Mean grounded token overlap: {summary['mean_grounded_token_overlap']:.3f}",
        f"- Unsupported number case rate: {summary['unsupported_number_case_rate']:.3f}",
        f"- Overclaim flag rate: {summary['overclaim_flag_rate']:.3f}",
        f"- OOD abstention success rate: {summary['ood_abstention_success_rate']:.3f}",
        f"- Unexpected errors: {summary['unexpected_error_count']}",
        "",
        summary["metric_note"],
        "",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate answer-quality proxy metrics.")
    parser.add_argument("--questions", type=Path, default=Path("evaluation/radiotherapy_skill_open_questions.json"))
    parser.add_argument("--index-dir", type=Path, default=Path("index"))
    parser.add_argument("--retrieval-backend", choices=["auto", "hybrid", "sparse", "routed"], default="routed")
    parser.add_argument("--max-questions", type=int, default=0)
    parser.add_argument("--output-json", type=Path, default=Path("evaluation/answer_quality_eval_results.json"))
    parser.add_argument("--output-md", type=Path, default=Path("evaluation/answer_quality_eval_results.md"))
    args = parser.parse_args()

    summary = evaluate_answer_quality(
        load_questions(args.questions),
        args.index_dir,
        args.retrieval_backend,
        max_questions=args.max_questions or None,
    )
    write_json(args.output_json, summary)
    write_markdown(summary, args.output_md)
    print(json.dumps({k: v for k, v in summary.items() if k != "details"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
