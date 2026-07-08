"""Hybrid retrieval that combines dense and sparse signals."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from src.retrieval.dense import DenseIndexer
from src.retrieval.embedder import TextEmbedder
from src.retrieval.heuristics import compute_chunk_bonus
from src.retrieval.sparse import SparseIndexer
from src.utils import iter_jsonl


class HybridRetriever:
    """Perform dense retrieval, BM25 retrieval, and reciprocal-rank fusion."""

    def __init__(
        self,
        embedding_model_name: str,
        metadata_path: Path,
        query_prefix: str = "",
        document_prefix: str = "",
        use_heuristics: bool = True,
    ):
        self.embedder = TextEmbedder(embedding_model_name, query_prefix=query_prefix, document_prefix=document_prefix)
        self.dense = DenseIndexer(self.embedder)
        self.sparse = SparseIndexer()
        self.metadata = {record["chunk_id"]: record for record in iter_jsonl(metadata_path)}
        self.use_heuristics = use_heuristics

    def retrieve(
        self,
        query: str,
        dense_index_dir: Path,
        sparse_index_dir: Path,
        dense_top_k: int = 20,
        sparse_top_k: int = 20,
        fused_top_k: int = 20,
        rrf_k: int = 60,
    ) -> List[Dict]:
        dense_hits = self.dense.search(query, dense_index_dir, dense_top_k)
        sparse_hits = self.sparse.search(query, sparse_index_dir, sparse_top_k)

        fusion: Dict[str, Dict] = {}
        for rank, (chunk_id, score) in enumerate(dense_hits, start=1):
            fusion.setdefault(
                chunk_id,
                {
                    "chunk_id": chunk_id,
                    "dense_score": 0.0,
                    "bm25_score": 0.0,
                    "dense_hit": False,
                    "bm25_hit": False,
                    "fusion_score": 0.0,
                },
            )
            fusion[chunk_id]["dense_score"] = float(score)
            fusion[chunk_id]["dense_hit"] = True
            fusion[chunk_id]["fusion_score"] += 1.0 / (rrf_k + rank)

        for rank, (chunk_id, score) in enumerate(sparse_hits, start=1):
            fusion.setdefault(
                chunk_id,
                {
                    "chunk_id": chunk_id,
                    "dense_score": 0.0,
                    "bm25_score": 0.0,
                    "dense_hit": False,
                    "bm25_hit": False,
                    "fusion_score": 0.0,
                },
            )
            fusion[chunk_id]["bm25_score"] = float(score)
            fusion[chunk_id]["bm25_hit"] = True
            fusion[chunk_id]["fusion_score"] += 1.0 / (rrf_k + rank)

        items = list(fusion.values())
        for item in items:
            chunk = self.metadata[item["chunk_id"]]
            item["chunk"] = chunk
            bonus = compute_chunk_bonus(query, chunk) if self.use_heuristics else 0.0
            item["heuristic_bonus"] = float(bonus)
            item["final_retrieval_score"] = float(item["fusion_score"] + bonus)

        ranked = sorted(items, key=lambda x: x["final_retrieval_score"], reverse=True)[:fused_top_k]
        for rank, item in enumerate(ranked, start=1):
            item["retrieval_rank"] = rank
        return ranked
