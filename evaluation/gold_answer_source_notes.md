# Public Answer-Target Benchmark Source Notes

The public answer-target benchmark is a non-expert stress-test set. It is not an expert-adjudicated medical physics exam and it is not a substitute for clinical or board-review validation.

## Included Source Types

- 12 public external answer-key seed items from AFOMP medical physics pages and the RANZCR public sample questions and answers PDF.
- 49 open-report answer-target items generated from public AAPM/IAEA source metadata and locally parsed report evidence.

The benchmark stores paraphrased questions and short answer targets. It does not copy private, leaked, commercial, ABR, RAPHEX, or board-review question-bank material. Open-report targets are generated from public source catalog entries and are used to test whether the skill can retrieve and surface report-grounded answer targets.

## Intended Use

- Check whether the skill can retrieve evidence that contains a known public answer target.
- Expose extractive-only limitations on calculation-style and public-answer-key questions.
- Provide a reproducible placeholder until expert answer adjudication is available.
- Separate retrieval/evidence gaps from answer-synthesis gaps.

## Interpretation Boundary

`gold_answer_success_rate` means the returned evidence/answer text contained the expected short target and citation evidence was present. It does not mean the system has passed expert medical physics grading.
