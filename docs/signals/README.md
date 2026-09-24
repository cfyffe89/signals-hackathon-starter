# Signals knowledge pack
> For people **and** for the AI (the in-editor copilot, and the apps' "Ask" feature). Read top-down and stop when you have the answer.

| Need | Open |
|---|---|
| A working call, fast | `CHEAT_SHEET.md` (+ `backend/signals_client.py`) |
| "Why does this return 0 / 406 / 415 / 428 / an orphan?" | `GOTCHAS.md` (live-verified; wins over everything else) |
| How a concept works (auth, REST conventions, search, External Actions, notifications, Data Sources, workflows) | `references/guide/core/01…07-*.md` |
| Worked tutorials (External Lists, chemical drawings, metrics dashboard) | `references/guide/core/08…10-*.md`. The tutorial code uses Flask for brevity; **in this repo write FastAPI/Streamlit** |
| Data Factory (SDF) API | `references/guide/data-factory/guide.md` |
| Does endpoint X exist? Its parameters/body? | `python docs/signals/scripts/lookup_endpoint.py --system core --grep <word>` then `… --system core <file> <METHOD> <path>` (or the index files `references/endpoint-index-*.md`) |
| Raw OpenAPI | `spec/core/*.yaml`, `spec/data-factory/sdf-openapi.yaml`. Large: use the lookup script instead of opening them |

Rules of thumb: never invent endpoints; if `lookup_endpoint.py --grep` doesn't find it, it doesn't exist. The two APIs (core `/api/rest/v1.0` vs Data Factory `/datafactory/api/v1|v2`) have different conventions, so say which one you mean.
