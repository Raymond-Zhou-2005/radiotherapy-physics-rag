#!/usr/bin/env python
"""Compare legacy and semantic sentence selection for extractive answers.

The compared methods see the same retrieved evidence. They neither access the
benchmark answer keys at runtime nor generate new claims: both return report
sentences verbatim. The comparison measures whether sentence selection exposes
answer-bearing evidence more reliably on the frozen public answer-target set.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.evaluate import load_questions
from scripts.evaluate_answer_generation import _flattened_to_chunk_like, group_hit
from scripts.evaluate_statistical_uncertainty import (
    bootstrap_paired_difference_interval,
    exact_mcnemar_p_value,
    wilson_interval,
)
from scripts.run_skill import SkillExecutionError, build_extractive_answer, run_skill
from src.utils import write_json


def profile_summary(details: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for detail in details:
        grouped[str(detail.get("benchmark_profile", "unspecified"))].append(detail)
    return {
        profile: {
            "questions": len(items),
            "answer_value_hit_rate": sum(int(item["answer_value_hit"]) for item in items) / max(1, len(items)),
            "citation_present_rate": sum(int(item["citation_present"]) for item in items) / max(1, len(items)),
        }
        for profile, items in sorted(grouped.items())
    }


def paired_comparison(baseline: Dict[str, Any], challenger: Dict[str, Any]) -> Dict[str, Any]:
    baseline_by_qid = {item["qid"]: item for item in baseline["details"]}
    challenger_by_qid = {item["qid"]: item for item in challenger["details"]}
    qids = sorted(set(baseline_by_qid) & set(challenger_by_qid))
    baseline_values = [int(baseline_by_qid[qid]["answer_value_hit"]) for qid in qids]
    challenger_values = [int(challenger_by_qid[qid]["answer_value_hit"]) for qid in qids]
    baseline_hits = sum(baseline_values)
    challenger_hits = sum(challenger_values)
    semantic_better = sum(before == 0 and after == 1 for before, after in zip(baseline_values, challenger_values))
    semantic_worse = sum(before == 1 and after == 0 for before, after in zip(baseline_values, challenger_values))
    return {
        "baseline_selector": baseline["selector"],
        "challenger_selector": challenger["selector"],
        "questions": len(qids),
        "baseline_hit_rate": baseline_hits / max(1, len(qids)),
        "challenger_hit_rate": challenger_hits / max(1, len(qids)),
        "absolute_difference": (challenger_hits - baseline_hits) / max(1, len(qids)),
        "baseline_wilson_95_ci": wilson_interval(baseline_hits, len(qids)),
        "challenger_wilson_95_ci": wilson_interval(challenger_hits, len(qids)),
        "paired_bootstrap_95_ci": bootstrap_paired_difference_interval(
            challenger_values,
            baseline_values,
            repetitions=10000,
            seed=20260714,
        ),
        "exact_mcnemar_two_sided_p": exact_mcnemar_p_value(challenger_values, baseline_values),
        "challenger_better_cases": semantic_better,
        "challenger_worse_cases": semantic_worse,
    }


def evaluate_selectors(
    selectors: List[str],
    questions: List[Dict[str, Any]],
    index_dir: Path,
    retrieval_backend: str,
    evidence_top_k: int,
) -> List[Dict[str, Any]]:
    state = {
        selector: {
            "counts": {"questions": 0, "answer_value_hit": 0, "citation_present": 0, "unexpected_errors": 0},
            "resolved_backends": {},
            "details": [],
        }
        for selector in selectors
    }

    for question in questions:
        error_code = None
        try:
            baseline_result = run_skill(
                mode="answer",
                query=question["question"],
                index_dir=index_dir,
                retrieval_backend=retrieval_backend,
                evidence_top_k=evidence_top_k,
                answer_engine="extractive",
                extractive_selector="lexical",
            )
        except SkillExecutionError as exc:
            baseline_result = {}
            error_code = exc.code
        raw_evidence = [
            {"chunk": chunk}
            for chunk in _flattened_to_chunk_like(baseline_result.get("evidence", []) or [])
        ]

        for selector in selectors:
            result = baseline_result
            if not error_code and selector != "lexical":
                answer = build_extractive_answer(
                    question["question"],
                    raw_evidence,
                    project_root=index_dir.parent,
                    selector=selector,
                )
                result = dict(baseline_result)
                result.update(answer)

            answer_hit = group_hit(str(result.get("answer", "") or ""), question.get("expected_answer_groups", []) or [])
            citation_present = bool(result.get("citations"))
            backend = str(result.get("extractive_selector_backend", "not_run") or "not_run")
            expected_abstain = bool(question.get("expected_abstain", False))
            selector_state = state[selector]
            counts = selector_state["counts"]
            resolved_backends = selector_state["resolved_backends"]
            resolved_backends[backend] = resolved_backends.get(backend, 0) + 1
            counts["questions"] += 1
            counts["answer_value_hit"] += int(answer_hit)
            counts["citation_present"] += int(citation_present)
            counts["unexpected_errors"] += int(bool(error_code) and not expected_abstain)
            selector_state["details"].append(
                {
                    "qid": question.get("qid"),
                    "benchmark_profile": question.get("benchmark_profile", "unspecified"),
                    "answer_value_hit": answer_hit,
                    "citation_present": citation_present,
                    "error_code": error_code,
                    "extractive_selector_backend": backend,
                    "used_evidence_ids": result.get("used_evidence_ids", []),
                }
            )

    summaries = []
    for selector in selectors:
        selector_state = state[selector]
        counts = selector_state["counts"]
        denom = max(1, counts["questions"])
        summaries.append(
            {
                "selector": selector,
                "questions": counts["questions"],
                "answer_value_hit_rate": counts["answer_value_hit"] / denom,
                "citation_present_rate": counts["citation_present"] / denom,
                "unexpected_error_count": counts["unexpected_errors"],
                "resolved_selector_backends": selector_state["resolved_backends"],
                "details": selector_state["details"],
                "by_benchmark_profile": profile_summary(selector_state["details"]),
            }
        )
    comparisons = []
    if "lexical" in selectors:
        baseline = next(item for item in summaries if item["selector"] == "lexical")
        for challenger in summaries:
            if challenger["selector"] != "lexical":
                comparisons.append(paired_comparison(baseline, challenger))
    return summaries, comparisons


def write_markdown(payload: Dict[str, Any], output_path: Path) -> None:
    rows = payload["selectors"]
    lines = [
        "# Extractive Sentence Selector Ablation",
        "",
        f"- Questions: {payload['questions']}",
        f"- Retrieval backend: {payload['retrieval_backend']}",
        f"- Evidence top-k: {payload['evidence_top_k']}",
        "- Both selectors receive the same retrieved evidence and return only copied evidence sentences.",
        "- This is an automatic public answer-target evaluation, not expert answer grading or clinical validation.",
        "",
        "| Selector | Answer value hit | Citation present | Unexpected errors | Resolved backend |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        backend = ", ".join(f"{key}: {value}" for key, value in sorted(row["resolved_selector_backends"].items()))
        lines.append(
            "| {selector} | {answer:.3f} | {citation:.3f} | {errors} | {backend} |".format(
                selector=row["selector"],
                answer=row["answer_value_hit_rate"],
                citation=row["citation_present_rate"],
                errors=row["unexpected_error_count"],
                backend=backend,
            )
        )
    if len(rows) >= 2:
        baseline = rows[0]["answer_value_hit_rate"]
        for row in rows[1:]:
            delta = row["answer_value_hit_rate"] - baseline
            lines.append("")
            lines.append(f"- Absolute answer-value-hit difference versus `{rows[0]['selector']}` for `{row['selector']}`: {delta:+.3f}.")
    for comparison in payload.get("paired_comparisons", []):
        lines.extend(
            [
                "",
                "## Paired Comparison",
                "",
                f"- Baseline: `{comparison['baseline_selector']}`; challenger: `{comparison['challenger_selector']}`.",
                f"- Absolute answer-value-hit difference: {comparison['absolute_difference']:+.3f}.",
                f"- Paired bootstrap 95% CI: {comparison['paired_bootstrap_95_ci']}.",
                f"- Exact two-sided McNemar p: {comparison['exact_mcnemar_two_sided_p']:.6f}.",
                f"- Challenger better/worse discordant cases: {comparison['challenger_better_cases']}/{comparison['challenger_worse_cases']}.",
                "- These intervals quantify the fixed automatic answer-target set, not expert correctness or clinical validity.",
            ]
        )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate extractive sentence selectors on frozen answer targets.")
    parser.add_argument("--questions", type=Path, default=Path("evaluation/radiotherapy_gold_answer_questions.json"))
    parser.add_argument("--index-dir", type=Path, default=Path("index"))
    parser.add_argument("--retrieval-backend", choices=["auto", "hybrid", "sparse", "routed"], default="auto")
    parser.add_argument("--evidence-top-k", type=int, default=8)
    parser.add_argument("--selectors", nargs="+", choices=["lexical", "semantic_coverage"], default=["lexical", "semantic_coverage"])
    parser.add_argument("--max-questions", type=int, default=0)
    parser.add_argument(
        "--summarize-existing",
        type=Path,
        default=None,
        help="Recompute profile and paired statistics from a frozen per-question selector result without rerunning retrieval or models.",
    )
    parser.add_argument("--output-json", type=Path, default=Path("evaluation/extractive_selector_ablation.json"))
    parser.add_argument("--output-md", type=Path, default=Path("evaluation/extractive_selector_ablation.md"))
    args = parser.parse_args()

    if args.summarize_existing:
        payload = json.loads(args.summarize_existing.read_text(encoding="utf-8"))
        selectors = payload.get("selectors") or []
        if not selectors or any("details" not in item for item in selectors):
            raise ValueError("Existing selector result must contain per-question details for every selector.")
        for selector in selectors:
            selector["by_benchmark_profile"] = profile_summary(selector["details"])
        lexical = next((item for item in selectors if item.get("selector") == "lexical"), None)
        paired_comparisons = [paired_comparison(lexical, item) for item in selectors if lexical and item is not lexical]
        payload["paired_comparisons"] = paired_comparisons
        payload["metric_note"] = "Frozen automatic answer-target comparison; neither selector uses answer keys at runtime."
        args.output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        write_markdown(payload, args.output_md)
        print(json.dumps({"resummarized_existing": str(args.summarize_existing), "selectors": len(selectors)}, ensure_ascii=False, indent=2))
        return

    questions = load_questions(args.questions)
    if args.max_questions:
        questions = questions[: args.max_questions]
    selectors, paired_comparisons = evaluate_selectors(
        args.selectors,
        questions,
        args.index_dir,
        args.retrieval_backend,
        args.evidence_top_k,
    )
    payload = {
        "questions": len(questions),
        "retrieval_backend": args.retrieval_backend,
        "evidence_top_k": args.evidence_top_k,
        "selectors": selectors,
        "paired_comparisons": paired_comparisons,
        "metric_note": "Frozen automatic answer-target comparison; neither selector uses answer keys at runtime.",
    }
    write_json(args.output_json, payload)
    write_markdown(payload, args.output_md)
    print(json.dumps({key: value for key, value in payload.items() if key != "selectors"}, ensure_ascii=False, indent=2))
    for result in selectors:
        print(json.dumps({key: value for key, value in result.items() if key != "details"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
