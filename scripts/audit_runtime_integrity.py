#!/usr/bin/env python
"""Fingerprint a full local runtime and verify its evidence dependencies.

The public source package cannot contain the PDFs, indexes, or model cache used
in a particular experiment. This local-only audit records their identities and
checks that frozen evaluation outputs refer to a coherent runtime. It is a
reproducibility check, not an independent benchmark or clinical validation.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RUNTIME_FILES = (
    "reports/starter_corpus_sources.json",
    "reports/manifest.jsonl",
    "reports/provenance_manifest.json",
    "index/dense/dense_meta.json",
    "index/dense/embeddings.npy",
    "index/dense/chunk_ids.json",
    "index/metadata/chunk_metadata.jsonl",
    "index/sparse/bm25.pkl",
    "assets/extracted/asset_manifest.json",
    "chatgpt_knowledge/upload_manifest.json",
    "evaluation/evaluation_output_audit.json",
    "evaluation/statistical_uncertainty.json",
)

DEPENDENCIES = (
    "opendataloader-pdf",
    "faiss-cpu",
    "huggingface-hub",
    "numpy",
    "rank-bm25",
    "sentence-transformers",
    "torch",
    "transformers",
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "detail": detail})


def distribution_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for package in DEPENDENCIES:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "not_installed"
    return versions


def model_cache_directory(model_name: str, hub_cache: Path) -> Path:
    return hub_cache / f"models--{model_name.replace('/', '--')}"


def resolve_hub_cache(explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit
    if value := os.environ.get("HF_HUB_CACHE"):
        return Path(value)
    if value := os.environ.get("HF_HOME"):
        return Path(value) / "hub"
    return Path.home() / ".cache" / "huggingface" / "hub"


def local_model_revision(model_name: str, hub_cache: Path) -> dict[str, Any]:
    directory = model_cache_directory(model_name, hub_cache)
    main_ref = directory / "refs" / "main"
    revision = main_ref.read_text(encoding="utf-8").strip() if main_ref.exists() else None
    snapshots_dir = directory / "snapshots"
    snapshots = sorted(path.name for path in snapshots_dir.glob("*") if path.is_dir()) if snapshots_dir.exists() else []
    return {
        "model_name": model_name,
        "hub_cache_present": directory.exists(),
        "local_main_revision": revision,
        "local_snapshots": snapshots,
    }


def audit_runtime(root: Path, hub_cache: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    checks: list[dict[str, Any]] = []
    file_hashes: dict[str, str | None] = {}
    for rel in RUNTIME_FILES:
        path = root / rel
        file_hashes[rel] = sha256_file(path) if path.exists() else None
        add_check(checks, f"required_runtime_file:{rel}", path.exists(), "present" if path.exists() else "missing")

    source_path = root / "reports/starter_corpus_sources.json"
    manifest_path = root / "reports/manifest.jsonl"
    provenance_path = root / "reports/provenance_manifest.json"
    sources = read_json(source_path) if source_path.exists() else []
    manifest = read_jsonl(manifest_path)
    provenance = read_json(provenance_path) if provenance_path.exists() else {}
    source_by_id = {str(item.get("doc_id")): item for item in sources if item.get("doc_id")}
    manifest_by_id = {str(item.get("doc_id")): item for item in manifest if item.get("doc_id")}
    provenance_by_id = {
        str(item.get("doc_id")): item
        for item in (provenance.get("documents") or [])
        if item.get("doc_id")
    }
    source_ids = set(source_by_id)
    manifest_ids = set(manifest_by_id)
    provenance_ids = set(provenance_by_id)
    add_check(
        checks,
        "corpus:source_manifest_identity",
        source_ids == manifest_ids == provenance_ids,
        f"source={len(source_ids)}, manifest={len(manifest_ids)}, provenance={len(provenance_ids)}",
    )

    pdf_checks = 0
    pdf_passes = 0
    for doc_id in sorted(source_ids):
        source = source_by_id[doc_id]
        record = manifest_by_id.get(doc_id)
        provenance_record = provenance_by_id.get(doc_id)
        pdf_path = root / Path(str(source.get("file") or ""))
        present = pdf_path.exists() and pdf_path.is_file()
        expected_hash = str((record or {}).get("sha256") or "")
        observed_hash = sha256_file(pdf_path) if present else None
        provenance_hash = str(((provenance_record or {}).get("local_runtime") or {}).get("sha256") or "")
        passed = present and bool(expected_hash) and observed_hash == expected_hash == provenance_hash
        pdf_checks += 1
        pdf_passes += int(passed)
        add_check(
            checks,
            f"pdf:{doc_id}",
            passed,
            f"present={present}, manifest_hash_match={observed_hash == expected_hash if observed_hash else False}, "
            f"provenance_hash_match={observed_hash == provenance_hash if observed_hash else False}",
        )

    chunk_records = read_jsonl(root / "index/metadata/chunk_metadata.jsonl")
    chunk_doc_ids = {str(item.get("doc_id")) for item in chunk_records if item.get("doc_id")}
    add_check(
        checks,
        "chunks:all_manifest_documents_present",
        chunk_doc_ids == manifest_ids,
        f"chunk_documents={len(chunk_doc_ids)}, manifest_documents={len(manifest_ids)}, chunks={len(chunk_records)}",
    )

    dense_meta_path = root / "index/dense/dense_meta.json"
    dense_meta = read_json(dense_meta_path) if dense_meta_path.exists() else {}
    embedding_model = str(dense_meta.get("embedding_model_name") or "")
    embedding_backend = str(dense_meta.get("embedding_backend") or "")
    add_check(
        checks,
        "dense_index:semantic_backend",
        embedding_backend == "sentence_transformers" and bool(embedding_model),
        f"backend={embedding_backend or 'missing'}, model={embedding_model or 'missing'}",
    )

    asset_path = root / "assets/extracted/asset_manifest.json"
    assets = read_json(asset_path) if asset_path.exists() else {}
    asset_documents = assets.get("documents") or []
    asset_ids = {str(item.get("doc_id")) for item in asset_documents if item.get("doc_id")}
    add_check(
        checks,
        "assets:all_manifest_documents_present",
        asset_ids == manifest_ids,
        f"asset_documents={len(asset_ids)}, manifest_documents={len(manifest_ids)}",
    )

    upload_path = root / "chatgpt_knowledge/upload_manifest.json"
    uploads = read_json(upload_path) if upload_path.exists() else {}
    upload_ids = {str(item.get("doc_id")) for item in (uploads.get("upload_files") or []) if item.get("doc_id")}
    add_check(
        checks,
        "knowledge_uploads:all_manifest_documents_present",
        upload_ids == manifest_ids,
        f"upload_documents={len(upload_ids)}, manifest_documents={len(manifest_ids)}",
    )

    evaluation_audit_path = root / "evaluation/evaluation_output_audit.json"
    evaluation_audit = read_json(evaluation_audit_path) if evaluation_audit_path.exists() else {}
    add_check(
        checks,
        "evaluation:frozen_output_audit",
        evaluation_audit.get("ok") is True and int(evaluation_audit.get("failed", -1)) == 0,
        f"ok={evaluation_audit.get('ok')}, failed={evaluation_audit.get('failed')}",
    )

    hub_cache_path = resolve_hub_cache(hub_cache)
    reranker_model = "BAAI/bge-reranker-base"
    models = {
        "embedding": local_model_revision(embedding_model, hub_cache_path) if embedding_model else {},
        "reranker": local_model_revision(reranker_model, hub_cache_path),
    }
    for role, model in models.items():
        add_check(
            checks,
            f"model_cache:{role}",
            bool(model.get("local_main_revision")),
            f"model={model.get('model_name')}, revision={model.get('local_main_revision') or 'missing'}",
        )

    summary = {
        "source_records": len(source_ids),
        "manifest_records": len(manifest_ids),
        "pdfs_verified": pdf_passes,
        "pdfs_checked": pdf_checks,
        "indexed_chunks": len(chunk_records),
        "asset_tables": sum(int(item.get("table_count") or 0) for item in asset_documents),
        "asset_images": sum(int(item.get("image_count") or 0) for item in asset_documents),
        "knowledge_upload_files": len(upload_ids),
    }
    return {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "root_name": root.name,
        "scope_note": (
            "This local audit fingerprints the observed corpus, index, model-cache revisions, environment, and frozen "
            "automatic evaluation artifacts. It does not verify publisher rights, benchmark-label validity, clinical "
            "correctness, expert agreement, or independent generalization."
        ),
        "summary": summary,
        "runtime_file_sha256": file_hashes,
        "dense_index": dense_meta,
        "models": models,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "java_executable": shutil.which("java"),
            "dependencies": distribution_versions(),
        },
        "checks": checks,
        "passed": sum(item["passed"] for item in checks),
        "failed": sum(not item["passed"] for item in checks),
        "ok": all(item["passed"] for item in checks),
    }


def write_markdown(result: dict[str, Any], output_path: Path) -> None:
    summary = result["summary"]
    lines = [
        "# Local Runtime Integrity Audit",
        "",
        result["scope_note"],
        "",
        f"- Status: {'PASS' if result['ok'] else 'FAIL'}",
        f"- Passed checks: {result['passed']}",
        f"- Failed checks: {result['failed']}",
        f"- Source/manifest records: {summary['source_records']} / {summary['manifest_records']}",
        f"- PDF SHA-256 checks: {summary['pdfs_verified']} / {summary['pdfs_checked']}",
        f"- Indexed chunks: {summary['indexed_chunks']}",
        f"- Extracted assets: {summary['asset_tables']} tables, {summary['asset_images']} images",
        f"- Knowledge upload files: {summary['knowledge_upload_files']}",
        "",
        "## Model Revisions",
        "",
        "| Role | Model | Local revision |",
        "|---|---|---|",
    ]
    for role, model in result["models"].items():
        lines.append(f"| {role} | {model.get('model_name', 'missing')} | {model.get('local_main_revision') or 'missing'} |")
    lines.extend(["", "## Checks", "", "| Check | Status | Detail |", "|---|---|---|"])
    for check in result["checks"]:
        lines.append(f"| {check['name']} | {'PASS' if check['passed'] else 'FAIL'} | {check['detail']} |")
    lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fingerprint and audit a full local radiotherapy RAG runtime.")
    parser.add_argument("--root", type=Path, default=PROJECT_ROOT)
    parser.add_argument("--hub-cache", type=Path, default=None)
    parser.add_argument("--output-json", type=Path, default=Path("evaluation/runtime_integrity_audit.json"))
    parser.add_argument("--output-md", type=Path, default=Path("evaluation/runtime_integrity_audit.md"))
    args = parser.parse_args()
    result = audit_runtime(args.root, args.hub_cache)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(result, args.output_md)
    print(json.dumps({"ok": result["ok"], "passed": result["passed"], "failed": result["failed"]}, ensure_ascii=False))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
