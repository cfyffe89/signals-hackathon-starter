# Revvity Signals EMEA Hackathon 2026: starter

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/cfyffe89/signals-hackathon-starter)

A ready-to-hack Codespace with **two working apps** on the Signals REST API, **AI grounded in your Signals data**, and a **Signals knowledge pack** that your AI copilot and your apps both use.

## 1. Start (2 minutes)
1. Click **Open in GitHub Codespaces**. Dependencies install and both apps start automatically.
2. Add your team credentials, either as **one Codespaces secret named `HACKATHON`** (paste the lines from your table sheet) or by copying `.env.example` to `.env` and filling it in:
   ```
   SIGNALS_BASE_URL=https://<your-tenant>/api/rest/v1.0
   SIGNALS_API_KEY=...
   SIGNALS_NOTEBOOK_EID=journal:...       # your team notebook: experiments are created here
   GEMINI_API_KEY=...                     # or AI_GATEWAY_URL + AI_GATEWAY_KEY
   ```
3. Restart the apps: `./scripts/start.sh`, then check everything: `python scripts/check_setup.py`.

No keys yet? Everything runs in **mock mode** with sample data, so you can start building straight away.

| App | Port | What it shows |
|---|---|---|
| **Streamlit** `app_streamlit.py` | 8501 | Experiments (read one, see exactly what the AI reads, ask about it) · Chemistry (drawings, reaction breakdown with RDKit, substructure search) · Materials · **Ask the Signals expert** (API/integration Q&A) |
| **FastAPI** `backend/app.py` | 8000 | JSON API (`/docs`), a small web page, `/api/ask` (grounded AI), and a working **External Action** at `/action` |

## 2. How it fits together
```
backend/signals_client.py   Signals REST client. Every method is live-verified (scripts/smoke_live.py)
backend/context.py          Signals records -> prompt text (text as HTML->text, tables as CSV, drawings as SMILES)
backend/knowledge.py        retrieval over docs/signals (guides, gotchas, endpoint index)
backend/ai_client.py        Gemini or OpenAI-compatible gateway; ai.ask(question, records=, knowledge=)
backend/app.py              FastAPI routes           app_streamlit.py   Streamlit UI
docs/signals/               the knowledge pack (see docs/signals/README.md)
AGENTS.md                   rules for AI assistants (mirrored in .github/copilot-instructions.md)
```
Typical AI feature (3 lines):
```python
ctx = experiment_context(sc, eid)                       # what's in the experiment
kb  = knowledge_block("how do I add a sample?")         # verified API knowledge
ai.ask("Suggest the next experiment and how to create it via the API", records=ctx["text"], knowledge=kb)
```

## 3. Signals API essentials
- Use `SignalsClient` first. The task → method → HTTP map is in **`docs/signals/CHEAT_SHEET.md`**.
- Before any raw call, read **`docs/signals/GOTCHAS.md`** (media types, `includeTypes` not `filter[type]`, keyword search, creating with ancestors + digest, `source=IVT`, `$chemsearch`...).
- Does an endpoint exist? `python docs/signals/scripts/lookup_endpoint.py --system core --grep <word>`. If it isn't there, it doesn't exist.
- Concepts and tutorials: `docs/signals/references/guide/core/` (REST, search, External Actions, notifications, Data Sources, workflows). The Data Factory API guide is in `…/guide/data-factory/`.

## 4. AI copilot in the editor
Continue (Ctrl+L chat, Ctrl+I inline edit) is configured from your `.env` (`python scripts/setup_continue.py`). Slash prompts:
`/signals` (write API code) · `/signals-endpoint` (find the exact endpoint) · `/signals-action` (External Action page) · `/signals-drawing` (chemistry + RDKit) · `/signals-ai` (add a grounded AI feature). GitHub Copilot and other agents read `AGENTS.md`.

## 5. Integrations from a Codespace
- **External Actions** open your page in the user's browser. Register `https://<codespace>-8000.app.github.dev/action` (GET, parameter `__eid`, open in a dialog).
- **External Data Sources / webhooks** are called by Signals' servers, so set port 8000 to **Public** (it is by default here).

## 6. Rules
Write only into your team notebook. Never commit `.env` or keys. Record a 60-second screencast of your working prototype before judging.
