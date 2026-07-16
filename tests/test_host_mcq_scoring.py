import json

import pytest

from scripts.score_host_mcq_answers import ScoringValidationError, score_host_answers


def _write_json(path, value):
    path.write_text(json.dumps(value), encoding="utf-8")


def _write_jsonl(path, records):
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")


def _make_inputs(tmp_path, answers):
    questions_path = tmp_path / "questions.json"
    tasks_path = tmp_path / "tasks.jsonl"
    answers_path = tmp_path / "answers.jsonl"
    questions = {
        "question_count": 2,
        "questions": [
            {
                "qid": "q1",
                "question": "First question?",
                "options": [{"label": "A", "text": "one"}, {"label": "B", "text": "two"}],
                "gold_label": "B",
            },
            {
                "qid": "q2",
                "question": "Second question?",
                "options": [{"label": "A", "text": "alpha"}, {"label": "B", "text": "beta"}],
                "gold_label": "A",
            },
        ],
    }
    tasks = [
        {
            "qid": item["qid"],
            "question": item["question"],
            "options": item["options"],
            "required_host_behavior": "Select one option label and cite evidence.",
        }
        for item in questions["questions"]
    ]
    _write_json(questions_path, questions)
    _write_jsonl(tasks_path, tasks)
    _write_jsonl(answers_path, answers)
    return questions_path, tasks_path, answers_path


def test_scores_complete_valid_answer_log(tmp_path):
    paths = _make_inputs(
        tmp_path,
        [
            {"qid": "q1", "selected_label": "B", "citations": [{"doc_id": "doc-1"}], "latency_seconds": 1.0},
            {"qid": "q2", "selected_label": "B", "latency_seconds": 3.0},
        ],
    )

    result = score_host_answers(*paths)

    assert result["metrics"]["accuracy"] == {"correct": 1, "total": 2, "rate": 0.5}
    assert result["metrics"]["citation_rate"] == {"with_citations": 1, "total": 2, "rate": 0.5}
    assert result["metrics"]["latency_seconds"]["mean"] == 2.0
    assert all("gold_label" not in detail for detail in result["details"])


def test_rejects_duplicate_answer_qid(tmp_path):
    paths = _make_inputs(
        tmp_path,
        [
            {"qid": "q1", "selected_label": "B", "latency_seconds": 1.0},
            {"qid": "q1", "selected_label": "A", "latency_seconds": 2.0},
        ],
    )

    with pytest.raises(ScoringValidationError, match="duplicate qid 'q1'"):
        score_host_answers(*paths)


def test_rejects_invalid_selected_label(tmp_path):
    paths = _make_inputs(
        tmp_path,
        [
            {"qid": "q1", "selected_label": "Z", "latency_seconds": 1.0},
            {"qid": "q2", "selected_label": "A", "latency_seconds": 2.0},
        ],
    )

    with pytest.raises(ScoringValidationError, match="not a valid label"):
        score_host_answers(*paths)
