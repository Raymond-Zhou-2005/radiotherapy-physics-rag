#!/usr/bin/env python
"""Audit a public release directory for forbidden runtime artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List


FORBIDDEN_SUFFIXES = {
    ".pdf",
    ".pkl",
    ".npy",
    ".index",
    ".pyc",
    ".pyo",
    ".zip",
    ".pptx",
}

FORBIDDEN_PARTS = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

FORBIDDEN_RUNTIME_PREFIXES = (
    "reports/raw/",
    "parsed/",
    "chunks/",
    "index/metadata/",
    "index/sparse/",
    "index/dense/",
    "assets/extracted/",
    "chatgpt_knowledge/upload_files/",
)

FORBIDDEN_EXACT = {
    "reports/manifest.jsonl",
    "chatgpt_knowledge/upload_manifest.json",
}


def is_forbidden(rel: str, path: Path) -> bool:
    normalized = rel.replace("\\", "/")
    if any(part in path.parts for part in FORBIDDEN_PARTS):
        return True
    if normalized in FORBIDDEN_EXACT:
        return True
    if any(normalized.startswith(prefix) for prefix in FORBIDDEN_RUNTIME_PREFIXES):
        return not normalized.endswith(".gitkeep")
    return path.suffix.lower() in FORBIDDEN_SUFFIXES


def audit(root: Path) -> Dict:
    forbidden: List[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = str(path.relative_to(root))
        if is_forbidden(rel, path):
            forbidden.append(rel.replace("\\", "/"))
    required = [
        "README.md",
        "reports/starter_corpus_sources.json",
        "skills/radiotherapy-physics-rag/SKILL.md",
        "scripts/download_starter_corpus.py",
        "scripts/prepare_index.py",
        "scripts/evaluate_strategies.py",
        "scripts/evaluate_navigator.py",
        "scripts/evaluate_agent_skill.py",
        "evaluation/public_credible_questions.json",
        ".github/workflows/ci.yml",
    ]
    missing = [rel for rel in required if not (root / rel).exists()]
    return {
        "ok": not forbidden and not missing,
        "root": str(root),
        "forbidden_files": forbidden,
        "missing_required_files": missing,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit a clean public release directory.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    result = audit(args.root)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
