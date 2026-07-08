"""Extract searchable table and image metadata from report PDFs."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import fitz

from src.schemas import PdfAssetRecord
from src.utils import normalize_whitespace


CAPTION_RE = re.compile(r"^(fig\.?|figure|table)\s+[A-ZIVX\d\-]+[.:]?\s+", re.IGNORECASE)


@dataclass
class TextLine:
    text: str
    bbox: List[float]


def _relative_path(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _page_lines(page: fitz.Page) -> List[TextLine]:
    data = page.get_text("dict")
    lines: List[TextLine] = []
    for block in data.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            text = normalize_whitespace("".join(span.get("text", "") for span in spans))
            if not text:
                continue
            bbox = [float(value) for value in line.get("bbox", [0, 0, 0, 0])]
            lines.append(TextLine(text=text, bbox=bbox))
    return sorted(lines, key=lambda item: (item.bbox[1], item.bbox[0]))


def _caption_near(lines: List[TextLine], bbox: List[float], asset_type: str) -> str:
    x0, y0, x1, y1 = bbox
    candidates: List[tuple[float, str]] = []
    for line in lines:
        lx0, ly0, lx1, ly1 = line.bbox
        horizontal_overlap = max(0.0, min(x1, lx1) - max(x0, lx0))
        required_overlap = max(20.0, min(x1 - x0, lx1 - lx0) * 0.15)
        if horizontal_overlap < required_overlap:
            continue
        vertical_distance = min(abs(ly0 - y1), abs(y0 - ly1))
        if vertical_distance > 95:
            continue
        text = normalize_whitespace(line.text)
        if CAPTION_RE.search(text):
            candidates.append((vertical_distance, text))
        elif asset_type == "table" and text.lower().startswith("table"):
            candidates.append((vertical_distance + 5, text))
        elif asset_type == "image" and text.lower().startswith(("fig", "figure")):
            candidates.append((vertical_distance + 5, text))
    if not candidates:
        return ""
    candidates.sort(key=lambda item: item[0])
    return candidates[0][1]


def _table_shape(table: Any) -> tuple[Optional[int], Optional[int]]:
    try:
        rows = table.extract()
    except Exception:
        return None, None
    if not rows:
        return 0, 0
    return len(rows), max((len(row) for row in rows if row), default=0)


def _table_text_preview(table: Any, max_chars: int = 700) -> str:
    try:
        rows = table.extract()
    except Exception:
        return ""
    cells: List[str] = []
    for row in rows or []:
        for cell in row or []:
            text = normalize_whitespace(str(cell or ""))
            if text:
                cells.append(text)
    preview = " | ".join(cells)
    if len(preview) > max_chars:
        preview = preview[:max_chars].rstrip() + "..."
    return preview


def extract_pdf_assets(
    pdf_path: Path,
    doc_id: str,
    title: str,
    root: Path,
    save_images: bool = False,
    image_output_dir: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    records: List[PdfAssetRecord] = []
    doc = fitz.open(pdf_path)
    rel_source = _relative_path(pdf_path, root)

    for page_index in range(len(doc)):
        page = doc[page_index]
        page_number = page_index + 1
        lines = _page_lines(page)

        if hasattr(page, "find_tables"):
            try:
                table_result = page.find_tables()
                tables = getattr(table_result, "tables", []) or []
            except Exception:
                tables = []
            for table_index, table in enumerate(tables, start=1):
                bbox = [float(value) for value in table.bbox]
                rows, columns = _table_shape(table)
                records.append(
                    PdfAssetRecord(
                        asset_id=f"{doc_id}_p{page_number:03d}_table_{table_index:02d}",
                        doc_id=doc_id,
                        title=title,
                        source_path=rel_source,
                        page=page_number,
                        asset_type="table",
                        bbox=bbox,
                        caption=_caption_near(lines, bbox, "table"),
                        rows=rows,
                        columns=columns,
                        text_preview=_table_text_preview(table),
                    )
                )

        image_seen: set[tuple[int, tuple[float, float, float, float]]] = set()
        for image_index, image_info in enumerate(page.get_images(full=True), start=1):
            xref = int(image_info[0])
            rects = page.get_image_rects(xref)
            if not rects:
                continue
            metadata: Dict[str, Any] = {}
            try:
                metadata = doc.extract_image(xref)
            except Exception:
                metadata = {}
            for rect_index, rect in enumerate(rects, start=1):
                bbox = [float(rect.x0), float(rect.y0), float(rect.x1), float(rect.y1)]
                key = (xref, tuple(round(value, 2) for value in bbox))
                if key in image_seen:
                    continue
                image_seen.add(key)

                extracted_path = None
                if save_images and image_output_dir and metadata.get("image"):
                    extension = str(metadata.get("ext") or "bin")
                    target_dir = image_output_dir / doc_id
                    target_dir.mkdir(parents=True, exist_ok=True)
                    target = target_dir / f"p{page_number:03d}_img_{image_index:02d}_{rect_index:02d}.{extension}"
                    target.write_bytes(metadata["image"])
                    extracted_path = _relative_path(target, root)

                records.append(
                    PdfAssetRecord(
                        asset_id=f"{doc_id}_p{page_number:03d}_image_{image_index:02d}_{rect_index:02d}",
                        doc_id=doc_id,
                        title=title,
                        source_path=rel_source,
                        page=page_number,
                        asset_type="image",
                        bbox=bbox,
                        caption=_caption_near(lines, bbox, "image"),
                        image_xref=xref,
                        width=int(metadata.get("width")) if metadata.get("width") else None,
                        height=int(metadata.get("height")) if metadata.get("height") else None,
                        extension=str(metadata.get("ext")) if metadata.get("ext") else None,
                        extracted_image_path=extracted_path,
                    )
                )

    return [record.to_dict() for record in records]


def write_jsonl(path: Path, records: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
