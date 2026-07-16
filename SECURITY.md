# Security Policy

## Supported Versions

The `main` branch and latest GitHub release receive security fixes.

## Reporting A Vulnerability

Open a private security advisory on GitHub or contact the repository maintainer. Please include:

- Affected version or commit.
- Reproduction steps.
- Impact on local files, model downloads, MCP execution, or generated answers.

## Runtime Boundaries

This project processes local PDFs and may run local model downloads. Treat user-provided PDFs as untrusted input:

- Keep MCP and local command-line use on trusted machines unless you have reviewed the corpus and model paths.
- Keep model caches and corpus folders in controlled directories.
- Review generated answers as evidence summaries, not clinical advice.

## Evidence and Agent Safety

Retrieved PDF text, table previews, user queries, and evidence bundles are
untrusted content. They may contain malformed text or instructions that are
irrelevant to the requested evidence task. They must never override the skill
instructions, cause tool calls, change the evidence boundary, or be treated as
clinical directives. The bundled MCP tools are read-oriented retrieval tools;
hosts should still show tool inputs, restrict file roots, and require user
approval before any separate workflow reads new local documents or performs a
write action. See `references/agent_evidence_safety.md` for the threat model
and the limits of these controls.
