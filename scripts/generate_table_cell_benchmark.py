#!/usr/bin/env python
"""Generate deterministic cell-value table QA benchmark items."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils import iter_jsonl, write_json


def load_asset_ids(project_root: Path) -> set[str]:
    asset_ids: set[str] = set()
    for path in (project_root / "assets" / "extracted").glob("*.assets.jsonl"):
        for item in iter_jsonl(path):
            if item.get("asset_id"):
                asset_ids.add(str(item["asset_id"]))
    return asset_ids


def table_items() -> List[Dict[str, Any]]:
    tg101_asset = "aapm_tg101_sbrt_p002_table_01"
    tg100_asset = "aapm_tg100_radiotherapy_quality_management_p014_table_01"
    tg113_table1 = "aapm_report_113_physics_clinical_trials_p011_table_01"
    tg113_table2 = "aapm_report_113_physics_clinical_trials_p015_table_01"
    tg101_url = "https://aapm.onlinelibrary.wiley.com/doi/full/10.1118/1.3438081"
    tg100_url = "https://pmc.ncbi.nlm.nih.gov/articles/PMC4985013/"
    tg113_url = "https://www.aapm.org/pubs/reports/RPT_113.pdf"
    return [
        {
            "qid": "table_cell_q0001",
            "question": "In AAPM TG 101 Table I on page 2, what dose per fraction range is listed for SBRT?",
            "report_id": "aapm_tg101_sbrt",
            "expected_page": 2,
            "expected_page_window": 1,
            "asset_id": tg101_asset,
            "asset_type": "table",
            "expected_answer_groups": [["6-30", "6 to 30"], ["Gy"]],
            "source_basis": "Cell value from locally extracted public PDF table metadata",
            "source_urls": [tg101_url],
            "benchmark_profile": "table_cell_value",
            "expected_abstain": False,
        },
        {
            "qid": "table_cell_q0002",
            "question": "In AAPM TG 101 Table I on page 2, how many fractions are listed for SBRT?",
            "report_id": "aapm_tg101_sbrt",
            "expected_page": 2,
            "expected_page_window": 1,
            "asset_id": tg101_asset,
            "asset_type": "table",
            "expected_answer_groups": [["1-5", "1 to 5"]],
            "source_basis": "Cell value from locally extracted public PDF table metadata",
            "source_urls": [tg101_url],
            "benchmark_profile": "table_cell_value",
            "expected_abstain": False,
        },
        {
            "qid": "table_cell_q0003",
            "question": "In AAPM TG 101 Table I, what margin scale is listed for SBRT?",
            "report_id": "aapm_tg101_sbrt",
            "expected_page": 2,
            "expected_page_window": 1,
            "asset_id": tg101_asset,
            "asset_type": "table",
            "expected_answer_groups": [["millimeters", "millimetres", "mm"]],
            "source_basis": "Cell value from locally extracted public PDF table metadata",
            "source_urls": [tg101_url],
            "benchmark_profile": "table_cell_value",
            "expected_abstain": False,
        },
        {
            "qid": "table_cell_q0004",
            "question": "In AAPM TG 101 Table I, what physics/dosimetry monitoring style is listed for SBRT?",
            "report_id": "aapm_tg101_sbrt",
            "expected_page": 2,
            "expected_page_window": 1,
            "asset_id": tg101_asset,
            "asset_type": "table",
            "expected_answer_groups": [["direct"], ["monitoring"]],
            "source_basis": "Cell value from locally extracted public PDF table metadata",
            "source_urls": [tg101_url],
            "benchmark_profile": "table_cell_value",
            "expected_abstain": False,
        },
        {
            "qid": "table_cell_q0005",
            "question": "In AAPM TG 101 Table I, what dose per fraction range is listed for conventional 3D/IMRT?",
            "report_id": "aapm_tg101_sbrt",
            "expected_page": 2,
            "expected_page_window": 1,
            "asset_id": tg101_asset,
            "asset_type": "table",
            "expected_answer_groups": [["1.8-3", "1.8 to 3"], ["Gy"]],
            "source_basis": "Cell value from locally extracted public PDF table metadata",
            "source_urls": [tg101_url],
            "benchmark_profile": "table_cell_value",
            "expected_abstain": False,
        },
        {
            "qid": "table_cell_q0006",
            "question": "In AAPM TG 101 Table I, how many fractions are listed for conventional 3D/IMRT?",
            "report_id": "aapm_tg101_sbrt",
            "expected_page": 2,
            "expected_page_window": 1,
            "asset_id": tg101_asset,
            "asset_type": "table",
            "expected_answer_groups": [["10-30", "10 to 30"]],
            "source_basis": "Cell value from locally extracted public PDF table metadata",
            "source_urls": [tg101_url],
            "benchmark_profile": "table_cell_value",
            "expected_abstain": False,
        },
        {
            "qid": "table_cell_q0007",
            "question": "In AAPM TG 100 Table II on page 14, what qualitative occurrence description is listed for rank 1?",
            "report_id": "aapm_tg100_radiotherapy_quality_management",
            "expected_page": 14,
            "expected_page_window": 1,
            "asset_id": tg100_asset,
            "asset_type": "table",
            "expected_answer_groups": [["failure unlikely"]],
            "source_basis": "Cell value from locally extracted public PDF table metadata",
            "source_urls": [tg100_url],
            "benchmark_profile": "table_cell_value",
            "expected_abstain": False,
        },
        {
            "qid": "table_cell_q0008",
            "question": "In AAPM TG 100 Table II, what occurrence frequency percentage is listed for rank 1?",
            "report_id": "aapm_tg100_radiotherapy_quality_management",
            "expected_page": 14,
            "expected_page_window": 1,
            "asset_id": tg100_asset,
            "asset_type": "table",
            "expected_answer_groups": [["0.01"]],
            "source_basis": "Cell value from locally extracted public PDF table metadata",
            "source_urls": [tg100_url],
            "benchmark_profile": "table_cell_value",
            "expected_abstain": False,
        },
        {
            "qid": "table_cell_q0009",
            "question": "In AAPM TG 100 Table II, what occurrence description is listed for rank 8?",
            "report_id": "aapm_tg100_radiotherapy_quality_management",
            "expected_page": 14,
            "expected_page_window": 1,
            "asset_id": tg100_asset,
            "asset_type": "table",
            "expected_answer_groups": [["repeated failures"]],
            "source_basis": "Cell value from locally extracted public PDF table metadata",
            "source_urls": [tg100_url],
            "benchmark_profile": "table_cell_value",
            "expected_abstain": False,
        },
        {
            "qid": "table_cell_q0010",
            "question": "In AAPM TG 113 Table 1, what previous name is listed for the American College of Radiology QA center?",
            "report_id": "aapm_report_113_physics_clinical_trials",
            "expected_page": 11,
            "expected_page_window": 1,
            "asset_id": tg113_table1,
            "asset_type": "table",
            "expected_answer_groups": [["no name change"]],
            "source_basis": "Cell value from locally extracted public PDF table metadata",
            "source_urls": [tg113_url],
            "benchmark_profile": "table_cell_value",
            "expected_abstain": False,
        },
        {
            "qid": "table_cell_q0011",
            "question": "In AAPM TG 113 Table 1, what previous organization is listed for IROC?",
            "report_id": "aapm_report_113_physics_clinical_trials",
            "expected_page": 11,
            "expected_page_window": 1,
            "asset_id": tg113_table1,
            "asset_type": "table",
            "expected_answer_groups": [["no previous organization"]],
            "source_basis": "Cell value from locally extracted public PDF table metadata",
            "source_urls": [tg113_url],
            "benchmark_profile": "table_cell_value",
            "expected_abstain": False,
        },
        {
            "qid": "table_cell_q0012",
            "question": "In AAPM TG 113 Table 2 on PET/CT quality control, what control is listed for blood glucose levels?",
            "report_id": "aapm_report_113_physics_clinical_trials",
            "expected_page": 15,
            "expected_page_window": 1,
            "asset_id": tg113_table2,
            "asset_type": "table",
            "expected_answer_groups": [["measure fasting blood glucose", "fasting blood glucose"], ["exclusion criteria"]],
            "source_basis": "Cell value from locally extracted public PDF table metadata",
            "source_urls": [tg113_url],
            "benchmark_profile": "table_cell_value",
            "expected_abstain": False,
        },
        {
            "qid": "table_cell_q0013",
            "question": "In AAPM TG 113 Table 2, what control is listed for residual activity in a radiotracer syringe?",
            "report_id": "aapm_report_113_physics_clinical_trials",
            "expected_page": 15,
            "expected_page_window": 1,
            "asset_id": tg113_table2,
            "asset_type": "table",
            "expected_answer_groups": [["measure", "correct"], ["residual activity"]],
            "source_basis": "Cell value from locally extracted public PDF table metadata",
            "source_urls": [tg113_url],
            "benchmark_profile": "table_cell_value",
            "expected_abstain": False,
        },
        {
            "qid": "table_cell_q0014",
            "question": "In AAPM TG 113 Table 2, what control is listed for decay correction errors?",
            "report_id": "aapm_report_113_physics_clinical_trials",
            "expected_page": 15,
            "expected_page_window": 1,
            "asset_id": tg113_table2,
            "asset_type": "table",
            "expected_answer_groups": [["synchronize", "synchronise"], ["scanner clock"]],
            "source_basis": "Cell value from locally extracted public PDF table metadata",
            "source_urls": [tg113_url],
            "benchmark_profile": "table_cell_value",
            "expected_abstain": False,
        },
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate table cell-value benchmark questions.")
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--output", type=Path, default=Path("evaluation/radiotherapy_table_cell_questions.json"))
    args = parser.parse_args()

    asset_ids = load_asset_ids(args.project_root)
    items = table_items()
    missing = sorted({item["asset_id"] for item in items if item["asset_id"] not in asset_ids})
    if missing:
        raise SystemExit("Missing expected asset ids: " + ", ".join(missing))
    write_json(args.output, items)
    print(f"Wrote {len(items)} table cell-value items to {args.output}")


if __name__ == "__main__":
    main()
