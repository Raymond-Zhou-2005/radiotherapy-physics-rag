# Codex Host MCQ Runner

`scripts/run_codex_host_mcq.py` dispatches the public, gold-free MCQ task export to a real `codex exec` host. It starts the project's `scripts/mcp_server.py` with `D:\APP\Anaconda\python.exe`, supplies the local `index` directory, and records only the scorer-required JSONL fields:

```json
{"qid":"public_mcq_001","selected_label":"C","citations":["[E2] IAEA ..."],"latency_seconds":42.18}
```

## Run

Start with exactly one task. The output path's parent must already exist.

```powershell
& D:\APP\Anaconda\python.exe scripts\run_codex_host_mcq.py `
  --max-questions 1 `
  --answers evaluation\external\codex_host_answers.jsonl `
  --timeout 180
```

Continue an interrupted run without overwriting validated records:

```powershell
& D:\APP\Anaconda\python.exe scripts\run_codex_host_mcq.py `
  --resume `
  --answers evaluation\external\codex_host_answers.jsonl `
  --timeout 180
```

Useful overrides are `--tasks`, `--index-dir`, and `--codex-bin`. `--max-questions` limits *new* unanswered tasks when used with `--resume`.

Score the completed file only with the separate scorer and answer-key input:

```powershell
& D:\APP\Anaconda\python.exe scripts\score_host_mcq_answers.py `
  --questions evaluation\external\public_medical_physics_100_mcq.json `
  --host-tasks evaluation\external\public_mcq_codex_host_tasks.jsonl `
  --answers evaluation\external\codex_host_answers.jsonl `
  --output-json evaluation\external\codex_host_score.json `
  --output-md evaluation\external\codex_host_score.md
```

## Execution Contract

- Every task runs `codex exec --ephemeral --sandbox read-only --json --output-schema` with an isolated temporary working directory under `D:\CodexWorkplace\Temp`.
- The runner uses `-c mcp_servers...` flags for a one-command MCP registration. It never calls `codex mcp add` and never changes `~/.codex/config.toml`.
- The model receives only `qid`-free question text and options from the host-task JSONL. The gold-bearing `public_medical_physics_100_mcq.json` is never opened by the runner and must never be supplied to the host.
- The model's final response is constrained to `selected_label` and citation strings by a per-task strict JSON Schema. The runner adds `qid` and measured `latency_seconds`, then validates the exact scorer answer schema before appending JSONL.
- A row is written only after Codex emits a successful MCP `query_reports` event. A model answer following a failed or cancelled tool call is rejected rather than logged as an evidence-grounded result.
- A failed task leaves prior completed rows intact. Fix the underlying issue and use `--resume`; do not hand-edit or duplicate rows.

## Public Development-Set Boundary

This is a source-pinned public MCQ development evaluation, not an independent hidden test set, expert medical-physics examination, clinical validation, or evidence of clinical performance. Keep task text, options, prior outputs, and observed errors out of prompt tuning, model selection, retriever tuning, and manual answer editing for any result claimed on this set. Any such iteration contaminates subsequent measurements and must be disclosed as development-set reuse.

Do not give the host the source answer-key file, merged score reports, prior completed answer logs, or any derived artifact that exposes labels. Use the tasks JSONL for host execution and reserve the answer-key JSON for the offline scorer after the run is complete.

## Cost And Operations

Each unanswered qid is one independent Codex model call plus one local MCP server startup and retrieval. Cost therefore scales approximately linearly with new questions and can include substantial input-token, reasoning-token, and local retrieval latency. `--max-questions 1` is the required operational check before any batch, and `--resume` avoids paying to repeat completed qids. `--timeout` bounds wall time per qid but not model-token cost.

The current Codex CLI can emit a cancelled `query_reports` event even when the standalone MCP client/server contract succeeds. The runner intentionally stops at that qid instead of writing an unsupported answer. Preserve the event log externally when diagnosing that host-side condition; do not replace it with a non-MCP answer.

## Tests

```powershell
& D:\APP\Anaconda\python.exe -m pytest tests\test_codex_host_runner.py -q
```
