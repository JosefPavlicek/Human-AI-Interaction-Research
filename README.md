# Human–AI Interaction Research (HAIR)

Exploratory desktop tool for identifying **candidate conversational signals** of acceptance, authority deference, position shifts, disagreement, and verification in human–AI dialogues.

## Run

Python 3.9+ with Tkinter installed:

```bash
python app.py
```

No external Python packages, API keys, or cloud services required. Text remains local.

## Input

- UTF-8 `.txt` with role-prefixed turns, e.g. `User: ...` / `AI: ...` (also `Human:` / `Assistant:`); multiline messages supported.
- `.json` array of `{ "role": "user" | "assistant", "content": "..." }`, or object with a `messages` array.

Use **Load example** to try a synthetic dialogue. Click a detected signal to inspect the preceding AI turn. Export a UTF-8 CSV for human coding.

## Important methodological limits

This is a **rule-based screening prototype**, not a validated psychological instrument. It cannot establish truth, actual belief, causal influence, or uncritical acceptance. Patterns are deliberately sparse (English/Czech) and may miss indirect signals or flag ordinary politeness. Position changes may be justified. A human annotator should verify every candidate and assess whether an unsupported AI claim was adopted without independent checking. No conversation data are uploaded.

## Suggested validation

Define an annotation codebook; have at least two independent coders label dialogue spans; report agreement (e.g., Cohen's kappa), precision and recall against adjudicated labels; compare with baseline detectors; explicitly separate agreement, persuasion, and uncritical acceptance. Obtain informed consent and remove personal information from study dialogues.
