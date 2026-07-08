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
