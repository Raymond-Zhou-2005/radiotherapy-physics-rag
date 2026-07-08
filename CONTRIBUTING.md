# Contributing

Thank you for improving `radiotherapy-physics-rag`.

## Local Setup

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]" -c constraints.txt
```

Use `source .venv/bin/activate` on Linux or macOS.

## Development Checks

```bash
pytest -q
python scripts/validate_skill_package.py --skill-root . --check-sample-baseline
python scripts/build_skill_bundle.py --skill-root . --output dist/radiotherapy-physics-rag.zip
```

## Retrieval Changes

Retrieval quality is part of the public contract. Any change to parsing, chunking, indexing, retrieval, reranking, or evidence sufficiency should include:

- A before/after note for at least one affected starter-corpus report, preferably with the balanced corpus validation still passing.
- Updated evaluation output under `evaluation/` when the local starter corpus is available.
- A short explanation of why citations and abstention behavior remain safe.

## Pull Requests

- Keep changes focused.
- Do not remove structured error handling.
- Do not let answer generation bypass retrieved evidence.
- Add or update examples when changing user-facing outputs.
