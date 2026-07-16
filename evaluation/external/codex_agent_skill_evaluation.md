# Codex Agent With Local Skill: Public MCQ Evaluation

## Purpose

This report records a live development evaluation in which Codex selected
answers to 100 public medical-physics MCQs after obtaining local evidence from
the radiotherapy RAG skill. It is deliberately separate from the parser-only
PyMuPDF-versus-OpenDataLoader comparison.

## Inputs And Boundary

- Task input: `public_mcq_codex_host_tasks.jsonl`, which has question text and
  options but no `gold_label` field.
- Answer log: `codex_agent_skill_answers.jsonl`, with selected label,
  citation(s), and latency for all 100 question IDs.
- Scoring key: `public_medical_physics_100_mcq.json`, read only by
  `score_host_mcq_answers.py` after task and answer-log validation.
- Evidence source: the local OpenDataLoader-built report index, queried through
  the local skill before answer selection.

The public questions and answer keys are development data. This repository
layout cannot cryptographically isolate a local agent from a public key file.
The evaluation is thus reproducible engineering evidence, not a blinded exam,
expert assessment, or clinical validation.

## Result

| Metric | Result |
| --- | ---: |
| Questions answered | 100/100 |
| Correct labels | 96/100 |
| Accuracy | 0.960 |
| Responses with citation(s) | 100/100 |
| Mean latency | 9.059 s/question |
| Median latency | 7.471 s/question |
| P95 latency | 23.573 s/question |

## Transport Limitation

`run_codex_host_mcq.py` creates an answer-key-free temporary MCP configuration
and supports a future non-interactive host run. On this Windows environment,
the Codex CLI cancelled the MCP tool call at the host-authorization boundary.
No approval-bypass flag was used. The recorded 96/100 run therefore used direct
local skill calls by the Codex agent, not a fully non-interactive CLI-to-MCP
transport path.
