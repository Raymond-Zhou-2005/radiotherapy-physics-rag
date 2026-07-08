"""Answer assembly, citation construction, and MedGemma-ready bundle export."""

from __future__ import annotations

from typing import Dict, List

from src.generation.prompting import build_grounded_prompt
from src.schemas import AnswerRecord


class GroundedAnswerer:
    """Generate an evidence-grounded answer and map evidence IDs back to citations."""

    def __init__(self, model_client):
        self.model_client = model_client

    def build_bundle(self, query: str, evidence_chunks: List[Dict]) -> Dict:
        citations = []
        evidence_items = []
        for i, item in enumerate(evidence_chunks, start=1):
            chunk = item["chunk"]
            eid = f"E{i}"
            citations.append(
                {
                    "evidence_id": eid,
                    "chunk_id": chunk["chunk_id"],
                    "document": chunk["title"],
                    "doc_id": chunk["doc_id"],
                    "section": chunk["section"],
                    "subsection": chunk["subsection"],
                    "page_start": chunk["page_start"],
                    "page_end": chunk["page_end"],
                }
            )
            evidence_items.append(
                {
                    "evidence_id": eid,
                    "scores": {
                        "dense_score": float(item.get("dense_score", 0.0)),
                        "bm25_score": float(item.get("bm25_score", 0.0)),
                        "fusion_score": float(item.get("fusion_score", 0.0)),
                        "heuristic_bonus": float(item.get("heuristic_bonus", 0.0)),
                        "final_retrieval_score": float(item.get("final_retrieval_score", 0.0)),
                        "retrieval_rank": int(item.get("retrieval_rank", 0)),
                        "rerank_model_score": float(item.get("rerank_model_score", 0.0)) if item.get("rerank_model_score") is not None else None,
                        "rerank_model_score_normalized": float(item.get("rerank_model_score_normalized", 0.0)) if item.get("rerank_model_score_normalized") is not None else None,
                        "rerank_retrieval_prior": float(item.get("rerank_retrieval_prior", 0.0)) if item.get("rerank_retrieval_prior") is not None else None,
                        "rerank_heuristic_bonus": float(item.get("rerank_heuristic_bonus", 0.0)) if item.get("rerank_heuristic_bonus") is not None else None,
                        "rerank_retrieval_bonus": float(item.get("rerank_retrieval_bonus", 0.0)) if item.get("rerank_retrieval_bonus") is not None else None,
                        "rerank_score": float(item.get("rerank_score", 0.0)) if item.get("rerank_score") is not None else None,
                        "rerank_rank": int(item.get("rank", 0)) if item.get("rank") is not None else None,
                    },
                    "chunk": chunk,
                }
            )

        return {
            "query": query,
            "evidence": evidence_items,
            "citations": citations,
            "prompt_for_medgemma": build_grounded_prompt(query, evidence_chunks),
        }

    def answer(self, query: str, evidence_chunks: List[Dict]) -> AnswerRecord:
        if not evidence_chunks:
            return AnswerRecord(
                query=query,
                answer="Insufficient evidence in the indexed report corpus.",
                citations=[],
                confidence="low",
                evidence_status="insufficient",
                abstained=True,
                abstention_reason="No evidence chunks were retrieved.",
                used_evidence_ids=[],
            )

        prompt = build_grounded_prompt(query, evidence_chunks)
        model_json = self.model_client.generate_json(prompt)

        evidence_id_map = {f"E{i}": item for i, item in enumerate(evidence_chunks, start=1)}
        used_ids = [eid for eid in model_json.get("evidence_ids", []) if eid in evidence_id_map]
        citations = []
        for eid in used_ids:
            chunk = evidence_id_map[eid]["chunk"]
            citations.append(
                {
                    "evidence_id": eid,
                    "chunk_id": chunk["chunk_id"],
                    "document": chunk["title"],
                    "doc_id": chunk["doc_id"],
                    "section": chunk["section"],
                    "subsection": chunk["subsection"],
                    "page_start": chunk["page_start"],
                    "page_end": chunk["page_end"],
                }
            )

        return AnswerRecord(
            query=query,
            answer=model_json.get("answer", ""),
            citations=citations,
            confidence=model_json.get("confidence", "low"),
            evidence_status=model_json.get("evidence_status", "insufficient"),
            abstained=bool(model_json.get("abstained", False)),
            abstention_reason=model_json.get("abstention_reason", ""),
            used_evidence_ids=used_ids,
        )
