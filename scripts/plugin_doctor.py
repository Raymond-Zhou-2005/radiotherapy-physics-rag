#!/usr/bin/env python
"""Check whether the local plugin package is ready to use."""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.list_corpus import list_corpus

REQUIRED_FILES = [
    ".codex-plugin/plugin.json",
    ".mcp.json",
    "skills/radiotherapy-physics-rag/SKILL.md",
    "README.md",
    "pyproject.toml",
    "reports/starter_corpus_sources.json",
]

RUNTIME_FILES = [
    "reports/manifest.jsonl",
    "assets/extracted/asset_manifest.json",
    "index/metadata/chunk_metadata.jsonl",
    "index/sparse/bm25.pkl",
]

OPTIONAL_DENSE_FILES = [
    "index/dense/dense_meta.json",
    "index/dense/embeddings.npy",
    "index/dense/chunk_ids.json",
    "index/dense/faiss.index",
]

MODULES = [
    "opendataloader_pdf",
    "numpy",
    "rank_bm25",
    "sentence_transformers",
    "transformers",
    "faiss",
    "mcp",
    "jsonschema",
]


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def rel_status(root: Path, rels: Iterable[str]) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for rel in rels:
        path = root / rel
        result[rel] = {"exists": path.exists(), "bytes": path.stat().st_size if path.exists() else 0}
    return result


def doctor(root: Path) -> Dict[str, Any]:
    root = root.resolve()
    required = rel_status(root, REQUIRED_FILES)
    runtime = rel_status(root, RUNTIME_FILES)
    dense = rel_status(root, OPTIONAL_DENSE_FILES)
    modules = {name: module_available(name) for name in MODULES}
    java_available = shutil.which("java") is not None
    corpus = list_corpus(root)
    dense_meta = read_json(root / "index" / "dense" / "dense_meta.json")
    asset_manifest = read_json(root / "assets" / "extracted" / "asset_manifest.json")

    errors = []
    warnings = []
    for rel, status in required.items():
        if not status["exists"]:
            errors.append({"code": "missing_required_file", "path": rel})

    runtime_ready = all(item["exists"] for item in runtime.values())
    if not runtime_ready:
        warnings.append(
            {
                "code": "runtime_artifacts_missing",
                "message": "The public source package is present, but the local corpus/index has not been built. Run download_starter_corpus.py, prepare_index.py, extract_pdf_assets.py, and build_chatgpt_knowledge.py.",
            }
        )

    if runtime_ready and not modules.get("rank_bm25") and not (root / "index" / "sparse" / "bm25.pkl").exists():
        errors.append({"code": "missing_sparse_runtime", "message": "BM25 retrieval needs rank-bm25 or an existing sparse index."})

    if not modules.get("sentence_transformers"):
        warnings.append({"code": "dense_runtime_unavailable", "message": "Dense retrieval will fall back or require model dependencies."})
    if runtime_ready and not all(item["exists"] for item in dense.values()):
        warnings.append({"code": "dense_index_incomplete", "message": "Hybrid retrieval may be unavailable; sparse retrieval can still work."})
    if not modules.get("opendataloader_pdf"):
        warnings.append({"code": "pdf_parser_unavailable", "message": "OpenDataLoader PDF is not installed; run pip install -r requirements.txt."})
    if not java_available:
        warnings.append({"code": "java_unavailable", "message": "Java 11 or newer is required to parse or inspect PDFs with OpenDataLoader."})

    return {
        "ok": not errors,
        "source_package_ok": not errors,
        "runtime_ready": runtime_ready,
        "root": str(root),
        "python": {"executable": sys.executable, "version": platform.python_version(), "platform": platform.platform()},
        "required_files": required,
        "runtime_files": runtime,
        "optional_dense_files": dense,
        "modules": modules,
        "java_available": java_available,
        "dense_meta": dense_meta,
        "asset_manifest": {
            "document_count": len(asset_manifest.get("documents", [])),
            "table_count": sum(int(item.get("table_count", 0)) for item in asset_manifest.get("documents", [])),
            "image_count": sum(int(item.get("image_count", 0)) for item in asset_manifest.get("documents", [])),
        },
        "corpus": corpus,
        "errors": errors,
        "warnings": warnings,
        "usage": {
            "sparse_query": "python scripts/plugin_query.py --retrieval-backend sparse \"What does the corpus say about radiation oncology QA?\"",
            "auto_query": "python scripts/plugin_query.py --retrieval-backend auto \"What does the corpus say about absorbed dose determination in external beam radiotherapy?\"",
            "chatgpt_knowledge": "python scripts/build_chatgpt_knowledge.py --root .",
            "extract_assets": "python scripts/extract_pdf_assets.py reports/raw --output-dir assets/extracted",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check local plugin readiness.")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    result = doctor(args.root)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
