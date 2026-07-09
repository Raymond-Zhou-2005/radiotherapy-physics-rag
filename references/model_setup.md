# Model Setup Notes

## Default Neural Retrieval Profile

- Embedding model: `BAAI/bge-small-en-v1.5`
- Query prefix: `Represent this sentence for searching relevant passages: `
- Passage prefix: none
- Reranker model: `BAAI/bge-reranker-base`
- Recommended reranker max length: 512
- Current local dense index: `sentence_transformers` backend, 384 dimensions, FAISS inner-product search.

This profile requires `sentence-transformers`, `transformers`, `torch`, and local model cache access. `RAG_FORCE_LEXICAL_RERANK=1` can be used to keep reranking deterministic while still using real semantic embeddings.

Default retrieval uses `auto`: semantic dense + BM25 hybrid retrieval when a semantic dense index is present, with cross-encoder reranking when the reranker can be loaded. If neural components are absent, the skill falls back to lexical reranking instead of failing ordinary queries.

## No-model Reproducible Profile

For open-source CI, local smoke tests, and machines without Hugging Face model cache, use hash embeddings plus lexical reranking:

```powershell
$env:RAG_FORCE_HASH_EMBEDDINGS="1"
$env:RAG_FORCE_LEXICAL_RERANK="1"
$env:EMBEDDING_MODEL_NAME="hash-fallback"
```

Then build both sparse and dense/hash artifacts:

```powershell
python scripts/prepare_index.py --reports-dir reports/raw --manifest reports/manifest.jsonl --parsed-dir parsed --chunks-dir chunks --index-dir index --index-backend both
```

This creates `index/dense/embeddings.npy`, `chunk_ids.json`, `dense_meta.json`, and `faiss.index` when FAISS is available. It is a reproducible dense-like baseline, not a neural semantic embedding baseline.

## Reranking

The skill uses lexical reranking when:

- `RAG_FORCE_LEXICAL_RERANK=1`
- `RAG_FORCE_HASH_EMBEDDINGS=1`
- neural reranker dependencies or model downloads fail

This keeps retrieval usable offline and prevents large evaluations from repeatedly attempting model downloads.

Use `RAG_RERANKER_BACKEND=cross_encoder` for formal cross-encoder runs. Use `RAG_RERANKER_STRICT=1` when you want evaluation to fail instead of silently falling back to lexical reranking.

Report-aware heuristic flags default to off:

```powershell
Remove-Item Env:USE_RETRIEVAL_HEURISTICS -ErrorAction SilentlyContinue
Remove-Item Env:USE_RERANK_HEURISTICS -ErrorAction SilentlyContinue
```

They can be enabled for ablation:

```powershell
$env:USE_RETRIEVAL_HEURISTICS="1"
$env:USE_RERANK_HEURISTICS="1"
```

Current formal ablation found lower document recall with those flags enabled, so they are experimental rather than the recommended default.

## Optional Answer Model

- `answer --answer-engine extractive` requires no generation model.
- `answer --answer-engine medgemma` requires `MEDGEMMA_MODEL_NAME_OR_PATH`.
- `bundle` mode is the safest cross-platform handoff when another agent or hosted LLM will generate final prose.

## Install

```powershell
python -m pip install -r requirements.txt -c constraints.txt
python -m pip install -e ".[dev]" -c constraints.txt
```

`mcp` is required for the Codex Plugin MCP stdio server.

## Hugging Face Cache

By default on Windows, downloaded model files are stored in:

```text
%USERPROFILE%\.cache\huggingface\hub
```

unless `HF_HOME` or `HUGGINGFACE_HUB_CACHE` is set.

## Warning Handling

- The repository sets `HF_HUB_DISABLE_SYMLINKS_WARNING=1` before loading model libraries.
- To enable symlink-based caching on Windows, turn on Developer Mode or run Python as Administrator.
- `hf-xet` is included in requirements for Xet-backed model repositories.

## Validation

Semantic validation:

```powershell
Remove-Item Env:RAG_FORCE_HASH_EMBEDDINGS -ErrorAction SilentlyContinue
$env:RAG_FORCE_LEXICAL_RERANK="1"
$env:EMBEDDING_MODEL_NAME="BAAI/bge-small-en-v1.5"
python scripts/validate_skill_package.py --skill-root . --check-sample-baseline --require-index
python scripts/evaluate_strategies.py --questions evaluation/radiotherapy_skill_open_questions.json --index-dir index --strategies sparse hybrid auto routed --ignore-report-scope
```

Cross-encoder validation:

```powershell
Remove-Item Env:RAG_FORCE_LEXICAL_RERANK -ErrorAction SilentlyContinue
$env:RAG_RERANKER_BACKEND="cross_encoder"
$env:RERANKER_MODEL_NAME="BAAI/bge-reranker-base"
python scripts/evaluate_strategies.py --questions evaluation/radiotherapy_skill_open_questions.json --index-dir index --strategies hybrid auto --ignore-report-scope
```
