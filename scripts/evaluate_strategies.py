#!/usr/bin/env python
"""Compare retrieval strategies on one evaluation question file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.evaluate import evaluate_retrieval, load_questions


def write_markdown(results: dict, output_path: Path) -> None:
    lines = ["# Strategy Evaluation Results", ""]
    for strategy, summary in results["strategies"].items():
        abst = summary["abstention"]
        lines.extend(
            [
                f"## {strategy}",
                "",
                f"- Recall@3: {summary['recall@3']:.3f}",
                f"- Recall@5: {summary['recall@5']:.3f}",
                f"- Document Recall@3: {summary['doc_recall@3']:.3f}",
                f"- Document Recall@5: {summary['doc_recall@5']:.3f}",
                f"- MRR: {summary['mrr']:.3f}",
                f"- Abstention: TP={abst['tp']}, FP={abst['fp']}, TN={abst['tn']}, FN={abst['fn']}",
                f"- Ignore report scope: {summary['ignore_report_scope']}",
                "",
            ]
        )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate sparse, auto, routed, and optional hybrid retrieval strategies.")
    parser.add_argument("--questions", type=Path, default=Path("evaluation/public_credible_questions.json"))
    parser.add_argument("--index-dir", type=Path, default=Path("index"))
    parser.add_argument("--strategies", nargs="+", default=["sparse", "auto", "routed"])
    parser.add_argument("--ignore-report-scope", action="store_true")
    parser.add_argument("--output-json", type=Path, default=Path("evaluation/strategy_eval_results.json"))
    parser.add_argument("--output-md", type=Path, default=Path("evaluation/strategy_eval_results.md"))
    args = parser.parse_args()

    questions = load_questions(args.questions)
    results = {
        "question_file": str(args.questions),
        "index_dir": str(args.index_dir),
        "question_count": len(questions),
        "strategies": {},
    }
    for strategy in args.strategies:
        results["strategies"][strategy] = evaluate_retrieval(
            questions,
            args.index_dir,
            retrieval_backend=strategy,
            ignore_report_scope=args.ignore_report_scope,
        )

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(results, args.output_md)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

