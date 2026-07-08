# Changelog

## Unreleased

- Expanded the public source catalog to 49 records and the current local runtime to 49 indexed PDFs.
- Rebuilt the runtime corpus with 10923 chunks, 49 local ChatGPT Knowledge upload files, and PDF asset metadata for 655 tables and 3263 images.
- Added five direct-download IAEA sources covering 3DCRT/IMRT transition, national radiotherapy services, facility radiation protection, medical radiation safety, and global radiotherapy access.
- Refreshed TG100 and TG158 into the local runtime and added 12 additional public/free-access AAPM reports covering accelerator QA, IMRT commissioning and QA, beam data, IGRT, SBRT, image registration, imaging dose, and Tomotherapy QA.
- Added a 260-question open-source topic benchmark generated from public source metadata, with 245 in-domain questions and 15 OOD controls.
- Added strategy, navigator, and agent-skill contract evaluations for sparse, hybrid/hash, auto, and routed retrieval; sparse, auto, and routed Document Recall@5 are 0.857, hybrid hash+dense Document Recall@5 is 0.804, and routed agent Document Hit Rate@5 is 0.857 on the current benchmark.
- Added an explicit OOD sufficiency gate for non-radiotherapy controls; current OOD abstention success is 1.000 on the public control set.
- Added no-model hash dense and lexical rerank controls for reproducible public benchmarking.
- Updated `auto` and `routed` retrieval so a hash dense index is treated as a reproducibility baseline, not a semantic dense index; both now fall back to sparse retrieval unless a semantic dense index is available.
- Made routed retrieval memory appends opt-in with `RAG_EXPERIENCE_APPEND=1` and excluded local memory logs from the public release.
- Added public release build and audit scripts to create a clean GitHub package without PDFs, parsed text, chunks, indexes, or generated upload files.
- Allowed `auto` and `sparse` retrieval to run from sparse BM25 plus chunk metadata without requiring dense index files.
- Added a sparse-only index builder and `prepare_index.py --index-backend sparse` for the no-model path.
- Added display-ready citation strings, `page_range`, and `source_path` to evidence and citation outputs.
- Clarified no-code user surfaces for Codex Plugin and ChatGPT Knowledge while keeping Python as the local build/retrieval engine.
- Clarified that evaluation assets live in the repository `evaluation/` folder and remain separate from runtime skill files.

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
