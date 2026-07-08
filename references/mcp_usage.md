# MCP Usage

The Codex Plugin uses the local MCP server so Codex can query the report corpus without asking the user to run Python commands manually.

## Start The Local MCP Server

```bash
python scripts/mcp_server.py --index-dir index
```

Installed command:

```bash
radiotherapy-rag-mcp --index-dir index
```

The plugin manifest points to `.mcp.json`, which starts the same server for Codex-compatible environments.

## Tools

- `query_reports`: retrieve evidence, build an evidence bundle, or produce an extractive answer.
- `list_reports`: list local PDFs, chunks, and indexed report IDs after the corpus is built.

`query_reports` accepts:

- `query`: user question.
- `mode`: `evidence`, `bundle`, or `answer`.
- `report_id`: optional document scope.
- `evidence_top_k`: optional final evidence count.
- `answer_engine`: `auto`, `extractive`, or `medgemma`.
- `retrieval_backend`: `auto`, `hybrid`, or `sparse`.

Use `retrieval_backend="sparse"` for the most portable no-model path. Use `auto` when local dense retrieval models are installed or cached.

## Evidence Boundary

The MCP tool returns the same structured evidence contract as `scripts/run_skill.py`. Answers should cite returned evidence only and should abstain when the indexed corpus is insufficient.
