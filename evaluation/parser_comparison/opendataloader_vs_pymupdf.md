# PyMuPDF vs OpenDataLoader Comparison

## Design

- Old parser: PyMuPDF historical runtime snapshot.
- New parser: OpenDataLoader rebuilt runtime.
- Held constant: 49 runtime PDFs, the 100-question public MCQ set, auto retrieval, cross-encoder option selection, top-6 evidence, and evidence mode.
- Boundary: this is public answer-keyed development evidence, not a hidden test, Codex-host run, expert grade, or clinical validation.

## Runtime Artifacts

| Measure | PyMuPDF | OpenDataLoader | Delta |
|---|---:|---:|---:|
| source_records | 49 | 49 | +0 |
| parsed_files | 49 | 49 | +0 |
| parsed_blocks | 66937 | 81375 | +14438 |
| chunk_files | 49 | 49 | +0 |
| indexed_chunks | 10923 | 8948 | -1975 |
| asset_documents | 49 | 49 | +0 |
| asset_tables | 655 | 440 | -215 |
| asset_images | 3263 | 2140 | -1123 |

## Public MCQ Result

| Metric | PyMuPDF | OpenDataLoader | Delta |
|---|---:|---:|---:|
| skill_ok_rate | 1.000 | 0.990 | -0.010 |
| citation_present_rate | 1.000 | 0.990 | -0.010 |
| evidence_contains_gold_option_rate | 0.140 | 0.140 | +0.000 |
| mcq_option_accuracy | 0.340 | 0.360 | +0.020 |
| mean_total_latency_seconds | 14.932 | 13.503 | -1.428 |

## Per-question Outcome Changes

- Improved: 16
- Regressed: 14
- Correct in both: 20
- Incorrect in both: 50
