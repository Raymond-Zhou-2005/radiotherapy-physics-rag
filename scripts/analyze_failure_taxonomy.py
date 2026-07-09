#!/usr/bin/env python
"""Build a paper-facing failure taxonomy from evaluation result files."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def add_case(cases: List[Dict[str, Any]], source: str, qid: str, category: str, detail: str, evidence: Dict[str, Any]) -> None:
    cases.append(
        {
            "source": source,
            "qid": qid,
            "category": category,
            "detail": detail,
            "retrieved_doc_ids_at_5": evidence.get("retrieved_doc_ids_at_5", []),
            "error_code": evidence.get("error_code"),
        }
    )


def classify_gold(gold: Dict[str, Any], cases: List[Dict[str, Any]]) -> None:
    for item in gold.get("details", []) or []:
        if item.get("gold_answer_success"):
            continue
        qid = str(item.get("qid"))
        if item.get("error_code"):
            add_case(cases, "gold_answer", qid, "skill_error", "Skill returned an error on an in-scope answer-target item.", item)
        elif not item.get("citation_present"):
            add_case(cases, "gold_answer", qid, "citation_contract_failure", "No citation was returned for an answer-target item.", item)
        elif item.get("evidence_value_hit") and not item.get("answer_value_hit"):
            add_case(cases, "gold_answer", qid, "answer_synthesis_gap", "Evidence contained the answer target but extractive answer did not surface it.", item)
        elif not item.get("evidence_value_hit"):
            add_case(cases, "gold_answer", qid, "retrieval_or_evidence_gap", "Returned evidence did not contain the expected answer target.", item)
        else:
            add_case(cases, "gold_answer", qid, "unclassified_gold_failure", "Failure did not match standard gold-answer categories.", item)


def classify_answer_generation(answer_gen: Dict[str, Any], cases: List[Dict[str, Any]]) -> None:
    for item in answer_gen.get("details", []) or []:
        qid = str(item.get("qid"))
        if item.get("retrieval_gap"):
            add_case(
                cases,
                "answer_generation",
                qid,
                "retrieval_gap",
                "Neither answer, evidence-only output, nor bundle prompt contained the expected target.",
                item,
            )
        elif item.get("answer_synthesis_gap"):
            add_case(
                cases,
                "answer_generation",
                qid,
                "answer_synthesis_gap",
                "Evidence or bundle contained the target but extractive answer did not.",
                item,
            )


def classify_agent_tasks(agent_tasks: Dict[str, Any], cases: List[Dict[str, Any]]) -> None:
    for item in agent_tasks.get("details", []) or []:
        if item.get("task_success"):
            continue
        qid = str(item.get("qid"))
        if item.get("expected_abstain") and not item.get("abstention_success"):
            add_case(cases, "agent_task", qid, "ood_abstention_failure", "Expected OOD abstention was not produced.", item)
        elif not item.get("doc_hit_at_5"):
            add_case(cases, "agent_task", qid, "document_miss", "No expected document appeared in the top-five evidence set.", item)
        elif not item.get("citation_success"):
            add_case(cases, "agent_task", qid, "citation_contract_failure", "Expected citations were missing.", item)
        elif not item.get("bundle_prompt_success"):
            add_case(cases, "agent_task", qid, "bundle_contract_failure", "Expected bundle prompt was missing.", item)
        elif not item.get("asset_trace_success"):
            add_case(cases, "agent_task", qid, "asset_trace_failure", "Expected table or figure asset trace was missing.", item)
        elif not item.get("answer_value_success"):
            add_case(cases, "agent_task", qid, "answer_value_gap", "Expected short answer value was not surfaced.", item)
        else:
            add_case(cases, "agent_task", qid, "unclassified_agent_task_failure", "Task failed for an unclassified reason.", item)


def classify_table_cells(table_cell: Dict[str, Any], cases: List[Dict[str, Any]]) -> None:
    for item in table_cell.get("details", []) or []:
        if item.get("cell_qa_success"):
            if item.get("evidence_cell_value_hit") and not item.get("answer_cell_value_hit"):
                add_case(
                    cases,
                    "table_cell",
                    str(item.get("qid")),
                    "answer_synthesis_gap",
                    "Cell value was present in evidence but not in the extractive answer.",
                    item,
                )
            continue
        qid = str(item.get("qid"))
        if not item.get("doc_hit_at_5"):
            add_case(cases, "table_cell", qid, "document_miss", "Expected table document was not retrieved.", item)
        elif not item.get("page_hit_at_5"):
            add_case(cases, "table_cell", qid, "page_miss", "Expected table page was not retrieved.", item)
        elif not item.get("asset_trace_hit_at_5"):
            add_case(cases, "table_cell", qid, "asset_trace_failure", "Expected table asset trace was not returned.", item)
        elif not item.get("evidence_cell_value_hit"):
            add_case(cases, "table_cell", qid, "cell_value_evidence_gap", "Expected cell value was absent from evidence and nearby assets.", item)
        else:
            add_case(cases, "table_cell", qid, "unclassified_table_failure", "Table-cell task failed for an unclassified reason.", item)


def build_taxonomy(eval_dir: Path) -> Dict[str, Any]:
    cases: List[Dict[str, Any]] = []
    classify_gold(read_json(eval_dir / "gold_answer_eval_results.json"), cases)
    classify_answer_generation(read_json(eval_dir / "answer_generation_eval_results.json"), cases)
    classify_agent_tasks(read_json(eval_dir / "agent_task_eval_results.json"), cases)
    classify_table_cells(read_json(eval_dir / "table_cell_qa_eval_results.json"), cases)

    by_category = Counter(case["category"] for case in cases)
    by_source = Counter(case["source"] for case in cases)
    return {
        "taxonomy_version": "1.0",
        "evaluation_dir": str(eval_dir),
        "case_count": len(cases),
        "by_category": dict(sorted(by_category.items())),
        "by_source": dict(sorted(by_source.items())),
        "cases": cases,
        "interpretation": (
            "Failure cases are automatically classified from benchmark outputs. "
            "They identify engineering failure modes, not expert clinical correctness."
        ),
    }


def write_markdown(taxonomy: Dict[str, Any], output_path: Path) -> None:
    lines = [
        "# Failure Taxonomy",
        "",
        f"- Evaluation directory: {taxonomy['evaluation_dir']}",
        f"- Failure/gap cases: {taxonomy['case_count']}",
        "",
        taxonomy["interpretation"],
        "",
        "## Counts By Category",
        "",
        "| Category | Count |",
        "|---|---:|",
    ]
    for category, count in taxonomy["by_category"].items():
        lines.append(f"| {category} | {count} |")
    lines.extend(["", "## Counts By Source", "", "| Source | Count |", "|---|---:|"])
    for source, count in taxonomy["by_source"].items():
        lines.append(f"| {source} | {count} |")
    lines.extend(["", "## Cases", ""])
    for case in taxonomy["cases"]:
        docs = ", ".join(str(x) for x in case.get("retrieved_doc_ids_at_5", []))
        lines.extend(
            [
                f"### {case['source']} / {case['qid']}",
                f"- Category: {case['category']}",
                f"- Detail: {case['detail']}",
                f"- Error code: {case.get('error_code')}",
                f"- Retrieved doc_ids@5: {docs}",
                "",
            ]
        )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze evaluation failures into a paper-facing taxonomy.")
    parser.add_argument("--eval-dir", type=Path, default=Path("evaluation"))
    parser.add_argument("--output-json", type=Path, default=Path("evaluation/failure_taxonomy.json"))
    parser.add_argument("--output-md", type=Path, default=Path("evaluation/failure_taxonomy.md"))
    args = parser.parse_args()

    taxonomy = build_taxonomy(args.eval_dir)
    args.output_json.write_text(json.dumps(taxonomy, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(taxonomy, args.output_md)
    print(json.dumps({k: v for k, v in taxonomy.items() if k != "cases"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
