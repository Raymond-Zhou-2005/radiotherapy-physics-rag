# Host-Agent Evaluation Protocol

## Status

The current 40 direct skill-contract tasks and 7 MCP stdio tasks validate local
interfaces. They do not evaluate a host agent's planning, tool choice, or
multi-step reasoning. This protocol defines that future evaluation.

## Host Configurations

Evaluate at least two independently configured host agents, for example a
Codex-compatible host and a second MCP-compatible host. Freeze for every run:

- host name and version;
- model identifier, temperature, tool-use settings, and system instructions;
- MCP server command and protocol version;
- skill instruction file checksum;
- local corpus manifest checksum; and
- date, operating system, Python version, and model-cache status.

Do not compare hosts when one has access to additional web search, private
documents, or hidden tools unless that access is explicitly part of the study.

## Task Families

Use a held-out task set that requires the host to decide which tool to call:

1. Find and cite a report-level answer with page and chunk evidence.
2. Compare two reports while preserving each source identity.
3. Retrieve a table-associated value and identify the relevant page/asset.
4. Reject a medically related but out-of-scope request.
5. Detect insufficient evidence rather than inventing a conclusion.
6. Produce a compact evidence bundle for a downstream writing/review step.

For each item, record the expected tool sequence at a permissive level, the
minimum evidence identifiers, whether abstention is expected, and a success
rubric. Do not hard-code a single exact natural-language answer as the only
passing behavior.

## Logged Outcomes

Store per-run, redacted JSON logs containing tool names, arguments, response
status, evidence identifiers, final output, latency, token/cost data where
available, and error codes. Keep private prompts or patient information outside
the public repository.

Report task success, unnecessary tool calls, invalid tool calls, evidence trace
success, appropriate abstention, and host-side failure modes separately.
Manual scoring of final answer correctness still requires the external review
protocol.
