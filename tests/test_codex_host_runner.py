import json

import pytest

from scripts.run_codex_host_mcq import (
    CodexHostError,
    HostTask,
    RunnerValidationError,
    build_codex_command,
    build_response_schema,
    load_resume_answers,
    load_tasks,
    parse_json_events,
    parse_model_response,
    remaining_tasks,
    successful_query_reports_call,
)


def _write_jsonl(path, records):
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")


def _task_record(qid="q1"):
    return {
        "qid": qid,
        "question": "Which option is correct?",
        "options": [{"label": "A", "text": "one"}, {"label": "B", "text": "two"}],
        "required_host_behavior": "Use MCP evidence only.",
    }


def test_response_schema_uses_only_the_task_labels():
    schema = build_response_schema(["A", "B", "A"])

    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert schema["properties"]["selected_label"]["enum"] == ["A", "B"]
    assert schema["required"] == ["selected_label", "citations"]


def test_load_tasks_accepts_fixed_gold_free_schema(tmp_path):
    tasks_path = tmp_path / "tasks.jsonl"
    _write_jsonl(tasks_path, [_task_record()])

    tasks = load_tasks(tasks_path)

    assert tasks[0].qid == "q1"
    assert tasks[0].labels == ("A", "B")


def test_load_tasks_rejects_gold_field(tmp_path):
    tasks_path = tmp_path / "tasks.jsonl"
    record = _task_record()
    record["gold_label"] = "A"
    _write_jsonl(tasks_path, [record])

    with pytest.raises(RunnerValidationError, match="public host-task schema"):
        load_tasks(tasks_path)


def test_resume_helpers_skip_completed_qids_and_reject_duplicates(tmp_path):
    tasks_path = tmp_path / "tasks.jsonl"
    _write_jsonl(tasks_path, [_task_record("q1"), _task_record("q2")])
    tasks = load_tasks(tasks_path)
    answers_path = tmp_path / "answers.jsonl"
    _write_jsonl(answers_path, [{"qid": "q1", "selected_label": "A", "latency_seconds": 1.5}])

    completed = load_resume_answers(answers_path, tasks)

    assert [task.qid for task in remaining_tasks(tasks, completed)] == ["q2"]
    _write_jsonl(
        answers_path,
        [
            {"qid": "q1", "selected_label": "A", "latency_seconds": 1.5},
            {"qid": "q1", "selected_label": "A", "latency_seconds": 2.0},
        ],
    )
    with pytest.raises(RunnerValidationError, match="repeats qid"):
        load_resume_answers(answers_path, tasks)


def test_event_parsing_requires_successful_query_reports_before_accepting_answer():
    events = parse_json_events(
        "\n".join(
            [
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {
                            "type": "mcp_tool_call",
                            "server": "radiotherapy_physics_rag",
                            "tool": "query_reports",
                            "status": "completed",
                            "result": {"content": []},
                            "error": None,
                        },
                    }
                ),
                json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": '{"selected_label":"A","citations":[]}'}}),
                "non-json diagnostic",
            ]
        )
    )

    assert successful_query_reports_call(events) is True
    task = HostTask("q1", "Question?", (("A", "one"), ("B", "two")), "Use MCP.")
    assert parse_model_response('{"selected_label":"A","citations":[]}', task) == {
        "selected_label": "A",
        "citations": [],
    }
    with pytest.raises(CodexHostError, match="violates the response schema"):
        parse_model_response('{"selected_label":"A","extra":true}', task)


def test_command_uses_ephemeral_command_scoped_mcp_configuration(tmp_path):
    command = build_codex_command(
        codex_bin=tmp_path / "codex.exe",
        schema_path=tmp_path / "schema.json",
        isolated_workdir=tmp_path / "host-workdir",
        index_dir=tmp_path / "index",
        timeout_seconds=12.1,
        prompt="Question",
    )
    joined = "\n".join(command)

    assert "--ephemeral" in command
    assert "--sandbox" in command and "read-only" in command
    assert "--ignore-user-config" in command
    assert "mcp add" not in joined
    assert "mcp_servers.radiotherapy_physics_rag.command" in joined
    assert "mcp_servers.radiotherapy_physics_rag.tool_timeout_sec=13" in joined
