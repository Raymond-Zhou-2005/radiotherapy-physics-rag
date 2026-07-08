"""Sparse retrieval with BM25.

This module prefers rank-bm25. If that package is unavailable, it falls back to
an in-project BM25 implementation.
"""

from __future__ import annotations

import math
import pickle
from pathlib import Path
from typing import Dict, List, Tuple

from src.utils import ensure_dir, simple_tokenize, top_k_indices

try:
    from rank_bm25 import BM25Okapi  # type: ignore
except Exception:  # pragma: no cover
    BM25Okapi = None


class SimpleBM25:
    """A small self-contained BM25 implementation for fallback use."""

    def __init__(self, tokenized_corpus: List[List[str]], k1: float = 1.5, b: float = 0.75):
        self.corpus = tokenized_corpus
        self.k1 = k1
        self.b = b
        self.doc_lengths = [len(doc) for doc in tokenized_corpus]
        self.avgdl = sum(self.doc_lengths) / max(1, len(self.doc_lengths))
        self.df: Dict[str, int] = {}
        self.tf: List[Dict[str, int]] = []
        for doc in tokenized_corpus:
            counts: Dict[str, int] = {}
            for token in doc:
                counts[token] = counts.get(token, 0) + 1
            self.tf.append(counts)
            for token in counts:
                self.df[token] = self.df.get(token, 0) + 1
        self.N = len(tokenized_corpus)

    def _idf(self, token: str) -> float:
        n_q = self.df.get(token, 0)
        return math.log(1 + (self.N - n_q + 0.5) / (n_q + 0.5))

    def get_scores(self, query_tokens: List[str]) -> List[float]:
        scores: List[float] = []
        for doc_idx, tf in enumerate(self.tf):
            dl = self.doc_lengths[doc_idx]
            score = 0.0
            for token in query_tokens:
                f = tf.get(token, 0)
                if f == 0:
                    continue
                idf = self._idf(token)
                denom = f + self.k1 * (1 - self.b + self.b * dl / max(self.avgdl, 1e-9))
                score += idf * (f * (self.k1 + 1)) / denom
            scores.append(score)
        return scores


class SparseIndexer:
    """Build and query a BM25 index over chunk texts."""

    _cache: Dict[str, Dict] = {}

    def build(self, chunk_records: List[Dict], output_dir: Path) -> None:
        ensure_dir(output_dir)
        tokenized_corpus = [simple_tokenize(self._compose_index_text(record)) for record in chunk_records]
        chunk_ids = [record["chunk_id"] for record in chunk_records]
        bm25 = BM25Okapi(tokenized_corpus) if BM25Okapi is not None else SimpleBM25(tokenized_corpus)
        with (output_dir / "bm25.pkl").open("wb") as f:
            pickle.dump({"bm25": bm25, "chunk_ids": chunk_ids}, f)

    def _compose_index_text(self, record: Dict) -> str:
        parts = [
            record.get("title", ""),
            record.get("section", ""),
            record.get("subsection", ""),
            " ".join(record.get("tags", [])),
            record.get("text", ""),
        ]
        return " ".join(part for part in parts if part and part != "UNKNOWN")

    def search(self, query: str, index_dir: Path, top_k: int) -> List[Tuple[str, float]]:
        cache_key = str((index_dir / "bm25.pkl").resolve())
        payload = self._cache.get(cache_key)
        if payload is None:
            with (index_dir / "bm25.pkl").open("rb") as f:
                payload = pickle.load(f)
            self._cache[cache_key] = payload
        bm25 = payload["bm25"]
        chunk_ids: List[str] = payload["chunk_ids"]
        scores = bm25.get_scores(simple_tokenize(query))
        indices = top_k_indices(scores, top_k)
        return [(chunk_ids[i], float(scores[i])) for i in indices]
