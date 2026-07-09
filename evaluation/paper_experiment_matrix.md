# Paper Experiment Matrix

- Evaluation directory: evaluation
- Experiment rows: 17

| Experiment | N | Primary metric | Value | Secondary metrics | Note |
|---|---:|---|---:|---|---|
| Ablation: bm25_lexical_no_reportaware | 280 | Document Recall@5 | 0.918 | MRR=0.0; Recall@5=0.0; Observed reranker=['lexical']; Uses dense=False; Uses cross encoder=False; Uses report-aware heuristics=False; Uses routing=False | BM25 candidates, lexical rerank, report-aware heuristics disabled. |
| Ablation: bm25_lexical_reportaware | 280 | Document Recall@5 | 0.861 | MRR=0.0; Recall@5=0.0; Observed reranker=['lexical']; Uses dense=False; Uses cross encoder=False; Uses report-aware heuristics=True; Uses routing=False | BM25 candidates, lexical rerank, report-aware heuristics enabled. |
| Ablation: hybrid_lexical_no_reportaware | 280 | Document Recall@5 | 0.955 | MRR=0.0; Recall@5=0.0; Observed reranker=['lexical']; Uses dense=True; Uses cross encoder=False; Uses report-aware heuristics=False; Uses routing=False | Semantic dense + BM25 hybrid candidates, lexical rerank, report-aware heuristics disabled. |
| Ablation: hybrid_crossencoder_no_reportaware | 280 | Document Recall@5 | 0.947 | MRR=0.0; Recall@5=0.0; Observed reranker=['cross_encoder']; Uses dense=True; Uses cross encoder=True; Uses report-aware heuristics=False; Uses routing=False | Semantic dense + BM25 hybrid candidates, cross-encoder rerank, report-aware heuristics disabled. |
| Ablation: hybrid_crossencoder_reportaware | 280 | Document Recall@5 | 0.873 | MRR=0.0; Recall@5=0.0; Observed reranker=['cross_encoder']; Uses dense=True; Uses cross encoder=True; Uses report-aware heuristics=True; Uses routing=False | Semantic dense + BM25 hybrid candidates, cross-encoder rerank, report-aware heuristics enabled. |
| Ablation: routed_full | 280 | Document Recall@5 | 0.898 | MRR=0.0; Recall@5=0.0; Observed reranker=['cross_encoder']; Uses dense=True; Uses cross encoder=True; Uses report-aware heuristics=True; Uses routing=True | Scene-routed retrieval with semantic dense available, cross-encoder rerank, report-aware heuristics enabled. |
| Retrieval strategy: sparse | 280 | Document Recall@5 | 0.918 | Document Recall@3=0.8693877551020408; MRR=0.0; Abstention={'tp': 35, 'fp': 0, 'tn': 245, 'fn': 0}; Observed reranker=['lexical'] | Open-source topic retrieval benchmark; not expert answer grading. |
| Retrieval strategy: hybrid | 280 | Document Recall@5 | 0.947 | Document Recall@3=0.9224489795918367; MRR=0.0; Abstention={'tp': 35, 'fp': 0, 'tn': 245, 'fn': 0}; Observed reranker=['cross_encoder'] | Open-source topic retrieval benchmark; not expert answer grading. |
| Retrieval strategy: auto | 280 | Document Recall@5 | 0.947 | Document Recall@3=0.9224489795918367; MRR=0.0; Abstention={'tp': 35, 'fp': 0, 'tn': 245, 'fn': 0}; Observed reranker=['cross_encoder'] | Open-source topic retrieval benchmark; not expert answer grading. |
| Retrieval strategy: routed | 280 | Document Recall@5 | 0.927 | Document Recall@3=0.8979591836734694; MRR=0.0; Abstention={'tp': 35, 'fp': 0, 'tn': 245, 'fn': 0}; Observed reranker=['cross_encoder', 'lexical'] | Open-source topic retrieval benchmark; not expert answer grading. |
| Agent-facing skill contract | 280 | Document Hit Rate@5 | 0.947 | Citation present=1.0; OOD abstention=1.0; Unexpected errors=0 | End-to-end skill invocation without an external LLM API. |
| Realistic agent tasks | 12 | Task success rate | 1.000 | Structured success=0.75; Citation success=1.0; Bundle prompt success=1.0; Asset trace success=1.0; OOD abstention=1.0 | Checks reusable skill contract behaviour for downstream agents. |
| Table/figure asset proximity | 120 | Asset ID Trace Hit Rate@5 | 0.950 | Document Hit@5=1.0; Page Hit@5=0.9833333333333333; Asset Type Trace@5=0.975 | Metadata proximity check, not visual interpretation. |
| Cell-level table QA | 14 | Cell QA success rate | 0.929 | Evidence cell value hit=0.9285714285714286; Answer cell value hit=0.6428571428571429; Asset trace@5=0.9285714285714286; Page Hit@5=0.9285714285714286 | Checks short values from extracted table text previews. |
| External gold-answer seed | 12 | Gold-answer success rate | 0.583 | Evidence value hit=0.5833333333333334; Answer value hit=0.3333333333333333; Citation present=0.9166666666666666 | Public short-answer seed; not expert clinical grading. |
| Answer-quality proxy | 280 | Mean grounded token overlap | 0.993 | Citation marker=1.0; Evidence ID valid=1.0; Unsupported number case=0.0; Overclaim flag=0.02040816326530612; OOD abstention=1.0 | Automatic faithfulness proxy; not expert correctness grading. |
| Navigator retrieval | 280 | Topic Recall@3 | 0.967 | Candidate Document Recall@5=0.673469387755102 | Checks navigable topic index support. |
