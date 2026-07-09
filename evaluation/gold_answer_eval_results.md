# Gold-Answer Seed Evaluation Results

- Questions: 12
- Retrieval backend: auto
- Evidence top-k: 8
- Skill OK rate: 0.917
- Citation present rate: 0.917
- Answer value hit rate: 0.333
- Evidence value hit rate: 0.583
- Gold-answer success rate: 0.583
- Unexpected errors: 1

Gold-answer seed evaluation checks short answer targets from public answer keys. It does not replace expert grading and may penalize extractive-only answers on calculation questions.

## Misses

### gold_external_q0001
- Answer value hit: False
- Evidence value hit: False
- Error code: None
- Retrieved doc_ids@5: iaea_pub1196_radiation_oncology_physics_handbook, iaea_hhr8_in_vivo_dosimetry, iaea_pub1196_radiation_oncology_physics_handbook, iaea_tecdoc1540_tps_acceptance, tg158

### gold_external_q0003
- Answer value hit: False
- Evidence value hit: False
- Error code: insufficient_evidence
- Retrieved doc_ids@5: 

### gold_external_q0006
- Answer value hit: False
- Evidence value hit: False
- Error code: None
- Retrieved doc_ids@5: iaea_trs492_brachytherapy_dosimetry, iaea_trs469_reference_dosimeters, iaea_trs492_brachytherapy_dosimetry, iaea_pub1196_radiation_oncology_physics_handbook, iaea_hhs14_planning_national_radiotherapy_services

### gold_external_q0007
- Answer value hit: False
- Evidence value hit: False
- Error code: None
- Retrieved doc_ids@5: iaea_pub1196_radiation_oncology_physics_handbook, iaea_hhs31_accuracy_requirements_dosimetry, iaea_pub1196_radiation_oncology_physics_handbook, aapm_report_46_tg40_radiation_oncology_qa, iaea_pub1196_radiation_oncology_physics_handbook

### gold_external_q0008
- Answer value hit: False
- Evidence value hit: False
- Error code: None
- Retrieved doc_ids@5: iaea_hhs14_planning_national_radiotherapy_services, iaea_ssg46_medical_uses_radiation_safety, iaea_trs492_brachytherapy_dosimetry, iaea_ssg46_medical_uses_radiation_safety, iaea_pub1196_radiation_oncology_physics_handbook
