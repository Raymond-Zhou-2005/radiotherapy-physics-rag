# Radiotherapy Physics RAG Skill

`radiotherapy-physics-rag` is an open-source, local-first RAG skill for evidence-grounded radiotherapy physics report QA. It is designed for Codex-style agents, MCP clients, Python users, and maintainers who need a reproducible report-grounded evidence workflow rather than a general chatbot.

The project retrieves evidence from locally built AAPM/IAEA radiotherapy physics PDFs and returns structured citations with document title, section, page range, chunk ID, scores, and routing metadata.

## What This Is

- A Codex-usable skill under `skills/radiotherapy-physics-rag/`.
- A local MCP stdio server with tools for querying reports and fetching chunks.
- A reproducible PDF -> OpenDataLoader parse -> chunk -> BM25/semantic dense -> navigator pipeline.
- A topic-tree navigator under `navigator/`.
- A scene-aware routed retrieval layer under `src/orchestration/`.
- A public open-source topic benchmark under `evaluation/`.

## What This Is Not

- Not a patient-specific clinical decision support system.
- Not medical advice.
- Not a redistribution package for third-party PDFs.
- Not an expert-adjudicated board-exam benchmark.

## Current Local Build

The current local runtime bundle used for validation contains:

- Source catalog records: 49.
- Downloaded/indexed runtime PDFs: 49.
- Manual source candidates not included in runtime: none in this local build.
- Indexed chunks: 8948.
- PDF asset metadata: 440 tables and 2140 images across 49 documents.
- ChatGPT Knowledge upload files generated locally: 49.
- Public answer-target benchmark: 61 questions, including public external answer-key seeds and open-report answer targets.
- External public MCQ benchmark: 100 Apache-2.0 medical-physics questions with source answer keys, kept outside runtime retrieval.
- Direct skill-contract benchmark: 40 tasks, including 10 hard medical-boundary OOD tasks.
- MCP stdio contract benchmark: 7 separate-process client/server tasks.
- Combined evaluation inventory: 622 test cases across topic retrieval/refusal,
  answer targets, asset/table questions, direct skill/MCP contracts, and the
  external MCQ set. These are separate benchmark families, not 622 independent
  clinical cases.
- Navigator topics: 10.
- Semantic dense artifacts present: `BAAI/bge-small-en-v1.5` via `sentence-transformers`, 384 dimensions, FAISS inner-product index.
- Cross-encoder reranker: `BAAI/bge-reranker-base`, with lexical fallback when neural models are unavailable.
- No-model hash dense remains available as an explicit CI/debug fallback, but it is not treated as a semantic baseline.

The public GitHub repository intentionally excludes PDFs, parsed full text, chunks, indexes, extracted asset metadata, and generated ChatGPT upload files. Users rebuild them locally from permitted public sources.

## Install

The PDF parser is OpenDataLoader PDF. It is a Python library backed by a local
Java process, so install Java 11 or newer before building or inspecting PDFs.
The parser adapter automatically adds a documented legacy Java sort compatibility
option for one older IAEA PDF that triggers an upstream OpenDataLoader 2.5.0
comparator failure; this does not restore or depend on PyMuPDF.

```bash
python -m pip install -r requirements.txt -c constraints.txt
python -m pip install -e ".[dev]" -c constraints.txt
```

## Build The Local Corpus

```bash
python scripts/download_starter_corpus.py --allow-manual-missing
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5 RERANKER_MODEL_NAME=BAAI/bge-reranker-base python scripts/prepare_index.py --reports-dir reports/raw --manifest reports/manifest.jsonl --parsed-dir parsed --chunks-dir chunks --index-dir index --index-backend both
python scripts/build_navigator.py --index-dir index --manifest reports/manifest.jsonl --output-dir navigator --skill-dir skills/radiotherapy-physics-navigator
python scripts/extract_pdf_assets.py reports/raw --output-dir assets/extracted
python scripts/build_provenance_manifest.py --output reports/provenance_manifest.json
python scripts/build_chatgpt_knowledge.py --root .
```

On Windows PowerShell:

```powershell
Remove-Item Env:RAG_FORCE_HASH_EMBEDDINGS -ErrorAction SilentlyContinue
$env:EMBEDDING_MODEL_NAME="BAAI/bge-small-en-v1.5"
$env:RERANKER_MODEL_NAME="BAAI/bge-reranker-base"
python scripts/prepare_index.py --reports-dir reports/raw --manifest reports/manifest.jsonl --parsed-dir parsed --chunks-dir chunks --index-dir index --index-backend both
```

For a fully local no-model hybrid baseline:

```bash
RAG_FORCE_HASH_EMBEDDINGS=1 EMBEDDING_MODEL_NAME=hash-fallback python scripts/prepare_index.py --reports-dir reports/raw --manifest reports/manifest.jsonl --parsed-dir parsed --chunks-dir chunks --index-dir index --index-backend both
```

On Windows PowerShell:

```powershell
$env:RAG_FORCE_HASH_EMBEDDINGS="1"
$env:RAG_FORCE_LEXICAL_RERANK="1"
$env:EMBEDDING_MODEL_NAME="hash-fallback"
python scripts/prepare_index.py --reports-dir reports/raw --manifest reports/manifest.jsonl --parsed-dir parsed --chunks-dir chunks --index-dir index --index-backend both
```

Some AAPM/Wiley sources are public or free-access but may block scripted downloads or point to publisher pages. If a source is reported as manual, download or browser-render it yourself if permitted and place it at the exact `reports/raw/*.pdf` path listed in `reports/starter_corpus_sources.json`. The current local build includes refreshed TG100 and TG158 runtime files; TG158 was browser-rendered from the Wiley free-access full-text page rather than copied from a raw publisher PDF endpoint.

## Query

Evidence mode:

```bash
python scripts/plugin_query.py --mode evidence --retrieval-backend routed "What accuracy and uncertainty issues matter for radiotherapy dose delivery?"
```

Extractive answer mode:

```bash
python scripts/plugin_query.py --mode answer --answer-engine extractive --extractive-selector auto --retrieval-backend sparse "What does the corpus say about treatment planning system commissioning?"
```

MCP server:

```bash
python scripts/mcp_server.py --index-dir index
```

Main MCP tools:

- `query_reports`
- `list_reports`
- `get_chunk`
- `list_navigator_topics`

## Evaluation

Generate the open-source benchmark:

```bash
python scripts/generate_public_benchmark.py --runtime-only --output evaluation/public_credible_questions.json
```

Run retrieval strategy evaluation:

```bash
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5 RERANKER_MODEL_NAME=BAAI/bge-reranker-base python scripts/evaluate_strategies.py --questions evaluation/radiotherapy_skill_open_questions.json --index-dir index --strategies sparse hybrid auto routed --ignore-report-scope --output-json evaluation/strategy_eval_results.json --output-md evaluation/strategy_eval_results.md
```

Run navigator evaluation:

```bash
python scripts/evaluate_navigator.py --questions evaluation/radiotherapy_skill_open_questions.json --navigator-dir navigator --output-json evaluation/navigator_eval_results.json --output-md evaluation/navigator_eval_results.md
```

Run end-to-end skill-contract evaluation:

```bash
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5 RERANKER_MODEL_NAME=BAAI/bge-reranker-base python scripts/evaluate_agent_skill.py --questions evaluation/radiotherapy_skill_open_questions.json --index-dir index --retrieval-backend auto --output-json evaluation/agent_skill_eval_results.json --output-md evaluation/agent_skill_eval_results.md
```

Run asset and answer-quality proxy evaluations:

```bash
python scripts/generate_asset_benchmark.py --assets-dir assets/extracted --sources reports/starter_corpus_sources.json --output evaluation/radiotherapy_asset_questions.json
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5 RERANKER_MODEL_NAME=BAAI/bge-reranker-base python scripts/evaluate_asset_qa.py --questions evaluation/radiotherapy_asset_questions.json --index-dir index --retrieval-backend auto --output-json evaluation/asset_qa_eval_results.json --output-md evaluation/asset_qa_eval_results.md
python scripts/generate_table_cell_benchmark.py --output evaluation/radiotherapy_table_cell_questions.json
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5 RERANKER_MODEL_NAME=BAAI/bge-reranker-base python scripts/evaluate_table_cell_qa.py --questions evaluation/radiotherapy_table_cell_questions.json --index-dir index --retrieval-backend auto --output-json evaluation/table_cell_qa_eval_results.json --output-md evaluation/table_cell_qa_eval_results.md
python scripts/generate_gold_answer_benchmark.py --output evaluation/radiotherapy_gold_answer_questions.json
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5 RERANKER_MODEL_NAME=BAAI/bge-reranker-base python scripts/evaluate_gold_answers.py --questions evaluation/radiotherapy_gold_answer_questions.json --index-dir index --retrieval-backend auto --output-json evaluation/gold_answer_eval_results.json --output-md evaluation/gold_answer_eval_results.md
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5 RERANKER_MODEL_NAME=BAAI/bge-reranker-base python scripts/evaluate_answer_generation.py --questions evaluation/radiotherapy_gold_answer_questions.json --index-dir index --retrieval-backend auto --output-json evaluation/answer_generation_eval_results.json --output-md evaluation/answer_generation_eval_results.md
python scripts/generate_agent_task_benchmark.py --output evaluation/radiotherapy_agent_tasks.json
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5 RERANKER_MODEL_NAME=BAAI/bge-reranker-base python scripts/evaluate_agent_tasks.py --tasks evaluation/radiotherapy_agent_tasks.json --index-dir index --retrieval-backend auto --output-json evaluation/agent_task_eval_results.json --output-md evaluation/agent_task_eval_results.md
python scripts/evaluate_mcp_contract.py --index-dir index --output-json evaluation/mcp_contract_eval_results.json --output-md evaluation/mcp_contract_eval_results.md
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5 RERANKER_MODEL_NAME=BAAI/bge-reranker-base python scripts/evaluate_answer_quality.py --questions evaluation/radiotherapy_skill_open_questions.json --index-dir index --retrieval-backend auto --output-json evaluation/answer_quality_eval_results.json --output-md evaluation/answer_quality_eval_results.md
python scripts/evaluate_ablation.py --questions evaluation/radiotherapy_skill_open_questions.json --index-dir index --output-json evaluation/ablation_eval_results.json --output-md evaluation/ablation_eval_results.md
python scripts/evaluate_public_mcq_exam.py --questions evaluation/external/public_medical_physics_100_mcq.json --index-dir index --retrieval-backend auto --output-json evaluation/public_mcq_eval_results.json --output-md evaluation/public_mcq_eval_results.md --export-host-tasks evaluation/external/public_mcq_codex_host_tasks.jsonl
python scripts/score_host_mcq_answers.py --tasks evaluation/external/public_mcq_codex_host_tasks.jsonl --answers evaluation/external/codex_agent_skill_answers.jsonl --gold evaluation/external/public_medical_physics_100_mcq.json --output-json evaluation/external/codex_agent_skill_score.json --output-md evaluation/external/codex_agent_skill_score.md
python scripts/compare_mcq_answer_methods.py --pymupdf evaluation/parser_comparison/pymupdf_baseline/public_mcq_eval_results.json --opendataloader evaluation/parser_comparison/opendataloader/public_mcq_eval_results.json --codex-score evaluation/external/codex_agent_skill_score.json --output-json evaluation/external/mcq_method_comparison.json --output-md evaluation/external/mcq_method_comparison.md
python scripts/analyze_failure_taxonomy.py --eval-dir evaluation --output-json evaluation/failure_taxonomy.json --output-md evaluation/failure_taxonomy.md
python scripts/build_paper_experiment_matrix.py --eval-dir evaluation --output-json evaluation/paper_experiment_matrix.json --output-md evaluation/paper_experiment_matrix.md
```

Current OpenDataLoader results:

| Evaluation | Main result |
| --- | --- |
| Formal retrieval ablation, best document recall | Hybrid semantic + cross-encoder, no report-aware rules: Document Recall@5 = 0.959; OOD abstention = 34/35 |
| Formal retrieval ablation, OOD-safe condition | Hybrid semantic + cross-encoder + report-aware rules: Document Recall@5 = 0.910; OOD abstention = 35/35 |
| Routed full retrieval | Document Recall@5 = 0.918; OOD abstention = 35/35 |
| Asset QA metadata | Document Hit@5 = 119/120; page and asset trace hit = 114/120 |
| Cell-level table QA | Cell QA success = 14/14; evidence and answer cell value hit = 14/14 |
| Public answer-target aggregate | Gold-answer success = 44/61; evidence value hit = 44/61; extractive answer value hit = 31/61 |
| External public answer-target profile | N = 12; evidence value hit = 5/12; extractive answer value hit = 4/12 |
| In-corpus open-report profile | N = 49; evidence value hit = 39/49; extractive answer value hit = 27/49 |
| Answer generation mode comparison | Evidence/bundle value hit = 49/61; extractive answer value hit = 31/61; answer synthesis gap = 18/61 |
| Direct skill contract tasks | Task success = 40/40; 30 in-scope structured successes and 10 correct hard medical-boundary refusals |
| MCP stdio contract integration | 7 separate-process MCP tasks passed; required tools present; no transport errors |
| Extractive answer quality proxies | 60/61 successful answers; mean grounded-token overlap = 0.956; unsupported-number and overclaim flags = 0 |
| Parser-only external MCQ comparison | PyMuPDF 34/100 vs OpenDataLoader 36/100 with the same deterministic option-evidence selector; mean latency 14.932 vs 13.503 s/question |
| Codex agent using local skill evidence | 96/100 public MCQs correct; 100/100 responses included citations; mean latency 9.059 s/question |

Interpretation: the project now has a real semantic dense index and a cross-encoder retrieval reranker. The formal ablation exposes a real tradeoff: the highest document recall condition missed one of 35 OOD controls, while the report-aware conditions rejected all 35 but retrieved the correct document less often. The 100-question parser comparison isolates the parser/index change only; the 96/100 Codex result additionally changes the answer host, so it is an end-to-end agent-use result rather than parser-only evidence. The 49 in-corpus answer targets are not an independent generalization test. All answer-target and answer-quality results are automatic research proxies, not expert adjudication or clinical validation.

Calculate confidence intervals from the frozen per-question outputs:

```bash
python scripts/evaluate_statistical_uncertainty.py --eval-dir evaluation
```

The resulting report uses Wilson 95% intervals for binary rates and deterministic bootstrap intervals for grounded-token overlap and paired retrieval differences. It describes uncertainty within the fixed automatic benchmark, not clinical validity or expert agreement.

Audit that frozen headline metrics and intervals still agree with their per-question outputs:

```bash
python scripts/audit_evaluation_outputs.py --eval-dir evaluation
```

Fingerprint the exact local PDFs, indexes, model-cache revisions, dependencies,
and frozen evaluation artifacts used by a runtime build:

```bash
python scripts/audit_runtime_integrity.py --root .
```

This audit is local-only and verifies runtime identity, not independent
generalization, publisher rights, expert agreement, or clinical correctness.

Prospective materials for the next external study are in
`evaluation/external_validation_protocol.md`,
`evaluation/expert_review_rubric_template.csv`, and
`evaluation/agent_host_evaluation_protocol.md`. They are protocols only and
do not represent completed expert review or host-agent evaluation.

## Public Release

### Source-Only Docker Build

The included Dockerfile validates the public source package while intentionally
excluding third-party PDFs and locally generated runtime artifacts:

```bash
docker build -t radiotherapy-physics-rag:source .
docker run --rm radiotherapy-physics-rag:source
```

See `CONTAINER.md` for the runtime-mounting and redistribution boundary. The
Docker CLI was not installed on the current maintainer machine, so this image
definition has not been locally built in this workspace.

Build a clean public directory:

```bash
python scripts/build_public_release.py --source-root . --output-dir D:\CodexWorkplace\RAG\radiotherapy-physics-rag-public --force
python scripts/audit_public_release.py --root D:\CodexWorkplace\RAG\radiotherapy-physics-rag-public
```

Forbidden public artifacts include:

- `reports/raw/*.pdf`
- `reports/manifest.jsonl`
- `parsed/*.jsonl`
- `chunks/*.jsonl`
- `index/**` runtime artifacts except `.gitkeep`
- `assets/extracted/**`
- `chatgpt_knowledge/upload_files/*.md`
- `chatgpt_knowledge/upload_manifest.json`

## Repository Layout

| Path | Purpose |
| --- | --- |
| `skills/` | Codex skill instructions |
| `.codex-plugin/`, `.mcp.json` | Codex plugin and MCP launch metadata |
| `scripts/` | Build, query, evaluation, and release commands |
| `src/` | PDF processing, chunking, retrieval, routing, generation helpers |
| `navigator/` | Topic tree and chunk pointers |
| `experience/` | Optional local routing memory placeholder |
| `reports/starter_corpus_sources.json` | Public source catalog |
| `evaluation/` | Public benchmark questions and evaluation outputs |
| `references/` | Focused implementation notes |
| `tests/` | Regression tests and public-boundary checks |

## Validation

```bash
pytest -q
python scripts/validate_skill_package.py --skill-root . --check-sample-baseline --require-index
python scripts/plugin_doctor.py --root .
```

## License

Project code is MIT licensed. Third-party reports, model packages, and Python dependencies remain under their own licenses and terms. This repository stores source metadata and build scripts; users must download and use source PDFs under the terms of the original publishers.
