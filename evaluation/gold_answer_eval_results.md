# Gold-Answer Seed Evaluation Results

- Questions: 61
- Retrieval backend: hybrid
- Evidence top-k: 8
- Extractive selector: auto
- Skill OK rate: 0.984
- Citation present rate: 0.984
- Answer value hit rate: 0.508
- Evidence value hit rate: 0.721
- Gold-answer success rate: 0.721
- Unexpected errors: 1

Gold-answer seed evaluation checks short answer targets from public answer keys. It does not replace expert grading and may penalize extractive-only answers on calculation questions.

## Results By Benchmark Profile

| Profile | Questions | Answer value hit | Evidence value hit | Gold-answer success |
| --- | ---: | ---: | ---: | ---: |
| external_gold_answer | 12 | 0.333 | 0.417 | 0.417 |
| open_report_gold_answer | 49 | 0.551 | 0.796 | 0.796 |

## Misses

### gold_external_q0001
- Answer value hit: False
- Evidence value hit: False
- Error code: None
- Retrieved doc_ids@5: iaea_pub1196_radiation_oncology_physics_handbook, iaea_hhr8_in_vivo_dosimetry, iaea_pub1196_radiation_oncology_physics_handbook, iaea_pub1196_radiation_oncology_physics_handbook, iaea_pub1196_radiation_oncology_physics_handbook

### gold_external_q0003
- Answer value hit: False
- Evidence value hit: False
- Error code: None
- Retrieved doc_ids@5: iaea_trs430_tps_commissioning_qa, aapm_tg106_beam_data_commissioning, iaea_hhs31_accuracy_requirements_dosimetry, aapm_tg106_beam_data_commissioning, iaea_tecdoc1274_brachytherapy_source_calibration

### gold_external_q0004
- Answer value hit: False
- Evidence value hit: False
- Error code: None
- Retrieved doc_ids@5: iaea_pub1196_radiation_oncology_physics_handbook, iaea_pub1196_radiation_oncology_physics_handbook, aapm_tg101_sbrt, iaea_pub1196_radiation_oncology_physics_handbook, aapm_report_166_biological_models_treatment_planning_qa

### gold_external_q0006
- Answer value hit: False
- Evidence value hit: False
- Error code: None
- Retrieved doc_ids@5: iaea_trs492_brachytherapy_dosimetry, iaea_trs492_brachytherapy_dosimetry, aapm_report_46_tg40_radiation_oncology_qa, iaea_trs469_reference_dosimeters, iaea_tecdoc1274_brachytherapy_source_calibration

### gold_external_q0007
- Answer value hit: False
- Evidence value hit: False
- Error code: None
- Retrieved doc_ids@5: iaea_hhs31_accuracy_requirements_dosimetry, aapm_report_104_kv_imaging_guidance, iaea_pub1196_radiation_oncology_physics_handbook, iaea_pub1196_radiation_oncology_physics_handbook, iaea_pub1196_radiation_oncology_physics_handbook

### gold_external_q0008
- Answer value hit: False
- Evidence value hit: False
- Error code: None
- Retrieved doc_ids@5: iaea_hhs14_planning_national_radiotherapy_services, iaea_trs492_brachytherapy_dosimetry, iaea_trs469_reference_dosimeters, iaea_trs492_brachytherapy_dosimetry, iaea_trs492_brachytherapy_dosimetry

### gold_external_q0012
- Answer value hit: False
- Evidence value hit: False
- Error code: None
- Retrieved doc_ids@5: iaea_tecdoc1588_3dcrt_imrt_transition, iaea_hhr16_igrt_qa, aapm_tg179_ct_based_igrt_qa, aapm_tg179_ct_based_igrt_qa, iaea_hhs31_accuracy_requirements_dosimetry

### gold_report_q0004
- Answer value hit: False
- Evidence value hit: False
- Error code: None
- Retrieved doc_ids@5: aapm_report_113_physics_clinical_trials, aapm_report_113_physics_clinical_trials, aapm_tg263_nomenclature, aapm_tg263_nomenclature, aapm_report_113_physics_clinical_trials

### gold_report_q0016
- Answer value hit: False
- Evidence value hit: False
- Error code: None
- Retrieved doc_ids@5: aapm_tg218_imrt_measurement_based_qa, aapm_tg218_imrt_measurement_based_qa, aapm_tg218_imrt_measurement_based_qa, aapm_tg218_imrt_measurement_based_qa, aapm_tg218_imrt_measurement_based_qa

### gold_report_q0019
- Answer value hit: False
- Evidence value hit: False
- Error code: None
- Retrieved doc_ids@5: aapm_tg101_sbrt, aapm_tg101_sbrt, aapm_tg101_sbrt, aapm_tg101_sbrt, aapm_tg101_sbrt

### gold_report_q0021
- Answer value hit: False
- Evidence value hit: False
- Error code: None
- Retrieved doc_ids@5: aapm_tg180_image_guidance_dose_management, aapm_tg180_image_guidance_dose_management, aapm_tg180_image_guidance_dose_management, aapm_tg180_image_guidance_dose_management, aapm_tg180_image_guidance_dose_management

### gold_report_q0024
- Answer value hit: False
- Evidence value hit: False
- Error code: None
- Retrieved doc_ids@5: tg158, tg158, aapm_tg120_imrt_dosimetry_tools, tg158, tg158

### gold_report_q0030
- Answer value hit: False
- Evidence value hit: False
- Error code: None
- Retrieved doc_ids@5: iaea_trs430_tps_commissioning_qa, iaea_trs430_tps_commissioning_qa, iaea_trs430_tps_commissioning_qa, iaea_trs430_tps_commissioning_qa

### gold_report_q0032
- Answer value hit: False
- Evidence value hit: False
- Error code: insufficient_evidence
- Retrieved doc_ids@5: 

### gold_report_q0038
- Answer value hit: False
- Evidence value hit: False
- Error code: None
- Retrieved doc_ids@5: iaea_hhr7_record_verify_systems, iaea_pub1297_quatro_audit_tool, iaea_hhs19_ct_sim_radiotherapy, iaea_ssg46_medical_uses_radiation_safety, iaea_pub1196_radiation_oncology_physics_handbook

### gold_report_q0040
- Answer value hit: False
- Evidence value hit: False
- Error code: None
- Retrieved doc_ids@5: iaea_hhr17_linear_accelerators, iaea_hhr17_linear_accelerators, iaea_hhr17_linear_accelerators, iaea_ssg46_medical_uses_radiation_safety, iaea_trs398_rev1_absorbed_dose_ebrt

### gold_report_q0049
- Answer value hit: False
- Evidence value hit: False
- Error code: None
- Retrieved doc_ids@5: iaea_hhs31_accuracy_requirements_dosimetry, iaea_trs483_small_static_fields, iaea_pub1297_quatro_audit_tool, iaea_hhs31_accuracy_requirements_dosimetry, iaea_pub1196_radiation_oncology_physics_handbook
