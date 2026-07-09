#!/usr/bin/env python
"""Run formal retrieval ablations in isolated subprocesses."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]


ABLATION_VARIANTS: List[Dict[str, Any]] = [
    {
        "variant": "bm25_lexical_no_reportaware",
        "description": "BM25 candidates, lexical rerank, report-aware heuristics disabled.",
        "strategy": "sparse",
        "uses_dense": False,
        "uses_cross_encoder": False,
        "uses_reportaware": False,
        "uses_routing": False,
        "env": {
            "RAG_FORCE_LEXICAL_RERANK": "1",
            "RAG_SPARSE_RERANK_BACKEND": "lexical",
            "USE_RETRIEVAL_HEURISTICS": "0",
            "USE_RERANK_HEURISTICS": "0",
        },
    },
    {
        "variant": "bm25_lexical_reportaware",
        "description": "BM25 candidates, lexical rerank, report-aware heuristics enabled.",
        "strategy": "sparse",
        "uses_dense": False,
        "uses_cross_encoder": False,
        "uses_reportaware": True,
        "uses_routing": False,
        "env": {
            "RAG_FORCE_LEXICAL_RERANK": "1",
            "RAG_SPARSE_RERANK_BACKEND": "lexical",
            "USE_RETRIEVAL_HEURISTICS": "1",
            "USE_RERANK_HEURISTICS": "1",
        },
    },
    {
        "variant": "hybrid_lexical_no_reportaware",
        "description": "Semantic dense + BM25 hybrid candidates, lexical rerank, report-aware heuristics disabled.",
        "strategy": "hybrid",
        "uses_dense": True,
        "uses_cross_encoder": False,
        "uses_reportaware": False,
        "uses_routing": False,
        "env": {
            "RAG_FORCE_LEXICAL_RERANK": "1",
            "RAG_RERANKER_BACKEND": "lexical",
            "USE_RETRIEVAL_HEURISTICS": "0",
            "USE_RERANK_HEURISTICS": "0",
        },
    },
    {
        "variant": "hybrid_crossencoder_no_reportaware",
        "description": "Semantic dense + BM25 hybrid candidates, cross-encoder rerank, report-aware heuristics disabled.",
        "strategy": "hybrid",
        "uses_dense": True,
        "uses_cross_encoder": True,
        "uses_reportaware": False,
        "uses_routing": False,
        "env": {
            "RAG_FORCE_LEXICAL_RERANK": "0",
            "RAG_RERANKER_BACKEND": "cross_encoder",
            "USE_RETRIEVAL_HEURISTICS": "0",
            "USE_RERANK_HEURISTICS": "0",
        },
    },
    {
        "variant": "hybrid_crossencoder_reportaware",
        "description": "Semantic dense + BM25 hybrid candidates, cross-encoder rerank, report-aware heuristics enabled.",
        "strategy": "hybrid",
        "uses_dense": True,
        "uses_cross_encoder": True,
        "uses_reportaware": True,
        "uses_routing": False,
        "env": {
            "RAG_FORCE_LEXICAL_RERANK": "0",
            "RAG_RERANKER_BACKEND": "cross_encoder",
            "USE_RETRIEVAL_HEURISTICS": "1",
            "USE_RERANK_HEURISTICS": "1",
        },
    },
    {
        "variant": "routed_full",
        "description": "Scene-routed retrieval with semantic dense available, cross-encoder rerank, report-aware heuristics enabled.",
        "strategy": "routed",
        "uses_dense": True,
        "uses_cross_encoder": True,
        "uses_reportaware": True,
        "uses_routing": True,
        "env": {
            "RAG_FORCE_LEXICAL_RERANK": "0",
            "RAG_RERANKER_BACKEND": "cross_encoder",
            "RAG_SPARSE_RERANK_BACKEND": "cross_encoder",
            "USE_RETRIEVAL_HEURISTICS": "1",
            "USE_RERANK_HEURISTICS": "1",
            "RAG_EXPERIENCE_APPEND": "0",
        },
    },
]


def run_variant(
    variant: Dict[str, Any],
    questions: Path,
    index_dir: Path,
    ignore_report_scope: bool,
    temp_dir: Path,
) -> Dict[str, Any]:
    output_json = temp_dir / f"{variant['variant']}.json"
    output_md = temp_dir / f"{variant['variant']}.md"
    env = os.environ.copy()
    env.update({key: str(value) for key, value in variant["env"].items()})
    env.setdefault("PYTHONIOENCODING", "utf-8")

    command = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "evaluate_strategies.py"),
        "--questions",
        str(questions),
        "--index-dir",
        str(index_dir),
        "--strategies",
        variant["strategy"],
        "--output-json",
        str(output_json),
        "--output-md",
        str(output_md),
    ]
    if ignore_report_scope:
        command.append("--ignore-report-scope")

    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=7200,
    )
    if completed.returncode != 0:
        return {
            **{key: variant[key] for key in variant if key != "env"},
            "ok": False,
            "error": completed.stderr[-4000:] or completed.stdout[-4000:],
        }

    payload = json.loads(output_json.read_text(encoding="utf-8"))
    summary = payload["strategies"][variant["strategy"]]
    return {
        **{key: variant[key] for key in variant if key != "env"},
        "ok": True,
        "questions": payload.get("question_count"),
        "recall@3": summary.get("recall@3"),
        "recall@5": summary.get("recall@5"),
        "doc_recall@3": summary.get("doc_recall@3"),
        "doc_recall@5": summary.get("doc_recall@5"),
        "mrr": summary.get("mrr"),
        "abstention": summary.get("abstention"),
        "observed_reranker_backends": summary.get("observed_reranker_backends", []),
        "ignore_report_scope": summary.get("ignore_report_scope"),
    }


def write_markdown(results: Dict[str, Any], output_path: Path) -> None:
    lines = [
        "# Formal Ablation Results",
        "",
        f"- Question file: {results['question_file']}",
        f"- Index directory: {results['index_dir']}",
        f"- Ignore report scope: {results['ignore_report_scope']}",
        "",
        "| Variant | Dense | Cross-encoder requested | Report-aware | Routing | Doc Recall@5 | MRR | OOD TP/FN | Observed reranker |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for item in results["variants"]:
        abst = item.get("abstention") or {}
        lines.append(
            "| {variant} | {dense} | {ce} | {reportaware} | {routing} | {doc5:.3f} | {mrr:.3f} | {tp}/{fn} | {reranker} |".format(
                variant=item["variant"],
                dense=int(bool(item.get("uses_dense"))),
                ce=int(bool(item.get("uses_cross_encoder"))),
                reportaware=int(bool(item.get("uses_reportaware"))),
                routing=int(bool(item.get("uses_routing"))),
                doc5=float(item.get("doc_recall@5") or 0.0),
                mrr=float(item.get("mrr") or 0.0),
                tp=abst.get("tp", 0),
                fn=abst.get("fn", 0),
                reranker=", ".join(item.get("observed_reranker_backends", [])),
            )
        )
    lines.extend(
        [
            "",
            "Metric note: variants are run in isolated subprocesses so environment-controlled config is reloaded for each condition.",
            "If a requested neural reranker cannot be loaded, the observed reranker column will show lexical fallback.",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run formal retrieval ablations.")
    parser.add_argument("--questions", type=Path, default=Path("evaluation/public_credible_questions.json"))
    parser.add_argument("--index-dir", type=Path, default=Path("index"))
    parser.add_argument("--ignore-report-scope", action="store_true", default=True)
    parser.add_argument("--output-json", type=Path, default=Path("evaluation/ablation_eval_results.json"))
    parser.add_argument("--output-md", type=Path, default=Path("evaluation/ablation_eval_results.md"))
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        temp_dir = Path(tmp)
        variants = [
            run_variant(item, args.questions, args.index_dir, args.ignore_report_scope, temp_dir)
            for item in ABLATION_VARIANTS
        ]

    results = {
        "question_file": str(args.questions),
        "index_dir": str(args.index_dir),
        "ignore_report_scope": args.ignore_report_scope,
        "variants": variants,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(results, args.output_md)
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
