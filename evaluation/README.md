# Radiotherapy Physics RAG Evaluation

This folder contains public evaluation assets for the radiotherapy physics RAG skill. Evaluation files are intentionally separate from runtime skill files.

## Source Policy

The benchmark does not copy ABR, RAPHEX, board-review, commercial, leaked, or private question-bank material. The main public topic benchmark is generated from the public source catalog metadata in `reports/starter_corpus_sources.json`.

The public answer-target benchmark stores short answer targets paraphrased from public answer-key pages/documents and generated from public AAPM/IAEA report evidence. It is intended for method stress testing, not redistribution of a full exam bank.

This means the benchmark is useful for open-source retrieval and skill-contract testing, but it is not an expert-adjudicated clinical correctness benchmark.

Read [benchmark_governance.md](benchmark_governance.md) before interpreting any combined answer-target metric. It defines the external versus in-corpus profiles and the limits of each automated evaluation.

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
- Public answer-target benchmark: 61 questions, including 12 public external answer-key seeds and 49 open-report answer targets.
- Table-cell QA seed: 14 questions checking exact values from extracted table text previews.
- Direct skill-contract benchmark: 40 tasks checking the Python skill contract, including 10 hard medical-boundary OOD tasks.
- MCP stdio contract benchmark: 7 separate-process client/server tasks.
- External public medical-physics MCQ benchmark: 100 answer-keyed questions
  imported from a pinned Apache-2.0 source, kept outside the runtime corpus.
- Combined inventory: 622 test cases across these benchmark families. They are
  not a single independent clinical cohort and must not be pooled into one
  clinical accuracy claim.

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

The frozen `strategy_eval_results.*` files predate the OpenDataLoader rebuild and
are retained only for historical traceability. Use the current formal ablation
below for parser-refresh claims. `Recall@3`, `Recall@5`, and `MRR` at chunk
level are zero because the open benchmark has no expert gold chunk IDs after
the parser changed chunk boundaries. Use document recall and abstention metrics
for this public-source benchmark. Semantic dense retrieval is available through
`BAAI/bge-small-en-v1.5`; cross-encoder reranking uses
`BAAI/bge-reranker-base` when available and falls back to lexical scoring when
neural model loading fails.

## Formal Ablation

```bash
python scripts/evaluate_ablation.py --questions evaluation/radiotherapy_skill_open_questions.json --index-dir index --output-json evaluation/ablation_eval_results.json --output-md evaluation/ablation_eval_results.md
```

## Statistical Uncertainty

```bash
python scripts/evaluate_statistical_uncertainty.py --eval-dir evaluation --output-json evaluation/statistical_uncertainty.json --output-md evaluation/statistical_uncertainty.md
```

This post-processing step reads frozen per-question evaluation outputs. It reports Wilson 95% confidence intervals for binary rates, a deterministic bootstrap interval for mean grounded-token overlap, and a paired sparse-versus-hybrid comparison. These intervals quantify sampling variability within the fixed automatic benchmark; they are not clinical confidence intervals or evidence of expert agreement.

## Frozen-output Consistency Audit

```bash
python scripts/audit_evaluation_outputs.py --eval-dir evaluation --output-json evaluation/evaluation_output_audit.json --output-md evaluation/evaluation_output_audit.md
```

This audit recomputes headline rates and the statistical-uncertainty object from per-question details. It detects stale or internally inconsistent automatic-result files; it does not validate the benchmark labels or medical correctness.

Current 280-question ablation:

| Variant | Dense | Cross-encoder | Report-aware | Routing | Document Recall@5 | OOD TP/FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BM25 + lexical, no report-aware | 0 | 0 | 0 | 0 | 0.918 | 34/1 |
| BM25 + lexical, report-aware | 0 | 0 | 1 | 0 | 0.894 | 34/1 |
| Hybrid + lexical, no report-aware | 1 | 0 | 0 | 0 | 0.935 | 34/1 |
| Hybrid + cross-encoder, no report-aware | 1 | 1 | 0 | 0 | 0.959 | 34/1 |
| Hybrid + cross-encoder, report-aware | 1 | 1 | 1 | 0 | 0.910 | 35/0 |
| Routed full | 1 | 1 | 1 | 1 | 0.918 | 35/0 |

There is no single condition that dominates on both measurements. The
cross-encoder/no-report-aware condition has the highest document recall, while
the report-aware conditions reject every predefined OOD question. Select the
mode according to the deployment safety policy and report the tradeoff.

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

The frozen `agent_skill_eval_results.*` files predate the parser-refresh
runtime and are not a current OpenDataLoader headline result. The current
40-task direct skill-contract evaluation is reported below; it exercises the
same structured response contract and includes hard medical-boundary OOD tasks.

## Asset QA Evaluation

```bash
python scripts/generate_asset_benchmark.py --assets-dir assets/extracted --sources reports/starter_corpus_sources.json --output evaluation/radiotherapy_asset_questions.json
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5 RERANKER_MODEL_NAME=BAAI/bge-reranker-base python scripts/evaluate_asset_qa.py --questions evaluation/radiotherapy_asset_questions.json --index-dir index --retrieval-backend auto --output-json evaluation/asset_qa_eval_results.json --output-md evaluation/asset_qa_eval_results.md
```

Current results on 120 metadata-derived table/figure questions:

- Skill OK rate: 1.000.
- Document Hit Rate@5: 119/120 (0.992).
- Page Hit Rate@5: 114/120 (0.950).
- Asset ID Trace Hit Rate@5: 114/120 (0.950).
- Asset Type Trace Hit Rate@5: 114/120 (0.950).

This is table/figure metadata proximity QA, not visual interpretation.

## Cell-Level Table QA

```bash
python scripts/generate_table_cell_benchmark.py --output evaluation/radiotherapy_table_cell_questions.json
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5 RERANKER_MODEL_NAME=BAAI/bge-reranker-base python scripts/evaluate_table_cell_qa.py --questions evaluation/radiotherapy_table_cell_questions.json --index-dir index --retrieval-backend auto --output-json evaluation/table_cell_qa_eval_results.json --output-md evaluation/table_cell_qa_eval_results.md
```

Current 14-question table-cell results:

- Skill OK rate: 1.000.
- Document Hit Rate@5: 1.000.
- Page Hit Rate@5: 14/14 (1.000).
- Asset Trace Hit Rate@5: 14/14 (1.000).
- Evidence Cell Value Hit Rate: 14/14 (1.000).
- Answer Cell Value Hit Rate: 14/14 (1.000).
- Cell QA Success Rate: 14/14 (1.000).

This checks whether short values from extracted table text previews are recoverable. It is stricter than metadata proximity, but still not human visual QA.

## Public Answer-Target Benchmark

```bash
python scripts/generate_gold_answer_benchmark.py --output evaluation/radiotherapy_gold_answer_questions.json
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5 RERANKER_MODEL_NAME=BAAI/bge-reranker-base python scripts/evaluate_gold_answers.py --questions evaluation/radiotherapy_gold_answer_questions.json --index-dir index --retrieval-backend auto --output-json evaluation/gold_answer_eval_results.json --output-md evaluation/gold_answer_eval_results.md
```

Current 61-question results for the default semantic-coverage selector:

- Skill OK rate: 60/61 (0.984).
- Citation present rate: 60/61 (0.984).
- Answer value hit rate: 31/61 (0.508).
- Evidence value hit rate: 44/61 (0.721).
- Gold-answer success rate: 44/61 (0.721).

Profile-specific results:

| Profile | N | Evidence value hit | Answer value hit | Gold-answer success |
| --- | ---: | ---: | ---: | ---: |
| `external_gold_answer` | 12 | 0.417 | 0.333 | 0.417 |
| `open_report_gold_answer` | 49 | 0.796 | 0.551 | 0.796 |

Interpretation: the skill is stronger as an evidence-finding tool than as an extractive-only answer generator, although semantic sentence selection narrows the answer-surfacing gap. The 49-item open-report profile is an in-corpus check, while the 12-item external profile is a small non-expert stress test. Neither is expert clinical grading.

## Answer Generation Mode Comparison

```bash
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5 RERANKER_MODEL_NAME=BAAI/bge-reranker-base python scripts/evaluate_answer_generation.py --questions evaluation/radiotherapy_gold_answer_questions.json --index-dir index --retrieval-backend auto --output-json evaluation/answer_generation_eval_results.json --output-md evaluation/answer_generation_eval_results.md
```

Current 61-question results for the default semantic-coverage selector:

- Extractive answer value hit rate: 31/61 (0.508).
- Extractive evidence value hit rate: 49/61 (0.803).
- Evidence-only value hit rate: 49/61 (0.803).
- Bundle prompt value hit rate: 49/61 (0.803).
- Answer synthesis gap rate: 18/61 (0.295).
- Retrieval gap rate: 12/61 (0.197).

Interpretation: most remaining misses are answer-synthesis gaps rather than absence of relevant retrieved evidence.

## Extractive Sentence-Selector Ablation

```bash
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5 RERANKER_MODEL_NAME=BAAI/bge-reranker-base python scripts/evaluate_extractive_selectors.py --questions evaluation/radiotherapy_gold_answer_questions.json --index-dir index --retrieval-backend auto --output-json evaluation/extractive_selector_ablation.json --output-md evaluation/extractive_selector_ablation.md
```

The frozen selector-ablation files predate the OpenDataLoader rebuild and are
not used as a current parser-refresh claim. The current answer-target and
answer-generation outputs above use the default selector and are automatic
evidence/answer-value proxies, not expert correctness estimates.

## Direct Skill Contract Tasks

```bash
python scripts/generate_agent_task_benchmark.py --output evaluation/radiotherapy_agent_tasks.json
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5 RERANKER_MODEL_NAME=BAAI/bge-reranker-base python scripts/evaluate_agent_tasks.py --tasks evaluation/radiotherapy_agent_tasks.json --index-dir index --retrieval-backend auto --output-json evaluation/agent_task_eval_results.json --output-md evaluation/agent_task_eval_results.md
```

Current 40-task results:

- Task success rate: 1.000.
- In-scope structured `ok=true` rate: 30/30; the remaining 10 tasks are correct structured OOD refusals.
- Document Hit Rate@5: 1.000 on in-scope tasks.
- Citation success rate: 1.000.
- Bundle prompt success rate: 1.000.
- Asset trace success rate: 1.000.
- Hard medical-boundary OOD abstention success rate: 1.000.

This invokes the local Python skill contract directly. It does not verify MCP transport or autonomous agent planning.

## MCP Stdio Contract Integration

```bash
python scripts/evaluate_mcp_contract.py --index-dir index --output-json evaluation/mcp_contract_eval_results.json --output-md evaluation/mcp_contract_eval_results.md
```

Current 7-task separate-process MCP result:

- Required tools present: true.
- Task success rate: 1.000.
- In-scope task success rate: 1.000.
- OOD refusal success rate: 1.000.
- Transport errors: 0.

This starts the stdio server through an MCP client, lists tools, and invokes corpus, navigator, chunk, evidence, bundle, table-answer, and OOD calls. It does not assess a host agent's autonomous planning or skill selection.

## Failure Taxonomy

```bash
python scripts/analyze_failure_taxonomy.py --eval-dir evaluation --output-json evaluation/failure_taxonomy.json --output-md evaluation/failure_taxonomy.md
```

Current automatically classified failure/gap cases:

- Total cases: 41.
- Answer synthesis gap: 18.
- Retrieval gap: 9.
- Retrieval or evidence gap in gold-answer evaluation: 12.
- Page miss: 1.
- Skill error: 1.

These categories are engineering diagnostics for the paper discussion. They are not expert clinical correctness labels.

## Answer Quality Proxy Evaluation

```bash
EMBEDDING_MODEL_NAME=BAAI/bge-small-en-v1.5 RERANKER_MODEL_NAME=BAAI/bge-reranker-base python scripts/evaluate_answer_quality.py --questions evaluation/radiotherapy_skill_open_questions.json --index-dir index --retrieval-backend auto --output-json evaluation/answer_quality_eval_results.json --output-md evaluation/answer_quality_eval_results.md
```

Current automatic proxy results:

- In-scope OK rate: 1.000.
- Citation marker rate: 1.000.
- Used evidence ID valid rate: 1.000.
- Current semantic-coverage selector mean grounded token overlap: 0.960.
- Unsupported number case rate: 0.000.
- Overclaim flag rate: 0.000.

The 61 answer-target items do not contain OOD controls, so this evaluation does
not measure OOD abstention. OOD behavior is measured by the 280-question
retrieval ablation and the 40-task direct skill-contract benchmark.

These metrics check answer format and grounding proxies. Number and overclaim checks apply to the extractive summary, not verbatim supporting excerpts. They do not replace expert answer grading.

## Local Runtime Integrity Audit

```bash
python scripts/audit_runtime_integrity.py --root .
```

The audit is intentionally local-only. It verifies every runtime PDF SHA-256
against the corpus and provenance manifests, records index/model/dependency
fingerprints, and requires the frozen output audit to pass. It is not a new
accuracy result and does not validate labels, licensing, medical correctness,
or independent generalization.

## Paper Experiment Matrix

```bash
python scripts/build_paper_experiment_matrix.py --eval-dir evaluation --output-json evaluation/paper_experiment_matrix.json --output-md evaluation/paper_experiment_matrix.md
```

The matrix consolidates retrieval ablations, direct skill-contract metrics, MCP transport metrics, asset/table-cell metrics, profile-separated public answer-target metrics, answer-generation mode comparison, failure taxonomy, answer-quality proxies, and navigator metrics into one paper-facing table.

## External Public MCQ And Codex-Agent Evaluation

The Apache-2.0 100-question medical-physics MCQ source, answer-key-free host
tasks, host-answer scorer, and final output files are in
[`external/`](external/README.md). This is a separate question-answering
benchmark rather than a retrieval-only test.

Two comparisons must remain separate:

| Comparison | Accuracy | Mean latency | What it isolates |
| --- | ---: | ---: | --- |
| Historical PyMuPDF runtime + deterministic option selector | 34/100 | 14.932 s/question | Old parser/index under a fixed option selector |
| OpenDataLoader runtime + same deterministic option selector | 36/100 | 13.503 s/question | Parser/index change only |
| OpenDataLoader runtime + Codex agent using local skill evidence | 96/100 | 9.059 s/question | End-to-end agent use of skill evidence |

The third row changes the answer host as well as the parser/runtime. It is a
live Codex-agent result, but not a blinded study: the public benchmark is
available in the repository and the agent was instructed to use the local
skill before selecting an option. It is not a clinical or expert-validation
claim. The current Windows Codex CLI MCP probe was cancelled by host
authorization in non-interactive mode, so that result used direct local skill
calls rather than a fully non-interactive CLI-to-MCP transport path.

## Private Licensed Questions

If you personally have access to licensed ABR, RAPHEX, or other copyrighted question sets, keep them out of GitHub. Put them in this folder with a `.local.json` suffix, for example:

```text
evaluation/abr_raphex_private.local.json
```

Private `.local.json` files are ignored by `.gitignore`. When reporting results, summarize aggregate metrics and failing IDs without reproducing copyrighted question text.
