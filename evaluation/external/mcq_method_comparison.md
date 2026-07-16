# Public MCQ Method Comparison

- Benchmark: Radiation Oncology NLP Database Medical Physics 100-question QA set
- Questions: 100
- Boundary: All results use a public answer-keyed benchmark. They are not hidden-test, expert, or clinical-validation results.

| Method | Parser/runtime | Answer host | Accuracy | Mean latency (s/question) |
|---|---|---|---:|---:|
| PyMuPDF + deterministic cross-encoder option selector | PyMuPDF historical snapshot | deterministic option-evidence selector | 0.340 | 14.932 |
| OpenDataLoader + deterministic cross-encoder option selector | OpenDataLoader rebuilt runtime | deterministic option-evidence selector | 0.360 | 13.503 |
| OpenDataLoader + Codex agent using local skill evidence | OpenDataLoader rebuilt runtime | Codex agent, instructed to call the local skill before selecting | 0.960 | 9.059 |

## Pairwise Outcome Changes

- PyMuPDF selector to OpenDataLoader selector: improved 16, regressed 14, both correct 20, both incorrect 50.
- OpenDataLoader selector to Codex-agent skill use: improved 61, regressed 1, both correct 35, both incorrect 3.

## Interpretation

- Only the first two methods hold the answer-selection mechanism fixed and therefore isolate the parser/index change.
- The Codex-agent result changes both the parser/runtime and the answer host. It demonstrates agent use of skill evidence, not a parser-only effect.
- The Codex CLI MCP runner was implemented but its non-interactive Windows MCP call was cancelled by host authorization; this live result used direct local skill calls by the Codex agent.
