#!/usr/bin/env python
"""Evaluate RAG evidence and option selection on a public, answer-keyed MCQ set.

This evaluator has two deliberately separate layers. First, it invokes the
project skill to retrieve report evidence. Second, a deterministic option-
evidence selector ranks answer choices against that returned evidence. The
gold answer is used only after selection for scoring. This is a real multiple
choice accuracy metric for the selector, but it is not a Codex-host evaluation
or expert clinical validation.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_skill import SkillExecutionError, run_skill
from src.config import MODELS
from src.retrieval.reranker import CandidateReranker
from src.utils import write_json

SPACE_RE = re.compile(r"\s+")


def normalize(text: str) -> str:
    return SPACE_RE.sub(" ", text.lower().replace("–", "-").replace("—", "-")).strip()


def option_in_text(option_text: str, text: str) -> bool:
    option = normalize(option_text)
    return bool(option and option in normalize(text))


def evidence_text(result: dict[str, Any]) -> str:
    parts: list[str] = []
    for item in result.get("evidence", []) or []:
        parts.extend([str(item.get("text") or ""), str(item.get("document") or "")])
        for asset in item.get("nearby_assets", []) or []:
            parts.append(str(asset.get("text_preview") or ""))
            parts.append(str(asset.get("caption") or ""))
    return "\n".join(parts)


def select_option(
    question: str,
    options: list[dict[str, str]],
    evidence: list[dict[str, Any]],
    reranker: CandidateReranker,
) -> tuple[str | None, list[dict[str, Any]], str]:
    chunks = [
        {
            "title": item.get("document", ""),
            "section": item.get("section", ""),
            "subsection": item.get("subsection", ""),
            "text": item.get("text", ""),
        }
        for item in evidence
    ]
    pairs = [
        (f"Question: {question}\nCandidate answer: {option['text']}", chunk)
        for option in options
        for chunk in chunks
    ]
    raw_scores = reranker.score_query_chunk_pairs(pairs)
    scored = []
    cursor = 0
    for option in options:
        option_scores = raw_scores[cursor : cursor + len(chunks)]
        cursor += len(chunks)
        scored.append(
            {
                "label": option["label"],
                "text": option["text"],
                "score": max(option_scores) if option_scores else float("-inf"),
            }
        )
    scored.sort(key=lambda item: (-float(item["score"]), str(item["label"])))
    return (str(scored[0]["label"]) if scored else None), scored, reranker.resolved_backend


def evaluate_exam(
    payload: dict[str, Any],
    index_dir: Path,
    retrieval_backend: str,
    evidence_top_k: int,
    skill_mode: str,
    max_questions: int | None = None,
) -> dict[str, Any]:
    questions = list(payload.get("questions") or [])[:max_questions]
    reranker = CandidateReranker(
        MODELS.reranker_model_name,
        max_length=min(512, MODELS.reranker_max_length),
        use_heuristics=False,
        backend=MODELS.reranker_backend,
    )
    details = []
    for item in questions:
        started = time.perf_counter()
        result: dict[str, Any] = {}
        error_code = None
        try:
            result = run_skill(
                mode=skill_mode,
                query=str(item["question"]),
                index_dir=index_dir,
                retrieval_backend=retrieval_backend,
                evidence_top_k=evidence_top_k,
                answer_engine="extractive" if skill_mode == "answer" else "auto",
                extractive_selector="semantic_coverage" if skill_mode == "answer" else "auto",
            )
        except SkillExecutionError as exc:
            error_code = exc.code
        retrieval_seconds = time.perf_counter() - started
        selection_started = time.perf_counter()
        selected_label, option_scores, selector_backend = select_option(
            str(item["question"]),
            list(item.get("options") or []),
            list(result.get("evidence") or []),
            reranker,
        )
        selection_seconds = time.perf_counter() - selection_started
        gold_label = str(item["gold_label"])
        gold_answer = str(item["gold_answer"])
        evidence = list(result.get("evidence") or [])
        evidence_joined = evidence_text(result)
        answer_available = skill_mode == "answer" and "answer" in result
        answer = str(result.get("answer") or "")
        details.append(
            {
                "qid": item["qid"],
                "source_question_number": item["source_question_number"],
                "ok": bool(result.get("ok")),
                "error_code": error_code,
                "selected_label": selected_label,
                "gold_label": gold_label,
                "selected_correct": selected_label == gold_label,
                "evidence_contains_gold_option": option_in_text(gold_answer, evidence_joined),
                "extractive_answer_contains_gold_option": (
                    option_in_text(gold_answer, answer) if answer_available else None
                ),
                "citation_present": bool(result.get("citations")),
                "retrieved_doc_ids_at_5": [entry.get("doc_id") for entry in evidence[:5]],
                "option_scores": option_scores,
                "retrieval_backend": result.get("rag_pipeline", {}).get("retrieval_backend", retrieval_backend),
                "option_selector_backend": selector_backend,
                "retrieval_latency_seconds": round(retrieval_seconds, 6),
                "option_selection_latency_seconds": round(selection_seconds, 6),
                "total_latency_seconds": round(retrieval_seconds + selection_seconds, 6),
            }
        )

    denominator = max(1, len(details))

    def success(key: str) -> float:
        return sum(bool(detail.get(key)) for detail in details) / denominator

    answer_details = [detail for detail in details if detail.get("extractive_answer_contains_gold_option") is not None]
    answer_option_rate = (
        sum(bool(detail["extractive_answer_contains_gold_option"]) for detail in answer_details) / len(answer_details)
        if answer_details
        else None
    )

    def latency(key: str) -> float:
        return sum(float(detail.get(key, 0.0)) for detail in details) / denominator

    return {
        "dataset_name": payload.get("dataset_name"),
        "dataset_license": payload.get("license"),
        "source_repository": payload.get("source_repository"),
        "source_commit": payload.get("source_commit"),
        "source_csv_sha256": payload.get("source_csv_sha256"),
        "questions": len(details),
        "retrieval_backend_requested": retrieval_backend,
        "evidence_top_k": evidence_top_k,
        "skill_mode": skill_mode,
        "option_selector": "cross_encoder_option_evidence",
        "option_selector_backend": reranker.resolved_backend,
        "skill_ok_rate": success("ok"),
        "citation_present_rate": success("citation_present"),
        "evidence_contains_gold_option_rate": success("evidence_contains_gold_option"),
        "extractive_answer_contains_gold_option_rate": answer_option_rate,
        "mcq_option_accuracy": success("selected_correct"),
        "mean_retrieval_latency_seconds": latency("retrieval_latency_seconds"),
        "mean_option_selection_latency_seconds": latency("option_selection_latency_seconds"),
        "mean_total_latency_seconds": latency("total_latency_seconds"),
        "details": details,
        "metric_note": (
            "The option selector sees only question, options, and skill-returned evidence. Gold labels are read only "
            "after selection to compute MCQ accuracy. This is a public answer-keyed external benchmark, not a hidden "
            "test, a Codex-host evaluation, expert grading, or clinical validation."
        ),
    }


def export_host_tasks(payload: dict[str, Any], output: Path) -> None:
    """Export answer-key-free tasks for a real Codex or MCP host evaluation."""
    lines = []
    for item in payload.get("questions") or []:
        lines.append(
            json.dumps(
                {
                    "qid": item["qid"],
                    "question": item["question"],
                    "options": item["options"],
                    "required_host_behavior": (
                        "Use the radiotherapy-physics-rag skill or MCP evidence tool. Return exactly one option label "
                        "and a concise evidence-grounded justification with citations. Do not use web search."
                    ),
                },
                ensure_ascii=False,
            )
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_markdown(result: dict[str, Any], output: Path) -> None:
    lines = [
        "# Public Medical Physics MCQ Evaluation",
        "",
        f"- Dataset: {result['dataset_name']}",
        f"- Source commit: {result['source_commit']}",
        f"- Questions: {result['questions']}",
        f"- Retrieval backend: {result['retrieval_backend_requested']}",
        f"- Option selector backend: {result['option_selector_backend']}",
        f"- Skill OK rate: {result['skill_ok_rate']:.3f}",
        f"- Citation-present rate: {result['citation_present_rate']:.3f}",
        f"- Evidence contains gold-option text: {result['evidence_contains_gold_option_rate']:.3f}",
        "- Extractive answer contains gold-option text: "
        + (
            f"{result['extractive_answer_contains_gold_option_rate']:.3f}"
            if result["extractive_answer_contains_gold_option_rate"] is not None
            else "not run (evidence-only skill mode)"
        ),
        f"- MCQ option accuracy: {result['mcq_option_accuracy']:.3f}",
        f"- Mean total latency: {result['mean_total_latency_seconds']:.3f} s/question",
        "",
        result["metric_note"],
        "",
    ]
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the RAG skill on public answer-keyed medical-physics MCQs.")
    parser.add_argument("--questions", type=Path, default=Path("evaluation/external/public_medical_physics_100_mcq.json"))
    parser.add_argument("--index-dir", type=Path, default=Path("index"))
    parser.add_argument("--retrieval-backend", choices=["auto", "hybrid", "sparse", "routed"], default="auto")
    parser.add_argument("--skill-mode", choices=["evidence", "answer"], default="evidence")
    parser.add_argument("--evidence-top-k", type=int, default=8)
    parser.add_argument("--max-questions", type=int, default=0)
    parser.add_argument("--output-json", type=Path, default=Path("evaluation/public_mcq_eval_results.json"))
    parser.add_argument("--output-md", type=Path, default=Path("evaluation/public_mcq_eval_results.md"))
    parser.add_argument("--export-host-tasks", type=Path, default=None)
    args = parser.parse_args()

    payload = json.loads(args.questions.read_text(encoding="utf-8"))
    if args.export_host_tasks:
        export_host_tasks(payload, args.export_host_tasks)
    result = evaluate_exam(
        payload,
        args.index_dir,
        args.retrieval_backend,
        args.evidence_top_k,
        args.skill_mode,
        args.max_questions or None,
    )
    write_json(args.output_json, result)
    write_markdown(result, args.output_md)
    print(json.dumps({key: value for key, value in result.items() if key != "details"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
