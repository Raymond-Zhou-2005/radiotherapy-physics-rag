# Statistical Uncertainty Report

## Scope

Intervals describe uncertainty within the fixed automatic evaluation sets. They do not establish clinical validity, expert agreement, or population generalization.

## Retrieval

| Strategy | In-scope n | Document Recall@5 | Wilson 95% CI | OOD n | OOD refusal | Wilson 95% CI |
|---|---:|---:|---|---:|---:|---|
| sparse | 245 | 0.918 | [0.877, 0.947] | 35 | 1.000 | [0.901, 1.000] |
| hybrid | 245 | 0.947 | [0.911, 0.969] | 35 | 1.000 | [0.901, 1.000] |
| auto | 245 | 0.947 | [0.911, 0.969] | 35 | 1.000 | [0.901, 1.000] |
| routed | 245 | 0.927 | [0.887, 0.953] | 35 | 1.000 | [0.901, 1.000] |

### Paired Sparse Versus Hybrid Comparison

- Paired in-scope questions: 245
- Hybrid minus sparse Document Recall@5: 0.029
- Bootstrap 95% CI: [0.000, 0.061]
- Discordant questions: hybrid-only=11, sparse-only=4
- Exact two-sided McNemar p-value: 0.1185

## Answer Targets

| Profile | Metric | Successes / n | Rate | Wilson 95% CI |
|---|---|---:|---:|---|
| external_gold_answer | gold_evidence_value_hit | 5 / 12 | 0.417 | [0.193, 0.680] |
| external_gold_answer | gold_extractive_answer_value_hit | 4 / 12 | 0.333 | [0.138, 0.609] |
| external_gold_answer | generation_evidence_only_value_hit | 5 / 12 | 0.417 | [0.193, 0.680] |
| external_gold_answer | generation_extractive_answer_value_hit | 4 / 12 | 0.333 | [0.138, 0.609] |
| open_report_gold_answer | gold_evidence_value_hit | 39 / 49 | 0.796 | [0.664, 0.885] |
| open_report_gold_answer | gold_extractive_answer_value_hit | 27 / 49 | 0.551 | [0.413, 0.681] |
| open_report_gold_answer | generation_evidence_only_value_hit | 44 / 49 | 0.898 | [0.782, 0.956] |
| open_report_gold_answer | generation_extractive_answer_value_hit | 27 / 49 | 0.551 | [0.413, 0.681] |

## Capability Contracts

| Metric | Successes / n | Rate | Wilson 95% CI |
|---|---:|---:|---|
| cell_level_table_qa | 14 / 14 | 1.000 | [0.785, 1.000] |
| direct_skill_task_success | 40 / 40 | 1.000 | [0.912, 1.000] |
| mcp_stdio_task_success | 7 / 7 | 1.000 | [0.646, 1.000] |

## Automatic Answer-Quality Proxy

- In-scope grounded-token overlap mean: 0.940
- Bootstrap 95% CI: [0.906, 0.959]
- OOD refusal: 0 / 0 (0.000; Wilson 95% CI [0.000, 0.000])
