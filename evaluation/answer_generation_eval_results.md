# Answer Generation Mode Evaluation

- Questions: 61
- Retrieval backend: hybrid
- Evidence top-k: 8
- Answer engine: extractive
- Extractive selector: auto
- Extractive answer value hit rate: 0.508
- Extractive evidence value hit rate: 0.803
- Evidence-only value hit rate: 0.803
- Bundle prompt value hit rate: 0.803
- Citation present rate: 0.984
- Answer synthesis gap rate: 0.295
- Retrieval gap rate: 0.197
- Unexpected errors: 1

This local evaluation separates retrieval/evidence availability from extractive answer synthesis. It is not expert answer grading and does not use hosted LLMs.

## Results By Benchmark Profile

| Profile | Questions | Answer value hit | Evidence-only value hit | Synthesis gap | Retrieval gap |
| --- | ---: | ---: | ---: | ---: | ---: |
| external_gold_answer | 12 | 0.333 | 0.417 | 0.083 | 0.583 |
| open_report_gold_answer | 49 | 0.551 | 0.898 | 0.347 | 0.102 |

## Gap Cases

### gold_external_q0001 (retrieval_gap)
- Retrieved doc_ids@5: iaea_pub1196_radiation_oncology_physics_handbook, iaea_hhr8_in_vivo_dosimetry, iaea_pub1196_radiation_oncology_physics_handbook, iaea_pub1196_radiation_oncology_physics_handbook, iaea_pub1196_radiation_oncology_physics_handbook
- Hit flags: answer=False, answer_evidence=False, evidence=False, bundle=False

### gold_external_q0003 (retrieval_gap)
- Retrieved doc_ids@5: iaea_trs430_tps_commissioning_qa, aapm_tg106_beam_data_commissioning, iaea_hhs31_accuracy_requirements_dosimetry, aapm_tg106_beam_data_commissioning, iaea_tecdoc1274_brachytherapy_source_calibration
- Hit flags: answer=False, answer_evidence=False, evidence=False, bundle=False

### gold_external_q0004 (retrieval_gap)
- Retrieved doc_ids@5: iaea_pub1196_radiation_oncology_physics_handbook, iaea_pub1196_radiation_oncology_physics_handbook, aapm_tg101_sbrt, iaea_pub1196_radiation_oncology_physics_handbook, aapm_report_166_biological_models_treatment_planning_qa
- Hit flags: answer=False, answer_evidence=False, evidence=False, bundle=False

### gold_external_q0006 (retrieval_gap)
- Retrieved doc_ids@5: iaea_trs492_brachytherapy_dosimetry, iaea_trs492_brachytherapy_dosimetry, aapm_report_46_tg40_radiation_oncology_qa, iaea_trs469_reference_dosimeters, iaea_tecdoc1274_brachytherapy_source_calibration
- Hit flags: answer=False, answer_evidence=False, evidence=False, bundle=False

### gold_external_q0007 (retrieval_gap)
- Retrieved doc_ids@5: iaea_hhs31_accuracy_requirements_dosimetry, aapm_report_104_kv_imaging_guidance, iaea_pub1196_radiation_oncology_physics_handbook, iaea_pub1196_radiation_oncology_physics_handbook, iaea_pub1196_radiation_oncology_physics_handbook
- Hit flags: answer=False, answer_evidence=False, evidence=False, bundle=False

### gold_external_q0008 (retrieval_gap)
- Retrieved doc_ids@5: iaea_hhs14_planning_national_radiotherapy_services, iaea_trs492_brachytherapy_dosimetry, iaea_trs469_reference_dosimeters, iaea_trs492_brachytherapy_dosimetry, iaea_trs492_brachytherapy_dosimetry
- Hit flags: answer=False, answer_evidence=False, evidence=False, bundle=False

### gold_external_q0011 (answer_synthesis_gap)
- Retrieved doc_ids@5: iaea_hhs31_accuracy_requirements_dosimetry, iaea_hhs31_accuracy_requirements_dosimetry
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_external_q0012 (retrieval_gap)
- Retrieved doc_ids@5: iaea_tecdoc1588_3dcrt_imrt_transition, iaea_hhr16_igrt_qa, aapm_tg179_ct_based_igrt_qa, aapm_tg179_ct_based_igrt_qa, iaea_hhs31_accuracy_requirements_dosimetry
- Hit flags: answer=False, answer_evidence=False, evidence=False, bundle=False

### gold_report_q0004 (retrieval_gap)
- Retrieved doc_ids@5: aapm_report_113_physics_clinical_trials, aapm_report_113_physics_clinical_trials, aapm_tg263_nomenclature, aapm_tg263_nomenclature, aapm_report_113_physics_clinical_trials
- Hit flags: answer=False, answer_evidence=False, evidence=False, bundle=False

### gold_report_q0008 (answer_synthesis_gap)
- Retrieved doc_ids@5: aapm_tg142_medical_accelerator_qa, aapm_tg142_medical_accelerator_qa, aapm_report_46_tg40_radiation_oncology_qa, aapm_report_46_tg40_radiation_oncology_qa, aapm_report_46_tg40_radiation_oncology_qa
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0015 (answer_synthesis_gap)
- Retrieved doc_ids@5: aapm_tg120_imrt_dosimetry_tools, aapm_tg120_imrt_dosimetry_tools, aapm_tg120_imrt_dosimetry_tools, aapm_tg120_imrt_dosimetry_tools, aapm_tg120_imrt_dosimetry_tools
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0016 (retrieval_gap)
- Retrieved doc_ids@5: aapm_tg218_imrt_measurement_based_qa, aapm_tg218_imrt_measurement_based_qa, aapm_tg218_imrt_measurement_based_qa, aapm_tg218_imrt_measurement_based_qa, aapm_tg218_imrt_measurement_based_qa
- Hit flags: answer=False, answer_evidence=False, evidence=False, bundle=False

### gold_report_q0018 (answer_synthesis_gap)
- Retrieved doc_ids@5: aapm_tg147_nonradiographic_localization_qa, aapm_tg147_nonradiographic_localization_qa, aapm_tg147_nonradiographic_localization_qa, aapm_tg147_nonradiographic_localization_qa, aapm_tg147_nonradiographic_localization_qa
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0019 (retrieval_gap)
- Retrieved doc_ids@5: aapm_tg101_sbrt, aapm_tg101_sbrt, aapm_tg101_sbrt, aapm_tg101_sbrt, aapm_tg101_sbrt
- Hit flags: answer=False, answer_evidence=False, evidence=False, bundle=False

### gold_report_q0020 (answer_synthesis_gap)
- Retrieved doc_ids@5: aapm_tg75_igrt_imaging_dose, aapm_tg75_igrt_imaging_dose, aapm_tg75_igrt_imaging_dose, aapm_tg180_image_guidance_dose_management, aapm_tg75_igrt_imaging_dose
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0021 (answer_synthesis_gap)
- Retrieved doc_ids@5: aapm_tg180_image_guidance_dose_management, aapm_tg180_image_guidance_dose_management, aapm_tg180_image_guidance_dose_management, aapm_tg180_image_guidance_dose_management, aapm_tg180_image_guidance_dose_management
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0024 (answer_synthesis_gap)
- Retrieved doc_ids@5: tg158, tg158, aapm_tg120_imrt_dosimetry_tools, tg158, tg158
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0027 (answer_synthesis_gap)
- Retrieved doc_ids@5: iaea_trs469_reference_dosimeters, iaea_trs469_reference_dosimeters, iaea_trs469_reference_dosimeters, iaea_trs469_reference_dosimeters, iaea_trs469_reference_dosimeters
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0029 (answer_synthesis_gap)
- Retrieved doc_ids@5: iaea_trs492_brachytherapy_dosimetry, iaea_trs492_brachytherapy_dosimetry, iaea_trs492_brachytherapy_dosimetry, iaea_trs492_brachytherapy_dosimetry, iaea_trs492_brachytherapy_dosimetry
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0030 (retrieval_gap)
- Retrieved doc_ids@5: iaea_trs430_tps_commissioning_qa, iaea_trs430_tps_commissioning_qa, iaea_trs430_tps_commissioning_qa, iaea_trs430_tps_commissioning_qa
- Hit flags: answer=False, answer_evidence=False, evidence=False, bundle=False

### gold_report_q0032 (retrieval_gap)
- Retrieved doc_ids@5: 
- Hit flags: answer=False, answer_evidence=False, evidence=False, bundle=False

### gold_report_q0035 (answer_synthesis_gap)
- Retrieved doc_ids@5: iaea_hhr16_igrt_qa, iaea_hhr16_igrt_qa, iaea_hhr16_igrt_qa, iaea_hhr16_igrt_qa, iaea_hhr16_igrt_qa
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0037 (answer_synthesis_gap)
- Retrieved doc_ids@5: iaea_hhr8_in_vivo_dosimetry, iaea_hhr8_in_vivo_dosimetry, iaea_hhr8_in_vivo_dosimetry, iaea_hhr8_in_vivo_dosimetry, iaea_hhr8_in_vivo_dosimetry
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0038 (answer_synthesis_gap)
- Retrieved doc_ids@5: iaea_hhr7_record_verify_systems, iaea_pub1297_quatro_audit_tool, iaea_hhs19_ct_sim_radiotherapy, iaea_ssg46_medical_uses_radiation_safety, iaea_pub1196_radiation_oncology_physics_handbook
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0039 (answer_synthesis_gap)
- Retrieved doc_ids@5: iaea_hhr10_radiotherapy_facilities, iaea_hhr10_radiotherapy_facilities, iaea_hhr10_radiotherapy_facilities, iaea_hhr10_radiotherapy_facilities, iaea_hhr10_radiotherapy_facilities
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0040 (answer_synthesis_gap)
- Retrieved doc_ids@5: iaea_hhr17_linear_accelerators, iaea_hhr17_linear_accelerators, iaea_hhr17_linear_accelerators, iaea_ssg46_medical_uses_radiation_safety, iaea_trs398_rev1_absorbed_dose_ebrt
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0041 (answer_synthesis_gap)
- Retrieved doc_ids@5: iaea_srs47_radiotherapy_facility_radiation_protection, iaea_srs47_radiotherapy_facility_radiation_protection, iaea_srs47_radiotherapy_facility_radiation_protection, iaea_srs47_radiotherapy_facility_radiation_protection, iaea_srs47_radiotherapy_facility_radiation_protection
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0042 (answer_synthesis_gap)
- Retrieved doc_ids@5: iaea_ssg46_medical_uses_radiation_safety, iaea_ssg46_medical_uses_radiation_safety, iaea_ssg46_medical_uses_radiation_safety, iaea_ssg46_medical_uses_radiation_safety, iaea_ssg46_medical_uses_radiation_safety
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0046 (answer_synthesis_gap)
- Retrieved doc_ids@5: iaea_hhs14_planning_national_radiotherapy_services, iaea_hhs14_planning_national_radiotherapy_services, iaea_hhs14_planning_national_radiotherapy_services, iaea_hhs14_planning_national_radiotherapy_services, iaea_hhs14_planning_national_radiotherapy_services
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0049 (answer_synthesis_gap)
- Retrieved doc_ids@5: iaea_hhs31_accuracy_requirements_dosimetry, iaea_trs483_small_static_fields, iaea_pub1297_quatro_audit_tool, iaea_hhs31_accuracy_requirements_dosimetry, iaea_pub1196_radiation_oncology_physics_handbook
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True
