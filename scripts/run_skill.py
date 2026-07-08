#!/usr/bin/env python
"""Codex-compatible entrypoint for the report RAG evidence QA skill."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Allow `python scripts/<name>.py` to import the local src package.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import MODELS, RETRIEVAL
from src.generation.answering import GroundedAnswerer
from src.generation.prompting import build_grounded_prompt
from src.orchestration.router import (
    analyze_scene,
    append_experience_record,
    find_memory_matches,
    load_experience_memory,
    select_retrieval_strategy,
)
from src.retrieval.heuristics import compute_chunk_bonus, get_query_type, report_title_terms
from src.retrieval.hybrid import HybridRetriever
from src.retrieval.reranker import CandidateReranker
from src.retrieval.sparse import SparseIndexer
from src.utils import iter_jsonl, simple_tokenize, write_json


SKILL_NAME = "radiotherapy-physics-rag"
SCHEMA_VERSION = "1.0.0"
RETRIEVAL_BACKENDS = {"auto", "hybrid", "sparse", "routed"}
_METADATA_CACHE: Dict[str, Dict[str, Dict[str, Any]]] = {}
_HYBRID_RETRIEVER_CACHE: Dict[Tuple[str, str, str, str, bool], HybridRetriever] = {}
_ASSET_CACHE: Dict[str, List[Dict[str, Any]]] = {}

ERROR_EXIT_CODES = {
    "missing_index": 2,
    "out_of_scope": 3,
    "insufficient_evidence": 4,
    "missing_model_path": 5,
    "empty_corpus": 6,
    "ocr_required": 7,
    "runtime_failure": 1,
}

QUERY_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "according",
    "about",
    "based",
    "be",
    "by",
    "define",
    "discuss",
    "discussed",
    "does",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "say",
    "section",
    "the",
    "to",
    "tg",
    "what",
    "which",
    "with",
}

ASSET_QUERY_RE = re.compile(r"\b(table|figure|fig\.?|image|diagram|asset)\b", re.IGNORECASE)
PAGE_QUERY_RE = re.compile(r"\bpage\s+(\d{1,4})\b", re.IGNORECASE)


class SkillExecutionError(Exception):
    """Expected skill-level error with a structured output code."""

    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


def validate_query(query: str) -> None:
    """Reject only empty queries; evidence sufficiency handles corpus mismatch."""
    if not query or not query.strip():
        raise SkillExecutionError(
            "out_of_scope",
            "A non-empty question is required for RAG retrieval.",
            {"query": query},
        )


def required_sparse_index_files(index_dir: Path) -> List[Path]:
    return [
        index_dir / "sparse" / "bm25.pkl",
        index_dir / "metadata" / "chunk_metadata.jsonl",
    ]


def required_dense_index_files(index_dir: Path) -> List[Path]:
    return [
        index_dir / "dense" / "embeddings.npy",
        index_dir / "dense" / "chunk_ids.json",
        index_dir / "dense" / "dense_meta.json",
    ]


def dense_index_status(index_dir: Path) -> Dict[str, Any]:
    files = required_dense_index_files(index_dir)
    missing = [str(path) for path in files if not path.exists()]
    if missing:
        return {"available": False, "semantic": False, "missing": missing, "reason": "missing_dense_files"}

    meta_path = index_dir / "dense" / "dense_meta.json"
    try:
        with meta_path.open("r", encoding="utf-8") as handle:
            meta = json.load(handle)
    except Exception as exc:
        return {
            "available": True,
            "semantic": False,
            "reason": "unreadable_dense_meta",
            "exception_type": exc.__class__.__name__,
            "exception": str(exc),
        }

    backend = str(meta.get("embedding_backend", "") or "").lower()
    model_name = str(meta.get("embedding_model_name", "") or "").lower()
    allow_hash_hybrid = os.getenv("RAG_ALLOW_HASH_HYBRID", "").lower() in {"1", "true", "yes"}
    hash_like = backend == "hash_fallback" or model_name in {"hash", "hash-fallback", "hash_fallback"}
    if hash_like and not allow_hash_hybrid:
        return {
            "available": True,
            "semantic": False,
            "reason": "hash_dense_index",
            "embedding_backend": meta.get("embedding_backend"),
            "embedding_model_name": meta.get("embedding_model_name"),
        }
    return {
        "available": True,
        "semantic": True,
        "reason": "semantic_dense_index",
        "embedding_backend": meta.get("embedding_backend"),
        "embedding_model_name": meta.get("embedding_model_name"),
    }


def dense_index_is_semantic(index_dir: Path) -> bool:
    return bool(dense_index_status(index_dir).get("semantic"))


def experience_append_enabled() -> bool:
    return os.getenv("RAG_EXPERIENCE_APPEND", "").lower() in {"1", "true", "yes"}


def required_index_files(index_dir: Path, retrieval_backend: str = "auto") -> List[Path]:
    backend = (retrieval_backend or "auto").lower()
    files = required_sparse_index_files(index_dir)
    if backend == "hybrid":
        files = required_dense_index_files(index_dir) + files
    return files


def ensure_index(index_dir: Path, retrieval_backend: str = "auto") -> None:
    missing = [str(path) for path in required_index_files(index_dir, retrieval_backend) if not path.exists()]
    if missing:
        backend_note = (
            "Sparse retrieval requires index/sparse/bm25.pkl and index/metadata/chunk_metadata.jsonl. "
            "Hybrid retrieval also requires the dense index files."
        )
        raise SkillExecutionError(
            "missing_index",
            "The retrieval index is missing or incomplete. Run scripts/prepare_index.py first.",
            {"index_dir": str(index_dir), "retrieval_backend": retrieval_backend, "missing": missing, "note": backend_note},
        )


def load_metadata(index_dir: Path) -> List[Dict[str, Any]]:
    return list(iter_jsonl(index_dir / "metadata" / "chunk_metadata.jsonl"))


def build_report_scope(metadata: List[Dict[str, Any]], report_id: Optional[str]) -> Dict[str, Any]:
    available = sorted({str(item.get("doc_id", "")) for item in metadata if item.get("doc_id")})
    if report_id and report_id not in available:
        raise SkillExecutionError(
            "out_of_scope",
            f"Document or report '{report_id}' is not indexed.",
            {"requested_report_id": report_id, "available_report_ids": available},
        )
    return {
        "requested_report_id": report_id,
        "applied": bool(report_id),
        "available_report_ids": available,
    }


def collect_evidence(
    query: str,
    index_dir: Path,
    report_id: Optional[str] = None,
    evidence_top_k: Optional[int] = None,
) -> List[Dict[str, Any]]:
    evidence, _, _ = collect_evidence_with_backend(
        query=query,
        index_dir=index_dir,
        report_id=report_id,
        evidence_top_k=evidence_top_k,
        retrieval_backend="hybrid",
    )
    return evidence


def collect_evidence_with_backend(
    query: str,
    index_dir: Path,
    report_id: Optional[str] = None,
    evidence_top_k: Optional[int] = None,
    retrieval_backend: str = "auto",
) -> Tuple[List[Dict[str, Any]], str, List[Dict[str, Any]]]:
    backend = (retrieval_backend or "auto").lower()
    if backend not in RETRIEVAL_BACKENDS:
        raise SkillExecutionError(
            "out_of_scope",
            f"Unsupported retrieval backend '{retrieval_backend}'.",
            {"supported_retrieval_backends": sorted(RETRIEVAL_BACKENDS)},
        )

    warnings: List[Dict[str, Any]] = []
    if backend == "routed":
        return collect_routed_evidence(query, index_dir, report_id, evidence_top_k)

    if backend == "sparse":
        return collect_sparse_evidence(query, index_dir, report_id, evidence_top_k), "sparse", warnings

    dense_status = dense_index_status(index_dir)
    if backend == "auto" and not dense_status["semantic"]:
        warnings.append(
            {
                "code": "hybrid_retrieval_unavailable",
                "message": "Semantic dense retrieval is unavailable; using local BM25 sparse retrieval without loading embedding models.",
                "dense_index_status": dense_status,
            }
        )
        return collect_sparse_evidence(query, index_dir, report_id, evidence_top_k), "sparse", warnings

    try:
        return collect_hybrid_evidence(query, index_dir, report_id, evidence_top_k), "hybrid", warnings
    except Exception as exc:
        if backend == "hybrid":
            raise
        warnings.append(
            {
                "code": "hybrid_retrieval_unavailable",
                "message": "Dense or neural retrieval was unavailable; falling back to local BM25 sparse retrieval.",
                "exception_type": exc.__class__.__name__,
                "exception": str(exc),
            }
        )
        return collect_sparse_evidence(query, index_dir, report_id, evidence_top_k), "sparse", warnings


def collect_routed_evidence(
    query: str,
    index_dir: Path,
    report_id: Optional[str] = None,
    evidence_top_k: Optional[int] = None,
) -> Tuple[List[Dict[str, Any]], str, List[Dict[str, Any]]]:
    """Route retrieval strategy from scene features and experience memory."""
    dense_status = dense_index_status(index_dir)
    dense_available = bool(dense_status["semantic"])
    memory_path = Path(os.getenv("RAG_EXPERIENCE_MEMORY", str(index_dir.parent / "experience" / "experience_memory.jsonl")))
    records = load_experience_memory(memory_path)
    scene = analyze_scene(query, report_id=report_id)
    memory_matches = find_memory_matches(scene, records)
    decision = select_retrieval_strategy(scene, dense_available=dense_available, memory_matches=memory_matches)
    routed_top_k = evidence_top_k if evidence_top_k is not None else decision.evidence_top_k

    warnings: List[Dict[str, Any]] = [
        {
            "code": "routing_decision",
            "message": "Scene-aware router selected a retrieval strategy for this query.",
            "scene_features": scene,
            "decision": decision.to_dict(),
            "experience_memory_path": str(memory_path),
            "experience_memory_records": len(records),
            "dense_index_status": dense_status,
            "experience_matches": [
                {
                    "query": item.get("query"),
                    "strategy_used": item.get("strategy_used"),
                    "retrieval_backend": item.get("retrieval_backend"),
                    "evidence_status": item.get("evidence_status"),
                }
                for item in memory_matches
            ],
        }
    ]

    try:
        if decision.backend == "hybrid":
            return collect_hybrid_evidence(query, index_dir, report_id, routed_top_k), "hybrid", warnings
        return collect_sparse_evidence(query, index_dir, report_id, routed_top_k), "sparse", warnings
    except Exception as exc:
        if decision.backend == "hybrid":
            warnings.append(
                {
                    "code": "routed_hybrid_fallback",
                    "message": "Routed hybrid retrieval failed; falling back to local BM25 sparse retrieval.",
                    "exception_type": exc.__class__.__name__,
                    "exception": str(exc),
                }
            )
            return collect_sparse_evidence(query, index_dir, report_id, routed_top_k), "sparse", warnings
        raise


def collect_hybrid_evidence(
    query: str,
    index_dir: Path,
    report_id: Optional[str] = None,
    evidence_top_k: Optional[int] = None,
) -> List[Dict[str, Any]]:
    metadata_path = index_dir / "metadata" / "chunk_metadata.jsonl"
    cache_key = (
        str(metadata_path.resolve()),
        MODELS.embedding_model_name,
        MODELS.embedding_query_prefix,
        MODELS.embedding_document_prefix,
        RETRIEVAL.use_retrieval_heuristics,
    )
    retriever = _HYBRID_RETRIEVER_CACHE.get(cache_key)
    if retriever is None:
        retriever = HybridRetriever(
            embedding_model_name=MODELS.embedding_model_name,
            metadata_path=metadata_path,
            query_prefix=MODELS.embedding_query_prefix,
            document_prefix=MODELS.embedding_document_prefix,
            use_heuristics=RETRIEVAL.use_retrieval_heuristics,
        )
        _HYBRID_RETRIEVER_CACHE[cache_key] = retriever
    candidates = retriever.retrieve(
        query=query,
        dense_index_dir=index_dir / "dense",
        sparse_index_dir=index_dir / "sparse",
        dense_top_k=RETRIEVAL.dense_top_k,
        sparse_top_k=RETRIEVAL.sparse_top_k,
        fused_top_k=RETRIEVAL.fused_top_k,
        rrf_k=RETRIEVAL.rrf_k,
    )
    if report_id:
        candidates = [item for item in candidates if item.get("chunk", {}).get("doc_id") == report_id]

    return rerank_and_refine(query, candidates, evidence_top_k=evidence_top_k)


def collect_sparse_evidence(
    query: str,
    index_dir: Path,
    report_id: Optional[str] = None,
    evidence_top_k: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Retrieve evidence with only the local BM25 index.

    This path is intentionally model-free. It keeps the plugin usable in CI,
    offline demos, and ordinary downloads where Hugging Face models have not
    been cached yet.
    """
    metadata_path = index_dir / "metadata" / "chunk_metadata.jsonl"
    cache_key = str(metadata_path.resolve())
    metadata = _METADATA_CACHE.get(cache_key)
    if metadata is None:
        metadata = {record["chunk_id"]: record for record in iter_jsonl(metadata_path)}
        _METADATA_CACHE[cache_key] = metadata
    sparse_hits = SparseIndexer().search(query, index_dir / "sparse", RETRIEVAL.sparse_top_k)
    candidates: List[Dict[str, Any]] = []
    for rank, (chunk_id, score) in enumerate(sparse_hits, start=1):
        chunk = metadata.get(chunk_id)
        if not chunk:
            continue
        if report_id and chunk.get("doc_id") != report_id:
            continue
        bonus = compute_chunk_bonus(query, chunk) if RETRIEVAL.use_retrieval_heuristics else 0.0
        fusion_score = 1.0 / (RETRIEVAL.rrf_k + rank)
        candidates.append(
            {
                "chunk_id": chunk_id,
                "dense_score": 0.0,
                "bm25_score": float(score),
                "dense_hit": False,
                "bm25_hit": True,
                "fusion_score": float(fusion_score),
                "heuristic_bonus": float(bonus),
                "final_retrieval_score": float(fusion_score + bonus),
                "retrieval_rank": rank,
                "chunk": chunk,
            }
        )

    candidates = sorted(candidates, key=lambda x: x.get("final_retrieval_score", 0.0), reverse=True)[
        : RETRIEVAL.fused_top_k
    ]
    for rank, item in enumerate(candidates, start=1):
        item["retrieval_rank"] = rank
    return rerank_and_refine(query, candidates, evidence_top_k=evidence_top_k, rerank_backend="lexical")


def rerank_and_refine(
    query: str,
    candidates: List[Dict[str, Any]],
    evidence_top_k: Optional[int] = None,
    rerank_backend: str = "auto",
) -> List[Dict[str, Any]]:
    reranker = CandidateReranker(
        MODELS.reranker_model_name,
        max_length=MODELS.reranker_max_length,
        use_heuristics=RETRIEVAL.use_rerank_heuristics,
        backend=rerank_backend,
    )
    evidence = reranker.rerank(query, candidates, top_k=RETRIEVAL.rerank_top_k)
    evidence = refine_evidence(query, evidence, evidence_top_k=evidence_top_k)
    return evidence


def refine_evidence(query: str, evidence: List[Dict[str, Any]], evidence_top_k: Optional[int] = None) -> List[Dict[str, Any]]:
    """Keep the answer/bundle layer's existing definition-query drift suppression."""
    if not evidence:
        return []

    from src.retrieval.heuristics import (
        extract_query_focus,
        has_definition_cue,
        has_focus_definition_sentence,
        is_modality_specific,
        is_recommendation_chunk,
        is_summary_like_chunk,
    )

    qtype = get_query_type(query)
    if qtype != "definition":
        return evidence[:evidence_top_k] if evidence_top_k is not None else evidence

    focus = extract_query_focus(query)
    filtered: List[Dict[str, Any]] = []
    for item in evidence:
        chunk = item["chunk"]
        text = chunk.get("text", "") or ""
        section = (chunk.get("section", "") or "").upper()
        focus_definition_match = has_focus_definition_sentence(text, focus)
        has_cue = has_definition_cue(text)

        if is_modality_specific(chunk) and not focus_definition_match:
            continue
        if is_summary_like_chunk(chunk) and not focus_definition_match and not section.startswith("1. INTRODUCTION"):
            continue
        if is_recommendation_chunk(chunk) and not has_cue and not focus_definition_match and not section.startswith("1. INTRODUCTION"):
            continue
        filtered.append(item)

    if len(filtered) < 2:
        filtered = evidence

    limit = evidence_top_k if evidence_top_k is not None else min(4, len(filtered))
    return filtered[:limit]


def query_content_terms(query: str) -> List[str]:
    terms = []
    for token in simple_tokenize(query):
        lowered = token.lower()
        if lowered in QUERY_STOPWORDS:
            continue
        if lowered.isdigit():
            continue
        if len(lowered) < 3:
            continue
        terms.append(lowered)
    return terms


def assess_evidence_sufficiency(query: str, evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
    scene = analyze_scene(query)
    if scene.get("task_type") == "out_of_scope":
        return {
            "sufficient": False,
            "reason": "Query is outside the radiotherapy physics corpus scope.",
            "query_terms": sorted(set(query_content_terms(query))),
            "max_overlap": 0.0,
            "best_overlap_chunk_id": None,
            "threshold": 1.0,
            "scene_features": scene,
        }

    if not evidence:
        return {"sufficient": False, "reason": "No evidence chunks were retrieved.", "query_terms": [], "max_overlap": 0.0}

    terms = query_content_terms(query)
    if not terms:
        return {"sufficient": True, "reason": "No content terms available for lexical sufficiency check.", "query_terms": [], "max_overlap": 1.0}

    term_set = set(terms)
    max_overlap = 0.0
    best_chunk_id = None
    for item in evidence:
        chunk = item.get("chunk", {})
        haystack = " ".join(
            str(chunk.get(key, "") or "")
            for key in ("title", "section", "subsection", "text")
        )
        evidence_terms = set(simple_tokenize(haystack))
        overlap = len(term_set & evidence_terms) / max(1, len(term_set))
        if overlap > max_overlap:
            max_overlap = overlap
            best_chunk_id = chunk.get("chunk_id")

    threshold = 0.30
    return {
        "sufficient": max_overlap >= threshold,
        "reason": "Top evidence overlaps enough query content terms." if max_overlap >= threshold else "Retrieved evidence does not overlap enough query content terms.",
        "query_terms": sorted(term_set),
        "max_overlap": round(float(max_overlap), 4),
        "best_overlap_chunk_id": best_chunk_id,
        "threshold": threshold,
    }


def extract_requested_page(query: str) -> Optional[int]:
    match = PAGE_QUERY_RE.search(query)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def is_asset_page_query(query: str) -> bool:
    return bool(ASSET_QUERY_RE.search(query) and extract_requested_page(query) is not None)


def infer_asset_doc_id(query: str, metadata: List[Dict[str, Any]], evidence: List[Dict[str, Any]]) -> Optional[str]:
    q_terms = report_title_terms(query)
    by_doc: Dict[str, str] = {}
    for chunk in metadata:
        doc_id = str(chunk.get("doc_id", "") or "")
        if doc_id and doc_id not in by_doc:
            by_doc[doc_id] = str(chunk.get("title", "") or doc_id)

    best_doc = None
    best_score = 0
    for doc_id, title in by_doc.items():
        terms = report_title_terms(f"{doc_id} {title}")
        score = len(q_terms & terms)
        if score > best_score:
            best_score = score
            best_doc = doc_id
    if best_doc and best_score >= 2:
        return best_doc

    for item in evidence:
        doc_id = item.get("chunk", {}).get("doc_id")
        if doc_id:
            return str(doc_id)
    return None


def augment_asset_page_evidence(
    query: str,
    evidence: List[Dict[str, Any]],
    metadata: List[Dict[str, Any]],
    evidence_top_k: Optional[int] = None,
    window_pages: int = 1,
) -> List[Dict[str, Any]]:
    """Prepend chunks from the requested asset page neighborhood when explicit."""
    if not is_asset_page_query(query):
        return evidence
    page = extract_requested_page(query)
    if page is None:
        return evidence
    doc_id = infer_asset_doc_id(query, metadata, evidence)
    if not doc_id:
        return evidence

    low = page - window_pages
    high = page + window_pages
    nearby_chunks = [
        chunk for chunk in metadata
        if chunk.get("doc_id") == doc_id
        and int(chunk.get("page_start", -999)) <= high
        and int(chunk.get("page_end", -999)) >= low
    ]
    nearby_chunks.sort(
        key=lambda chunk: (
            min(abs(int(chunk.get("page_start", page)) - page), abs(int(chunk.get("page_end", page)) - page)),
            int(chunk.get("page_start", page)),
            str(chunk.get("chunk_id", "")),
        )
    )

    seen = {item.get("chunk_id") for item in evidence}
    augmented: List[Dict[str, Any]] = []
    for chunk in nearby_chunks[:3]:
        chunk_id = chunk.get("chunk_id")
        if chunk_id in seen:
            continue
        augmented.append(
            {
                "chunk_id": chunk_id,
                "dense_score": None,
                "bm25_score": None,
                "dense_hit": False,
                "bm25_hit": False,
                "fusion_score": 0.0,
                "heuristic_bonus": 0.0,
                "final_retrieval_score": 1.0,
                "retrieval_rank": 0,
                "rerank_score": 1.0,
                "rank": 0,
                "asset_page_injected": True,
                "chunk": chunk,
            }
        )
        seen.add(chunk_id)

    if not augmented:
        return evidence
    combined = augmented + evidence
    for rank, item in enumerate(combined, start=1):
        item["rank"] = rank
    limit = evidence_top_k if evidence_top_k is not None else len(evidence)
    return combined[:limit]


def build_citations(evidence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    citations = []
    for i, item in enumerate(evidence, start=1):
        chunk = item["chunk"]
        page_range = format_page_range(chunk["page_start"], chunk["page_end"])
        citation_text = format_citation_text(
            evidence_id=f"E{i}",
            document=chunk["title"],
            section=chunk["section"],
            page_range=page_range,
            chunk_id=chunk["chunk_id"],
        )
        citations.append(
            {
                "evidence_id": f"E{i}",
                "chunk_id": chunk["chunk_id"],
                "document": chunk["title"],
                "doc_id": chunk["doc_id"],
                "section": chunk["section"],
                "subsection": chunk["subsection"],
                "page_start": chunk["page_start"],
                "page_end": chunk["page_end"],
                "page_range": page_range,
                "source_path": chunk.get("source_path"),
                "citation": citation_text,
            }
        )
    return citations


def format_page_range(page_start: Any, page_end: Any) -> str:
    start = int(page_start)
    end = int(page_end)
    return f"p. {start}" if start == end else f"pp. {start}-{end}"


def format_citation_text(evidence_id: str, document: str, section: str, page_range: str, chunk_id: str) -> str:
    section_text = section if section and section != "UNKNOWN" else "section unknown"
    return f"[{evidence_id}] {document}; {section_text}; {page_range}; chunk {chunk_id}"


def safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_doc_assets(project_root: Path, doc_id: str) -> List[Dict[str, Any]]:
    asset_path = project_root / "assets" / "extracted" / f"{doc_id}.assets.jsonl"
    cache_key = str(asset_path.resolve())
    if cache_key in _ASSET_CACHE:
        return _ASSET_CACHE[cache_key]
    if not asset_path.exists():
        _ASSET_CACHE[cache_key] = []
        return []
    assets = []
    for record in iter_jsonl(asset_path):
        assets.append(record)
    _ASSET_CACHE[cache_key] = assets
    return assets


def find_nearby_assets(
    project_root: Path,
    doc_id: str,
    page_start: int,
    page_end: int,
    window_pages: int = 1,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    assets = load_doc_assets(project_root, doc_id)
    nearby = []
    low = page_start - window_pages
    high = page_end + window_pages
    for asset in assets:
        page = int(asset.get("page", -999))
        if low <= page <= high:
            nearby.append(
                {
                    "asset_id": asset.get("asset_id"),
                    "asset_type": asset.get("asset_type"),
                    "page": page,
                    "caption": str(asset.get("caption", "") or "")[:240],
                    "rows": asset.get("rows"),
                    "columns": asset.get("columns"),
                    "width": asset.get("width"),
                    "height": asset.get("height"),
                }
            )
    nearby.sort(key=lambda item: (abs(int(item["page"]) - page_start), str(item.get("asset_id", ""))))
    return nearby[:limit]


def flatten_evidence(evidence: List[Dict[str, Any]], project_root: Optional[Path] = None) -> List[Dict[str, Any]]:
    flattened = []
    root = project_root or PROJECT_ROOT
    for i, item in enumerate(evidence, start=1):
        chunk = item["chunk"]
        page_start = int(chunk["page_start"])
        page_end = int(chunk["page_end"])
        page_range = format_page_range(chunk["page_start"], chunk["page_end"])
        citation_text = format_citation_text(
            evidence_id=f"E{i}",
            document=chunk["title"],
            section=chunk["section"],
            page_range=page_range,
            chunk_id=chunk["chunk_id"],
        )
        flattened.append(
            {
                "evidence_id": f"E{i}",
                "chunk_id": chunk["chunk_id"],
                "doc_id": chunk["doc_id"],
                "document": chunk["title"],
                "section": chunk["section"],
                "subsection": chunk["subsection"],
                "page_start": page_start,
                "page_end": page_end,
                "page_range": page_range,
                "chunk_kind": chunk.get("chunk_kind", "standard"),
                "parent_chunk_id": chunk.get("parent_chunk_id"),
                "tags": chunk.get("tags", []),
                "source_path": chunk.get("source_path"),
                "citation": citation_text,
                "nearby_assets": find_nearby_assets(root, chunk["doc_id"], page_start, page_end),
                "text": chunk["text"],
                "scores": {
                    "dense_score": safe_float(item.get("dense_score")),
                    "bm25_score": safe_float(item.get("bm25_score")),
                    "fusion_score": safe_float(item.get("fusion_score")),
                    "heuristic_bonus": safe_float(item.get("heuristic_bonus")),
                    "final_retrieval_score": safe_float(item.get("final_retrieval_score")),
                    "retrieval_rank": item.get("retrieval_rank"),
                    "rerank_model_score": safe_float(item.get("rerank_model_score")),
                    "rerank_model_score_normalized": safe_float(item.get("rerank_model_score_normalized")),
                    "rerank_retrieval_prior": safe_float(item.get("rerank_retrieval_prior")),
                    "rerank_heuristic_bonus": safe_float(item.get("rerank_heuristic_bonus")),
                    "rerank_retrieval_bonus": safe_float(item.get("rerank_retrieval_bonus")),
                    "rerank_score": safe_float(item.get("rerank_score")),
                    "rerank_rank": item.get("rank"),
                },
            }
        )
    return flattened


def base_success(
    mode: str,
    query: str,
    report_scope: Dict[str, Any],
    evidence: List[Dict[str, Any]],
    retrieval_backend: str = "hybrid",
    retrieval_warnings: Optional[List[Dict[str, Any]]] = None,
    project_root: Optional[Path] = None,
) -> Dict[str, Any]:
    retrieval_label = (
        "dense semantic search + BM25 sparse search"
        if retrieval_backend == "hybrid"
        else "local BM25 sparse search"
    )
    routing_items = [
        item for item in (retrieval_warnings or [])
        if item.get("code") == "routing_decision"
    ]
    return {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "skill_name": SKILL_NAME,
        "mode": mode,
        "query": query,
        "report_scope": report_scope,
        "rag_pipeline": {
            "required": True,
            "ingestion": "parse -> chunk -> dense index + BM25 index",
            "retrieval": retrieval_label,
            "retrieval_backend": retrieval_backend,
            "retrieval_warnings": retrieval_warnings or [],
            "fusion": "reciprocal-rank fusion with report-aware heuristics"
            if retrieval_backend == "hybrid"
            else "BM25 ranking with report-aware heuristics",
            "post_retrieval": "candidate reranking and evidence refinement",
            "answer_boundary": "answers must use returned evidence only",
            "routing": routing_items[-1] if routing_items else None,
        },
        "evidence_status": "sufficient",
        "abstained": False,
        "evidence": flatten_evidence(evidence, project_root=project_root),
        "citations": build_citations(evidence),
    }


def build_extractive_answer(query: str, evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Return a conservative no-model answer assembled from retrieved evidence."""
    if not evidence:
        return {
            "answer": "Insufficient evidence in the indexed corpus.",
            "confidence": "low",
            "evidence_status": "insufficient",
            "abstained": True,
            "abstention_reason": "No evidence chunks were retrieved.",
            "used_evidence_ids": [],
        }

    used = []
    answer_parts = []
    for idx, item in enumerate(evidence[:2], start=1):
        chunk = item["chunk"]
        text = " ".join(str(chunk.get("text", "")).split())
        snippet = text[:700].rstrip()
        if len(text) > len(snippet):
            snippet += "..."
        used.append(f"E{idx}")
        answer_parts.append(f"[E{idx}] {snippet}")

    return {
        "answer": "Based only on the retrieved evidence:\n\n" + "\n\n".join(answer_parts),
        "confidence": "medium",
        "evidence_status": "sufficient",
        "abstained": False,
        "abstention_reason": "",
        "used_evidence_ids": used,
    }


def run_skill(
    mode: str,
    query: str,
    index_dir: Path,
    report_id: Optional[str] = None,
    evidence_top_k: Optional[int] = None,
    answer_engine: str = "auto",
    retrieval_backend: Optional[str] = None,
) -> Dict[str, Any]:
    if mode not in {"evidence", "bundle", "answer"}:
        raise SkillExecutionError(
            "out_of_scope",
            f"Unsupported mode '{mode}'.",
            {"supported_modes": ["evidence", "bundle", "answer"]},
        )
    if answer_engine not in {"auto", "extractive", "medgemma"}:
        raise SkillExecutionError(
            "out_of_scope",
            f"Unsupported answer engine '{answer_engine}'.",
            {"supported_answer_engines": ["auto", "extractive", "medgemma"]},
        )
    selected_retrieval_backend = (retrieval_backend or os.getenv("RAG_RETRIEVAL_BACKEND", "auto")).lower()
    if selected_retrieval_backend not in RETRIEVAL_BACKENDS:
        raise SkillExecutionError(
            "out_of_scope",
            f"Unsupported retrieval backend '{selected_retrieval_backend}'.",
            {"supported_retrieval_backends": sorted(RETRIEVAL_BACKENDS)},
        )
    ensure_index(index_dir, selected_retrieval_backend)
    metadata = load_metadata(index_dir)
    report_scope = build_report_scope(metadata, report_id)
    validate_query(query)

    if mode == "answer" and answer_engine == "medgemma" and not MODELS.medgemma_model_name_or_path:
        raise SkillExecutionError(
            "missing_model_path",
            "MedGemma answer mode requires MEDGEMMA_MODEL_NAME_OR_PATH. Use --answer-engine extractive, evidence mode, or bundle mode when no local answer model is configured.",
            {"env_var": "MEDGEMMA_MODEL_NAME_OR_PATH", "answer_engine": answer_engine},
        )

    evidence, actual_retrieval_backend, retrieval_warnings = collect_evidence_with_backend(
        query,
        index_dir,
        report_id=report_id,
        evidence_top_k=evidence_top_k,
        retrieval_backend=selected_retrieval_backend,
    )
    evidence = augment_asset_page_evidence(query, evidence, metadata, evidence_top_k=evidence_top_k)
    sufficiency = assess_evidence_sufficiency(query, evidence)
    if not sufficiency["sufficient"]:
        raise SkillExecutionError(
            "insufficient_evidence",
            "The indexed report evidence is insufficient to answer this query safely.",
            {"query": query, "report_scope": report_scope, "sufficiency": sufficiency},
        )

    result = base_success(
        mode,
        query,
        report_scope,
        evidence,
        retrieval_backend=actual_retrieval_backend,
        retrieval_warnings=retrieval_warnings,
        project_root=index_dir.parent,
    )
    if selected_retrieval_backend == "routed" and experience_append_enabled():
        routing = result.get("rag_pipeline", {}).get("routing") or {}
        decision = routing.get("decision") or {}
        scene = routing.get("scene_features") or {}
        memory_path = Path(os.getenv("RAG_EXPERIENCE_MEMORY", str(index_dir.parent / "experience" / "experience_memory.jsonl")))
        append_experience_record(
            memory_path,
            {
                "query": query,
                "mode": mode,
                "report_id": report_id,
                "scene_features": scene,
                "strategy_used": decision.get("strategy"),
                "retrieval_backend": actual_retrieval_backend,
                "evidence_top_k": evidence_top_k if evidence_top_k is not None else decision.get("evidence_top_k"),
                "evidence_status": result.get("evidence_status"),
                "retrieved_chunk_ids": [item.get("chunk_id") for item in result.get("evidence", [])],
                "retrieved_doc_ids": [item.get("doc_id") for item in result.get("evidence", [])],
            },
        )
    if mode == "bundle":
        result["prompt_for_medgemma"] = build_grounded_prompt(query, evidence)
    elif mode == "answer":
        engine = "medgemma" if answer_engine == "auto" and MODELS.medgemma_model_name_or_path else answer_engine
        if engine == "auto":
            engine = "extractive"
        result["answer_engine"] = engine

        if engine == "extractive":
            answer = build_extractive_answer(query, evidence)
            result["answer"] = answer["answer"]
            result["confidence"] = answer["confidence"]
            result["evidence_status"] = answer["evidence_status"]
            result["abstained"] = answer["abstained"]
            result["abstention_reason"] = answer.get("abstention_reason", "")
            result["used_evidence_ids"] = answer.get("used_evidence_ids", [])
            return result

        if engine != "medgemma":
            raise SkillExecutionError(
                "out_of_scope",
                f"Unsupported answer engine '{answer_engine}'.",
                {"supported_answer_engines": ["auto", "extractive", "medgemma"]},
            )

        if not MODELS.medgemma_model_name_or_path:
            raise SkillExecutionError(
                "missing_model_path",
                "MedGemma answer mode requires MEDGEMMA_MODEL_NAME_OR_PATH.",
                {"env_var": "MEDGEMMA_MODEL_NAME_OR_PATH", "answer_engine": engine},
            )

        from src.generation.medgemma_client import MedGemmaClient

        model_client = MedGemmaClient(
            model_name_or_path=MODELS.medgemma_model_name_or_path,
            max_new_tokens=MODELS.max_new_tokens,
        )
        answerer = GroundedAnswerer(model_client)
        answer = answerer.answer(query, evidence).to_dict()
        result["answer"] = answer["answer"]
        result["confidence"] = answer["confidence"]
        result["evidence_status"] = answer["evidence_status"]
        result["abstained"] = answer["abstained"]
        result["abstention_reason"] = answer.get("abstention_reason", "")
        result["used_evidence_ids"] = answer.get("used_evidence_ids", [])
    return result


def build_error_response(
    code: str,
    message: str,
    details: Optional[Dict[str, Any]],
    mode: Optional[str],
    query: Optional[str],
) -> Dict[str, Any]:
    return {
        "ok": False,
        "schema_version": SCHEMA_VERSION,
        "skill_name": SKILL_NAME,
        "mode": mode,
        "query": query,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AAPM report evidence QA skill.")
    parser.add_argument("--mode", choices=["evidence", "bundle", "answer"], default="evidence")
    parser.add_argument("--query", type=str, required=True)
    parser.add_argument("--report-id", type=str, default=None)
    parser.add_argument("--index-dir", type=Path, default=Path("index"))
    parser.add_argument("--evidence-top-k", type=int, default=None)
    parser.add_argument("--answer-engine", choices=["auto", "extractive", "medgemma"], default="auto")
    parser.add_argument("--retrieval-backend", choices=sorted(RETRIEVAL_BACKENDS), default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    exit_code = 0
    try:
        result = run_skill(
            mode=args.mode,
            query=args.query,
            index_dir=args.index_dir,
            report_id=args.report_id,
            evidence_top_k=args.evidence_top_k,
            answer_engine=args.answer_engine,
            retrieval_backend=args.retrieval_backend,
        )
    except SkillExecutionError as exc:
        result = build_error_response(exc.code, exc.message, exc.details, args.mode, args.query)
        exit_code = ERROR_EXIT_CODES.get(exc.code, 1)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        details = {
            "exception_type": exc.__class__.__name__,
            "traceback": traceback.format_exc(limit=8),
        }
        result = build_error_response("runtime_failure", str(exc), details, args.mode, args.query)
        exit_code = ERROR_EXIT_CODES["runtime_failure"]

    if args.output is not None:
        write_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
