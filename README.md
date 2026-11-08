# Haq

Haq is a polished Streamlit prototype for organising everyday legal problems in India. It helps a user build a case file, review evidence, identify contradictions, prepare factual documents, understand possible official routes, handle replies, track follow-ups, and prepare a professional handoff.

Haq is a legal-information and case-organisation tool. It does not act as a lawyer, calculate legal deadlines, decide eligibility, file complaints, contact another party, or guarantee an outcome.

## Run locally

The project already has a local virtual environment in this workspace. Start the app with:

```bash
./run.sh
```

Then open <http://127.0.0.1:8501>.

For a fresh checkout:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
./run.sh
```

Add the Gemini key only to `.streamlit/secrets.toml`. That file is ignored by Git. Never commit it.

## Change the model

The interface depends on `ModelClient`, not directly on Gemini. Change the configured model from the **Settings** page or update `MODEL_NAME` in `.streamlit/secrets.toml`.

Two provider adapters are supported:

- `gemini`: Gemini REST API, including structured JSON and image/audio inputs.
- `compatible`: an OpenAI-compatible HTTPS endpoint for text and extracted-text inputs. Configure `MODEL_BASE_URL`, `MODEL_API_KEY`, and `MODEL_NAME`.

Provider code is isolated in `haq/provider.py`, so another provider can be added without changing the case, evidence, document, or interface layers.

## Product capabilities

- English, Hindi, and Hinglish case intake by text or voice.
- Editable transcript with confirmation of critical facts.
- Structured facts labelled user-reported, source-supported, disputed, or unknown.
- Evidence library for PDFs, images, and text with duplicate detection and original-file retention.
- Contradiction and evidence-gap analysis.
- Curated official route cards for consumer, banking, cyber-fraud, Tele-Law, and legal-aid navigation.
- Versioned document studio with factual offline templates and AI-assisted drafts.
- Reply, filing-correction, notice, settlement, roleplay, and fulfilment workflows.
- User-created reminders with private `.ics` exports.
- DOCX, text, and searchable PDF exports with Hindi font support.
- Encrypted portable `.haq` backups; no application database is used.
- Session-level model switching and request throttling.
- Consent gate and best-effort identifier masking before model calls.

## Privacy and operating limits

Case data is kept in the Streamlit session and can disappear when the browser refreshes, disconnects, or the server restarts. Users should download an encrypted `.haq` backup. Original files are retained only when the user chooses that option.

AI processing sends selected context to the configured provider. Text masking is best-effort and does not guarantee anonymity. Images and audio cannot be automatically masked. Provider terms and retention policies apply, and the interaction should not be assumed to have legal professional privilege.

Curated source summaries are navigation aids, not a complete legal database. Their `checked` dates are displayed in the product. A production release needs a legal-review and source-update process.

## Tests

Run:

```bash
.venv/bin/python -m pytest -q
```

The suite covers case creation, evidence provenance, duplicate handling, encrypted backups, identifier masking, urgent routing, Hindi PDF/DOCX generation, safe provider validation, session model switching, draft persistence, no-AI fallbacks, and resolution safeguards.

The project also includes optional scripts:

- `scripts/check_model.py`: one small live structured-output check.
- `scripts/evaluate.py`: three synthetic model checks saved under `output/test-results/`.
- `scripts/diagnose_model.py`: model discovery and API diagnostics with the key redacted from output.

These scripts consume provider quota and are not required to run the application.

