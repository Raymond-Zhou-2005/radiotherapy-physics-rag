# Academic Norm Review Result

## Scope

Reviewed materials include the public source policy, README, evaluation
documentation, release boundary, benchmark files, experiment matrix, and current
paper-preparation notes. This is a documentation-driven review, not a
proprietary similarity-database screen and not an expert medical physicist
review.

## Summary

| Area | Status | Note |
|---|---|---|
| Private exam-bank avoidance | PASS | Public benchmark policy excludes private, paid, leaked, commercial, ABR, RAPHEX, and board-review question-bank material. |
| Copyright boundary | PASS | Public package excludes PDFs, parsed full text, chunks, runtime indexes, extracted asset JSONL, generated upload files, and local experience memory. |
| Clinical safety boundary | PASS | Documentation states that the system is not medical advice, not clinical decision support, and not for patient-specific recommendations. |
| Expert-review boundary | PASS | Documentation states that current results are automatic public-source evaluations, not expert-adjudicated clinical correctness. |
| Metric interpretation | PASS | Answer-quality, answer-target, and failure-taxonomy metrics are labeled as proxies or engineering diagnostics. |
| DOI/release status | PARTIAL | `.zenodo.json` is present; DOI creation requires a GitHub release and Zenodo integration or manual upload. |
| Final manuscript reference style | PARTIAL | A publication-style manuscript package exists, but target-journal formatting and final reference adaptation remain pending. |

## Required Claim Boundary

Supported claim:

> This repository provides an open-source, local-first radiotherapy physics RAG
> skill with reproducible public-source evaluation and structured evidence
> outputs for downstream agents.

Unsupported claims unless additional evidence is added:

- Clinical validation.
- Expert-level correctness.
- Patient-specific medical advice.
- Board-exam performance.
- Complete visual interpretation of tables or figures.

## Main Remaining Scientific Limitation

The strongest measured area is evidence retrieval and evidence bundling. The
current semantic-coverage extractor improves automatic answer-value hit from
0.393 to 0.557 on the fixed 61-question set without changing retrieved
evidence, but evidence/bundle target availability remains higher at 0.852.
The remaining gap and weaker external profile must still be reported as
limitations rather than hidden.

## Pre-Submission Requirements

- Generate final manuscript references in the selected target style.
- Create a release tag and mint or attach a DOI before journal submission.
- If expert review is unavailable, describe the study as public-source,
  automatic, and reproducible rather than expert-validated.
- If expert review becomes available, report the expert scoring protocol,
  reviewer qualifications, item sampling, rubric, and agreement statistics.
