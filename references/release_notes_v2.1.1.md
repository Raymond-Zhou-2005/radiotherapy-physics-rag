# Release Notes: v2.1.1

## Summary

This release prepares the radiotherapy physics RAG skill for paper-facing
open-source evaluation. It expands public-source answer-target and agent-task
benchmarks, adds answer-generation mode analysis, adds an automatic failure
taxonomy, and documents academic claim boundaries.

## Added

- 61-question public answer-target benchmark.
- 40-task realistic agent-task benchmark with hard medical-boundary OOD cases.
- `scripts/evaluate_answer_generation.py`.
- `scripts/analyze_failure_taxonomy.py`.
- Answer generation mode comparison outputs.
- Failure taxonomy outputs.
- Paper experiment matrix with 24 experiment rows.
- Public academic norm review.
- Paper readiness checklist.

## Changed

- Default research interpretation remains `auto` retrieval with semantic hybrid
  retrieval and cross-encoder reranking when available.
- Public answer-target results are reported as public-source automatic targets,
  not expert gold-standard correctness.
- The OOD router includes additional PET/CT SUV and recurrence boundary terms.
- README, evaluation documentation, project brief, deliverable summary, and
  changelog now reflect the expanded evaluation suite.

## Current Key Results

- Auto Document Recall@5 on the 280-question public benchmark: 0.947.
- OOD abstention success on current controls: 1.000.
- Public answer-target aggregate success: 0.787; extractive answer value hit: 0.393.
- External public-answer-key profile: N = 12, evidence value hit = 0.583, answer value hit = 0.333.
- In-corpus open-report profile: N = 49, evidence value hit = 0.837, answer value hit = 0.408.
- Evidence/bundle target hit in answer-generation comparison: 0.852; answer synthesis gap: 0.459.
- Direct skill-contract success: 1.000 across 40 tasks; MCP stdio contract success: 1.000 across 7 tasks.
- Table-cell QA success: 0.929.
- Failure/gap cases classified: 51, dominated by answer synthesis gaps.

## Release Boundary

The public repository does not include third-party PDFs, parsed full text,
chunks, runtime indexes, extracted asset JSONL, generated ChatGPT upload files,
or local experience memory. Users rebuild runtime artifacts locally from
permitted source documents.

## DOI Note

`.zenodo.json` is present. A DOI requires either GitHub-Zenodo integration on
the repository or a manual Zenodo upload of the release archive.
