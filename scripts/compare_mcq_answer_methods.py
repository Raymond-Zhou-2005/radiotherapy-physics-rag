#!/usr/bin/env python
"""Summarize parser and answer-host MCQ results without exposing answer keys.

The first comparison holds the deterministic option selector fixed across the
historical PyMuPDF and rebuilt OpenDataLoader indices.  The third result uses
a Codex agent that called the local skill before selecting an option, so it is
reported separately rather than as a parser-only ablation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def index_details(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    details = payload.get("details") or []
    indexed = {str(item["qid"]): item for item in details}
    if len(indexed) != len(details):
        raise ValueError("MCQ result details contain duplicate qids.")
    return indexed


def summarize(payload: dict[str, Any], accuracy_path: tuple[str, ...], latency_path: tuple[str, ...]) -> dict[str, Any]:
    node: Any = payload
    for key in accuracy_path:
        node = node[key]
    accuracy = float(node)
    node = payload
    for key in latency_path:
        node = node[key]
    return {"accuracy": accuracy, "mean_latency_seconds": float(node), "questions": int(payload["questions"])}


def outcome_change(left: dict[str, dict[str, Any]], right: dict[str, dict[str, Any]]) -> dict[str, int]:
    if set(left) != set(right):
        raise ValueError("MCQ method comparison requires matching qids.")
    groups = {"improved": 0, "regressed": 0, "both_correct": 0, "both_incorrect": 0}
    for qid in left:
        left_correct = bool(left[qid].get("selected_correct"))
        right_correct = bool(right[qid].get("selected_correct"))
        if not left_correct and right_correct:
            groups["improved"] += 1
        elif left_correct and not right_correct:
            groups["regressed"] += 1
        elif right_correct:
            groups["both_correct"] += 1
        else:
            groups["both_incorrect"] += 1
    return groups


def build_report(pymupdf: dict[str, Any], opendataloader: dict[str, Any], codex_agent: dict[str, Any]) -> dict[str, Any]:
    old_details = index_details(pymupdf)
    odl_details = index_details(opendataloader)
    agent_details = index_details(codex_agent)
    agent_latency = codex_agent["metrics"]["latency_seconds"]["mean"]
    return {
        "benchmark": {
            "name": pymupdf.get("dataset_name"),
            "questions": int(pymupdf["questions"]),
            "public_development_set": True,
            "boundary": (
                "All results use a public answer-keyed benchmark. They are not hidden-test, expert, or clinical-validation results."
            ),
        },
        "methods": [
            {
                "name": "PyMuPDF + deterministic cross-encoder option selector",
                "parser": "PyMuPDF historical snapshot",
                "answer_host": "deterministic option-evidence selector",
                **summarize(pymupdf, ("mcq_option_accuracy",), ("mean_total_latency_seconds",)),
            },
            {
                "name": "OpenDataLoader + deterministic cross-encoder option selector",
                "parser": "OpenDataLoader rebuilt runtime",
                "answer_host": "deterministic option-evidence selector",
                **summarize(opendataloader, ("mcq_option_accuracy",), ("mean_total_latency_seconds",)),
            },
            {
                "name": "OpenDataLoader + Codex agent using local skill evidence",
                "parser": "OpenDataLoader rebuilt runtime",
                "answer_host": "Codex agent, instructed to call the local skill before selecting",
                "accuracy": float(codex_agent["metrics"]["accuracy"]["rate"]),
                "mean_latency_seconds": float(agent_latency),
                "questions": int(codex_agent["questions"]),
            },
        ],
        "controlled_parser_comparison": outcome_change(old_details, odl_details),
        "host_reasoning_comparison": outcome_change(odl_details, agent_details),
        "interpretation": {
            "parser_ablation": (
                "Only the first two methods hold the answer-selection mechanism fixed and therefore isolate the parser/index change."
            ),
            "agent_result": (
                "The Codex-agent result changes both the parser/runtime and the answer host. It demonstrates agent use of skill evidence, not a parser-only effect."
            ),
            "host_transport": (
                "The Codex CLI MCP runner was implemented but its non-interactive Windows MCP call was cancelled by host authorization; this live result used direct local skill calls by the Codex agent."
            ),
        },
    }


def write_markdown(report: dict[str, Any], output: Path) -> None:
    lines = [
        "# Public MCQ Method Comparison",
        "",
        f"- Benchmark: {report['benchmark']['name']}",
        f"- Questions: {report['benchmark']['questions']}",
        f"- Boundary: {report['benchmark']['boundary']}",
        "",
        "| Method | Parser/runtime | Answer host | Accuracy | Mean latency (s/question) |",
        "|---|---|---|---:|---:|",
    ]
    for method in report["methods"]:
        lines.append(
            f"| {method['name']} | {method['parser']} | {method['answer_host']} | "
            f"{method['accuracy']:.3f} | {method['mean_latency_seconds']:.3f} |"
        )
    parser = report["controlled_parser_comparison"]
    host = report["host_reasoning_comparison"]
    lines.extend(
        [
            "",
            "## Pairwise Outcome Changes",
            "",
            f"- PyMuPDF selector to OpenDataLoader selector: improved {parser['improved']}, regressed {parser['regressed']}, both correct {parser['both_correct']}, both incorrect {parser['both_incorrect']}.",
            f"- OpenDataLoader selector to Codex-agent skill use: improved {host['improved']}, regressed {host['regressed']}, both correct {host['both_correct']}, both incorrect {host['both_incorrect']}.",
            "",
            "## Interpretation",
            "",
            f"- {report['interpretation']['parser_ablation']}",
            f"- {report['interpretation']['agent_result']}",
            f"- {report['interpretation']['host_transport']}",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare public MCQ parser and answer-host methods.")
    parser.add_argument("--pymupdf", type=Path, default=Path("evaluation/parser_comparison/pymupdf_baseline/public_mcq_eval_results.json"))
    parser.add_argument("--opendataloader", type=Path, default=Path("evaluation/parser_comparison/opendataloader/public_mcq_eval_results.json"))
    parser.add_argument("--codex-agent", type=Path, default=Path("evaluation/external/codex_agent_skill_score.json"))
    parser.add_argument("--output-json", type=Path, default=Path("evaluation/external/mcq_method_comparison.json"))
    parser.add_argument("--output-md", type=Path, default=Path("evaluation/external/mcq_method_comparison.md"))
    args = parser.parse_args()

    report = build_report(read_json(args.pymupdf), read_json(args.opendataloader), read_json(args.codex_agent))
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, args.output_md)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
