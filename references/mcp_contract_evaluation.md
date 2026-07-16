# MCP Contract Evaluation

`scripts/evaluate_mcp_contract.py` is a protocol-level integration test for the distributable skill. It starts `scripts/mcp_server.py` as a separate stdio process, initializes an MCP client session, lists the registered tools, and invokes representative corpus, navigator, chunk, evidence, bundle, table-answer, and out-of-domain calls.

Run it only in a full local runtime that has an index, navigator, PDFs, and model dependencies:

```bash
python scripts/evaluate_mcp_contract.py --index-dir index
```

The task fixture is `evaluation/radiotherapy_mcp_contract_tasks.json`; outputs are `evaluation/mcp_contract_eval_results.json` and `.md`.

This evaluation verifies MCP transport and tool-contract behavior. It does not assess whether Codex, ChatGPT, Claude, or another host autonomously selects the skill at the right time, plans a multi-step workflow correctly, or gives clinically correct advice. Those claims require a host-agent benchmark and expert review respectively.
