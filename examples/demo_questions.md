# Demo Questions

Use these after the local corpus and index are built. Keep generated full
evidence outputs local unless you have checked that they do not reproduce long
copyrighted passages.

## In-scope Evidence Queries

```bash
python scripts/plugin_query.py --mode evidence --retrieval-backend sparse "How are process maps, FMEA, fault trees, severity, occurrence, and detectability used in radiotherapy quality management?"
```

Expected source direction: AAPM TG 100.

```bash
python scripts/plugin_query.py --mode evidence --retrieval-backend sparse "How is absorbed dose to water determined for external beam reference dosimetry using calibrated ionization chambers?"
```

Expected source direction: IAEA TRS 398.

```bash
python scripts/plugin_query.py --mode evidence --retrieval-backend sparse "What commissioning tests are recommended for computerized treatment planning systems used in radiation therapy?"
```

Expected source direction: IAEA TRS 430.

```bash
python scripts/plugin_query.py --mode evidence --retrieval-backend sparse "What elements should an image guided radiotherapy QA programme include for imaging systems, registration, workflow, and safety?"
```

Expected source direction: IAEA HHR 16 and related image guidance reports.

```bash
python scripts/plugin_query.py --mode evidence --retrieval-backend sparse "How should nontarget and out-of-field doses be measured, calculated, reduced, and reported in external beam radiation therapy?"
```

Expected source direction: AAPM TG 158.

## Extractive Answer Demo

```bash
python scripts/plugin_query.py --mode answer --answer-engine extractive --retrieval-backend sparse "What quality assurance issues arise when biological response models are used in treatment planning?"
```

Expected behavior: concise extractive answer using returned evidence only.

## Out-of-scope Abstention Demo

```bash
python scripts/plugin_query.py --mode evidence --retrieval-backend sparse "What does the corpus say about portfolio allocation between municipal bonds and cryptocurrency ETFs?"
```

Expected behavior: insufficient evidence / abstention rather than invented
radiotherapy evidence.

