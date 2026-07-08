import json
import os
import re
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HAS_LOCAL_INDEX = (PROJECT_ROOT / "index" / "metadata" / "chunk_metadata.jsonl").exists()
HAS_LOCAL_PDFS = bool(list((PROJECT_ROOT / "reports" / "raw").glob("*.pdf")))


def tracked_files(*paths: str) -> list[str]:
    completed = subprocess.run(
        ["git", "ls-files", "--", *paths],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return []
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def test_plugin_skill_metadata_exists():
    skill_md = PROJECT_ROOT / "skills" / "radiotherapy-physics-rag" / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    assert text.startswith("---")
    assert "name: radiotherapy-physics-rag" in text
    assert "radiotherapy physics" in text.lower()
    assert not (PROJECT_ROOT / "SKILL.md").exists()
    assert not (PROJECT_ROOT / "skill").exists()


def test_skill_schemas_are_valid_json():
    for rel in [
        "schemas/skill_input.schema.json",
        "schemas/skill_output.schema.json",
        "schemas/skill_error.schema.json",
    ]:
        payload = json.loads((PROJECT_ROOT / rel).read_text(encoding="utf-8"))
        assert payload["type"] == "object"
        assert "$schema" in payload

    input_schema = json.loads((PROJECT_ROOT / "schemas" / "skill_input.schema.json").read_text(encoding="utf-8"))
    assert input_schema["properties"]["retrieval_backend"]["enum"] == ["auto", "hybrid", "sparse", "routed"]


def test_error_schema_covers_ingestion_and_ocr_errors():
    payload = json.loads((PROJECT_ROOT / "schemas" / "skill_error.schema.json").read_text(encoding="utf-8"))
    codes = payload["properties"]["error"]["properties"]["code"]["enum"]
    assert "empty_corpus" in codes
    assert "ocr_required" in codes


def test_examples_cover_required_cases_without_http_api_examples():
    examples = {path.stem for path in (PROJECT_ROOT / "examples").glob("*.json")}
    assert {
        "empty_corpus_bootstrap",
        "build_index_from_pdfs",
        "evidence_query",
        "bundle_query",
        "extractive_answer_query",
        "insufficient_evidence_query",
        "invalid_document_scope",
        "inspect_pdfs",
        "mcp_query",
        "ocr_required",
    } <= examples
    assert "http_api_query" not in examples
    assert "http_upload_documents" not in examples
    assert "reindex_api" not in examples


def test_github_maturity_files_exist():
    for rel in [
        "pyproject.toml",
        "LICENSE",
        "PRIVACY.md",
        "THIRD_PARTY_SOURCES.md",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "CITATION.cff",
        ".github/workflows/ci.yml",
        "constraints.txt",
        ".codex-plugin/plugin.json",
        ".mcp.json",
        ".agents/plugins/marketplace.json",
    ]:
        assert (PROJECT_ROOT / rel).exists()
    assert not (PROJECT_ROOT / "Dockerfile").exists()
    assert not (PROJECT_ROOT / "docker-compose.yml").exists()
    assert not (PROJECT_ROOT / "scripts" / "serve_api.py").exists()
    assert not (PROJECT_ROOT / "requirements-dev.txt").exists()
    assert not (PROJECT_ROOT / "scripts" / "clean_hf_cache.py").exists()
    assert not (PROJECT_ROOT / "agents").exists()
    assert not (PROJECT_ROOT / "eval").exists()
    assert not (PROJECT_ROOT / "reports" / "pdf_text_readiness.json").exists()
    assert not (PROJECT_ROOT / ".github" / "ISSUE_TEMPLATE").exists()
    assert not (PROJECT_ROOT / ".github" / "workflows" / "release.yml").exists()


def test_maturity_scripts_exist():
    for rel in [
        "scripts/inspect_pdfs.py",
        "scripts/ocr_pdfs.py",
        "scripts/mcp_server.py",
        "scripts/add_documents.py",
        "scripts/build_corpus.py",
        "scripts/build_index.py",
        "scripts/build_sparse_index.py",
        "scripts/chunk_corpus.py",
        "scripts/parse_pdf.py",
        "scripts/plugin_doctor.py",
        "scripts/plugin_query.py",
        "scripts/evaluate.py",
        "scripts/evaluate_strategies.py",
        "scripts/extract_pdf_assets.py",
        "scripts/build_navigator.py",
        "scripts/build_chatgpt_knowledge.py",
        "scripts/generate_public_benchmark.py",
        "scripts/generate_asset_benchmark.py",
        "scripts/evaluate_navigator.py",
        "scripts/evaluate_agent_skill.py",
        "scripts/evaluate_answer_quality.py",
        "scripts/evaluate_asset_qa.py",
        "scripts/build_public_release.py",
        "scripts/audit_public_release.py",
    ]:
        assert (PROJECT_ROOT / rel).exists()


def test_codex_plugin_and_chatgpt_knowledge_files_exist():
    for rel in [
        ".codex-plugin/plugin.json",
        ".mcp.json",
        "skills/radiotherapy-physics-rag/SKILL.md",
        "chatgpt_knowledge/README.md",
        "chatgpt_knowledge/custom_gpt_instructions.md",
        "reports/starter_corpus_sources.json",
        "references/pdf_asset_extraction.md",
        "references/mcp_usage.md",
    ]:
        assert (PROJECT_ROOT / rel).exists()

    tracked_upload_files = tracked_files("chatgpt_knowledge/upload_files")
    assert not [path for path in tracked_upload_files if path.endswith(".md")]
    assert not (PROJECT_ROOT / "chatgpt_knowledge" / "citation_policy.md").exists()
    assert not (PROJECT_ROOT / "chatgpt_knowledge" / "source_manifest.md").exists()
    assert "chatgpt_knowledge/upload_manifest.json" not in tracked_files("chatgpt_knowledge/upload_manifest.json")


def test_redundant_design_notes_are_not_in_deliverable_package():
    for rel in [
        "references/rag_blueprint.md",
        "references/skill_positioning.md",
        "references/corpus_manifest.md",
    ]:
        assert not (PROJECT_ROOT / rel).exists()


def test_pyproject_console_scripts_are_declared_without_http_server():
    text = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for command in [
        "radiotherapy-rag",
        "radiotherapy-rag-add",
        "radiotherapy-rag-inspect-pdfs",
        "radiotherapy-rag-list",
        "radiotherapy-rag-mcp",
        "radiotherapy-rag-ocr",
        "radiotherapy-rag-prepare",
        "radiotherapy-rag-validate",
        "radiotherapy-rag-doctor",
        "radiotherapy-rag-extract-assets",
        "radiotherapy-rag-query",
        "radiotherapy-rag-chatgpt-knowledge",
        "radiotherapy-rag-generate-benchmark",
        "radiotherapy-rag-generate-asset-benchmark",
        "radiotherapy-rag-build-sparse",
        "radiotherapy-rag-build-public-release",
        "radiotherapy-rag-audit-public-release",
        "radiotherapy-rag-evaluate-navigator",
        "radiotherapy-rag-evaluate-agent-skill",
        "radiotherapy-rag-evaluate-answer-quality",
        "radiotherapy-rag-evaluate-asset-qa",
    ]:
        assert command in text
    assert "radiotherapy-rag-serve" not in text


def test_starter_corpus_sources_are_public_metadata():
    sources = json.loads((PROJECT_ROOT / "reports" / "starter_corpus_sources.json").read_text(encoding="utf-8"))
    assert len(sources) >= 49
    for record in sources:
        assert record["doc_id"]
        assert record["file"].startswith("reports/raw/")
        assert record["source_url"].startswith("https://")
        assert not Path(record["file"]).is_absolute()


def test_runtime_full_text_artifacts_are_not_committed():
    tracked = tracked_files(
        "reports/raw",
        "reports/manifest.jsonl",
        "parsed",
        "chunks",
        "index",
        "assets/extracted",
        "chatgpt_knowledge/upload_files",
        "chatgpt_knowledge/upload_manifest.json",
    )
    forbidden = [
        path
        for path in tracked
        if not path.endswith(".gitkeep")
        and (
            path.endswith(".pdf")
            or path.endswith(".jsonl")
            or path.endswith(".pkl")
            or path.endswith(".npy")
            or path.endswith(".index")
            or path.endswith("asset_manifest.json")
            or path.endswith("upload_manifest.json")
            or (path.startswith("chatgpt_knowledge/upload_files/") and path.endswith(".md"))
        )
    ]
    assert forbidden == []


def test_shareable_artifacts_do_not_contain_local_absolute_paths():
    absolute_windows_path = re.compile(r"[A-Za-z]:\\\\(?:Users|DKU|Research|RAG|[^\\\r\n]+\\\\)")
    rels = [
        "README.md",
        "references/starter_corpus.md",
        "reports/starter_corpus_sources.json",
    ]
    rels.extend(str(path.relative_to(PROJECT_ROOT)) for path in (PROJECT_ROOT / "chatgpt_knowledge").rglob("*.md"))
    for rel in rels:
        text = (PROJECT_ROOT / rel).read_text(encoding="utf-8", errors="ignore")
        assert not absolute_windows_path.search(text), rel


def test_local_runtime_outputs_are_ignored_by_gitignore():
    gitignore = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in [
        "reports/raw/*.pdf",
        "reports/manifest.jsonl",
        "parsed/*.jsonl",
        "chunks/*.jsonl",
        "index/metadata/*",
        "assets/extracted/asset_manifest.json",
        "chatgpt_knowledge/upload_files/*.md",
    ]:
        assert pattern in gitignore


def test_public_evaluation_files_exist_and_are_source_attributed():
    for rel in [
        "evaluation/README.md",
        "evaluation/public_credible_questions.json",
        "evaluation/public_credible_eval_results.md",
        "evaluation/corpus_baseline.json",
    ]:
        assert (PROJECT_ROOT / rel).exists()
    questions = json.loads((PROJECT_ROOT / "evaluation" / "public_credible_questions.json").read_text(encoding="utf-8"))
    assert len(questions) >= 250
    for item in questions:
        assert "qid" in item
        assert "question" in item
        assert "source_basis" in item
        assert "source_urls" in item


def test_run_skill_structured_error_helpers():
    from scripts.run_skill import build_error_response

    result = build_error_response(
        "out_of_scope",
        "outside",
        {"reason": "unit test"},
        mode="evidence",
        query="What is the capital of France?",
    )
    assert result["ok"] is False
    assert result["error"]["code"] == "out_of_scope"
    assert result["skill_name"] == "radiotherapy-physics-rag"


def test_run_skill_validates_mode_before_retrieval():
    from scripts.run_skill import SkillExecutionError, run_skill

    with pytest.raises(SkillExecutionError) as excinfo:
        run_skill(
            mode="chat",
            query="What does the corpus say about radiation oncology QA?",
            index_dir=PROJECT_ROOT / "index",
        )
    assert excinfo.value.code == "out_of_scope"


def test_run_skill_missing_index_error(tmp_path):
    from scripts.run_skill import SkillExecutionError, run_skill

    with pytest.raises(SkillExecutionError) as excinfo:
        run_skill(
            mode="evidence",
            query="What does AAPM Report 104 discuss about in-room kV imaging?",
            index_dir=tmp_path,
            report_id="aapm_report_104_kv_imaging_guidance",
        )
    assert excinfo.value.code == "missing_index"


def test_sparse_backend_runs_without_dense_index(tmp_path):
    from scripts.run_skill import run_skill
    from src.retrieval.sparse import SparseIndexer
    from src.utils import write_jsonl

    chunk = {
        "chunk_id": "qa_doc_c0001",
        "doc_id": "qa_doc",
        "title": "Synthetic QA Report",
        "section": "2. Quality Assurance",
        "subsection": "2.1 Chart Checks",
        "page_start": 4,
        "page_end": 5,
        "text": "Radiotherapy quality assurance includes chart checks, treatment record review, and planning review.",
        "token_count": 12,
        "source_path": "reports/raw/qa_doc.pdf",
        "tags": ["recommendation"],
        "chunk_kind": "standard",
        "parent_chunk_id": None,
    }
    index_dir = tmp_path / "index"
    write_jsonl(index_dir / "metadata" / "chunk_metadata.jsonl", [chunk])
    SparseIndexer().build([chunk], index_dir / "sparse")

    result = run_skill(
        mode="evidence",
        query="What does radiotherapy quality assurance include for chart checks?",
        index_dir=index_dir,
        report_id="qa_doc",
        retrieval_backend="sparse",
        evidence_top_k=1,
    )

    assert result["ok"] is True
    assert result["rag_pipeline"]["retrieval_backend"] == "sparse"
    assert not (index_dir / "dense" / "embeddings.npy").exists()
    assert result["evidence"][0]["page_range"] == "pp. 4-5"
    assert result["evidence"][0]["source_path"] == "reports/raw/qa_doc.pdf"
    assert result["citations"][0]["citation"].startswith("[E1] Synthetic QA Report")
    assert "chunk qa_doc_c0001" in result["citations"][0]["citation"]


def test_run_skill_invalid_report_scope_before_retrieval():
    if not HAS_LOCAL_INDEX:
        pytest.skip("local runtime index is generated by bootstrap commands and is not committed")
    from scripts.run_skill import SkillExecutionError, run_skill

    with pytest.raises(SkillExecutionError) as excinfo:
        run_skill(
            mode="evidence",
            query="What is the key recommendation?",
            index_dir=PROJECT_ROOT / "index",
            report_id="not_indexed",
        )
    assert excinfo.value.code == "out_of_scope"


def test_answer_mode_defaults_to_extractive_without_model_path():
    if not HAS_LOCAL_INDEX:
        pytest.skip("local runtime index is generated by bootstrap commands and is not committed")
    from scripts.run_skill import run_skill

    result = run_skill(
        mode="answer",
        query="What commissioning tests are recommended for computerized treatment planning systems used in radiation therapy?",
        index_dir=PROJECT_ROOT / "index",
        report_id="iaea_trs430_tps_commissioning_qa",
        answer_engine="extractive",
        retrieval_backend="sparse",
    )
    assert result["ok"] is True
    assert result["answer_engine"] == "extractive"
    assert result["used_evidence_ids"]


def test_python_facade_runs_evidence_query():
    if not HAS_LOCAL_INDEX:
        pytest.skip("local runtime index is generated by bootstrap commands and is not committed")
    from radiotherapy_physics_rag import query

    result = query(
        "What does IAEA TRS 398 cover about absorbed dose determination in external beam radiotherapy?",
        mode="evidence",
        index_dir=PROJECT_ROOT / "index",
        report_id="iaea_trs398_absorbed_dose_ebrt",
        evidence_top_k=2,
        retrieval_backend="sparse",
    )
    assert result["ok"] is True
    assert result["evidence"][0]["doc_id"] == "iaea_trs398_absorbed_dose_ebrt"
    assert result["rag_pipeline"]["retrieval_backend"] == "sparse"


def test_list_corpus_handles_public_source_package_without_runtime_artifacts():
    from scripts.list_corpus import list_corpus

    result = list_corpus(PROJECT_ROOT)
    assert result["ok"] is True
    if HAS_LOCAL_PDFS:
        assert result["pdf_count"] == len(list((PROJECT_ROOT / "reports" / "raw").glob("*.pdf")))
        assert result["manifest_count"] >= 1
        assert result["indexed_chunk_count"] >= 1
    else:
        assert result["pdf_count"] == 0
        assert result["manifest_count"] == 0
        assert result["indexed_chunk_count"] == 0


def test_inspect_pdfs_reports_text_readiness():
    if not HAS_LOCAL_PDFS:
        pytest.skip("local report PDFs are downloaded by bootstrap commands and are not committed")
    from scripts.inspect_pdfs import inspect_paths

    result = inspect_paths([PROJECT_ROOT / "reports" / "raw" / "aapm_report_104_kv_imaging_guidance.pdf"])
    assert result["ok"] is True
    assert result["pdf_count"] == 1
    assert result["results"][0]["page_count"] > 0


def test_downloader_retains_existing_manual_source(tmp_path):
    from scripts.download_starter_corpus import download_sources

    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    existing = reports_dir / "manual.pdf"
    existing.write_bytes(b"%PDF- fake test pdf")
    sources = tmp_path / "sources.json"
    sources.write_text(
        json.dumps(
            [
                {
                    "doc_id": "manual",
                    "file": "reports/raw/manual.pdf",
                    "title": "Manual source",
                    "source_url": "https://example.com/detail.asp?docid=1",
                    "role": "test",
                }
            ]
        ),
        encoding="utf-8",
    )
    result = download_sources(sources, reports_dir, force=True)
    assert result["ok"] is True
    assert result["results"][0]["status"] == "manual_source_retained"
    assert existing.read_bytes().startswith(b"%PDF-")


def test_ocr_missing_binary_returns_structured_error(tmp_path, monkeypatch):
    from scripts.ocr_pdfs import ocr_pdf

    monkeypatch.setenv("PATH", str(tmp_path))
    source_pdf = tmp_path / "source.pdf"
    source_pdf.write_bytes(b"%PDF- fake test pdf")
    result = ocr_pdf(source_pdf, tmp_path / "ocr.pdf")
    assert result["ok"] is False
    assert result["error"]["code"] == "ocr_required"


def test_mcp_server_can_be_constructed():
    from scripts.mcp_server import create_mcp

    mcp = create_mcp(PROJECT_ROOT / "index")
    assert mcp is not None


def test_medgemma_answer_engine_requires_model_path():
    if not HAS_LOCAL_INDEX:
        pytest.skip("local runtime index is generated by bootstrap commands and is not committed")
    from scripts.run_skill import SkillExecutionError, run_skill

    with pytest.raises(SkillExecutionError) as excinfo:
        run_skill(
            mode="answer",
            query="What physics responsibilities are discussed for clinical trials in AAPM TG 113?",
            index_dir=PROJECT_ROOT / "index",
            report_id="aapm_report_113_physics_clinical_trials",
            answer_engine="medgemma",
        )
    assert excinfo.value.code == "missing_model_path"


def test_validate_skill_package_passes():
    from scripts.validate_skill_package import validate

    result = validate(PROJECT_ROOT, check_sample_baseline=False)
    assert result["ok"] is True
    assert result["checks"]["starter_corpus_sources"] >= 49


@pytest.mark.skipif(os.getenv("RUN_SKILL_INTEGRATION") != "1", reason="live retrieval integration is opt-in")
def test_live_balanced_query_runs():
    from scripts.run_skill import run_skill

    result = run_skill(
        mode="evidence",
        query="What does AAPM Report 104 discuss about in-room kV imaging?",
        index_dir=PROJECT_ROOT / "index",
        report_id="aapm_report_104_kv_imaging_guidance",
        retrieval_backend="sparse",
    )
    assert result["ok"] is True
    assert result["evidence"][0]["doc_id"] == "aapm_report_104_kv_imaging_guidance"
