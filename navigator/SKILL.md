---
name: radiotherapy-physics-navigator
description: >
  Navigate the local radiotherapy physics evidence corpus by topic before retrieving full evidence chunks. Use when questions require corpus overview, multi-report synthesis, source triage, or agent-visible RAG navigation.
---

# Radiotherapy Physics Navigator

This navigator is a metadata map over the local indexed corpus. Use it to decide where to look, then retrieve full evidence with `get_chunk` or `query_reports`.

## Hard Rules

- Treat this navigator as routing metadata, not as answer evidence.
- Every factual answer must cite chunks returned by `get_chunk` or `query_reports`.
- Scan at least two plausible topic branches for broad synthesis questions.
- Use `entity_index.json` for report IDs, topic names, and recurring terms.

## Topic Branches

- `topics/reference-dosimetry/INDEX.md` (2789 chunks, 11 docs): Absorbed dose, ionization chambers, beam quality, calibration coefficients, small fields, and reference dosimeters.
- `topics/brachytherapy/INDEX.md` (143 chunks, 2 docs): Brachytherapy source calibration, dose calculation, QA, mesh, ocular plaque, and HDR/LDR workflow.
- `topics/treatment-planning/INDEX.md` (1158 chunks, 11 docs): TPS commissioning, acceptance testing, beam models, monitor units, plan review, IMRT/VMAT QA, and calculation verification.
- `topics/imaging-and-localization/INDEX.md` (428 chunks, 6 docs): kV imaging, CT simulation, CBCT, image registration, fusion, localization, surface guidance, and imaging dose.
- `topics/quality-management-and-safety/INDEX.md` (1415 chunks, 16 docs): Radiotherapy QA/QC, FMEA, chart review, audit, QUATRO, risk analysis, event narratives, and programme safety.
- `topics/equipment-and-facilities/INDEX.md` (78 chunks, 3 docs): Linacs, radiotherapy equipment, facility design, shielding, staffing, infrastructure, and programme implementation.
- `topics/nomenclature-and-data/INDEX.md` (104 chunks, 3 docs): TG-263 style naming, data transfer, structure naming, electronic charting, and interoperability.
- `topics/biological-models-and-response/INDEX.md` (37 chunks, 1 docs): TCP, NTCP, biological response models, RBE, radiobiology, and biologically based optimization QA.
- `topics/nontarget-dose-and-radiation-protection/INDEX.md` (935 chunks, 3 docs): Out-of-field dose, imaging dose, induced activity, radiation protection, shielding, and safety of sources.
- `topics/education-and-foundations/INDEX.md` (2203 chunks, 5 docs): General radiation oncology physics foundations, residency training scope, definitions, and teaching reference material.

## Full Metadata Indexes

- `topic_indexes/<topic>.jsonl`: chunk-level pointers for grep/search.
- `all_chunks_index.jsonl`: all navigator rows.
- `entity_index.json`: report IDs, topic paths, and high-frequency terms.
