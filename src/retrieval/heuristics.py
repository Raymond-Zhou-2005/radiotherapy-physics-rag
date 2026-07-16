"""Lightweight task-aware retrieval and reranking heuristics.

These heuristics are designed for structured technical reports. They are not a
replacement for neural retrieval or reranking. They add small, transparent
bonuses when a chunk looks like a definition, a recommendation, or a section
locator answer.
"""

from __future__ import annotations

import re
from typing import Dict, Optional, Set

from src.utils import normalize_whitespace, split_sentences

DEFINITION_PATTERNS = [
    re.compile(r"\bis referred to as\b", re.IGNORECASE),
    re.compile(r"\bis defined as\b", re.IGNORECASE),
    re.compile(r"\brefers to\b", re.IGNORECASE),
    re.compile(r"\bcan be subdivided into\b", re.IGNORECASE),
]

SECTION_LOCATOR_PATTERNS = [
    re.compile(r"^which section", re.IGNORECASE),
    re.compile(r"^where does", re.IGNORECASE),
]

DEFINITION_QUERY_PATTERNS = [
    re.compile(r"^what is\b", re.IGNORECASE),
    re.compile(r"^define\b", re.IGNORECASE),
    re.compile(r"\baccording to\b", re.IGNORECASE),
]

RECOMMENDATION_QUERY_PATTERNS = [
    re.compile(r"\brecommend", re.IGNORECASE),
    re.compile(r"\bguidance", re.IGNORECASE),
    re.compile(r"\bshould\b", re.IGNORECASE),
]

COMPARISON_QUERY_PATTERNS = [
    re.compile(r"^compare\b", re.IGNORECASE),
    re.compile(r"\bdifference\b", re.IGNORECASE),
    re.compile(r"\bversus\b|\bvs\b", re.IGNORECASE),
]

MODALITY_HINTS = (
    "brachytherapy",
    "electron therapy",
    "photon therapy",
    "proton therapy",
    "carbon ion therapy",
    "total body irradiation",
    "concomitant imaging doses",
)

SUMMARY_SECTION_HINTS = (
    "8. RECOMMENDATIONS",
    "6. TECHNIQUES TO MINIMIZE NONTARGET DOSE",
)

SUMMARY_TEXT_PATTERNS = [
    re.compile(r"\bthis report provides\b", re.IGNORECASE),
    re.compile(r"\bthis report aims to\b", re.IGNORECASE),
    re.compile(r"\bto those ends\b", re.IGNORECASE),
    re.compile(r"\bthe focus of this report\b", re.IGNORECASE),
    re.compile(r"\bprovides guidance\b", re.IGNORECASE),
]

REPORT_CUE_PATTERNS = [
    ("tg", re.compile(r"\b(?:tg|task\s*group)\s*[-#:]?\s*(\d+[a-z]?)\b", re.IGNORECASE)),
    ("report", re.compile(r"\b(?:aapm\s*)?(?:report|rpt)\s*(?:no\.?|number|#)?\s*[-#:]?\s*(\d+[a-z]?)\b", re.IGNORECASE)),
    ("trs", re.compile(r"\btrs\s*[-#:]?\s*(\d+[a-z]?)\b", re.IGNORECASE)),
    ("tecdoc", re.compile(r"\btecdoc\s*[-#:]?\s*(\d+[a-z]?)\b", re.IGNORECASE)),
    ("hhr", re.compile(r"\b(?:hhr|human\s+health\s+reports?\s*(?:no\.?|number)?)\s*[-#:]?\s*(\d+[a-z]?)\b", re.IGNORECASE)),
    ("hhs", re.compile(r"\b(?:hhs|human\s+health\s+series\s*(?:no\.?|number)?)\s*[-#:]?\s*(\d+[a-z]?)\b", re.IGNORECASE)),
    ("ssg", re.compile(r"\bssg\s*[-#:]?\s*(\d+[a-z]?)\b", re.IGNORECASE)),
    ("srs", re.compile(r"\bsrs\s*[-#:]?\s*(\d+[a-z]?)\b", re.IGNORECASE)),
    ("pub", re.compile(r"\bpub(?:lication)?\s*[-#:]?\s*(\d+[a-z]?)\b", re.IGNORECASE)),
]

TITLE_STOPWORDS = {
    "aapm",
    "iaea",
    "report",
    "reports",
    "publication",
    "radiation",
    "radiotherapy",
    "therapy",
    "physics",
    "quality",
    "assurance",
    "guidance",
    "evidence",
    "grounded",
    "matter",
    "covers",
    "cover",
    "what",
    "which",
    "does",
    "that",
    "would",
    "for",
    "and",
    "the",
    "with",
}


def get_query_type(query: str) -> str:
    q = normalize_whitespace(query)
    if any(p.search(q) for p in SECTION_LOCATOR_PATTERNS):
        return "section_locator"
    if any(p.search(q) for p in DEFINITION_QUERY_PATTERNS):
        return "definition"
    if any(p.search(q) for p in RECOMMENDATION_QUERY_PATTERNS):
        return "recommendation"
    if any(p.search(q) for p in COMPARISON_QUERY_PATTERNS):
        return "comparison"
    return "general"



def extract_query_focus(query: str) -> Optional[str]:
    """Best-effort extraction of the main concept from a definition query."""
    q = normalize_whitespace(query)
    m = re.match(r"(?i)^what is\s+(.+?)(?:\s+according to.*)?\??$", q)
    if m:
        return normalize_whitespace(m.group(1)).lower()
    m = re.match(r"(?i)^define\s+(.+?)\??$", q)
    if m:
        return normalize_whitespace(m.group(1)).lower()
    return None


def extract_report_cues(text: str) -> Set[str]:
    """Extract normalized source identifiers such as tg:100 or trs:398."""
    normalized = normalize_whitespace(text.replace("_", " ").replace("-", " "))
    cues: Set[str] = set()
    for kind, pattern in REPORT_CUE_PATTERNS:
        for match in pattern.finditer(normalized):
            number = match.group(1).lower().lstrip("0") or "0"
            cues.add(f"{kind}:{number}")
    return cues


def report_title_terms(text: str) -> Set[str]:
    terms = {
        term
        for term in re.findall(r"[a-zA-Z][a-zA-Z0-9]{2,}", text.lower())
        if term not in TITLE_STOPWORDS and not term.isdigit()
    }
    return terms


def compute_report_match_bonus(query: str, chunk: Dict) -> float:
    """Reward exact report cues and mild title overlap for similar-report ranking."""
    query_cues = extract_report_cues(query)
    source_text = " ".join(
        str(chunk.get(key, "") or "")
        for key in ("doc_id", "title", "source_path")
    )
    chunk_cues = extract_report_cues(source_text)

    bonus = 0.0
    if query_cues:
        overlap = query_cues & chunk_cues
        if overlap:
            bonus += 0.46 + min(0.10, 0.03 * len(overlap))
        elif chunk_cues:
            bonus -= 0.18

    query_terms = report_title_terms(query)
    title_terms = report_title_terms(source_text)
    if query_terms and title_terms:
        ratio = len(query_terms & title_terms) / max(1, len(query_terms))
        if ratio >= 0.45:
            bonus += min(0.18, 0.08 + ratio * 0.15)
        elif ratio >= 0.25:
            bonus += 0.05

    return bonus



def keyword_overlap_ratio(query: str, text: str) -> float:
    q_terms = set(re.findall(r"[a-zA-Z]{3,}", query.lower()))
    t_terms = set(re.findall(r"[a-zA-Z]{3,}", text.lower()))
    if not q_terms or not t_terms:
        return 0.0
    return len(q_terms & t_terms) / len(q_terms)



def has_definition_cue(text: str) -> bool:
    lowered = normalize_whitespace(text).lower()
    return any(p.search(lowered) for p in DEFINITION_PATTERNS)



def chunk_has_tag(chunk: Dict, tag: str) -> bool:
    return tag.lower() in {str(t).lower() for t in chunk.get("tags", [])}



def get_chunk_kind(chunk: Dict) -> str:
    return str(chunk.get("chunk_kind", "standard"))



def is_front_matter(chunk: Dict) -> bool:
    section = (chunk.get("section", "") or "").upper()
    subsection = (chunk.get("subsection", "") or "").upper()
    text = normalize_whitespace(chunk.get("text", "") or "")
    page_start = int(chunk.get("page_start", 999))
    if section == "FRONT_MATTER":
        return True
    if section == "UNKNOWN" and subsection == "UNKNOWN" and page_start <= 6:
        if re.search(r"\.{3,}\s*\d{1,3}", text):
            return True
        if "contents" in text.lower() or "table of contents" in text.lower():
            return True
    return False


def is_references(chunk: Dict) -> bool:
    return (chunk.get("section", "") or "").upper().startswith("REFERENCES")



def is_modality_specific(chunk: Dict) -> bool:
    if chunk_has_tag(chunk, "modality_specific"):
        return True
    text = normalize_whitespace(
        f"{chunk.get('section', '')} {chunk.get('subsection', '')} {chunk.get('text', '')}"
    ).lower()
    return any(hint in text for hint in MODALITY_HINTS)



def is_recommendation_chunk(chunk: Dict) -> bool:
    if chunk_has_tag(chunk, "recommendation"):
        return True
    text = normalize_whitespace(f"{chunk.get('section', '')} {chunk.get('subsection', '')}").lower()
    return "recommend" in text



def is_summary_like_chunk(chunk: Dict) -> bool:
    section = normalize_whitespace(chunk.get("section", "") or "").upper()
    text = normalize_whitespace(chunk.get("text", "") or "")
    if any(section.startswith(hint) for hint in SUMMARY_SECTION_HINTS):
        return True
    return any(pattern.search(text) for pattern in SUMMARY_TEXT_PATTERNS)



def has_focus_definition_sentence(text: str, focus: Optional[str]) -> bool:
    if not focus:
        return False
    sentences = split_sentences(text)
    if not sentences:
        return False
    for sentence in sentences:
        lowered = sentence.lower()
        if focus in lowered and any(pattern.search(lowered) for pattern in DEFINITION_PATTERNS):
            return True
    return False



def compute_chunk_bonus(query: str, chunk: Dict) -> float:
    qtype = get_query_type(query)
    text = chunk.get("text", "")
    section = chunk.get("section", "") or ""
    subsection = chunk.get("subsection", "") or ""
    haystack = f"{section} {subsection} {text}".lower()

    bonus = 0.0
    focus = extract_query_focus(query)
    has_cue = has_definition_cue(text)
    focus_definition_match = has_focus_definition_sentence(text, focus)
    chunk_kind = get_chunk_kind(chunk)
    recommendation_like = is_recommendation_chunk(chunk)
    summary_like = is_summary_like_chunk(chunk)
    front_matter = is_front_matter(chunk)
    references = is_references(chunk)

    bonus += compute_report_match_bonus(query, chunk)

    if front_matter:
        bonus -= 0.18
    if references and "reference" not in query.lower():
        bonus -= 0.12

    if qtype == "definition":
        if section.upper().startswith("1. INTRODUCTION"):
            bonus += 0.18
        if chunk_kind == "definition_microchunk":
            bonus += 0.22
        if has_cue:
            bonus += 0.18
        if chunk_has_tag(chunk, "definition"):
            bonus += 0.06
        if focus and focus in haystack:
            bonus += 0.10
        if focus_definition_match:
            bonus += 0.24
        if is_modality_specific(chunk) and not focus_definition_match:
            bonus -= 0.20
        if recommendation_like and not focus_definition_match and not section.upper().startswith("1. INTRODUCTION"):
            bonus -= 0.10
        if summary_like and not focus_definition_match and not has_cue:
            bonus -= 0.14
        if not section.upper().startswith("1. INTRODUCTION") and not has_cue:
            bonus -= 0.10
        if chunk.get("token_count", 0) > 420:
            bonus -= 0.05
        if front_matter:
            bonus -= 0.08

    elif qtype == "recommendation":
        if "recommend" in section.lower() or "recommend" in subsection.lower():
            bonus += 0.18
        if recommendation_like:
            bonus += 0.10

    elif qtype == "section_locator":
        if keyword_overlap_ratio(query, f"{section} {subsection}") > 0.2:
            bonus += 0.15
        if section != "UNKNOWN":
            bonus += 0.03

    elif qtype == "comparison":
        if "vs" in subsection.lower() or "versus" in subsection.lower() or "compare" in text.lower():
            bonus += 0.10
        if section.upper().startswith(("4. MEASUREMENT", "5. COMPUTATIONAL", "6. TECHNIQUES")):
            bonus += 0.04

    if text.strip().startswith(("FIG.", "TABLE ")):
        bonus -= 0.10

    return bonus



def compute_rerank_adjustment(query: str, chunk: Dict) -> float:
    """Additional task-specific rerank adjustment.

    Retrieval heuristics are intentionally broad. Rerank adjustments are stricter,
    because they are applied after candidate recall.
    """
    qtype = get_query_type(query)
    text = chunk.get("text", "") or ""
    section = (chunk.get("section", "") or "").upper()
    subsection = (chunk.get("subsection", "") or "").upper()
    bonus = 0.0
    focus = extract_query_focus(query)
    has_cue = has_definition_cue(text)
    focus_definition_match = has_focus_definition_sentence(text, focus)
    chunk_kind = get_chunk_kind(chunk)
    recommendation_like = is_recommendation_chunk(chunk)
    summary_like = is_summary_like_chunk(chunk)
    front_matter = is_front_matter(chunk)
    references = is_references(chunk)

    bonus += compute_report_match_bonus(query, chunk)

    if front_matter:
        bonus -= 0.22
    if references and "reference" not in query.lower():
        bonus -= 0.16

    if qtype == "definition":
        if section.startswith("1. INTRODUCTION"):
            bonus += 0.24
        if chunk_kind == "definition_microchunk":
            bonus += 0.26
        if has_cue:
            bonus += 0.16
        if chunk_has_tag(chunk, "definition"):
            bonus += 0.08
        if focus and focus in f"{section} {subsection} {text}".lower():
            bonus += 0.08
        if focus_definition_match:
            bonus += 0.24
        if is_modality_specific(chunk) and not focus_definition_match:
            bonus -= 0.30
        if recommendation_like and not focus_definition_match and not section.startswith("1. INTRODUCTION"):
            bonus -= 0.16
        if summary_like and not focus_definition_match and not has_cue:
            bonus -= 0.24
        if not section.startswith("1. INTRODUCTION") and not has_cue:
            bonus -= 0.20
        if chunk.get("token_count", 0) > 360:
            bonus -= 0.05
        if front_matter:
            bonus -= 0.12
        if text.strip().startswith(("FIG.", "TABLE ")):
            bonus -= 0.15
    elif qtype == "recommendation":
        if "RECOMMEND" in section or "RECOMMEND" in subsection:
            bonus += 0.18
        if recommendation_like:
            bonus += 0.08
    elif qtype == "section_locator":
        if keyword_overlap_ratio(query, f"{section} {subsection}") > 0.25:
            bonus += 0.12

    return bonus
