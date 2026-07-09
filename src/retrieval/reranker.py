"""Candidate reranking.

This module supports three levels of reranking:
1. A Hugging Face sequence-classification reranker.
2. A sentence-transformers CrossEncoder when applicable.
3. A lexical fallback when no neural model is available.

It also applies lightweight report-aware heuristics so definition questions and
section-location questions are treated more appropriately for technical PDFs.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import os
import numpy as np

# Suppress the repetitive Windows symlink warning in normal project use.
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

from src.retrieval.heuristics import compute_chunk_bonus, compute_rerank_adjustment, get_query_type
from src.utils import simple_tokenize

VALID_BACKENDS = {"auto", "lexical", "cross_encoder", "hf"}
FORCE_LEXICAL = os.getenv("RAG_FORCE_LEXICAL_RERANK", "").lower() in {"1", "true", "yes"} or os.getenv(
    "RAG_FORCE_HASH_EMBEDDINGS", ""
).lower() in {"1", "true", "yes"}

if FORCE_LEXICAL:
    CrossEncoder = None
else:
    try:
        from sentence_transformers import CrossEncoder
    except Exception:  # pragma: no cover
        CrossEncoder = None

if FORCE_LEXICAL:
    torch = None
    AutoModelForSequenceClassification = None
    AutoTokenizer = None
else:
    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except Exception:  # pragma: no cover
        torch = None
        AutoModelForSequenceClassification = None
        AutoTokenizer = None

_CROSS_ENCODER_CACHE: Dict[Tuple[str, int], Any] = {}
_HF_RERANKER_CACHE: Dict[Tuple[str, str], Tuple[Any, Any, str]] = {}


class CandidateReranker:
    """Re-rank candidate chunks for a given query."""

    def __init__(self, model_name: str, max_length: int = 1024, use_heuristics: bool = True, backend: str = "auto"):
        self.model_name = model_name
        self.max_length = max_length
        self.use_heuristics = use_heuristics
        requested_backend = (backend or os.getenv("RAG_RERANKER_BACKEND", "auto")).lower()
        if requested_backend not in VALID_BACKENDS:
            requested_backend = "auto"
        self.backend = requested_backend
        self.requested_backend = requested_backend
        self.resolved_backend = "lexical"
        self.cross_encoder = None
        self.hf_tokenizer = None
        self.hf_model = None
        self.device = None

        if FORCE_LEXICAL:
            self.backend = "lexical"
            self.requested_backend = "lexical"

        if self.backend == "lexical":
            self.resolved_backend = "lexical"
            return

        if self.backend in {"auto", "cross_encoder"} and CrossEncoder is not None:
            try:
                cache_key = (model_name, max_length)
                if cache_key not in _CROSS_ENCODER_CACHE:
                    _CROSS_ENCODER_CACHE[cache_key] = CrossEncoder(model_name, max_length=max_length)
                self.cross_encoder = _CROSS_ENCODER_CACHE[cache_key]
                self.resolved_backend = "cross_encoder"
                return
            except Exception:
                self.cross_encoder = None

        if self.backend in {"auto", "hf"} and AutoTokenizer is not None and AutoModelForSequenceClassification is not None and torch is not None:
            try:
                device = "cuda" if torch.cuda.is_available() else "cpu"
                cache_key = (model_name, device)
                if cache_key not in _HF_RERANKER_CACHE:
                    tokenizer = AutoTokenizer.from_pretrained(model_name)
                    model = AutoModelForSequenceClassification.from_pretrained(model_name)
                    model.to(device)
                    model.eval()
                    _HF_RERANKER_CACHE[cache_key] = (tokenizer, model, device)
                self.hf_tokenizer, self.hf_model, self.device = _HF_RERANKER_CACHE[cache_key]
                self.resolved_backend = "hf_sequence_classifier"
            except Exception:
                self.hf_tokenizer = None
                self.hf_model = None
                self.device = None
        if self.resolved_backend == "lexical" and os.getenv("RAG_RERANKER_STRICT", "").lower() in {"1", "true", "yes"}:
            raise RuntimeError(
                f"Requested reranker backend '{self.requested_backend}' could not be loaded for model '{model_name}'."
            )

    def rerank(self, query: str, candidates: List[Dict], top_k: int = 5) -> List[Dict]:
        if not candidates:
            return []

        if self.cross_encoder is not None:
            pairs = [(query, self._compose_rerank_text(c["chunk"])) for c in candidates]
            scores = self.cross_encoder.predict(pairs)
            model_scores = [float(s) for s in scores]
        elif self.hf_model is not None and self.hf_tokenizer is not None and torch is not None:
            model_scores = self._predict_hf_scores(query, candidates)
        else:
            q_tokens = set(simple_tokenize(query))
            model_scores = []
            for candidate in candidates:
                c_tokens = set(simple_tokenize(self._compose_rerank_text(candidate["chunk"])))
                overlap = len(q_tokens & c_tokens)
                denom = max(1, len(q_tokens))
                model_scores.append(overlap / denom)

        normalized_model = self._minmax(model_scores)
        retrieval_prior = self._minmax([float(c.get("final_retrieval_score", 0.0)) for c in candidates])
        model_weight, prior_weight, retrieval_bonus_weight = self._blend_weights(query)

        for candidate, raw_model, norm_model, norm_prior in zip(candidates, model_scores, normalized_model, retrieval_prior):
            retrieval_bonus = compute_chunk_bonus(query, candidate["chunk"]) if self.use_heuristics else 0.0
            rerank_bonus = compute_rerank_adjustment(query, candidate["chunk"]) if self.use_heuristics else 0.0

            # Blend reranker score with retrieval prior to reduce unstable jumps.
            blended = model_weight * norm_model + prior_weight * norm_prior

            candidate["rerank_model_score"] = float(raw_model)
            candidate["rerank_model_score_normalized"] = float(norm_model)
            candidate["rerank_retrieval_prior"] = float(norm_prior)
            candidate["rerank_heuristic_bonus"] = float(rerank_bonus)
            candidate["rerank_retrieval_bonus"] = float(retrieval_bonus)
            candidate["rerank_score"] = float(blended + rerank_bonus + retrieval_bonus_weight * retrieval_bonus)
            candidate["reranker_backend"] = self.resolved_backend
            candidate["reranker_requested_backend"] = self.requested_backend
            candidate["reranker_model_name"] = self.model_name if self.resolved_backend != "lexical" else ""

        ranked = sorted(candidates, key=lambda x: x.get("rerank_score", 0.0), reverse=True)[:top_k]
        for rank, item in enumerate(ranked, start=1):
            item["rank"] = rank
        return ranked

    def _compose_rerank_text(self, chunk: Dict) -> str:
        parts = [
            chunk.get("title", ""),
            chunk.get("section", ""),
            chunk.get("subsection", ""),
            chunk.get("text", ""),
        ]
        return "\n".join(part for part in parts if part and part != "UNKNOWN")

    def _predict_hf_scores(self, query: str, candidates: List[Dict]) -> List[float]:
        assert self.hf_model is not None and self.hf_tokenizer is not None and torch is not None
        texts = [self._compose_rerank_text(c["chunk"]) for c in candidates]
        batch = self.hf_tokenizer(
            [query] * len(texts),
            texts,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )
        batch = {k: v.to(self.device) for k, v in batch.items()}
        with torch.no_grad():
            outputs = self.hf_model(**batch)
            logits = outputs.logits
            if logits.ndim == 2 and logits.shape[1] == 1:
                scores = logits[:, 0]
            elif logits.ndim == 2 and logits.shape[1] > 1:
                scores = logits[:, -1]
            else:
                scores = logits.reshape(-1)
        return [float(x) for x in scores.detach().cpu().numpy().astype(np.float32)]

    def _minmax(self, values: List[float]) -> List[float]:
        arr = np.asarray(values, dtype=np.float32)
        if arr.size == 0:
            return []
        vmin = float(arr.min())
        vmax = float(arr.max())
        if vmax - vmin < 1e-8:
            return [0.5 for _ in values]
        return [float((x - vmin) / (vmax - vmin)) for x in arr]

    def _blend_weights(self, query: str) -> Tuple[float, float, float]:
        qtype = get_query_type(query)
        if qtype == "definition":
            return 0.55, 0.45, 0.15
        if qtype == "section_locator":
            return 0.58, 0.42, 0.20
        if qtype == "recommendation":
            return 0.62, 0.38, 0.20
        return 0.65, 0.35, 0.25
