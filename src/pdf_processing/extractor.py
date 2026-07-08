"""PDF parsing logic.

Improved heuristic parser for long technical PDFs with clear sections.
This revision focuses on:
1. Better reading order for two-column reports.
2. Stronger heading detection.
3. More aggressive front-matter and footer cleanup.
4. Cleaner paragraph assembly for downstream chunking and citation.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Dict, List, Optional

import fitz  # PyMuPDF

from src.schemas import ParsedBlock
from src.utils import normalize_whitespace


MAIN_SECTION_RE = re.compile(r"^\d+\.\s+[A-Z][A-Z0-9 \-,:()/]{3,}$")
NUMBERED_TITLE_SECTION_RE = re.compile(r"^\d{1,2}\.\s+\S.{2,120}$")
NUMERIC_SUBSECTION_RE = re.compile(r"^\d{1,2}\.\d{1,2}\s+\S.{2,120}$")
SUBSECTION_RE = re.compile(r"^\d+\.[A-Z]\.?(?:\s+)[A-Z].{0,100}$")
SUBSUBSECTION_RE = re.compile(r"^\d+\.[A-Z]\.\d+\.?(?:\s+)[A-Z].{0,120}$")
DEEP_SECTION_RE = re.compile(r"^\d+\.[A-Z]\.\d+\.\d+\.?(?:\s+)[A-Z].{0,140}$")
HEADING_CONTINUATION_RE = re.compile(r"^[A-Z0-9()\-/ ]{2,24}$")
PAGE_NUMBER_ONLY_RE = re.compile(r"^[ex]?\d+$", re.IGNORECASE)
DOWNLOAD_NOISE_RE = re.compile(r"downloaded from|terms and conditions|wiley online library", re.IGNORECASE)
FRONT_MATTER_RE = re.compile(
    r"received \d|revised \d|accepted for publication|published \d|key words:|doi\.org|10\.1002/|© \d{4}|american association of physicists in medicine",
    re.IGNORECASE,
)
JOURNAL_FOOTER_RE = re.compile(
    r"med\.\s*phys\.|medical physics,|kry et al\.:|\be\d{3}\b|0094-2405/\d{4}",
    re.IGNORECASE,
)
FIGURE_TABLE_RE = re.compile(r"^(fig\.|figure\s+\d+|table\s+[ivx\d]+)", re.IGNORECASE)
AFFILIATION_RE = re.compile(
    r"department of|departments of|university|hospital|medical school|cancer center|institute|rensselaer polytechnic",
    re.IGNORECASE,
)
AUTHOR_LIST_RE = re.compile(
    r"^[A-Z][A-Za-z\-.']+(\s+[A-Z][A-Za-z\-.']+){1,4}$"
)


@dataclass
class LineRecord:
    """A single extracted line with positional metadata."""

    text: str
    x0: float
    x1: float
    y0: float
    y1: float
    font_size: float
    page_num: int
    column_id: int


@dataclass
class ParagraphBuffer:
    """Mutable buffer used while grouping lines into a paragraph block."""

    lines: List[str]
    page_start: int
    page_end: int

    def add_line(self, line: LineRecord) -> None:
        self.lines.append(line.text)
        self.page_end = line.page_num

    def text(self) -> str:
        if not self.lines:
            return ""
        pieces: List[str] = []
        prev = ""
        for line in self.lines:
            clean = normalize_whitespace(line)
            if not clean:
                continue
            if prev.endswith("-") and clean:
                pieces[-1] = pieces[-1][:-1] + clean
            else:
                pieces.append(clean)
            prev = clean
        return normalize_whitespace(" ".join(pieces))


class PDFStructuredParser:
    """Parse a technical PDF into structured paragraph blocks."""

    def __init__(self) -> None:
        self.current_section = "UNKNOWN"
        self.current_subsection = "UNKNOWN"

    def parse(self, pdf_path: Path, doc_id: str, title: str, source_path: str | None = None) -> List[ParsedBlock]:
        self.current_section = "UNKNOWN"
        self.current_subsection = "UNKNOWN"
        doc = fitz.open(pdf_path)
        display_source_path = source_path or str(pdf_path)
        all_page_lines: Dict[int, List[LineRecord]] = {}
        top_counter: Counter[str] = Counter()
        bottom_counter: Counter[str] = Counter()

        for page_index in range(len(doc)):
            page = doc[page_index]
            lines = self._extract_lines_from_page(page, page_index + 1)
            all_page_lines[page_index + 1] = lines
            page_height = page.rect.height
            for line in lines:
                norm = self._normalize_line_for_repetition(line.text)
                if not norm:
                    continue
                if line.y0 < page_height * 0.12:
                    top_counter[norm] += 1
                if line.y1 > page_height * 0.88:
                    bottom_counter[norm] += 1

        repeated_top = {t for t, c in top_counter.items() if c >= 3}
        repeated_bottom = {t for t, c in bottom_counter.items() if c >= 3}

        blocks: List[ParsedBlock] = []
        block_idx = 0

        for page_num in range(1, len(doc) + 1):
            page = doc[page_num - 1]
            page_height = page.rect.height

            lines = []
            for line in all_page_lines[page_num]:
                norm = self._normalize_line_for_repetition(line.text)
                if self._should_drop_line(line, norm, repeated_top, repeated_bottom, page_height):
                    continue
                lines.append(line)

            lines = self._page_specific_cleanup(lines, page_num)

            if not lines:
                continue

            page_text = normalize_whitespace(" ".join(line.text for line in lines))
            if "table of contents" in page_text.lower():
                intro_candidates = [
                    idx for idx, line in enumerate(lines)
                    if normalize_whitespace(line.text).upper().startswith("1. INTRODUCTION")
                ]
                if not intro_candidates:
                    continue
                lines = lines[intro_candidates[-1]:]

            page_blocks = self._group_lines_into_paragraphs(lines)
            for para in page_blocks:
                text = para.text()
                if not text:
                    continue
                if self._looks_like_noise_block(text):
                    continue

                heading_level = self._classify_heading(text)
                if heading_level is not None:
                    self._update_section_state(text, heading_level)
                    block_type = "heading"
                else:
                    block_type = "paragraph"

                block_section = self.current_section
                block_subsection = self.current_subsection
                if block_type != "heading" and block_section == "UNKNOWN" and para.page_start <= 2:
                    block_section = "FRONT_MATTER"
                    block_subsection = "FRONT_MATTER"

                block = ParsedBlock(
                    block_id=f"{doc_id}_p{para.page_start:03d}_b{block_idx:04d}",
                    doc_id=doc_id,
                    title=title,
                    page_start=para.page_start,
                    page_end=para.page_end,
                    section=block_section,
                    subsection=block_subsection,
                    text=text,
                    block_type=block_type,
                    source_path=display_source_path,
                )
                blocks.append(block)
                block_idx += 1

        return blocks

    def _extract_lines_from_page(self, page: fitz.Page, page_num: int) -> List[LineRecord]:
        data = page.get_text("dict")
        raw_lines: List[LineRecord] = []
        page_width = page.rect.width

        for block in data.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                spans = line.get("spans", [])
                if not spans:
                    continue
                text = "".join(span.get("text", "") for span in spans).strip()
                if not text:
                    continue
                bbox = line.get("bbox", [0, 0, 0, 0])
                x0 = float(bbox[0])
                x1 = float(bbox[2])
                y0 = float(bbox[1])
                y1 = float(bbox[3])
                font_size = median([float(span.get("size", 0.0)) for span in spans])

                center_x = (x0 + x1) / 2.0
                if x0 < page_width * 0.2 and x1 > page_width * 0.8:
                    column_id = -1
                else:
                    column_id = 0 if center_x < page_width * 0.5 else 1

                raw_lines.append(
                    LineRecord(
                        text=text,
                        x0=x0,
                        x1=x1,
                        y0=y0,
                        y1=y1,
                        font_size=font_size,
                        page_num=page_num,
                        column_id=column_id,
                    )
                )

        raw_lines.sort(key=lambda line: ((-1 if line.column_id < 0 else line.column_id), line.y0, line.x0))
        return raw_lines

    def _normalize_line_for_repetition(self, text: str) -> str:
        text = normalize_whitespace(text).lower()
        text = re.sub(r"\s+", " ", text)
        if PAGE_NUMBER_ONLY_RE.fullmatch(text):
            return ""
        return text

    def _should_drop_line(
        self,
        line: LineRecord,
        normalized_text: str,
        repeated_top: set[str],
        repeated_bottom: set[str],
        page_height: float,
    ) -> bool:
        if not normalized_text:
            return True
        if DOWNLOAD_NOISE_RE.search(normalized_text):
            return True
        if PAGE_NUMBER_ONLY_RE.fullmatch(normalized_text):
            return True
        if FRONT_MATTER_RE.search(normalized_text):
            return True
        if JOURNAL_FOOTER_RE.search(normalized_text):
            return True
        if FIGURE_TABLE_RE.match(normalized_text):
            return True
        if line.y0 < page_height * 0.12 and normalized_text in repeated_top:
            return True
        if line.y1 > page_height * 0.88 and normalized_text in repeated_bottom:
            return True
        return False

    def _page_specific_cleanup(self, lines: List[LineRecord], page_num: int) -> List[LineRecord]:
        if not lines:
            return lines

        cleaned = lines

        if page_num == 1:
            start_idx = 0
            for idx, line in enumerate(cleaned):
                t = line.text.lower()
                if "the introduction of advanced techniques and technology" in t:
                    start_idx = idx
                    break
            if start_idx > 0:
                cleaned = cleaned[start_idx:]

            tmp: List[LineRecord] = []
            for line in cleaned:
                t = line.text.strip()
                tl = t.lower()
                if AFFILIATION_RE.search(tl):
                    continue
                if AUTHOR_LIST_RE.match(t) and len(t.split()) <= 5:
                    continue
                if "aapm tg 158:" in tl and len(t) > 40:
                    continue
                tmp.append(line)
            cleaned = tmp

        return cleaned

    def _group_lines_into_paragraphs(self, lines: List[LineRecord]) -> List[ParagraphBuffer]:
        if not lines:
            return []

        heights = [max(1.0, line.y1 - line.y0) for line in lines]
        typical_height = median(heights) if heights else 12.0
        gap_threshold = typical_height * 1.35

        paragraphs: List[ParagraphBuffer] = []
        current: Optional[ParagraphBuffer] = None
        prev_line: Optional[LineRecord] = None

        for line in lines:
            line_heading = self._classify_heading(line.text)
            start_new = False

            if current is None:
                start_new = True
            else:
                current_first = normalize_whitespace(current.lines[0]) if current.lines else ""
                current_is_heading = self._classify_heading(current_first) is not None
                continuation = (
                    current_is_heading
                    and HEADING_CONTINUATION_RE.match(normalize_whitespace(line.text)) is not None
                    and len(normalize_whitespace(line.text).split()) <= 6
                    and len(current.lines) <= 2
                )

                if current_is_heading and not continuation:
                    start_new = True
                elif line_heading is not None:
                    start_new = True
                elif prev_line is not None:
                    if line.column_id != prev_line.column_id:
                        start_new = True
                    elif (line.y0 - prev_line.y1) > gap_threshold:
                        start_new = True
                    elif line.y0 < prev_line.y0 - typical_height:
                        start_new = True

            if start_new:
                current = ParagraphBuffer(lines=[], page_start=line.page_num, page_end=line.page_num)
                paragraphs.append(current)

            current.add_line(line)
            prev_line = line

        return paragraphs

    def _looks_like_noise_block(self, text: str) -> bool:
        lower = text.lower()
        if FRONT_MATTER_RE.search(lower):
            return True
        if JOURNAL_FOOTER_RE.search(lower):
            return True
        if "table of contents" in lower:
            return True
        if FIGURE_TABLE_RE.match(lower):
            return True
        if "downloaded from" in lower:
            return True
        if lower.startswith("10.1002/"):
            return True
        return False

    def _classify_heading(self, text: str) -> Optional[str]:
        text = normalize_whitespace(text)

        if self.current_section == "REFERENCES" and text != "REFERENCES":
            return None
        if len(text) > 120:
            return None
        if text.count(". ") > 1:
            return None
        if len(text.split()) > 18:
            return None

        if MAIN_SECTION_RE.match(text):
            after_number = re.sub(r"^\d+\.\s+", "", text)
            alpha_chars = [ch for ch in after_number if ch.isalpha()]
            if alpha_chars:
                upper_ratio = sum(ch.isupper() for ch in alpha_chars) / len(alpha_chars)
                if upper_ratio > 0.75:
                    return "main"

        if DEEP_SECTION_RE.match(text):
            return "deep"
        if NUMERIC_SUBSECTION_RE.match(text) and self._looks_like_numbered_heading(text):
            return "sub"
        if SUBSUBSECTION_RE.match(text):
            return "subsub"
        if SUBSECTION_RE.match(text):
            return "sub"
        if NUMBERED_TITLE_SECTION_RE.match(text) and self._looks_like_numbered_heading(text):
            return "main"
        if text == "REFERENCES":
            return "main"

        return None

    def _looks_like_numbered_heading(self, text: str) -> bool:
        """Accept title-case numbered report headings without catching citations."""
        body = re.sub(r"^\d{1,2}(?:\.\d{1,2})?\s+", "", text).strip()
        if not body or not re.search(r"[A-Za-z]{2}", body):
            return False
        if body.endswith((".", ",", ";", ":")):
            return False
        words = [word for word in re.split(r"\s+", body) if re.search(r"[A-Za-z]", word)]
        if not (2 <= len(words) <= 14):
            return False
        content_words = [word for word in words if word.lower() not in {"and", "or", "of", "the", "in", "for", "to"}]
        if not content_words:
            return False
        title_like = sum(1 for word in content_words if word[:1].isupper() or word.isupper()) / len(content_words)
        return title_like >= 0.55

    def _update_section_state(self, heading_text: str, heading_level: str) -> None:
        heading_text = normalize_whitespace(heading_text)
        if heading_level == "main":
            self.current_section = heading_text
            self.current_subsection = "UNKNOWN"
        elif heading_level in {"sub", "subsub", "deep"}:
            self.current_subsection = heading_text
