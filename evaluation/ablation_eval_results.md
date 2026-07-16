# Formal Ablation Results

- Question file: evaluation\radiotherapy_skill_open_questions.json
- Index directory: index
- Ignore report scope: True

| Variant | Dense | Cross-encoder requested | Report-aware | Routing | Doc Recall@5 | MRR | OOD TP/FN | Observed reranker |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| bm25_lexical_no_reportaware | 0 | 0 | 0 | 0 | 0.918 | 0.000 | 34/1 | lexical |
| bm25_lexical_reportaware | 0 | 0 | 1 | 0 | 0.894 | 0.000 | 34/1 | lexical |
| hybrid_lexical_no_reportaware | 1 | 0 | 0 | 0 | 0.935 | 0.000 | 34/1 | lexical |
| hybrid_crossencoder_no_reportaware | 1 | 1 | 0 | 0 | 0.959 | 0.000 | 34/1 | cross_encoder |
| hybrid_crossencoder_reportaware | 1 | 1 | 1 | 0 | 0.910 | 0.000 | 35/0 | cross_encoder |
| routed_full | 1 | 1 | 1 | 1 | 0.918 | 0.000 | 35/0 | cross_encoder |

Metric note: variants are run in isolated subprocesses so environment-controlled config is reloaded for each condition.
If a requested neural reranker cannot be loaded, the observed reranker column will show lexical fallback.
