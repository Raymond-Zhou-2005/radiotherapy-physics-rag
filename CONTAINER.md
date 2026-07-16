# Source-Only Container Build

The Docker image packages source code, public evaluation artifacts, and
dependencies. It deliberately excludes third-party report PDFs, parsed text,
chunks, indexes, extracted assets, ChatGPT Knowledge uploads, and model caches.
It is therefore a source-package validation image, not a ready-to-query
radiotherapy runtime image.

It includes OpenJDK 17 because OpenDataLoader PDF, the project's parser,
requires Java 11 or newer.

## Build

```bash
docker build -t radiotherapy-physics-rag:source .
```

## Validate The Public Source Package

```bash
docker run --rm radiotherapy-physics-rag:source
```

## Build A Local Runtime

Mount only PDFs and generated artifacts that you are permitted to use. Do not
publish an image containing third-party PDFs or derived full text unless you
have explicit redistribution rights. After mounting the permitted local
directories, run the documented download, index, asset-extraction, and
evaluation commands from the README.

## Current Verification Boundary

This repository includes a static source-only container contract. Docker was
not installed on the maintainer machine when this file was prepared, so a local
image build is not claimed as completed. A future CI or release workflow should
run the build command above and record its image digest.
