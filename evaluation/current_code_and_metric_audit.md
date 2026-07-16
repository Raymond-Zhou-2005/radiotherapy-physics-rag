# Current Code And Metric Audit

> **Parser-refresh status (2026-07-16):** This audit preserves the prior
> PyMuPDF-era code/metric comparison and is retained for historical
> traceability. Its numeric "current" results are not OpenDataLoader headline
> results. For the rebuilt 49-PDF OpenDataLoader runtime, use
> `ablation_eval_results.json`, `gold_answer_eval_results.json`,
> `answer_generation_eval_results.json`, `table_cell_qa_eval_results.json`,
> `asset_qa_eval_results.json`, `agent_task_eval_results.json`,
> `mcp_contract_eval_results.json`, and `external/mcq_method_comparison.md`.

This note records the current July 2026 audit of chunking, indexing, retrieval, reranking, asset lookup, and evaluation behavior for the radiotherapy physics RAG skill package.

## Compared Folders

- Current package: `D:\CodexWorkplace\RAG\Radiotherapy_RAG_Skill_Complete`
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

PDF asset extraction records table and image metadata, and table records include a short local `text_preview`. Runtime evidence outputs include `nearby_assets` for chunks near detected table/figure metadata. Explicit table/figure questions use asset-aware extractive answers; explicit page requests additionally inject chunks from the requested page neighborhood before citation formatting. Generic phrases such as `image-guided radiotherapy` do not trigger asset mode.

This supports metadata proximity and PDF-text-preview table-cell QA, not visual interpretation or general image semantic QA.

### Answer Quality

The package now includes automatic answer-quality proxy evaluation for extractive answers:

- answer presence
- citation marker presence
- used evidence ID validity
- summary grounded-token overlap
- unsupported-number cases in the extractive summary
- patient-instruction/overclaim phrase flags in the extractive summary
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
| sparse | 0.869 | 0.918 | 35 | 0 | 245 | 0 |
| hybrid semantic + cross-encoder | 0.922 | 0.947 | 35 | 0 | 245 | 0 |
| auto | 0.922 | 0.947 | 35 | 0 | 245 | 0 |
| routed | 0.898 | 0.927 | 35 | 0 | 245 | 0 |

Agent skill evaluation:

| Metric | Current value |
| --- | ---: |
| Tool success rate | 0.875 |
| Document Hit Rate@5 | 0.947 |
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

Cell-level table QA evaluation:

| Metric | Current value |
| --- | ---: |
| Questions | 14 |
| Cell QA success rate | 0.929 |
| Evidence cell value hit rate | 0.929 |
| Answer cell value hit rate | 0.929 |
| Page and asset trace hit rate@5 | 0.929 |

MCP stdio contract evaluation:

| Metric | Current value |
| --- | ---: |
| Separate-process tasks | 7 |
| Required tools present | true |
| Task success rate | 1.000 |
| OOD refusal success rate | 1.000 |
| Transport errors | 0 |

Public answer-target evaluation:

| Profile | N | Evidence value hit | Answer value hit | Gold-answer success |
| --- | ---: | ---: | ---: | ---: |
| Combined | 61 | 0.787 | 0.557 | 0.787 |
| External public-answer-key seed | 12 | 0.583 | 0.417 | 0.583 |
| In-corpus open-report target | 49 | 0.837 | 0.592 | 0.837 |

The two answer-target profiles are intentionally not interchangeable: the in-corpus profile tests report-grounded retrieval and surfacing, while the small external profile is a non-expert public-source stress test. A same-evidence selector ablation improved the legacy lexical extractive answer hit from 0.393 to 0.557 with cross-encoder semantic coverage selection (paired delta +0.164, bootstrap 95% CI [0.049, 0.279], exact McNemar p=0.0129). This automatic result does not establish expert correctness.

Current semantic-coverage answer-quality proxy evaluation:

| Metric | Current value |
| --- | ---: |
| Questions | 280 |
| In-scope OK rate | 1.000 |
| Answer present rate | 1.000 |
| Citation marker rate | 1.000 |
| Used evidence ID valid rate | 1.000 |
| Mean grounded token overlap | 0.960 |
| Unsupported number case rate | 0.000 |
| Overclaim flag rate | 0.000 |
| OOD abstention success rate | 1.000 |
| Unexpected errors | 0 |

## Interpretation

The current package has a real semantic embedding index, but the metadata-generated public benchmark rewards exact report identifiers, titles, and source-role terms. Semantic hybrid with lexical reranking reached the highest Document Recall@5 (0.955); the safety-oriented default is hybrid semantic retrieval with a cross-encoder (the `auto` path), which reached 0.947 with no OOD false negatives. This benchmark is closer to report-location retrieval than open-ended semantic QA.

The routed strategy remains available for experimentation, but its current Document Recall@5 (0.927) is lower than `auto`; it is not the preferred default for the reported benchmark.

The strongest remaining weak point is navigator document ranking. Topic recall is high, but picking the exact report inside overlapping QA/IMRT/IGRT/dosimetry topics remains hard. The default semantic-coverage answer selector also leaves 18/61 automatic answer-synthesis gaps. Its complete 280-question answer-quality proxy evaluation reports 0.960 mean grounded-token overlap, but this automatic proxy does not establish expert correctness or completeness.

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
- `Grounded token overlap`: token-overlap proxy between the extractive summary and returned evidence text, including returned asset previews.
- `Unsupported number case rate`: proportion of extractive summaries containing numbers not found in returned evidence text.
- `Overclaim flag rate`: proportion of extractive summaries containing patient-directed treatment language. It is a narrow automatic screen, not a safety assessment.

## Remaining Optimization Opportunities

1. Add expert gold chunk IDs for a smaller adjudicated benchmark so exact `Recall@k` and `MRR` become meaningful.
2. Improve navigator document ranking with report-number/title cues and topic-specific candidate ordering.
3. Add human-verified visual table and figure questions only if licensing and expert review boundaries are clear.
4. Compare the current semantic-coverage extractor with local or hosted LLM answers under the same evidence contract and a separate safety protocol.
5. Calibrate OOD abstention on broader independent negative controls beyond the current synthetic benchmark.
