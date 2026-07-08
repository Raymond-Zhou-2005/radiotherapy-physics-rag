# Model Setup Notes

## Default Neural Retrieval Profile

- Embedding model: `BAAI/bge-base-en-v1.5`
- Query prefix: `Represent this sentence for searching relevant passages: `
- Passage prefix: none
- Reranker model: `BAAI/bge-reranker-v2-m3`
- Recommended reranker max length: 1024

This profile requires `sentence-transformers`, `transformers`, `torch`, and local model cache access.

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

No-model validation:

```powershell
$env:RAG_FORCE_HASH_EMBEDDINGS="1"
$env:RAG_FORCE_LEXICAL_RERANK="1"
$env:EMBEDDING_MODEL_NAME="hash-fallback"
python scripts/validate_skill_package.py --skill-root . --check-sample-baseline --require-index
python scripts/evaluate_strategies.py --questions evaluation/radiotherapy_skill_open_questions.json --index-dir index --strategies sparse hybrid auto routed --ignore-report-scope
```
