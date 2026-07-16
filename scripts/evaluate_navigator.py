#!/usr/bin/env python
"""Evaluate the topic-tree navigator as a routing surface."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Set

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils import iter_jsonl, simple_tokenize


def load_questions(path: Path) -> List[Dict]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def topic_label(path: Path) -> str:
    return path.stem


def load_topic_rows(navigator_dir: Path) -> Dict[str, List[Dict]]:
    rows: Dict[str, List[Dict]] = {}
    for path in sorted((navigator_dir / "topic_indexes").glob("*.jsonl")):
        rows[topic_label(path)] = list(iter_jsonl(path))
    return rows


def row_text(row: Dict) -> str:
    parts = [
        row.get("topic", ""),
        row.get("document", ""),
        row.get("section", ""),
        row.get("subsection", ""),
        " ".join(row.get("tags", [])),
    ]
    return " ".join(str(part) for part in parts if part and part != "UNKNOWN")


def topic_text(topic: str, rows: List[Dict]) -> str:
    counter = Counter()
    for row in rows:
        counter.update(simple_tokenize(row_text(row)))
    frequent = " ".join(word for word, _ in counter.most_common(80))
    return f"{topic.replace('-', ' ')} {frequent}"


def score_text(query_tokens: Set[str], text: str) -> float:
    text_tokens = set(simple_tokenize(text))
    if not query_tokens or not text_tokens:
        return 0.0
    overlap = query_tokens & text_tokens
    return len(overlap) / max(1, len(query_tokens))


def rank_topics(question: str, topic_rows: Dict[str, List[Dict]]) -> List[Dict]:
    query_tokens = set(simple_tokenize(question))
    ranked = []
    for topic, rows in topic_rows.items():
        score = score_text(query_tokens, topic_text(topic, rows))
        ranked.append({"topic": topic, "score": score, "doc_ids": sorted({row["doc_id"] for row in rows})})
    return sorted(ranked, key=lambda item: item["score"], reverse=True)


def rank_candidate_docs(question: str, selected_topics: Iterable[str], topic_rows: Dict[str, List[Dict]]) -> List[Dict]:
    query_tokens = set(simple_tokenize(question))
    doc_scores: Dict[str, float] = defaultdict(float)
    doc_titles: Dict[str, str] = {}
    for topic in selected_topics:
        for row in topic_rows.get(topic, []):
            doc_id = row["doc_id"]
            doc_titles.setdefault(doc_id, row.get("document", doc_id))
            doc_scores[doc_id] += score_text(query_tokens, row_text(row))
    ranked = [
        {"doc_id": doc_id, "score": score, "title": doc_titles.get(doc_id, doc_id)}
        for doc_id, score in doc_scores.items()
    ]
    return sorted(ranked, key=lambda item: item["score"], reverse=True)


def evaluate(questions: List[Dict], navigator_dir: Path, topic_k: int = 3, doc_k: int = 5) -> Dict:
    topic_rows = load_topic_rows(navigator_dir)
    details = []
    topic_hits = {1: 0, 2: 0, 3: 0}
    doc_hits = {1: 0, 3: 0, 5: 0}
    in_scope = 0

    for question in questions:
        expected_doc_id = question.get("report_id")
        if question.get("expected_abstain") or not expected_doc_id:
            continue
        in_scope += 1
        ranked_topics = rank_topics(question["question"], topic_rows)
        top_topics = [item["topic"] for item in ranked_topics[:topic_k]]
        ranked_docs = rank_candidate_docs(question["question"], top_topics, topic_rows)
        top_docs = [item["doc_id"] for item in ranked_docs[:doc_k]]

        for k in topic_hits:
            if any(expected_doc_id in item["doc_ids"] for item in ranked_topics[:k]):
                topic_hits[k] += 1
        for k in doc_hits:
            if expected_doc_id in top_docs[:k]:
                doc_hits[k] += 1

        details.append(
            {
                "qid": question["qid"],
                "question": question["question"],
                "expected_doc_id": expected_doc_id,
                "top_topics": top_topics,
                "top_candidate_docs": top_docs,
                "topic_hit_at_3": any(expected_doc_id in item["doc_ids"] for item in ranked_topics[:3]),
                "doc_hit_at_5": expected_doc_id in top_docs[:5],
            }
        )

    summary = {
        "questions": len(questions),
        "in_scope_questions": in_scope,
        "topic_recall@1": topic_hits[1] / in_scope if in_scope else 0.0,
        "topic_recall@2": topic_hits[2] / in_scope if in_scope else 0.0,
        "topic_recall@3": topic_hits[3] / in_scope if in_scope else 0.0,
        "candidate_doc_recall@1": doc_hits[1] / in_scope if in_scope else 0.0,
        "candidate_doc_recall@3": doc_hits[3] / in_scope if in_scope else 0.0,
        "candidate_doc_recall@5": doc_hits[5] / in_scope if in_scope else 0.0,
        "details": details,
    }
    return summary


def write_markdown(summary: Dict, output_path: Path) -> None:
    lines = [
        "# Navigator Evaluation Results",
        "",
        f"- Questions: {summary['questions']}",
        f"- In-scope questions: {summary['in_scope_questions']}",
        f"- Topic Recall@1: {summary['topic_recall@1']:.3f}",
        f"- Topic Recall@2: {summary['topic_recall@2']:.3f}",
        f"- Topic Recall@3: {summary['topic_recall@3']:.3f}",
        f"- Candidate Document Recall@1: {summary['candidate_doc_recall@1']:.3f}",
        f"- Candidate Document Recall@3: {summary['candidate_doc_recall@3']:.3f}",
        f"- Candidate Document Recall@5: {summary['candidate_doc_recall@5']:.3f}",
        "",
        "## Failed Candidate Document@5 Cases",
        "",
    ]
    failures = [item for item in summary["details"] if not item["doc_hit_at_5"]]
    if not failures:
        lines.append("None.")
    for item in failures[:100]:
        lines.extend(
            [
                f"### {item['qid']}",
                f"- Question: {item['question']}",
                f"- Expected doc_id: {item['expected_doc_id']}",
                f"- Top topics: {', '.join(item['top_topics'])}",
                f"- Top candidate docs: {', '.join(item['top_candidate_docs'])}",
                "",
            ]
        )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate navigator routing over public benchmark questions.")
    parser.add_argument("--questions", type=Path, default=Path("evaluation/public_credible_questions.json"))
    parser.add_argument("--navigator-dir", type=Path, default=Path("navigator"))
    parser.add_argument("--output-json", type=Path, default=Path("evaluation/navigator_eval_results.json"))
    parser.add_argument("--output-md", type=Path, default=Path("evaluation/navigator_eval_results.md"))
    args = parser.parse_args()

    summary = evaluate(load_questions(args.questions), args.navigator_dir)
    args.output_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(summary, args.output_md)
    print(json.dumps({k: v for k, v in summary.items() if k != "details"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
