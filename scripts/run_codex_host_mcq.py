#!/usr/bin/env python
"""Run public MCQ tasks through an ephemeral Codex host and local RAG MCP server."""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CODEX_BIN = Path(
    r"C:\Users\HUAWEI\AppData\Local\OpenAI\Codex\bin\3135b80b111fd431\codex.exe"
)
DEFAULT_PYTHON_BIN = Path(r"D:\APP\Anaconda\python.exe")
DEFAULT_TASKS = PROJECT_ROOT / "evaluation" / "external" / "public_mcq_codex_host_tasks.jsonl"
DEFAULT_INDEX_DIR = PROJECT_ROOT / "index"
MCP_SERVER = PROJECT_ROOT / "scripts" / "mcp_server.py"
MCP_NAME = "radiotherapy_physics_rag"
WORKSPACE_TEMP_DIR = Path(r"D:\CodexWorkplace\Temp")


class RunnerValidationError(ValueError):
    """Raised when a task, existing answer log, or model response is invalid."""


class CodexHostError(RuntimeError):
    """Raised when Codex fails to produce a verifiable MCP-grounded response."""


@dataclass(frozen=True)
class HostTask:
    qid: str
    question: str
    options: tuple[tuple[str, str], ...]
    required_host_behavior: str

    @property
    def labels(self) -> tuple[str, ...]:
        return tuple(label for label, _ in self.options)


def _toml_string(value: str) -> str:
    """Return a JSON string, which is also a valid TOML basic string."""
    return json.dumps(value)


def build_response_schema(labels: Sequence[str]) -> dict[str, Any]:
    """Build the strict schema sent to ``codex exec --output-schema``."""
    unique_labels = list(dict.fromkeys(labels))
    if not unique_labels or any(not label for label in unique_labels):
        raise RunnerValidationError("A response schema requires at least one non-empty option label.")
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "selected_label": {"type": "string", "enum": unique_labels},
            # Citation strings keep OpenAI's strict structured-output contract simple.
            "citations": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["selected_label", "citations"],
    }


def _read_jsonl(path: Path) -> Iterable[tuple[int, dict[str, Any]]]:
    if not path.is_file():
        raise RunnerValidationError(f"JSONL input does not exist: {path}")
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            record = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise RunnerValidationError(f"{path}:{line_number} is not valid JSON: {exc.msg}") from exc
        if not isinstance(record, dict):
            raise RunnerValidationError(f"{path}:{line_number} must contain a JSON object.")
        yield line_number, record


def load_tasks(path: Path) -> list[HostTask]:
    """Load the fixed public host-task schema and reject any gold-bearing input."""
    expected_fields = {"qid", "question", "options", "required_host_behavior"}
    tasks: list[HostTask] = []
    seen_qids: set[str] = set()

    for line_number, record in _read_jsonl(path):
        actual_fields = set(record)
        if actual_fields != expected_fields:
            unexpected = sorted(actual_fields - expected_fields)
            missing = sorted(expected_fields - actual_fields)
            raise RunnerValidationError(
                f"{path}:{line_number} must use exactly the public host-task schema; "
                f"unexpected={unexpected}, missing={missing}."
            )
        qid = record["qid"]
        question = record["question"]
        behavior = record["required_host_behavior"]
        options = record["options"]
        if not isinstance(qid, str) or not qid.strip():
            raise RunnerValidationError(f"{path}:{line_number} has an empty qid.")
        if qid in seen_qids:
            raise RunnerValidationError(f"{path}:{line_number} has duplicate qid {qid!r}.")
        if not isinstance(question, str) or not question.strip():
            raise RunnerValidationError(f"{path}:{line_number} has an empty question.")
        if not isinstance(behavior, str) or not behavior.strip():
            raise RunnerValidationError(f"{path}:{line_number} has an empty required_host_behavior.")
        if not isinstance(options, list) or len(options) < 2:
            raise RunnerValidationError(f"{path}:{line_number} must contain at least two options.")

        parsed_options: list[tuple[str, str]] = []
        labels: set[str] = set()
        for option_number, option in enumerate(options, start=1):
            if not isinstance(option, dict) or set(option) != {"label", "text"}:
                raise RunnerValidationError(
                    f"{path}:{line_number} option {option_number} must contain only label and text."
                )
            label, text = option["label"], option["text"]
            if not isinstance(label, str) or not label.strip() or not isinstance(text, str):
                raise RunnerValidationError(f"{path}:{line_number} option {option_number} is malformed.")
            if label in labels:
                raise RunnerValidationError(f"{path}:{line_number} repeats option label {label!r}.")
            labels.add(label)
            parsed_options.append((label, text))

        seen_qids.add(qid)
        tasks.append(HostTask(qid, question, tuple(parsed_options), behavior))

    if not tasks:
        raise RunnerValidationError(f"No public host tasks were found in {path}.")
    return tasks


def _validate_answer_record(record: dict[str, Any], task_by_qid: dict[str, HostTask], source: str) -> None:
    allowed_fields = {"qid", "selected_label", "citations", "latency_seconds"}
    required_fields = {"qid", "selected_label", "latency_seconds"}
    actual_fields = set(record)
    if not required_fields.issubset(actual_fields) or not actual_fields.issubset(allowed_fields):
        raise RunnerValidationError(f"{source} does not match the scorer answer schema.")
    qid = record["qid"]
    if not isinstance(qid, str) or qid not in task_by_qid:
        raise RunnerValidationError(f"{source} has an unknown qid {qid!r}.")
    selected_label = record["selected_label"]
    if selected_label not in task_by_qid[qid].labels:
        raise RunnerValidationError(f"{source} has invalid selected_label {selected_label!r} for {qid!r}.")
    latency = record["latency_seconds"]
    if isinstance(latency, bool) or not isinstance(latency, (int, float)) or not math.isfinite(latency) or latency < 0:
        raise RunnerValidationError(f"{source} has invalid latency_seconds.")
    if "citations" in record:
        citations = record["citations"]
        if not isinstance(citations, list) or not all(isinstance(item, (str, dict)) for item in citations):
            raise RunnerValidationError(f"{source} has invalid citations.")


def load_resume_answers(path: Path, tasks: Sequence[HostTask]) -> dict[str, dict[str, Any]]:
    """Load a partial JSONL answer log, rejecting duplicates and invalid rows."""
    if not path.exists():
        return {}
    task_by_qid = {task.qid: task for task in tasks}
    answers: dict[str, dict[str, Any]] = {}
    for line_number, record in _read_jsonl(path):
        source = f"{path}:{line_number}"
        _validate_answer_record(record, task_by_qid, source)
        qid = str(record["qid"])
        if qid in answers:
            raise RunnerValidationError(f"{source} repeats qid {qid!r} in the answer log.")
        answers[qid] = record
    return answers


def remaining_tasks(tasks: Sequence[HostTask], completed: dict[str, dict[str, Any]]) -> list[HostTask]:
    return [task for task in tasks if task.qid not in completed]


def build_prompt(task: HostTask) -> str:
    option_lines = "\n".join(f"{label}. {text}" for label, text in task.options)
    return f"""You are answering one public multiple-choice radiotherapy-physics question.

You must call the MCP tool `query_reports` on server `{MCP_NAME}` and use its result as evidence before answering. Do not use web search, shell commands, files, other MCP servers, or any answer key. Do not look for or infer gold labels. The question and options below are the only benchmark input you receive.

Return only the JSON object required by the response schema. `selected_label` must be exactly one option label. `citations` must be an array of concise citation strings taken from the MCP response; return [] only when the successful MCP response has no usable citation.

Question: {task.question}
Options:
{option_lines}
"""


def build_codex_command(
    *,
    codex_bin: Path,
    schema_path: Path,
    isolated_workdir: Path,
    index_dir: Path,
    timeout_seconds: float,
    prompt: str,
) -> list[str]:
    """Build an isolated invocation with command-scoped MCP configuration only."""
    mcp_prefix = f"mcp_servers.{MCP_NAME}"
    tool_timeout = max(1, math.ceil(timeout_seconds))
    return [
        str(codex_bin),
        "exec",
        "--ephemeral",
        "--sandbox",
        "read-only",
        "--skip-git-repo-check",
        "--ignore-user-config",
        "--ignore-rules",
        "-c",
        'approval_policy="never"',
        "--json",
        "--output-schema",
        str(schema_path),
        "-C",
        str(isolated_workdir),
        "-c",
        f"{mcp_prefix}.command={_toml_string(str(DEFAULT_PYTHON_BIN))}",
        "-c",
        f"{mcp_prefix}.args={json.dumps([str(MCP_SERVER), '--index-dir', str(index_dir)])}",
        "-c",
        f"{mcp_prefix}.cwd={_toml_string(str(PROJECT_ROOT))}",
        "-c",
        f'{mcp_prefix}.env={{ RAG_RETRIEVAL_BACKEND = "auto", HF_HUB_DISABLE_SYMLINKS_WARNING = "1" }}',
        "-c",
        f"{mcp_prefix}.startup_timeout_sec={tool_timeout}",
        "-c",
        f"{mcp_prefix}.tool_timeout_sec={tool_timeout}",
        prompt,
    ]


def parse_json_events(stdout: str) -> list[dict[str, Any]]:
    """Extract JSONL events while tolerating non-JSON diagnostic lines on stdout."""
    events: list[dict[str, Any]] = []
    for raw_line in stdout.splitlines():
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    if not events:
        raise CodexHostError("Codex emitted no parseable JSON events.")
    return events


def _event_item(event: dict[str, Any]) -> dict[str, Any] | None:
    item = event.get("item")
    return item if isinstance(item, dict) else None


def successful_query_reports_call(events: Sequence[dict[str, Any]]) -> bool:
    for event in events:
        item = _event_item(event)
        if not item or item.get("type") != "mcp_tool_call":
            continue
        if item.get("server") != MCP_NAME or item.get("tool") != "query_reports":
            continue
        if event.get("type") == "item.completed" and item.get("status") == "completed" and not item.get("error"):
            return True
    return False


def _event_error_message(events: Sequence[dict[str, Any]]) -> str | None:
    messages: list[str] = []
    for event in events:
        if event.get("type") == "error" and event.get("message"):
            messages.append(str(event["message"]))
        turn_error = event.get("error")
        if isinstance(turn_error, dict) and turn_error.get("message"):
            messages.append(str(turn_error["message"]))
        item = _event_item(event)
        if item and isinstance(item.get("error"), dict) and item["error"].get("message"):
            messages.append(str(item["error"]["message"]))
    return messages[-1] if messages else None


def extract_final_message(events: Sequence[dict[str, Any]]) -> str:
    for event in reversed(events):
        item = _event_item(event)
        if not item or item.get("type") not in {"agent_message", "message"}:
            continue
        text = item.get("text")
        if isinstance(text, str) and text.strip():
            return text
    raise CodexHostError("Codex completed without an agent_message JSON event.")


def parse_model_response(text: str, task: HostTask) -> dict[str, Any]:
    try:
        response = json.loads(text.strip())
    except json.JSONDecodeError as exc:
        raise CodexHostError(f"Codex final message for {task.qid!r} was not JSON.") from exc
    if not isinstance(response, dict) or set(response) != {"selected_label", "citations"}:
        raise CodexHostError(f"Codex final message for {task.qid!r} violates the response schema.")
    selected_label = response.get("selected_label")
    citations = response.get("citations")
    if selected_label not in task.labels:
        raise CodexHostError(f"Codex selected an invalid label for {task.qid!r}: {selected_label!r}.")
    if not isinstance(citations, list) or not all(isinstance(item, str) for item in citations):
        raise CodexHostError(f"Codex returned invalid citations for {task.qid!r}.")
    return {"selected_label": selected_label, "citations": citations}


def _short_process_detail(stderr: str, events: Sequence[dict[str, Any]]) -> str:
    event_error = _event_error_message(events)
    if event_error:
        return event_error[:500]
    return stderr.strip()[:500] or "no diagnostic message"


def run_task(
    *, codex_bin: Path, index_dir: Path, timeout_seconds: float, task: HostTask
) -> dict[str, Any]:
    if not WORKSPACE_TEMP_DIR.is_dir():
        raise CodexHostError(f"Required workspace temporary directory does not exist: {WORKSPACE_TEMP_DIR}")
    if not codex_bin.is_file():
        raise CodexHostError(f"Codex executable does not exist: {codex_bin}")
    if not DEFAULT_PYTHON_BIN.is_file():
        raise CodexHostError(f"Required Anaconda Python does not exist: {DEFAULT_PYTHON_BIN}")
    if not MCP_SERVER.is_file():
        raise CodexHostError(f"MCP server does not exist: {MCP_SERVER}")
    if not index_dir.is_dir():
        raise CodexHostError(f"Index directory does not exist: {index_dir}")

    with tempfile.TemporaryDirectory(prefix="codex-host-mcq-", dir=WORKSPACE_TEMP_DIR) as temporary_directory:
        isolated_workdir = Path(temporary_directory)
        schema_path = isolated_workdir / "response.schema.json"
        schema_path.write_text(json.dumps(build_response_schema(task.labels), indent=2), encoding="utf-8")
        command = build_codex_command(
            codex_bin=codex_bin,
            schema_path=schema_path,
            isolated_workdir=isolated_workdir,
            index_dir=index_dir,
            timeout_seconds=timeout_seconds,
            prompt=build_prompt(task),
        )
        started = time.perf_counter()
        try:
            completed = subprocess.run(
                command,
                cwd=isolated_workdir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise CodexHostError(f"Codex timed out after {timeout_seconds:g}s for {task.qid!r}.") from exc
        latency_seconds = time.perf_counter() - started
        events = parse_json_events(completed.stdout)
        if completed.returncode != 0:
            detail = _short_process_detail(completed.stderr, events)
            raise CodexHostError(f"Codex exited {completed.returncode} for {task.qid!r}: {detail}")
        if not successful_query_reports_call(events):
            detail = _short_process_detail(completed.stderr, events)
            raise CodexHostError(f"No successful {MCP_NAME}.query_reports call for {task.qid!r}: {detail}")
        model_response = parse_model_response(extract_final_message(events), task)

    return {
        "qid": task.qid,
        "selected_label": model_response["selected_label"],
        "citations": model_response["citations"],
        "latency_seconds": round(latency_seconds, 6),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run public MCQs through an ephemeral Codex MCP host.")
    parser.add_argument("--tasks", type=Path, default=DEFAULT_TASKS, help="Gold-free public Codex host task JSONL.")
    parser.add_argument("--answers", type=Path, required=True, help="Scorer-compatible JSONL output path.")
    parser.add_argument("--index-dir", type=Path, default=DEFAULT_INDEX_DIR, help="Local RAG index supplied to MCP.")
    parser.add_argument("--codex-bin", type=Path, default=DEFAULT_CODEX_BIN, help="Codex executable path.")
    parser.add_argument("--timeout", type=float, default=180.0, help="Per-question process and MCP tool timeout in seconds.")
    parser.add_argument("--max-questions", type=int, help="Maximum number of unanswered tasks to run.")
    parser.add_argument("--resume", action="store_true", help="Append only qids absent from an existing valid answer log.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0:
        raise SystemExit("--timeout must be a finite value greater than zero.")
    if args.max_questions is not None and args.max_questions <= 0:
        raise SystemExit("--max-questions must be greater than zero.")
    if not args.answers.parent.is_dir():
        raise SystemExit(f"The --answers parent directory does not exist: {args.answers.parent}")
    if args.answers.exists() and not args.resume:
        raise SystemExit(f"Answer log already exists; use --resume to continue without overwriting: {args.answers}")

    tasks = load_tasks(args.tasks)
    completed = load_resume_answers(args.answers, tasks) if args.resume else {}
    pending = remaining_tasks(tasks, completed)
    if args.max_questions is not None:
        pending = pending[: args.max_questions]
    if not pending:
        print("No unanswered tasks selected.")
        return

    with args.answers.open("a", encoding="utf-8", newline="\n") as handle:
        for task in pending:
            answer = run_task(
                codex_bin=args.codex_bin,
                index_dir=args.index_dir,
                timeout_seconds=args.timeout,
                task=task,
            )
            _validate_answer_record(answer, {item.qid: item for item in tasks}, f"generated answer {task.qid!r}")
            handle.write(json.dumps(answer, ensure_ascii=False, separators=(",", ":")) + "\n")
            handle.flush()
            print(f"Completed {task.qid} in {answer['latency_seconds']:.3f}s")


if __name__ == "__main__":
    main()
