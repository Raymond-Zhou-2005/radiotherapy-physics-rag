# Radiotherapy Physics RAG Skill

`radiotherapy-physics-rag` is an open-source, local-first RAG skill for evidence-grounded radiotherapy physics report QA. It is designed for Codex-style agents, MCP clients, Python users, and maintainers who need a reproducible report-grounded evidence workflow rather than a general chatbot.

The project retrieves evidence from locally built AAPM/IAEA radiotherapy physics PDFs and returns structured citations with document title, section, page range, chunk ID, scores, and routing metadata.

## What This Is

- A Codex-usable skill under `skills/radiotherapy-physics-rag/`.
- A local MCP stdio server with tools for querying reports and fetching chunks.
- A reproducible PDF -> parse -> chunk -> BM25/semantic dense -> navigator pipeline.
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
- Indexed chunks: 10923.
- PDF asset metadata: 655 tables and 3263 images across 49 documents.
- ChatGPT Knowledge upload files generated locally: 49.
- Public answer-target benchmark: 61 questions, including public external answer-key seeds and open-report answer targets.
- Realistic agent-task benchmark: 40 tasks, including 10 hard medical-boundary OOD tasks.
- Navigator topics: 10.
- Semantic dense artifacts present: `BAAI/bge-small-en-v1.5` via `sentence-transformers`, 384 dimensions, FAISS inner-product index.
- Cross-encoder reranker: `BAAI/bge-reranker-base`, with lexical fallback when neural models are unavailable.
- No-model hash dense remains available as an explicit CI/debug fallback, but it is not treated as a semantic baseline.

The public GitHub repository intentionally excludes PDFs, parsed full text, chunks, indexes, extracted asset metadata, and generated ChatGPT upload files. Users rebuild them locally from permitted public sources.

## Install

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
python scripts/plugin_query.py --mode answer --answer-engine extractive --retrieval-backend sparse "What does the corpus say about treatment planning system commissioning?"
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
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5 RERANKER_MODEL_NAME=BAAI/bge-reranker-base python scripts/evaluate_answer_quality.py --questions evaluation/radiotherapy_skill_open_questions.json --index-dir index --retrieval-backend auto --output-json evaluation/answer_quality_eval_results.json --output-md evaluation/answer_quality_eval_results.md
python scripts/evaluate_ablation.py --questions evaluation/radiotherapy_skill_open_questions.json --index-dir index --output-json evaluation/ablation_eval_results.json --output-md evaluation/ablation_eval_results.md
python scripts/analyze_failure_taxonomy.py --eval-dir evaluation --output-json evaluation/failure_taxonomy.json --output-md evaluation/failure_taxonomy.md
python scripts/build_paper_experiment_matrix.py --eval-dir evaluation --output-json evaluation/paper_experiment_matrix.json --output-md evaluation/paper_experiment_matrix.md
```

Current 280-question open-source topic benchmark results:

| Evaluation | Main result |
| --- | --- |
| Sparse retrieval | Document Recall@5 = 0.918; OOD abstention = 1.000 |
| Hybrid semantic + cross-encoder retrieval | Document Recall@5 = 0.947; OOD abstention = 1.000 |
| Auto retrieval | Document Recall@5 = 0.947; OOD abstention = 1.000 |
| Routed retrieval | Document Recall@5 = 0.927; OOD abstention = 1.000 |
| Navigator routing | Topic Recall@3 = 0.967; Candidate Document Recall@5 = 0.673 |
| Auto agent skill contract | Document Hit Rate@5 = 0.947; Citation present rate = 1.000; OOD abstention success = 1.000 |
| Asset QA metadata | Document Hit@5 = 1.000; Page Hit@5 = 0.983; Asset ID Trace@5 = 0.950 |
| Cell-level table QA | Cell QA success = 0.929; evidence cell value hit = 0.929; answer cell value hit = 0.643 |
| Public answer-target benchmark | Gold-answer success = 0.787; evidence value hit = 0.787; answer value hit = 0.344 |
| Answer generation mode comparison | Evidence/bundle value hit = 0.852; extractive answer value hit = 0.344; answer synthesis gap = 0.508 |
| Realistic agent tasks | Task success = 1.000 across 40 tasks; hard medical-boundary OOD abstention = 1.000 |
| Failure taxonomy | 58 automatically classified failure/gap cases; most common category is answer synthesis gap |
| Extractive answer quality proxies | Citation marker = 1.000; valid evidence IDs = 1.000; grounded token overlap = 0.993; OOD abstention = 1.000 |

Interpretation: the project now has a real semantic dense index and a real cross-encoder reranker. Formal ablation showed that semantic hybrid retrieval with cross-encoder reranking and report-aware heuristics disabled is the preferred default for this public benchmark. Report-aware heuristics remain available as an ablation/experimental option, but they are not the default because they reduced document recall in the current matrix. The answer-target, answer-generation, failure-taxonomy, and answer-quality metrics are automatic research proxies, not expert adjudication.

## Public Release

Build a clean public directory:

```bash
python scripts/build_public_release.py --source-root . --output-dir D:\CodexWorkplace\radiotherapy-physics-rag-public --force
python scripts/audit_public_release.py --root D:\CodexWorkplace\radiotherapy-physics-rag-public
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
