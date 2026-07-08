# Current Code And Metric Audit

This note records the current July 2026 audit of chunking, indexing, retrieval, reranking, asset lookup, and evaluation behavior for the radiotherapy physics RAG skill package.

## Compared Folders

- Current package: `D:\CodexWorkplace\2026-07-08_Radiotherapy_RAG_Skill_Complete`
- Prior implementation reference: `D:\DKU\Research\RAG\2.0`
- Additional historical reference checked: `D:\DKU\Research\RAG\med_report_rag`

## Code Differences Versus 2.0

### Chunking

The section-aware chunking implementation remains close to 2.0. The main scale change is the runtime corpus: 49 PDFs and 10923 chunks. The current package also preserves definition microchunks and report metadata fields so retrieval and citations can be audited.

### Indexing

The current local build now uses a real semantic dense model:

- Embedding model: `BAAI/bge-small-en-v1.5`.
- Backend: `sentence_transformers`.
- Dense dimension: 384.
- Query prefix: `Represent this sentence for searching relevant passages: `.
- Dense search: FAISS inner-product search over normalized embeddings.

The no-model hash dense path still exists for CI/debugging, but it is explicitly treated as non-semantic. `dense_meta.json` is checked before hybrid search is trusted.

### Retrieval And Reranking

The skill-facing retrieval wrapper supports `sparse`, `hybrid`, `auto`, and `routed`.

- `sparse`: BM25 plus transparent report-aware heuristics.
- `hybrid`: semantic dense retrieval plus BM25 reciprocal-rank fusion.
- `auto`: uses semantic hybrid when the dense index is real; otherwise falls back to sparse.
- `routed`: uses scene analysis to choose sparse or hybrid. It currently prefers sparse for exact report/source lookup and QA/procedure questions, and reserves semantic hybrid for broader comparison or multi-report synthesis.

Report-aware ranking now uses TG, AAPM Report, TRS, TECDOC, HHR/HHS, SSG, SRS, and publication number cues, plus title-term overlap. This addresses the common failure where the system finds the right broad QA topic but the wrong similar report.

### OOD Boundary

The router now includes hard medical-boundary controls, such as chemotherapy, immunotherapy, billing, legal, symptom management, surgery, prognosis, and patient-specific treatment decisions. It deliberately does not reject phrases such as `patient-specific IMRT QA`, which are valid radiotherapy physics topics.

### Table And Figure Metadata

PDF asset extraction still records table and image metadata, and table records now include a short local `text_preview`. Runtime evidence outputs include `nearby_assets` for chunks near detected table/figure metadata. Explicit table/figure/page questions trigger asset-aware evidence augmentation, which injects chunks from the requested page neighborhood before citation formatting.

This is metadata-proximity QA, not visual interpretation or full table-cell answer grading.

### Answer Quality

The package now includes automatic answer-quality proxy evaluation for extractive answers:

- answer presence
- citation marker presence
- used evidence ID validity
- grounded token overlap
- unsupported number cases
- overclaim phrase flags
- OOD abstention success

These are reproducible proxies, not expert correctness labels.

## Current Evaluation Snapshot

Benchmark:

- Total questions: 280.
- In-domain public-source topic questions: 245.
- OOD controls: 35, including 20 hard medical-boundary controls.
- Runtime source records: 49.

Strategy evaluation:

| Strategy | Document Recall@3 | Document Recall@5 | OOD TP | OOD FP | OOD TN | OOD FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| sparse | 0.771 | 0.861 | 35 | 0 | 245 | 0 |
| hybrid semantic | 0.771 | 0.820 | 35 | 0 | 245 | 0 |
| auto | 0.771 | 0.820 | 35 | 0 | 245 | 0 |
| routed | 0.780 | 0.861 | 35 | 0 | 245 | 0 |

Agent skill evaluation:

| Metric | Current value |
| --- | ---: |
| Tool success rate | 0.875 |
| Document Hit Rate@5 | 0.861 |
| Citation present rate | 1.000 |
| OOD abstention success rate | 1.000 |
| Unexpected errors | 0 |

Navigator evaluation:

| Metric | Current value |
| --- | ---: |
| Topic Recall@1 | 0.837 |
| Topic Recall@2 | 0.939 |
| Topic Recall@3 | 0.967 |
| Candidate Document Recall@1 | 0.188 |
| Candidate Document Recall@3 | 0.490 |
| Candidate Document Recall@5 | 0.673 |

Asset QA evaluation:

| Metric | Current value |
| --- | ---: |
| Questions | 120 |
| Skill OK rate | 1.000 |
| Document Hit Rate@5 | 1.000 |
| Page Hit Rate@5 | 0.983 |
| Asset ID Trace Hit Rate@5 | 0.950 |
| Asset Type Trace Hit Rate@5 | 0.975 |

Answer-quality proxy evaluation:

| Metric | Current value |
| --- | ---: |
| Questions | 280 |
| In-scope OK rate | 1.000 |
| Answer present rate | 1.000 |
| Citation marker rate | 1.000 |
| Used evidence ID valid rate | 1.000 |
| Mean grounded token overlap | 0.994 |
| Unsupported number case rate | 0.016 |
| Overclaim flag rate | 0.004 |
| OOD abstention success rate | 1.000 |
| Unexpected errors | 0 |

## Interpretation

The current package has a real semantic embedding index, but the metadata-generated public benchmark rewards exact report identifiers, titles, and source-role terms. For that reason, sparse BM25 and routed retrieval currently outperform pure semantic hybrid on Document Recall@5. This is not a failure of semantic search; it shows that the benchmark is closer to report-location retrieval than open-ended semantic QA.

Routed retrieval is therefore the practical default: it uses sparse retrieval where exact report matching matters and keeps semantic hybrid available for broader synthesis or comparison tasks.

The strongest remaining weak point is navigator document ranking. Topic recall is high, but picking the exact report inside overlapping QA/IMRT/IGRT/dosimetry topics remains hard.

## Metric Meanings

- `Document Recall@3` / `Document Recall@5`: whether the expected source report appears among the top 3 or top 5 retrieved source documents.
- `Recall@3` / `Recall@5`: exact gold chunk recall. These are 0.000 because the public benchmark does not contain expert gold chunk IDs.
- `MRR`: mean reciprocal rank of the first exact gold chunk. Not meaningful until expert chunk labels exist.
- `OOD TP`: an out-of-domain question was correctly rejected or abstained.
- `OOD FP`: an in-domain question was incorrectly rejected.
- `OOD TN`: an in-domain question was answered instead of rejected.
- `OOD FN`: an out-of-domain question was incorrectly answered.
- `Topic Recall@k`: whether the navigator selected the expected broad topic within its top k topics.
- `Candidate Document Recall@k`: whether the navigator surfaced the expected source report within its top k candidate reports.
- `Tool success rate`: proportion of questions that return `ok=true`. Correct OOD abstentions are structured `insufficient_evidence` errors, so this rate can decrease when abstention improves.
- `Document Hit Rate@5`: whether the agent-facing evidence output includes the expected source report in its top 5 evidence items.
- `Citation present rate`: whether successful in-domain outputs include citations.
- `Page Hit Rate@5`: whether asset QA evidence lands within the expected page neighborhood.
- `Asset ID Trace Hit Rate@5`: whether returned `nearby_assets` include the expected asset ID.
- `Grounded token overlap`: token-overlap proxy between extractive answer text and returned evidence text.
- `Unsupported number case rate`: proportion of answers containing numbers not found in returned evidence text.
- `Overclaim flag rate`: proportion of answers containing high-risk phrases suggesting clinical overreach.

## Remaining Optimization Opportunities

1. Add expert gold chunk IDs for a smaller adjudicated benchmark so exact `Recall@k` and `MRR` become meaningful.
2. Improve navigator document ranking with report-number/title cues and topic-specific candidate ordering.
3. Add cell-level table QA only if table-content licensing and expert review boundaries are clear.
4. Compare extractive answers with local LLM or hosted LLM answers under the same evidence contract.
5. Calibrate OOD abstention on broader negative controls beyond the current synthetic benchmark.
