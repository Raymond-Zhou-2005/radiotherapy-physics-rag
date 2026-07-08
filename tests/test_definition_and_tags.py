from src.chunking.splitter import SectionAwareChunker
from src.retrieval.heuristics import compute_rerank_adjustment


def test_definition_microchunk_is_preserved():
    chunker = SectionAwareChunker(chunk_size_tokens=120, chunk_overlap_tokens=10, min_chunk_tokens=1)
    parsed_blocks = [
        {
            "block_type": "paragraph",
            "block_id": "b1",
            "doc_id": "doc1",
            "title": "Doc 1",
            "section": "1. INTRODUCTION",
            "subsection": "UNKNOWN",
            "page_start": 1,
            "page_end": 1,
            "text": (
                "Background text. The dose outside the PTV is referred to as nontarget dose. "
                "Additional context sentence."
            ),
            "source_path": "dummy.pdf",
        }
    ]
    chunks = chunker.chunk_document(parsed_blocks)
    kinds = [chunk.chunk_kind for chunk in chunks]
    assert "definition_microchunk" in kinds
    assert any(chunk.parent_chunk_id is not None for chunk in chunks if chunk.chunk_kind == "definition_microchunk")


def test_recommendation_tag_is_not_added_from_generic_should_be_phrase():
    chunker = SectionAwareChunker(chunk_size_tokens=200, chunk_overlap_tokens=20, min_chunk_tokens=1)
    parsed_blocks = [
        {
            "block_type": "paragraph",
            "block_id": "b1",
            "doc_id": "doc1",
            "title": "Doc 1",
            "section": "1. INTRODUCTION",
            "subsection": "UNKNOWN",
            "page_start": 1,
            "page_end": 1,
            "text": "The dose outside the PTV is referred to as nontarget dose and should be minimized.",
            "source_path": "dummy.pdf",
        }
    ]
    chunks = chunker.chunk_document(parsed_blocks)
    standard = next(chunk for chunk in chunks if chunk.chunk_kind == "standard")
    assert "recommendation" not in standard.tags


def test_summary_like_recommendation_chunk_is_penalized_for_definition_query():
    chunk = {
        "section": "8. RECOMMENDATIONS",
        "subsection": "UNKNOWN",
        "text": "This report provides guidance for physicists managing cases where nontarget doses are a concern.",
        "token_count": 25,
        "tags": ["recommendation"],
        "chunk_kind": "standard",
    }
    adjustment = compute_rerank_adjustment("Define nontarget dose.", chunk)
    assert adjustment < 0
