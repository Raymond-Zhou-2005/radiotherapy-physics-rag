#!/usr/bin/env python
"""Quantify uncertainty for the fixed evaluation outputs used in the paper.

The project deliberately distinguishes fixed public benchmark performance from
clinical validation. This script adds reproducible uncertainty intervals without
rerunning retrieval. Binary metrics receive Wilson score intervals; continuous
grounded-token overlap receives a deterministic nonparametric bootstrap interval.
The sparse-versus-hybrid document-recall comparison is evaluated on paired
question outcomes with a bootstrap confidence interval and exact McNemar test.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path
from typing import Any, Iterable

Z_95 = 1.959963984540054


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def percentile(values: list[float], probability: float) -> float:
    if not values:
        raise ValueError("Cannot calculate a percentile of an empty sequence.")
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def wilson_interval(successes: int, total: int, z: float = Z_95) -> list[float]:
    """Return a two-sided Wilson score confidence interval for a binomial rate."""
    if total <= 0:
        return [0.0, 0.0]
    proportion = successes / total
    denominator = 1 + z * z / total
    centre = (proportion + z * z / (2 * total)) / denominator
    margin = z * math.sqrt((proportion * (1 - proportion) + z * z / (4 * total)) / total) / denominator
    return [max(0.0, centre - margin), min(1.0, centre + margin)]


def bootstrap_mean_interval(values: list[float], repetitions: int, seed: int) -> list[float]:
    """Return a deterministic percentile bootstrap interval for a mean."""
    if not values:
        return [0.0, 0.0]
    rng = random.Random(seed)
    sample_size = len(values)
    means = [
        sum(values[rng.randrange(sample_size)] for _ in range(sample_size)) / sample_size
        for _ in range(repetitions)
    ]
    return [percentile(means, 0.025), percentile(means, 0.975)]


def bootstrap_paired_difference_interval(
    left: list[int], right: list[int], repetitions: int, seed: int
) -> list[float]:
    """Return a percentile bootstrap interval for mean(left - right)."""
    if not left or len(left) != len(right):
        raise ValueError("Paired samples must be non-empty and have equal length.")
    rng = random.Random(seed)
    sample_size = len(left)
    differences = [
        sum(left[index] - right[index] for index in (rng.randrange(sample_size) for _ in range(sample_size)))
        / sample_size
        for _ in range(repetitions)
    ]
    return [percentile(differences, 0.025), percentile(differences, 0.975)]


def exact_mcnemar_p_value(left: list[int], right: list[int]) -> float:
    """Two-sided exact McNemar p-value for paired binary outcomes."""
    discordant_left = sum(1 for a, b in zip(left, right) if a == 1 and b == 0)
    discordant_right = sum(1 for a, b in zip(left, right) if a == 0 and b == 1)
    total = discordant_left + discordant_right
    if total == 0:
        return 1.0
    tail = sum(math.comb(total, value) for value in range(min(discordant_left, discordant_right) + 1))
    return min(1.0, 2 * tail / (2**total))


def binary_summary(values: Iterable[bool]) -> dict[str, Any]:
    outcomes = [int(bool(value)) for value in values]
    successes = sum(outcomes)
    total = len(outcomes)
    return {
        "successes": successes,
        "total": total,
        "rate": successes / total if total else 0.0,
        "wilson_95_ci": wilson_interval(successes, total),
    }


def strategy_document_outcomes(summary: dict[str, Any]) -> dict[str, int]:
    outcomes: dict[str, int] = {}
    for item in summary.get("details", []):
        if item.get("expected_abstain"):
            continue
        expected = item.get("expected_doc_id")
        outcomes[str(item["qid"])] = int(bool(expected and expected in (item.get("retrieved_doc_ids") or [])[:5]))
    return outcomes


def strategy_ood_outcomes(summary: dict[str, Any]) -> dict[str, int]:
    outcomes: dict[str, int] = {}
    for item in summary.get("details", []):
        if not item.get("expected_abstain"):
            continue
        outcomes[str(item["qid"])] = int(bool(item.get("predicted_abstain_proxy")))
    return outcomes


def profile_details(details: list[dict[str, Any]], profile: str) -> list[dict[str, Any]]:
    return [item for item in details if item.get("benchmark_profile") == profile]


def summarize_binary_details(details: list[dict[str, Any]], key: str) -> dict[str, Any]:
    return binary_summary(bool(item.get(key)) for item in details)


def run_uncertainty_analysis(eval_dir: Path, repetitions: int, seed: int) -> dict[str, Any]:
    strategy = read_json(eval_dir / "strategy_eval_results.json")
    gold = read_json(eval_dir / "gold_answer_eval_results.json")
    generation = read_json(eval_dir / "answer_generation_eval_results.json")
    table = read_json(eval_dir / "table_cell_qa_eval_results.json")
    agent = read_json(eval_dir / "agent_task_eval_results.json")
    mcp = read_json(eval_dir / "mcp_contract_eval_results.json")
    quality = read_json(eval_dir / "answer_quality_eval_results.json")

    strategy_summaries: dict[str, Any] = {}
    document_outcomes: dict[str, dict[str, int]] = {}
    for name, summary in (strategy.get("strategies") or {}).items():
        docs = strategy_document_outcomes(summary)
        ood = strategy_ood_outcomes(summary)
        document_outcomes[name] = docs
        strategy_summaries[name] = {
            "document_recall_at_5": binary_summary(docs.values()),
            "ood_refusal": binary_summary(ood.values()),
        }

    paired: dict[str, Any] = {}
    if {"sparse", "hybrid"}.issubset(document_outcomes):
        qids = sorted(set(document_outcomes["sparse"]).intersection(document_outcomes["hybrid"]))
        hybrid = [document_outcomes["hybrid"][qid] for qid in qids]
        sparse = [document_outcomes["sparse"][qid] for qid in qids]
        paired = {
            "comparison": "hybrid_minus_sparse_document_recall_at_5",
            "paired_questions": len(qids),
            "hybrid_minus_sparse": sum(hybrid) / len(hybrid) - sum(sparse) / len(sparse),
            "bootstrap_95_ci": bootstrap_paired_difference_interval(hybrid, sparse, repetitions, seed),
            "discordant_hybrid_only": sum(1 for left, right in zip(hybrid, sparse) if left == 1 and right == 0),
            "discordant_sparse_only": sum(1 for left, right in zip(hybrid, sparse) if left == 0 and right == 1),
            "exact_mcnemar_two_sided_p": exact_mcnemar_p_value(hybrid, sparse),
        }

    answer_profiles: dict[str, Any] = {}
    for profile in ("external_gold_answer", "open_report_gold_answer"):
        gold_profile = profile_details(gold.get("details", []), profile)
        generation_profile = profile_details(generation.get("details", []), profile)
        answer_profiles[profile] = {
            "gold_evidence_value_hit": summarize_binary_details(gold_profile, "evidence_value_hit"),
            "gold_extractive_answer_value_hit": summarize_binary_details(gold_profile, "answer_value_hit"),
            "generation_evidence_only_value_hit": summarize_binary_details(generation_profile, "evidence_only_value_hit"),
            "generation_extractive_answer_value_hit": summarize_binary_details(
                generation_profile, "extractive_answer_value_hit"
            ),
        }

    quality_details = [item for item in quality.get("details", []) if not item.get("expected_abstain")]
    grounded = [float(item.get("grounded_token_overlap", 0.0)) for item in quality_details]

    return {
        "analysis_version": "1.0",
        "source_evaluation_files": [
            "strategy_eval_results.json",
            "gold_answer_eval_results.json",
            "answer_generation_eval_results.json",
            "table_cell_qa_eval_results.json",
            "agent_task_eval_results.json",
            "mcp_contract_eval_results.json",
            "answer_quality_eval_results.json",
        ],
        "method": {
            "confidence_level": 0.95,
            "binary_interval": "Wilson score interval",
            "continuous_interval": "nonparametric percentile bootstrap for the mean",
            "paired_comparison": "paired percentile bootstrap and two-sided exact McNemar test",
            "bootstrap_repetitions": repetitions,
            "random_seed": seed,
            "scope_note": (
                "Intervals describe uncertainty within the fixed automatic evaluation sets. "
                "They do not establish clinical validity, expert agreement, or population generalization."
            ),
        },
        "retrieval": {
            "strategies": strategy_summaries,
            "paired_sparse_vs_hybrid": paired,
        },
        "answer_targets": answer_profiles,
        "capability_contracts": {
            "cell_level_table_qa": summarize_binary_details(table.get("details", []), "cell_qa_success"),
            "direct_skill_task_success": summarize_binary_details(agent.get("details", []), "task_success"),
            "mcp_stdio_task_success": summarize_binary_details(mcp.get("details", []), "task_success"),
        },
        "answer_quality_proxy": {
            "in_scope_grounded_token_overlap": {
                "total": len(grounded),
                "mean": sum(grounded) / len(grounded) if grounded else 0.0,
                "bootstrap_95_ci": bootstrap_mean_interval(grounded, repetitions, seed),
            },
            "ood_refusal": binary_summary(
                item.get("error_code") in {"insufficient_evidence", "out_of_scope"}
                for item in quality.get("details", [])
                if item.get("expected_abstain")
            ),
        },
    }


def interval_text(interval: list[float]) -> str:
    return f"[{interval[0]:.3f}, {interval[1]:.3f}]"


def write_markdown(results: dict[str, Any], output_path: Path) -> None:
    lines = [
        "# Statistical Uncertainty Report",
        "",
        "## Scope",
        "",
        results["method"]["scope_note"],
        "",
        "## Retrieval",
        "",
        "| Strategy | In-scope n | Document Recall@5 | Wilson 95% CI | OOD n | OOD refusal | Wilson 95% CI |",
        "|---|---:|---:|---|---:|---:|---|",
    ]
    for name, item in results["retrieval"]["strategies"].items():
        document = item["document_recall_at_5"]
        ood = item["ood_refusal"]
        lines.append(
            f"| {name} | {document['total']} | {document['rate']:.3f} | {interval_text(document['wilson_95_ci'])} "
            f"| {ood['total']} | {ood['rate']:.3f} | {interval_text(ood['wilson_95_ci'])} |"
        )
    paired = results["retrieval"].get("paired_sparse_vs_hybrid") or {}
    if paired:
        lines.extend(
            [
                "",
                "### Paired Sparse Versus Hybrid Comparison",
                "",
                f"- Paired in-scope questions: {paired['paired_questions']}",
                f"- Hybrid minus sparse Document Recall@5: {paired['hybrid_minus_sparse']:.3f}",
                f"- Bootstrap 95% CI: {interval_text(paired['bootstrap_95_ci'])}",
                f"- Discordant questions: hybrid-only={paired['discordant_hybrid_only']}, sparse-only={paired['discordant_sparse_only']}",
                f"- Exact two-sided McNemar p-value: {paired['exact_mcnemar_two_sided_p']:.4f}",
            ]
        )
    lines.extend(
        [
            "",
            "## Answer Targets",
            "",
            "| Profile | Metric | Successes / n | Rate | Wilson 95% CI |",
            "|---|---|---:|---:|---|",
        ]
    )
    for profile, metrics in results["answer_targets"].items():
        for metric, summary in metrics.items():
            lines.append(
                f"| {profile} | {metric} | {summary['successes']} / {summary['total']} | "
                f"{summary['rate']:.3f} | {interval_text(summary['wilson_95_ci'])} |"
            )
    lines.extend(
        [
            "",
            "## Capability Contracts",
            "",
            "| Metric | Successes / n | Rate | Wilson 95% CI |",
            "|---|---:|---:|---|",
        ]
    )
    for name, summary in results["capability_contracts"].items():
        lines.append(
            f"| {name} | {summary['successes']} / {summary['total']} | {summary['rate']:.3f} | "
            f"{interval_text(summary['wilson_95_ci'])} |"
        )
    quality = results["answer_quality_proxy"]
    lines.extend(
        [
            "",
            "## Automatic Answer-Quality Proxy",
            "",
            f"- In-scope grounded-token overlap mean: {quality['in_scope_grounded_token_overlap']['mean']:.3f}",
            f"- Bootstrap 95% CI: {interval_text(quality['in_scope_grounded_token_overlap']['bootstrap_95_ci'])}",
            f"- OOD refusal: {quality['ood_refusal']['successes']} / {quality['ood_refusal']['total']} "
            f"({quality['ood_refusal']['rate']:.3f}; Wilson 95% CI "
            f"{interval_text(quality['ood_refusal']['wilson_95_ci'])})",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate confidence intervals from frozen RAG evaluation outputs.")
    parser.add_argument("--eval-dir", type=Path, default=Path("evaluation"))
    parser.add_argument("--bootstrap-repetitions", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=20260714)
    parser.add_argument("--output-json", type=Path, default=Path("evaluation/statistical_uncertainty.json"))
    parser.add_argument("--output-md", type=Path, default=Path("evaluation/statistical_uncertainty.md"))
    args = parser.parse_args()

    if args.bootstrap_repetitions < 100:
        raise ValueError("--bootstrap-repetitions must be at least 100.")
    results = run_uncertainty_analysis(args.eval_dir, args.bootstrap_repetitions, args.seed)
    args.output_json.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(results, args.output_md)
    print(json.dumps({"output_json": str(args.output_json), "output_md": str(args.output_md)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
