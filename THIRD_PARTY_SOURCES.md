# Third-party Sources

This repository stores source metadata and build scripts. It does not redistribute third-party report PDFs or derived full-text artifacts.

## Report Sources

The starter corpus source list is maintained in `reports/starter_corpus_sources.json`. It records official source URLs, expected local filenames, titles, organizations, and the role of each document.

Some records include `download_url` or `render_url` hints when the official landing page is more stable than a direct PDF endpoint. For example, some AAPM/Wiley reports are public or free-access but may require browser rendering for a local runtime PDF. Users are responsible for downloading, rendering, and using report PDFs under the terms of the original publishers. Generated local artifacts are ignored by Git:

- `reports/raw/*.pdf`
- `reports/manifest.jsonl`
- `parsed/*.jsonl`
- `chunks/*.jsonl`
- `index/**`
- `assets/extracted/*.jsonl`
- `assets/extracted/asset_manifest.json`
- `chatgpt_knowledge/upload_files/*.md`
- `chatgpt_knowledge/upload_manifest.json`

## Evaluation

The public evaluation questions in `evaluation/public_credible_questions.json` and `evaluation/radiotherapy_skill_open_questions.json` are generated from the public source catalog metadata and official source URLs. They are not copied from paid, private, leaked, expert-only, ABR, RAPHEX, institutional, or commercial board-review question banks.

The current public benchmark is an open-source topic benchmark, not an expert-adjudicated clinical correctness benchmark.

`evaluation/external/public_medical_physics_100_mcq.json` is imported from the
Apache-2.0 **Radiation Oncology NLP Database** at its pinned commit
`27e04f14a141a3a92dcc1df0449245175ae94b7c`. It contains 100 public
medical-physics multiple-choice questions with one source answer each. The
imported license is retained at `evaluation/external/LICENSE-Apache-2.0.txt`.
This test is external to the runtime corpus, but public rather than hidden and
is not expert-adjudicated for this project. The runtime code does not read its
gold-answer fields.

Private licensed ABR, RAPHEX, institutional, or commercial questions should be kept in `.local.json` files under `evaluation/`. These files are ignored by Git.

## Dependency Licenses

Project code is MIT licensed. Python dependencies, local model packages, and report PDFs remain under their own licenses and terms.

### OpenDataLoader PDF

Local PDF parsing uses `opendataloader-pdf` rather than PyMuPDF. It is a
third-party Python package and Java-backed command-line parser. The runtime
requires Java 11 or newer. Its source, documentation, version, and license
must be checked from the upstream project before each release:
`https://github.com/opendataloader-project/opendataloader-pdf` and
`https://opendataloader.org/docs`.
