# Signals REST API cheat sheet (verified)
> Every recipe here matches a method in `backend/signals_client.py`, and every method is run against a real tenant by `scripts/smoke_live.py`. **Use the client first**; write raw calls only for what it doesn't cover.
> Traps and why: `GOTCHAS.md`. Any other endpoint: `python docs/signals/scripts/lookup_endpoint.py --system core --grep <word>`.

```python
from backend.signals_client import SignalsClient
sc = SignalsClient()   # reads SIGNALS_BASE_URL, SIGNALS_API_KEY (no default notebook: pass notebook eids explicitly)
```

| Task | Client method | HTTP |
|---|---|---|
| Is my key working? | `sc.check_connection()` | `GET /entities?includeTypes=journal&page[limit]=1` |
| My notebooks | `sc.list_notebooks()` | `GET /entities?includeTypes=journal` |
| Recent experiments | `sc.list_experiments(15)` | `POST /entities/search` `$match type=experiment (keyword)` + sort modifiedAt desc |
| Any entity | `sc.get_entity(eid)` | `GET /entities/{eid}` |
| What's inside an experiment | `sc.list_child_entities(eid)` | `GET /entities/{eid}/children` |
| Experiments in a notebook | `sc.list_notebook_experiments(nb)` | `GET /entities/{nb}/children` (type experiment) |
| Create an experiment (in your notebook) | `sc.create_experiment(name, nb, desc)` | `POST /entities?digest=<notebook digest>` + `ancestors` |
| Add a sample | `sc.create_sample(exp_eid, template_eid, {field_id: value})` | `POST /entities?digest=<exp digest>` + `ancestors` + `template` |
| Attach a file / HTML note | `sc.upload_child_attachment(eid, "note.html", b"<p>..</p>", "text/html")` | `POST /entities/{eid}/children/{filename}?digest=` |
| Recent chemical drawings | `sc.list_chemical_drawings(20)` | search `type=chemicalDrawing` + export |
| Structure as SMILES/SVG/mol | `sc.export_entity(eid, "smiles")` | `GET /entities/{eid}/export?format=` |
| Reaction table | `sc.get_stoichiometry(eid)` | `GET /stoichiometry/{eid}` |
| Substructure / exact search | `sc.chemistry_search("c1ccccc1", exact=False)` | search `$chemsearch` |
| Registered materials | `sc.search_materials("benz*")` | search `type=asset` + `$simple` |
| Material libraries | `sc.list_material_libraries()` | `GET /materials/libraries` |
| Inventory containers | `sc.search_containers("FZ7")` | search `source=IVT`, `type=container`, not templates |
| Container by barcode | `sc.find_containers_by_barcode(["0000000014"])` | `POST /inventory/containers/search` (<100 per call) |
| One container | `sc.get_container(id)` | `GET /inventory/containers/{uuid}` |
| Container types | `sc.list_inventory_types("container")` | `GET /inventory/types?entityType=container` |
| New container | `sc.create_container(type_id, loc_id, "batch:…", 5, "g", {field_id: value})` | `POST /inventory/containers` (contents + required fields) |
| Change amount | `sc.update_container_amount(id, "4 g")` | `PATCH /inventory/containers/{uuid}/amount?digest=` |
| Check out / in, dispose | `sc.set_container_status(id, "checkout", owner_user_id="100")` | `POST /inventory/containers/{uuid}/status/{action}?digest=` |
| Plates in an experiment | `sc.create_plate_container(exp_eid, 8, 12, 1)` | `POST /plates?digest=<exp digest>` |
| Fill wells | `sc.set_plate_wells(pc, "Concentration", {"A1": "10 umolar"})` | `PATCH /plates/{pc}/plates/Plate-1?digest=` |
| Plates as CSV | `sc.export_plates_csv(pc)` | `GET /entities/{pc}/export?format=csv` |
| Who am I / which release | `sc.get_current_user()`, `sc.get_version()` | `GET /profiles/me`, `GET /version` |
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
