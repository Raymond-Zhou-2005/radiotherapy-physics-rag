"""Dense indexing and search.

This module prefers FAISS when available. If FAISS is not installed, it falls
back to a NumPy-based brute-force search so the project can still run end to
end on small corpora.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

from src.retrieval.embedder import TextEmbedder
from src.utils import ensure_dir

try:
    import faiss  # type: ignore
except Exception:  # pragma: no cover
    faiss = None


class DenseIndexer:
    """Build and query a dense index."""

    _search_cache: Dict[str, Dict[str, Any]] = {}

    def __init__(self, embedder: TextEmbedder):
        self.embedder = embedder

    def build(self, chunk_records: List[Dict], output_dir: Path) -> None:
        ensure_dir(output_dir)
        chunk_ids = [record["chunk_id"] for record in chunk_records]
        embeddings = self.embedder.encode_records(chunk_records, normalize_embeddings=True).astype("float32")

        np.save(output_dir / "embeddings.npy", embeddings)
        with (output_dir / "chunk_ids.json").open("w", encoding="utf-8") as f:
            json.dump(chunk_ids, f, ensure_ascii=False, indent=2)
        with (output_dir / "dense_meta.json").open("w", encoding="utf-8") as f:
            json.dump(
                {
                    "embedding_model_name": self.embedder.model_name,
                    "embedding_backend": self.embedder.backend,
                    "dimension": int(embeddings.shape[1]),
                    "query_prefix": self.embedder.query_prefix,
                    "document_prefix": self.embedder.document_prefix,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )

        if faiss is not None:
            dimension = embeddings.shape[1]
            index = faiss.IndexFlatIP(dimension)
            index.add(embeddings)
            faiss.write_index(index, str(output_dir / "faiss.index"))

    def search(self, query: str, index_dir: Path, top_k: int) -> List[Tuple[str, float]]:
        cache_key = str(index_dir.resolve())
        cached = self._search_cache.get(cache_key)
        if cached is None:
            with (index_dir / "chunk_ids.json").open("r", encoding="utf-8") as f:
                chunk_ids = json.load(f)
            embeddings = np.load(index_dir / "embeddings.npy")
            meta_path = index_dir / "dense_meta.json"
            meta = {}
            if meta_path.exists():
                with meta_path.open("r", encoding="utf-8") as f:
                    meta = json.load(f)
            faiss_index = None
            if faiss is not None and (index_dir / "faiss.index").exists():
                faiss_index = faiss.read_index(str(index_dir / "faiss.index"))
            cached = {"chunk_ids": chunk_ids, "embeddings": embeddings, "meta": meta, "faiss_index": faiss_index}
            self._search_cache[cache_key] = cached

        chunk_ids = cached["chunk_ids"]
        embeddings = cached["embeddings"]
        meta = cached.get("meta") or {}
        if meta:
            stored_dim = int(meta.get("dimension", embeddings.shape[1]))
            if stored_dim != embeddings.shape[1]:
                raise ValueError("Dense index metadata dimension does not match embeddings.npy.")
            if meta.get("embedding_model_name") and meta["embedding_model_name"] != self.embedder.model_name:
                raise ValueError(
                    f"Dense index was built with embedding model '{meta['embedding_model_name']}', "
                    f"but the current model is '{self.embedder.model_name}'. Re-run build_index.py."
                )
            stored_backend = meta.get("embedding_backend")
            if stored_backend and stored_backend != self.embedder.backend:
                raise ValueError(
                    f"Dense index was built with embedding backend '{stored_backend}', "
                    f"but the current backend is '{self.embedder.backend}'. Re-run build_index.py."
                )
            if meta.get("query_prefix", "") != self.embedder.query_prefix or meta.get("document_prefix", "") != self.embedder.document_prefix:
                raise ValueError(
                    "Dense index prefix configuration does not match the current embedder configuration. "
                    "Re-run build_index.py."
                )

        q = self.embedder.encode_query(query, normalize_embeddings=True).astype("float32")
        if embeddings.shape[1] != q.shape[0]:
            raise ValueError(
                f"Dense index dimension {embeddings.shape[1]} does not match query embedding dimension {q.shape[0]}. "
                "Delete index/dense and rebuild the index with the current embedding model."
            )

        if cached.get("faiss_index") is not None:
            index = cached["faiss_index"]
            scores, indices = index.search(q.reshape(1, -1), top_k)
            hits: List[Tuple[str, float]] = []
            for idx, score in zip(indices[0].tolist(), scores[0].tolist()):
                if idx == -1:
                    continue
                hits.append((chunk_ids[idx], float(score)))
            return hits

        scores = embeddings @ q
        ranked_indices = np.argsort(scores)[::-1][:top_k]
        return [(chunk_ids[int(i)], float(scores[int(i)])) for i in ranked_indices]
