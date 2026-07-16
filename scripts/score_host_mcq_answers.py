#!/usr/bin/env python
"""Score answer logs from a real Codex or MCP host on public MCQ tasks.

The benchmark JSON is the only input that contains answer keys. Host tasks and
score details remain answer-key-free, so this script can validate the boundary
between task delivery and post-run scoring without invoking a model or MCP
server.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


class ScoringValidationError(ValueError):
    """Raised when one of the benchmark, task, or answer-log contracts fails."""


@dataclass(frozen=True)
class BenchmarkQuestion:
    qid: str
    question: str
    options: tuple[tuple[str, str], ...]
    gold_label: str

    @property
    def labels(self) -> tuple[str, ...]:
        return tuple(label for label, _ in self.options)


HOST_TASK_FIELDS = frozenset({"qid", "question", "options", "required_host_behavior"})
ANSWER_FIELDS = frozenset({"qid", "selected_label", "citations", "latency_seconds"})


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ScoringValidationError(f"Cannot read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ScoringValidationError(f"Invalid JSON in {path}: {exc}") from exc


def _load_jsonl(path: Path, record_type: str) -> list[dict[str, Any]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ScoringValidationError(f"Cannot read {path}: {exc}") from exc

    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ScoringValidationError(f"Invalid {record_type} JSONL at {path}:{line_number}: {exc}") from exc
        if not isinstance(record, dict):
            raise ScoringValidationError(f"{record_type} record at {path}:{line_number} must be a JSON object.")
        records.append(record)

    if not records:
        raise ScoringValidationError(f"{record_type} JSONL {path} contains no records.")
    return records


def _require_string(value: Any, field: str, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ScoringValidationError(f"{context} field '{field}' must be a non-empty string.")
    return value


def _parse_options(value: Any, context: str) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, list) or not value:
        raise ScoringValidationError(f"{context} field 'options' must be a non-empty list.")

    options: list[tuple[str, str]] = []
    labels: set[str] = set()
    for option_number, option in enumerate(value, start=1):
        option_context = f"{context} option {option_number}"
        if not isinstance(option, dict):
            raise ScoringValidationError(f"{option_context} must be a JSON object.")
        label = _require_string(option.get("label"), "label", option_context)
        text = _require_string(option.get("text"), "text", option_context)
        if label in labels:
            raise ScoringValidationError(f"{context} contains duplicate option label '{label}'.")
        labels.add(label)
        options.append((label, text))
    return tuple(options)


def _index_unique_qids(records: Sequence[Mapping[str, Any]], record_type: str) -> dict[str, Mapping[str, Any]]:
    indexed: dict[str, Mapping[str, Any]] = {}
    for record_number, record in enumerate(records, start=1):
        qid = _require_string(record.get("qid"), "qid", f"{record_type} record {record_number}")
        if qid in indexed:
            raise ScoringValidationError(f"{record_type} contains duplicate qid '{qid}'.")
        indexed[qid] = record
    return indexed


def _require_same_qids(expected: set[str], observed: set[str], record_type: str) -> None:
    missing = sorted(expected - observed)
    unexpected = sorted(observed - expected)
    if missing or unexpected:
        parts: list[str] = []
        if missing:
            parts.append(f"missing qids: {', '.join(missing)}")
        if unexpected:
            parts.append(f"unexpected qids: {', '.join(unexpected)}")
        raise ScoringValidationError(f"{record_type} qids do not exactly match the benchmark ({'; '.join(parts)}).")


def _gold_field_paths(value: Any, path: str = "$") -> list[str]:
    """Return paths whose field names could expose answer-key information."""
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if isinstance(key, str) and "gold" in key.casefold():
                found.append(child_path)
            found.extend(_gold_field_paths(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_gold_field_paths(child, f"{path}[{index}]"))
    return found


def load_benchmark(path: Path, expected_question_count: int | None = None) -> dict[str, BenchmarkQuestion]:
    payload = _load_json(path)
    if not isinstance(payload, dict):
        raise ScoringValidationError(f"Benchmark {path} must be a JSON object.")

    raw_questions = payload.get("questions")
    if not isinstance(raw_questions, list) or not raw_questions:
        raise ScoringValidationError(f"Benchmark {path} field 'questions' must be a non-empty list.")
    if "question_count" in payload and payload["question_count"] != len(raw_questions):
        raise ScoringValidationError(
            f"Benchmark {path} question_count does not match its questions array ({payload['question_count']} != "
            f"{len(raw_questions)})."
        )
    if expected_question_count is not None and len(raw_questions) != expected_question_count:
        raise ScoringValidationError(
            f"Benchmark {path} must contain {expected_question_count} questions, found {len(raw_questions)}."
        )

    indexed = _index_unique_qids(
        [question if isinstance(question, dict) else {} for question in raw_questions], "benchmark"
    )
    if len(indexed) != len(raw_questions):
        raise ScoringValidationError(f"Benchmark {path} contains a non-object question record.")

    questions: dict[str, BenchmarkQuestion] = {}
    for raw_question in raw_questions:
        if not isinstance(raw_question, dict):
            raise ScoringValidationError(f"Benchmark {path} contains a non-object question record.")
        qid = _require_string(raw_question.get("qid"), "qid", "benchmark question")
        question = _require_string(raw_question.get("question"), "question", f"benchmark question {qid}")
        options = _parse_options(raw_question.get("options"), f"benchmark question {qid}")
        gold_label = _require_string(raw_question.get("gold_label"), "gold_label", f"benchmark question {qid}")
        labels = {label for label, _ in options}
        if gold_label not in labels:
            raise ScoringValidationError(
                f"Benchmark question {qid} gold_label '{gold_label}' is not one of its option labels."
            )
        questions[qid] = BenchmarkQuestion(qid=qid, question=question, options=options, gold_label=gold_label)
    return questions


def validate_host_tasks(
    task_records: Sequence[Mapping[str, Any]], benchmark: Mapping[str, BenchmarkQuestion]
) -> dict[str, Mapping[str, Any]]:
    """Validate answer-key-free host tasks against the public benchmark shell."""
    tasks = _index_unique_qids(task_records, "host tasks")
    _require_same_qids(set(benchmark), set(tasks), "host tasks")

    for qid, task in tasks.items():
        unexpected_fields = sorted(set(task) - HOST_TASK_FIELDS)
        if unexpected_fields:
            raise ScoringValidationError(f"Host task {qid} has unsupported fields: {', '.join(unexpected_fields)}.")
        gold_paths = _gold_field_paths(task)
        if gold_paths:
            raise ScoringValidationError(f"Host task {qid} exposes gold-key fields: {', '.join(gold_paths)}.")

        benchmark_question = benchmark[qid]
        question = _require_string(task.get("question"), "question", f"host task {qid}")
        options = _parse_options(task.get("options"), f"host task {qid}")
        behavior = _require_string(task.get("required_host_behavior"), "required_host_behavior", f"host task {qid}")
        if "gold" in behavior.casefold():
            raise ScoringValidationError(f"Host task {qid} required_host_behavior must not mention gold answers.")
        if question != benchmark_question.question:
            raise ScoringValidationError(f"Host task {qid} question text does not match the benchmark.")
        if options != benchmark_question.options:
            raise ScoringValidationError(f"Host task {qid} options do not match the benchmark.")
    return tasks


def validate_answers(
    answer_records: Sequence[Mapping[str, Any]], host_tasks: Mapping[str, Mapping[str, Any]]
) -> dict[str, Mapping[str, Any]]:
    """Validate complete, one-answer-per-task host output before scoring."""
    answers = _index_unique_qids(answer_records, "answers")
    _require_same_qids(set(host_tasks), set(answers), "answers")

    for qid, answer in answers.items():
        unexpected_fields = sorted(set(answer) - ANSWER_FIELDS)
        if unexpected_fields:
            raise ScoringValidationError(f"Answer {qid} has unsupported fields: {', '.join(unexpected_fields)}.")
        selected_label = _require_string(answer.get("selected_label"), "selected_label", f"answer {qid}")
        task_labels = {label for label, _ in _parse_options(host_tasks[qid].get("options"), f"host task {qid}")}
        if selected_label not in task_labels:
            raise ScoringValidationError(
                f"Answer {qid} selected_label '{selected_label}' is not a valid label for that task."
            )

        citations = answer.get("citations", [])
        if not isinstance(citations, list):
            raise ScoringValidationError(f"Answer {qid} citations must be a JSON array when provided.")
        if any(not isinstance(citation, (str, dict)) for citation in citations):
            raise ScoringValidationError(f"Answer {qid} citations must contain only strings or JSON objects.")

        latency = answer.get("latency_seconds")
        if isinstance(latency, bool) or not isinstance(latency, (int, float)):
            raise ScoringValidationError(f"Answer {qid} latency_seconds must be a finite non-negative number.")
        if not math.isfinite(float(latency)) or float(latency) < 0:
            raise ScoringValidationError(f"Answer {qid} latency_seconds must be a finite non-negative number.")
    return answers


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6)


def _nearest_rank_percentile(values: Sequence[float], percentile: float) -> float:
    ordered = sorted(values)
    rank = max(1, math.ceil(percentile * len(ordered)))
    return ordered[rank - 1]


def score_host_answers(
    questions_path: Path,
    host_tasks_path: Path,
    answers_path: Path,
    expected_question_count: int | None = None,
) -> dict[str, Any]:
    """Score a complete host answer log without exposing answer keys in details."""
    benchmark = load_benchmark(questions_path, expected_question_count=expected_question_count)
    host_tasks = validate_host_tasks(_load_jsonl(host_tasks_path, "host task"), benchmark)
    answers = validate_answers(_load_jsonl(answers_path, "answer"), host_tasks)

    details: list[dict[str, Any]] = []
    latencies: list[float] = []
    correct_count = 0
    cited_count = 0
    for qid in sorted(benchmark):
        answer = answers[qid]
        selected_correct = answer["selected_label"] == benchmark[qid].gold_label
        citations = answer.get("citations", [])
        latency = float(answer["latency_seconds"])
        citation_present = bool(citations)
        correct_count += int(selected_correct)
        cited_count += int(citation_present)
        latencies.append(latency)
        details.append(
            {
                "qid": qid,
                "selected_label": answer["selected_label"],
                "selected_correct": selected_correct,
                "citation_present": citation_present,
                "citation_count": len(citations),
                "latency_seconds": round(latency, 6),
            }
        )

    total = len(details)
    return {
        "schema_version": "1.0",
        "scorer": "host_mcq_answers",
        "inputs": {
            "benchmark_sha256": _sha256(questions_path),
            "host_tasks_sha256": _sha256(host_tasks_path),
            "answers_sha256": _sha256(answers_path),
        },
        "questions": total,
        "metrics": {
            "accuracy": {
                "correct": correct_count,
                "total": total,
                "rate": _rate(correct_count, total),
            },
            "citation_rate": {
                "with_citations": cited_count,
                "total": total,
                "rate": _rate(cited_count, total),
            },
            "latency_seconds": {
                "count": total,
                "mean": round(statistics.fmean(latencies), 6),
                "median": round(statistics.median(latencies), 6),
                "min": round(min(latencies), 6),
                "max": round(max(latencies), 6),
                "p95_nearest_rank": round(_nearest_rank_percentile(latencies, 0.95), 6),
            },
        },
        "details": details,
        "scoring_boundary": (
            "Gold labels are read only after host-task and answer-log validation. They are not included in host "
            "tasks or per-question score details."
        ),
    }


def write_markdown(result: Mapping[str, Any], output_path: Path) -> None:
    """Write a deterministic, answer-key-free human-readable scoring report."""
    accuracy = result["metrics"]["accuracy"]
    citation_rate = result["metrics"]["citation_rate"]
    latency = result["metrics"]["latency_seconds"]
    lines = [
        "# Codex/MCP Host MCQ Scoring",
        "",
        f"- Questions: {result['questions']}",
        f"- Accuracy: {accuracy['rate']:.3%} ({accuracy['correct']}/{accuracy['total']})",
        f"- Citation rate: {citation_rate['rate']:.3%} ({citation_rate['with_citations']}/{citation_rate['total']})",
        f"- Mean latency: {latency['mean']:.6f} s/question",
        f"- Median latency: {latency['median']:.6f} s/question",
        f"- P95 latency (nearest-rank): {latency['p95_nearest_rank']:.6f} s/question",
        f"- Latency range: {latency['min']:.6f}-{latency['max']:.6f} s/question",
        "",
        "## Per-Question Details",
        "",
        "| QID | Selected label | Correct | Citations | Latency (s) |",
        "| --- | --- | --- | ---: | ---: |",
    ]
    for detail in result["details"]:
        lines.append(
            f"| {detail['qid']} | {detail['selected_label']} | "
            f"{'yes' if detail['selected_correct'] else 'no'} | {detail['citation_count']} | "
            f"{detail['latency_seconds']:.6f} |"
        )
    lines.extend(["", str(result["scoring_boundary"]), ""])
    _write_text(output_path, "\n".join(lines))


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_outputs(result: Mapping[str, Any], json_path: Path, markdown_path: Path) -> None:
    _write_text(json_path, json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    write_markdown(result, markdown_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and score Codex/MCP host MCQ answer logs.")
    parser.add_argument(
        "--questions",
        type=Path,
        default=Path("evaluation/external/public_medical_physics_100_mcq.json"),
        help="Public answer-keyed 100-question benchmark JSON.",
    )
    parser.add_argument(
        "--host-tasks",
        type=Path,
        default=Path("evaluation/external/public_mcq_codex_host_tasks.jsonl"),
        help="Answer-key-free task JSONL supplied to the host.",
    )
    parser.add_argument("--answers", type=Path, required=True, help="Host-produced answer JSONL.")
    parser.add_argument("--output-json", type=Path, required=True, help="Path for the detailed score JSON.")
    parser.add_argument("--output-md", type=Path, required=True, help="Path for the Markdown score report.")
    parser.add_argument(
        "--expected-question-count",
        type=int,
        default=100,
        help="Required benchmark size; pass 0 to disable this check for a fixture or subset.",
    )
    args = parser.parse_args()
    if args.expected_question_count < 0:
        parser.error("--expected-question-count must be zero or a positive integer.")

    try:
        result = score_host_answers(
            args.questions,
            args.host_tasks,
            args.answers,
            expected_question_count=args.expected_question_count or None,
        )
        write_outputs(result, args.output_json, args.output_md)
    except ScoringValidationError as exc:
        parser.error(str(exc))

    summary = {
        "questions": result["questions"],
        "accuracy": result["metrics"]["accuracy"],
        "citation_rate": result["metrics"]["citation_rate"],
        "latency_seconds": result["metrics"]["latency_seconds"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
