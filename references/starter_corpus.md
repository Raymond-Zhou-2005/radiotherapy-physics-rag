# Starter Corpus

## Scope

The starter source catalog supports radiotherapy physics evidence QA across dosimetry, treatment planning, image guidance, QA, safety, audits, brachytherapy, nontarget dose, facilities, nomenclature, workforce, and programme planning.

The public repository stores source metadata and build scripts. It does not redistribute third-party report PDFs or derived full-text artifacts. Users build the local corpus from official source URLs or from PDFs they are permitted to use locally.

## Current Catalog

- Source records: 37.
- Current local runtime PDFs: 35.
- Manual candidates not included in the current runtime: `aapm_tg100_radiotherapy_quality_management`, `tg158`.
- Current runtime chunks: 9290.

The latest source metadata lives in:

```text
reports/starter_corpus_sources.json
```

## Added 2026-07-08

The corpus was expanded with five direct-download IAEA sources:

- `iaea_tecdoc1588_3dcrt_imrt_transition`
- `iaea_hhs14_planning_national_radiotherapy_services`
- `iaea_srs47_radiotherapy_facility_radiation_protection`
- `iaea_ssg46_medical_uses_radiation_safety`
- `iaea_pub1638_radiotherapy_in_cancer_care`

These were selected because they use official IAEA PDF URLs that can be rebuilt by the public download script.

## Runtime Build

```bash
python scripts/download_starter_corpus.py --allow-manual-missing
python scripts/prepare_index.py --reports-dir reports/raw --manifest reports/manifest.jsonl --parsed-dir parsed --chunks-dir chunks --index-dir index --index-backend both
python scripts/build_navigator.py --index-dir index --manifest reports/manifest.jsonl --output-dir navigator --skill-dir skills/radiotherapy-physics-navigator
python scripts/extract_pdf_assets.py reports/raw --output-dir assets/extracted
python scripts/build_chatgpt_knowledge.py --root .
```

## Public Boundary

Do not commit:

- PDFs
- manifest files derived from local PDFs
- parsed JSONL files
- chunk JSONL files
- BM25, FAISS, dense, or metadata index artifacts
- extracted asset metadata
- generated ChatGPT upload files

Do commit:

- `reports/starter_corpus_sources.json`
- scripts
- skill files
- tests
- benchmark questions
- public documentation
- navigator metadata if it does not include full document text

## Evaluation

Current public benchmark:

- `evaluation/radiotherapy_skill_open_questions.json`
- 190 questions total.
- 175 in-domain public-source topic questions.
- 15 OOD controls.

The benchmark is open-source and source-attributed, but not expert-adjudicated.
