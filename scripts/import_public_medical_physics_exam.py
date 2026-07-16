#!/usr/bin/env python
"""Import a licensed public medical-physics MCQ set for external evaluation.

The imported file is evaluation data only. Runtime retrieval and answer code do
not read its answer keys. The source is version-pinned so results can be
reproduced without relying on a mutable repository branch.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import urllib.request
from collections import OrderedDict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SOURCE_REPOSITORY = "https://github.com/Mayo-Clinic-RadOnc-Foundation-Models/Radiation-Oncology-NLP-Database"
SOURCE_COMMIT = "27e04f14a141a3a92dcc1df0449245175ae94b7c"
SOURCE_RELATIVE_PATH = "5-Question and answering (QA)/Medical-Physics-100questions-QA-format.csv"
SOURCE_URL = (
    "https://raw.githubusercontent.com/Mayo-Clinic-RadOnc-Foundation-Models/"
    f"Radiation-Oncology-NLP-Database/{SOURCE_COMMIT}/"
    "5-Question%20and%20answering%20(QA)/Medical-Physics-100questions-QA-format.csv"
)
QUESTION_PREFIX_RE = re.compile(r"^(?P<number>\d+)\.\s*(?P<text>.+)$")
OPTION_RE = re.compile(r"^(?P<label>[A-Z])\.\s*(?P<text>.+)$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: OrderedDict[str, list[dict[str, str]]] = OrderedDict()
    for row in rows:
        question = str(row.get("Question") or "").strip()
        if not question:
            continue
        grouped.setdefault(question, []).append(row)

    questions: list[dict[str, Any]] = []
    for index, (source_question, choices) in enumerate(grouped.items(), start=1):
        question_match = QUESTION_PREFIX_RE.match(source_question)
        if not question_match:
            raise ValueError(f"Question has no numeric prefix: {source_question!r}")
        options = []
        gold_labels = []
        for choice in choices:
            option_match = OPTION_RE.match(str(choice.get("Answer_choice") or "").strip())
            if not option_match:
                raise ValueError(f"Option has no letter label: {choice!r}")
            label = option_match.group("label")
            option_text = option_match.group("text").strip()
            options.append({"label": label, "text": option_text})
            if str(choice.get("Correct_or_not") or "").strip() == "1":
                gold_labels.append(label)
        if len(gold_labels) != 1:
            raise ValueError(f"Expected exactly one correct option for question {index}, found {gold_labels}")
        questions.append(
            {
                "qid": f"public_mcq_{index:03d}",
                "source_question_number": int(question_match.group("number")),
                "question": question_match.group("text").strip(),
                "options": options,
                "gold_label": gold_labels[0],
                "gold_answer": next(option["text"] for option in options if option["label"] == gold_labels[0]),
                "benchmark_profile": "external_public_mcq",
                "corpus_relation": "external_to_runtime_corpus",
                "expected_abstain": False,
            }
        )
    return questions


def import_exam(source_csv: Path, output: Path, license_file: Path | None = None) -> dict[str, Any]:
    with source_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required_columns = {"Question", "Answer_choice", "Correct_or_not"}
    if not rows or not required_columns <= set(rows[0]):
        raise ValueError(f"Source CSV must contain {sorted(required_columns)}")

    questions = parse_rows(rows)
    if len(questions) != 100:
        raise ValueError(f"Expected 100 questions, found {len(questions)}")
    payload = {
        "schema_version": "1.0",
        "dataset_name": "Radiation Oncology NLP Database Medical Physics 100-question QA set",
        "license": "Apache-2.0",
        "source_repository": SOURCE_REPOSITORY,
        "source_commit": SOURCE_COMMIT,
        "source_relative_path": SOURCE_RELATIVE_PATH,
        "source_csv_sha256": sha256_file(source_csv),
        "source_policy": (
            "Imported from a version-pinned Apache-2.0 public dataset. This file is external evaluation data, "
            "not runtime knowledge. The skill must not read its gold_label or gold_answer fields at inference time."
        ),
        "question_count": len(questions),
        "questions": questions,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if license_file is not None:
        license_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(license_file, license_file.parent / "LICENSE-Apache-2.0.txt")
    return payload


def download_source(destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(SOURCE_URL, timeout=60) as response:
        destination.write_bytes(response.read())


def main() -> None:
    parser = argparse.ArgumentParser(description="Import the version-pinned Apache-2.0 public medical-physics MCQ set.")
    parser.add_argument("--source-csv", type=Path, default=None, help="Use a checked local source CSV instead of downloading.")
    parser.add_argument("--license-file", type=Path, default=None, help="Copy the source Apache-2.0 license beside output.")
    parser.add_argument("--output", type=Path, default=Path("evaluation/external/public_medical_physics_100_mcq.json"))
    parser.add_argument("--download-cache", type=Path, default=Path("Temp/public_medical_physics_100_mcq.csv"))
    args = parser.parse_args()

    source_csv = args.source_csv
    if source_csv is None:
        source_csv = args.download_cache
        download_source(source_csv)
    payload = import_exam(source_csv, args.output, args.license_file)
    print(
        json.dumps(
            {
                "ok": True,
                "questions": payload["question_count"],
                "output": str(args.output),
                "source_csv_sha256": payload["source_csv_sha256"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
