#!/usr/bin/env python
"""Build a paper-facing experiment matrix from evaluation result JSON files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def add_metric_row(
    rows: List[Dict[str, Any]],
    experiment: str,
    artifact: str,
    sample_count: int | None,
    primary_metric: str,
    primary_value: float | None,
    secondary_metrics: Dict[str, Any],
    note: str,
) -> None:
    rows.append(
        {
            "experiment": experiment,
            "artifact": artifact,
            "sample_count": sample_count,
            "primary_metric": primary_metric,
            "primary_value": primary_value,
            "secondary_metrics": secondary_metrics,
            "note": note,
        }
    )


def build_matrix(eval_dir: Path) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []

    ablation = read_json(eval_dir / "ablation_eval_results.json")
    for item in ablation.get("variants", []):
        add_metric_row(
            rows,
            experiment=f"Ablation: {item.get('variant')}",
            artifact="evaluation/ablation_eval_results.json",
            sample_count=item.get("questions"),
            primary_metric="Document Recall@5",
            primary_value=item.get("doc_recall@5"),
            secondary_metrics={
                "MRR": item.get("mrr"),
                "Recall@5": item.get("recall@5"),
                "Observed reranker": item.get("observed_reranker_backends"),
                "Uses dense": item.get("uses_dense"),
                "Uses cross encoder": item.get("uses_cross_encoder"),
                "Uses report-aware heuristics": item.get("uses_reportaware"),
                "Uses routing": item.get("uses_routing"),
            },
            note=item.get("description", ""),
        )

    strategy = read_json(eval_dir / "strategy_eval_results.json")
    for name, item in (strategy.get("strategies") or {}).items():
        add_metric_row(
            rows,
            experiment=f"Retrieval strategy: {name}",
            artifact="evaluation/strategy_eval_results.json",
            sample_count=strategy.get("question_count"),
            primary_metric="Document Recall@5",
            primary_value=item.get("doc_recall@5"),
            secondary_metrics={
                "Document Recall@3": item.get("doc_recall@3"),
                "MRR": item.get("mrr"),
                "Abstention": item.get("abstention"),
                "Observed reranker": item.get("observed_reranker_backends"),
            },
            note="Open-source topic retrieval benchmark; not expert answer grading.",
        )

    agent_skill = read_json(eval_dir / "agent_skill_eval_results.json")
    if agent_skill:
        add_metric_row(
            rows,
            experiment="Agent-facing skill contract",
            artifact="evaluation/agent_skill_eval_results.json",
            sample_count=agent_skill.get("questions"),
            primary_metric="Document Hit Rate@5",
            primary_value=agent_skill.get("document_hit_rate@5"),
            secondary_metrics={
                "Citation present": agent_skill.get("citation_present_rate"),
                "OOD abstention": agent_skill.get("ood_abstention_success_rate"),
                "Unexpected errors": agent_skill.get("unexpected_error_count"),
            },
            note="End-to-end skill invocation without an external LLM API.",
        )

    agent_tasks = read_json(eval_dir / "agent_task_eval_results.json")
    if agent_tasks:
        add_metric_row(
            rows,
            experiment="Realistic agent tasks",
            artifact="evaluation/agent_task_eval_results.json",
            sample_count=agent_tasks.get("tasks"),
            primary_metric="Task success rate",
            primary_value=agent_tasks.get("task_success_rate"),
            secondary_metrics={
                "Structured success": agent_tasks.get("structured_success_rate"),
                "Citation success": agent_tasks.get("citation_success_rate"),
                "Bundle prompt success": agent_tasks.get("bundle_prompt_success_rate"),
                "Asset trace success": agent_tasks.get("asset_trace_success_rate"),
                "OOD abstention": agent_tasks.get("ood_abstention_success_rate"),
            },
            note="Checks reusable skill contract behaviour for downstream agents.",
        )

    asset_qa = read_json(eval_dir / "asset_qa_eval_results.json")
    if asset_qa:
        add_metric_row(
            rows,
            experiment="Table/figure asset proximity",
            artifact="evaluation/asset_qa_eval_results.json",
            sample_count=asset_qa.get("questions"),
            primary_metric="Asset ID Trace Hit Rate@5",
            primary_value=asset_qa.get("asset_id_trace_hit_rate@5"),
            secondary_metrics={
                "Document Hit@5": asset_qa.get("doc_hit_rate@5"),
                "Page Hit@5": asset_qa.get("page_hit_rate@5"),
                "Asset Type Trace@5": asset_qa.get("asset_type_trace_hit_rate@5"),
            },
            note="Metadata proximity check, not visual interpretation.",
        )

    table_cell = read_json(eval_dir / "table_cell_qa_eval_results.json")
    if table_cell:
        add_metric_row(
            rows,
            experiment="Cell-level table QA",
            artifact="evaluation/table_cell_qa_eval_results.json",
            sample_count=table_cell.get("questions"),
            primary_metric="Cell QA success rate",
            primary_value=table_cell.get("cell_qa_success_rate"),
            secondary_metrics={
                "Evidence cell value hit": table_cell.get("evidence_cell_value_hit_rate"),
                "Answer cell value hit": table_cell.get("answer_cell_value_hit_rate"),
                "Asset trace@5": table_cell.get("asset_trace_hit_rate@5"),
                "Page Hit@5": table_cell.get("page_hit_rate@5"),
            },
            note="Checks short values from extracted table text previews.",
        )

    gold = read_json(eval_dir / "gold_answer_eval_results.json")
    if gold:
        add_metric_row(
            rows,
            experiment="External gold-answer seed",
            artifact="evaluation/gold_answer_eval_results.json",
            sample_count=gold.get("questions"),
            primary_metric="Gold-answer success rate",
            primary_value=gold.get("gold_answer_success_rate"),
            secondary_metrics={
                "Evidence value hit": gold.get("evidence_value_hit_rate"),
                "Answer value hit": gold.get("answer_value_hit_rate"),
                "Citation present": gold.get("citation_present_rate"),
            },
            note="Public short-answer seed; not expert clinical grading.",
        )

    answer_generation = read_json(eval_dir / "answer_generation_eval_results.json")
    if answer_generation:
        add_metric_row(
            rows,
            experiment="Answer generation mode comparison",
            artifact="evaluation/answer_generation_eval_results.json",
            sample_count=answer_generation.get("questions"),
            primary_metric="Extractive answer value hit rate",
            primary_value=answer_generation.get("extractive_answer_value_hit_rate"),
            secondary_metrics={
                "Evidence-only value hit": answer_generation.get("evidence_only_value_hit_rate"),
                "Bundle prompt value hit": answer_generation.get("bundle_prompt_value_hit_rate"),
                "Answer synthesis gap": answer_generation.get("answer_synthesis_gap_rate"),
                "Retrieval gap": answer_generation.get("retrieval_gap_rate"),
                "Citation present": answer_generation.get("citation_present_rate"),
            },
            note="Local no-hosted-LLM comparison separating evidence availability from extractive answer synthesis.",
        )

    answer_quality = read_json(eval_dir / "answer_quality_eval_results.json")
    if answer_quality:
        add_metric_row(
            rows,
            experiment="Answer-quality proxy",
            artifact="evaluation/answer_quality_eval_results.json",
            sample_count=answer_quality.get("questions"),
            primary_metric="Mean grounded token overlap",
            primary_value=answer_quality.get("mean_grounded_token_overlap"),
            secondary_metrics={
                "Citation marker": answer_quality.get("citation_marker_rate"),
                "Evidence ID valid": answer_quality.get("used_evidence_id_valid_rate"),
                "Unsupported number case": answer_quality.get("unsupported_number_case_rate"),
                "Overclaim flag": answer_quality.get("overclaim_flag_rate"),
                "OOD abstention": answer_quality.get("ood_abstention_success_rate"),
            },
            note="Automatic faithfulness proxy; not expert correctness grading.",
        )

    navigator = read_json(eval_dir / "navigator_eval_results.json")
    if navigator:
        add_metric_row(
            rows,
            experiment="Navigator retrieval",
            artifact="evaluation/navigator_eval_results.json",
            sample_count=navigator.get("questions"),
            primary_metric="Topic Recall@3",
            primary_value=navigator.get("topic_recall@3"),
            secondary_metrics={
                "Candidate Document Recall@5": navigator.get("candidate_doc_recall@5"),
            },
            note="Checks navigable topic index support.",
        )

    failure_taxonomy = read_json(eval_dir / "failure_taxonomy.json")
    if failure_taxonomy:
        add_metric_row(
            rows,
            experiment="Failure taxonomy",
            artifact="evaluation/failure_taxonomy.json",
            sample_count=failure_taxonomy.get("case_count"),
            primary_metric="Automatically classified failure/gap cases",
            primary_value=float(failure_taxonomy.get("case_count", 0)),
            secondary_metrics=failure_taxonomy.get("by_category", {}),
            note="Engineering failure taxonomy for paper discussion; not expert clinical adjudication.",
        )

    return {
        "matrix_version": "1.0",
        "evaluation_dir": str(eval_dir),
        "experiment_count": len(rows),
        "rows": rows,
    }


def write_markdown(matrix: Dict[str, Any], output_path: Path) -> None:
    lines = [
        "# Paper Experiment Matrix",
        "",
        f"- Evaluation directory: {matrix['evaluation_dir']}",
        f"- Experiment rows: {matrix['experiment_count']}",
        "",
        "| Experiment | N | Primary metric | Value | Secondary metrics | Note |",
        "|---|---:|---|---:|---|---|",
    ]
    for row in matrix["rows"]:
        secondary = "; ".join(f"{key}={value}" for key, value in row["secondary_metrics"].items())
        value = row["primary_value"]
        value_text = "" if value is None else f"{float(value):.3f}"
        lines.append(
            f"| {row['experiment']} | {row.get('sample_count') or ''} | {row['primary_metric']} | {value_text} | {secondary} | {row['note']} |"
        )
    lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build paper-facing experiment matrix.")
    parser.add_argument("--eval-dir", type=Path, default=Path("evaluation"))
    parser.add_argument("--output-json", type=Path, default=Path("evaluation/paper_experiment_matrix.json"))
    parser.add_argument("--output-md", type=Path, default=Path("evaluation/paper_experiment_matrix.md"))
    args = parser.parse_args()

    matrix = build_matrix(args.eval_dir)
    args.output_json.write_text(json.dumps(matrix, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(matrix, args.output_md)
    print(json.dumps({"experiment_count": matrix["experiment_count"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
