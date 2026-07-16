# Benchmark Governance and Interpretation

## Purpose

This repository evaluates an evidence-retrieval skill, not a clinical decision system. The evaluation suite measures whether the local skill returns source-linked material, whether it refuses clearly out-of-scope requests, and whether a conservative extractive answer surfaces short public targets. It does not establish medical correctness, safety in patient care, or equivalence to a credentialing examination.

## Answer-Target Profiles

`evaluation/radiotherapy_gold_answer_questions.json` contains two deliberately separate profiles. Evaluation scripts report both profiles separately in `by_benchmark_profile` and the combined score must not be interpreted alone.

| Profile | Current size | Construction | What it can support |
| --- | ---: | --- | --- |
| `external_gold_answer` | 12 | Paraphrased short targets from public AFOMP answer-key pages and a public RANZCR sample-questions document. Those source URLs are not corpus entries in `reports/starter_corpus_sources.json`. | A small, public-source stress test whose answer-key source is external to the indexed corpus. |
| `open_report_gold_answer` | 49 | Short targets generated from the indexed, publicly obtainable AAPM/IAEA report corpus. | An in-corpus retrieval-and-surfacing check, not an independent generalization test. |

Neither profile is expert-adjudicated. The external profile is small and includes concepts that may only partially overlap the corpus; it is therefore a stress test rather than a broad claim of generalization. The open-report profile has unavoidable retrieval-source overlap and must be labelled as such in any report or paper.

## Other Evaluations

- The 280-question topic benchmark is metadata-derived. It supports document-level retrieval and abstention measurements, not gold-chunk recall or clinical answer accuracy.
- The 14-question table-cell set checks strings from locally extracted table previews. It is not image understanding or human verification of a rendered PDF table.
- The 40 agent-task set calls the local skill contract directly. It is an integration test, not an evaluation of an autonomous host agent's planning behavior.
- The 35 out-of-domain controls, including 20 medical-boundary controls, test whether the skill refuses unsupported requests. They are not a substitute for a formal safety study.
- The answer-quality proxy checks citation and textual-overlap properties. It is not an LLM-as-judge or clinician assessment.
- `statistical_uncertainty.json` reports Wilson intervals for binary automatic metrics and deterministic bootstrap intervals for a paired retrieval comparison. It describes uncertainty within the fixed benchmark outputs only; it is not evidence of clinical validity, expert agreement, or independent generalization.

## Reporting Rules

1. Report sample counts and `by_benchmark_profile` results alongside every combined answer-target metric.
2. Do not describe `gold_answer_success_rate`, cell-value hit rate, or grounded-token overlap as clinical accuracy.
3. State the exact retrieval backend, embedding model, cross-encoder availability, evidence top-k, corpus manifest, and evaluation command used for a result.
4. Keep private or licensed questions out of the repository. Report only aggregate results for any locally held licensed set.
5. Present expert review, independent external questions, and visual table verification as future validation work unless they have actually been completed.
6. When reporting a point estimate with a confidence interval, name the automatic benchmark and denominator. Do not interpret an interval as a clinical confidence interval or use it to erase the benchmark-construction limitations.
7. Treat `external_validation_protocol.md`, `expert_review_rubric_template.csv`, and `agent_host_evaluation_protocol.md` as prospective study materials. Do not describe their existence as completed expert or host-agent evaluation.
