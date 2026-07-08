#!/usr/bin/env python
"""Generate an open-source topic benchmark from the public source catalog.

The generated questions are intentionally paraphrased from public source
metadata. They are not copied from ABR, RAPHEX, or commercial question banks.
This benchmark tests whether the skill routes open-domain radiotherapy physics
questions to the right public report family; it is not an expert-adjudicated
clinical correctness benchmark.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List


DEFAULT_SOURCE_NOTE = (
    "Open-source topic benchmark item generated from public source metadata. "
    "It is not copied from paid, private, leaked, or expert-only examination material."
)

OOD_QUESTIONS = [
    "What hydration schedule is recommended for sourdough starter maintenance?",
    "Which Python web framework should I choose for a personal finance dashboard?",
    "What are the tax filing deadlines for a sole proprietorship in California?",
    "How should a violinist adjust bow pressure for Baroque ornamentation?",
    "What soil pH is best for growing blueberries in a home garden?",
    "Which chess opening is most suitable after 1. e4 c5 2. Nf3?",
    "How do I troubleshoot a leaking kitchen faucet cartridge?",
    "What is the best itinerary for a two-day visit to Kyoto?",
    "How should I train for a half marathon after a knee injury?",
    "What camera lens is best for street photography at night?",
    "How do I compare mortgage refinance offers?",
    "What is the safest way to clean mold from bathroom grout?",
    "How should a beginner learn jazz piano voicings?",
    "What are common causes of packet loss in a home Wi-Fi network?",
    "Which bread flour protein percentage is best for Neapolitan pizza dough?",
]

HARD_OOD_QUESTIONS = [
    "What chemotherapy regimen should be used for stage III lung cancer?",
    "How should a patient manage skin burns after radiotherapy?",
    "What MRI protocol is best for diagnosing a brain tumor?",
    "What ICD-10 code should be billed for external beam radiotherapy?",
    "Which antibiotic treats cellulitis after radiation dermatitis?",
    "What survival benefit does immunotherapy add after chemoradiation?",
    "How should a hospital obtain insurance authorization for IMRT?",
    "What CT contrast dose should be used for a patient with renal insufficiency?",
    "What diet should a patient follow during head and neck radiotherapy?",
    "Can proton therapy cure prostate cancer better than surgery?",
    "How should a patient interpret PET/CT SUV after treatment?",
    "What radiation dose should this patient receive for a new tumor diagnosis?",
    "Should my mother choose SBRT or surgery for early stage lung cancer?",
    "What are the legal requirements for malpractice documentation after a treatment error?",
    "How should a dentist manage osteoradionecrosis risk after radiotherapy?",
    "Which immunotherapy should be combined with radiation for melanoma?",
    "What prognosis should be given to a patient with metastatic disease after palliative radiotherapy?",
    "How should nausea be treated during abdominal radiotherapy?",
    "What surgical margin is required after preoperative radiotherapy?",
    "Which hospital billing code applies to adaptive radiotherapy planning?",
]


def slug_words(text: str, max_words: int = 18) -> str:
    words = re.findall(r"[A-Za-z0-9]+(?:[-/][A-Za-z0-9]+)?", text)
    return " ".join(words[:max_words]).lower()


def normalize_phrase(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    text = text.rstrip(".")
    return text[0].lower() + text[1:] if text else text


def is_runtime_source(record: Dict, runtime_only: bool) -> bool:
    if not runtime_only:
        return True
    return Path(record["file"]).exists()


def question_templates(record: Dict) -> Iterable[Dict[str, str]]:
    title = record.get("title", "").strip()
    role = normalize_phrase(record.get("role", "radiotherapy physics evidence"))
    topic = slug_words(role, max_words=16) or "radiotherapy physics"
    short_title = re.sub(r"^IAEA:\s*", "", title)

    yield {
        "type": "source_locator",
        "question": f"Which report evidence is most relevant for {topic}, and what should be checked first?",
    }
    yield {
        "type": "qa_or_safety",
        "question": f"What quality assurance, safety, or documentation issues are emphasized for {topic}?",
    }
    yield {
        "type": "implementation",
        "question": f"How should a radiotherapy physicist use guidance on {topic} when implementing or auditing a service?",
    }
    yield {
        "type": "uncertainty_or_limits",
        "question": f"What limitations, uncertainty sources, or practical constraints should be considered for {topic}?",
    }
    yield {
        "type": "named_source",
        "question": f"What does {short_title} cover that would matter for evidence-grounded radiotherapy physics QA?",
    }


def build_questions(sources: List[Dict], runtime_only: bool) -> List[Dict]:
    questions: List[Dict] = []
    in_scope_sources = [record for record in sources if is_runtime_source(record, runtime_only)]
    for record in in_scope_sources:
        for template in question_templates(record):
            qid = f"public_q{len(questions) + 1:04d}"
            questions.append(
                {
                    "qid": qid,
                    "question": template["question"],
                    "type": template["type"],
                    "report_id": record["doc_id"],
                    "gold_section": "",
                    "gold_chunk_ids": [],
                    "expected_abstain": False,
                    "source_basis": (
                        "Public source catalog topic derived from: "
                        f"{record.get('organization', 'unknown')} - {record.get('title', record['doc_id'])}"
                    ),
                    "source_urls": [record["source_url"]],
                    "source_note": DEFAULT_SOURCE_NOTE,
                    "benchmark_profile": "open_source_topic",
                }
            )

    for prompt in OOD_QUESTIONS:
        qid = f"public_q{len(questions) + 1:04d}"
        questions.append(
            {
                "qid": qid,
                "question": prompt,
                "type": "out_of_domain_control",
                "report_id": None,
                "gold_section": "",
                "gold_chunk_ids": [],
                "expected_abstain": True,
                "source_basis": "Negative control outside radiotherapy physics and outside the public source catalog.",
                "source_urls": [],
                "source_note": "Synthetic out-of-domain control used to test abstention behaviour.",
                "benchmark_profile": "open_source_topic",
            }
        )
    for prompt in HARD_OOD_QUESTIONS:
        qid = f"public_q{len(questions) + 1:04d}"
        questions.append(
            {
                "qid": qid,
                "question": prompt,
                "type": "medical_boundary_control",
                "report_id": None,
                "gold_section": "",
                "gold_chunk_ids": [],
                "expected_abstain": True,
                "source_basis": "Hard negative medical or administrative boundary question outside radiotherapy physics report QA.",
                "source_urls": [],
                "source_note": "Synthetic boundary control used to test abstention on medical-adjacent but out-of-scope requests.",
                "benchmark_profile": "open_source_topic",
            }
        )
    return questions


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a public radiotherapy physics topic benchmark.")
    parser.add_argument("--sources", type=Path, default=Path("reports/starter_corpus_sources.json"))
    parser.add_argument("--output", type=Path, default=Path("evaluation/public_credible_questions.json"))
    parser.add_argument(
        "--runtime-only",
        action="store_true",
        help="Only generate questions for sources whose PDF exists locally at the catalog file path.",
    )
    args = parser.parse_args()

    with args.sources.open("r", encoding="utf-8") as f:
        sources = json.load(f)
    questions = build_questions(sources, runtime_only=args.runtime_only)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(questions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "questions": len(questions), "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
