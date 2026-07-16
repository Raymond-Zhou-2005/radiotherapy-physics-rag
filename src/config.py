"""Central configuration for the medical report RAG project."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ProjectPaths:
    """Absolute paths used across the project."""

    root: Path = PROJECT_ROOT
    reports_dir: Path = PROJECT_ROOT / "reports" / "raw"
    parsed_dir: Path = PROJECT_ROOT / "parsed"
    chunks_dir: Path = PROJECT_ROOT / "chunks"
    index_dir: Path = PROJECT_ROOT / "index"
    dense_index_dir: Path = PROJECT_ROOT / "index" / "dense"
    sparse_index_dir: Path = PROJECT_ROOT / "index" / "sparse"
    metadata_index_dir: Path = PROJECT_ROOT / "index" / "metadata"
    eval_dir: Path = PROJECT_ROOT / "eval"


@dataclass(frozen=True)
class ModelConfig:
    """Model-related configuration.

    Retrieval and generation are intentionally separated.
    The default retrieval setup is semantic but lightweight:
    - Dense retrieval: BAAI/bge-small-en-v1.5
    - Reranking: BAAI/bge-reranker-base cross-encoder
    These can be overridden through environment variables.
    """

    embedding_model_name: str = os.getenv(
        "EMBEDDING_MODEL_NAME",
        "BAAI/bge-small-en-v1.5",
    )
    reranker_model_name: str = os.getenv(
        "RERANKER_MODEL_NAME",
        "BAAI/bge-reranker-base",
    )
    reranker_backend: str = os.getenv("RAG_RERANKER_BACKEND", "auto")
    medgemma_model_name_or_path: str = os.getenv(
        "MEDGEMMA_MODEL_NAME_OR_PATH",
        "",
    )
    embedding_query_prefix: str = os.getenv(
        "EMBEDDING_QUERY_PREFIX",
        "Represent this sentence for searching relevant passages: ",
    )
    embedding_document_prefix: str = os.getenv(
        "EMBEDDING_DOCUMENT_PREFIX",
        "",
    )
    reranker_max_length: int = int(os.getenv("RERANKER_MAX_LENGTH", "512"))
    max_new_tokens: int = int(os.getenv("MAX_NEW_TOKENS", "512"))


@dataclass(frozen=True)
class ChunkingConfig:
    """Parameters controlling chunk generation."""

    chunk_size_tokens: int = int(os.getenv("CHUNK_SIZE_TOKENS", "280"))
    chunk_overlap_tokens: int = int(os.getenv("CHUNK_OVERLAP_TOKENS", "40"))
    min_chunk_tokens: int = int(os.getenv("MIN_CHUNK_TOKENS", "90"))
    definitional_microchunk_max_tokens: int = int(os.getenv("DEFINITIONAL_MICROCHUNK_MAX_TOKENS", "180"))


@dataclass(frozen=True)
class RetrievalConfig:
    """Parameters controlling retrieval and reranking."""

    dense_top_k: int = int(os.getenv("DENSE_TOP_K", "24"))
    sparse_top_k: int = int(os.getenv("SPARSE_TOP_K", "24"))
    fused_top_k: int = int(os.getenv("FUSED_TOP_K", "20"))
    rerank_top_k: int = int(os.getenv("RERANK_TOP_K", "6"))
    rrf_k: int = int(os.getenv("RRF_K", "60"))
    use_retrieval_heuristics: bool = os.getenv("USE_RETRIEVAL_HEURISTICS", "0") == "1"
    use_rerank_heuristics: bool = os.getenv("USE_RERANK_HEURISTICS", "0") == "1"


PATHS = ProjectPaths()
MODELS = ModelConfig()
CHUNKING = ChunkingConfig()
RETRIEVAL = RetrievalConfig()
