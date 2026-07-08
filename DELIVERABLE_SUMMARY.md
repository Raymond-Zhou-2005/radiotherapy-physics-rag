# Radiotherapy RAG Skill Delivery Summary

## Scope

This folder is the complete non-article implementation bundle for an open-source, Codex-usable radiotherapy physics RAG skill. It includes the local runtime build, clean public-release tooling, expanded source catalog, expanded benchmark, strategy evaluation, navigator evaluation, and agent-skill contract evaluation.

## Current Runtime

- Source metadata records: 37.
- Downloaded/indexed PDFs: 35.
- Manual source candidates not in runtime: `aapm_tg100_radiotherapy_quality_management`, `tg158`.
- Indexed chunks: 9290.
- PDF asset metadata: 348 tables and 3198 images.
- ChatGPT Knowledge upload files generated locally: 35.
- Navigator topics: 10.
- Dense/hash artifacts: present for reproducible no-model hybrid baseline.

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

- Total questions: 190.
- In-domain public-source topic questions: 175.
- Out-of-domain controls: 15.
- Source policy: generated from public source catalog metadata; no ABR/RAPHEX/commercial copyrighted question text.

Strategy evaluation:

- Sparse Document Recall@5: 0.806.
- Hybrid hash+dense Document Recall@5: 0.754.
- Auto Document Recall@5: 0.754.
- Routed Document Recall@5: 0.794.

Navigator evaluation:

- Topic Recall@3: 0.966.
- Candidate Document Recall@5: 0.709.

Agent-skill contract evaluation:

- Routed tool success rate: 0.947.
- Routed Document Hit Rate@5: 0.800.
- Citation present rate: 0.994.
- OOD abstention success rate: 0.600.
- Unexpected in-scope error count: 1.

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
