# Radiotherapy Physics RAG Skill Project Brief

## Goal

Build an open-source, Codex-usable radiotherapy physics RAG skill that can be released publicly and later used as the software artifact for a paper. The article itself is intentionally out of scope for this delivery.

## Current Status

The implementation is now a local runtime bundle plus clean public-release package.

- Source catalog: 49 public AAPM/IAEA records.
- Local runtime: 49 downloaded or locally rendered PDFs.
- Manual source candidates not in runtime: none in this local build.
- Indexed chunks: 8948 after the OpenDataLoader rebuild.
- Extracted PDF asset metadata: 440 tables and 2140 images.
- ChatGPT Knowledge local export: 49 Markdown files.
- Benchmark: 280 open-source topic questions, including 35 OOD controls with 20 hard medical-boundary negatives.
- Asset benchmark: 120 metadata-derived table/figure questions.
- Table-cell benchmark: 14 exact-value questions from extracted public PDF table text previews.
- Public answer-target benchmark: 61 questions, including 12 paraphrased public answer-key seeds and 49 open-report answer targets.
- External public MCQ benchmark: 100 Apache-2.0 answer-keyed medical-physics questions, outside runtime retrieval.
- Combined evaluation inventory: 622 cases across separate retrieval, answer, asset, contract, and MCQ benchmark families; this is not a pooled clinical cohort.
- Agent-task benchmark: 40 realistic downstream skill-use tasks, including 10 hard medical-boundary OOD tasks.
- Answer-generation mode comparison plus a same-evidence lexical-versus-semantic sentence-selector ablation.
- Failure taxonomy: automatic classification of benchmark failure/gap cases for paper discussion.
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
13. Evaluates retrieval, formal ablations, navigator routing, direct skill-contract behavior, MCP stdio transport, table/figure asset metadata, cell-level table values, profile-separated public answer targets, answer-generation gaps, failure taxonomy, and answer-quality proxies.
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

Current OpenDataLoader formal ablation:

- BM25 + lexical, no report-aware rules: Document Recall@5 = 0.918; OOD abstention = 34/35.
- Hybrid + lexical, no report-aware rules: Document Recall@5 = 0.935; OOD abstention = 34/35.
- Hybrid + cross-encoder, no report-aware rules: Document Recall@5 = 0.959; OOD abstention = 34/35.
- Hybrid + cross-encoder + report-aware rules: Document Recall@5 = 0.910; OOD abstention = 35/35.
- Routed full: Document Recall@5 = 0.918; OOD abstention = 35/35.

This is a safety/recall tradeoff rather than a single winner. Earlier strategy,
navigator, and 280-question agent-skill result files predate the parser rebuild
and are retained only as historical outputs, not current ODL headline claims.

Asset QA results:

- Document Hit Rate@5: 119/120 (0.992).
- Page Hit Rate@5: 114/120 (0.950).
- Asset ID Trace Hit Rate@5: 114/120 (0.950).

Cell-level table QA results:

- Cell QA success rate: 14/14 (1.000).
- Evidence cell value hit rate: 14/14 (1.000).
- Answer cell value hit rate: 14/14 (1.000).

Public answer-target benchmark results:

- Gold-answer success rate: 44/61 (0.721).
- Evidence value hit rate: 44/61 (0.721).
- Current extractive answer value hit rate: 31/61 (0.508).
- External public-answer-key profile: N = 12, evidence value hit = 5/12, answer value hit = 4/12.
- In-corpus open-report profile: N = 49, evidence value hit = 39/49, answer value hit = 27/49.

Answer-generation mode comparison:

- Current extractive answer value hit rate: 31/61 (0.508).
- Evidence-only value hit rate: 49/61 (0.803).
- Bundle prompt value hit rate: 49/61 (0.803).
- Answer synthesis gap rate: 0.295.
- Retrieval gap rate: 12/61 (0.197).

Direct skill-contract task results:

- Task success rate: 1.000.
- In-scope Document Hit Rate@5: 1.000 across 30 tasks.
- Hard medical-boundary OOD abstention success rate: 1.000.

MCP stdio contract results:

- Seven separate-process MCP tasks passed.
- Required MCP tools were present and transport errors were 0.
- This validates protocol transport and tool contracts, not autonomous host-agent planning.

Failure taxonomy:

- The frozen taxonomy is a historical diagnostic and must be regenerated before it is used as an ODL result.

Answer quality proxy results:

- Citation marker rate: 1.000.
- Used evidence ID valid rate: 1.000.
- Mean grounded token overlap: 0.956 on 60 successful ODL answers.
- Unsupported number case rate: 0.000.
- Overclaim flag rate: 0.000.
- OOD abstention is not measured by this 61-item answer-target proxy; use the formal ablation and direct skill-contract tasks instead.

External public MCQ results: keeping the deterministic option selector fixed,
the historical PyMuPDF runtime answered 34/100 and the OpenDataLoader runtime
answered 36/100 (mean latency 14.932 versus 13.503 s/question). A recorded
Codex agent instructed to use the local skill answered 96/100 with citations on
all 100 responses (mean 9.059 s/question). The latter changes the answer host
as well as the parser/runtime and is not blinded, expert-adjudicated, or a
clinical claim.

Interpretation: the package is a reproducible open-source RAG skill and
benchmark prototype. It uses a real semantic embedding index and a real
cross-encoder reranker. The 49 in-corpus answer targets must not be reported as
independent generalization; the 12 external short-answer items remain small;
and the public MCQ result is development data. The project still lacks expert
answer adjudication.

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
python scripts/evaluate_answer_generation.py --questions evaluation/radiotherapy_gold_answer_questions.json --index-dir index --retrieval-backend auto
python scripts/evaluate_agent_tasks.py --tasks evaluation/radiotherapy_agent_tasks.json --index-dir index --retrieval-backend auto
python scripts/analyze_failure_taxonomy.py --eval-dir evaluation
python scripts/build_paper_experiment_matrix.py --eval-dir evaluation
```

Build public release:

```bash
python scripts/build_public_release.py --source-root . --output-dir D:\CodexWorkplace\RAG\radiotherapy-physics-rag-public --force
python scripts/audit_public_release.py --root D:\CodexWorkplace\RAG\radiotherapy-physics-rag-public
```

## Risks And Limitations

- AAPM public/free-access report pages can block scripted downloads; some sources require local browser rendering or manual download.
- PDF section extraction is imperfect.
- The benchmark is public-source generated and not expert-adjudicated.
- Cross-encoder evaluation is slower than lexical reranking and needs local Hugging Face model cache or network access.
- Report-aware heuristics remain experimental because formal ablation showed lower recall on the current benchmark.
- OOD abstention is still heuristic beyond the explicit public negative controls.
- Table/figure support includes metadata proximity and extracted table text previews, not full multimodal visual QA.
- Public answer-target performance shows that evidence retrieval remains stronger than extractive answer synthesis, although same-evidence cross-encoder sentence selection improved automatic answer-value hit by +0.164 on the fixed benchmark.

## Next Research Steps

These are article-preparation or article-upgrade steps after the current software release:

1. Add expert-reviewed answer keys if a medical physicist becomes available.
2. Add a stronger answer generator and compare extractive, local LLM, and hosted LLM answer modes under the same evidence contract.
3. Improve answer generation for calculation-style and public-answer-key questions while preserving evidence grounding.
4. Improve navigator document ranking.
5. Add multimodal figure QA if licensing and expert review become available.
6. Write the manuscript around safe claims supported by the current evaluation.
