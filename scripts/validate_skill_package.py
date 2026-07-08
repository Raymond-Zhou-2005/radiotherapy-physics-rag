#!/usr/bin/env python
"""Validate that this repository is a deliverable radiotherapy physics RAG skill package."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List


REQUIRED_FILES = [
    ".github/workflows/ci.yml",
    ".gitignore",
    ".codex-plugin/plugin.json",
    ".mcp.json",
    "CHANGELOG.md",
    "CITATION.cff",
    "CONTRIBUTING.md",
    "LICENSE",
    "PRIVACY.md",
    "THIRD_PARTY_SOURCES.md",
    "constraints.txt",
    "pyproject.toml",
    "schemas/skill_input.schema.json",
    "schemas/skill_output.schema.json",
    "schemas/skill_error.schema.json",
    "scripts/add_documents.py",
    "scripts/build_corpus.py",
    "scripts/build_index.py",
    "scripts/build_sparse_index.py",
    "scripts/download_starter_corpus.py",
    "scripts/evaluate.py",
    "scripts/evaluate_strategies.py",
    "scripts/extract_pdf_assets.py",
    "scripts/build_navigator.py",
    "scripts/chunk_corpus.py",
    "scripts/inspect_pdfs.py",
    "scripts/list_corpus.py",
    "scripts/mcp_server.py",
    "scripts/ocr_pdfs.py",
    "scripts/parse_pdf.py",
    "scripts/plugin_doctor.py",
    "scripts/plugin_query.py",
    "scripts/run_skill.py",
    "scripts/init_corpus.py",
    "scripts/prepare_index.py",
    "scripts/validate_skill_package.py",
    "scripts/build_skill_bundle.py",
    "scripts/build_chatgpt_knowledge.py",
    "README.md",
    "references/document_onboarding.md",
    "references/mcp_usage.md",
    "references/model_setup.md",
    "references/output_contract.md",
    "references/pdf_asset_extraction.md",
    "references/starter_corpus.md",
    "requirements.txt",
    "SECURITY.md",
    "reports/starter_corpus_sources.json",
    "skills/radiotherapy-physics-rag/SKILL.md",
    "skills/radiotherapy-physics-navigator/SKILL.md",
    "chatgpt_knowledge/README.md",
    "chatgpt_knowledge/custom_gpt_instructions.md",
    "chatgpt_knowledge/starter_questions.md",
    "evaluation/README.md",
    "evaluation/public_credible_questions.json",
    "evaluation/public_credible_eval_results.md",
    "evaluation/corpus_baseline.json",
    ".agents/plugins/marketplace.json",
]

REQUIRED_DIRS = [
    "examples",
    ".github",
    ".agents",
    ".agents/plugins",
    "references",
    "evaluation",
    "assets",
    "assets/extracted",
    "chatgpt_knowledge/upload_files",
    "radiotherapy_physics_rag",
    "reports/raw",
    "parsed",
    "chunks",
    "index/dense",
    "index/sparse",
    "index/metadata",
    "navigator",
    "src",
    "scripts",
    "tests",
]

FORBIDDEN_PATHS = [
    "SKILL.md",
    "skill",
    "agents",
    ".github/ISSUE_TEMPLATE",
    ".github/workflows/release.yml",
    "Dockerfile",
    "docker-compose.yml",
    "requirements-dev.txt",
    "references/rag_blueprint.md",
    "references/skill_positioning.md",
    "references/corpus_manifest.md",
    "chatgpt_knowledge/citation_policy.md",
    "chatgpt_knowledge/source_manifest.md",
    "scripts/serve_api.py",
    "scripts/clean_hf_cache.py",
    "eval",
    "reports/pdf_text_readiness.json",
]

SPARSE_INDEX_FILES = [
    "index/sparse/bm25.pkl",
    "index/metadata/chunk_metadata.jsonl",
]

DENSE_INDEX_FILES = [
    "index/dense/embeddings.npy",
    "index/dense/chunk_ids.json",
    "index/dense/dense_meta.json",
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
    "chatgpt_knowledge/upload_manifest.json",
    "chatgpt_knowledge/upload_files/*.md",
]

EXPECTED_BASELINE = {
    "minimum_document_count": 16,
}


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def parse_frontmatter(skill_md: str) -> Dict[str, str]:
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    frontmatter = text[4:end].strip().splitlines()
    parsed = {}
    for line in frontmatter:
        match = re.match(r"^([A-Za-z0-9_-]+):\s*['\"]?(.*?)['\"]?$", line.strip())
        if match:
            parsed[match.group(1)] = match.group(2)
    return parsed


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def validate(skill_root: Path, require_index: bool = False, check_sample_baseline: bool = False) -> Dict[str, Any]:
    errors: List[str] = []
    warnings: List[str] = []
    checks: Dict[str, Any] = {}

    for rel in REQUIRED_FILES:
        if not (skill_root / rel).is_file():
            errors.append(f"Missing required file: {rel}")
    for rel in REQUIRED_DIRS:
        if not (skill_root / rel).is_dir():
            errors.append(f"Missing required directory: {rel}")
    for rel in FORBIDDEN_PATHS:
        if (skill_root / rel).exists():
            errors.append(f"Unexpected redundant or retired path: {rel}")

    skill_md = skill_root / "skills" / "radiotherapy-physics-rag" / "SKILL.md"
    if skill_md.exists():
        frontmatter = parse_frontmatter(skill_md)
        checks["skill_frontmatter"] = frontmatter
        if frontmatter.get("name") != "radiotherapy-physics-rag":
            errors.append("skills/radiotherapy-physics-rag/SKILL.md frontmatter name must be radiotherapy-physics-rag")
        if not frontmatter.get("description"):
            errors.append("skills/radiotherapy-physics-rag/SKILL.md frontmatter description is required")

    for rel in ["schemas/skill_input.schema.json", "schemas/skill_output.schema.json", "schemas/skill_error.schema.json"]:
        path = skill_root / rel
        if path.exists():
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"Invalid JSON schema {rel}: {exc}")

    pyproject = skill_root / "pyproject.toml"
    if pyproject.exists():
        text = pyproject.read_text(encoding="utf-8")
        for command in [
            "radiotherapy-rag",
            "radiotherapy-rag-add",
            "radiotherapy-rag-extract-assets",
            "radiotherapy-rag-inspect-pdfs",
            "radiotherapy-rag-list",
            "radiotherapy-rag-mcp",
            "radiotherapy-rag-ocr",
            "radiotherapy-rag-prepare",
            "radiotherapy-rag-validate",
            "radiotherapy-rag-doctor",
            "radiotherapy-rag-query",
            "radiotherapy-rag-chatgpt-knowledge",
            "radiotherapy-rag-build-navigator",
            "radiotherapy-rag-build-sparse",
            "radiotherapy-rag-evaluate-strategies",
        ]:
            if command not in text:
                errors.append(f"pyproject.toml is missing console script {command}")

    example_files = sorted((skill_root / "examples").glob("*.json")) if (skill_root / "examples").exists() else []
    checks["example_count"] = len(example_files)
    if len(example_files) < 10:
        errors.append("Expected at least 10 JSON examples covering CLI, MCP, upload, OCR, and error cases")
    for path in example_files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid example JSON {path.name}: {exc}")
            continue
        if "command" not in payload:
            errors.append(f"Example {path.name} must contain command")
        input_payload = payload.get("input", {})
        command = str(payload.get("command", ""))
        if "scripts/run_skill.py" in command and "query" not in input_payload:
            errors.append(f"Run-skill example {path.name} must contain input.query")

    if require_index:
        for rel in SPARSE_INDEX_FILES:
            if not (skill_root / rel).is_file():
                errors.append(f"Missing index artifact: {rel}")
        missing_dense = [rel for rel in DENSE_INDEX_FILES if not (skill_root / rel).is_file()]
        if missing_dense:
            warnings.append(
                "Dense index artifacts are absent; hybrid retrieval will fall back to sparse unless dense is built: "
                + ", ".join(missing_dense)
            )
        for rel in [
            "reports/manifest.jsonl",
            "assets/extracted/asset_manifest.json",
            "chatgpt_knowledge/upload_manifest.json",
            "navigator/SKILL.md",
            "navigator/entity_index.json",
            "navigator/all_chunks_index.jsonl",
        ]:
            if not (skill_root / rel).is_file():
                errors.append(f"Missing local runtime artifact: {rel}")
    else:
        committed_runtime = []
        for pattern in RUNTIME_ARTIFACT_PATTERNS:
            committed_runtime.extend(
                str(path.relative_to(skill_root))
                for path in skill_root.glob(pattern)
                if path.name != ".gitkeep"
            )
        if committed_runtime:
            warnings.append(
                "Local third-party corpus/runtime artifacts are present. Keep them out of the public repository unless you have redistribution rights: "
                + ", ".join(sorted(committed_runtime)[:20])
            )

    sources_path = skill_root / "reports" / "starter_corpus_sources.json"
    manifest_doc_ids: List[str] = []
    if sources_path.exists():
        try:
            sources = json.loads(sources_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid starter corpus source metadata: {exc}")
            sources = []
        checks["starter_corpus_sources"] = len(sources)
        if len(sources) < EXPECTED_BASELINE["minimum_document_count"]:
            errors.append(
                f"Expected at least {EXPECTED_BASELINE['minimum_document_count']} starter corpus source records, found {len(sources)}"
            )
        manifest_doc_ids = [str(item.get("doc_id")) for item in sources if item.get("doc_id")]
        if require_index:
            raw_pdf_count = len(list((skill_root / "reports" / "raw").glob("*.pdf")))
            checks["starter_corpus_pdf_count"] = raw_pdf_count
            if raw_pdf_count < EXPECTED_BASELINE["minimum_document_count"]:
                errors.append(f"Expected at least {EXPECTED_BASELINE['minimum_document_count']} starter corpus PDFs, found {raw_pdf_count}")

    if check_sample_baseline:
        metadata_path = skill_root / "index" / "metadata" / "chunk_metadata.jsonl"
        if not metadata_path.exists():
            errors.append("Cannot check sample baseline without index/metadata/chunk_metadata.jsonl. Build the local corpus first.")
            indexed_records = []
        else:
            indexed_records = read_jsonl(metadata_path)
        indexed_doc_ids = sorted({str(item.get("doc_id")) for item in indexed_records if item.get("doc_id")})
        checks["corpus_baseline"] = {
            "document_count": len(indexed_doc_ids),
            "total_indexed_chunks": len(indexed_records),
            "doc_ids": indexed_doc_ids,
        }
        if metadata_path.exists() and len(indexed_doc_ids) < EXPECTED_BASELINE["minimum_document_count"]:
            errors.append(
                f"Corpus document count is below minimum {EXPECTED_BASELINE['minimum_document_count']}: found {len(indexed_doc_ids)}"
            )
        runtime_pdf_doc_ids = sorted(path.stem for path in (skill_root / "reports" / "raw").glob("*.pdf"))
        checks["runtime_pdf_doc_ids"] = runtime_pdf_doc_ids
        if metadata_path.exists() and runtime_pdf_doc_ids and indexed_doc_ids != runtime_pdf_doc_ids:
            errors.append("Indexed doc_ids do not match runtime PDFs")

    asset_manifest_path = skill_root / "assets" / "extracted" / "asset_manifest.json"
    if asset_manifest_path.exists():
        try:
            asset_manifest = json.loads(asset_manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid PDF asset manifest JSON: {exc}")
            asset_manifest = {}
        documents = asset_manifest.get("documents", []) if isinstance(asset_manifest, dict) else []
        total_tables = sum(int(item.get("table_count", 0)) for item in documents)
        total_images = sum(int(item.get("image_count", 0)) for item in documents)
        asset_doc_ids = [str(item.get("doc_id")) for item in documents if item.get("doc_id")]
        checks["pdf_asset_manifest"] = {
            "document_count": len(documents),
            "table_count": total_tables,
            "image_count": total_images,
            "doc_ids": asset_doc_ids,
        }
        if check_sample_baseline:
            indexed_doc_ids_for_assets = checks.get("corpus_baseline", {}).get("doc_ids", [])
            if len(documents) < EXPECTED_BASELINE["minimum_document_count"]:
                errors.append(
                    f"PDF asset manifest document count is below minimum {EXPECTED_BASELINE['minimum_document_count']}: found {len(documents)}"
                )
            if indexed_doc_ids_for_assets and sorted(asset_doc_ids) != sorted(indexed_doc_ids_for_assets):
                errors.append("PDF asset manifest doc_ids do not match indexed runtime corpus")
            if total_tables <= 0:
                errors.append("PDF asset manifest contains no extracted tables")
            if total_images <= 0:
                errors.append("PDF asset manifest contains no extracted images")
            for item in documents:
                output = item.get("output")
                if output and not (skill_root / output).is_file():
                    errors.append(f"PDF asset output is missing: {output}")
    elif check_sample_baseline:
        errors.append("Missing assets/extracted/asset_manifest.json")

    dependency_checks = {
        "fitz": module_available("fitz"),
        "numpy": module_available("numpy"),
        "rank_bm25": module_available("rank_bm25"),
        "sentence_transformers": module_available("sentence_transformers"),
        "transformers": module_available("transformers"),
        "faiss": module_available("faiss"),
        "mcp": module_available("mcp"),
        "jsonschema": module_available("jsonschema"),
    }
    checks["dependencies"] = dependency_checks
    if not dependency_checks["fitz"]:
        warnings.append("PyMuPDF/fitz is not installed; PDF parsing and prepare_index.py require pip install -r requirements.txt.")
    if not dependency_checks["numpy"]:
        warnings.append("numpy is not installed; dense index loading requires pip install -r requirements.txt.")
    if not dependency_checks["rank_bm25"]:
        warnings.append("rank_bm25 is not installed; existing index/sparse/bm25.pkl may not unpickle. Run pip install -r requirements.txt.")
    for optional in ["sentence_transformers", "transformers", "faiss"]:
        if not dependency_checks[optional]:
            warnings.append(f"{optional} is not installed; live dense/rerank/model execution may use fallbacks or be unavailable.")
    for integration in ["mcp", "jsonschema"]:
        if not dependency_checks[integration]:
            warnings.append(f"{integration} is not installed; plugin MCP/schema validation surfaces may be unavailable.")

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "checks": checks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the radiotherapy physics RAG skill package.")
    parser.add_argument("--skill-root", type=Path, default=Path("."))
    parser.add_argument("--require-index", action="store_true", help="Require locally built index artifacts.")
    parser.add_argument("--check-sample-baseline", action="store_true", help="Check the locally built starter corpus baseline.")
    args = parser.parse_args()

    result = validate(
        args.skill_root.resolve(),
        require_index=args.require_index,
        check_sample_baseline=args.check_sample_baseline,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
