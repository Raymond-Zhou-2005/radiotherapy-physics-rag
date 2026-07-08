"""Minimal smoke tests.

These tests are intentionally light. They verify that the utility functions and
chunker can be imported and run on a tiny synthetic example.
"""

from src.chunking.splitter import SectionAwareChunker
from src.orchestration.router import analyze_scene
from src.utils import count_approx_tokens


def test_count_approx_tokens_nonempty():
    assert count_approx_tokens("This is a short sentence.") > 0


def test_chunker_runs_on_tiny_example():
    chunker = SectionAwareChunker(chunk_size_tokens=10, chunk_overlap_tokens=2, min_chunk_tokens=1)
    parsed_blocks = [
        {
            "block_type": "paragraph",
            "doc_id": "doc1",
            "title": "Doc 1",
            "section": "1. INTRODUCTION",
            "subsection": "UNKNOWN",
            "page_start": 1,
            "page_end": 1,
            "text": "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu",
            "source_path": "dummy.pdf",
        }
    ]
    chunks = chunker.chunk_document(parsed_blocks)
    assert len(chunks) >= 1


def test_medical_boundary_question_is_out_of_scope():
    scene = analyze_scene("Should my mother choose SBRT or surgery for early stage lung cancer?")
    assert scene["task_type"] == "out_of_scope"
    assert scene["clinical_boundary_matches"]


def test_patient_specific_imrt_qa_is_in_scope():
    scene = analyze_scene("What QA issues matter for patient-specific IMRT measurement-based verification?")
    assert scene["task_type"] != "out_of_scope"
