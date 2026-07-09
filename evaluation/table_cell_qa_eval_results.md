# Table Cell QA Evaluation Results

- Questions: 14
- Retrieval backend: auto
- Evidence top-k: 8
- Skill OK rate: 1.000
- Document Hit Rate@5: 1.000
- Page Hit Rate@5: 0.929
- Asset Trace Hit Rate@5: 0.929
- Answer Cell Value Hit Rate: 0.643
- Evidence Cell Value Hit Rate: 0.929
- Cell QA Success Rate: 0.929
- Unexpected errors: 0

Cell-level table QA checks exact short values in extracted table text previews. It is stricter than page-level asset proximity but still not human visual QA.

## Misses

### table_cell_q0009
- Expected asset: aapm_tg100_radiotherapy_quality_management_p014_table_01
- Error code: None
- Retrieved doc_ids@5: aapm_tg100_radiotherapy_quality_management, aapm_tg100_radiotherapy_quality_management, aapm_tg100_radiotherapy_quality_management, aapm_tg100_radiotherapy_quality_management, aapm_tg100_radiotherapy_quality_management
- Doc/Page/Asset/Cell: True/False/False/False
