#!/usr/bin/env python
"""Generate public answer-target benchmark items.

The benchmark deliberately avoids ABR, RAPHEX, commercial, leaked, or private
question-bank material. It combines:

1. Short targets paraphrased from public answer-key pages/documents.
2. Open-report answer targets derived from the public AAPM/IAEA source catalog.

This is a reproducible, non-expert benchmark for retrieval and answer-grounding
stress tests. It is not expert medical-physics grading.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils import write_json

AFOMP_2025 = "https://afomp.org/2025/02/27/answers-for-mcq-quiz/"
AFOMP_2023 = "https://afomp.org/2023/08/31/mcq-in-medical-physics-2/"
RANZCR_2023 = (
    "https://www.ranzcr.com/wp-content/uploads/2023/04/"
    "Radiation-Oncology-Phase-1-Examination-Sample-Questions-and-Answers-FINAL.pdf"
)


def load_source_urls() -> Dict[str, str]:
    source_path = PROJECT_ROOT / "reports" / "starter_corpus_sources.json"
    if not source_path.exists():
        return {}
    records = json.loads(source_path.read_text(encoding="utf-8"))
    return {
        str(item.get("doc_id")): str(item.get("source_url") or item.get("render_url") or "")
        for item in records
        if item.get("doc_id")
    }


def external_gold_items(common_note: str) -> List[Dict[str, Any]]:
    return [
        {
            "qid": "gold_external_q0001",
            "question": "In single-field megavoltage x-ray treatment prescribed at 5 cm depth, what happens to exit dose when using 15 MV instead of 6 MV?",
            "answer_type": "concept",
            "expected_answer_groups": [["exit dose will increase", "exit dose increases", "increase exit dose", "higher exit dose"]],
            "source_basis": "AFOMP public MCQ answer key, paraphrased",
            "source_urls": [AFOMP_2025],
        },
        {
            "qid": "gold_external_q0002",
            "question": "For the adjacent-field setup in the public AFOMP physics quiz, what skin gap was given for fields intersecting at 5 cm depth?",
            "answer_type": "numeric",
            "expected_answer_groups": [["0.80", "0.8"]],
            "source_basis": "AFOMP public MCQ answer key, paraphrased",
            "source_urls": [AFOMP_2025],
        },
        {
            "qid": "gold_external_q0003",
            "question": "What detector type is identified by the public AFOMP answer key as best for locating a dropped I-125 seed?",
            "answer_type": "device",
            "expected_answer_groups": [["Geiger counter", "GM counter", "Geiger-Mueller"]],
            "source_basis": "AFOMP public MCQ answer key, paraphrased",
            "source_urls": [AFOMP_2025],
        },
        {
            "qid": "gold_external_q0004",
            "question": "What whole-body dose is given in the public AFOMP answer key for LD50/60 without medical intervention?",
            "answer_type": "numeric",
            "expected_answer_groups": [["450 cGy", "450", "4.5 Gy", "4.5"]],
            "source_basis": "AFOMP public MCQ answer key, paraphrased",
            "source_urls": [AFOMP_2025],
        },
        {
            "qid": "gold_external_q0005",
            "question": "Among an electron, proton, and alpha particle each with 20 MeV kinetic energy, which particle is described as travelling almost at light speed?",
            "answer_type": "concept",
            "expected_answer_groups": [["electron"], ["speed of light", "light speed", "almost at the speed"]],
            "source_basis": "AFOMP public MCQ answer key, paraphrased",
            "source_urls": [AFOMP_2025],
        },
        {
            "qid": "gold_external_q0006",
            "question": "For Cs-131 with an approximately 10 day half-life, what activity 24 hours earlier corresponds to a 1.000 mCi calibration seed at the stated time?",
            "answer_type": "numeric",
            "expected_answer_groups": [["1.072", "1.07"]],
            "source_basis": "AFOMP public MCQ answer key, paraphrased",
            "source_urls": [AFOMP_2025],
        },
        {
            "qid": "gold_external_q0007",
            "question": "What interaction change explains the loss of contrast in a therapy verification image compared with a simulator radiographic image?",
            "answer_type": "concept",
            "expected_answer_groups": [["decreased photoelectric", "fewer photoelectric", "decrease in photoelectric"]],
            "source_basis": "AFOMP public MCQ answer key, paraphrased",
            "source_urls": [AFOMP_2023],
        },
        {
            "qid": "gold_external_q0008",
            "question": "After ten half-lives, approximately what fraction of the original radioactive activity remains?",
            "answer_type": "numeric",
            "expected_answer_groups": [["A/1000", "1/1000", "one thousandth", "0.1%"]],
            "source_basis": "AFOMP public MCQ answer key, paraphrased",
            "source_urls": [AFOMP_2023],
        },
        {
            "qid": "gold_external_q0009",
            "question": "In the RANZCR sample rubric, what is the planning organ at risk volume intended to account for?",
            "answer_type": "short_answer",
            "expected_answer_groups": [["margin", "volume"], ["organ at risk", "OAR"], ["uncertainty", "variation"]],
            "source_basis": "RANZCR public sample questions and answers, paraphrased",
            "source_urls": [RANZCR_2023],
        },
        {
            "qid": "gold_external_q0010",
            "question": "In the RANZCR sample rubric, what target motion concept is captured by internal target volume?",
            "answer_type": "short_answer",
            "expected_answer_groups": [["CTV", "clinical target volume"], ["position", "shape", "size"]],
            "source_basis": "RANZCR public sample questions and answers, paraphrased",
            "source_urls": [RANZCR_2023],
        },
        {
            "qid": "gold_external_q0011",
            "question": "According to the RANZCR sample rubric, why did ICRU 83 matter for IMRT prescribing and reporting?",
            "answer_type": "short_answer",
            "expected_answer_groups": [
                ["absorbed dose", "dose"],
                ["volume", "volumes", "DVH"],
                ["prescribing", "recording", "reporting"],
            ],
            "source_basis": "RANZCR public sample questions and answers, paraphrased",
            "source_urls": [RANZCR_2023],
        },
        {
            "qid": "gold_external_q0012",
            "question": "In the RANZCR sample rubric, what are common reasons for daily image-guided treatment verification in bulky head and neck IMRT?",
            "answer_type": "short_answer",
            "expected_answer_groups": [
                ["precision", "accuracy", "reproducibility"],
                ["margin", "margins"],
                ["adaptive", "anatomy", "tumour", "tumor"],
            ],
            "source_basis": "RANZCR public sample questions and answers, paraphrased",
            "source_urls": [RANZCR_2023],
        },
    ]


OPEN_REPORT_TARGETS: List[Dict[str, Any]] = [
    {
        "doc_id": "aapm_report_104_kv_imaging_guidance",
        "question": "How does TG-104 define in-room kV imaging in the treatment room?",
        "groups": [["radiographic imaging"], ["kV x-ray", "kilovoltage"], ["treatment room"]],
    },
    {
        "doc_id": "aapm_report_104_kv_imaging_guidance",
        "question": "What broad categories of in-room kV imaging systems are described by TG-104?",
        "groups": [["rail-track", "rail track"], ["ceiling", "floor"], ["gantry-mounted", "gantry mounted"]],
    },
    {
        "doc_id": "aapm_report_104_kv_imaging_guidance",
        "question": "What system properties does TG-104 say should be checked for kV imaging acceptance, commissioning, and QA?",
        "groups": [["image quality"], ["localization accuracy"], ["imaging dose"], ["system operation"]],
    },
    {
        "doc_id": "aapm_report_113_physics_clinical_trials",
        "question": "What data and naming issues are emphasized for radiation oncology clinical trial physics support?",
        "groups": [["DICOM"], ["DICOM RT"], ["AAPM TG-263", "TG-263", "structure names"]],
    },
    {
        "doc_id": "aapm_report_113_physics_clinical_trials",
        "question": "What type of preparation can QA centers use for trials that need benchmark planning studies?",
        "groups": [["benchmark"], ["phantom"], ["QA center", "QA centers"]],
    },
    {
        "doc_id": "aapm_report_166_biological_models_treatment_planning_qa",
        "question": "What biological treatment planning indices are discussed in AAPM Report 166?",
        "groups": [["TCP"], ["NTCP"], ["gEUD", "EUD"]],
    },
    {
        "doc_id": "aapm_report_166_biological_models_treatment_planning_qa",
        "question": "Why does AAPM Report 166 treat biologically based planning systems cautiously?",
        "groups": [["limitations"], ["model", "models"], ["clinical data", "parameter"]],
    },
    {
        "doc_id": "aapm_report_46_tg40_radiation_oncology_qa",
        "question": "What broad program area is covered by AAPM TG-40?",
        "groups": [["quality assurance", "QA"], ["radiation oncology"], ["comprehensive"]],
    },
    {
        "doc_id": "aapm_tg100_radiotherapy_quality_management",
        "question": "Which FMEA scoring dimensions are used in TG-100 radiotherapy quality management?",
        "groups": [["occurrence"], ["severity"], ["detectability"]],
    },
    {
        "doc_id": "aapm_tg100_radiotherapy_quality_management",
        "question": "What process-analysis tools does TG-100 connect with radiotherapy quality management?",
        "groups": [["process map", "process mapping"], ["fault tree"], ["FMEA"]],
    },
    {
        "doc_id": "aapm_tg263_nomenclature",
        "question": "What does TG-263 standardize for radiation oncology?",
        "groups": [["nomenclature"], ["structure", "structures"], ["target", "organ"]],
    },
    {
        "doc_id": "aapm_tg142_medical_accelerator_qa",
        "question": "What equipment class is the subject of TG-142 QA guidance?",
        "groups": [["medical accelerator", "accelerators"], ["quality assurance", "QA"], ["tolerance", "tolerances"]],
    },
    {
        "doc_id": "aapm_tg119_imrt_commissioning",
        "question": "What kind of IMRT commissioning evidence is associated with TG-119?",
        "groups": [["IMRT"], ["commissioning"], ["benchmark", "confidence"]],
    },
    {
        "doc_id": "aapm_tg106_beam_data_commissioning",
        "question": "What measurements and equipment does TG-106 associate with accelerator beam data commissioning?",
        "groups": [["beam data"], ["commissioning"], ["detector", "phantom"]],
    },
    {
        "doc_id": "aapm_tg120_imrt_dosimetry_tools",
        "question": "What measurement tools are discussed in TG-120 for IMRT dosimetry?",
        "groups": [["film"], ["ion chamber", "chambers"], ["array", "arrays"]],
    },
    {
        "doc_id": "aapm_tg218_imrt_measurement_based_qa",
        "question": "What QA methodology and limits are central to TG-218?",
        "groups": [["IMRT", "VMAT"], ["gamma"], ["tolerance", "action"]],
    },
    {
        "doc_id": "aapm_tg179_ct_based_igrt_qa",
        "question": "What CT-based image guidance technologies are within TG-179's QA scope?",
        "groups": [["CBCT", "cone-beam"], ["MVCT", "CT-on-rails", "CT on rails"], ["quality assurance", "QA"]],
    },
    {
        "doc_id": "aapm_tg147_nonradiographic_localization_qa",
        "question": "What nonradiographic localization systems are discussed in TG-147?",
        "groups": [["optical", "surface"], ["infrared", "radiofrequency", "electromagnetic"], ["localization", "positioning"]],
    },
    {
        "doc_id": "aapm_tg101_sbrt",
        "question": "What technical areas are emphasized by TG-101 for SBRT practice?",
        "groups": [["SBRT", "stereotactic body"], ["image guidance"], ["small field", "small fields"]],
    },
    {
        "doc_id": "aapm_tg75_igrt_imaging_dose",
        "question": "What patient-dose issue is the focus of TG-75 for image-guided radiotherapy?",
        "groups": [["imaging dose"], ["image-guided", "IGRT"], ["management"]],
    },
    {
        "doc_id": "aapm_tg180_image_guidance_dose_management",
        "question": "What three dose-management actions are described in TG-180's title and scope?",
        "groups": [["quantification"], ["management"], ["reduction"]],
    },
    {
        "doc_id": "aapm_tg148_helical_tomotherapy_qa",
        "question": "What modality-specific QA topic is covered by TG-148?",
        "groups": [["helical tomotherapy"], ["quality assurance", "QA"], ["delivery", "imaging", "treatment planning"]],
    },
    {
        "doc_id": "aapm_tg132_image_registration_fusion",
        "question": "What image-registration topics are central to TG-132?",
        "groups": [["rigid", "deformable"], ["registration"], ["commissioning", "validation", "quality assurance"]],
    },
    {
        "doc_id": "tg158",
        "question": "What dose region is the focus of TG-158?",
        "groups": [["outside the treated volume", "nontarget", "out-of-field"], ["external-beam", "external beam"], ["measurement", "calculation"]],
    },
    {
        "doc_id": "iaea_trs398_absorbed_dose_ebrt",
        "question": "What physical quantity and medium are central to IAEA TRS-398 reference dosimetry?",
        "groups": [["absorbed dose"], ["water"], ["external beam"]],
    },
    {
        "doc_id": "iaea_trs398_rev1_absorbed_dose_ebrt",
        "question": "What does TRS-398 Rev. 1 update for external beam radiotherapy?",
        "groups": [["absorbed dose"], ["external beam"], ["code of practice"]],
    },
    {
        "doc_id": "iaea_trs469_reference_dosimeters",
        "question": "What calibration topic is covered by IAEA TRS-469?",
        "groups": [["calibration"], ["reference dosimeter", "reference dosimeters"], ["external beam"]],
    },
    {
        "doc_id": "iaea_trs483_small_static_fields",
        "question": "What field type is covered by IAEA TRS-483 dosimetry guidance?",
        "groups": [["small static field", "small static fields"], ["dosimetry"], ["external beam"]],
    },
    {
        "doc_id": "iaea_trs492_brachytherapy_dosimetry",
        "question": "What treatment modality does IAEA TRS-492 address?",
        "groups": [["brachytherapy"], ["dosimetry"], ["source", "calibration"]],
    },
    {
        "doc_id": "iaea_trs430_tps_commissioning_qa",
        "question": "According to TRS-430, what are the main purposes of TPS commissioning tests?",
        "groups": [["education"], ["verification"], ["documentation"]],
    },
    {
        "doc_id": "iaea_trs430_tps_commissioning_qa",
        "question": "What user understanding is emphasized as a major component of TPS commissioning?",
        "groups": [["capabilities"], ["limitations"], ["TPS", "treatment planning system"]],
    },
    {
        "doc_id": "iaea_tecdoc1540_tps_acceptance",
        "question": "What procurement-stage TPS activities are covered by IAEA TECDOC-1540?",
        "groups": [["specification"], ["acceptance testing"], ["treatment planning system", "TPS"]],
    },
    {
        "doc_id": "iaea_tecdoc1583_tps_commissioning",
        "question": "What implementation activity is covered by IAEA TECDOC-1583 for radiotherapy TPSs?",
        "groups": [["commissioning"], ["treatment planning system", "TPS"], ["quality assurance", "QA", "testing"]],
    },
    {
        "doc_id": "iaea_hhs19_ct_sim_radiotherapy",
        "question": "What radiotherapy imaging equipment is the focus of IAEA HHS-19 QA guidance?",
        "groups": [["computed tomography", "CT"], ["radiotherapy"], ["quality assurance", "QA"]],
    },
    {
        "doc_id": "iaea_hhr16_igrt_qa",
        "question": "What programme type is covered by IAEA Human Health Reports No. 16?",
        "groups": [["image guided", "IGRT"], ["quality assurance", "QA"], ["programme", "program"]],
    },
    {
        "doc_id": "iaea_hhr18_radiotherapy_dosimetry_audits",
        "question": "What independent quality process is the focus of IAEA HHR-18?",
        "groups": [["audit", "audits"], ["dosimetry"], ["radiotherapy"]],
    },
    {
        "doc_id": "iaea_hhr8_in_vivo_dosimetry",
        "question": "What clinical dosimetry procedure is covered by IAEA Human Health Reports No. 8?",
        "groups": [["in vivo"], ["dosimetry"], ["radiotherapy"]],
    },
    {
        "doc_id": "iaea_hhr7_record_verify_systems",
        "question": "What workflow safety system is covered by IAEA HHR-7?",
        "groups": [["record and verify"], ["radiation treatment"], ["quality control", "commissioning", "safety"]],
    },
    {
        "doc_id": "iaea_hhr10_radiotherapy_facilities",
        "question": "What facility-planning topics are covered by IAEA HHR-10?",
        "groups": [["radiotherapy facilities", "facility"], ["shielding", "room"], ["workflow", "safety"]],
    },
    {
        "doc_id": "iaea_hhr17_linear_accelerators",
        "question": "Which equipment lifecycle activities are covered by IAEA HHR-17?",
        "groups": [["selection"], ["acceptance testing"], ["commissioning"], ["quality control"]],
    },
    {
        "doc_id": "iaea_srs47_radiotherapy_facility_radiation_protection",
        "question": "What design concern is central to IAEA SRS-47?",
        "groups": [["radiation protection"], ["design"], ["radiotherapy facilities", "shielding"]],
    },
    {
        "doc_id": "iaea_ssg46_medical_uses_radiation_safety",
        "question": "What safety domain is addressed by IAEA SSG-46?",
        "groups": [["radiation protection"], ["safety"], ["medical uses"]],
    },
    {
        "doc_id": "iaea_tecdoc1274_brachytherapy_source_calibration",
        "question": "What source-calibration setting is covered by IAEA TECDOC-1274?",
        "groups": [["brachytherapy"], ["source calibration", "calibration"], ["SSDL", "hospital"]],
    },
    {
        "doc_id": "iaea_tecdoc989_radiation_dose_prescription_delivery",
        "question": "What dose-chain stages are linked in IAEA TECDOC-989?",
        "groups": [["prescription"], ["delivery"], ["quality assurance", "QA"]],
    },
    {
        "doc_id": "iaea_tecdoc1588_3dcrt_imrt_transition",
        "question": "What technology transition is covered by IAEA TECDOC-1588?",
        "groups": [["2-D", "2D"], ["3-D conformal", "3D conformal"], ["IMRT"]],
    },
    {
        "doc_id": "iaea_hhs14_planning_national_radiotherapy_services",
        "question": "What health-system planning topic is covered by IAEA HHS-14?",
        "groups": [["national radiotherapy services"], ["planning"], ["resource", "capacity"]],
    },
    {
        "doc_id": "iaea_pub1638_radiotherapy_in_cancer_care",
        "question": "What global cancer-care issue is discussed in IAEA Radiotherapy in Cancer Care?",
        "groups": [["global"], ["radiotherapy"], ["access", "infrastructure", "workforce"]],
    },
    {
        "doc_id": "iaea_pub1297_quatro_audit_tool",
        "question": "What type of audit methodology is associated with the IAEA QUATRO tool?",
        "groups": [["comprehensive"], ["audit", "audits"], ["radiotherapy practices"]],
    },
    {
        "doc_id": "iaea_hhs31_accuracy_requirements_dosimetry",
        "question": "What two measurement concepts are central to IAEA HHS-31?",
        "groups": [["accuracy"], ["uncertainty", "uncertainties"], ["radiotherapy"]],
    },
]


def open_report_gold_items(common_note: str) -> List[Dict[str, Any]]:
    source_urls = load_source_urls()
    items: List[Dict[str, Any]] = []
    for offset, target in enumerate(OPEN_REPORT_TARGETS, start=1):
        doc_id = target["doc_id"]
        items.append(
            {
                "qid": f"gold_report_q{offset:04d}",
                "question": target["question"],
                "answer_type": "open_report_answer_target",
                "expected_answer_groups": target["groups"],
                "expected_doc_ids": [doc_id],
                "source_basis": "Open AAPM/IAEA report source catalog and locally parsed public report text",
                "source_urls": [source_urls.get(doc_id, "")],
                "source_note": common_note,
                "benchmark_profile": "open_report_gold_answer",
                "expected_abstain": False,
            }
        )
    return items


def gold_items() -> List[Dict[str, Any]]:
    external_note = (
        "Paraphrased public answer-key seed. The benchmark stores short factual answer targets, "
        "not copied proprietary exam banks. It is not expert-adjudicated."
    )
    open_report_note = (
        "Open-report answer target generated from public AAPM/IAEA source metadata and locally parsed report evidence. "
        "This is a reproducible benchmark target, not expert grading."
    )
    items = external_gold_items(external_note)
    for item in items:
        item["source_note"] = external_note
        item["benchmark_profile"] = "external_gold_answer"
        item["expected_abstain"] = False
    items.extend(open_report_gold_items(open_report_note))
    return items


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate public answer-target benchmark questions.")
    parser.add_argument("--output", type=Path, default=Path("evaluation/radiotherapy_gold_answer_questions.json"))
    args = parser.parse_args()
    items = gold_items()
    write_json(args.output, items)
    print(f"Wrote {len(items)} gold-answer benchmark items to {args.output}")


if __name__ == "__main__":
    main()
