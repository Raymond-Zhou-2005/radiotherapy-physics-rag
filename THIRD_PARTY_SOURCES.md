# Third-party Sources

This repository stores source metadata and build scripts. It does not redistribute third-party report PDFs or derived full-text artifacts.

## Report Sources

The starter corpus source list is maintained in `reports/starter_corpus_sources.json`. It records official source URLs, expected local filenames, titles, organizations, and the role of each document.

Users are responsible for downloading and using report PDFs under the terms of the original publishers. Generated local artifacts are ignored by Git:

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

Private licensed ABR, RAPHEX, institutional, or commercial questions should be kept in `.local.json` files under `evaluation/`. These files are ignored by Git.

## Dependency Licenses

Project code is MIT licensed. Python dependencies, local model packages, and report PDFs remain under their own licenses and terms.
