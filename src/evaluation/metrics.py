"""Evaluation utilities for retrieval, answer review, and abstention."""

from __future__ import annotations

from typing import Dict, List, Tuple


def recall_at_k(retrieved_ids: List[str], gold_ids: List[str], k: int) -> float:
    """Return 1.0 if any gold item appears in the top-k retrieved list, else 0.0."""
    top = set(retrieved_ids[:k])
    gold = set(gold_ids)
    return 1.0 if top & gold else 0.0



def mrr(retrieved_ids: List[str], gold_ids: List[str]) -> float:
    """Mean reciprocal rank contribution for a single query."""
    gold = set(gold_ids)
    for rank, rid in enumerate(retrieved_ids, start=1):
        if rid in gold:
            return 1.0 / rank
    return 0.0



def section_match_recall(retrieved_sections: List[str], gold_section: str, k: int) -> float:
    """Fallback retrieval signal when gold chunk IDs are not yet annotated."""
    gold_section = gold_section.lower().strip()
    for section in retrieved_sections[:k]:
        if gold_section in section.lower():
            return 1.0
    return 0.0



def abstention_confusion(pred_abstained: bool, gold_should_abstain: bool) -> Dict[str, int]:
    """Return a simple confusion-count dictionary for one example."""
    if pred_abstained and gold_should_abstain:
        return {"tp": 1, "fp": 0, "tn": 0, "fn": 0}
    if pred_abstained and not gold_should_abstain:
        return {"tp": 0, "fp": 1, "tn": 0, "fn": 0}
    if (not pred_abstained) and gold_should_abstain:
        return {"tp": 0, "fp": 0, "tn": 0, "fn": 1}
    return {"tp": 0, "fp": 0, "tn": 1, "fn": 0}
