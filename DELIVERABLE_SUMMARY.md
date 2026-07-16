# Radiotherapy RAG Skill Delivery Summary

## Scope

This folder is the complete non-article implementation bundle for an open-source, Codex-usable radiotherapy physics RAG skill. It includes the local runtime build, clean public-release tooling, expanded source catalog, expanded benchmark, strategy evaluation, navigator evaluation, and agent-skill contract evaluation.

## Current Runtime

- Source metadata records: 49.
- Downloaded/indexed runtime PDFs: 49.
- Manual source candidates not in runtime: none in this local build.
- Indexed chunks: 8948 after the OpenDataLoader rebuild.
- PDF asset metadata: 440 tables and 2140 images.
- ChatGPT Knowledge upload files generated locally: 49.
- Navigator topics: 10.
- Semantic dense artifacts: `BAAI/bge-small-en-v1.5`, `sentence_transformers`, 384 dimensions, FAISS index.
- Cross-encoder reranker: `BAAI/bge-reranker-base`, with lexical fallback.
- Hash dense fallback: available only as explicit no-model CI/debug profile.
- Public answer-target benchmark: 61 questions.
- Direct skill-contract benchmark: 40 tasks.
- MCP stdio contract benchmark: 7 separate-process tasks.
- External public medical-physics MCQ benchmark: 100 Apache-2.0 answer-keyed questions outside the runtime corpus.
- Combined evaluation inventory: 622 cases across separate benchmark families, not a pooled clinical cohort.

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
python scripts/build_public_release.py --source-root . --output-dir D:\CodexWorkplace\RAG\radiotherapy-physics-rag-public --force
python scripts/audit_public_release.py --root D:\CodexWorkplace\RAG\radiotherapy-physics-rag-public
```

## Evaluation Snapshot

Benchmark: `evaluation/radiotherapy_skill_open_questions.json`

- Total questions: 280.
- In-domain public-source topic questions: 245.
- Out-of-domain controls: 35, including 20 hard medical-boundary negatives.
- Source policy: generated from public source catalog metadata; no ABR/RAPHEX/commercial copyrighted question text.

Current OpenDataLoader formal ablation:

- BM25 + lexical, no report-aware rules: Document Recall@5 = 0.918; OOD abstention = 34/35.
- Hybrid + lexical, no report-aware rules: Document Recall@5 = 0.935; OOD abstention = 34/35.
- Hybrid + cross-encoder, no report-aware rules: Document Recall@5 = 0.959; OOD abstention = 34/35.
- Hybrid + cross-encoder + report-aware rules: Document Recall@5 = 0.910; OOD abstention = 35/35.
- Routed full: Document Recall@5 = 0.918; OOD abstention = 35/35.

The highest-recall condition and the OOD-safe conditions differ. Pre-parser
strategy, navigator, and 280-question agent-skill result files are historical
traceability artifacts, not current ODL headline claims.

Asset QA evaluation:

- 120 table/figure metadata questions.
- Document Hit Rate@5: 119/120 (0.992).
- Page Hit Rate@5: 114/120 (0.950).
- Asset ID Trace Hit Rate@5: 114/120 (0.950).

Cell-level table QA:

- 14 exact-value table questions.
- Cell QA success rate: 14/14 (1.000).
- Evidence cell value hit rate: 14/14 (1.000).
- Answer cell value hit rate: 14/14 (1.000).

Public answer-target benchmark:

- 61 public answer-target questions.
- Gold-answer success rate: 44/61 (0.721).
- Evidence value hit rate: 44/61 (0.721).
- Extractive answer value hit rate: 31/61 (0.508).
- External public-answer-key profile: N = 12, evidence value hit = 5/12, answer value hit = 4/12.
- In-corpus open-report profile: N = 49, evidence value hit = 39/49, answer value hit = 27/49.

Answer-generation mode comparison:

- 61 public answer-target questions.
- Extractive answer value hit rate: 31/61 (0.508).
- Evidence-only value hit rate: 49/61 (0.803).
- Bundle prompt value hit rate: 49/61 (0.803).
- Answer synthesis gap rate: 0.295.

Direct skill-contract task evaluation:

- 40 downstream agent-use tasks.
- Task success rate: 1.000.
- In-scope structured success: 30/30; the 10 remaining tasks are correct OOD refusals.
- In-scope Document Hit Rate@5: 1.000.
- Hard medical-boundary OOD abstention success rate: 1.000.

MCP stdio contract evaluation:

- Seven separate-process MCP tasks passed.
- Required tools were present and transport errors were 0.
- This validates protocol transport and tool contracts, not autonomous host-agent planning.

Failure taxonomy:

- The frozen taxonomy needs regeneration before it is used as an ODL result.

Answer-quality proxy evaluation:

- Citation marker rate: 1.000.
- Used evidence ID valid rate: 1.000.
- Mean grounded token overlap: 0.956 on 60 successful ODL answers.
- Unsupported number case rate: 0.000.
- Overclaim flag rate: 0.000.
- OOD abstention is not measured in this 61-item answer-target proxy; use the formal ablation and direct skill-contract task results for OOD behavior.

Paper experiment matrix:

- `evaluation/paper_experiment_matrix.md`
- `evaluation/paper_experiment_matrix.json`
- The regenerated matrix reports current ODL formal ablations, direct skill/MCP contracts, asset/table QA, answer-target and answer-generation proxies, and the separate public-MCQ parser and Codex-agent comparisons.

External public MCQ comparison:

- Same deterministic option selector: historical PyMuPDF 34/100 versus OpenDataLoader 36/100; mean latency 14.932 versus 13.503 s/question.
- Recorded Codex agent using local skill evidence: 96/100 correct and citations on 100/100 responses; mean latency 9.059 s/question.
- The Codex result changes the answer host as well as the parser/runtime, is public development data, and is not blinded, expert-adjudicated, or clinical validation.

## Verification Snapshot

Latest expected validation commands:

```bash
pytest -q
python scripts/validate_skill_package.py --skill-root . --check-sample-baseline --require-index
python scripts/plugin_doctor.py --root .
python scripts/audit_public_release.py --root D:\CodexWorkplace\RAG\radiotherapy-physics-rag-public
```

## Boundary

This is research software and an open-source evaluation bundle, not a clinical decision system. It should not be used for patient-specific medical advice. The local folder contains third-party PDFs and derived runtime artifacts for local research use; the public GitHub release excludes those artifacts and keeps only source metadata, code, skill files, tests, and benchmark assets.

Routed retrieval can optionally append local query traces when `RAG_EXPERIENCE_APPEND=1` is set. That local memory file is excluded from the public release.
