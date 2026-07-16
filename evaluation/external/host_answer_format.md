# Codex/MCP Host MCQ Answer Log

Run a real Codex or MCP host only against
`public_mcq_codex_host_tasks.jsonl`. Do not provide the host with
`public_medical_physics_100_mcq.json`, because that file contains the answer
key used solely by the scorer.

The host writes one JSON object per line, with exactly these fields:

```json
{"qid":"public_mcq_001","selected_label":"C","citations":[{"doc_id":"iaea_hhs31_accuracy_requirements_dosimetry","page":12}],"latency_seconds":2.84}
```

`citations` is optional. When present, it must be a JSON array of citation
strings or JSON objects. An empty array counts as no citation. The scorer does
not judge citation correctness; it reports the fraction of answers with at
least one supplied citation. `latency_seconds` is required and must be a finite
non-negative number measured by the host for that task.

The answer log must contain each task `qid` exactly once. `selected_label` is
case-sensitive and must match one of the labels in that task's `options` array.
Extra fields are rejected, so redact prompts, tool logs, answer text, and any
private data before creating this file.

## Scoring

The scorer only validates and scores files. It does not call a model, MCP
server, web service, or local RAG index.

```powershell
python scripts/score_host_mcq_answers.py `
  --questions evaluation/external/public_medical_physics_100_mcq.json `
  --host-tasks evaluation/external/public_mcq_codex_host_tasks.jsonl `
  --answers D:\path\to\host_answers.jsonl `
  --output-json D:\path\to\host_mcq_score.json `
  --output-md D:\path\to\host_mcq_score.md
```

By default, the scorer requires exactly 100 benchmark questions. It validates:

- unique and complete qids in the benchmark, task file, and answer log;
- exact question/option agreement between the task JSONL and the benchmark;
- no task fields that contain `gold`, and no fields outside the fixed host-task
  schema;
- a valid option label and non-negative finite latency for every answer.

The JSON and Markdown reports include accuracy, citation rate, latency summary,
input SHA-256 values, and per-question selected label/citation/latency details.
They do not include answer-key labels. The score should be reported as a public
external MCQ benchmark result, not expert medical-physics grading or clinical
validation.
