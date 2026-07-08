#!/usr/bin/env python
"""Expose the RAG skill as an MCP stdio server."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.list_corpus import list_corpus
from scripts.run_skill import SkillExecutionError, build_error_response, format_citation_text, format_page_range, run_skill
from src.utils import iter_jsonl


def create_mcp(default_index_dir: Path = Path("index")):
    try:
        from mcp.server.fastmcp import FastMCP
    except Exception as exc:  # pragma: no cover - dependency boundary
        raise RuntimeError("MCP support requires the mcp package. Run pip install -r requirements.txt.") from exc

    mcp = FastMCP("radiotherapy-physics-rag")

    @mcp.tool()
    def query_reports(
        query: str,
        mode: str = "evidence",
        report_id: Optional[str] = None,
        evidence_top_k: Optional[int] = None,
        answer_engine: str = "auto",
        retrieval_backend: Optional[str] = None,
        index_dir: str = "",
    ) -> dict:
        """Query indexed radiotherapy physics reports with grounded RAG evidence."""
        try:
            return run_skill(
                mode=mode,
                query=query,
                index_dir=Path(index_dir) if index_dir else default_index_dir,
                report_id=report_id,
                evidence_top_k=evidence_top_k,
                answer_engine=answer_engine,
                retrieval_backend=retrieval_backend,
            )
        except SkillExecutionError as exc:
            return build_error_response(exc.code, exc.message, exc.details, mode, query)
        except Exception as exc:  # pragma: no cover - defensive MCP boundary
            return build_error_response(
                "runtime_failure",
                str(exc),
                {"exception_type": exc.__class__.__name__},
                mode,
                query,
            )

    @mcp.tool()
    def list_reports(root: str = ".") -> dict:
        """List local corpus PDFs, chunks, and indexed report identifiers."""
        return list_corpus(Path(root).resolve())

    @mcp.tool()
    def get_chunk(chunk_id: str, index_dir: str = "") -> dict:
        """Retrieve one full indexed evidence chunk by chunk_id."""
        target_index = Path(index_dir) if index_dir else default_index_dir
        metadata_path = target_index / "metadata" / "chunk_metadata.jsonl"
        if not metadata_path.exists():
            return {
                "ok": False,
                "error": {
                    "code": "missing_index",
                    "message": "Chunk metadata is missing.",
                    "details": {"metadata_path": str(metadata_path)},
                },
            }
        for record in iter_jsonl(metadata_path):
            rid = str(record.get("chunk_id", ""))
            if rid == chunk_id or rid.startswith(chunk_id):
                page_range = format_page_range(record.get("page_start", 0), record.get("page_end", 0))
                return {
                    "ok": True,
                    "chunk_id": rid,
                    "doc_id": record.get("doc_id"),
                    "document": record.get("title"),
                    "section": record.get("section"),
                    "subsection": record.get("subsection"),
                    "page_start": record.get("page_start"),
                    "page_end": record.get("page_end"),
                    "page_range": page_range,
                    "chunk_kind": record.get("chunk_kind", "standard"),
                    "tags": record.get("tags", []),
                    "citation": format_citation_text("E1", str(record.get("title", "")), str(record.get("section", "")), page_range, rid),
                    "text": record.get("text", ""),
                }
        return {
            "ok": False,
            "error": {
                "code": "out_of_scope",
                "message": f"Chunk '{chunk_id}' is not indexed.",
                "details": {"metadata_path": str(metadata_path)},
            },
        }

    @mcp.tool()
    def list_navigator_topics(root: str = ".") -> dict:
        """List navigator topics and their indexed document IDs."""
        navigator_path = Path(root).resolve() / "navigator" / "entity_index.json"
        if not navigator_path.exists():
            return {
                "ok": False,
                "error": {
                    "code": "missing_navigator",
                    "message": "Navigator index has not been built. Run scripts/build_navigator.py.",
                    "details": {"navigator_path": str(navigator_path)},
                },
            }
        data = json.loads(navigator_path.read_text(encoding="utf-8"))
        return {"ok": True, "navigator_path": str(navigator_path), "topics": data.get("topics", {})}

    return mcp


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the radiotherapy physics RAG MCP server over stdio.")
    parser.add_argument("--index-dir", type=Path, default=Path("index"))
    args = parser.parse_args()
    create_mcp(args.index_dir).run()


if __name__ == "__main__":
    main()
