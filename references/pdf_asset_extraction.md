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

`assets/extracted/asset_manifest.json` summarizes per-document asset counts.

Current local 35-document extraction summary:

| `doc_id` | Tables | Images |
| --- | ---: | ---: |
| `aapm_report_104_kv_imaging_guidance` | 0 | 22 |
| `aapm_report_113_physics_clinical_trials` | 4 | 24 |
| `aapm_report_166_biological_models_treatment_planning_qa` | 1 | 7 |
| `aapm_report_46_tg40_radiation_oncology_qa` | 0 | 134 |
| `aapm_report_90_essential_medical_physics_ebrt` | 0 | 1 |
| `aapm_tg263_nomenclature` | 4 | 7 |
| `aapm_tg51_photon_dosimetry_addendum` | 0 | 1 |
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

Totals: 348 tables and 3198 images.

## Commands

Metadata only:

```bash
python scripts/extract_pdf_assets.py reports/raw --output-dir assets/extracted
```

Metadata plus embedded image binaries:

```bash
python scripts/extract_pdf_assets.py reports/raw --output-dir assets/extracted --save-images
```

The metadata path is useful for review, evaluation, and future multimodal indexing. Generated asset metadata is ignored by Git because it is derived from third-party report PDFs. The main RAG index remains text-first until figure/table content is explicitly curated.
