#!/usr/bin/env python
"""Generate agent-facing task benchmark items."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils import write_json


def in_scope_task(
    qid: int,
    task: str,
    mode: str,
    question: str,
    expected_doc_ids: List[str],
    expected_bundle_prompt: bool = False,
    expected_asset_id: str | None = None,
    expected_answer_groups: List[List[str]] | None = None,
) -> Dict[str, Any]:
    item: Dict[str, Any] = {
        "qid": f"agent_task_q{qid:04d}",
        "task": task,
        "mode": mode,
        "question": question,
        "expected_doc_ids": expected_doc_ids,
        "expected_citations": True,
        "expected_abstain": False,
        "benchmark_profile": "agent_task",
    }
    if expected_bundle_prompt:
        item["expected_bundle_prompt"] = True
    if expected_asset_id:
        item["expected_asset_id"] = expected_asset_id
    if expected_answer_groups:
        item["expected_answer_groups"] = expected_answer_groups
    return item


def ood_task(qid: int, task: str, mode: str, question: str) -> Dict[str, Any]:
    return {
        "qid": f"agent_task_q{qid:04d}",
        "task": task,
        "mode": mode,
        "question": question,
        "expected_doc_ids": [],
        "expected_abstain": True,
        "benchmark_profile": "agent_task_hard_ood",
    }


def task_items() -> List[Dict[str, Any]]:
    tasks = [
        in_scope_task(
            1,
            "Collect cited evidence for an agent drafting a medical accelerator QA implementation note.",
            "evidence",
            "Find evidence for routine medical accelerator QA checks and tolerances in radiotherapy physics.",
            ["aapm_tg142_medical_accelerator_qa"],
        ),
        in_scope_task(
            2,
            "Build a grounded prompt bundle for treatment planning system commissioning QA.",
            "bundle",
            "Prepare an evidence bundle about commissioning computerized treatment planning systems for radiation therapy.",
            ["iaea_trs430_tps_commissioning_qa", "iaea_tecdoc1540_tps_acceptance", "iaea_tecdoc1583_tps_commissioning"],
            expected_bundle_prompt=True,
        ),
        in_scope_task(
            3,
            "Collect evidence for risk-analysis/FMEA quality management in radiotherapy.",
            "evidence",
            "Find evidence about FMEA, occurrence, severity, and detectability scoring for radiotherapy quality management.",
            ["aapm_tg100_radiotherapy_quality_management"],
        ),
        in_scope_task(
            4,
            "Answer a table-cell question and preserve the table asset trace.",
            "answer",
            "In AAPM TG 101 Table I on page 2, what dose per fraction range is listed for SBRT?",
            ["aapm_tg101_sbrt"],
            expected_asset_id="aapm_tg101_sbrt_p002_table_01",
            expected_answer_groups=[["6-30", "6 to 30"], ["Gy"]],
        ),
        in_scope_task(
            5,
            "Collect evidence for image-guided radiotherapy QA.",
            "evidence",
            "Find radiotherapy physics evidence on CT based image-guided radiotherapy QA and localization checks.",
            ["aapm_tg179_ct_based_igrt_qa", "aapm_tg75_igrt_imaging_dose", "iaea_hhr16_igrt_qa"],
        ),
        in_scope_task(
            6,
            "Collect evidence for absorbed-dose reference dosimetry.",
            "evidence",
            "Find evidence about absorbed dose determination in external beam radiotherapy reference dosimetry.",
            ["iaea_trs398_absorbed_dose_ebrt", "iaea_trs398_rev1_absorbed_dose_ebrt"],
        ),
        in_scope_task(
            7,
            "Collect evidence for target and OAR naming conventions.",
            "evidence",
            "Find evidence about standardized nomenclature for target volumes and organs at risk in radiation oncology.",
            ["aapm_tg263_nomenclature"],
        ),
        in_scope_task(
            8,
            "Collect evidence for clinical-trial physics QA responsibilities.",
            "evidence",
            "Find evidence about medical physics responsibilities and QA centers in radiation oncology clinical trials.",
            ["aapm_report_113_physics_clinical_trials"],
        ),
        in_scope_task(
            9,
            "Build a bundle for brachytherapy dosimetry evidence.",
            "bundle",
            "Prepare a grounded evidence bundle on brachytherapy dosimetry recommendations and source calibration.",
            ["iaea_trs492_brachytherapy_dosimetry", "iaea_tecdoc1274_brachytherapy_source_calibration"],
            expected_bundle_prompt=True,
        ),
        in_scope_task(
            10,
            "Collect evidence for small-field dosimetry.",
            "evidence",
            "Find evidence about dosimetry of small static fields in external beam radiotherapy.",
            ["iaea_trs483_small_static_fields"],
        ),
        in_scope_task(
            11,
            "Collect evidence for image-registration QA.",
            "evidence",
            "Find evidence about rigid and deformable image registration commissioning and validation in radiotherapy.",
            ["aapm_tg132_image_registration_fusion"],
        ),
        in_scope_task(
            12,
            "Collect evidence for nonradiographic localization QA.",
            "evidence",
            "Find evidence about nonradiographic radiotherapy localization and positioning system QA.",
            ["aapm_tg147_nonradiographic_localization_qa"],
        ),
        in_scope_task(
            13,
            "Collect evidence for SBRT workflow safety.",
            "evidence",
            "Find evidence about SBRT simulation, immobilization, image guidance, treatment planning, and QA.",
            ["aapm_tg101_sbrt"],
        ),
        in_scope_task(
            14,
            "Collect evidence for IGRT imaging-dose management.",
            "evidence",
            "Find evidence about managing and reducing imaging dose during image-guided radiotherapy.",
            ["aapm_tg75_igrt_imaging_dose", "aapm_tg180_image_guidance_dose_management"],
        ),
        in_scope_task(
            15,
            "Collect evidence for helical tomotherapy QA.",
            "evidence",
            "Find evidence about helical tomotherapy delivery, imaging, treatment planning, and dosimetric QA.",
            ["aapm_tg148_helical_tomotherapy_qa"],
        ),
        in_scope_task(
            16,
            "Collect evidence for IMRT patient-specific QA.",
            "evidence",
            "Find evidence about IMRT measurement-based verification, gamma analysis, tolerance limits, and action limits.",
            ["aapm_tg218_imrt_measurement_based_qa", "aapm_tg120_imrt_dosimetry_tools"],
        ),
        in_scope_task(
            17,
            "Build a bundle for accelerator beam-data commissioning.",
            "bundle",
            "Prepare a grounded evidence bundle on accelerator beam data commissioning equipment and measurement procedures.",
            ["aapm_tg106_beam_data_commissioning"],
            expected_bundle_prompt=True,
        ),
        in_scope_task(
            18,
            "Collect evidence for IMRT commissioning benchmark tests.",
            "evidence",
            "Find evidence about IMRT commissioning benchmark cases, confidence limits, planning, and dosimetry comparisons.",
            ["aapm_tg119_imrt_commissioning"],
        ),
        in_scope_task(
            19,
            "Collect evidence for biologically based treatment planning QA.",
            "evidence",
            "Find evidence about biological models, TCP, NTCP, gEUD, and QA for biologically based treatment planning.",
            ["aapm_report_166_biological_models_treatment_planning_qa"],
        ),
        in_scope_task(
            20,
            "Collect evidence for nontarget and out-of-field dose.",
            "evidence",
            "Find evidence about measurement and calculation of doses outside the treated volume from external-beam radiotherapy.",
            ["tg158"],
        ),
        in_scope_task(
            21,
            "Collect evidence for CT simulation QA.",
            "evidence",
            "Find evidence about computed tomography quality assurance for radiotherapy simulation and treatment planning.",
            ["iaea_hhs19_ct_sim_radiotherapy"],
        ),
        in_scope_task(
            22,
            "Collect evidence for independent dosimetry audits.",
            "evidence",
            "Find evidence about quality audits in radiotherapy dosimetry and independent audit interpretation.",
            ["iaea_hhr18_radiotherapy_dosimetry_audits"],
        ),
        in_scope_task(
            23,
            "Collect evidence for in vivo dosimetry workflow.",
            "evidence",
            "Find evidence about in vivo dosimetry procedures, detector selection, tolerances, and action levels.",
            ["iaea_hhr8_in_vivo_dosimetry"],
        ),
        in_scope_task(
            24,
            "Collect evidence for record-and-verify systems.",
            "evidence",
            "Find evidence about record and verify systems, workflow safety, commissioning, and quality control.",
            ["iaea_hhr7_record_verify_systems"],
        ),
        in_scope_task(
            25,
            "Collect evidence for radiotherapy facility design.",
            "evidence",
            "Find evidence about radiotherapy facility design, equipment rooms, shielding, workflow, and safety infrastructure.",
            ["iaea_hhr10_radiotherapy_facilities", "iaea_srs47_radiotherapy_facility_radiation_protection"],
        ),
        in_scope_task(
            26,
            "Collect evidence for equipment selection and acceptance testing.",
            "evidence",
            "Find evidence about selection, acceptance testing, commissioning, and quality control of radiotherapy equipment.",
            ["iaea_hhr17_linear_accelerators"],
        ),
        in_scope_task(
            27,
            "Build a bundle for national radiotherapy service planning.",
            "bundle",
            "Prepare a grounded evidence bundle about national radiotherapy service planning, resources, and capacity.",
            ["iaea_hhs14_planning_national_radiotherapy_services", "iaea_pub1638_radiotherapy_in_cancer_care"],
            expected_bundle_prompt=True,
        ),
        in_scope_task(
            28,
            "Collect evidence for radiation protection in medical radiation use.",
            "evidence",
            "Find evidence about radiation protection and safety responsibilities for medical uses of ionizing radiation relevant to radiotherapy.",
            ["iaea_ssg46_medical_uses_radiation_safety"],
        ),
        in_scope_task(
            29,
            "Collect evidence for dose accuracy and uncertainty requirements.",
            "evidence",
            "Find evidence about accuracy requirements and uncertainties in radiotherapy dosimetry.",
            ["iaea_hhs31_accuracy_requirements_dosimetry"],
        ),
        in_scope_task(
            30,
            "Collect evidence for prescription-to-delivery dose transfer.",
            "evidence",
            "Find evidence about radiation dose in radiotherapy from prescription to delivery and related QA.",
            ["iaea_tecdoc989_radiation_dose_prescription_delivery"],
        ),
        ood_task(31, "Reject a medically related but non-radiotherapy-physics query.", "evidence", "Which chemotherapy regimen should be selected for metastatic pancreatic cancer?"),
        ood_task(32, "Reject a clinical medication-management query outside the corpus.", "answer", "How should an insulin dose be adjusted for an individual patient with fasting hypoglycemia?"),
        ood_task(33, "Reject a medical-imaging question that is not radiotherapy physics guidance.", "evidence", "What is the best MRI sequence to diagnose acute ischemic stroke in an emergency department?"),
        ood_task(34, "Reject a billing and insurance question.", "evidence", "Which ICD-10 code should be used to bill a radiation dermatitis follow-up visit?"),
        ood_task(35, "Reject a nutrition-support question.", "answer", "What diet should a head and neck cancer patient follow during mucositis?"),
        ood_task(36, "Reject a dental management question.", "evidence", "How should osteoradionecrosis of the mandible be treated clinically?"),
        ood_task(37, "Reject a PET/CT interpretation question outside the physics corpus.", "evidence", "What SUV cutoff should diagnose malignant recurrence on PET/CT?"),
        ood_task(38, "Reject a legal risk-management question.", "answer", "What malpractice liability applies if a radiotherapy plan review is delayed?"),
        ood_task(39, "Reject a general surgery decision question.", "evidence", "Should a patient choose SBRT or surgery for an operable lung tumor?"),
        ood_task(40, "Reject a symptom-management question.", "answer", "How should severe nausea after cancer treatment be managed with medication?"),
    ]
    return tasks


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate agent task benchmark questions.")
    parser.add_argument("--output", type=Path, default=Path("evaluation/radiotherapy_agent_tasks.json"))
    args = parser.parse_args()
    items = task_items()
    write_json(args.output, items)
    print(f"Wrote {len(items)} agent task items to {args.output}")


if __name__ == "__main__":
    main()
