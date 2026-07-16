# Document Onboarding

## Build the starter corpus locally

The repository includes source metadata for a radiotherapy physics starter corpus, but it does not redistribute third-party report PDFs or derived full-text indexes. Download the official source PDFs and build the local runtime artifacts before querying:

```bash
python scripts/download_starter_corpus.py
python scripts/prepare_index.py --reports-dir reports/raw --manifest reports/manifest.jsonl --parsed-dir parsed --chunks-dir chunks --index-dir index --index-backend sparse
```

Then run a query:

```bash
python scripts/plugin_query.py --mode evidence --retrieval-backend sparse "What does the corpus say about nontarget dose?"
```

## Start from no files

Run:

```bash
python scripts/init_corpus.py --root .
```

Then add PDF files to:

```text
reports/raw/
```

Build the corpus:

```bash
python scripts/prepare_index.py --reports-dir reports/raw --manifest reports/manifest.jsonl --parsed-dir parsed --chunks-dir chunks --index-dir index --index-backend sparse
```

## Inspect PDFs before indexing

Run:

```bash
python scripts/inspect_pdfs.py reports/raw --output reports/pdf_text_readiness.local.json
```

Use this before adding unfamiliar reports. PDFs with very low extracted text per page are probably scanned or image-heavy and should be OCRed before indexing.

## Extract table and image metadata

## Record local corpus provenance

Run `python scripts/build_provenance_manifest.py` after building the corpus.
The resulting local manifest captures observed PDF hashes and page counts, but
does not replace a maintainer's publisher-license review.

Run:

```bash
python scripts/extract_pdf_assets.py reports/raw --output-dir assets/extracted
```

This writes JSONL records with asset type, page, bounding box, caption, table shape, and image dimensions. Add `--save-images` only when embedded image binaries should also be exported.

## OCR scanned PDFs

If OCRmyPDF is available:

```bash
python scripts/ocr_pdfs.py reports/raw/scanned_report.pdf --output-dir reports/ocr
```

Then copy the OCRed output PDF back into `reports/raw/` or add it with:

```bash
python scripts/add_documents.py reports/ocr/scanned_report.pdf --rebuild
```

If OCRmyPDF is missing, the OCR helper returns `ok: false` with `error.code: ocr_required`. On Windows, OCRmyPDF usually also needs Ghostscript and Tesseract on `PATH`.

## Add documents by CLI

Copy one PDF and rebuild:

```bash
python scripts/add_documents.py path/to/report.pdf --rebuild
```

Copy every PDF in a directory and rebuild:

```bash
python scripts/add_documents.py path/to/pdf_folder --rebuild
```

Equivalent installed command:

```bash
radiotherapy-rag-add path/to/report.pdf --rebuild
```

## Document IDs

Document IDs are inferred from PDF filenames by `scripts/build_corpus.py`. For example:

- `AAPM Report 104.pdf` -> `aapm_report_104`
- `dose-reporting-guideline.pdf` -> `dose_reporting_guideline`

Use the resulting ID with:

```bash
python scripts/plugin_query.py --mode evidence --report-id <doc_id> --retrieval-backend sparse "..."
```

## Recommended source files

Best inputs are:

- text-native PDFs
- radiotherapy physics reports
- dosimetry codes of practice
- QA and safety guidance
- treatment planning reports
- clinical-trial physics manuals
- local institutional physics procedures

Avoid relying on scanned PDFs unless OCR is added before ingestion.

## Empty corpus behavior

If `prepare_index.py` finds no PDFs, it returns a JSON error:

```json
{
  "ok": false,
  "error": {
    "code": "empty_corpus"
  }
}
```

This is intentional. The skill must not pretend to answer without indexed source documents.
