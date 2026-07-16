# Corpus Provenance Protocol

The public source catalog identifies where a user may locate reports. It is not
a blanket license statement and it does not redistribute source PDFs or derived
full text.

After a local runtime is built, generate an auditable local manifest:

```bash
python scripts/build_provenance_manifest.py \
  --sources reports/starter_corpus_sources.json \
  --reports-dir reports/raw \
  --corpus-manifest reports/manifest.jsonl \
  --output reports/provenance_manifest.json
```

For each report, the generated manifest records the source URL, optional direct
or rendered URL, local SHA-256, file size, and page count. It intentionally
uses `not_verified` when the publisher license or access terms have not been
checked by a maintainer. Do not change this field to `verified` without a
recorded review of the applicable publisher terms.

`reports/provenance_manifest.json` is a local runtime artifact. It is ignored
by Git because it identifies a particular local corpus build. A paper should
report its aggregate corpus version and manifest checksum, not redistribute the
underlying PDFs or their derived full text.

## Runtime Fingerprint

After the corpus, indexes, assets, model cache, and frozen evaluations are in
place, run the local integrity audit:

```bash
python scripts/audit_runtime_integrity.py --root .
```

The generated `evaluation/runtime_integrity_audit.json` and Markdown summary
are local-only artifacts. They verify local PDF SHA-256 values against both
the corpus and provenance manifests; fingerprint the runtime indexes, model
cache revisions, and dependency versions; and require the frozen evaluation
output audit to pass. They do not verify publisher rights, benchmark labels,
clinical correctness, expert agreement, or external generalization.
