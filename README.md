# HAIR Alpha — Human–AI Interaction Research

A small Streamlit application for **exploratory** research on communication patterns in human–AI dialogues. The project is independent of other research codebases.

## Installation and launch

Requires Python 3.10+ and internet access for Groq analysis.

### Run in GitHub Codespaces

```bash
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py --server.address 0.0.0.0
```

Open the forwarded **8501** port in the browser. No desktop GUI / DISPLAY is needed.

### Run locally (macOS, Linux, Windows)

Open a terminal in the repository folder, then:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

On Windows PowerShell use `.venv\Scripts\Activate.ps1` instead of `source .venv/bin/activate`, and use `python` if `python3` is unavailable. Streamlit will display a local URL (usually http://localhost:8501). The GUI is browser-based; do not use `python3 app.py`.

## Groq free API

1. Obtain a key from https://console.groq.com/keys (check current free-tier terms).
2. In the sidebar, enable **Groq AI analysis** and paste the key in the password field, or create a **Codespaces secret** named `GROQ_API_KEY` and restart the Codespace.
3. Click **Run AI analysis**. Model default: `openai/gpt-oss-20b`; availability and limits may change.

**API keys are not included in this distribution.** Each researcher must obtain their own Groq key. Never commit a token. Do not paste it into source code, README, terminal commands that will be committed, or screenshots. API usage sends the selected dialogue to Groq; anonymize and obtain appropriate consent first.

### Automatic rate-limit waiting

When Groq returns HTTP **429**, HAIR checks the server `Retry-After` header, then the retry hint in the response, and otherwise uses a bounded backoff. The app displays a notice below **Run AI analysis**, waits, and retries automatically (up to 8 retries per window). For very long waits (over two minutes), exhausted daily quotas, or repeated failures, it stops with an explanation; it never upgrades your plan or initiates payment. Limits are organization-wide and may change; see https://console.groq.com/docs/rate-limits.

If a multi-window analysis fails, the app does not yet persist completed windows across a restart; retrying starts the analysis again. Do not run multiple analyses concurrently against the same key if you want to minimize rate-limit errors.

## Input

Paste a dialogue or upload UTF-8 TXT/JSON. Use exact speaker prefixes `User:` and `AI:` (also supports common variants). Multi-line messages are supported. JSON input accepts an array of `{ "role": "user" | "assistant", "content": "..." }` or `{ "messages": [...] }`.

Use **verbatim** transcripts, not AI summaries, for research analysis. AI-created exports may omit turns or paraphrase evidence.

Example TXT:

```text
User: I doubt this conclusion. What is the evidence?
AI: Several studies support it.
User: Can you cite those studies?
AI: I cannot provide a reliable citation.
```

Speaker labels must start each message; subsequent lines belong to the same message until the next label. The app does not automatically infer speakers from unlabelled text. Export transcripts with exact wording where possible.

## What the application does

1. Parses the dialogue into numbered User/AI turns and offers a normalized TXT download.
2. Runs a local lexical baseline and exports its findings as JSON.
3. Optionally sends overlapping context windows to Groq for cautious, evidence-grounded candidate annotations (not psychological diagnoses).
4. Verifies that model evidence quotations occur in the cited turns; discards unverifiable events.
5. Allows a researcher to mark candidate events as supported, rejected, or uncertain and export CSV/JSON.

## Outputs

- Local rule-based baseline (comparison only)
- Contextual Groq annotations with mechanisms, quoted evidence, alternative explanations, and evidence strength
- Evidence quote validation against original turn, rejection of unverifiable quotes
- Multi-window processing for longer conversations, with overlap
- Researcher review (`supported`, `rejected`, `uncertain`) and CSV/JSON exports

## Methodological caution

A model cannot infer actual submissiveness or prove persuasion from text alone. The tool identifies **candidate observable patterns** such as critical checking, AI sycophancy, epistemic delegation, and possible uncritical adoption. Agreement is not automatically uncritical adoption. A single model's `evidence_strength` is a qualitative judgment, **not** a calibrated probability. Long conversations are analyzed in windows, so findings can vary with segmentation. Establish reliability using independent human annotation, clear codebooks, and agreement measures.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Suggested final commit

After replacing `app.py`, `analyzer.py`, and `README.md` in your repository:

```bash
python3 -m unittest discover -s tests -v
git status
git add app.py analyzer.py README.md tests
git commit -m "HAIR alpha: automatic Groq rate-limit retries and setup documentation"
git push origin main
```

Only commit test fixtures that contain synthetic or appropriately anonymized dialogue.

### Groq JSON output limit (HTTP 400)

If Groq returns `json_validate_failed` because the completion-token budget was exhausted, HAIR automatically retries with smaller dialogue windows (bounded recursion). It also asks for concise JSON and sets an explicit completion-token budget. This can consume additional API requests and may trigger the free-tier 429 waiting mechanism. Extremely long individual messages may still need manual shortening.
