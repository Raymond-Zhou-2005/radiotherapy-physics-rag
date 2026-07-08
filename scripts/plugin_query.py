#!/usr/bin/env python
"""Small CLI wrapper intended for Codex plugin and human use."""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.run_skill import ERROR_EXIT_CODES, RETRIEVAL_BACKENDS, SkillExecutionError, build_error_response, run_skill
from src.utils import write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Query the local radiotherapy physics evidence agent.")
    parser.add_argument("question", nargs="*", help="Question to ask. If omitted, --query or stdin is used.")
    parser.add_argument("--query", type=str, default="")
    parser.add_argument("--mode", choices=["evidence", "bundle", "answer"], default="evidence")
    parser.add_argument("--report-id", type=str, default=None)
    parser.add_argument("--index-dir", type=Path, default=PROJECT_ROOT / "index")
    parser.add_argument("--evidence-top-k", type=int, default=None)
    parser.add_argument("--answer-engine", choices=["auto", "extractive", "medgemma"], default="auto")
    parser.add_argument("--retrieval-backend", choices=sorted(RETRIEVAL_BACKENDS), default="auto")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    query = args.query or " ".join(args.question).strip()
    if not query and not sys.stdin.isatty():
        query = sys.stdin.read().strip()

    exit_code = 0
    try:
        result = run_skill(
            mode=args.mode,
            query=query,
            index_dir=args.index_dir,
            report_id=args.report_id,
            evidence_top_k=args.evidence_top_k,
            answer_engine=args.answer_engine,
            retrieval_backend=args.retrieval_backend,
        )
    except SkillExecutionError as exc:
        result = build_error_response(exc.code, exc.message, exc.details, args.mode, query)
        exit_code = ERROR_EXIT_CODES.get(exc.code, 1)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        result = build_error_response(
            "runtime_failure",
            str(exc),
            {"exception_type": exc.__class__.__name__, "traceback": traceback.format_exc(limit=8)},
            args.mode,
            query,
        )
        exit_code = ERROR_EXIT_CODES["runtime_failure"]

    if args.output:
        write_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
