# Signals REST API cheat sheet (verified)
> Every recipe here matches a method in `backend/signals_client.py`, and every method is run against a real tenant by `scripts/smoke_live.py`. **Use the client first**; write raw calls only for what it doesn't cover.
> Traps and why: `GOTCHAS.md`. Any other endpoint: `python docs/signals/scripts/lookup_endpoint.py --system core --grep <word>`.

```python
from backend.signals_client import SignalsClient
sc = SignalsClient()   # reads SIGNALS_BASE_URL, SIGNALS_API_KEY, SIGNALS_NOTEBOOK_EID
```

| Task | Client method | HTTP |
|---|---|---|
| Is my key working? | `sc.check_connection()` | `GET /entities?includeTypes=journal&page[limit]=1` |
| My notebooks | `sc.list_notebooks()` | `GET /entities?includeTypes=journal` |
| Recent experiments | `sc.list_experiments(15)` | `POST /entities/search` `$match type=experiment (keyword)` + sort modifiedAt desc |
| Any entity | `sc.get_entity(eid)` | `GET /entities/{eid}` |
| What's inside an experiment | `sc.list_child_entities(eid)` | `GET /entities/{eid}/children` |
| Create an experiment (in your notebook) | `sc.create_experiment(name, desc)` | `POST /entities?digest=<notebook digest>` + `ancestors` |
| Add a sample | `sc.create_sample(exp_eid, template_eid, {field_id: value})` | `POST /entities?digest=<exp digest>` + `ancestors` + `template` |
| Attach a file / HTML note | `sc.upload_child_attachment(eid, "note.html", b"<p>..</p>", "text/html")` | `POST /entities/{eid}/children/{filename}?digest=` |
| Recent chemical drawings | `sc.list_chemical_drawings(20)` | search `type=chemicalDrawing` + export |
| Structure as SMILES/SVG/mol | `sc.export_entity(eid, "smiles")` | `GET /entities/{eid}/export?format=` |
| Reaction table | `sc.get_stoichiometry(eid)` | `GET /stoichiometry/{eid}` |
| Substructure / exact search | `sc.chemistry_search("c1ccccc1", exact=False)` | search `$chemsearch` |
| Registered materials | `sc.search_materials("benz*")` | search `type=asset` + `$simple` |
| Material libraries | `sc.list_material_libraries()` | `GET /materials/libraries` |
| Inventory containers | `sc.search_containers("FZ7")` | search `source=IVT`, `type=container` |
| Any search | `sc.search_entities(query, options, limit, source)` | `POST /entities/search` |

## Raw call template
```python
import os, requests
BASE = os.environ["SIGNALS_BASE_URL"]           # https://<tenant>/api/rest/v1.0
H = {"x-api-key": os.environ["SIGNALS_API_KEY"], "Accept": "application/vnd.api+json"}
r = requests.get(f"{BASE}/entities", headers=H, params={"includeTypes": "experiment", "page[limit]": 25})
r.raise_for_status(); rows = r.json()["data"]    # each row: row["id"], row["attributes"]["name"|"type"|"digest"]
```

## Search query shapes
```jsonc
{"query": {"$and": [
  {"$match": {"field": "type", "value": "experiment", "mode": "keyword"}},
  {"$match": {"field": "name", "value": "QC-2026-001", "mode": "keyword"}},   // exact name
  {"$simple": {"query": "suzuki*", "operator": "and"}},                        // full text
  {"$gt": {"field": "modifiedAt", "value": "2026-09-01T00:00:00Z", "as": "date"}}
]}, "options": {"sort": {"modifiedAt": "desc"}}}
// numeric tag: {"$gt": {"field": "materials.Molecular Weight", "value": 300, "in": "tags", "as": "double"}}
// structure:   {"$chemsearch": {"molecule": "c1ccccc1", "mime": "chemical/x-daylight-smiles"}}   (+ "options":"full=true" for exact)
```

## External Action page (FastAPI)
```python
from fastapi import Query
from fastapi.responses import HTMLResponse
@app.get("/action", response_class=HTMLResponse)
def action(eid: str = Query(alias="__eid")):   # Signals opens https://<your-app>/action?__eid=experiment:...
    exp = sc.get_entity(eid)
    return f"""<h3>{exp['attributes']['name']}</h3><button onclick="done()">Done</button>
    <script>function done(){{window.parent.postMessage(["closeAndContinue",[]], "*")}}</script>"""
```
In production, restrict `postMessage` to your tenant origin instead of `"*"`.
