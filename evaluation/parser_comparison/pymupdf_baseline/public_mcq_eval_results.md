# Public Medical Physics MCQ Evaluation

- Dataset: Radiation Oncology NLP Database Medical Physics 100-question QA set
- Source commit: 27e04f14a141a3a92dcc1df0449245175ae94b7c
- Questions: 100
- Retrieval backend: auto
- Option selector backend: cross_encoder
- Skill OK rate: 1.000
- Citation-present rate: 1.000
- Evidence contains gold-option text: 0.140
- Extractive answer contains gold-option text: not run (evidence-only skill mode)
- MCQ option accuracy: 0.340
- Mean total latency: 14.932 s/question

The option selector sees only question, options, and skill-returned evidence. Gold labels are read only after selection to compute MCQ accuracy. This is a public answer-keyed external benchmark, not a hidden test, a Codex-host evaluation, expert grading, or clinical validation.
