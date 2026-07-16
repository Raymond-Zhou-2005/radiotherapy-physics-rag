"""Utility helpers used across scripts."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Sequence

WORD_RE = re.compile(r"\b\w+\b", re.UNICODE)
SENTENCE_BOUNDARY_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"“(])")


def ensure_dir(path: Path) -> None:
    """Create a directory if it does not already exist."""
    path.mkdir(parents=True, exist_ok=True)



def read_jsonl(path: Path) -> List[Dict]:
    """Read a JSONL file into memory."""
    records: List[Dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records



def iter_jsonl(path: Path) -> Iterator[Dict]:
    """Stream records from a JSONL file one at a time."""
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)



def write_jsonl(path: Path, records: Iterable[Dict]) -> None:
    """Write an iterable of dictionaries to JSONL."""
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")



def write_json(path: Path, payload: Dict | List) -> None:
    """Write JSON with a stable UTF-8 encoding and indentation."""
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")



def sha256_file(path: Path) -> str:
    """Return the SHA256 hash of a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()



def slugify_filename(name: str) -> str:
    """Make a file or title safe for use as a simple document ID."""
    name = name.lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")



def normalize_whitespace(text: str) -> str:
    """Collapse repeated whitespace so the output is easier to index."""
    text = text.replace("\u00ad", "")
    text = text.replace("‐", "-")
    text = text.replace("‑", "-")
    text = text.replace("‒", "-")
    text = text.replace("–", "-")
    text = text.replace("—", "-")
    text = text.replace("ﬁ", "fi")
    text = text.replace("ﬂ", "fl")
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()



def simple_tokenize(text: str) -> List[str]:
    """A lightweight tokenizer used for BM25 and token counting."""
    return [t.lower() for t in WORD_RE.findall(text)]



def count_approx_tokens(text: str) -> int:
    """Approximate token count using whitespace-style word units."""
    return len(simple_tokenize(text))



def split_sentences(text: str) -> List[str]:
    """Split paragraph text into approximate sentences.

    This splitter is intentionally simple and stable. It works well enough for
    scientific prose and allows the chunker to isolate short definition-focused
    passages instead of keeping them inside very long introduction chunks.
    """
    text = normalize_whitespace(text)
    if not text:
        return []
    parts = SENTENCE_BOUNDARY_RE.split(text)
    return [normalize_whitespace(p) for p in parts if normalize_whitespace(p)]



def top_k_indices(scores: Sequence[float], k: int) -> List[int]:
    """Return indices of the top-k highest scores."""
    indexed = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    return [idx for idx, _ in indexed[:k]]
