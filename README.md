# ⚡ Revvity Signals EMEA Hackathon 2026 — Universal Starter Hub

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/cfyffe89/signals-hackathon-starter)

Welcome to the official developer starter template for the **Frankfurt Signals EMEA Hackathon 2026**. This repository gives every participant an immediate, pre-configured cloud development environment with zero local setup.

---

## 🚀 60-Second Quickstart

1. **Launch a Codespace:** Click the green **Open in GitHub Codespaces** button above (or open `https://codespaces.new/cfyffe89/signals-hackathon-starter`).
2. **Auto-Bootstrap:** Codespaces will automatically:
   * Boot Python 3.11 inside a Linux devcontainer.
   * Pre-install all scientific, chemistry, web, and AI dependencies.
   * Pre-configure the **Continue.dev** in-editor AI Copilot.
   * Forward Port 8000 (Public) and launch the interactive Developer Dashboard.
3. **Configure Your Team Credentials:**
   * Open `.env` and fill in your team credentials:
     ```env
     SIGNALS_BASE_URL=https://hackathon.signalsnotebook.revvitycloud.com/api/rest/v1.0
     SIGNALS_API_KEY=your-signals-api-key
     GEMINI_API_KEY=your-gemini-api-key
     # Or central hackathon gateway:
     AI_GATEWAY_URL=https://signals-ai.revvity-hackathon.com/v1
     AI_GATEWAY_KEY=your-team-gateway-key
     AI_MODEL=gemini-3.5-flash
     ```
   * *Offline / Testing mode:* If keys are not yet configured, the environment automatically runs in **Mock Simulation Mode** so your team is never blocked.

---

## 🤖 In-Editor AI Coding Copilot (Continue.dev + Gemini Flash)

This Codespace is pre-configured with the **Continue.dev** VS Code extension connected to **Gemini 3.5 Flash** (via direct key or the Hackathon AI Gateway).

| Shortcut | Feature | Usage |
| :--- | :--- | :--- |
| **Ctrl+L** (or Cmd+L) | **AI Chat Sidebar** | Ask questions about Signals API endpoints, RDKit functions, or debug stack traces. |
| **Ctrl+I** (or Cmd+I) | **Inline Code Generator** | Highlight any block of code and press Ctrl+I to refactor, write tests, or generate functions. |
| **/signals** | **Custom Signals Prompt** | In the chat, type `/signals <what you want to build>` to generate code referencing the 21 OpenAPI specs. |

---

## 📦 What's Pre-Installed?

Your environment comes with all packages pre-installed for every hackathon track:

* **Web & APIs:** `fastapi`, `uvicorn[standard]`, `requests`, `httpx`, `pydantic`, `jinja2`, `python-dotenv`
* **Rapid UI & Dashboards:** `streamlit`
* **Chemistry & Cheminformatics:** `rdkit-pypi`
* **Bioinformatics:** `biopython`
* **Data Science & Analytics:** `pandas`, `numpy`, `openpyxl` (Excel), `scipy`, `matplotlib`
* **AI & Multimodal:** `openai`, `google-genai`, `pillow`
* **Testing:** `pytest`, `black`

---

## 📚 Signals API Documentation & Cheat Sheets

* **21 Modular OpenAPI Specifications:** Located in [docs/signals-api/](docs/signals-api/) covering entities, materials, inventory, chemistry, plates, stoichiometry, parallelExperiments, and more.
* **[SIGNALS_DEVELOPER_CHEAT_SHEET.md](docs/SIGNALS_DEVELOPER_CHEAT_SHEET.md):** High-density guide containing the top 10 practical copy-pasteable REST recipes and common gotchas.

### 🌟 The Golden Rule for Child Uploads:
When uploading images, rich text HTML notes, or attachments to an experiment, **always append `?force=true`**:
```http
POST /entities/{experiment_eid}/children/{filename}?force=true
```
This avoids 409 conflict and digest mismatch errors during rapid uploads!

---

## 🛠️ Project Track Blueprints

### Track 1: Fast Web / Mobile PWA
```bash
# Start FastAPI backend & static PWA server on port 8000
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

### Track 2: Streamlit Data & Analytics Dashboard
```bash
# Launch interactive Streamlit dashboard on port 8501
streamlit run your_dashboard.py --server.port 8501 --server.address 0.0.0.0
```

### Track 3: Chemistry & RDKit Automation
```python
from rdkit import Chem
from rdkit.Chem import Descriptors
from backend.signals_client import SignalsClient

sc = SignalsClient()
# Connect to Signals, fetch chemical structures, and compute properties
```

---

## 🧪 Testing Your Environment

Run the automated verification suite anytime:
```bash
python test_starter_environment.py
```
