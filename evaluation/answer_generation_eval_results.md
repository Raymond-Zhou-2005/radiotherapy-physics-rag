# Answer Generation Mode Evaluation

- Questions: 61
- Retrieval backend: auto
- Evidence top-k: 8
- Answer engine: extractive
- Extractive answer value hit rate: 0.344
- Extractive evidence value hit rate: 0.852
- Evidence-only value hit rate: 0.852
- Bundle prompt value hit rate: 0.852
- Citation present rate: 0.984
- Answer synthesis gap rate: 0.508
- Retrieval gap rate: 0.148
- Unexpected errors: 1

This local evaluation separates retrieval/evidence availability from extractive answer synthesis. It is not expert answer grading and does not use hosted LLMs.

## Gap Cases

### gold_external_q0001 (retrieval_gap)
- Retrieved doc_ids@5: iaea_pub1196_radiation_oncology_physics_handbook, iaea_hhr8_in_vivo_dosimetry, iaea_pub1196_radiation_oncology_physics_handbook, iaea_tecdoc1540_tps_acceptance, tg158
- Hit flags: answer=False, answer_evidence=False, evidence=False, bundle=False

### gold_external_q0003 (retrieval_gap)
- Retrieved doc_ids@5: 
- Hit flags: answer=False, answer_evidence=False, evidence=False, bundle=False

### gold_external_q0004 (answer_synthesis_gap)
- Retrieved doc_ids@5: iaea_pub1196_radiation_oncology_physics_handbook, aapm_tg75_igrt_imaging_dose, aapm_report_166_biological_models_treatment_planning_qa, iaea_ssg46_medical_uses_radiation_safety, iaea_pub1196_radiation_oncology_physics_handbook
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_external_q0006 (retrieval_gap)
- Retrieved doc_ids@5: iaea_trs492_brachytherapy_dosimetry, iaea_trs469_reference_dosimeters, iaea_trs492_brachytherapy_dosimetry, iaea_pub1196_radiation_oncology_physics_handbook, iaea_hhs14_planning_national_radiotherapy_services
- Hit flags: answer=False, answer_evidence=False, evidence=False, bundle=False

### gold_external_q0007 (retrieval_gap)
- Retrieved doc_ids@5: iaea_pub1196_radiation_oncology_physics_handbook, iaea_hhs31_accuracy_requirements_dosimetry, iaea_pub1196_radiation_oncology_physics_handbook, aapm_report_46_tg40_radiation_oncology_qa, iaea_pub1196_radiation_oncology_physics_handbook
- Hit flags: answer=False, answer_evidence=False, evidence=False, bundle=False

### gold_external_q0008 (retrieval_gap)
- Retrieved doc_ids@5: iaea_hhs14_planning_national_radiotherapy_services, iaea_ssg46_medical_uses_radiation_safety, iaea_trs492_brachytherapy_dosimetry, iaea_ssg46_medical_uses_radiation_safety, iaea_pub1196_radiation_oncology_physics_handbook
- Hit flags: answer=False, answer_evidence=False, evidence=False, bundle=False

### gold_external_q0011 (answer_synthesis_gap)
- Retrieved doc_ids@5: aapm_report_113_physics_clinical_trials, aapm_report_113_physics_clinical_trials, iaea_hhs31_accuracy_requirements_dosimetry, iaea_hhs31_accuracy_requirements_dosimetry, iaea_ssg46_medical_uses_radiation_safety
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_external_q0012 (answer_synthesis_gap)
- Retrieved doc_ids@5: iaea_pub1638_radiotherapy_in_cancer_care, iaea_tecdoc1588_3dcrt_imrt_transition, aapm_tg179_ct_based_igrt_qa, iaea_tecdoc1588_3dcrt_imrt_transition, iaea_tecdoc1588_3dcrt_imrt_transition
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0002 (answer_synthesis_gap)
- Retrieved doc_ids@5: aapm_report_104_kv_imaging_guidance, aapm_report_104_kv_imaging_guidance, aapm_report_104_kv_imaging_guidance, aapm_report_104_kv_imaging_guidance, aapm_report_104_kv_imaging_guidance
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0004 (retrieval_gap)
- Retrieved doc_ids@5: aapm_report_113_physics_clinical_trials, aapm_tg263_nomenclature, aapm_report_113_physics_clinical_trials, aapm_report_113_physics_clinical_trials, aapm_report_113_physics_clinical_trials
- Hit flags: answer=False, answer_evidence=False, evidence=False, bundle=False

### gold_report_q0005 (answer_synthesis_gap)
- Retrieved doc_ids@5: aapm_report_113_physics_clinical_trials, aapm_report_113_physics_clinical_trials, aapm_report_113_physics_clinical_trials, aapm_report_113_physics_clinical_trials, aapm_report_113_physics_clinical_trials
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0008 (answer_synthesis_gap)
- Retrieved doc_ids@5: aapm_report_46_tg40_radiation_oncology_qa, aapm_tg142_medical_accelerator_qa, aapm_tg142_medical_accelerator_qa, aapm_report_46_tg40_radiation_oncology_qa, aapm_report_46_tg40_radiation_oncology_qa
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0010 (answer_synthesis_gap)
- Retrieved doc_ids@5: aapm_tg100_radiotherapy_quality_management, aapm_tg100_radiotherapy_quality_management, aapm_tg100_radiotherapy_quality_management, aapm_tg100_radiotherapy_quality_management, aapm_tg100_radiotherapy_quality_management
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0011 (answer_synthesis_gap)
- Retrieved doc_ids@5: aapm_tg263_nomenclature, aapm_tg263_nomenclature, aapm_tg263_nomenclature, aapm_tg263_nomenclature, aapm_tg263_nomenclature
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0012 (answer_synthesis_gap)
- Retrieved doc_ids@5: aapm_tg148_helical_tomotherapy_qa, aapm_tg100_radiotherapy_quality_management, aapm_tg142_medical_accelerator_qa, aapm_tg148_helical_tomotherapy_qa, aapm_tg147_nonradiographic_localization_qa
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0013 (answer_synthesis_gap)
- Retrieved doc_ids@5: aapm_tg119_imrt_commissioning, aapm_tg119_imrt_commissioning, aapm_tg119_imrt_commissioning, aapm_tg119_imrt_commissioning, aapm_tg119_imrt_commissioning
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
- Retrieved doc_ids@5: aapm_tg75_igrt_imaging_dose, aapm_tg75_igrt_imaging_dose, aapm_tg180_image_guidance_dose_management, aapm_tg75_igrt_imaging_dose, aapm_tg75_igrt_imaging_dose
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0021 (answer_synthesis_gap)
- Retrieved doc_ids@5: aapm_tg180_image_guidance_dose_management, aapm_tg180_image_guidance_dose_management, aapm_tg180_image_guidance_dose_management, aapm_tg180_image_guidance_dose_management, aapm_tg180_image_guidance_dose_management
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0022 (answer_synthesis_gap)
- Retrieved doc_ids@5: aapm_tg148_helical_tomotherapy_qa, aapm_tg148_helical_tomotherapy_qa, aapm_tg148_helical_tomotherapy_qa, aapm_tg148_helical_tomotherapy_qa, aapm_tg148_helical_tomotherapy_qa
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0023 (answer_synthesis_gap)
- Retrieved doc_ids@5: aapm_report_113_physics_clinical_trials, aapm_tg132_image_registration_fusion, aapm_report_113_physics_clinical_trials, aapm_tg179_ct_based_igrt_qa, aapm_tg132_image_registration_fusion
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0024 (answer_synthesis_gap)
- Retrieved doc_ids@5: tg158, tg158, tg158, aapm_tg120_imrt_dosimetry_tools, tg158
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0026 (answer_synthesis_gap)
- Retrieved doc_ids@5: iaea_trs398_rev1_absorbed_dose_ebrt, iaea_trs398_rev1_absorbed_dose_ebrt, iaea_trs398_rev1_absorbed_dose_ebrt, iaea_trs398_rev1_absorbed_dose_ebrt, iaea_trs398_rev1_absorbed_dose_ebrt
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0027 (answer_synthesis_gap)
- Retrieved doc_ids@5: iaea_trs469_reference_dosimeters, iaea_trs469_reference_dosimeters, iaea_trs469_reference_dosimeters, iaea_trs469_reference_dosimeters, iaea_trs469_reference_dosimeters
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0028 (answer_synthesis_gap)
- Retrieved doc_ids@5: iaea_trs483_small_static_fields, iaea_trs483_small_static_fields, iaea_trs483_small_static_fields, iaea_trs483_small_static_fields, iaea_trs483_small_static_fields
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0030 (retrieval_gap)
- Retrieved doc_ids@5: iaea_trs430_tps_commissioning_qa, iaea_tecdoc1583_tps_commissioning, iaea_tecdoc1583_tps_commissioning, iaea_trs430_tps_commissioning_qa
- Hit flags: answer=False, answer_evidence=False, evidence=False, bundle=False

### gold_report_q0035 (answer_synthesis_gap)
- Retrieved doc_ids@5: iaea_hhr16_igrt_qa, iaea_hhr16_igrt_qa, iaea_hhr16_igrt_qa, iaea_hhr16_igrt_qa, iaea_hhr16_igrt_qa
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0036 (answer_synthesis_gap)
- Retrieved doc_ids@5: iaea_hhr18_radiotherapy_dosimetry_audits, iaea_hhr18_radiotherapy_dosimetry_audits, iaea_pub1297_quatro_audit_tool, iaea_hhr18_radiotherapy_dosimetry_audits, iaea_pub1638_radiotherapy_in_cancer_care
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0038 (answer_synthesis_gap)
- Retrieved doc_ids@5: iaea_hhs19_ct_sim_radiotherapy, iaea_hhr7_record_verify_systems, iaea_ssg46_medical_uses_radiation_safety, iaea_ssg46_medical_uses_radiation_safety, iaea_ssg46_medical_uses_radiation_safety
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0039 (answer_synthesis_gap)
- Retrieved doc_ids@5: iaea_hhr10_radiotherapy_facilities, iaea_hhr10_radiotherapy_facilities, iaea_hhr10_radiotherapy_facilities, iaea_hhr10_radiotherapy_facilities, iaea_hhr10_radiotherapy_facilities
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0040 (answer_synthesis_gap)
- Retrieved doc_ids@5: iaea_ssg46_medical_uses_radiation_safety, iaea_hhr17_linear_accelerators, iaea_ssg46_medical_uses_radiation_safety, iaea_hhr17_linear_accelerators, iaea_hhr17_linear_accelerators
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0041 (answer_synthesis_gap)
- Retrieved doc_ids@5: iaea_srs47_radiotherapy_facility_radiation_protection, iaea_srs47_radiotherapy_facility_radiation_protection, iaea_srs47_radiotherapy_facility_radiation_protection, iaea_srs47_radiotherapy_facility_radiation_protection, iaea_pub1638_radiotherapy_in_cancer_care
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0044 (answer_synthesis_gap)
- Retrieved doc_ids@5: iaea_tecdoc989_radiation_dose_prescription_delivery, iaea_tecdoc989_radiation_dose_prescription_delivery, iaea_tecdoc989_radiation_dose_prescription_delivery, iaea_tecdoc989_radiation_dose_prescription_delivery, iaea_tecdoc989_radiation_dose_prescription_delivery
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0045 (answer_synthesis_gap)
- Retrieved doc_ids@5: iaea_tecdoc1588_3dcrt_imrt_transition, iaea_tecdoc1588_3dcrt_imrt_transition, iaea_tecdoc1588_3dcrt_imrt_transition, iaea_tecdoc1588_3dcrt_imrt_transition, iaea_tecdoc1588_3dcrt_imrt_transition
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0046 (answer_synthesis_gap)
- Retrieved doc_ids@5: iaea_hhs14_planning_national_radiotherapy_services, iaea_hhs14_planning_national_radiotherapy_services, iaea_hhs14_planning_national_radiotherapy_services, iaea_hhs14_planning_national_radiotherapy_services, iaea_hhs14_planning_national_radiotherapy_services
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0048 (answer_synthesis_gap)
- Retrieved doc_ids@5: iaea_pub1990_quatro_quality_improvement, iaea_pub1990_quatro_quality_improvement, iaea_pub1990_quatro_quality_improvement, iaea_pub1990_quatro_quality_improvement, iaea_pub1638_radiotherapy_in_cancer_care
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True

### gold_report_q0049 (answer_synthesis_gap)
- Retrieved doc_ids@5: iaea_pub1196_radiation_oncology_physics_handbook, iaea_hhs31_accuracy_requirements_dosimetry, iaea_trs483_small_static_fields, iaea_hhs31_accuracy_requirements_dosimetry, iaea_hhs31_accuracy_requirements_dosimetry
- Hit flags: answer=False, answer_evidence=True, evidence=True, bundle=True
