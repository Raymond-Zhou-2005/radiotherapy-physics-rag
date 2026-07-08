#!/usr/bin/env python
"""Build a distributable zip bundle for the radiotherapy physics RAG skill package."""

from __future__ import annotations

import argparse
import fnmatch
import json
import sys
import zipfile
from pathlib import Path

# Allow `python scripts/<name>.py` to import sibling validation code.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.validate_skill_package import validate


EXCLUDE_PARTS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "dist",
    "radiotherapy_physics_rag.egg-info",
}

EXCLUDE_PATTERNS = [
    "*.pyc",
    "*.pyo",
    "*.zip",
    ".DS_Store",
]

RUNTIME_ARTIFACT_PATTERNS = [
    "reports/raw/*.pdf",
    "reports/manifest.jsonl",
    "parsed/*.jsonl",
    "chunks/*.jsonl",
    "index/dense/*",
    "index/sparse/*",
    "index/metadata/*",
    "assets/extracted/*.jsonl",
    "assets/extracted/asset_manifest.json",
    "assets/extracted/images/*",
    "chatgpt_knowledge/upload_manifest.json",
    "chatgpt_knowledge/upload_files/*.md",
]


def should_include(path: Path, skill_root: Path, output: Path, include_runtime_artifacts: bool = False) -> bool:
    try:
        rel = path.relative_to(skill_root)
    except ValueError:
        return False
    if path.resolve() == output.resolve():
        return False
    if any(part in EXCLUDE_PARTS for part in rel.parts):
        return False
    rel_posix = rel.as_posix()
    if not include_runtime_artifacts:
        for pattern in RUNTIME_ARTIFACT_PATTERNS:
            if fnmatch.fnmatch(rel_posix, pattern):
                return path.name == ".gitkeep"
    return not any(fnmatch.fnmatch(path.name, pattern) for pattern in EXCLUDE_PATTERNS)


def build_bundle(
    skill_root: Path,
    output: Path,
    skip_validate: bool = False,
    include_runtime_artifacts: bool = False,
) -> dict:
    skill_root = skill_root.resolve()
    output = output.resolve()

    if not skip_validate:
        validation = validate(skill_root, require_index=False, check_sample_baseline=False)
        if not validation["ok"]:
            return {
                "ok": False,
                "output": str(output),
                "validation": validation,
            }

    output.parent.mkdir(parents=True, exist_ok=True)
    file_count = 0
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(skill_root.rglob("*")):
            if not path.is_file():
                continue
            if not should_include(path, skill_root, output, include_runtime_artifacts=include_runtime_artifacts):
                continue
            archive.write(path, path.relative_to(skill_root).as_posix())
            file_count += 1

    return {
        "ok": True,
        "output": str(output),
        "file_count": file_count,
        "include_runtime_artifacts": include_runtime_artifacts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the radiotherapy physics RAG skill bundle.")
    parser.add_argument("--skill-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path("dist/radiotherapy-physics-rag.zip"))
    parser.add_argument("--skip-validate", action="store_true")
    parser.add_argument("--include-runtime-artifacts", dest="include_runtime_artifacts", action="store_true", help="Include local PDFs, parsed files, chunks, index files, extracted assets, and ChatGPT upload files.")
    parser.add_argument("--exclude-runtime-artifacts", dest="include_runtime_artifacts", action="store_false", help="Build the public lightweight skill without local corpus/index artifacts. This is the default.")
    parser.set_defaults(include_runtime_artifacts=False)
    args = parser.parse_args()

    result = build_bundle(
        args.skill_root,
        args.output,
        skip_validate=args.skip_validate,
        include_runtime_artifacts=args.include_runtime_artifacts,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
