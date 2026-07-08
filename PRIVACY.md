# Privacy

`radiotherapy-physics-rag` is designed for local use.

- The Python CLI, MCP server, corpus builder, evaluator, and ChatGPT Knowledge exporter run on local files.
- The project does not include telemetry, analytics, or hosted logging.
- Local report PDFs, parsed text, chunks, indexes, extracted asset metadata, and generated ChatGPT Knowledge upload files remain on the user's machine unless the user explicitly uploads or shares them.
- Model downloads, when enabled, are handled by the configured model provider libraries such as Hugging Face. Their caches and network behavior follow the user's local environment and dependency configuration.

Do not place patient data, protected health information, private licensed question banks, or proprietary institutional procedures in a public repository.
