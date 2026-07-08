# ChatGPT Knowledge Lightweight Package

This folder contains instructions for generating a Custom GPT Knowledge package from the local radiotherapy physics corpus. Generated upload files preserve chunk IDs, report titles, sections, page ranges, and source file metadata so the GPT can answer with traceable report evidence.

Use it in GPT Builder:

1. Build the local corpus from the repository root.
2. Run `python scripts/build_chatgpt_knowledge.py --root .`.
3. Create or edit a Custom GPT.
4. Upload every generated Markdown file in `upload_files/` to Knowledge.
5. Paste `custom_gpt_instructions.md` into Instructions.
6. Start with the questions in `starter_questions.md`.

`upload_manifest.json` is generated locally with the report files and chunk counts.
