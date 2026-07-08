# Current Code And Metric Audit

This note records the July 2026 audit of chunking, indexing, retrieval, reranking, and evaluation behavior for the current radiotherapy physics RAG skill package.

## Compared Folders

- Current package: `D:\CodexWorkplace\2026-07-08_Radiotherapy_RAG_Skill_Complete`
- Prior implementation reference: `D:\DKU\Research\RAG\2.0`
- Additional historical reference checked: `D:\DKU\Research\RAG\med_report_rag`

## Code Differences Versus 2.0

### Chunking

The section-aware chunking implementation is effectively unchanged from 2.0. The current package still uses the same splitter structure and chunk metadata fields. The major difference is scale: the current runtime indexes 49 PDFs and 10923 chunks, while the prior 2.0 package was built around a smaller starter corpus.

Practical meaning: the chunking logic did not become smarter; retrieval performance changes mainly come from corpus expansion, sparse/hybrid index behavior, routing defaults, and evaluation changes.

### Indexing

The dense index builder path remains compatible with the earlier design, but the current package adds a sparse-only path:

- `scripts/prepare_index.py` now supports `--index-backend sparse`.
- `scripts/build_sparse_index.py` builds the BM25 payload without requiring embedding model downloads.
- `src/retrieval/sparse.py` caches BM25 payload loading.
- `src/retrieval/dense.py` caches dense index loading and validates model/backend metadata before querying.
- `src/retrieval/embedder.py` supports forced hash embeddings for reproducible no-model builds.

Practical meaning: the project can now run a public, reproducible BM25 benchmark without a neural embedding model. The bundled hash dense index is useful for CI and packaging checks, but it is not a semantic dense retriever.

### Retrieval

The basic hybrid retriever remains close to 2.0, but the skill-facing retrieval wrapper changed substantially:

- `scripts/run_skill.py` now supports `sparse`, `hybrid`, `auto`, and `routed`.
- `auto` can run from sparse files alone.
- `routed` uses query scene features and lightweight memory records to select a retrieval mode and evidence depth.
- Metadata and hybrid retriever objects are cached to reduce repeated load cost.
- The current patch treats hash dense artifacts as non-semantic by default. `auto` and `routed` use sparse retrieval unless a real semantic dense index is available or `RAG_ALLOW_HASH_HYBRID=1` is set.
- Routed query traces are no longer appended by default. Set `RAG_EXPERIENCE_APPEND=1` only for intentional local experiments; the public release excludes the local memory file.

Practical meaning: current default behavior is more conservative and more reproducible. It avoids letting a hash dense baseline degrade retrieval quality while still keeping explicit `hybrid` available for diagnostics.

### Reranking

`src/retrieval/reranker.py` now supports forced lexical reranking:

- `RAG_FORCE_LEXICAL_RERANK=1` prevents neural reranker loading.
- `RAG_FORCE_HASH_EMBEDDINGS=1` also forces lexical reranking.
- If lexical mode is forced, the reranker avoids importing sentence-transformer or transformer rerank models.

Practical meaning: public evaluation can run on machines without model downloads, GPU, or Hugging Face cache state. This improves reproducibility but limits semantic reranking strength.

## What Was Learned From Comparable RAG Skill Designs

The useful transferable ideas were:

- Package the system as an agent-callable skill, not only a chatbot. The agent needs clear entry points, argument contracts, evidence objects, and failure modes.
- Keep runtime artifacts separate from the public repository. Source metadata, scripts, tests, and benchmark assets are public; PDFs, parsed text, chunks, indexes, and generated full-text uploads stay local.
- Use a topic navigator as a routing layer. It gives an agent a structured map of the corpus before retrieval.
- Add strategy evaluation, navigator evaluation, and agent-contract evaluation separately. A retrieval algorithm can look good while the agent interface still fails, or the navigator can route to the right topic while missing the exact report.
- Include abstention behavior in the benchmark. A medical-domain RAG skill should know when the local corpus is insufficient.
- Make the no-model baseline explicit. A fully reproducible BM25 baseline is valuable even if later semantic dense baselines are added.

## Current Evaluation Snapshot

Benchmark:

- Total questions: 260.
- In-domain public-source topic questions: 245.
- Out-of-domain controls: 15.
- Runtime source records: 49.

Strategy evaluation:

| Strategy | Document Recall@3 | Document Recall@5 | OOD TP | OOD FP | OOD TN | OOD FN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| sparse | 0.755 | 0.857 | 15 | 0 | 245 | 0 |
| hybrid hash+dense | 0.702 | 0.804 | 15 | 0 | 245 | 0 |
| auto | 0.755 | 0.857 | 15 | 0 | 245 | 0 |
| routed | 0.755 | 0.857 | 15 | 0 | 245 | 0 |

Agent skill evaluation:

| Metric | Current value |
| --- | ---: |
| Tool success rate | 0.942 |
| Document Hit Rate@5 | 0.857 |
| Citation present rate | 1.000 |
| OOD abstention success rate | 1.000 |
| Unexpected errors | 0 |

Navigator evaluation:

| Metric | Current value |
| --- | ---: |
| Topic Recall@1 | 0.837 |
| Topic Recall@2 | 0.939 |
| Topic Recall@3 | 0.967 |
| Candidate Document Recall@1 | 0.188 |
| Candidate Document Recall@3 | 0.490 |
| Candidate Document Recall@5 | 0.673 |

## Comparison With Previous Public Release

The previous public release had 35 runtime documents and 190 questions. The current package has 49 runtime documents and 260 questions.

Strategy-level comparison:

| Strategy | Previous Doc Recall@3 | Current Doc Recall@3 | Previous Doc Recall@5 | Current Doc Recall@5 |
| --- | ---: | ---: | ---: | ---: |
| sparse | 0.686 | 0.755 | 0.806 | 0.857 |
| hybrid hash+dense | 0.663 | 0.702 | 0.754 | 0.804 |
| auto | 0.663 | 0.755 | 0.754 | 0.857 |
| routed | 0.674 | 0.755 | 0.794 | 0.857 |

Agent-contract comparison:

| Metric | Previous | Current |
| --- | ---: | ---: |
| Tool success rate | 0.947 | 0.942 |
| Document Hit Rate@5 | 0.800 | 0.857 |
| Citation present rate | 0.994 | 1.000 |
| OOD abstention success rate | 0.600 | 1.000 |
| Unexpected errors | 1 | 0 |

Navigator comparison:

| Metric | Previous | Current |
| --- | ---: | ---: |
| Topic Recall@1 | 0.880 | 0.837 |
| Topic Recall@2 | 0.926 | 0.939 |
| Topic Recall@3 | 0.966 | 0.967 |
| Candidate Document Recall@1 | 0.211 | 0.188 |
| Candidate Document Recall@3 | 0.480 | 0.490 |
| Candidate Document Recall@5 | 0.709 | 0.673 |

Interpretation: the expanded corpus improved document-level retrieval and agent evidence hits, especially after `auto` and `routed` stopped using hash dense retrieval as if it were semantic dense retrieval. Explicit OOD controls are now rejected before lexical overlap scoring. The main remaining cost is that navigator document ranking became harder because the runtime now contains more overlapping QA, IMRT, IGRT, SBRT, dosimetry, commissioning, and safety reports.

## Metric Meanings

- `Document Recall@3` / `Document Recall@5`: whether the expected source report appears among the top 3 or top 5 retrieved source documents. This is the main metric for the current public benchmark.
- `Recall@3` / `Recall@5`: whether the exact gold chunk appears in the top 3 or top 5 retrieved chunks. These are currently 0.000 because the public benchmark does not contain expert gold chunk IDs.
- `MRR`: mean reciprocal rank of the first exact gold chunk. This is also not meaningful until expert chunk-level gold labels exist.
- `OOD TP`: an out-of-domain question was correctly rejected or abstained.
- `OOD FP`: an in-domain question was incorrectly rejected.
- `OOD TN`: an in-domain question was answered instead of rejected.
- `OOD FN`: an out-of-domain question was incorrectly answered.
- `Topic Recall@k`: whether the navigator selected the expected broad topic within its top k topics.
- `Candidate Document Recall@k`: whether the navigator surfaced the expected source report within its top k candidate reports.
- `Tool success rate`: proportion of questions that return `ok=true`. Correct OOD abstentions are structured `insufficient_evidence` errors, so this rate can decrease when abstention improves.
- `Document Hit Rate@5`: whether the agent-facing evidence output includes the expected source report in its top 5 evidence items.
- `Citation present rate`: whether successful in-domain outputs include citations.
- `OOD abstention success rate`: proportion of out-of-domain control questions correctly rejected.
- `Unexpected errors`: uncaught or unexpected runtime failures during agent-skill evaluation.

## Optimization Opportunities

Highest-impact next steps:

1. Add a real semantic dense index with documented model name, cache instructions, and fixed embedding metadata, then rerun sparse, dense, hybrid, auto, and routed comparisons.
2. Add a source-title-aware reranking feature to handle overlapping reports, especially older/newer report versions and reports that share QA or commissioning vocabulary.
3. Further strengthen OOD abstention with a calibrated domain gate, evidence sufficiency threshold, and broader negative-topic controls. The current package already rejects explicit non-radiotherapy control topics before lexical overlap scoring.
4. Add expert or semi-expert gold chunk IDs for a smaller benchmark subset so `Recall@k` and `MRR` become meaningful.
5. Add table/figure-specific benchmark items if the paper wants to claim asset-aware retrieval rather than text-only evidence retrieval.
