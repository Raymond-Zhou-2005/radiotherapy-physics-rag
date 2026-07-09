#!/usr/bin/env python
"""Generate a small public-answer-key benchmark seed.

The items are deliberately paraphrased from public answer-key pages/documents.
They are not bound to one indexed report. The evaluator asks the skill to search
the whole local corpus and checks whether the returned evidence/answer contains
the public gold answer.
"""

from __future__ import annotations

import argparse
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


def gold_items() -> List[Dict[str, Any]]:
    common_note = (
        "Paraphrased public answer-key seed. The benchmark stores short factual answer targets, "
        "not copied proprietary exam banks. Review source terms before expanding redistribution."
    )
    return [
        {
            "qid": "gold_external_q0001",
            "question": "In single-field megavoltage x-ray treatment prescribed at 5 cm depth, what happens to exit dose when using 15 MV instead of 6 MV?",
            "answer_type": "concept",
            "expected_answer_groups": [["exit dose will increase", "exit dose increases", "increase exit dose", "higher exit dose"]],
            "source_basis": "AFOMP public MCQ answer key, paraphrased",
            "source_urls": [AFOMP_2025],
            "source_note": common_note,
            "benchmark_profile": "external_gold_answer",
            "expected_abstain": False,
        },
        {
            "qid": "gold_external_q0002",
            "question": "For the adjacent-field setup in the public AFOMP physics quiz, what skin gap was given for fields intersecting at 5 cm depth?",
            "answer_type": "numeric",
            "expected_answer_groups": [["0.80", "0.8"]],
            "source_basis": "AFOMP public MCQ answer key, paraphrased",
            "source_urls": [AFOMP_2025],
            "source_note": common_note,
            "benchmark_profile": "external_gold_answer",
            "expected_abstain": False,
        },
        {
            "qid": "gold_external_q0003",
            "question": "What detector type is identified by the public AFOMP answer key as best for locating a dropped I-125 seed?",
            "answer_type": "device",
            "expected_answer_groups": [["Geiger counter", "GM counter", "Geiger-Mueller"]],
            "source_basis": "AFOMP public MCQ answer key, paraphrased",
            "source_urls": [AFOMP_2025],
            "source_note": common_note,
            "benchmark_profile": "external_gold_answer",
            "expected_abstain": False,
        },
        {
            "qid": "gold_external_q0004",
            "question": "What whole-body dose is given in the public AFOMP answer key for LD50/60 without medical intervention?",
            "answer_type": "numeric",
            "expected_answer_groups": [["450 cGy", "450", "4.5 Gy", "4.5"]],
            "source_basis": "AFOMP public MCQ answer key, paraphrased",
            "source_urls": [AFOMP_2025],
            "source_note": common_note,
            "benchmark_profile": "external_gold_answer",
            "expected_abstain": False,
        },
        {
            "qid": "gold_external_q0005",
            "question": "Among an electron, proton, and alpha particle each with 20 MeV kinetic energy, which particle is described as travelling almost at light speed?",
            "answer_type": "concept",
            "expected_answer_groups": [["electron"], ["speed of light", "light speed", "almost at the speed"]],
            "source_basis": "AFOMP public MCQ answer key, paraphrased",
            "source_urls": [AFOMP_2025],
            "source_note": common_note,
            "benchmark_profile": "external_gold_answer",
            "expected_abstain": False,
        },
        {
            "qid": "gold_external_q0006",
            "question": "For Cs-131 with an approximately 10 day half-life, what activity 24 hours earlier corresponds to a 1.000 mCi calibration seed at the stated time?",
            "answer_type": "numeric",
            "expected_answer_groups": [["1.072", "1.07"]],
            "source_basis": "AFOMP public MCQ answer key, paraphrased",
            "source_urls": [AFOMP_2025],
            "source_note": common_note,
            "benchmark_profile": "external_gold_answer",
            "expected_abstain": False,
        },
        {
            "qid": "gold_external_q0007",
            "question": "What interaction change explains the loss of contrast in a therapy verification image compared with a simulator radiographic image?",
            "answer_type": "concept",
            "expected_answer_groups": [["decreased photoelectric", "fewer photoelectric", "decrease in photoelectric"]],
            "source_basis": "AFOMP public MCQ answer key, paraphrased",
            "source_urls": [AFOMP_2023],
            "source_note": common_note,
            "benchmark_profile": "external_gold_answer",
            "expected_abstain": False,
        },
        {
            "qid": "gold_external_q0008",
            "question": "After ten half-lives, approximately what fraction of the original radioactive activity remains?",
            "answer_type": "numeric",
            "expected_answer_groups": [["A/1000", "1/1000", "one thousandth", "0.1%"]],
            "source_basis": "AFOMP public MCQ answer key, paraphrased",
            "source_urls": [AFOMP_2023],
            "source_note": common_note,
            "benchmark_profile": "external_gold_answer",
            "expected_abstain": False,
        },
        {
            "qid": "gold_external_q0009",
            "question": "In the RANZCR sample rubric, what is the planning organ at risk volume intended to account for?",
            "answer_type": "short_answer",
            "expected_answer_groups": [["margin", "volume"], ["organ at risk", "OAR"], ["uncertainty", "variation"]],
            "source_basis": "RANZCR public sample questions and answers, paraphrased",
            "source_urls": [RANZCR_2023],
            "source_note": common_note,
            "benchmark_profile": "external_gold_answer",
            "expected_abstain": False,
        },
        {
            "qid": "gold_external_q0010",
            "question": "In the RANZCR sample rubric, what target motion concept is captured by internal target volume?",
            "answer_type": "short_answer",
            "expected_answer_groups": [["CTV", "clinical target volume"], ["position", "shape", "size"]],
            "source_basis": "RANZCR public sample questions and answers, paraphrased",
            "source_urls": [RANZCR_2023],
            "source_note": common_note,
            "benchmark_profile": "external_gold_answer",
            "expected_abstain": False,
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
            "source_note": common_note,
            "benchmark_profile": "external_gold_answer",
            "expected_abstain": False,
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
            "source_note": common_note,
            "benchmark_profile": "external_gold_answer",
            "expected_abstain": False,
        },
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate external gold-answer seed questions.")
    parser.add_argument("--output", type=Path, default=Path("evaluation/radiotherapy_gold_answer_questions.json"))
    args = parser.parse_args()
    write_json(args.output, gold_items())
    print(f"Wrote {len(gold_items())} gold-answer seed items to {args.output}")


if __name__ == "__main__":
    main()
