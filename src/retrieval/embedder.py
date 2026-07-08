"""Embedding utilities for dense retrieval.

This module prefers sentence-transformers. If that package is not available, it
falls back to a lightweight hashed bag-of-words embedding so the rest of the
pipeline can still run for debugging.

Runtime notes
-------------
- We suppress the Windows symlink warning from huggingface_hub by default. This
  only hides the warning; the underlying cache behaviour is unchanged unless
  Developer Mode or Administrator mode is enabled.
- For BGE models, we add the recommended retrieval instruction to queries but
  not to passages.
- For EmbeddingGemma models, we prefer encode_query / encode_document whenever
  those APIs are available.
"""

from __future__ import annotations

import os
from typing import Dict, Iterable, List

import numpy as np

from src.utils import simple_tokenize

# Suppress the repetitive Windows symlink warning in normal project use.
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

if os.getenv("RAG_FORCE_HASH_EMBEDDINGS", "").lower() in {"1", "true", "yes"}:
    SentenceTransformer = None
else:
    try:
        from sentence_transformers import SentenceTransformer
    except Exception:  # pragma: no cover
        SentenceTransformer = None


class TextEmbedder:
    """Thin wrapper around sentence-transformers or a fallback embedder."""

    def __init__(
        self,
        model_name: str,
        fallback_dim: int = 768,
        query_prefix: str = "",
        document_prefix: str = "",
    ):
        self.model_name = model_name
        self.fallback_dim = fallback_dim
        self.model = None
        self.query_prefix = query_prefix
        self.document_prefix = document_prefix
        self.backend = "hash_fallback"
        lowered = model_name.lower()
        self.is_embedding_gemma = "embeddinggemma" in lowered
        self.is_bge = "bge-" in lowered

        if self.is_embedding_gemma:
            self.query_prefix = query_prefix or "task: search result | query: "
            self.document_prefix = (
                document_prefix
                or "title: {title} | section: {section} | subsection: {subsection} | text: "
            )
        elif self.is_bge:
            self.query_prefix = query_prefix or "Represent this sentence for searching relevant passages: "
            # BGE model cards recommend no instruction for passages.
            self.document_prefix = document_prefix or ""

        force_hash = os.getenv("RAG_FORCE_HASH_EMBEDDINGS", "").lower() in {"1", "true", "yes"}
        if lowered in {"hash", "hash-fallback", "hash_fallback"}:
            force_hash = True
            self.model_name = "hash-fallback"

        if SentenceTransformer is not None and not force_hash:
            try:
                self.model = SentenceTransformer(model_name)
                self.backend = "sentence_transformers"
            except Exception:
                self.model = None

    def format_document_text(self, record: Dict) -> str:
        prefix = self.document_prefix
        if "{" in prefix and "}" in prefix:
            prefix = prefix.format(
                title=record.get("title", "none") or "none",
                section=record.get("section", "none") or "none",
                subsection=record.get("subsection", "none") or "none",
            )
        text = record.get("text", "")
        if prefix:
            return f"{prefix}{text}"
        parts = [
            record.get("title", ""),
            record.get("section", ""),
            record.get("subsection", ""),
            " ".join(record.get("tags", [])),
            text,
        ]
        return "\n".join(part for part in parts if part and part != "UNKNOWN")

    def encode_texts(self, texts: Iterable[str], normalize_embeddings: bool = True) -> np.ndarray:
        texts = list(texts)
        if self.model is not None:
            return self.model.encode(
                texts,
                normalize_embeddings=normalize_embeddings,
                convert_to_numpy=True,
                show_progress_bar=True,
            )
        vectors = np.vstack([self._fallback_encode(t) for t in texts])
        if normalize_embeddings:
            vectors = self._normalize(vectors)
        return vectors.astype("float32")

    def encode_records(self, records: List[Dict], normalize_embeddings: bool = True) -> np.ndarray:
        texts = [self.format_document_text(record) for record in records]

        if self.model is not None:
            if self.is_embedding_gemma and hasattr(self.model, "encode_document"):
                return self.model.encode_document(
                    texts,
                    normalize_embeddings=normalize_embeddings,
                    convert_to_numpy=True,
                    show_progress_bar=True,
                )
            return self.model.encode(
                texts,
                normalize_embeddings=normalize_embeddings,
                convert_to_numpy=True,
                show_progress_bar=True,
            )

        vectors = np.vstack([self._fallback_encode(t) for t in texts])
        if normalize_embeddings:
            vectors = self._normalize(vectors)
        return vectors.astype("float32")

    def encode_query(self, query: str, normalize_embeddings: bool = True) -> np.ndarray:
        if self.query_prefix:
            query = self.query_prefix + query

        if self.model is not None:
            if self.is_embedding_gemma and hasattr(self.model, "encode_query"):
                emb = self.model.encode_query(
                    query,
                    normalize_embeddings=normalize_embeddings,
                    convert_to_numpy=True,
                    show_progress_bar=False,
                )
                return emb.astype("float32")
            emb = self.model.encode(
                [query],
                normalize_embeddings=normalize_embeddings,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
            return emb[0].astype("float32")
        vec = self._fallback_encode(query)
        if normalize_embeddings:
            vec = self._normalize(vec.reshape(1, -1))[0]
        return vec.astype("float32")

    def _fallback_encode(self, text: str) -> np.ndarray:
        vec = np.zeros(self.fallback_dim, dtype=np.float32)
        for token in simple_tokenize(text):
            idx = hash(token) % self.fallback_dim
            vec[idx] += 1.0
        return vec

    def _normalize(self, matrix: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return matrix / norms
