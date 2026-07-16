#!/usr/bin/env python
"""Evaluate the public skill through a real MCP stdio client/server session.

The existing agent-task evaluation calls the Python contract directly.  This
script validates a separate deployment boundary: an MCP client starts the
stdio server, completes protocol initialization, lists tools, and calls the
registered tools.  It does not assess autonomous agent planning.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.evaluate import load_questions
from src.utils import write_json

REQUIRED_TOOL_NAMES = {"query_reports", "list_reports", "get_chunk", "list_navigator_topics"}


def normalize(text: str) -> str:
    return " ".join(text.lower().replace("\u2013", "-").replace("\u2014", "-").split())


def group_hit(text: str, groups: List[List[str]]) -> bool:
    for group in groups:
        if not any(normalize(alias) in normalize(text) for alias in group):
            return False
    return True


def response_payload(result: Any) -> Dict[str, Any]:
    """Decode FastMCP's JSON text content without depending on private APIs."""
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict):
        return structured
    texts = [str(getattr(item, "text", "") or "") for item in getattr(result, "content", [])]
    for text in texts:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return {
        "ok": False,
        "error": {
            "code": "invalid_mcp_payload",
            "message": "The MCP tool response did not contain a JSON object.",
            "details": {"text_content_count": len(texts), "transport_error": bool(getattr(result, "isError", False))},
        },
    }


def retrieved_doc_ids(payload: Dict[str, Any]) -> List[str]:
    evidence = payload.get("evidence", []) or []
    return [str(item.get("doc_id", "")) for item in evidence[:5] if item.get("doc_id")]


def asset_trace_hit(payload: Dict[str, Any], asset_id: str) -> bool:
    for evidence in payload.get("evidence", []) or []:
        for asset in evidence.get("nearby_assets", []) or []:
            if asset.get("asset_id") == asset_id:
                return True
    return False


def evaluate_payload(task: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, bool]:
    expected_abstain = bool(task.get("expected_abstain"))
    if expected_abstain:
        actual_code = str((payload.get("error") or {}).get("code", ""))
        return {
            "ok": not bool(payload.get("ok")),
            "abstention": actual_code in set(task.get("expected_error_codes", [])),
            "tool_specific": True,
            "doc": True,
            "citation": True,
            "bundle": True,
            "asset": True,
            "answer_value": True,
        }

    expected_docs = set(task.get("expected_doc_ids", []) or [])
    docs = set(retrieved_doc_ids(payload))
    if task.get("tool") == "get_chunk":
        docs.add(str(payload.get("doc_id", "")))
    expected_asset = str(task.get("expected_asset_id", "") or "")
    expected_groups = task.get("expected_answer_groups", []) or []
    tool_specific = True
    if task.get("tool") == "list_reports":
        tool_specific = int(payload.get("indexed_chunk_count", 0) or 0) > 0 and bool(payload.get("indexed_report_ids"))
    elif task.get("tool") == "list_navigator_topics":
        tool_specific = bool(payload.get("topics"))

    return {
        "ok": bool(payload.get("ok")),
        "abstention": True,
        "tool_specific": tool_specific,
        "doc": not expected_docs or bool(expected_docs & docs),
        "citation": not task.get("expected_citations") or bool(payload.get("citations")),
        "bundle": not task.get("expected_bundle_prompt") or bool(payload.get("prompt_for_medgemma")),
        "asset": not expected_asset or asset_trace_hit(payload, expected_asset),
        "answer_value": not expected_groups or group_hit(str(payload.get("answer", "") or ""), expected_groups),
    }


async def evaluate_mcp_contract_async(
    tasks: List[Dict[str, Any]], index_dir: Path, timeout_seconds: int
) -> Dict[str, Any]:
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except Exception as exc:  # pragma: no cover - dependency boundary
        raise RuntimeError("MCP contract evaluation requires the mcp package.") from exc

    server = StdioServerParameters(
        command=sys.executable,
        args=["-B", "scripts/mcp_server.py", "--index-dir", str(index_dir)],
        cwd=PROJECT_ROOT,
    )
    details = []
    async with stdio_client(server) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            initialization = await session.initialize()
            tool_response = await session.list_tools()
            tool_names = sorted(tool.name for tool in tool_response.tools)
            required_tools_present = REQUIRED_TOOL_NAMES.issubset(set(tool_names))

            for task in tasks:
                transport_error = None
                try:
                    call_result = await session.call_tool(
                        str(task["tool"]),
                        arguments=task.get("arguments", {}),
                        read_timeout_seconds=timedelta(seconds=timeout_seconds),
                    )
                    payload = response_payload(call_result)
                except Exception as exc:  # pragma: no cover - external process boundary
                    transport_error = f"{exc.__class__.__name__}: {exc}"
                    payload = {
                        "ok": False,
                        "error": {"code": "mcp_transport_failure", "message": transport_error, "details": {}},
                    }

                flags = evaluate_payload(task, payload)
                success = all(flags.values())
                details.append(
                    {
                        "qid": task.get("qid"),
                        "tool": task.get("tool"),
                        "expected_abstain": bool(task.get("expected_abstain")),
                        "transport_error": transport_error,
                        "response_ok": bool(payload.get("ok")),
                        "error_code": (payload.get("error") or {}).get("code"),
                        "retrieved_doc_ids_at_5": retrieved_doc_ids(payload),
                        "checks": flags,
                        "task_success": success,
                    }
                )

    total = max(1, len(tasks))
    in_scope = [item for item in details if not item["expected_abstain"]]
    ood = [item for item in details if item["expected_abstain"]]
    return {
        "tasks": len(tasks),
        "transport": "mcp_stdio",
        "mcp_server_name": initialization.serverInfo.name,
        "mcp_protocol_version": initialization.protocolVersion,
        "tool_names": tool_names,
        "required_tools_present": required_tools_present,
        "task_success_rate": sum(item["task_success"] for item in details) / total,
        "in_scope_task_success_rate": sum(item["task_success"] for item in in_scope) / max(1, len(in_scope)),
        "ood_refusal_success_rate": sum(item["task_success"] for item in ood) / max(1, len(ood)),
        "transport_error_count": sum(bool(item["transport_error"]) for item in details),
        "details": details,
        "metric_note": (
            "This is an end-to-end MCP stdio transport and tool-contract evaluation. "
            "It does not evaluate an autonomous host agent's planning, tool selection, or clinical correctness."
        ),
    }


def write_markdown(summary: Dict[str, Any], output_path: Path) -> None:
    lines = [
        "# MCP Contract Evaluation Results",
        "",
        f"- Tasks: {summary['tasks']}",
        f"- Transport: {summary['transport']}",
        f"- MCP server: {summary['mcp_server_name']}",
        f"- Required tools present: {summary['required_tools_present']}",
        f"- Task success rate: {summary['task_success_rate']:.3f}",
        f"- In-scope task success rate: {summary['in_scope_task_success_rate']:.3f}",
        f"- OOD refusal success rate: {summary['ood_refusal_success_rate']:.3f}",
        f"- Transport errors: {summary['transport_error_count']}",
        "",
        summary["metric_note"],
        "",
        "## Failed Tasks",
        "",
    ]
    failures = [item for item in summary["details"] if not item["task_success"]]
    if not failures:
        lines.append("None.")
    for item in failures:
        lines.extend(
            [
                f"### {item['qid']}",
                f"- Tool: {item['tool']}",
                f"- Error code: {item['error_code']}",
                f"- Transport error: {item['transport_error']}",
                f"- Checks: {item['checks']}",
                "",
            ]
        )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the skill through a real MCP stdio session.")
    parser.add_argument("--tasks", type=Path, default=Path("evaluation/radiotherapy_mcp_contract_tasks.json"))
    parser.add_argument("--index-dir", type=Path, default=Path("index"))
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--output-json", type=Path, default=Path("evaluation/mcp_contract_eval_results.json"))
    parser.add_argument("--output-md", type=Path, default=Path("evaluation/mcp_contract_eval_results.md"))
    args = parser.parse_args()

    summary = asyncio.run(
        evaluate_mcp_contract_async(load_questions(args.tasks), args.index_dir, args.timeout_seconds)
    )
    write_json(args.output_json, summary)
    write_markdown(summary, args.output_md)
    print(json.dumps({key: value for key, value in summary.items() if key != "details"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
