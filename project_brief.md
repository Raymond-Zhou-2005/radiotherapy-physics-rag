# Radiotherapy Physics RAG Skill Project Brief

## Goal

Build an open-source, Codex-usable radiotherapy physics RAG skill that can be released publicly and later used as the software artifact for a paper. The article itself is intentionally out of scope for this delivery.

## Current Status

The implementation is now a local runtime bundle plus clean public-release package.

- Source catalog: 49 public AAPM/IAEA records.
- Local runtime: 49 downloaded or locally rendered PDFs.
- Manual source candidates not in runtime: none in this local build.
- Indexed chunks: 10923.
- Extracted PDF asset metadata: 655 tables and 3263 images.
- ChatGPT Knowledge local export: 49 Markdown files.
- Benchmark: 280 open-source topic questions, including 35 OOD controls with 20 hard medical-boundary negatives.
- Asset benchmark: 120 metadata-derived table/figure questions.
- Table-cell benchmark: 14 exact-value questions from extracted public PDF table text previews.
- External gold-answer seed: 12 paraphrased public answer-key questions with short answer targets.
- Agent-task benchmark: 12 realistic downstream skill-use tasks.
- Interfaces: Python CLI, Codex skill, MCP server, navigator skill, ChatGPT Knowledge export.
- Public packaging: `scripts/build_public_release.py` and `scripts/audit_public_release.py`.

## What The System Does

1. Stores public source metadata for radiotherapy physics reports.
2. Downloads direct public PDFs where scripted download is possible.
3. Accepts manual PDFs for sources whose official pages block automated download.
4. Parses PDFs into structured text blocks.
5. Builds section-aware chunks.
6. Builds sparse BM25 and semantic dense indexes with an explicit hash fallback for CI/debugging.
7. Applies cross-encoder reranking through `BAAI/bge-reranker-base` when available, with lexical fallback.
8. Builds a topic-tree navigator.
9. Performs sparse, hybrid, auto, or routed evidence retrieval.
10. Returns structured evidence and citations.
11. Exposes MCP tools for Codex and other local agents.
12. Generates public open-source benchmarks.
13. Evaluates retrieval, formal ablations, navigator routing, agent-facing skill behavior, table/figure asset metadata, cell-level table values, external gold-answer seeds, and answer-quality proxies.
14. Builds a clean GitHub release directory without PDFs or derived full text.

## What The System Does Not Do

- It does not provide patient-specific medical advice.
- It is not a clinical decision support system.
- It does not redistribute third-party PDFs.
- It does not include expert-adjudicated medical physics answers.
- It does not claim clinical validation.
- It does not use copyrighted ABR/RAPHEX/commercial exam questions.

## Current Evaluation

Benchmark: `evaluation/radiotherapy_skill_open_questions.json`

- 280 questions total.
- 245 in-domain public-source topic questions.
- 35 out-of-domain controls, including medical-adjacent hard negatives.
- Questions are generated from public source catalog metadata.

Strategy results:

- Sparse Document Recall@5: 0.918.
- Hybrid semantic + cross-encoder Document Recall@5: 0.947.
- Auto Document Recall@5: 0.947.
- Routed Document Recall@5: 0.927.
- OOD abstention success: 1.000 for all evaluated strategies.

Formal ablation result:

- Best safe default: semantic hybrid + BM25 candidates with cross-encoder reranking, report-aware heuristics disabled.
- Hybrid + lexical without report-aware heuristics reached Document Recall@5 0.955 but had one OOD false negative, so it is kept as an ablation condition rather than the default.

Navigator results:

- Topic Recall@3: 0.967.
- Candidate Document Recall@5: 0.673.

Agent skill results:

- Tool success rate: 0.875.
- Document Hit Rate@5: 0.947.
- Citation present rate: 1.000.
- OOD abstention success rate: 1.000.

Asset QA results:

- Document Hit Rate@5: 1.000.
- Page Hit Rate@5: 0.983.
- Asset ID Trace Hit Rate@5: 0.950.

Cell-level table QA results:

- Cell QA success rate: 0.929.
- Evidence cell value hit rate: 0.929.
- Answer cell value hit rate: 0.643.

External gold-answer seed results:

- Gold-answer success rate: 0.583.
- Evidence value hit rate: 0.583.
- Answer value hit rate: 0.333.

Realistic agent-task results:

- Task success rate: 1.000.
- Hard medical-boundary OOD abstention success rate: 1.000.

Answer quality proxy results:

- Citation marker rate: 1.000.
- Used evidence ID valid rate: 1.000.
- Mean grounded token overlap: 0.993.
- Unsupported number case rate: 0.000.
- Overclaim flag rate: 0.020.
- OOD abstention success rate: 1.000.

Interpretation: the package is now credible as an open-source RAG skill and reproducible benchmark prototype. It uses a real semantic embedding index and a real cross-encoder reranker. The safest default is `auto` retrieval, which uses semantic hybrid retrieval when the dense index is semantic and falls back to sparse retrieval when neural artifacts are absent. Topic-to-document ranking inside the navigator and answer generation for calculation-style gold questions remain the weakest measured areas. The project still lacks expert answer adjudication.

## Public Repository Boundary

Committed:

- source metadata
- code and scripts
- tests
- skill files
- navigator metadata and chunk pointers
- benchmark questions and evaluation summaries
- documentation

Excluded:

- `reports/raw/*.pdf`
- `reports/manifest.jsonl`
- `parsed/*.jsonl`
- `chunks/*.jsonl`
- `index/**` runtime artifacts except `.gitkeep`
- `assets/extracted/**`
- `chatgpt_knowledge/upload_files/*.md`
- `chatgpt_knowledge/upload_manifest.json`
- `experience/experience_memory.jsonl`

## Key Commands

Build local runtime:

```bash
python scripts/download_starter_corpus.py --allow-manual-missing
python scripts/prepare_index.py --reports-dir reports/raw --manifest reports/manifest.jsonl --parsed-dir parsed --chunks-dir chunks --index-dir index --index-backend both
python scripts/build_navigator.py --index-dir index --manifest reports/manifest.jsonl --output-dir navigator --skill-dir skills/radiotherapy-physics-navigator
python scripts/extract_pdf_assets.py reports/raw --output-dir assets/extracted
python scripts/build_chatgpt_knowledge.py --root .
```

Run evaluations:

```bash
python scripts/generate_public_benchmark.py --runtime-only --output evaluation/public_credible_questions.json
python scripts/evaluate_strategies.py --questions evaluation/radiotherapy_skill_open_questions.json --index-dir index --strategies sparse hybrid auto routed --ignore-report-scope
python scripts/evaluate_navigator.py --questions evaluation/radiotherapy_skill_open_questions.json --navigator-dir navigator
python scripts/evaluate_agent_skill.py --questions evaluation/radiotherapy_skill_open_questions.json --index-dir index --retrieval-backend auto
python scripts/evaluate_ablation.py --questions evaluation/radiotherapy_skill_open_questions.json --index-dir index
python scripts/evaluate_table_cell_qa.py --questions evaluation/radiotherapy_table_cell_questions.json --index-dir index --retrieval-backend auto
python scripts/evaluate_gold_answers.py --questions evaluation/radiotherapy_gold_answer_questions.json --index-dir index --retrieval-backend auto
python scripts/evaluate_agent_tasks.py --tasks evaluation/radiotherapy_agent_tasks.json --index-dir index --retrieval-backend auto
python scripts/build_paper_experiment_matrix.py --eval-dir evaluation
```

Build public release:

```bash
python scripts/build_public_release.py --source-root . --output-dir D:\CodexWorkplace\radiotherapy-physics-rag-public --force
python scripts/audit_public_release.py --root D:\CodexWorkplace\radiotherapy-physics-rag-public
```

## Risks And Limitations

- AAPM public/free-access report pages can block scripted downloads; some sources require local browser rendering or manual download.
- PDF section extraction is imperfect.
- The benchmark is public-source generated and not expert-adjudicated.
- Cross-encoder evaluation is slower than lexical reranking and needs local Hugging Face model cache or network access.
- Report-aware heuristics remain experimental because formal ablation showed lower recall on the current benchmark.
- OOD abstention is still heuristic beyond the explicit public negative controls.
- Table/figure support includes metadata proximity and extracted table text previews, not full multimodal visual QA.
- External gold-answer seed performance is limited because the current answer mode is conservative and extractive-only.

## Next Research Steps

These are article-preparation steps, not required for the current software release:

1. Add expert-reviewed answer keys if a medical physicist becomes available.
2. Add a stronger answer generator and compare extractive, local LLM, and hosted LLM answer modes under the same evidence contract.
3. Improve answer generation for calculation-style and public-answer-key questions while preserving evidence grounding.
4. Calibrate OOD abstention on broader negative controls and report confidence thresholds.
5. Improve navigator document ranking.
6. Add multimodal figure QA if licensing and expert review become available.
7. Write the manuscript around safe claims supported by the current evaluation.
