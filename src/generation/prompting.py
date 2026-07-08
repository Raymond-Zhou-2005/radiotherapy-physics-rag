"""Prompt construction for grounded answering."""

from __future__ import annotations

from typing import Dict, List


SYSTEM_INSTRUCTIONS = """You are answering questions about medical technical reports.
You must obey the following rules strictly:
1. Use only the evidence provided below.
2. Do not add facts that are not supported by the evidence.
3. If the evidence is insufficient, say so clearly.
4. Return valid JSON only.
5. In the field `evidence_ids`, include only evidence IDs from the provided list.
"""


def build_grounded_prompt(query: str, evidence_chunks: List[Dict]) -> str:
    """Create a single prompt string for MedGemma.

    The model is asked to produce a compact JSON object instead of free-form
    prose. This makes the answer stage easier to postprocess and evaluate.
    """
    evidence_lines = []
    for i, item in enumerate(evidence_chunks, start=1):
        chunk = item["chunk"]
        evidence_lines.append(
            f"E{i}\n"
            f"Document: {chunk['title']}\n"
            f"Section: {chunk['section']}\n"
            f"Subsection: {chunk['subsection']}\n"
            f"Pages: {chunk['page_start']}-{chunk['page_end']}\n"
            f"Text: {chunk['text']}\n"
        )

    json_schema = """{
  "answer": "...",
  "evidence_ids": ["E1", "E2"],
  "confidence": "high|medium|low",
  "evidence_status": "sufficient|partial|insufficient",
  "abstained": true_or_false,
  "abstention_reason": "..."
}"""

    prompt = (
        SYSTEM_INSTRUCTIONS
        + "\n\n"
        + "Question:\n"
        + query
        + "\n\nEvidence:\n"
        + "\n".join(evidence_lines)
        + "\n\nReturn JSON with this exact schema:\n"
        + json_schema
    )
    return prompt
