# Failure Taxonomy

- Evaluation directory: evaluation
- Failure/gap cases: 58

Failure cases are automatically classified from benchmark outputs. They identify engineering failure modes, not expert clinical correctness.

## Counts By Category

| Category | Count |
|---|---:|
| answer_synthesis_gap | 35 |
| page_miss | 1 |
| retrieval_gap | 9 |
| retrieval_or_evidence_gap | 12 |
| skill_error | 1 |

## Counts By Source

| Source | Count |
|---|---:|
| answer_generation | 40 |
| gold_answer | 13 |
| table_cell | 5 |

## Cases

### gold_answer / gold_external_q0001
- Category: retrieval_or_evidence_gap
- Detail: Returned evidence did not contain the expected answer target.
- Error code: None
- Retrieved doc_ids@5: iaea_pub1196_radiation_oncology_physics_handbook, iaea_hhr8_in_vivo_dosimetry, iaea_pub1196_radiation_oncology_physics_handbook, iaea_tecdoc1540_tps_acceptance, tg158

### gold_answer / gold_external_q0003
- Category: skill_error
- Detail: Skill returned an error on an in-scope answer-target item.
- Error code: insufficient_evidence
- Retrieved doc_ids@5: 

### gold_answer / gold_external_q0006
- Category: retrieval_or_evidence_gap
- Detail: Returned evidence did not contain the expected answer target.
- Error code: None
- Retrieved doc_ids@5: iaea_trs492_brachytherapy_dosimetry, iaea_trs469_reference_dosimeters, iaea_trs492_brachytherapy_dosimetry, iaea_pub1196_radiation_oncology_physics_handbook, iaea_hhs14_planning_national_radiotherapy_services

### gold_answer / gold_external_q0007
- Category: retrieval_or_evidence_gap
- Detail: Returned evidence did not contain the expected answer target.
- Error code: None
- Retrieved doc_ids@5: iaea_pub1196_radiation_oncology_physics_handbook, iaea_hhs31_accuracy_requirements_dosimetry, iaea_pub1196_radiation_oncology_physics_handbook, aapm_report_46_tg40_radiation_oncology_qa, iaea_pub1196_radiation_oncology_physics_handbook

### gold_answer / gold_external_q0008
- Category: retrieval_or_evidence_gap
- Detail: Returned evidence did not contain the expected answer target.
- Error code: None
- Retrieved doc_ids@5: iaea_hhs14_planning_national_radiotherapy_services, iaea_ssg46_medical_uses_radiation_safety, iaea_trs492_brachytherapy_dosimetry, iaea_ssg46_medical_uses_radiation_safety, iaea_pub1196_radiation_oncology_physics_handbook

### gold_answer / gold_report_q0004
- Category: retrieval_or_evidence_gap
- Detail: Returned evidence did not contain the expected answer target.
- Error code: None
- Retrieved doc_ids@5: aapm_report_113_physics_clinical_trials, aapm_tg263_nomenclature, aapm_report_113_physics_clinical_trials, aapm_report_113_physics_clinical_trials, aapm_report_113_physics_clinical_trials

### gold_answer / gold_report_q0016
- Category: retrieval_or_evidence_gap
- Detail: Returned evidence did not contain the expected answer target.
- Error code: None
- Retrieved doc_ids@5: aapm_tg218_imrt_measurement_based_qa, aapm_tg218_imrt_measurement_based_qa, aapm_tg218_imrt_measurement_based_qa, aapm_tg218_imrt_measurement_based_qa, aapm_tg218_imrt_measurement_based_qa

### gold_answer / gold_report_q0019
- Category: retrieval_or_evidence_gap
- Detail: Returned evidence did not contain the expected answer target.
- Error code: None
- Retrieved doc_ids@5: aapm_tg101_sbrt, aapm_tg101_sbrt, aapm_tg101_sbrt, aapm_tg101_sbrt, aapm_tg101_sbrt

### gold_answer / gold_report_q0021
- Category: retrieval_or_evidence_gap
- Detail: Returned evidence did not contain the expected answer target.
- Error code: None
- Retrieved doc_ids@5: aapm_tg180_image_guidance_dose_management, aapm_tg180_image_guidance_dose_management, aapm_tg180_image_guidance_dose_management, aapm_tg180_image_guidance_dose_management, aapm_tg180_image_guidance_dose_management

### gold_answer / gold_report_q0024
- Category: retrieval_or_evidence_gap
- Detail: Returned evidence did not contain the expected answer target.
- Error code: None
- Retrieved doc_ids@5: tg158, tg158, tg158, aapm_tg120_imrt_dosimetry_tools, tg158

### gold_answer / gold_report_q0030
- Category: retrieval_or_evidence_gap
- Detail: Returned evidence did not contain the expected answer target.
- Error code: None
- Retrieved doc_ids@5: iaea_trs430_tps_commissioning_qa, iaea_tecdoc1583_tps_commissioning, iaea_tecdoc1583_tps_commissioning, iaea_trs430_tps_commissioning_qa

### gold_answer / gold_report_q0038
- Category: retrieval_or_evidence_gap
- Detail: Returned evidence did not contain the expected answer target.
- Error code: None
- Retrieved doc_ids@5: iaea_hhs19_ct_sim_radiotherapy, iaea_hhr7_record_verify_systems, iaea_ssg46_medical_uses_radiation_safety, iaea_ssg46_medical_uses_radiation_safety, iaea_ssg46_medical_uses_radiation_safety

### gold_answer / gold_report_q0040
- Category: retrieval_or_evidence_gap
- Detail: Returned evidence did not contain the expected answer target.
- Error code: None
- Retrieved doc_ids@5: iaea_ssg46_medical_uses_radiation_safety, iaea_hhr17_linear_accelerators, iaea_ssg46_medical_uses_radiation_safety, iaea_hhr17_linear_accelerators, iaea_hhr17_linear_accelerators

### answer_generation / gold_external_q0001
- Category: retrieval_gap
- Detail: Neither answer, evidence-only output, nor bundle prompt contained the expected target.
- Error code: None
- Retrieved doc_ids@5: iaea_pub1196_radiation_oncology_physics_handbook, iaea_hhr8_in_vivo_dosimetry, iaea_pub1196_radiation_oncology_physics_handbook, iaea_tecdoc1540_tps_acceptance, tg158

### answer_generation / gold_external_q0003
- Category: retrieval_gap
- Detail: Neither answer, evidence-only output, nor bundle prompt contained the expected target.
- Error code: None
- Retrieved doc_ids@5: 

### answer_generation / gold_external_q0004
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: iaea_pub1196_radiation_oncology_physics_handbook, aapm_tg75_igrt_imaging_dose, aapm_report_166_biological_models_treatment_planning_qa, iaea_ssg46_medical_uses_radiation_safety, iaea_pub1196_radiation_oncology_physics_handbook

### answer_generation / gold_external_q0006
- Category: retrieval_gap
- Detail: Neither answer, evidence-only output, nor bundle prompt contained the expected target.
- Error code: None
- Retrieved doc_ids@5: iaea_trs492_brachytherapy_dosimetry, iaea_trs469_reference_dosimeters, iaea_trs492_brachytherapy_dosimetry, iaea_pub1196_radiation_oncology_physics_handbook, iaea_hhs14_planning_national_radiotherapy_services

### answer_generation / gold_external_q0007
- Category: retrieval_gap
- Detail: Neither answer, evidence-only output, nor bundle prompt contained the expected target.
- Error code: None
- Retrieved doc_ids@5: iaea_pub1196_radiation_oncology_physics_handbook, iaea_hhs31_accuracy_requirements_dosimetry, iaea_pub1196_radiation_oncology_physics_handbook, aapm_report_46_tg40_radiation_oncology_qa, iaea_pub1196_radiation_oncology_physics_handbook

### answer_generation / gold_external_q0008
- Category: retrieval_gap
- Detail: Neither answer, evidence-only output, nor bundle prompt contained the expected target.
- Error code: None
- Retrieved doc_ids@5: iaea_hhs14_planning_national_radiotherapy_services, iaea_ssg46_medical_uses_radiation_safety, iaea_trs492_brachytherapy_dosimetry, iaea_ssg46_medical_uses_radiation_safety, iaea_pub1196_radiation_oncology_physics_handbook

### answer_generation / gold_external_q0011
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: aapm_report_113_physics_clinical_trials, aapm_report_113_physics_clinical_trials, iaea_hhs31_accuracy_requirements_dosimetry, iaea_hhs31_accuracy_requirements_dosimetry, iaea_ssg46_medical_uses_radiation_safety

### answer_generation / gold_external_q0012
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: iaea_pub1638_radiotherapy_in_cancer_care, iaea_tecdoc1588_3dcrt_imrt_transition, aapm_tg179_ct_based_igrt_qa, iaea_tecdoc1588_3dcrt_imrt_transition, iaea_tecdoc1588_3dcrt_imrt_transition

### answer_generation / gold_report_q0002
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: aapm_report_104_kv_imaging_guidance, aapm_report_104_kv_imaging_guidance, aapm_report_104_kv_imaging_guidance, aapm_report_104_kv_imaging_guidance, aapm_report_104_kv_imaging_guidance

### answer_generation / gold_report_q0004
- Category: retrieval_gap
- Detail: Neither answer, evidence-only output, nor bundle prompt contained the expected target.
- Error code: None
- Retrieved doc_ids@5: aapm_report_113_physics_clinical_trials, aapm_tg263_nomenclature, aapm_report_113_physics_clinical_trials, aapm_report_113_physics_clinical_trials, aapm_report_113_physics_clinical_trials

### answer_generation / gold_report_q0005
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: aapm_report_113_physics_clinical_trials, aapm_report_113_physics_clinical_trials, aapm_report_113_physics_clinical_trials, aapm_report_113_physics_clinical_trials, aapm_report_113_physics_clinical_trials

### answer_generation / gold_report_q0008
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: aapm_report_46_tg40_radiation_oncology_qa, aapm_tg142_medical_accelerator_qa, aapm_tg142_medical_accelerator_qa, aapm_report_46_tg40_radiation_oncology_qa, aapm_report_46_tg40_radiation_oncology_qa

### answer_generation / gold_report_q0010
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: aapm_tg100_radiotherapy_quality_management, aapm_tg100_radiotherapy_quality_management, aapm_tg100_radiotherapy_quality_management, aapm_tg100_radiotherapy_quality_management, aapm_tg100_radiotherapy_quality_management

### answer_generation / gold_report_q0011
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: aapm_tg263_nomenclature, aapm_tg263_nomenclature, aapm_tg263_nomenclature, aapm_tg263_nomenclature, aapm_tg263_nomenclature

### answer_generation / gold_report_q0012
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: aapm_tg148_helical_tomotherapy_qa, aapm_tg100_radiotherapy_quality_management, aapm_tg142_medical_accelerator_qa, aapm_tg148_helical_tomotherapy_qa, aapm_tg147_nonradiographic_localization_qa

### answer_generation / gold_report_q0013
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: aapm_tg119_imrt_commissioning, aapm_tg119_imrt_commissioning, aapm_tg119_imrt_commissioning, aapm_tg119_imrt_commissioning, aapm_tg119_imrt_commissioning

### answer_generation / gold_report_q0015
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: aapm_tg120_imrt_dosimetry_tools, aapm_tg120_imrt_dosimetry_tools, aapm_tg120_imrt_dosimetry_tools, aapm_tg120_imrt_dosimetry_tools, aapm_tg120_imrt_dosimetry_tools

### answer_generation / gold_report_q0016
- Category: retrieval_gap
- Detail: Neither answer, evidence-only output, nor bundle prompt contained the expected target.
- Error code: None
- Retrieved doc_ids@5: aapm_tg218_imrt_measurement_based_qa, aapm_tg218_imrt_measurement_based_qa, aapm_tg218_imrt_measurement_based_qa, aapm_tg218_imrt_measurement_based_qa, aapm_tg218_imrt_measurement_based_qa

### answer_generation / gold_report_q0018
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: aapm_tg147_nonradiographic_localization_qa, aapm_tg147_nonradiographic_localization_qa, aapm_tg147_nonradiographic_localization_qa, aapm_tg147_nonradiographic_localization_qa, aapm_tg147_nonradiographic_localization_qa

### answer_generation / gold_report_q0019
- Category: retrieval_gap
- Detail: Neither answer, evidence-only output, nor bundle prompt contained the expected target.
- Error code: None
- Retrieved doc_ids@5: aapm_tg101_sbrt, aapm_tg101_sbrt, aapm_tg101_sbrt, aapm_tg101_sbrt, aapm_tg101_sbrt

### answer_generation / gold_report_q0020
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: aapm_tg75_igrt_imaging_dose, aapm_tg75_igrt_imaging_dose, aapm_tg180_image_guidance_dose_management, aapm_tg75_igrt_imaging_dose, aapm_tg75_igrt_imaging_dose

### answer_generation / gold_report_q0021
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: aapm_tg180_image_guidance_dose_management, aapm_tg180_image_guidance_dose_management, aapm_tg180_image_guidance_dose_management, aapm_tg180_image_guidance_dose_management, aapm_tg180_image_guidance_dose_management

### answer_generation / gold_report_q0022
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: aapm_tg148_helical_tomotherapy_qa, aapm_tg148_helical_tomotherapy_qa, aapm_tg148_helical_tomotherapy_qa, aapm_tg148_helical_tomotherapy_qa, aapm_tg148_helical_tomotherapy_qa

### answer_generation / gold_report_q0023
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: aapm_report_113_physics_clinical_trials, aapm_tg132_image_registration_fusion, aapm_report_113_physics_clinical_trials, aapm_tg179_ct_based_igrt_qa, aapm_tg132_image_registration_fusion

### answer_generation / gold_report_q0024
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: tg158, tg158, tg158, aapm_tg120_imrt_dosimetry_tools, tg158

### answer_generation / gold_report_q0026
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: iaea_trs398_rev1_absorbed_dose_ebrt, iaea_trs398_rev1_absorbed_dose_ebrt, iaea_trs398_rev1_absorbed_dose_ebrt, iaea_trs398_rev1_absorbed_dose_ebrt, iaea_trs398_rev1_absorbed_dose_ebrt

### answer_generation / gold_report_q0027
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: iaea_trs469_reference_dosimeters, iaea_trs469_reference_dosimeters, iaea_trs469_reference_dosimeters, iaea_trs469_reference_dosimeters, iaea_trs469_reference_dosimeters

### answer_generation / gold_report_q0028
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: iaea_trs483_small_static_fields, iaea_trs483_small_static_fields, iaea_trs483_small_static_fields, iaea_trs483_small_static_fields, iaea_trs483_small_static_fields

### answer_generation / gold_report_q0030
- Category: retrieval_gap
- Detail: Neither answer, evidence-only output, nor bundle prompt contained the expected target.
- Error code: None
- Retrieved doc_ids@5: iaea_trs430_tps_commissioning_qa, iaea_tecdoc1583_tps_commissioning, iaea_tecdoc1583_tps_commissioning, iaea_trs430_tps_commissioning_qa

### answer_generation / gold_report_q0035
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: iaea_hhr16_igrt_qa, iaea_hhr16_igrt_qa, iaea_hhr16_igrt_qa, iaea_hhr16_igrt_qa, iaea_hhr16_igrt_qa

### answer_generation / gold_report_q0036
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: iaea_hhr18_radiotherapy_dosimetry_audits, iaea_hhr18_radiotherapy_dosimetry_audits, iaea_pub1297_quatro_audit_tool, iaea_hhr18_radiotherapy_dosimetry_audits, iaea_pub1638_radiotherapy_in_cancer_care

### answer_generation / gold_report_q0038
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: iaea_hhs19_ct_sim_radiotherapy, iaea_hhr7_record_verify_systems, iaea_ssg46_medical_uses_radiation_safety, iaea_ssg46_medical_uses_radiation_safety, iaea_ssg46_medical_uses_radiation_safety

### answer_generation / gold_report_q0039
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: iaea_hhr10_radiotherapy_facilities, iaea_hhr10_radiotherapy_facilities, iaea_hhr10_radiotherapy_facilities, iaea_hhr10_radiotherapy_facilities, iaea_hhr10_radiotherapy_facilities

### answer_generation / gold_report_q0040
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: iaea_ssg46_medical_uses_radiation_safety, iaea_hhr17_linear_accelerators, iaea_ssg46_medical_uses_radiation_safety, iaea_hhr17_linear_accelerators, iaea_hhr17_linear_accelerators

### answer_generation / gold_report_q0041
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: iaea_srs47_radiotherapy_facility_radiation_protection, iaea_srs47_radiotherapy_facility_radiation_protection, iaea_srs47_radiotherapy_facility_radiation_protection, iaea_srs47_radiotherapy_facility_radiation_protection, iaea_pub1638_radiotherapy_in_cancer_care

### answer_generation / gold_report_q0044
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: iaea_tecdoc989_radiation_dose_prescription_delivery, iaea_tecdoc989_radiation_dose_prescription_delivery, iaea_tecdoc989_radiation_dose_prescription_delivery, iaea_tecdoc989_radiation_dose_prescription_delivery, iaea_tecdoc989_radiation_dose_prescription_delivery

### answer_generation / gold_report_q0045
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: iaea_tecdoc1588_3dcrt_imrt_transition, iaea_tecdoc1588_3dcrt_imrt_transition, iaea_tecdoc1588_3dcrt_imrt_transition, iaea_tecdoc1588_3dcrt_imrt_transition, iaea_tecdoc1588_3dcrt_imrt_transition

### answer_generation / gold_report_q0046
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: iaea_hhs14_planning_national_radiotherapy_services, iaea_hhs14_planning_national_radiotherapy_services, iaea_hhs14_planning_national_radiotherapy_services, iaea_hhs14_planning_national_radiotherapy_services, iaea_hhs14_planning_national_radiotherapy_services

### answer_generation / gold_report_q0048
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: iaea_pub1990_quatro_quality_improvement, iaea_pub1990_quatro_quality_improvement, iaea_pub1990_quatro_quality_improvement, iaea_pub1990_quatro_quality_improvement, iaea_pub1638_radiotherapy_in_cancer_care

### answer_generation / gold_report_q0049
- Category: answer_synthesis_gap
- Detail: Evidence or bundle contained the target but extractive answer did not.
- Error code: None
- Retrieved doc_ids@5: iaea_pub1196_radiation_oncology_physics_handbook, iaea_hhs31_accuracy_requirements_dosimetry, iaea_trs483_small_static_fields, iaea_hhs31_accuracy_requirements_dosimetry, iaea_hhs31_accuracy_requirements_dosimetry

### table_cell / table_cell_q0001
- Category: answer_synthesis_gap
- Detail: Cell value was present in evidence but not in the extractive answer.
- Error code: None
- Retrieved doc_ids@5: aapm_tg101_sbrt, aapm_tg101_sbrt, aapm_tg101_sbrt, aapm_tg101_sbrt, aapm_tg101_sbrt

### table_cell / table_cell_q0002
- Category: answer_synthesis_gap
- Detail: Cell value was present in evidence but not in the extractive answer.
- Error code: None
- Retrieved doc_ids@5: aapm_tg101_sbrt, aapm_tg101_sbrt, aapm_tg101_sbrt, aapm_tg101_sbrt, aapm_tg101_sbrt

### table_cell / table_cell_q0008
- Category: answer_synthesis_gap
- Detail: Cell value was present in evidence but not in the extractive answer.
- Error code: None
- Retrieved doc_ids@5: aapm_tg100_radiotherapy_quality_management, aapm_tg100_radiotherapy_quality_management, aapm_tg100_radiotherapy_quality_management, aapm_tg100_radiotherapy_quality_management, aapm_tg100_radiotherapy_quality_management

### table_cell / table_cell_q0009
- Category: page_miss
- Detail: Expected table page was not retrieved.
- Error code: None
- Retrieved doc_ids@5: aapm_tg100_radiotherapy_quality_management, aapm_tg100_radiotherapy_quality_management, aapm_tg100_radiotherapy_quality_management, aapm_tg100_radiotherapy_quality_management, aapm_tg100_radiotherapy_quality_management

### table_cell / table_cell_q0014
- Category: answer_synthesis_gap
- Detail: Cell value was present in evidence but not in the extractive answer.
- Error code: None
- Retrieved doc_ids@5: aapm_report_113_physics_clinical_trials, iaea_pub1196_radiation_oncology_physics_handbook, aapm_tg179_ct_based_igrt_qa, iaea_trs430_tps_commissioning_qa, aapm_tg100_radiotherapy_quality_management
