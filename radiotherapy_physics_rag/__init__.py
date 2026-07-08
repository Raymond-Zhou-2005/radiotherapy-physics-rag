"""Public Python facade for the radiotherapy physics RAG skill."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from scripts.run_skill import run_skill

__all__ = ["query", "run_skill"]


def query(
    question: str,
    mode: str = "evidence",
    index_dir: str | Path = "index",
    report_id: Optional[str] = None,
    evidence_top_k: Optional[int] = None,
    answer_engine: str = "auto",
    retrieval_backend: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the skill from Python code and return the structured JSON object."""
    return run_skill(
        mode=mode,
        query=question,
        index_dir=Path(index_dir),
        report_id=report_id,
        evidence_top_k=evidence_top_k,
        answer_engine=answer_engine,
        retrieval_backend=retrieval_backend,
    )
