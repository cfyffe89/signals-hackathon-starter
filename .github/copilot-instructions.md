# Signals Hackathon Starter — AI Copilot & Assistant Guidelines

## 1. Project Technology Stack
This repository is pre-configured with a modern Python 3.11+ full-stack architecture:
* **Backend API:** **FastAPI** (`backend/app.py`), Uvicorn, Pydantic v2.
* **Interactive UI & Chemoinformatics:** **Streamlit** (`app_streamlit.py` on Port 8501).
* **Cheminformatics Engine:** **RDKit** (`rdkit.Chem`, `rdkit.Chem.Draw`, `rdkit.Chem.Descriptors`).
* **Signals Client:** Custom JSON:API 1.0 client (`backend/signals_client.py`).
* **AI & LLM Integration:** Google GenAI / Gemini 3.6 Flash (`backend/ai_client.py`).
* **Lightweight Alternative Frontend:** Vanilla HTML/JS (`frontend/app.js`, `frontend/index.html`) served statically by FastAPI.

---

## 2. Reference Documentation in `docs/`
* `docs/API_CATALOG.md`: Single-file master directory of all 425 exact endpoints, parameters, and payloads.
* `docs/signals-api/*.yaml`: Complete OpenAPI 3.0 specification for all 21 Revvity Signals Notebook endpoints.
* `docs/SIGNALS_DEVELOPER_CHEAT_SHEET.md`: Essential code recipes, standard JSON:API 1.0 headers, and common EID formats.
* `docs/guide/*.md`: 7 modular Markdown chapters covering tenant architecture, auth, chemistry, and webhooks.

---

## 3. STRICT SIGNALS REST API GROUNDING (ZERO GUESSING / ZERO HALLUCINATIONS)

> 🛑 **MANDATORY GROUNDING DIRECTIVE — NEVER GUESS SIGNALS API ENDPOINTS:**
> * Revvity Signals Notebook uses a strict proprietary REST API compliant with **JSON:API 1.0**.
> * **DO NOT guess, invent, or extrapolate endpoints** (e.g. NEVER generate `/api/experiments`, `/drawings`, `/reactions`, or `/inventory/reagents` unless verified).
> * **ONLY use exact endpoints documented in `docs/API_CATALOG.md` and the 21 OpenAPI YAML specs in `docs/signals-api/`**.
> * **Before generating ANY Signals API call, verify:**
>   1. The exact HTTP Method and Path in `docs/API_CATALOG.md` (e.g. `GET /materials/{assetBatchId}/drawing` or `GET /entities?filter[type]=experiment`).
>   2. Check `backend/signals_client.py` FIRST — high-frequency operations (`get_chemical_drawing`, `get_stoichiometry`, `create_experiment`, `search_materials`, `upload_child_attachment`) already have pre-tested, verified helper methods!
>   3. The exact query parameter names (e.g. `filter[type]=...`, `page[limit]=...`, `format=smiles`).
>   4. The exact payload structure: JSON:API operations MUST be wrapped in `{"data": {"type": "<entity_type>", "attributes": {...}}}`.
>   5. Child element uploads (attachments, HTML notes, images) MUST include `?force=true` on the URL.


### Verified Signals Endpoint Mapping Table (Never Guess Endpoints)
| Desired Operation | INCORRECT Guess (DO NOT USE) | EXACT Signals Endpoint (USE THIS) | Spec Source |
| :--- | :--- | :--- | :--- |
| **List Experiments** | `GET /api/experiments` | `GET /entities?filter[type]=experiment` | `entities.yaml` |
| **Get Experiment Details** | `GET /api/experiments/{id}` | `GET /entities/{id}` | `entities.yaml` |
| **Create Experiment** | `POST /api/experiments` | `POST /entities` (`type: experiment`) | `entities.yaml` |
| **Chemical Drawing** | `GET /api/drawings/{id}` | `GET /materials/{assetBatchId}/drawing?format=smiles` | `materials.yaml` |
| **Reaction Stoichiometry**| `GET /api/reactions/{id}` | `GET /stoichiometry/{eid}` | `stoichiometry.yaml` |
| **Search Reagents / Lots**| `GET /api/inventory/search` | `GET /materials/bulk?filter[query]={query}` | `materials.yaml` |
| **List Child Entities** | `GET /api/experiments/{id}/items` | `GET /entities/{parentEid}/children` | `entities.yaml` |
| **Upload Child Attachment**| `POST /api/upload` | `POST /entities/{parentEid}/children/{filename}?force=true` | `entities.yaml` |
| **Well Plates & Wells** | `GET /api/plates/{id}` | `GET /plates/{id}/wells` | `plates.yaml` |
| **Chemical Search** | `POST /api/chemistry` | `POST /chemistry/search` | `chemistry.yaml` |


---

## 4. CRITICAL ARCHITECTURAL CONSTRAINTS

> ⚠️ **DO NOT USE FLASK IN THIS PROJECT:**
> * Older tutorial snippets inside `docs/Full-Guide-Redraft-v3.html` use Flask (`Flask(__name__)`, `@app.route`, Jinja2 templates) solely for historical illustration.
> * **DO NOT copy or generate Flask code for this codebase.**
> * If the user asks to implement a feature described in the guide:
>   1. Implement any HTTP endpoints as **FastAPI routes** in `backend/app.py`.
>   2. Implement any interactive user interfaces in **Streamlit** (`app_streamlit.py`) or vanilla HTML/JS in `frontend/`.
>   3. Use **Pydantic** models for request/response validation instead of raw `request.form` or `request.args`.
