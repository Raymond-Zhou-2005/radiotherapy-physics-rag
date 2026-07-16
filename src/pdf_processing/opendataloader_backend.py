"""OpenDataLoader-backed PDF conversion for the local RAG runtime.

The module is deliberately the only place that knows about the third-party
OpenDataLoader JSON schema.  Callers receive the project's stable parsed-block
and asset records, while transient vendor JSON and extracted images are removed
after each batch conversion.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Sequence

from src.schemas import ParsedBlock, PdfAssetRecord
from src.utils import normalize_whitespace

TEXT_ELEMENT_TYPES = {"paragraph", "list", "text block", "caption", "table"}
LEGACY_SORT_OPTION = "-Djava.util.Arrays.useLegacyMergeSort=true"


def _temp_root() -> Path | None:
    """Use an explicit temporary root when supplied by the host environment."""
    value = os.getenv("RAG_ODL_TMPDIR", "").strip()
    if not value:
        return None
    root = Path(value).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _load_converter():
    try:
        import opendataloader_pdf
    except ImportError as exc:  # pragma: no cover - depends on host runtime
        raise RuntimeError(
            "OpenDataLoader PDF is required. Install opendataloader-pdf and Java 11+; "
            "see references/model_setup.md."
        ) from exc
    return opendataloader_pdf


def _ensure_java_sort_compatibility() -> None:
    """Work around an upstream comparator failure on legacy technical PDFs.

    OpenDataLoader 2.5.0 can abort on IAEA TRS-430 because its header/footer
    ordering comparator violates the modern TimSort contract. The legacy sort
    property keeps ordering deterministic enough for parsing and is appended
    without discarding host-provided JVM options.
    """
    existing = os.environ.get("JAVA_TOOL_OPTIONS", "").strip()
    if LEGACY_SORT_OPTION not in existing.split():
        os.environ["JAVA_TOOL_OPTIONS"] = " ".join(part for part in [existing, LEGACY_SORT_OPTION] if part)


def _element_text(element: Dict[str, Any]) -> str:
    content = element.get("content")
    if isinstance(content, str) and content.strip():
        return normalize_whitespace(content)
    parts: List[str] = []
    for child in element.get("kids") or []:
        if isinstance(child, dict):
            text = _element_text(child)
            if text:
                parts.append(text)
    return normalize_whitespace(" ".join(parts))


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_bbox(value: Any) -> List[float]:
    if not isinstance(value, list) or len(value) != 4:
        return [0.0, 0.0, 0.0, 0.0]
    try:
        return [float(item) for item in value]
    except (TypeError, ValueError):
        return [0.0, 0.0, 0.0, 0.0]


def _table_preview(element: Dict[str, Any], max_chars: int = 1800) -> str:
    rows: List[str] = []
    for row in element.get("rows") or []:
        cells: List[str] = []
        for cell in row.get("cells") or []:
            text = _element_text(cell)
            if text:
                cells.append(text)
        if cells:
            rows.append(" | ".join(cells))
    preview = normalize_whitespace(" || ".join(rows))
    if len(preview) > max_chars:
        return preview[:max_chars].rstrip() + "..."
    return preview


def _batch_size() -> int:
    """Keep CLI argument lists bounded; permit explicit local tuning."""
    try:
        return max(1, int(os.getenv("RAG_ODL_BATCH_SIZE", "8")))
    except ValueError:
        return 8


def _convert_batch(converter: Any, paths: Sequence[Path], output_dir: Path, image_output: str) -> None:
    _ensure_java_sort_compatibility()
    converter.convert(
        input_path=[str(path) for path in paths],
        output_dir=str(output_dir),
        format="json",
        quiet=True,
        table_method="default",
        reading_order="xycut",
        image_output=image_output,
        threads=os.getenv("RAG_ODL_THREADS", "1"),
    )


@contextmanager
def converted_documents(
    pdf_paths: Sequence[Path], *, image_output: str = "off"
) -> Iterator[tuple[Dict[Path, Dict[str, Any]], Path]]:
    """Convert a batch once and expose parsed vendor JSON only inside the context."""
    normalized_paths = [Path(path).resolve() for path in pdf_paths]
    if not normalized_paths:
        yield {}, Path.cwd()
        return

    converter = _load_converter()
    temp_root = _temp_root()
    with tempfile.TemporaryDirectory(prefix="radiotherapy-odl-", dir=str(temp_root) if temp_root else None) as raw_dir:
        output_dir = Path(raw_dir)
        for start in range(0, len(normalized_paths), _batch_size()):
            batch = normalized_paths[start : start + _batch_size()]
            try:
                _convert_batch(converter, batch, output_dir, image_output)
            except Exception as batch_error:  # pragma: no cover - third-party process detail varies by host
                if len(batch) == 1:
                    raise RuntimeError(f"OpenDataLoader conversion failed for {batch[0].name}: {batch_error}") from batch_error
                # The upstream CLI can abort an otherwise valid batch when one
                # document has an unusual PDF structure. Retry singly so the
                # failing filename is explicit and good documents still parse.
                for pdf_path in batch:
                    try:
                        _convert_batch(converter, [pdf_path], output_dir, image_output)
                    except Exception as single_error:
                        raise RuntimeError(
                            f"OpenDataLoader conversion failed for {pdf_path.name} after batch retry: {single_error}"
                        ) from single_error

        payloads: Dict[Path, Dict[str, Any]] = {}
        for pdf_path in normalized_paths:
            json_path = output_dir / f"{pdf_path.stem}.json"
            if not json_path.exists():
                raise RuntimeError(f"OpenDataLoader did not produce JSON for {pdf_path.name}.")
            with json_path.open("r", encoding="utf-8") as handle:
                payloads[pdf_path] = json.load(handle)
        yield payloads, output_dir


def document_metadata(pdf_paths: Sequence[Path]) -> Dict[Path, Dict[str, Any]]:
    """Return page-count and title metadata using the same parser as ingestion."""
    with converted_documents(pdf_paths) as (payloads, _):
        return {
            path: {
                "num_pages": _as_int(payload.get("number of pages")),
                "title": normalize_whitespace(str(payload.get("title") or "")),
                "element_count": len(payload.get("kids") or []),
            }
            for path, payload in payloads.items()
        }


def parsed_blocks_from_payload(
    payload: Dict[str, Any],
    *,
    doc_id: str,
    title: str,
    source_path: str,
) -> List[ParsedBlock]:
    """Map OpenDataLoader semantic elements onto stable project parsed blocks."""
    section = "UNKNOWN"
    subsection = "UNKNOWN"
    blocks: List[ParsedBlock] = []
    block_index = 0

    for element in payload.get("kids") or []:
        if not isinstance(element, dict):
            continue
        element_type = str(element.get("type") or "").lower()
        text = _element_text(element)
        if not text:
            continue

        page = max(1, _as_int(element.get("page number"), default=1))
        if element_type == "heading":
            level = _as_int(element.get("heading level"), default=6)
            if level <= 2:
                section = text
                subsection = "UNKNOWN"
            else:
                subsection = text
            block_type = "heading"
        elif element_type in TEXT_ELEMENT_TYPES:
            block_type = "table" if element_type == "table" else element_type.replace(" ", "_")
            if element_type == "table":
                text = _table_preview(element) or text
        else:
            continue

        blocks.append(
            ParsedBlock(
                block_id=f"{doc_id}_p{page:03d}_b{block_index:04d}",
                doc_id=doc_id,
                title=title,
                page_start=page,
                page_end=page,
                section=section,
                subsection=subsection,
                text=text,
                block_type=block_type,
                source_path=source_path,
            )
        )
        block_index += 1
    return blocks


def parse_documents(documents: Sequence[Dict[str, Any]]) -> Dict[str, List[ParsedBlock]]:
    """Parse manifest-like document records in one OpenDataLoader batch."""
    paths = [Path(str(document["pdf_path"])).resolve() for document in documents]
    result: Dict[str, List[ParsedBlock]] = {}
    with converted_documents(paths) as (payloads, _):
        for document, path in zip(documents, paths):
            doc_id = str(document["doc_id"])
            result[doc_id] = parsed_blocks_from_payload(
                payloads[path],
                doc_id=doc_id,
                title=str(document["title"]),
                source_path=str(document["source_path"]),
            )
    return result


def _nearest_caption(elements: Iterable[Dict[str, Any]], page: int, bbox: List[float]) -> str:
    candidates: List[tuple[float, str]] = []
    for element in elements:
        if str(element.get("type") or "").lower() != "caption":
            continue
        if _as_int(element.get("page number")) != page:
            continue
        text = _element_text(element)
        if not text:
            continue
        other = _as_bbox(element.get("bounding box"))
        distance = min(abs(other[1] - bbox[3]), abs(bbox[1] - other[3]))
        candidates.append((distance, text))
    return min(candidates, default=(0.0, ""), key=lambda item: item[0])[1]


def assets_from_payload(
    payload: Dict[str, Any],
    *,
    doc_id: str,
    title: str,
    source_path: str,
    save_images: bool,
    image_output_dir: Path | None,
    conversion_dir: Path,
) -> List[Dict[str, Any]]:
    """Create project asset records from OpenDataLoader table and image elements."""
    elements = [item for item in payload.get("kids") or [] if isinstance(item, dict)]
    table_index = 0
    image_index = 0
    records: List[PdfAssetRecord] = []

    for element in elements:
        element_type = str(element.get("type") or "").lower()
        if element_type not in {"table", "image"}:
            continue
        page = max(1, _as_int(element.get("page number"), default=1))
        bbox = _as_bbox(element.get("bounding box"))
        caption = _nearest_caption(elements, page, bbox)

        if element_type == "table":
            table_index += 1
            records.append(
                PdfAssetRecord(
                    asset_id=f"{doc_id}_p{page:03d}_table_{table_index:02d}",
                    doc_id=doc_id,
                    title=title,
                    source_path=source_path,
                    page=page,
                    asset_type="table",
                    bbox=bbox,
                    caption=caption,
                    rows=_as_int(element.get("number of rows")),
                    columns=_as_int(element.get("number of columns")),
                    text_preview=_table_preview(element),
                )
            )
            continue

        image_index += 1
        source_value = str(element.get("source") or "")
        source_file = conversion_dir / source_value if source_value else None
        extension = Path(source_value).suffix.lstrip(".") if source_value else None
        extracted_path = None
        asset_id = f"{doc_id}_p{page:03d}_image_{image_index:02d}"
        if save_images and source_file and source_file.exists() and image_output_dir:
            target_dir = image_output_dir / doc_id
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / f"{asset_id}.{extension or 'bin'}"
            shutil.copy2(source_file, target)
            extracted_path = str(target)
        records.append(
            PdfAssetRecord(
                asset_id=asset_id,
                doc_id=doc_id,
                title=title,
                source_path=source_path,
                page=page,
                asset_type="image",
                bbox=bbox,
                caption=caption,
                extension=extension or None,
                extracted_image_path=extracted_path,
            )
        )
    return [record.to_dict() for record in records]


def extract_assets_batch(documents: Sequence[Dict[str, Any]], *, save_images: bool, image_output_dir: Path | None) -> Dict[str, List[Dict[str, Any]]]:
    """Extract all metadata assets in one parser invocation."""
    paths = [Path(str(document["pdf_path"])).resolve() for document in documents]
    result: Dict[str, List[Dict[str, Any]]] = {}
    with converted_documents(paths, image_output="external" if save_images else "off") as (payloads, conversion_dir):
        for document, path in zip(documents, paths):
            doc_id = str(document["doc_id"])
            result[doc_id] = assets_from_payload(
                payloads[path],
                doc_id=doc_id,
                title=str(document["title"]),
                source_path=str(document["source_path"]),
                save_images=save_images,
                image_output_dir=image_output_dir,
                conversion_dir=conversion_dir,
            )
    return result
