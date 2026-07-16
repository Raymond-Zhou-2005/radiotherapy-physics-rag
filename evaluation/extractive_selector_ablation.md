# Extractive Sentence Selector Ablation

- Questions: 61
- Retrieval backend: auto
- Evidence top-k: 8
- Both selectors receive the same retrieved evidence and return only copied evidence sentences.
- This is an automatic public answer-target evaluation, not expert answer grading or clinical validation.

| Selector | Answer value hit | Citation present | Unexpected errors | Resolved backend |
| --- | ---: | ---: | ---: | --- |
| lexical | 0.393 | 0.984 | 1 | lexical: 60, not_run: 1 |
| semantic_coverage | 0.557 | 0.984 | 1 | cross_encoder: 60, not_run: 1 |

- Absolute answer-value-hit difference versus `lexical` for `semantic_coverage`: +0.164.

## Paired Comparison

- Baseline: `lexical`; challenger: `semantic_coverage`.
- Absolute answer-value-hit difference: +0.164.
- Paired bootstrap 95% CI: [0.04918032786885246, 0.2786885245901639].
- Exact two-sided McNemar p: 0.012939.
- Challenger better/worse discordant cases: 12/2.
- These intervals quantify the fixed automatic answer-target set, not expert correctness or clinical validity.
