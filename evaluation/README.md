# Radiotherapy Physics RAG Evaluation

This folder contains public evaluation assets for the radiotherapy physics RAG skill. Evaluation files are intentionally separate from runtime skill files.

## Source Policy

The benchmark does not copy ABR, RAPHEX, board-review, commercial, leaked, or private question-bank material. The main public topic benchmark is generated from the public source catalog metadata in `reports/starter_corpus_sources.json`.

The external gold-answer seed stores short answer targets paraphrased from public answer-key pages/documents. It is intended for method stress testing, not redistribution of a full exam bank.

This means the benchmark is useful for open-source retrieval and skill-contract testing, but it is not an expert-adjudicated clinical correctness benchmark.

## Current Benchmark

Main file:

```text
evaluation/radiotherapy_skill_open_questions.json
```

Equivalent public file:

```text
evaluation/public_credible_questions.json
```

Current size:

- Total questions: 280.
- In-domain public-source topic questions: 245.
- Out-of-domain controls: 35, including 20 hard medical-boundary controls.
- Source records represented in runtime: 49.
- External gold-answer seed: 12 public short-answer target questions.
- Table-cell QA seed: 14 questions checking exact values from extracted table text previews.
- Realistic agent-task seed: 12 tasks checking skill contract behavior.

Each item stores:

- `qid`
- `question`
- `type`
- `report_id`
- `gold_section`
- `gold_chunk_ids`
- `expected_abstain`
- `source_basis`
- `source_urls`
- `source_note`
- `benchmark_profile`

## Generate

```bash
python scripts/generate_public_benchmark.py --runtime-only --output evaluation/public_credible_questions.json
```

## Retrieval Strategy Evaluation

```bash
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5 RERANKER_MODEL_NAME=BAAI/bge-reranker-base python scripts/evaluate_strategies.py --questions evaluation/radiotherapy_skill_open_questions.json --index-dir index --strategies sparse hybrid auto routed --ignore-report-scope --output-json evaluation/strategy_eval_results.json --output-md evaluation/strategy_eval_results.md
```

Current results:

| Strategy | Document Recall@3 | Document Recall@5 | OOD TP | OOD FN |
| --- | ---: | ---: | ---: | ---: |
| sparse | 0.869 | 0.918 | 35 | 0 |
| hybrid semantic + cross-encoder | 0.922 | 0.947 | 35 | 0 |
| auto | 0.922 | 0.947 | 35 | 0 |
| routed | 0.898 | 0.927 | 35 | 0 |

`Recall@3`, `Recall@5`, and `MRR` are 0.000 in the current report because the generated public benchmark does not contain expert gold chunk IDs or section labels. Use document recall and abstention metrics for this open-source benchmark. Semantic dense retrieval is available through `BAAI/bge-small-en-v1.5`; cross-encoder reranking uses `BAAI/bge-reranker-base` when available and falls back to lexical scoring when neural model loading fails.

## Formal Ablation

```bash
python scripts/evaluate_ablation.py --questions evaluation/radiotherapy_skill_open_questions.json --index-dir index --output-json evaluation/ablation_eval_results.json --output-md evaluation/ablation_eval_results.md
```

Current 280-question ablation:

| Variant | Dense | Cross-encoder | Report-aware | Routing | Document Recall@5 | OOD TP/FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BM25 + lexical, no report-aware | 0 | 0 | 0 | 0 | 0.918 | 35/0 |
| BM25 + lexical, report-aware | 0 | 0 | 1 | 0 | 0.861 | 35/0 |
| Hybrid + lexical, no report-aware | 1 | 0 | 0 | 0 | 0.955 | 34/1 |
| Hybrid + cross-encoder, no report-aware | 1 | 1 | 0 | 0 | 0.947 | 35/0 |
| Hybrid + cross-encoder, report-aware | 1 | 1 | 1 | 0 | 0.873 | 34/1 |
| Routed full | 1 | 1 | 1 | 1 | 0.898 | 34/1 |

Preferred default: `auto` retrieval with semantic hybrid candidates and cross-encoder reranking, with report-aware heuristics disabled. The hybrid+lexical condition has slightly higher Document Recall@5 but one OOD false negative, so it is not the safest default.

## Navigator Evaluation

```bash
python scripts/evaluate_navigator.py --questions evaluation/radiotherapy_skill_open_questions.json --navigator-dir navigator --output-json evaluation/navigator_eval_results.json --output-md evaluation/navigator_eval_results.md
```

Current results:

- Topic Recall@1: 0.837.
- Topic Recall@2: 0.939.
- Topic Recall@3: 0.967.
- Candidate Document Recall@1: 0.188.
- Candidate Document Recall@3: 0.490.
- Candidate Document Recall@5: 0.673.

Interpretation: the navigator usually routes to the right broad topic. Document ranking inside topic branches became harder after adding overlapping AAPM QA, IMRT, IGRT, SBRT, registration, and commissioning reports.

## Agent Skill Evaluation

```bash
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5 RERANKER_MODEL_NAME=BAAI/bge-reranker-base python scripts/evaluate_agent_skill.py --questions evaluation/radiotherapy_skill_open_questions.json --index-dir index --retrieval-backend auto --output-json evaluation/agent_skill_eval_results.json --output-md evaluation/agent_skill_eval_results.md
```

Current results:

- Tool success rate: 0.875.
- Document Hit Rate@5: 0.947.
- Citation present rate: 1.000.
- OOD abstention success rate: 1.000.
- Unexpected in-scope error count: 0.

`Tool success rate` counts only `ok=true` tool responses, so correct OOD abstentions lower this aggregate rate because they are returned as structured `insufficient_evidence` errors. Use it together with `OOD abstention success rate` and `Unexpected in-scope error count`.

## Asset QA Evaluation

```bash
python scripts/generate_asset_benchmark.py --assets-dir assets/extracted --sources reports/starter_corpus_sources.json --output evaluation/radiotherapy_asset_questions.json
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5 RERANKER_MODEL_NAME=BAAI/bge-reranker-base python scripts/evaluate_asset_qa.py --questions evaluation/radiotherapy_asset_questions.json --index-dir index --retrieval-backend auto --output-json evaluation/asset_qa_eval_results.json --output-md evaluation/asset_qa_eval_results.md
```

Current results on 120 metadata-derived table/figure questions:

- Skill OK rate: 1.000.
- Document Hit Rate@5: 1.000.
- Page Hit Rate@5: 0.983.
- Asset ID Trace Hit Rate@5: 0.950.
- Asset Type Trace Hit Rate@5: 0.975.

This is table/figure metadata proximity QA, not visual interpretation.

## Cell-Level Table QA

```bash
python scripts/generate_table_cell_benchmark.py --output evaluation/radiotherapy_table_cell_questions.json
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5 RERANKER_MODEL_NAME=BAAI/bge-reranker-base python scripts/evaluate_table_cell_qa.py --questions evaluation/radiotherapy_table_cell_questions.json --index-dir index --retrieval-backend auto --output-json evaluation/table_cell_qa_eval_results.json --output-md evaluation/table_cell_qa_eval_results.md
```

Current 14-question table-cell results:

- Skill OK rate: 1.000.
- Document Hit Rate@5: 1.000.
- Page Hit Rate@5: 0.929.
- Asset Trace Hit Rate@5: 0.929.
- Evidence Cell Value Hit Rate: 0.929.
- Answer Cell Value Hit Rate: 0.643.
- Cell QA Success Rate: 0.929.

This checks whether short values from extracted table text previews are recoverable. It is stricter than metadata proximity, but still not human visual QA.

## External Gold-Answer Seed

```bash
python scripts/generate_gold_answer_benchmark.py --output evaluation/radiotherapy_gold_answer_questions.json
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5 RERANKER_MODEL_NAME=BAAI/bge-reranker-base python scripts/evaluate_gold_answers.py --questions evaluation/radiotherapy_gold_answer_questions.json --index-dir index --retrieval-backend auto --output-json evaluation/gold_answer_eval_results.json --output-md evaluation/gold_answer_eval_results.md
```

Current 12-question results:

- Skill OK rate: 0.917.
- Citation present rate: 0.917.
- Answer value hit rate: 0.333.
- Evidence value hit rate: 0.583.
- Gold-answer success rate: 0.583.

Interpretation: the skill is stronger as an evidence-finding tool than as an extractive-only answer generator for public answer-key and calculation-style questions. This is a limitation to report, not hide.

## Realistic Agent Tasks

```bash
python scripts/generate_agent_task_benchmark.py --output evaluation/radiotherapy_agent_tasks.json
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5 RERANKER_MODEL_NAME=BAAI/bge-reranker-base python scripts/evaluate_agent_tasks.py --tasks evaluation/radiotherapy_agent_tasks.json --index-dir index --retrieval-backend auto --output-json evaluation/agent_task_eval_results.json --output-md evaluation/agent_task_eval_results.md
```

Current 12-task results:

- Task success rate: 1.000.
- Document Hit Rate@5: 1.000 on in-scope tasks.
- Citation success rate: 1.000.
- Bundle prompt success rate: 1.000.
- Asset trace success rate: 1.000.
- Hard medical-boundary OOD abstention success rate: 1.000.

## Answer Quality Proxy Evaluation

```bash
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5 RERANKER_MODEL_NAME=BAAI/bge-reranker-base python scripts/evaluate_answer_quality.py --questions evaluation/radiotherapy_skill_open_questions.json --index-dir index --retrieval-backend auto --output-json evaluation/answer_quality_eval_results.json --output-md evaluation/answer_quality_eval_results.md
```

Current automatic proxy results:

- In-scope OK rate: 1.000.
- Citation marker rate: 1.000.
- Used evidence ID valid rate: 1.000.
- Mean grounded token overlap: 0.993.
- Unsupported number case rate: 0.000.
- Overclaim flag rate: 0.020.
- OOD abstention success rate: 1.000.

These metrics check answer format and grounding proxies. They do not replace expert answer grading.

## Paper Experiment Matrix

```bash
python scripts/build_paper_experiment_matrix.py --eval-dir evaluation --output-json evaluation/paper_experiment_matrix.json --output-md evaluation/paper_experiment_matrix.md
```

The matrix consolidates retrieval ablations, agent contract metrics, asset/table-cell metrics, external gold-answer seed metrics, answer-quality proxies, and navigator metrics into one paper-facing table.

## Private Licensed Questions

If you personally have access to licensed ABR, RAPHEX, or other copyrighted question sets, keep them out of GitHub. Put them in this folder with a `.local.json` suffix, for example:

```text
evaluation/abr_raphex_private.local.json
```

Private `.local.json` files are ignored by `.gitignore`. When reporting results, summarize aggregate metrics and failing IDs without reproducing copyrighted question text.
