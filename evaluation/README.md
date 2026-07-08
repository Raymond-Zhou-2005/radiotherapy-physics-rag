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

- Total questions: 190.
- In-domain public-source topic questions: 175.
- Out-of-domain controls: 15.
- Source records represented in runtime: 35.

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
| sparse | 0.686 | 0.806 | 9 | 6 |
| hybrid hash+dense | 0.663 | 0.754 | 10 | 5 |
| auto | 0.663 | 0.754 | 10 | 5 |
| routed | 0.674 | 0.794 | 9 | 6 |

`Recall@3`, `Recall@5`, and `MRR` are 0.000 in the current report because the generated public benchmark does not contain expert gold chunk IDs or section labels. Use document recall and abstention metrics for this open-source benchmark.

## Navigator Evaluation

```bash
python scripts/evaluate_navigator.py --questions evaluation/radiotherapy_skill_open_questions.json --navigator-dir navigator --output-json evaluation/navigator_eval_results.json --output-md evaluation/navigator_eval_results.md
```

Current results:

- Topic Recall@1: 0.880.
- Topic Recall@2: 0.926.
- Topic Recall@3: 0.966.
- Candidate Document Recall@1: 0.211.
- Candidate Document Recall@3: 0.480.
- Candidate Document Recall@5: 0.709.

Interpretation: the navigator usually routes to the right broad topic but still needs better document ranking within topic branches.

## Agent Skill Evaluation

```bash
RAG_FORCE_HASH_EMBEDDINGS=1 RAG_FORCE_LEXICAL_RERANK=1 EMBEDDING_MODEL_NAME=hash-fallback python scripts/evaluate_agent_skill.py --questions evaluation/radiotherapy_skill_open_questions.json --index-dir index --retrieval-backend routed --output-json evaluation/agent_skill_eval_results.json --output-md evaluation/agent_skill_eval_results.md
```

Current results:

- Tool success rate: 0.947.
- Document Hit Rate@5: 0.800.
- Citation present rate: 0.994.
- OOD abstention success rate: 0.600.
- Unexpected in-scope error count: 1.

## Private Licensed Questions

If you personally have access to licensed ABR, RAPHEX, or other copyrighted question sets, keep them out of GitHub. Put them in this folder with a `.local.json` suffix, for example:

```text
evaluation/abr_raphex_private.local.json
```

Private `.local.json` files are ignored by `.gitignore`. When reporting results, summarize aggregate metrics and failing IDs without reproducing copyrighted question text.
