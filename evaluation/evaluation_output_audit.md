# Evaluation Output Consistency Audit

This audit checks internal consistency of automatic evaluation artifacts. It does not validate the benchmark labels, clinical correctness, or expert agreement.

- Passed: 33
- Failed: 0

| Check | Status | Detail |
|---|---|---|
| strategy:sparse:document_recall_at_5 | PASS | summary=0.9183673469387755, details=0.9183673469387755, n=245 |
| strategy:sparse:abstention_confusion | PASS | summary={'tp': 35, 'fp': 0, 'tn': 245, 'fn': 0}, details={'tp': 35, 'fn': 0, 'fp': 0, 'tn': 245} |
| strategy:hybrid:document_recall_at_5 | PASS | summary=0.9469387755102041, details=0.9469387755102041, n=245 |
| strategy:hybrid:abstention_confusion | PASS | summary={'tp': 35, 'fp': 0, 'tn': 245, 'fn': 0}, details={'tp': 35, 'fn': 0, 'fp': 0, 'tn': 245} |
| strategy:auto:document_recall_at_5 | PASS | summary=0.9469387755102041, details=0.9469387755102041, n=245 |
| strategy:auto:abstention_confusion | PASS | summary={'tp': 35, 'fp': 0, 'tn': 245, 'fn': 0}, details={'tp': 35, 'fn': 0, 'fp': 0, 'tn': 245} |
| strategy:routed:document_recall_at_5 | PASS | summary=0.926530612244898, details=0.926530612244898, n=245 |
| strategy:routed:abstention_confusion | PASS | summary={'tp': 35, 'fp': 0, 'tn': 245, 'fn': 0}, details={'tp': 35, 'fn': 0, 'fp': 0, 'tn': 245} |
| gold:question_count | PASS | summary=61, details=61 |
| gold:evidence_value_hit_rate | PASS | summary=0.7213114754098361, details=0.7213114754098361 |
| gold:answer_value_hit_rate | PASS | summary=0.5081967213114754, details=0.5081967213114754 |
| gold:citation_present_rate | PASS | summary=0.9836065573770492, details=0.9836065573770492 |
| gold:gold_answer_success_rate | PASS | summary=0.7213114754098361, details=0.7213114754098361 |
| gold:external_gold_answer:success | PASS | summary_n=12, details_n=12, summary_rate=0.4166666666666667, details_rate=0.4166666666666667 |
| gold:open_report_gold_answer:success | PASS | summary_n=49, details_n=49, summary_rate=0.7959183673469388, details_rate=0.7959183673469388 |
| generation:question_count | PASS | summary=61, details=61 |
| generation:extractive_answer_value_hit_rate | PASS | summary=0.5081967213114754, details=0.5081967213114754 |
| generation:evidence_only_value_hit_rate | PASS | summary=0.8032786885245902, details=0.8032786885245902 |
| generation:answer_synthesis_gap_rate | PASS | summary=0.29508196721311475, details=0.29508196721311475 |
| generation:retrieval_gap_rate | PASS | summary=0.19672131147540983, details=0.19672131147540983 |
| generation:external_gold_answer:answer_hit | PASS | summary_n=12, details_n=12, summary_rate=0.3333333333333333, details_rate=0.3333333333333333 |
| generation:open_report_gold_answer:answer_hit | PASS | summary_n=49, details_n=49, summary_rate=0.5510204081632653, details_rate=0.5510204081632653 |
| selector:lexical:summary | PASS | summary_n=61, details_n=61, answer=0.39344262295081966/0.39344262295081966, citation=0.9836065573770492/0.9836065573770492 |
| selector:lexical:profiles | PASS | Profile-specific answer and citation rates were recomputed from frozen per-question details. |
| selector:semantic_coverage:summary | PASS | summary_n=61, details_n=61, answer=0.5573770491803278/0.5573770491803278, citation=0.9836065573770492/0.9836065573770492 |
| selector:semantic_coverage:profiles | PASS | Profile-specific answer and citation rates were recomputed from frozen per-question details. |
| selector:paired:semantic_coverage | PASS | Paired selector comparison, interval, and McNemar result were deterministically recomputed from frozen per-question details. |
| table:cell_qa_success | PASS | summary_n=14, details_n=14, summary_rate=1.0, details_rate=1.0 |
| direct_skill:task_success | PASS | summary_n=40, details_n=40, summary_rate=1.0, details_rate=1.0 |
| mcp_stdio:task_success | PASS | summary_n=7, details_n=7, summary_rate=1.0, details_rate=1.0 |
| quality:grounded_token_overlap | PASS | summary=0.9558402101493031, details=0.9558402101493031, n=60 |
| quality:ood_refusal | PASS | summary=0.0, details=0.0, n=0 |
| uncertainty:deterministic_recompute | PASS | The persisted uncertainty JSON was recomputed from the frozen per-item evaluation outputs. |
