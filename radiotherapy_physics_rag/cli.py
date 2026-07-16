"""Console-script entrypoints for packaged installs."""

from __future__ import annotations

from scripts.add_documents import main as add_documents_main
from scripts.analyze_failure_taxonomy import main as analyze_failure_taxonomy_main
from scripts.audit_evaluation_outputs import main as audit_evaluation_outputs_main
from scripts.audit_public_release import main as audit_public_release_main
from scripts.audit_runtime_integrity import main as audit_runtime_integrity_main
from scripts.build_chatgpt_knowledge import main as build_chatgpt_knowledge_main
from scripts.build_navigator import main as build_navigator_main
from scripts.build_paper_experiment_matrix import main as build_paper_experiment_matrix_main
from scripts.build_provenance_manifest import main as build_provenance_manifest_main
from scripts.build_public_release import main as build_public_release_main
from scripts.build_skill_bundle import main as build_bundle_main
from scripts.build_sparse_index import main as build_sparse_index_main
from scripts.compare_mcq_answer_methods import main as compare_mcq_answer_methods_main
from scripts.download_starter_corpus import main as download_corpus_main
from scripts.evaluate_ablation import main as evaluate_ablation_main
from scripts.evaluate_agent_skill import main as evaluate_agent_skill_main
from scripts.evaluate_agent_tasks import main as evaluate_agent_tasks_main
from scripts.evaluate_answer_generation import main as evaluate_answer_generation_main
from scripts.evaluate_answer_quality import main as evaluate_answer_quality_main
from scripts.evaluate_asset_qa import main as evaluate_asset_qa_main
from scripts.evaluate_extractive_selectors import main as evaluate_extractive_selectors_main
from scripts.evaluate_gold_answers import main as evaluate_gold_answers_main
from scripts.evaluate_mcp_contract import main as evaluate_mcp_contract_main
from scripts.evaluate_navigator import main as evaluate_navigator_main
from scripts.evaluate_public_mcq_exam import main as evaluate_public_mcq_exam_main
from scripts.evaluate_statistical_uncertainty import main as evaluate_statistical_uncertainty_main
from scripts.evaluate_strategies import main as evaluate_strategies_main
from scripts.evaluate_table_cell_qa import main as evaluate_table_cell_qa_main
from scripts.extract_pdf_assets import main as extract_assets_main
from scripts.generate_agent_task_benchmark import main as generate_agent_task_benchmark_main
from scripts.generate_asset_benchmark import main as generate_asset_benchmark_main
from scripts.generate_gold_answer_benchmark import main as generate_gold_answer_benchmark_main
from scripts.generate_public_benchmark import main as generate_public_benchmark_main
from scripts.generate_table_cell_benchmark import main as generate_table_cell_benchmark_main
from scripts.import_public_medical_physics_exam import main as import_public_medical_physics_exam_main
from scripts.inspect_pdfs import main as inspect_pdfs_main
from scripts.list_corpus import main as list_corpus_main
from scripts.mcp_server import main as mcp_server_main
from scripts.ocr_pdfs import main as ocr_pdfs_main
from scripts.plugin_doctor import main as plugin_doctor_main
from scripts.plugin_query import main as plugin_query_main
from scripts.prepare_index import main as prepare_index_main
from scripts.run_codex_host_mcq import main as run_codex_host_mcq_main
from scripts.run_skill import main as run_skill_main
from scripts.score_host_mcq_answers import main as score_host_mcq_answers_main
from scripts.validate_skill_package import main as validate_skill_main

__all__ = [
    "add_documents_main",
    "analyze_failure_taxonomy_main",
    "audit_evaluation_outputs_main",
    "audit_public_release_main",
    "audit_runtime_integrity_main",
    "build_chatgpt_knowledge_main",
    "build_navigator_main",
    "build_paper_experiment_matrix_main",
    "build_provenance_manifest_main",
    "build_public_release_main",
    "build_sparse_index_main",
    "build_bundle_main",
    "download_corpus_main",
    "evaluate_ablation_main",
    "evaluate_agent_skill_main",
    "evaluate_agent_tasks_main",
    "evaluate_answer_generation_main",
    "evaluate_answer_quality_main",
    "evaluate_extractive_selectors_main",
    "evaluate_asset_qa_main",
    "evaluate_gold_answers_main",
    "evaluate_mcp_contract_main",
    "evaluate_public_mcq_exam_main",
    "run_codex_host_mcq_main",
    "score_host_mcq_answers_main",
    "compare_mcq_answer_methods_main",
    "evaluate_navigator_main",
    "evaluate_strategies_main",
    "evaluate_statistical_uncertainty_main",
    "evaluate_table_cell_qa_main",
    "extract_assets_main",
    "generate_agent_task_benchmark_main",
    "generate_asset_benchmark_main",
    "generate_gold_answer_benchmark_main",
    "import_public_medical_physics_exam_main",
    "generate_public_benchmark_main",
    "generate_table_cell_benchmark_main",
    "inspect_pdfs_main",
    "list_corpus_main",
    "mcp_server_main",
    "ocr_pdfs_main",
    "plugin_doctor_main",
    "plugin_query_main",
    "prepare_index_main",
    "run_skill_main",
    "validate_skill_main",
]
