#!/usr/bin/env python
"""Evaluate retrieval and abstention behavior.

This script intentionally automates what can be measured robustly and exports a
manual-review file for answer quality dimensions such as completeness and
fine-grained groundedness.

Example
-------
python scripts/evaluate.py --questions evaluation/public_credible_questions.json --output evaluation/public_credible_eval_results.md
"""

from __future__ import annotations

import sys
from pathlib import Path as _PathBootstrap

# Allow `python scripts/<name>.py` to import the local src package.
PROJECT_ROOT = _PathBootstrap(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
import json
from pathlib import Path
from typing import Dict, List

from scripts.run_skill import RETRIEVAL_BACKENDS, assess_evidence_sufficiency, collect_evidence_with_backend
from src.evaluation.metrics import abstention_confusion, mrr, recall_at_k, section_match_recall


def load_questions(path: Path) -> List[Dict]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)



def evaluate_retrieval(
    questions: List[Dict],
    index_dir: Path,
    retrieval_backend: str = "sparse",
    ignore_report_scope: bool = False,
) -> Dict:
    r3 = []
    r5 = []
    reciprocal_ranks = []
    doc_r3 = []
    doc_r5 = []
    abstain_counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    detailed = []
    observed_reranker_backends = set()

    for q in questions:
        expected_doc_id = q.get("report_id")
        report_scope = None if ignore_report_scope else expected_doc_id
        ranked, actual_backend, warnings = collect_evidence_with_backend(
            query=q["question"],
            index_dir=index_dir,
            report_id=report_scope,
            retrieval_backend=retrieval_backend,
        )
        retrieved_ids = [item["chunk_id"] for item in ranked]
        retrieved_doc_ids = [item["chunk"]["doc_id"] for item in ranked]
        retrieved_sections = [item["chunk"]["section"] for item in ranked]
        reranker_backends = sorted({str(item.get("reranker_backend")) for item in ranked if item.get("reranker_backend")})
        observed_reranker_backends.update(reranker_backends)

        if q.get("gold_chunk_ids"):
            r3.append(recall_at_k(retrieved_ids, q["gold_chunk_ids"], 3))
            r5.append(recall_at_k(retrieved_ids, q["gold_chunk_ids"], 5))
            reciprocal_ranks.append(mrr(retrieved_ids, q["gold_chunk_ids"]))
        elif q.get("gold_section"):
            r3.append(section_match_recall(retrieved_sections, q["gold_section"], 3))
            r5.append(section_match_recall(retrieved_sections, q["gold_section"], 5))
            reciprocal_ranks.append(0.0)

        if expected_doc_id and not q.get("expected_abstain", False):
            doc_r3.append(1.0 if expected_doc_id in retrieved_doc_ids[:3] else 0.0)
            doc_r5.append(1.0 if expected_doc_id in retrieved_doc_ids[:5] else 0.0)

        sufficiency = assess_evidence_sufficiency(q["question"], ranked)
        pred_abstained = not sufficiency["sufficient"]
        gold_should_abstain = bool(q.get("expected_abstain", False))
        counts = abstention_confusion(pred_abstained, gold_should_abstain)
        for key in abstain_counts:
            abstain_counts[key] += counts[key]

        detailed.append(
            {
                "qid": q["qid"],
                "question": q["question"],
                "expected_doc_id": expected_doc_id,
                "report_scope_applied": report_scope,
                "retrieved_chunk_ids": retrieved_ids,
                "retrieved_doc_ids": retrieved_doc_ids,
                "retrieved_sections": retrieved_sections,
                "reranker_backends": reranker_backends,
                "predicted_abstain_proxy": pred_abstained,
                "expected_abstain": gold_should_abstain,
                "source_basis": q.get("source_basis") or q.get("authority_source", ""),
                "source_urls": q.get("source_urls", []),
                "source_note": q.get("source_note", ""),
                "sufficiency": sufficiency,
                "retrieval_backend": actual_backend,
                "retrieval_warnings": warnings,
            }
        )

    summary = {
        "recall@3": sum(r3) / len(r3) if r3 else 0.0,
        "recall@5": sum(r5) / len(r5) if r5 else 0.0,
        "doc_recall@3": sum(doc_r3) / len(doc_r3) if doc_r3 else 0.0,
        "doc_recall@5": sum(doc_r5) / len(doc_r5) if doc_r5 else 0.0,
        "mrr": sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0,
        "abstention": abstain_counts,
        "retrieval_backend": retrieval_backend,
        "observed_reranker_backends": sorted(observed_reranker_backends),
        "ignore_report_scope": ignore_report_scope,
        "details": detailed,
    }
    return summary



def write_markdown_report(summary: Dict, output_path: Path) -> None:
    lines = []
    lines.append("# Evaluation Results\n")
    lines.append(f"- Recall@3: {summary['recall@3']:.3f}")
    lines.append(f"- Recall@5: {summary['recall@5']:.3f}")
    lines.append(f"- Document Recall@3: {summary['doc_recall@3']:.3f}")
    lines.append(f"- Document Recall@5: {summary['doc_recall@5']:.3f}")
    lines.append(f"- MRR: {summary['mrr']:.3f}")
    lines.append(f"- Observed reranker backends: {', '.join(summary.get('observed_reranker_backends', []))}")
    lines.append(
        f"- Abstention confusion counts: TP={summary['abstention']['tp']}, FP={summary['abstention']['fp']}, TN={summary['abstention']['tn']}, FN={summary['abstention']['fn']}"
    )
    lines.append(f"- Requested retrieval backend: {summary['retrieval_backend']}")
    lines.append(f"- Report scope ignored during retrieval: {summary['ignore_report_scope']}")
    lines.append("\n## Detailed retrieval outputs\n")
    for item in summary["details"]:
        lines.append(f"### {item['qid']}: {item['question']}")
        lines.append(f"- Expected doc_id: {item['expected_doc_id']}")
        if item.get("source_basis"):
            lines.append(f"- Public source basis: {item['source_basis']}")
        if item.get("source_urls"):
            lines.append(f"- Public source URLs: {', '.join(item['source_urls'])}")
        if item.get("source_note"):
            lines.append(f"- Source note: {item['source_note']}")
        lines.append(f"- Report scope applied: {item['report_scope_applied']}")
        lines.append(f"- Retrieved doc_ids: {', '.join(item['retrieved_doc_ids'])}")
        lines.append(f"- Retrieved chunks: {', '.join(item['retrieved_chunk_ids'])}")
        lines.append(f"- Retrieved sections: {' | '.join(item['retrieved_sections'])}")
        lines.append(f"- Predicted abstain proxy: {item['predicted_abstain_proxy']}")
        lines.append(f"- Expected abstain: {item['expected_abstain']}\n")

    output_path.write_text("\n".join(lines), encoding="utf-8")



def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", type=Path, default=Path("evaluation/public_credible_questions.json"))
    parser.add_argument("--index-dir", type=Path, default=Path("index"))
    parser.add_argument("--output", type=Path, default=Path("evaluation/public_credible_eval_results.md"))
    parser.add_argument("--retrieval-backend", choices=sorted(RETRIEVAL_BACKENDS), default="sparse")
    parser.add_argument(
        "--ignore-report-scope",
        action="store_true",
        help="Use report_id only as gold metadata, not as a retrieval filter.",
    )
    args = parser.parse_args()

    questions = load_questions(args.questions)
    summary = evaluate_retrieval(
        questions,
        args.index_dir,
        retrieval_backend=args.retrieval_backend,
        ignore_report_scope=args.ignore_report_scope,
    )
    write_markdown_report(summary, args.output)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
