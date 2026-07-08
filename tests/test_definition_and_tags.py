from src.chunking.splitter import SectionAwareChunker
from src.retrieval.heuristics import compute_report_match_bonus, compute_rerank_adjustment, extract_report_cues


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


def test_report_cue_extraction_matches_common_report_names():
    cues = extract_report_cues("Compare AAPM TG 100, TG-142, IAEA TRS 398, and TECDOC1540.")
    assert {"tg:100", "tg:142", "trs:398", "tecdoc:1540"} <= cues


def test_report_match_bonus_rewards_exact_tg_and_penalizes_nearby_wrong_report():
    right = {
        "doc_id": "aapm_tg100_radiotherapy_quality_management",
        "title": "AAPM TG 100: Application of risk analysis methods to radiation therapy quality management",
        "source_path": "reports/raw/aapm_tg100_radiotherapy_quality_management.pdf",
    }
    wrong = {
        "doc_id": "aapm_tg142_medical_accelerator_qa",
        "title": "AAPM TG 142: Quality assurance of medical accelerators",
        "source_path": "reports/raw/aapm_tg142_medical_accelerator_qa.pdf",
    }
    query = "What does TG 100 recommend for FMEA in radiotherapy quality management?"
    assert compute_report_match_bonus(query, right) > 0.35
    assert compute_report_match_bonus(query, wrong) < 0
