"""Compatibility wrapper for the OpenDataLoader PDF parser.

``PDFStructuredParser`` remains the public class name used by older scripts,
but its implementation now delegates to OpenDataLoader rather than PyMuPDF.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Sequence

from src.pdf_processing.opendataloader_backend import parse_documents
from src.schemas import ParsedBlock


class PDFStructuredParser:
    """Parse technical PDFs into structured blocks with OpenDataLoader."""

    def parse(self, pdf_path: Path, doc_id: str, title: str, source_path: str | None = None) -> List[ParsedBlock]:
        document = {
            "pdf_path": str(pdf_path),
            "doc_id": doc_id,
            "title": title,
            "source_path": source_path or str(pdf_path),
        }
        return parse_documents([document])[doc_id]

    def parse_many(self, documents: Sequence[Dict[str, str]]) -> Dict[str, List[ParsedBlock]]:
        """Parse a manifest batch in one converter invocation."""
        return parse_documents(documents)
