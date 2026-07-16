#!/usr/bin/env python
"""Audit whether frozen evaluation summaries agree with their per-item details.

This is a reproducibility check, not a performance evaluation. It verifies that
headline metrics, profile splits, abstention counts, and the statistical
uncertainty report can be regenerated from the committed per-item JSON output.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.evaluate_extractive_selectors import paired_comparison, profile_summary
from scripts.evaluate_statistical_uncertainty import run_uncertainty_analysis

EPSILON = 1e-12
LEGACY_ROUNDING_TOLERANCE = 0.5e-4
VALID_ABSTENTION_ERRORS = {"insufficient_evidence", "out_of_scope"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def close(left: float | None, right: float | None) -> bool:
    return left is not None and right is not None and abs(float(left) - float(right)) <= EPSILON


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "detail": detail})


def rate(values: list[bool]) -> float:
    return sum(bool(value) for value in values) / len(values) if values else 0.0


def profile_items(items: list[dict[str, Any]], profile: str) -> list[dict[str, Any]]:
    return [item for item in items if item.get("benchmark_profile") == profile]


def audit_strategy(strategy: dict[str, Any], checks: list[dict[str, Any]]) -> None:
    for name, summary in (strategy.get("strategies") or {}).items():
        details = summary.get("details") or []
        in_scope = [item for item in details if not item.get("expected_abstain")]
        ood = [item for item in details if item.get("expected_abstain")]
        doc_hits = [
            bool(item.get("expected_doc_id") in (item.get("retrieved_doc_ids") or [])[:5])
            for item in in_scope
        ]
        expected_doc_rate = rate(doc_hits)
        add_check(
            checks,
            f"strategy:{name}:document_recall_at_5",
            close(summary.get("doc_recall@5"), expected_doc_rate),
            f"summary={summary.get('doc_recall@5')}, details={expected_doc_rate}, n={len(in_scope)}",
        )
        counts = {
            "tp": sum(bool(item.get("predicted_abstain_proxy")) for item in ood),
            "fn": sum(not bool(item.get("predicted_abstain_proxy")) for item in ood),
            "fp": sum(bool(item.get("predicted_abstain_proxy")) for item in in_scope),
            "tn": sum(not bool(item.get("predicted_abstain_proxy")) for item in in_scope),
        }
        reported = summary.get("abstention") or {}
        add_check(
            checks,
            f"strategy:{name}:abstention_confusion",
            all(int(reported.get(key, -1)) == value for key, value in counts.items()),
            f"summary={reported}, details={counts}",
        )


def audit_gold(gold: dict[str, Any], checks: list[dict[str, Any]]) -> None:
    details = gold.get("details") or []
    add_check(
        checks,
        "gold:question_count",
        int(gold.get("questions", -1)) == len(details),
        f"summary={gold.get('questions')}, details={len(details)}",
    )
    for key, metric in (
        ("evidence_value_hit", "evidence_value_hit_rate"),
        ("answer_value_hit", "answer_value_hit_rate"),
        ("citation_present", "citation_present_rate"),
        ("gold_answer_success", "gold_answer_success_rate"),
    ):
        expected = rate([bool(item.get(key)) for item in details])
        add_check(checks, f"gold:{metric}", close(gold.get(metric), expected), f"summary={gold.get(metric)}, details={expected}")
    for profile, summary in (gold.get("by_benchmark_profile") or {}).items():
        items = profile_items(details, profile)
        expected = rate([bool(item.get("gold_answer_success")) for item in items])
        add_check(
            checks,
            f"gold:{profile}:success",
            int(summary.get("questions", -1)) == len(items) and close(summary.get("gold_answer_success_rate"), expected),
            f"summary_n={summary.get('questions')}, details_n={len(items)}, summary_rate={summary.get('gold_answer_success_rate')}, details_rate={expected}",
        )


def audit_generation(generation: dict[str, Any], checks: list[dict[str, Any]]) -> None:
    details = generation.get("details") or []
    add_check(
        checks,
        "generation:question_count",
        int(generation.get("questions", -1)) == len(details),
        f"summary={generation.get('questions')}, details={len(details)}",
    )
    for key, metric in (
        ("extractive_answer_value_hit", "extractive_answer_value_hit_rate"),
        ("evidence_only_value_hit", "evidence_only_value_hit_rate"),
        ("answer_synthesis_gap", "answer_synthesis_gap_rate"),
        ("retrieval_gap", "retrieval_gap_rate"),
    ):
        expected = rate([bool(item.get(key)) for item in details])
        add_check(
            checks,
            f"generation:{metric}",
            close(generation.get(metric), expected),
            f"summary={generation.get(metric)}, details={expected}",
        )
    for profile, summary in (generation.get("by_benchmark_profile") or {}).items():
        items = profile_items(details, profile)
        expected = rate([bool(item.get("extractive_answer_value_hit")) for item in items])
        add_check(
            checks,
            f"generation:{profile}:answer_hit",
            int(summary.get("questions", -1)) == len(items)
            and close(summary.get("extractive_answer_value_hit_rate"), expected),
            f"summary_n={summary.get('questions')}, details_n={len(items)}, summary_rate={summary.get('extractive_answer_value_hit_rate')}, details_rate={expected}",
        )


def audit_extractive_selectors(payload: dict[str, Any], checks: list[dict[str, Any]]) -> None:
    selectors = payload.get("selectors") or []
    selector_by_name = {str(item.get("selector")): item for item in selectors}
    for selector in selectors:
        name = str(selector.get("selector", "unknown"))
        details = selector.get("details") or []
        expected_answer = rate([bool(item.get("answer_value_hit")) for item in details])
        expected_citation = rate([bool(item.get("citation_present")) for item in details])
        add_check(
            checks,
            f"selector:{name}:summary",
            int(selector.get("questions", -1)) == len(details)
            and close(selector.get("answer_value_hit_rate"), expected_answer)
            and close(selector.get("citation_present_rate"), expected_citation),
            f"summary_n={selector.get('questions')}, details_n={len(details)}, answer={selector.get('answer_value_hit_rate')}/{expected_answer}, citation={selector.get('citation_present_rate')}/{expected_citation}",
        )
        expected_profiles = profile_summary(details)
        add_check(
            checks,
            f"selector:{name}:profiles",
            selector.get("by_benchmark_profile") == expected_profiles,
            "Profile-specific answer and citation rates were recomputed from frozen per-question details.",
        )

    baseline = selector_by_name.get("lexical")
    comparisons = payload.get("paired_comparisons") or []
    for comparison in comparisons:
        challenger = selector_by_name.get(str(comparison.get("challenger_selector")))
        expected = paired_comparison(baseline, challenger) if baseline and challenger else None
        add_check(
            checks,
            f"selector:paired:{comparison.get('challenger_selector')}",
            expected is not None and comparison == expected,
            "Paired selector comparison, interval, and McNemar result were deterministically recomputed from frozen per-question details.",
        )
def audit_contract(
    payload: dict[str, Any], checks: list[dict[str, Any]], prefix: str, count_key: str, metric_key: str
) -> None:
    details = payload.get("details") or []
    expected = rate([bool(item.get("task_success")) for item in details])
    add_check(
        checks,
        f"{prefix}:task_success",
        int(payload.get(count_key, -1)) == len(details) and close(payload.get(metric_key), expected),
        f"summary_n={payload.get(count_key)}, details_n={len(details)}, summary_rate={payload.get(metric_key)}, details_rate={expected}",
    )


def audit_table(table: dict[str, Any], checks: list[dict[str, Any]]) -> None:
    details = table.get("details") or []
    expected = rate([bool(item.get("cell_qa_success")) for item in details])
    add_check(
        checks,
        "table:cell_qa_success",
        int(table.get("questions", -1)) == len(details) and close(table.get("cell_qa_success_rate"), expected),
        f"summary_n={table.get('questions')}, details_n={len(details)}, summary_rate={table.get('cell_qa_success_rate')}, details_rate={expected}",
    )


def audit_quality(quality: dict[str, Any], checks: list[dict[str, Any]]) -> None:
    details = quality.get("details") or []
    in_scope = [
        item
        for item in details
        if not item.get("expected_abstain") and item.get("error_code") is None
    ]
    ood = [item for item in details if item.get("expected_abstain")]
    overlap = sum(float(item.get("grounded_token_overlap", 0.0)) for item in in_scope) / len(in_scope) if in_scope else 0.0
    reported_overlap = quality.get("mean_grounded_token_overlap")
    legacy_rounded_details = all(
        abs(float(item.get("grounded_token_overlap", 0.0)) - round(float(item.get("grounded_token_overlap", 0.0)), 4))
        <= EPSILON
        for item in in_scope
    )
    overlap_matches = close(reported_overlap, overlap)
    legacy_precision_match = (
        reported_overlap is not None
        and legacy_rounded_details
        and abs(float(reported_overlap) - overlap) <= LEGACY_ROUNDING_TOLERANCE
    )
    overlap_detail = f"summary={reported_overlap}, details={overlap}, n={len(in_scope)}"
    if legacy_precision_match and not overlap_matches:
        overlap_detail += "; legacy output stores per-item overlap rounded to four decimals while its aggregate used pre-round values"
    ood_success = rate([item.get("error_code") in VALID_ABSTENTION_ERRORS for item in ood])
    add_check(
        checks,
        "quality:grounded_token_overlap",
        overlap_matches or legacy_precision_match,
        overlap_detail,
    )
    add_check(
        checks,
        "quality:ood_refusal",
        close(quality.get("ood_abstention_success_rate"), ood_success),
        f"summary={quality.get('ood_abstention_success_rate')}, details={ood_success}, n={len(ood)}",
    )


def audit_uncertainty(eval_dir: Path, uncertainty: dict[str, Any], checks: list[dict[str, Any]]) -> None:
    recomputed = run_uncertainty_analysis(
        eval_dir,
        int((uncertainty.get("method") or {}).get("bootstrap_repetitions", 10_000)),
        int((uncertainty.get("method") or {}).get("random_seed", 20260714)),
    )
    add_check(
        checks,
        "uncertainty:deterministic_recompute",
        uncertainty == recomputed,
        "The persisted uncertainty JSON was recomputed from the frozen per-item evaluation outputs.",
    )


def audit(eval_dir: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    strategy = read_json(eval_dir / "strategy_eval_results.json")
    gold = read_json(eval_dir / "gold_answer_eval_results.json")
    generation = read_json(eval_dir / "answer_generation_eval_results.json")
    selector_ablation = read_json(eval_dir / "extractive_selector_ablation.json")
    table = read_json(eval_dir / "table_cell_qa_eval_results.json")
    agent = read_json(eval_dir / "agent_task_eval_results.json")
    mcp = read_json(eval_dir / "mcp_contract_eval_results.json")
    quality = read_json(eval_dir / "answer_quality_eval_results.json")
    uncertainty = read_json(eval_dir / "statistical_uncertainty.json")
    audit_strategy(strategy, checks)
    audit_gold(gold, checks)
    audit_generation(generation, checks)
    audit_extractive_selectors(selector_ablation, checks)
    audit_table(table, checks)
    audit_contract(agent, checks, "direct_skill", "tasks", "task_success_rate")
    audit_contract(mcp, checks, "mcp_stdio", "tasks", "task_success_rate")
    audit_quality(quality, checks)
    audit_uncertainty(eval_dir, uncertainty, checks)
    return {
        "audit_version": "1.1",
        "evaluation_dir": str(eval_dir),
        "checks": checks,
        "passed": sum(item["passed"] for item in checks),
        "failed": sum(not item["passed"] for item in checks),
        "ok": all(item["passed"] for item in checks),
        "scope_note": (
            "This audit checks internal consistency of automatic evaluation artifacts. "
            "It does not validate the benchmark labels, clinical correctness, or expert agreement."
        ),
    }


def write_markdown(result: dict[str, Any], output_path: Path) -> None:
    lines = [
        "# Evaluation Output Consistency Audit",
        "",
        result["scope_note"],
        "",
        f"- Passed: {result['passed']}",
        f"- Failed: {result['failed']}",
        "",
        "| Check | Status | Detail |",
        "|---|---|---|",
    ]
    for item in result["checks"]:
        status = "PASS" if item["passed"] else "FAIL"
        lines.append(f"| {item['name']} | {status} | {item['detail']} |")
    lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit consistency of frozen evaluation outputs.")
    parser.add_argument("--eval-dir", type=Path, default=Path("evaluation"))
    parser.add_argument("--output-json", type=Path, default=Path("evaluation/evaluation_output_audit.json"))
    parser.add_argument("--output-md", type=Path, default=Path("evaluation/evaluation_output_audit.md"))
    args = parser.parse_args()
    result = audit(args.eval_dir)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(result, args.output_md)
    print(json.dumps({"ok": result["ok"], "passed": result["passed"], "failed": result["failed"]}, ensure_ascii=False))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
