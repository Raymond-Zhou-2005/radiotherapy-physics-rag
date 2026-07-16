"""OpenDataLoader-backed extraction of searchable table and image metadata."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Sequence

from src.pdf_processing.opendataloader_backend import extract_assets_batch
from src.utils import write_jsonl


def extract_pdf_assets(
    pdf_path: Path,
    doc_id: str,
    title: str,
    root: Path,
    save_images: bool = False,
    image_output_dir: Path | None = None,
) -> List[Dict[str, Any]]:
    """Compatibility wrapper for a single PDF asset request."""
    try:
        source_path = pdf_path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        source_path = pdf_path.as_posix()
    return extract_assets_batch(
        [{"pdf_path": str(pdf_path), "doc_id": doc_id, "title": title, "source_path": source_path}],
        save_images=save_images,
        image_output_dir=image_output_dir,
    )[doc_id]


def extract_pdf_assets_for_documents(
    documents: Sequence[Dict[str, str]], *, save_images: bool = False, image_output_dir: Path | None = None
) -> Dict[str, List[Dict[str, Any]]]:
    """Batch variant used by the CLI to avoid one JVM startup per report."""
    return extract_assets_batch(documents, save_images=save_images, image_output_dir=image_output_dir)


__all__ = ["extract_pdf_assets", "extract_pdf_assets_for_documents", "write_jsonl"]
