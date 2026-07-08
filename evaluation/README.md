# Radiotherapy Physics RAG Evaluation

This folder contains public evaluation assets for the radiotherapy physics RAG skill. Evaluation files are intentionally separate from runtime skill files.

## Source Policy

The benchmark does not copy ABR, RAPHEX, board-review, commercial, leaked, or private question-bank material. The current public benchmark is generated from the public source catalog metadata in `reports/starter_corpus_sources.json`.

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

- Total questions: 260.
- In-domain public-source topic questions: 245.
- Out-of-domain controls: 15.
- Source records represented in runtime: 49.

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
RAG_FORCE_HASH_EMBEDDINGS=1 RAG_FORCE_LEXICAL_RERANK=1 EMBEDDING_MODEL_NAME=hash-fallback python scripts/evaluate_strategies.py --questions evaluation/radiotherapy_skill_open_questions.json --index-dir index --strategies sparse hybrid auto routed --ignore-report-scope --output-json evaluation/strategy_eval_results.json --output-md evaluation/strategy_eval_results.md
```

Current results:

| Strategy | Document Recall@3 | Document Recall@5 | OOD TP | OOD FN |
| --- | ---: | ---: | ---: | ---: |
| sparse | 0.755 | 0.857 | 15 | 0 |
| hybrid hash+dense | 0.702 | 0.804 | 15 | 0 |
| auto | 0.755 | 0.857 | 15 | 0 |
| routed | 0.755 | 0.857 | 15 | 0 |

`Recall@3`, `Recall@5`, and `MRR` are 0.000 in the current report because the generated public benchmark does not contain expert gold chunk IDs or section labels. Use document recall and abstention metrics for this open-source benchmark. The hash dense index is a reproducible no-model artifact check, not a semantic dense model; `auto` and `routed` therefore prefer sparse retrieval unless a semantic dense index is available.

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
RAG_FORCE_HASH_EMBEDDINGS=1 RAG_FORCE_LEXICAL_RERANK=1 EMBEDDING_MODEL_NAME=hash-fallback python scripts/evaluate_agent_skill.py --questions evaluation/radiotherapy_skill_open_questions.json --index-dir index --retrieval-backend routed --output-json evaluation/agent_skill_eval_results.json --output-md evaluation/agent_skill_eval_results.md
```

Current results:

- Tool success rate: 0.942.
- Document Hit Rate@5: 0.857.
- Citation present rate: 1.000.
- OOD abstention success rate: 1.000.
- Unexpected in-scope error count: 0.

`Tool success rate` counts only `ok=true` tool responses, so correct OOD abstentions lower this aggregate rate because they are returned as structured `insufficient_evidence` errors. Use it together with `OOD abstention success rate` and `Unexpected in-scope error count`.

## Private Licensed Questions

If you personally have access to licensed ABR, RAPHEX, or other copyrighted question sets, keep them out of GitHub. Put them in this folder with a `.local.json` suffix, for example:

```text
evaluation/abr_raphex_private.local.json
```

Private `.local.json` files are ignored by `.gitignore`. When reporting results, summarize aggregate metrics and failing IDs without reproducing copyrighted question text.
