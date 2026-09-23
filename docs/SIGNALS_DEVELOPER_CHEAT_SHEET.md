# Revvity Signals Notebook REST API — Developer Cheat Sheet & LLM Prompt Reference
*Designed for Frankfurt Signals EMEA Hackathon 2026 participants and AI Copilots*

> ⚠️ **CRITICAL REFERENCE NOTICE FOR DEVELOPERS & AI ASSISTANTS:**
> * `docs/Full-Guide-Redraft-v3.html` is provided in this repository as an authoritative reference for Signals tenant architecture, authorization, webhooks, and External Actions.
> * **DO NOT USE FLASK IN THIS PROJECT:** While older tutorial snippets inside `Full-Guide-Redraft-v3.html` use Flask/Jinja for illustration, our hackathon project stack standardizes on **FastAPI (backend/app.py)** and **Streamlit (app_streamlit.py)** with RDKit and Google GenAI.
> * Always adapt any concepts or workflows from the reference guide to FastAPI endpoints or Streamlit UI components.

---

## 1. Authentication & Core Protocol

### Base URL Pattern:
`	ext
https://<tenant-subdomain>.signalsnotebook.revvitycloud.com/api/rest/v1.0
`

### Standard Headers (JSON:API 1.0):
`python
headers = {
    "x-api-key": os.getenv("SIGNALS_API_KEY"),
    "Content-Type": "application/vnd.api+json",
    "Accept": "application/vnd.api+json"
}
`

> **IMPORTANT:** Signals Notebook adheres strictly to the **JSON:API 1.0** specification. Standard requests and responses wrap payloads inside a top-level "data" dictionary with "type", "attributes", and optional "relationships".

---

## 2. Entity Identifiers (EIDs)

Every object in Signals has an id composed of its type prefix and a UUID:
* experiment:<uuid> — Top-level Experiment Notebook
* journal:<uuid> — Sub-notebook or Section
* 	ext:<uuid> — Rich Text Element
* image:<uuid> — Image Attachment Element
* chemicalDrawing:<uuid> — ChemDraw / Chemical Structure Element
* sample:<uuid> — Physical or virtual chemical/biological sample
* atch:<uuid> — Inventory lot / container batch

---

## 3. The 10 Essential Code Recipes

### Recipe 1: List Accessible Experiments (with Filtering & Pagination)
`python
import requests

url = f"{BASE_URL}/entities"
params = {
    "filter[type]": "experiment",
    "page[limit]": 25,
    "page[offset]": 0
}
res = requests.get(url, headers=headers, params=params)
res.raise_for_status()

experiments = []
for item in res.json().get("data", []):
    experiments.append({
        "eid": item["id"],
        "name": item["attributes"].get("name"),
        "modifiedAt": item["attributes"].get("modifiedAt")
    })
`

---

### Recipe 2: Create a New Experiment
`python
url = f"{BASE_URL}/entities"
payload = {
    "data": {
        "type": "experiment",
        "attributes": {
            "name": "EXP-2026-001: Hackathon Synthesis Pilot",
            "description": "Created via Signals Hackathon Starter API"
        }
    }
}
res = requests.post(url, headers=headers, json=payload)
res.raise_for_status()
new_exp_eid = res.json()["data"]["id"]
`

---

### Recipe 3: Upload Child Attachment (Image / HTML Note / CSV)
> **CRITICAL GOLDEN RULE:** Always append ?force=true to child uploads! This bypasses digest checks and guarantees instant entity creation without 409 conflict errors.
> **Note on Content-Type:** When uploading raw file bytes, pass the file's native MIME type (image/jpeg, 	ext/html, 	ext/csv) rather than pplication/vnd.api+json.

`python
# Uploading a rich text HTML note (Signals Notebook automatically creates an editable Text Element!)
note_filename = "bench_observation_summary.html"
html_content = "<h3>Observation</h3><p>Vial turned clear after heating to 45C.</p>"

url = f"{BASE_URL}/entities/{experiment_eid}/children/{note_filename}?force=true"
upload_headers = {
    "x-api-key": API_KEY,
    "Content-Type": "text/html"
}
res = requests.post(url, headers=upload_headers, data=html_content.encode("utf-8"))
res.raise_for_status()
note_element_eid = res.json()["data"]["id"]
`

---

### Recipe 4: Query Inventory Containers & Batches
`python
url = f"{BASE_URL}/materials/bulk"
params = {
    "filter[query]": "Sodium Hydroxide",
    "page[limit]": 10
}
res = requests.get(url, headers=headers, params=params)
res.raise_for_status()
materials = res.json().get("data", [])
`

---

### Recipe 5: Chemical Structure Substructure & Similarity Search
`python
url = f"{BASE_URL}/chemistry/search"
payload = {
    "data": {
        "type": "chemistrySearch",
        "attributes": {
            "format": "smiles",
            "structure": "c1ccccc1O",
            "searchType": "substructure"  # or 'similarity', 'exact'
        }
    }
}
res = requests.post(url, headers=headers, json=payload)
res.raise_for_status()
hits = res.json().get("data", [])
`

---

### Recipe 6: Register / Create a Sample Entity
`python
url = f"{BASE_URL}/entities"
payload = {
    "data": {
        "type": "sample",
        "attributes": {
            "name": "SAMPLE-4B-TURBID",
            "fields": {
                "Density": {"value": 1.05},
                "Storage Condition": {"value": "Room Temperature"}
            }
        },
        "relationships": {
            "parent": {
                "data": {"type": "experiment", "id": experiment_eid}
            }
        }
    }
}
res = requests.post(url, headers=headers, json=payload)
res.raise_for_status()
sample_eid = res.json()["data"]["id"]
`

---

### Recipe 7: Add Samples to Well Plate (Plates API)
`python
plate_eid = "plate:e323ff17-15c4-4706-9bf3-7f2e12a0004"
url = f"{BASE_URL}/plates/{plate_eid}/wells"
payload = {
    "data": [
        {
            "type": "well",
            "attributes": {
                "coordinate": "A01",
                "sampleId": sample_eid,
                "volume": {"value": 50.0, "unit": "uL"}
            }
        }
    ]
}
res = requests.post(url, headers=headers, json=payload)
res.raise_for_status()
`

---

### Recipe 8: External Action Integration (Custom ELN Action Button)
When a scientist clicks a custom action button in Signals Notebook, Signals sends an inbound webhook to your service:
`python
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/api/external-action")
async def handle_signals_action(request: Request):
    payload = await request.json()
    action_type = payload.get("action")
    entity_eid = payload.get("entity", {}).get("id")
    
    # Process event (e.g., trigger AI calculation, RDKit property generation)
    # ...
    
    # Return response back to Signals
    return {
        "status": "success",
        "message": f"Processed action {action_type} for {entity_eid}"
    }
`

---

### Recipe 9: Fetch Entity Metadata & Attributes
`python
url = f"{BASE_URL}/entities/{entity_eid}"
res = requests.get(url, headers=headers)
res.raise_for_status()
entity_data = res.json()["data"]
name = entity_data["attributes"]["name"]
created_at = entity_data["attributes"]["createdAt"]
`

---

### Recipe 10: Export Experiment as PDF / Archive
`python
url = f"{BASE_URL}/entities/{experiment_eid}/export/pdf"
res = requests.get(url, headers=headers, stream=True)
res.raise_for_status()

with open("experiment_report.pdf", "wb") as f:
    for chunk in res.iter_content(chunk_size=8192):
        f.write(chunk)
`

---

## 4. Top 5 Gotchas to Avoid

| Pitfall | Symptoms | Fix |
| :--- | :--- | :--- |
| **Missing orce=true on child upload** | 409 Conflict or digest mismatch | Append ?force=true to the upload URL: POST /entities/{eid}/children/{filename}?force=true |
| **Wrong Content-Type on JSON:API calls** | 415 Unsupported Media Type | Use "Content-Type": "application/vnd.api+json" for entity operations. |
| **Wrong Content-Type on Child Uploads** | Corrupted images or blank elements | Use the actual file MIME type: "image/jpeg" for .jpg, "text/html" for .html. |
| **Missing data root envelope** | 400 Bad Request: Missing 'data' | Always wrap post payloads in {"data": {"type": "...", "attributes": {...}}}. |
| **Rate Limit / Concurrent Uploads** | 429 Too Many Requests | Add standard exponential backoff or serialize uploads sequentially per experiment. |

---

## 5. OpenAPI YAML Index Map
All 21 OpenAPI specifications are located in docs/signals-api/:
* entities.yaml — Experiments, sub-notebooks, text/image elements, and tree structure
* materials.yaml — Chemicals, reagents, biological samples, containers, and lots
* inventory.yaml — Storage locations, inventory bars, barcodes, and checkouts
* chemistry.yaml — Structures, SMILES, ChemDraw drawings, stoichiometry
* plates.yaml — 96/384-well plates, layouts, well coordinates, and assay data
* parallelExperiments.yaml — Multi-variable DOE experimentation grids
* cro.yaml — Contract research organization workflows and submissions
* dt.yaml — Assay data management tables and curve fitting
