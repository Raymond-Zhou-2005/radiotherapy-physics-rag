#!/usr/bin/env python
"""Generate traceable cell-value table QA items from current extracted tables.

The targets are short values visible in OpenDataLoader table previews. They
exercise evidence retrieval, page linkage, asset linkage, and value surfacing;
they are not a substitute for visual or expert table verification.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils import iter_jsonl, write_json

SOURCES = {
    "aapm_tg100_radiotherapy_quality_management": "https://pmc.ncbi.nlm.nih.gov/articles/PMC4985013/",
    "aapm_report_113_physics_clinical_trials": "https://www.aapm.org/pubs/reports/RPT_113.pdf",
}


def load_tables(project_root: Path) -> Dict[str, Dict[str, Any]]:
    tables: Dict[str, Dict[str, Any]] = {}
    for path in (project_root / "assets" / "extracted").glob("*.assets.jsonl"):
        for item in iter_jsonl(path):
            asset_id = str(item.get("asset_id") or "")
            if item.get("asset_type") == "table" and asset_id and str(item.get("text_preview") or "").strip():
                tables[asset_id] = item
    return tables


def table_item(
    qid: str,
    question: str,
    report_id: str,
    asset_id: str,
    expected_answer_groups: List[List[str]],
) -> Dict[str, Any]:
    return {
        "qid": qid,
        "question": question,
        "report_id": report_id,
        "asset_id": asset_id,
        "asset_type": "table",
        "expected_answer_groups": expected_answer_groups,
        "source_basis": "Short cell value from current OpenDataLoader extraction of a public PDF table preview",
        "source_urls": [SOURCES[report_id]],
        "benchmark_profile": "table_cell_value",
        "expected_abstain": False,
    }


def table_items() -> List[Dict[str, Any]]:
    tg100 = "aapm_tg100_radiotherapy_quality_management_p014_table_01"
    tg113_qa = "aapm_report_113_physics_clinical_trials_p011_table_01"
    tg113_pet = "aapm_report_113_physics_clinical_trials_p015_table_12"
    return [
        table_item("table_cell_q0001", "In AAPM TG 100 Table II, what occurrence description is listed for rank 1?", "aapm_tg100_radiotherapy_quality_management", tg100, [["failure unlikely"]]),
        table_item("table_cell_q0002", "In AAPM TG 100 Table II, what occurrence frequency percentage is listed for rank 1?", "aapm_tg100_radiotherapy_quality_management", tg100, [["0.01"]]),
        table_item("table_cell_q0003", "In AAPM TG 100 Table II, what occurrence description is listed for rank 3?", "aapm_tg100_radiotherapy_quality_management", tg100, [["relatively few failures"]]),
        table_item("table_cell_q0004", "In AAPM TG 100 Table II, what severity description is listed for rank 4?", "aapm_tg100_radiotherapy_quality_management", tg100, [["minor dosimetric error"]]),
        table_item("table_cell_q0005", "In AAPM TG 100 Table II, what severity description is listed for rank 5?", "aapm_tg100_radiotherapy_quality_management", tg100, [["limited toxicity", "tumor underdose"]]),
        table_item("table_cell_q0006", "In AAPM TG 100 Table II, what occurrence description is listed for rank 8?", "aapm_tg100_radiotherapy_quality_management", tg100, [["repeated failures"]]),
        table_item("table_cell_q0007", "In AAPM TG 113 Table 1, what previous name is listed for the American College of Radiology QA center?", "aapm_report_113_physics_clinical_trials", tg113_qa, [["no name change"]]),
        table_item("table_cell_q0008", "In AAPM TG 113 Table 1, what previous organization is listed for IROC?", "aapm_report_113_physics_clinical_trials", tg113_qa, [["no previous organization"]]),
        table_item("table_cell_q0009", "In AAPM TG 113 Table 1, what grant-holder role is listed for the American College of Radiology?", "aapm_report_113_physics_clinical_trials", tg113_qa, [["grant holder"], ["IROC"]]),
        table_item("table_cell_q0010", "In AAPM TG 113 Table 1, what network role is listed for IROC?", "aapm_report_113_physics_clinical_trials", tg113_qa, [["integrated network"], ["clinical trial QA"]]),
        table_item("table_cell_q0011", "In AAPM TG 113 PET/CT quality-control table, what control is listed for blood glucose levels?", "aapm_report_113_physics_clinical_trials", tg113_pet, [["measure fasting blood glucose", "fasting blood glucose"], ["exclusion criteria"]]),
        table_item("table_cell_q0012", "In AAPM TG 113 PET/CT quality-control table, what control is listed for residual activity in a radiotracer syringe?", "aapm_report_113_physics_clinical_trials", tg113_pet, [["measure", "correct"], ["residual activity"]]),
        table_item("table_cell_q0013", "In AAPM TG 113 PET/CT quality-control table, what control is listed for decay correction errors?", "aapm_report_113_physics_clinical_trials", tg113_pet, [["synchronize", "synchronise"], ["scanner clock"]]),
        table_item("table_cell_q0014", "In AAPM TG 113 PET/CT quality-control table, what activity control is listed for metabolism levels?", "aapm_report_113_physics_clinical_trials", tg113_pet, [["limit physical activity"]]),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate cell-value table QA benchmark questions.")
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--output", type=Path, default=Path("evaluation/radiotherapy_table_cell_questions.json"))
    args = parser.parse_args()

    tables = load_tables(args.project_root)
    items = table_items()
    missing = sorted({str(item["asset_id"]) for item in items if item["asset_id"] not in tables})
    if missing:
        raise SystemExit("Missing current table assets: " + ", ".join(missing))
    for item in items:
        table = tables[str(item["asset_id"])]
        item["expected_page"] = int(table["page"])
        item["expected_page_window"] = 1
    write_json(args.output, items)
    print(f"Wrote {len(items)} OpenDataLoader table cell-value items to {args.output}")


if __name__ == "__main__":
    main()
