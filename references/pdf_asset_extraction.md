# PDF Asset Extraction

`scripts/extract_pdf_assets.py` extracts table and image metadata from report PDFs.

## Output

For each PDF, the script writes:

```text
assets/extracted/<doc_id>.assets.jsonl
```

Each record includes:

- `asset_id`
- `doc_id`
- `title`
- `source_path`
- `page`
- asset_type: `table` or `image`
- `bbox`
- `caption`
- rows and columns for detected tables
- image_xref, width, height, and extension for images
- short `text_preview` for detected tables in local runtime metadata

`assets/extracted/asset_manifest.json` summarizes per-document asset counts.

Current local 49-document extraction summary:

| `doc_id` | Tables | Images |
| --- | ---: | ---: |
| `aapm_report_104_kv_imaging_guidance` | 0 | 22 |
| `aapm_report_113_physics_clinical_trials` | 4 | 24 |
| `aapm_report_166_biological_models_treatment_planning_qa` | 1 | 7 |
| `aapm_report_46_tg40_radiation_oncology_qa` | 0 | 134 |
| `aapm_report_90_essential_medical_physics_ebrt` | 0 | 1 |
| `aapm_tg100_radiotherapy_quality_management` | 2 | 10 |
| `aapm_tg101_sbrt` | 46 | 4 |
| `aapm_tg106_beam_data_commissioning` | 4 | 15 |
| `aapm_tg119_imrt_commissioning` | 20 | 5 |
| `aapm_tg120_imrt_dosimetry_tools` | 6 | 3 |
| `aapm_tg132_image_registration_fusion` | 12 | 4 |
| `aapm_tg142_medical_accelerator_qa` | 19 | 2 |
| `aapm_tg147_nonradiographic_localization_qa` | 4 | 3 |
| `aapm_tg148_helical_tomotherapy_qa` | 9 | 8 |
| `aapm_tg179_ct_based_igrt_qa` | 37 | 2 |
| `aapm_tg180_image_guidance_dose_management` | 30 | 2 |
| `aapm_tg218_imrt_measurement_based_qa` | 32 | 2 |
| `aapm_tg263_nomenclature` | 4 | 7 |
| `aapm_tg51_photon_dosimetry_addendum` | 0 | 1 |
| `aapm_tg75_igrt_imaging_dose` | 34 | 3 |
| `iaea_hhr10_radiotherapy_facilities` | 10 | 526 |
| `iaea_hhr16_igrt_qa` | 3 | 1 |
| `iaea_hhr17_linear_accelerators` | 1 | 4 |
| `iaea_hhr18_radiotherapy_dosimetry_audits` | 8 | 78 |
| `iaea_hhr7_record_verify_systems` | 12 | 517 |
| `iaea_hhr8_in_vivo_dosimetry` | 40 | 626 |
| `iaea_hhs14_planning_national_radiotherapy_services` | 3 | 15 |
| `iaea_hhs19_ct_sim_radiotherapy` | 21 | 51 |
| `iaea_hhs31_accuracy_requirements_dosimetry` | 2 | 71 |
| `iaea_pub1196_radiation_oncology_physics_handbook` | 21 | 134 |
| `iaea_pub1297_quatro_audit_tool` | 0 | 9 |
| `iaea_pub1638_radiotherapy_in_cancer_care` | 14 | 101 |
| `iaea_pub1990_quatro_quality_improvement` | 85 | 8 |
| `iaea_srs47_radiotherapy_facility_radiation_protection` | 9 | 16 |
| `iaea_ssg46_medical_uses_radiation_safety` | 2 | 2 |
| `iaea_tecdoc1274_brachytherapy_source_calibration` | 2 | 4 |
| `iaea_tecdoc1540_tps_acceptance` | 29 | 5 |
| `iaea_tecdoc1543_quatro` | 21 | 215 |
| `iaea_tecdoc1583_tps_commissioning` | 4 | 37 |
| `iaea_tecdoc1588_3dcrt_imrt_transition` | 1 | 72 |
| `iaea_tecdoc989_radiation_dose_prescription_delivery` | 0 | 248 |
| `iaea_tecdoc_1040_radiotherapy_programme` | 0 | 97 |
| `iaea_trs398_absorbed_dose_ebrt` | 29 | 9 |
| `iaea_trs398_rev1_absorbed_dose_ebrt` | 0 | 51 |
| `iaea_trs430_tps_commissioning_qa` | 10 | 25 |
| `iaea_trs469_reference_dosimeters` | 2 | 6 |
| `iaea_trs483_small_static_fields` | 9 | 63 |
| `iaea_trs492_brachytherapy_dosimetry` | 1 | 11 |
| `tg158` | 52 | 2 |

Current OpenDataLoader rebuild totals: 440 tables and 2140 images.

## Commands

Metadata only:

```bash
python scripts/extract_pdf_assets.py reports/raw --output-dir assets/extracted
```

Metadata plus embedded image binaries:

```bash
python scripts/extract_pdf_assets.py reports/raw --output-dir assets/extracted --save-images
```

The metadata path is useful for review, evaluation, and future multimodal indexing. Generated asset metadata is ignored by Git because it is derived from third-party report PDFs. The main RAG index remains text-first, but explicit table/figure page queries now surface nearby asset metadata in evidence outputs.

## Asset QA Evaluation

```bash
python scripts/generate_asset_benchmark.py --assets-dir assets/extracted --sources reports/starter_corpus_sources.json --output evaluation/radiotherapy_asset_questions.json
python scripts/evaluate_asset_qa.py --questions evaluation/radiotherapy_asset_questions.json --index-dir index --retrieval-backend routed --output-json evaluation/asset_qa_eval_results.json --output-md evaluation/asset_qa_eval_results.md
```

Current 120-question metadata-derived result:

- Document Hit Rate@5: 1.000.
- Page Hit Rate@5: 0.983.
- Asset ID Trace Hit Rate@5: 0.950.
- Asset Type Trace Hit Rate@5: 0.975.

This evaluates whether the skill can retrieve evidence near the table/figure metadata. It is not full image understanding.
