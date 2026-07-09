# Changelog

## 2.1.1 - 2026-07-10

- Expanded the public answer-target benchmark from 12 to 61 items by combining paraphrased public answer-key seeds with open-report answer targets generated from public AAPM/IAEA report evidence.
- Expanded realistic agent-task evaluation from 12 to 40 tasks, including 30 in-scope agent-use tasks and 10 hard medical-boundary OOD refusal tasks.
- Added `evaluate_answer_generation.py` to separate extractive answer value hits from evidence-only and bundle-prompt target availability without hosted LLM calls.
- Added `analyze_failure_taxonomy.py` to classify benchmark failures and gaps into paper-facing categories such as answer synthesis gap, retrieval gap, page miss, and skill error.
- Added a hard OOD boundary for SUV cutoff / malignant recurrence PET-CT interpretation questions outside the radiotherapy physics evidence scope.
- Updated the paper experiment matrix to 19 rows, now including answer-generation mode comparison and failure taxonomy.
- Current new evaluation results: public answer-target gold-answer success 0.787, evidence-only/bundle target hit 0.852, extractive answer target hit 0.344, agent-task success 1.000 across 40 tasks, and 58 automatically classified failure/gap cases.

## 2.1.0 - 2026-07-09

- Added real cross-encoder reranking with `BAAI/bge-reranker-base`, backend caching, explicit backend metadata in evidence scores, and lexical fallback for offline use.
- Rebuilt and evaluated the preferred retrieval profile as semantic dense + BM25 hybrid retrieval with cross-encoder reranking and report-aware heuristics disabled.
- Added formal ablation evaluation across BM25, semantic hybrid, cross-encoder, report-aware heuristics, and routing variants. Current safest default reaches Document Recall@5 0.947 with OOD TP/FN 35/0 on the 280-question public benchmark.
- Added 12 external public gold-answer seed questions and evaluation. Current gold-answer success is 0.583, exposing the limitation of extractive-only answers on calculation/public-answer-key tasks.
- Added 14 cell-level table QA questions from extracted public PDF table text previews. Current Cell QA success is 0.929 and evidence cell-value hit is 0.929.
- Added 12 realistic agent-task evaluations covering evidence lookup, bundle generation, table asset trace, and hard medical-boundary OOD refusal. Current task success is 1.000.
- Added paper experiment matrix generation with 17 experiment rows covering retrieval ablations, strategy evaluation, agent contract, agent tasks, asset QA, table-cell QA, gold-answer seed, answer-quality proxy, and navigator metrics.
- Added `.zenodo.json` metadata and release DOI checklist steps. No fake DOI is committed.
- Extended hard OOD routing for medication dose adjustment, insulin/hypoglycemia, stroke MRI, and similar medically related but non-radiotherapy-physics questions.
- Exposed nearby table/figure `text_preview` metadata in evidence outputs and table-aware extractive answer snippets for explicit asset/page queries.
- Updated current public results: auto/hybrid Document Recall@5 0.947, agent skill Document Hit@5 0.947, answer-quality grounded token overlap 0.993, unsupported number case rate 0.000, and OOD abstention 1.000.

## 2.0.1 - 2026-07-09

- Rebuilt the dense index with a real semantic embedding model: `BAAI/bge-small-en-v1.5` via `sentence-transformers`, 384 dimensions, plus FAISS search.
- Expanded the public source catalog to 49 records and the local runtime to 49 indexed PDFs, 10923 chunks, 49 local ChatGPT Knowledge upload files, and PDF asset metadata for 655 tables and 3263 images.
- Refreshed TG100 and TG158 into the local runtime and added additional public/free-access AAPM and IAEA reports covering accelerator QA, IMRT commissioning and QA, beam data, IGRT, SBRT, image registration, imaging dose, Tomotherapy QA, radiation safety, and global radiotherapy access.
- Added a 280-question open-source topic benchmark generated from public source metadata, with 245 in-domain questions and 35 OOD controls.
- Added navigator, strategy, agent-skill, asset metadata, and answer-quality proxy evaluations.
- Added no-model hash dense and lexical rerank controls for reproducible public benchmarking.
- Made routed retrieval memory appends opt-in with `RAG_EXPERIENCE_APPEND=1` and excluded local memory logs from the public release.
- Added public release build and audit scripts to create a clean GitHub package without PDFs, parsed text, chunks, indexes, extracted asset records, or generated upload files.
- Clarified no-code user surfaces for Codex Plugin and ChatGPT Knowledge while keeping Python as the local build/retrieval engine.

## 2.0.0 - 2026-06-12

- Expanded the starter corpus source metadata from 5 to 16 radiotherapy physics documents while keeping the same niche.
- Added PDF text-readiness inspection, optional OCRmyPDF wrapper, Codex Plugin manifest, ChatGPT Knowledge package, and MCP stdio server.
- Added reproducibility-oriented `constraints.txt`, extra examples, MCP reference docs, and balanced package validation.
- Extended evaluation questions to cover QA, image guidance, risk-based quality management, biological treatment-planning model QA, reference dosimetry, and programme safety.
- Reworked starter and evaluation questions as blind content questions that do not name the expected report.
- Added 30-question blind sparse evaluation with Document Recall@3/5 of 1.000 and clean out-of-scope abstention proxy results.
- Added PDF table/image asset extraction and validation support for locally generated asset manifests.
- Replaced the optional corpus roadmap with a 16-document starter corpus source list built from directly available AAPM/IAEA sources.
- Kept evaluation datasets, baselines, and results in `evaluation/`, separate from runtime skill files.
- Added a 38-question public-credible evaluation set with Document Recall@3/5 of 1.000 and clean out-of-scope abstention proxy results.
- Consolidated final-package documentation around README, focused references, Codex Skill instructions, and ChatGPT Knowledge files.
- Removed third-party report PDFs, parsed full text, chunks, indexes, extracted assets, and ChatGPT upload full text from the public package; these are now local generated artifacts ignored by Git.
- Removed duplicated agent metadata, issue templates, release-only workflow, and early design notes from the deliverable folder.

## 1.0.0 - 2026-05-17

- Packaged the repository root as the `radiotherapy-physics-rag` Codex skill.
- Added CLI, Python package entrypoints, MCP support, validation, and bundle creation.
- Added a local radiotherapy physics starter corpus workflow and RAG artifact generation for local use.
- Preserved hybrid dense+BM25 retrieval, reranking, definition microchunks, structured JSON outputs, and balanced starter-corpus checks.
