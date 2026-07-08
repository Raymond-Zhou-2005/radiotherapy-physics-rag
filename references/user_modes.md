# User Modes And Python Boundary

This project has two user-facing modes. The important distinction is between
what a user sees and what the local system uses internally.

## 1. Codex Plugin Full Mode

Target users:

- technical users
- researchers
- developers
- medical physics students or physicists comfortable with local tooling

User experience:

- The user asks Codex an evidence question.
- Codex reads the skill instructions.
- Codex calls the local MCP server or repository scripts.
- The answer returns report title, section, page range, chunk ID, evidence text,
  scores, and citation strings.

What happens underneath:

- Python parses local PDFs.
- Python chunks text and builds BM25/dense indexes.
- Python retrieves and reranks evidence.
- Codex or another host model writes the final prose from returned evidence.

The user should not have to write Python application code to ask a question.
Python is still the local execution engine because the public repository does
not redistribute copyrighted PDFs, parsed full text, chunks, or indexes.

## 2. ChatGPT Knowledge Lightweight Mode

Target users:

- ordinary Custom GPT users
- collaborators who need a no-deployment interface
- readers who only need lightweight evidence lookup

User experience:

- The maintainer or local corpus owner generates Markdown Knowledge files.
- The Custom GPT owner uploads those files in GPT Builder.
- The user asks questions inside ChatGPT.
- The GPT cites document titles, page ranges, and chunk IDs embedded in the
  uploaded Knowledge files.

What happens underneath:

- The upload files are generated from the same local build pipeline.
- After upload, ordinary users do not run Python for normal use.
- Retrieval control is weaker than the local RAG path because Custom GPT
  Knowledge retrieval is managed by ChatGPT.

## Why Not Ship A Fully No-code Public Package?

The project intentionally does not commit:

- third-party report PDFs
- parsed full text
- chunks
- BM25/FAISS indexes
- generated ChatGPT Knowledge upload files

This protects publisher copyright boundaries and keeps the public repository
small. A fully prebuilt no-code package would require redistributing derived
full text or copyrighted source PDFs, which is not appropriate for the public
repository.

## Recommended Wording

Use this wording in demos and papers:

> The project is no-code for ordinary question asking in the ChatGPT Knowledge
> mode and low-code for technical users in Codex Plugin mode. Python is used as
> the local build and retrieval engine, not as something ordinary users must
> write to ask evidence questions.

