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
* `docs/signals-api/*.yaml`: Complete OpenAPI 3.0 specification for all 21 Revvity Signals Notebook endpoints.
* `docs/SIGNALS_DEVELOPER_CHEAT_SHEET.md`: Essential code recipes, standard JSON:API 1.0 headers, and common EID formats.
* `docs/Full-Guide-Redraft-v3.html`: Comprehensive reference manual covering Signals tenant architecture, authorization workflows, webhooks, and External Actions.

---

## 3. CRITICAL ARCHITECTURAL CONSTRAINTS

> ⚠️ **DO NOT USE FLASK IN THIS PROJECT:**
> * Older tutorial snippets inside `docs/Full-Guide-Redraft-v3.html` use Flask (`Flask(__name__)`, `@app.route`, Jinja2 templates) solely for historical illustration.
> * **DO NOT copy or generate Flask code for this codebase.**
> * If the user asks to implement a feature described in `Full-Guide-Redraft-v3.html` (e.g. Chemical Compliance Review, External Data Sources, or Usage Metrics):
>   1. Implement any HTTP endpoints as **FastAPI routes** in `backend/app.py`.
>   2. Implement any interactive user interfaces in **Streamlit** (`app_streamlit.py`) or vanilla HTML/JS in `frontend/`.
>   3. Use **Pydantic** models for request/response validation instead of raw `request.form` or `request.args`.
