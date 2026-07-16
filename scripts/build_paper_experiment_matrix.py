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

    agent_tasks = read_json(eval_dir / "agent_task_eval_results.json")
    if agent_tasks:
        add_metric_row(
            rows,
            experiment="Direct skill contract tasks",
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
            note="Direct Python skill-contract integration; not an MCP transport or autonomous-agent evaluation.",
        )

    mcp_contract = read_json(eval_dir / "mcp_contract_eval_results.json")
    if mcp_contract:
        add_metric_row(
            rows,
            experiment="MCP stdio contract integration",
            artifact="evaluation/mcp_contract_eval_results.json",
            sample_count=mcp_contract.get("tasks"),
            primary_metric="Task success rate",
            primary_value=mcp_contract.get("task_success_rate"),
            secondary_metrics={
                "Required tools present": mcp_contract.get("required_tools_present"),
                "In-scope task success": mcp_contract.get("in_scope_task_success_rate"),
                "OOD refusal": mcp_contract.get("ood_refusal_success_rate"),
                "Transport errors": mcp_contract.get("transport_error_count"),
                "Protocol version": mcp_contract.get("mcp_protocol_version"),
            },
            note="Separate-process MCP stdio client/server test; not autonomous host-agent planning evaluation.",
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
            experiment="Public answer-target aggregate",
            artifact="evaluation/gold_answer_eval_results.json",
            sample_count=gold.get("questions"),
            primary_metric="Gold-answer success rate",
            primary_value=gold.get("gold_answer_success_rate"),
            secondary_metrics={
                "Evidence value hit": gold.get("evidence_value_hit_rate"),
                "Answer value hit": gold.get("answer_value_hit_rate"),
                "Citation present": gold.get("citation_present_rate"),
            },
            note="Combined profiles; interpret only together with the two profile-specific rows below.",
        )
        for profile, metrics in (gold.get("by_benchmark_profile") or {}).items():
            is_external = profile == "external_gold_answer"
            add_metric_row(
                rows,
                experiment=f"Public answer-target: {profile}",
                artifact="evaluation/gold_answer_eval_results.json",
                sample_count=metrics.get("questions"),
                primary_metric="Gold-answer success rate",
                primary_value=metrics.get("gold_answer_success_rate"),
                secondary_metrics={
                    "Evidence value hit": metrics.get("evidence_value_hit_rate"),
                    "Answer value hit": metrics.get("answer_value_hit_rate"),
                    "Citation present": metrics.get("citation_present_rate"),
                },
                note=(
                    "Small external public-answer-key stress test; not expert-adjudicated."
                    if is_external
                    else "In-corpus open-report target check; not an independent generalization test."
                ),
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
        for profile, metrics in (answer_generation.get("by_benchmark_profile") or {}).items():
            add_metric_row(
                rows,
                experiment=f"Answer synthesis: {profile}",
                artifact="evaluation/answer_generation_eval_results.json",
                sample_count=metrics.get("questions"),
                primary_metric="Extractive answer value hit rate",
                primary_value=metrics.get("extractive_answer_value_hit_rate"),
                secondary_metrics={
                    "Evidence-only value hit": metrics.get("evidence_only_value_hit_rate"),
                    "Answer synthesis gap": metrics.get("answer_synthesis_gap_rate"),
                    "Retrieval gap": metrics.get("retrieval_gap_rate"),
                },
                note="Profile-specific answer-synthesis diagnostic; not expert answer grading.",
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

    pymupdf_mcq = read_json(eval_dir / "parser_comparison" / "pymupdf_baseline" / "public_mcq_eval_results.json")
    opendataloader_mcq = read_json(eval_dir / "parser_comparison" / "opendataloader" / "public_mcq_eval_results.json")
    if pymupdf_mcq and opendataloader_mcq:
        for label, artifact, result in [
            ("Public MCQ parser baseline: PyMuPDF", "evaluation/parser_comparison/pymupdf_baseline/public_mcq_eval_results.json", pymupdf_mcq),
            ("Public MCQ parser comparison: OpenDataLoader", "evaluation/parser_comparison/opendataloader/public_mcq_eval_results.json", opendataloader_mcq),
        ]:
            add_metric_row(
                rows,
                experiment=label,
                artifact=artifact,
                sample_count=result.get("questions"),
                primary_metric="MCQ option accuracy",
                primary_value=result.get("mcq_option_accuracy"),
                secondary_metrics={
                    "Mean total latency seconds": result.get("mean_total_latency_seconds"),
                    "Option selector": result.get("option_selector"),
                    "Option selector backend": result.get("option_selector_backend"),
                },
                note="Same deterministic option-evidence selector; parser/index comparison only, not host-agent evaluation.",
            )

    codex_score = read_json(eval_dir / "external" / "codex_agent_skill_score.json")
    codex_metrics = codex_score.get("metrics") or {}
    if codex_metrics:
        accuracy = codex_metrics.get("accuracy") or {}
        citations = codex_metrics.get("citation_rate") or {}
        latency = codex_metrics.get("latency_seconds") or {}
        add_metric_row(
            rows,
            experiment="Public MCQ: Codex agent using local skill evidence",
            artifact="evaluation/external/codex_agent_skill_score.json",
            sample_count=accuracy.get("total"),
            primary_metric="MCQ accuracy",
            primary_value=accuracy.get("rate"),
            secondary_metrics={
                "Correct": accuracy.get("correct"),
                "Citation rate": citations.get("rate"),
                "Mean latency seconds": latency.get("mean"),
                "P95 latency seconds": latency.get("p95_nearest_rank"),
            },
            note="Recorded Codex-agent local-skill run on public development data; not blinded, expert-adjudicated, or CLI-MCP end-to-end.",
        )

    return {
        "matrix_version": "1.2",
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
