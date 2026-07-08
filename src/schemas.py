"""Shared data structures.

The project uses JSONL files as intermediate storage. These dataclasses make it
clear what each record should contain.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DocumentRecord:
    doc_id: str
    title: str
    year: Optional[int]
    source_path: str
    authors: List[str] = field(default_factory=list)
    venue: Optional[str] = None
    topic_tags: List[str] = field(default_factory=list)
    organization: Optional[str] = None
    source_url: Optional[str] = None
    role: Optional[str] = None
    sha256: Optional[str] = None
    num_pages: Optional[int] = None
    language: str = "en"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ParsedBlock:
    block_id: str
    doc_id: str
    title: str
    page_start: int
    page_end: int
    section: str
    subsection: str
    text: str
    block_type: str
    source_path: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ChunkRecord:
    chunk_id: str
    doc_id: str
    title: str
    section: str
    subsection: str
    page_start: int
    page_end: int
    text: str
    token_count: int
    source_path: str
    tags: List[str] = field(default_factory=list)
    chunk_kind: str = "standard"
    parent_chunk_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PdfAssetRecord:
    asset_id: str
    doc_id: str
    title: str
    source_path: str
    page: int
    asset_type: str
    bbox: List[float]
    caption: str = ""
    rows: Optional[int] = None
    columns: Optional[int] = None
    image_xref: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    extension: Optional[str] = None
    extracted_image_path: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RetrievalHit:
    chunk_id: str
    dense_score: Optional[float]
    bm25_score: Optional[float]
    fusion_score: float
    rerank_score: Optional[float]
    rank: int
    chunk: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AnswerRecord:
    query: str
    answer: str
    citations: List[Dict[str, Any]]
    confidence: str
    evidence_status: str
    abstained: bool
    abstention_reason: str = ""
    used_evidence_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
