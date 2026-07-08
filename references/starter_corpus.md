# Starter Corpus

## Scope

The starter source catalog supports radiotherapy physics evidence QA across dosimetry, treatment planning, image guidance, QA, safety, audits, brachytherapy, nontarget dose, facilities, nomenclature, workforce, and programme planning.

The public repository stores source metadata and build scripts. It does not redistribute third-party report PDFs or derived full-text artifacts. Users build the local corpus from official source URLs or from PDFs they are permitted to use locally.

## Current Catalog

- Source records: 49.
- Current local runtime PDFs: 49.
- Manual candidates not included in the current runtime: none in this local build.
- Current runtime chunks: 10923.

The latest source metadata lives in:

```text
reports/starter_corpus_sources.json
```

## Added 2026-07-08

The corpus was first expanded with five direct-download IAEA sources:

- `iaea_tecdoc1588_3dcrt_imrt_transition`
- `iaea_hhs14_planning_national_radiotherapy_services`
- `iaea_srs47_radiotherapy_facility_radiation_protection`
- `iaea_ssg46_medical_uses_radiation_safety`
- `iaea_pub1638_radiotherapy_in_cancer_care`

These were selected because they use official IAEA PDF URLs that can be rebuilt by the public download script.

The local runtime was then expanded again by refreshing the two previously missing AAPM sources and adding 12 additional public/free-access AAPM reports that improve coverage of QA, IMRT, IGRT, SBRT, image registration, imaging dose, Tomotherapy, and commissioning:

- `aapm_tg100_radiotherapy_quality_management`
- `tg158`
- `aapm_tg142_medical_accelerator_qa`
- `aapm_tg119_imrt_commissioning`
- `aapm_tg106_beam_data_commissioning`
- `aapm_tg120_imrt_dosimetry_tools`
- `aapm_tg218_imrt_measurement_based_qa`
- `aapm_tg179_ct_based_igrt_qa`
- `aapm_tg147_nonradiographic_localization_qa`
- `aapm_tg101_sbrt`
- `aapm_tg75_igrt_imaging_dose`
- `aapm_tg180_image_guidance_dose_management`
- `aapm_tg148_helical_tomotherapy_qa`
- `aapm_tg132_image_registration_fusion`

Several AAPM/Wiley records are public or free-access but not reliable direct scripted downloads. The source catalog therefore records official URLs plus, where useful, `download_url` or `render_url` hints. The public release does not redistribute these PDFs or derived full text.

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
- 260 questions total.
- 245 in-domain public-source topic questions.
- 15 OOD controls.

The benchmark is open-source and source-attributed, but not expert-adjudicated.
