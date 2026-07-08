# Radiotherapy RAG Skill Delivery Summary

## Scope

This folder is the complete non-article implementation bundle for an open-source, Codex-usable radiotherapy physics RAG skill. It includes the local runtime build, clean public-release tooling, expanded source catalog, expanded benchmark, strategy evaluation, navigator evaluation, and agent-skill contract evaluation.

## Current Runtime

- Source metadata records: 49.
- Downloaded/indexed runtime PDFs: 49.
- Manual source candidates not in runtime: none in this local build.
- Indexed chunks: 10923.
- PDF asset metadata: 655 tables and 3263 images.
- ChatGPT Knowledge upload files generated locally: 49.
- Navigator topics: 10.
- Semantic dense artifacts: `BAAI/bge-small-en-v1.5`, `sentence_transformers`, 384 dimensions, FAISS index.
- Hash dense fallback: available only as explicit no-model CI/debug profile.

## Main Entry Points

Evidence query:

```bash
python scripts/plugin_query.py --mode evidence --retrieval-backend routed "What accuracy requirements and uncertainty sources affect radiotherapy dosimetry and dose delivery?"
```

Build local runtime:

```bash
python scripts/download_starter_corpus.py --allow-manual-missing
python scripts/prepare_index.py --reports-dir reports/raw --manifest reports/manifest.jsonl --parsed-dir parsed --chunks-dir chunks --index-dir index --index-backend both
python scripts/build_navigator.py --index-dir index --manifest reports/manifest.jsonl --output-dir navigator --skill-dir skills/radiotherapy-physics-navigator
python scripts/extract_pdf_assets.py reports/raw --output-dir assets/extracted
python scripts/build_chatgpt_knowledge.py --root .
```

Build clean public release:

```bash
python scripts/build_public_release.py --source-root . --output-dir D:\CodexWorkplace\radiotherapy-physics-rag-public --force
python scripts/audit_public_release.py --root D:\CodexWorkplace\radiotherapy-physics-rag-public
```

## Evaluation Snapshot

Benchmark: `evaluation/radiotherapy_skill_open_questions.json`

- Total questions: 280.
- In-domain public-source topic questions: 245.
- Out-of-domain controls: 35, including 20 hard medical-boundary negatives.
- Source policy: generated from public source catalog metadata; no ABR/RAPHEX/commercial copyrighted question text.

Strategy evaluation:

- Sparse Document Recall@5: 0.861.
- Hybrid semantic Document Recall@5: 0.820.
- Auto Document Recall@5: 0.820.
- Routed Document Recall@5: 0.861.
- OOD abstention success: 1.000 for all evaluated retrieval strategies.

Navigator evaluation:

- Topic Recall@3: 0.967.
- Candidate Document Recall@5: 0.673.

Agent-skill contract evaluation:

- Routed tool success rate: 0.875.
- Routed Document Hit Rate@5: 0.861.
- Citation present rate: 1.000.
- OOD abstention success rate: 1.000.
- Unexpected in-scope error count: 0.

Asset QA evaluation:

- 120 table/figure metadata questions.
- Document Hit Rate@5: 1.000.
- Page Hit Rate@5: 0.983.
- Asset ID Trace Hit Rate@5: 0.950.

Answer-quality proxy evaluation:

- Citation marker rate: 1.000.
- Used evidence ID valid rate: 1.000.
- Mean grounded token overlap: 0.994.
- OOD abstention success rate: 1.000.

## Verification Snapshot

Latest expected validation commands:

```bash
pytest -q
python scripts/validate_skill_package.py --skill-root . --check-sample-baseline --require-index
python scripts/plugin_doctor.py --root .
python scripts/audit_public_release.py --root D:\CodexWorkplace\radiotherapy-physics-rag-public
```

## Boundary

This is research software and an open-source evaluation bundle, not a clinical decision system. It should not be used for patient-specific medical advice. The local folder contains third-party PDFs and derived runtime artifacts for local research use; the public GitHub release excludes those artifacts and keeps only source metadata, code, skill files, tests, and benchmark assets.

Routed retrieval can optionally append local query traces when `RAG_EXPERIENCE_APPEND=1` is set. That local memory file is excluded from the public release.
