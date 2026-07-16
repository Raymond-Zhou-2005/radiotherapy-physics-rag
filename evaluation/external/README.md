# External Public MCQ Benchmark

`public_medical_physics_100_mcq.json` is a version-pinned import of the
Apache-2.0 Radiation Oncology NLP Database medical-physics QA CSV. It has 100
questions, 402 answer-option rows, and exactly one source answer per question.
The pinned upstream commit is
[`27e04f14a141a3a92dcc1df0449245175ae94b7c`](https://github.com/Mayo-Clinic-RadOnc-Foundation-Models/Radiation-Oncology-NLP-Database/tree/27e04f14a141a3a92dcc1df0449245175ae94b7c);
the imported CSV SHA-256 is
`e78390ab24c8ceb62454df03d28fa029b50c28c599e221fd758531dc0e122f96`.

There are 98 four-option and two five-option questions. The benchmark is
public development data, not a private or hidden exam. Its answer keys are
included only in the evaluation data; they are not loaded by the runtime skill.

The benchmark is outside the RAG runtime corpus. `scripts/run_skill.py` never
loads it. Only `scripts/evaluate_public_mcq_exam.py` reads `gold_label` after
the skill has returned evidence and the option-evidence selector has selected
an option.

Run an evidence-only RAG evaluation:

```powershell
$env:RAG_RERANKER_BACKEND="cross_encoder"
python scripts/evaluate_public_mcq_exam.py --questions evaluation/external/public_medical_physics_100_mcq.json --index-dir index --retrieval-backend auto --skill-mode evidence --export-host-tasks evaluation/external/public_mcq_codex_host_tasks.jsonl
```

The task export deliberately omits gold labels. It can be given to a real
Codex or MCP host, whose response log should be scored separately. The local
option-evidence selector is not a proxy for host-agent planning or expert
medical-physics grading.

Score a host response log only after it has been produced:

```powershell
python scripts/score_host_mcq_answers.py --tasks evaluation/external/public_mcq_codex_host_tasks.jsonl --answers evaluation/external/codex_agent_skill_answers.jsonl --gold evaluation/external/public_medical_physics_100_mcq.json --output-json evaluation/external/codex_agent_skill_score.json --output-md evaluation/external/codex_agent_skill_score.md
```

## Frozen Results

The parser-only comparison holds the deterministic cross-encoder option
selector fixed:

| Runtime | Correct | Accuracy | Mean latency |
| --- | ---: | ---: | ---: |
| Historical PyMuPDF snapshot | 34/100 | 0.340 | 14.932 s/question |
| OpenDataLoader rebuild | 36/100 | 0.360 | 13.503 s/question |

OpenDataLoader improved 16 answers and regressed 14 relative to the historical
snapshot. This is the only comparison that attributes a difference to the PDF
parser/index change while holding answer selection fixed.

For the live agent-use run, Codex was instructed to read only the answer-key-
free host-task file, to avoid web search, and to call the local skill before
choosing each label. The final answer log has 100 selections and citations;
the independent scorer then joined it to the public keys:

- Correct: 96/100 (0.960).
- Citation present: 100/100 (1.000).
- Mean / median / p95 latency: 9.059 / 7.471 / 23.573 s per question.

The run is reproducible as a recorded development evaluation, but it is not
blinded or expert adjudicated. Filesystem isolation cannot prove that a local
development agent never encountered the public answer-key file, and the
non-interactive Windows Codex CLI MCP probe was cancelled by host
authorization. Therefore the result demonstrates Codex-agent use of the local
skill evidence, not an end-to-end non-interactive CLI MCP benchmark or a
clinical claim. See `mcq_method_comparison.md`, `codex_agent_skill_score.md`,
and `codex_host_runner.md` for the exact setup and limitations.
