# Release Checklist

Use this checklist before pushing or tagging a public release.

## Public Repository Safety

- [ ] `git status --short` reviewed.
- [ ] No third-party PDFs are tracked.
- [ ] No parsed full text is tracked.
- [ ] No chunk JSONL files are tracked.
- [ ] No BM25, FAISS, dense, or metadata index artifacts are tracked.
- [ ] No generated ChatGPT Knowledge upload Markdown files are tracked.
- [ ] No old zip, tmp, debug, Docker, API server, or local log artifacts are
  tracked.
- [ ] `.gitignore` still covers local runtime artifacts.

Suggested check:

```powershell
python scripts/audit_public_release.py --root D:\CodexWorkplace\RAG\radiotherapy-physics-rag-public
```

The audit should return `"ok": true`.

## Local Build

- [ ] Dependencies installed.
- [ ] Starter PDFs downloaded or manually provided under `reports/raw/`.
- [ ] `prepare_index.py --index-backend sparse` completed for the no-model path,
  or dense+BM25 completed after local model dependencies are available.
- [ ] `extract_pdf_assets.py` completed.
- [ ] `build_chatgpt_knowledge.py` completed locally.
- [ ] `plugin_doctor.py` reports `source_package_ok: true`.
- [ ] If local runtime artifacts are present, they remain ignored by Git.

## Validation

Run:

```bash
pytest -q
python scripts/validate_skill_package.py --skill-root .
python scripts/plugin_doctor.py --root .
```

If the local starter corpus has been built, also run:

```bash
python scripts/validate_skill_package.py --skill-root . --check-sample-baseline --require-index
python scripts/evaluate_strategies.py --questions evaluation/radiotherapy_skill_open_questions.json --index-dir index --strategies sparse hybrid auto routed --ignore-report-scope
python scripts/evaluate_navigator.py --questions evaluation/radiotherapy_skill_open_questions.json --navigator-dir navigator
python scripts/evaluate_agent_skill.py --questions evaluation/radiotherapy_skill_open_questions.json --index-dir index --retrieval-backend auto
python scripts/evaluate_ablation.py --questions evaluation/radiotherapy_skill_open_questions.json --index-dir index
python scripts/evaluate_table_cell_qa.py --questions evaluation/radiotherapy_table_cell_questions.json --index-dir index --retrieval-backend auto
python scripts/evaluate_gold_answers.py --questions evaluation/radiotherapy_gold_answer_questions.json --index-dir index --retrieval-backend auto
python scripts/evaluate_agent_tasks.py --tasks evaluation/radiotherapy_agent_tasks.json --index-dir index --retrieval-backend auto
python scripts/evaluate_answer_quality.py --questions evaluation/radiotherapy_skill_open_questions.json --index-dir index --retrieval-backend auto
python scripts/build_paper_experiment_matrix.py --eval-dir evaluation
```

## Demo Readiness

- [ ] At least five demo queries run successfully.
- [ ] One out-of-scope query abstains.
- [ ] Demo evidence includes document title, section, page range, and chunk ID.
- [ ] No demo output commits long copyrighted passages.
- [ ] Public evaluation summaries reflect the current corpus and benchmark.
- [ ] `evaluation/paper_experiment_matrix.md` reflects the current result files.

## Documentation

- [ ] README quickstart works from a fresh clone.
- [ ] `references/user_modes.md` clearly explains no-code versus local build.
- [ ] `THIRD_PARTY_SOURCES.md` reflects the source metadata policy.
- [ ] `PRIVACY.md` still states local-only behavior accurately.
- [ ] `CHANGELOG.md` records user-visible changes.

## DOI Release

- [ ] `.zenodo.json` metadata reviewed.
- [ ] GitHub release tag created, for example `v2.1.0`.
- [ ] Zenodo connected to the GitHub repository and the release imported.
- [ ] Real Zenodo DOI copied back into `CITATION.cff`, README, and the manuscript after Zenodo mints it.
- [ ] No placeholder DOI is committed as if it were final.
