# Output Contract

All skill entrypoint output is JSON.

## Modes

- `evidence`: retrieve, rerank, refine, and return evidence items with citations and scores.
- `bundle`: return the same evidence plus `prompt_for_medgemma` for downstream grounded generation.
- `answer`: answer from selected evidence. Defaults to `--answer-engine auto`, which uses the configured local answer model when available and otherwise falls back to extractive evidence quoting.

## Success shape

Success responses include:

- `ok: true`
- `schema_version`
- `skill_name`
- `mode`
- `query`
- `report_scope`
- `evidence_status`
- `abstained`
- `rag_pipeline`
- `evidence`
- `citations`

Bundle mode also includes `prompt_for_medgemma`, the grounded prompt payload for a downstream local answer model.

Answer mode also includes `answer`, `confidence`, and `used_evidence_ids`.

## Error shape

Error responses include:

- `ok: false`
- `schema_version`
- `skill_name`
- `mode`
- `query`
- `error.code`
- `error.message`
- `error.details`

Codes:

- `missing_index`: index files are missing or incomplete.
- `out_of_scope`: query or requested report is outside indexed report QA.
- `insufficient_evidence`: retrieval did not produce enough relevant evidence.
- `missing_model_path`: answer mode was requested without `MEDGEMMA_MODEL_NAME_OR_PATH`.
- `ocr_required`: a scanned or low-text PDF needs OCR, or OCRmyPDF is missing when the OCR helper is called.
- `runtime_failure`: unexpected runtime exception.
- `empty_corpus`: indexing was requested before source PDFs were added.

MCP and local command-line surfaces return the same success and error objects. Document onboarding and reindexing are handled by local scripts.

## Evidence item

Each evidence item contains:

- `evidence_id`
- `chunk_id`
- `doc_id`
- `document`
- `section`
- `subsection`
- `page_start`
- `page_end`
- `page_range`
- `source_path`
- `citation`
- `chunk_kind`
- `parent_chunk_id`
- `text`
- `scores`

Scores preserve dense, BM25, fusion, retrieval heuristic, rerank, and rank fields when available.

Each citation mirrors the same locator fields and includes a display-ready `citation`
string in the form:

```text
[E1] Report title; section; pp. 10-12; chunk doc_id_c0001
```

`retrieval_backend="sparse"` requires only the BM25 index and chunk metadata.
`retrieval_backend="auto"` can fall back to the same sparse path when dense
retrieval files or local embedding models are unavailable. `hybrid` requires the
dense index files plus the sparse index.
