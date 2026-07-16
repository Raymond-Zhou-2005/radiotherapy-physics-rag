"""Section-aware chunking logic with sentence-aware splitting and light de-duplication."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Dict, List

from src.schemas import ChunkRecord
from src.utils import count_approx_tokens, normalize_whitespace, split_sentences

DEFINITION_CUES = (
    "is referred to as",
    "is defined as",
    "refers to",
    "can be subdivided into",
)

TAG_PATTERNS = {
    "measurement": [
        re.compile(r"\bdosimetr(?:y|ic)\b", re.IGNORECASE),
        re.compile(r"\bdetector(?:s)?\b", re.IGNORECASE),
        re.compile(r"\bmeasurement(?:s)?\b", re.IGNORECASE),
        re.compile(r"\bphantom(?:s)?\b", re.IGNORECASE),
    ],
    "computation": [
        re.compile(r"\bmonte carlo\b", re.IGNORECASE),
        re.compile(r"\btreatment planning\b", re.IGNORECASE),
        re.compile(r"\banalytical model\b", re.IGNORECASE),
        re.compile(r"\bcalculation(?:s)?\b", re.IGNORECASE),
        re.compile(r"\bcomputational\b", re.IGNORECASE),
    ],
    "dose_reporting": [
        re.compile(r"\bdose reporting\b", re.IGNORECASE),
        re.compile(r"\bequivalent dose\b", re.IGNORECASE),
        re.compile(r"\borgan doses?\b", re.IGNORECASE),
        re.compile(r"\beffective dose\b", re.IGNORECASE),
        re.compile(r"\breport(?:ing)?\b", re.IGNORECASE),
    ],
    "risk": [
        re.compile(r"\bsecond(?:ary)? cancer\b", re.IGNORECASE),
        re.compile(r"\bcardiac toxicity\b", re.IGNORECASE),
        re.compile(r"\bfetal dose\b", re.IGNORECASE),
        re.compile(r"\bcataract\b", re.IGNORECASE),
        re.compile(r"\bpacemaker\b", re.IGNORECASE),
        re.compile(r"\blate effects?\b", re.IGNORECASE),
        re.compile(r"\brisk\b", re.IGNORECASE),
    ],
    "modality_specific": [
        re.compile(r"\bbrachytherapy\b", re.IGNORECASE),
        re.compile(r"\belectron therapy\b", re.IGNORECASE),
        re.compile(r"\bphoton therapy\b", re.IGNORECASE),
        re.compile(r"\bproton therapy\b", re.IGNORECASE),
        re.compile(r"\bcarbon ion therapy\b", re.IGNORECASE),
        re.compile(r"\btotal body irradiation\b", re.IGNORECASE),
        re.compile(r"\bconcomitant imaging doses\b", re.IGNORECASE),
    ],
}

RECOMMENDATION_SECTION_PATTERNS = [
    re.compile(r"\brecommend(?:ation|ations|ed)?\b", re.IGNORECASE),
]

RECOMMENDATION_SENTENCE_PATTERNS = [
    re.compile(r"\bwe recommend\b", re.IGNORECASE),
    re.compile(r"\bit is recommended\b", re.IGNORECASE),
    re.compile(r"\bare recommended\b", re.IGNORECASE),
    re.compile(r"\bwere recommended\b", re.IGNORECASE),
    re.compile(r"\brecommend(?:ation|ations|ed)?\b", re.IGNORECASE),
]


class SectionAwareChunker:
    """Chunk parsed blocks while preserving document structure."""

    def __init__(
        self,
        chunk_size_tokens: int = 280,
        chunk_overlap_tokens: int = 40,
        min_chunk_tokens: int = 90,
        definitional_microchunk_max_tokens: int = 180,
    ):
        self.chunk_size_tokens = chunk_size_tokens
        self.chunk_overlap_tokens = chunk_overlap_tokens
        self.min_chunk_tokens = min_chunk_tokens
        self.definitional_microchunk_max_tokens = definitional_microchunk_max_tokens

    def chunk_document(self, parsed_blocks: List[Dict]) -> List[ChunkRecord]:
        if not parsed_blocks:
            return []

        normalized_blocks = self._pre_split_large_blocks(parsed_blocks)
        grouped: Dict[tuple, List[Dict]] = defaultdict(list)
        for block in normalized_blocks:
            if block["block_type"] == "heading":
                continue
            key = (block["section"], block["subsection"])
            grouped[key].append(block)

        chunks: List[ChunkRecord] = []
        chunk_counter = 0

        for (_, _), blocks in grouped.items():
            current_blocks: List[Dict] = []
            current_tokens = 0

            for block in blocks:
                block_tokens = count_approx_tokens(block["text"])
                if current_blocks and current_tokens + block_tokens > self.chunk_size_tokens:
                    chunk = self._make_chunk(current_blocks, chunk_counter)
                    chunks.append(chunk)
                    chunk_counter += 1

                    overlap_target = self.chunk_overlap_tokens
                    if current_blocks and current_blocks[0]["section"] == "UNKNOWN":
                        overlap_target = min(20, self.chunk_overlap_tokens)

                    carry: List[Dict] = []
                    carry_tokens = 0
                    for prev in reversed(current_blocks):
                        prev_tokens = count_approx_tokens(prev["text"])
                        if prev_tokens > overlap_target and current_blocks[0]["section"] != "UNKNOWN":
                            continue
                        carry.insert(0, prev)
                        carry_tokens += prev_tokens
                        if carry_tokens >= overlap_target:
                            break
                    current_blocks = carry
                    current_tokens = carry_tokens

                current_blocks.append(block)
                current_tokens += block_tokens

            if current_blocks:
                chunk = self._make_chunk(current_blocks, chunk_counter)
                chunks.append(chunk)
                chunk_counter += 1

        merged = self._merge_tiny_chunks(chunks)
        microchunks = self._create_definition_microchunks(merged)
        all_chunks = merged + microchunks
        deduped = self._dedupe_adjacent_chunks(
            sorted(all_chunks, key=lambda c: (c.doc_id, c.page_start, c.page_end, c.chunk_id))
        )
        return self._renumber_chunks(deduped)

    def _pre_split_large_blocks(self, parsed_blocks: List[Dict]) -> List[Dict]:
        split_blocks: List[Dict] = []
        for block in parsed_blocks:
            if block["block_type"] == "heading":
                split_blocks.append(block)
                continue
            token_count = count_approx_tokens(block["text"])
            if token_count <= self.chunk_size_tokens:
                split_blocks.append(block)
                continue

            sentences = split_sentences(block["text"])
            if len(sentences) <= 1:
                split_blocks.append(block)
                continue

            current_sentences: List[str] = []
            current_tokens = 0
            local_idx = 0
            for sentence in sentences:
                sent_tokens = count_approx_tokens(sentence)
                if current_sentences and current_tokens + sent_tokens > self.chunk_size_tokens:
                    split_blocks.append(self._make_split_block(block, current_sentences, local_idx))
                    local_idx += 1
                    current_sentences = []
                    current_tokens = 0
                current_sentences.append(sentence)
                current_tokens += sent_tokens
            if current_sentences:
                split_blocks.append(self._make_split_block(block, current_sentences, local_idx))
        return split_blocks

    def _make_split_block(self, original_block: Dict, sentences: List[str], local_idx: int) -> Dict:
        new_block = dict(original_block)
        new_block["block_id"] = f"{original_block['block_id']}_s{local_idx:02d}"
        new_block["text"] = " ".join(sentences)
        return new_block

    def _make_chunk(self, blocks: List[Dict], chunk_index: int) -> ChunkRecord:
        first = blocks[0]
        last = blocks[-1]
        text = "\n".join(block["text"] for block in blocks)
        token_count = count_approx_tokens(text)
        tags = self._infer_tags(first["section"], first["subsection"], text, chunk_kind="standard")
        return ChunkRecord(
            chunk_id=f"{first['doc_id']}_c{chunk_index:04d}",
            doc_id=first["doc_id"],
            title=first["title"],
            section=first["section"],
            subsection=first["subsection"],
            page_start=first["page_start"],
            page_end=last["page_end"],
            text=text,
            token_count=token_count,
            source_path=first["source_path"],
            tags=tags,
            chunk_kind="standard",
            parent_chunk_id=None,
        )

    def _merge_tiny_chunks(self, chunks: List[ChunkRecord]) -> List[ChunkRecord]:
        if not chunks:
            return []
        merged: List[ChunkRecord] = []
        for chunk in chunks:
            if (
                merged
                and chunk.token_count < self.min_chunk_tokens
                and merged[-1].doc_id == chunk.doc_id
                and merged[-1].section == chunk.section
                and merged[-1].subsection == chunk.subsection
                and merged[-1].chunk_kind == chunk.chunk_kind == "standard"
            ):
                prev = merged[-1]
                prev.text = prev.text + "\n" + chunk.text
                prev.page_end = chunk.page_end
                prev.token_count = count_approx_tokens(prev.text)
                prev.tags = sorted(set(prev.tags + chunk.tags))
            else:
                merged.append(chunk)
        return merged

    def _create_definition_microchunks(self, chunks: List[ChunkRecord]) -> List[ChunkRecord]:
        microchunks: List[ChunkRecord] = []
        for chunk in chunks:
            if chunk.section == "UNKNOWN":
                continue
            lowered = chunk.text.lower()
            if not any(cue in lowered for cue in DEFINITION_CUES):
                continue
            sentences = split_sentences(chunk.text)
            if not sentences:
                continue
            for i, sentence in enumerate(sentences):
                if not any(cue in sentence.lower() for cue in DEFINITION_CUES):
                    continue
                start = max(0, i - 1)
                end = min(len(sentences), i + 2)
                snippet = " ".join(sentences[start:end])
                if count_approx_tokens(snippet) > self.definitional_microchunk_max_tokens:
                    continue
                micro = ChunkRecord(
                    chunk_id=f"{chunk.chunk_id}_def{i}",
                    doc_id=chunk.doc_id,
                    title=chunk.title,
                    section=chunk.section,
                    subsection=chunk.subsection,
                    page_start=chunk.page_start,
                    page_end=chunk.page_end,
                    text=snippet,
                    token_count=count_approx_tokens(snippet),
                    source_path=chunk.source_path,
                    tags=self._infer_tags(chunk.section, chunk.subsection, snippet, chunk_kind="definition_microchunk"),
                    chunk_kind="definition_microchunk",
                    parent_chunk_id=chunk.chunk_id,
                )
                microchunks.append(micro)
        return microchunks

    def _dedupe_adjacent_chunks(self, chunks: List[ChunkRecord]) -> List[ChunkRecord]:
        if not chunks:
            return []
        deduped = [chunks[0]]
        for chunk in chunks[1:]:
            prev = deduped[-1]
            if chunk.chunk_kind != "standard" or prev.chunk_kind != "standard":
                deduped.append(chunk)
                continue
            if (
                chunk.doc_id == prev.doc_id
                and chunk.section == prev.section
                and chunk.subsection == prev.subsection
                and self._too_similar_text(prev.text, chunk.text)
            ):
                continue
            deduped.append(chunk)
        return deduped

    def _too_similar_text(self, a: str, b: str) -> bool:
        a_words = set(a.lower().split())
        b_words = set(b.lower().split())
        if not a_words or not b_words:
            return False
        overlap = len(a_words & b_words) / max(1, min(len(a_words), len(b_words)))
        return overlap > 0.88

    def _infer_tags(self, section: str, subsection: str, text: str, chunk_kind: str) -> List[str]:
        haystack = normalize_whitespace(f"{section} {subsection} {text}")
        tags = [
            tag
            for tag, patterns in TAG_PATTERNS.items()
            if any(pattern.search(haystack) for pattern in patterns)
        ]
        if self._is_recommendation_tag(section, subsection, text):
            tags.append("recommendation")
        if chunk_kind == "definition_microchunk" or self._is_definition_tag(text):
            tags.append("definition")
        return sorted(set(tags))

    def _is_definition_tag(self, text: str) -> bool:
        lowered = normalize_whitespace(text).lower()
        return any(cue in lowered for cue in DEFINITION_CUES)

    def _is_recommendation_tag(self, section: str, subsection: str, text: str) -> bool:
        title_text = normalize_whitespace(f"{section} {subsection}")
        if any(pattern.search(title_text) for pattern in RECOMMENDATION_SECTION_PATTERNS):
            return True
        for sentence in split_sentences(text):
            if any(pattern.search(sentence) for pattern in RECOMMENDATION_SENTENCE_PATTERNS):
                return True
        return False

    def _renumber_chunks(self, chunks: List[ChunkRecord]) -> List[ChunkRecord]:
        old_to_new: Dict[str, str] = {}
        for idx, chunk in enumerate(chunks):
            new_id = f"{chunk.doc_id}_c{idx:04d}"
            old_to_new[chunk.chunk_id] = new_id
            chunk.chunk_id = new_id

        for chunk in chunks:
            if chunk.parent_chunk_id is not None:
                chunk.parent_chunk_id = old_to_new.get(chunk.parent_chunk_id, chunk.parent_chunk_id)
        return chunks
