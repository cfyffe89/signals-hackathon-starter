# Instructions for AI coding assistants (Copilot, Continue, Gemini, Claude, Codex…)

You are pair-programming on the **Revvity Signals EMEA Hackathon 2026 starter**. Teams build prototypes on the Signals REST API in ~5 hours, so correct API usage beats cleverness.

## Stack (don't change it)
- `backend/app.py`: **FastAPI** (port 8000). `app_streamlit.py`: **Streamlit** (port 8501). Add features there.
- `backend/signals_client.py`: the Signals API client. **Every method is live-verified.** Use it first.
- `backend/ai_client.py`: LLM calls (Gemini or an OpenAI-compatible gateway). `backend/context.py`: turns Signals records into prompt text. `backend/knowledge.py`: retrieval over `docs/signals/`.
- RDKit for chemistry. No Flask (the guide tutorials use Flask for brevity; translate to FastAPI/Streamlit).

## Signals API rules (verified against a live tenant)
1. **Never invent endpoints.** Check first: `python docs/signals/scripts/lookup_endpoint.py --system core --grep <word>`. If it isn't in the index, it doesn't exist. Then get its parameters: `… --system core <file.yaml> <METHOD> <path>`.
2. Read `docs/signals/GOTCHAS.md` before writing any raw call. `docs/signals/CHEAT_SHEET.md` maps tasks → client methods → HTTP.
3. Headers: `x-api-key`, `Accept: application/vnd.api+json`. JSON:API bodies (`{"data":{"type","attributes","relationships"}}`) with `Content-Type: application/vnd.api+json` (`application/json` → 415 on `/entities`).
4. List by type with `includeTypes=` (**`filter[type]` is silently ignored**). Search is `POST /entities/search`. Always send `"mode":"keyword"` when matching names/IDs. Use the right `source` (`IVT` for inventory).
5. **Creating:** pass `relationships.ancestors` (the notebook for experiments, the experiment for samples) and `?digest=<parent digest>`. Samples also need a `template`. Without ancestors Signals creates orphans. Use `sc.create_experiment()` / `sc.create_sample()`.
6. Structure search = `$chemsearch` inside `/entities/search` (substructure by default, `"options":"full=true"` for exact). Structures: `GET /entities/{eid}/export?format=smiles|svg|mol`.
7. **External Actions** open *your page in the user's browser* with `?__eid=<eid>`. They're not webhooks. Close the dialog with `window.parent.postMessage(["closeAndContinue",[]], origin)`. See `/action` in `backend/app.py`.
8. External Data Sources and notification webhooks are called server-to-server: use the Codespaces **public** port URL.
9. Two different APIs: core `/api/rest/v1.0` vs Data Factory `/datafactory/api/v1|v2` (`references/guide/data-factory/guide.md`). Say which one you mean.

## AI features in the apps
Ground every answer in data: `experiment_context(sc, eid)` for records, `knowledge_block(question)` for API/integration knowledge, and `ai.ask(question, records=..., knowledge=...)`. Tell the model to cite and to say when the context doesn't contain the answer.

## Secrets & safety
Keys come from `.env` / Codespaces secrets (`SIGNALS_API_KEY`, `GEMINI_API_KEY`, …). Never hard-code or print them, never commit `.env`. Write only into your team notebook (there's no default: pick it with `sc.list_notebooks()` or the Streamlit sidebar, and pass its eid).
