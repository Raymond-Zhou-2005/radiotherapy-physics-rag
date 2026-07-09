#!/usr/bin/env python
"""Build a clean public repository directory from the local runtime bundle."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT_FILES = [
    ".env.example",
    ".gitignore",
    ".mcp.json",
    ".zenodo.json",
    "CHANGELOG.md",
    "CITATION.cff",
    "CONTRIBUTING.md",
    "DELIVERABLE_SUMMARY.md",
    "LICENSE",
    "PRIVACY.md",
    "README.md",
    "SECURITY.md",
    "THIRD_PARTY_SOURCES.md",
    "constraints.txt",
    "project_brief.md",
    "pyproject.toml",
    "requirements.txt",
]

ROOT_DIRS = [
    ".agents",
    ".codex-plugin",
    ".github",
    "assets",
    "chatgpt_knowledge",
    "chunks",
    "evaluation",
    "examples",
    "experience",
    "index",
    "navigator",
    "parsed",
    "radiotherapy_physics_rag",
    "references",
    "reports",
    "schemas",
    "scripts",
    "skills",
    "src",
    "tests",
]

EXCLUDE_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "manuscript",
    "presentation",
}

EXCLUDE_PREFIXES = (
    "reports/raw/",
    "parsed/",
    "chunks/",
    "index/metadata/",
    "index/sparse/",
    "index/dense/",
    "assets/extracted/",
    "chatgpt_knowledge/upload_files/",
)

EXCLUDE_EXACT = {
    "reports/manifest.jsonl",
    "chatgpt_knowledge/upload_manifest.json",
    "experience/experience_memory.jsonl",
}

EXCLUDE_SUFFIXES = {".pdf", ".pkl", ".npy", ".index", ".pyc", ".pyo", ".pptx", ".zip"}


def normalize(rel: Path) -> str:
    return str(rel).replace("\\", "/")


def should_copy(path: Path, source_root: Path) -> bool:
    rel = path.relative_to(source_root)
    normalized = normalize(rel)
    if any(part in EXCLUDE_DIR_NAMES for part in rel.parts):
        return False
    if normalized in EXCLUDE_EXACT:
        return False
    if any(normalized.startswith(prefix) for prefix in EXCLUDE_PREFIXES):
        return normalized.endswith(".gitkeep")
    if path.suffix.lower() in EXCLUDE_SUFFIXES:
        return False
    return True


def assert_safe_output(source_root: Path, output_dir: Path) -> None:
    source_root = source_root.resolve()
    output_dir = output_dir.resolve()
    if output_dir == source_root:
        raise ValueError("Output directory must not be the source root.")
    if str(source_root).lower().startswith(str(output_dir).lower()):
        raise ValueError("Output directory must not contain the source root.")
    if output_dir.anchor and output_dir.name in {"", "\\", "/"}:
        raise ValueError("Refusing to write to a filesystem root.")


def copy_file(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def clear_output_dir(output_dir: Path) -> None:
    for child in output_dir.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()


def build_public_release(source_root: Path, output_dir: Path, force: bool = False) -> None:
    assert_safe_output(source_root, output_dir)
    if output_dir.exists():
        if not force:
            raise FileExistsError(f"{output_dir} already exists; pass --force to rebuild it.")
        clear_output_dir(output_dir)
    else:
        output_dir.mkdir(parents=True)

    for rel in ROOT_FILES:
        source = source_root / rel
        if source.exists() and should_copy(source, source_root):
            copy_file(source, output_dir / rel)

    for rel_dir in ROOT_DIRS:
        source_dir = source_root / rel_dir
        if not source_dir.exists():
            continue
        for source in source_dir.rglob("*"):
            if not source.is_file() or not should_copy(source, source_root):
                continue
            copy_file(source, output_dir / source.relative_to(source_root))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a clean public release directory.")
    parser.add_argument("--source-root", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    build_public_release(args.source_root, args.output_dir, force=args.force)
    print(f"Built public release at {args.output_dir}")


if __name__ == "__main__":
    main()
