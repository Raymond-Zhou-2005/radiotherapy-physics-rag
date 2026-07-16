# Agent Evidence Safety Boundary

## Scope

This document describes engineering safeguards for an evidence-retrieval skill.
It does not establish clinical safety, model robustness, or regulatory fitness.
The skill is not patient-specific decision support.

## Threat Model

Treat the following as untrusted data rather than trusted instructions:

- user questions and requested report identifiers;
- PDF text, OCR text, table previews, captions, and metadata;
- evidence bundles passed to a downstream language model; and
- any local document added after the original corpus build.

Potential failures include prompt injection embedded in source text, citation
laundering of an irrelevant passage, stale or altered PDF files, a host agent
calling unnecessary tools, and a downstream model converting technical evidence
into unsupported clinical advice.

## Implemented Controls

1. The skill keeps a bounded local corpus and returns document, page, chunk,
   and asset identifiers with evidence.
2. The local runtime integrity audit verifies PDF SHA-256 values against both
   corpus and provenance manifests and records the semantic-model revisions.
3. The generation prompt and skill rules state that evidence is quoted content,
   not instructions that can modify rules or cause tool use.
4. MCP tools provide retrieval and inspection functions only. They do not
   prescribe treatment, write to a patient record, or execute actions described
   in retrieved evidence.
5. OOD and medical-boundary controls test predefined refusals, while output
   schemas preserve error codes and cited evidence identifiers.

## Residual Risks

These controls do not prove resistance to adversarial PDFs or model-level prompt
injection. A host agent can still misuse a read-only tool, and a downstream
generative model can still make unsupported inferences from a valid citation.
Do not add unreviewed local documents to a high-stakes workflow. Future work
should evaluate adversarially authored evidence, malformed documents, host-side
permission boundaries, multi-agent tool selection, and expert review of safety
failures under a pre-registered protocol.
