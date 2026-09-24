# Signals API: verified gotchas
> Behaviour **verified against a live Signals tenant** (Sept 2026). Where the published guide or spec disagrees, trust this file. Each item: the trap → what to do.

## Requests & media types
- `GET` with `Accept: application/json` → **406**. Send `Accept: application/vnd.api+json` (or `*/*`).
- `POST /entities` with `Content-Type: application/json` → **415**. Use `application/vnd.api+json`. (`POST /entities/search` accepts either.)
- Payloads are JSON:API: `{"data": {"type": "...", "attributes": {...}, "relationships": {...}}}`.
- Base path `/api/rest/v1.0`. Auth: the `x-api-key` header, or an OAuth bearer token (Auth Code + PKCE or Implicit). The request runs **as the key's user** (their permissions).
- `GET /users/me` doesn't exist (400). There's no endpoint that returns the release version.
- `curl`: add `-g` / `--globoff` when a URL has `page[limit]` (otherwise the shell eats the brackets).

## Creating & editing
- **Create inside a notebook:** `POST /entities?digest=<NOTEBOOK digest>` with `relationships.ancestors = {"data":[{"type":"journal","id":"journal:..."}]}`. Without ancestors, Signals returns 201 and creates an **orphan experiment in no notebook**. Ancestors without a digest → 400.
- Creating a child **changes the parent's digest**. Re-read it before each create in a loop.
- Names are unique **per notebook and type** (same name in the same notebook → 409). A name isn't a global key.
- `PATCH /entities/{eid}/properties` (**PUT → 404**).
- **Samples:** `POST /entities?digest=<experiment digest>`, type `sample`, `ancestors` = the experiment, `relationships.template` = a sample template (`sample:...`), `attributes.fields` = a **list** `[{"id":"<field id>","content":{"value":...}}]`. The samples table is auto-created. `relationships.parent` → 400.
- **Uploads:** `POST /entities/{eid}/children/{filename}?digest=<parent digest>` with the file's own MIME type (`text/html` → an editable text element). `?force=true` instead of a digest also works (it skips the concurrency check and allows duplicate names). Neither → 400.
- **Delete is soft:** `DELETE /entities/{eid}?digest=` or `?force=true` → 204, the entity gets `flags.isTrashed: true`, and it's still readable. Wrong digest → 428. Deleting it again → 403.
- **Tasks:** `POST /entities?digest=<experiment digest>`, type `task`, `ancestors` = the experiment (the task container is found for you), `relationships.template` = a task template, `attributes.fields` = `[{"id":"<field id>","content":{...}}]`. Field ids: `GET /tasks/{template eid}/properties` (e.g. `Required By` = `{"value":"2026-10-21T09:00:00.000Z"}`). `Experiment Link` is system-managed (400 "not editable"); to point at another entity use `Reference ID` = `{"values":[{"eid":"experiment:..."}]}`.
- **Text elements:** the upload filename becomes the element name. `Procedure` (no extension) reads better than `Procedure.html`.
- Sample `Amount` accepts only the units the template's field allows (on one tenant, mass only: `"150 g"` works, `"100 item"` / `"1 mL"` → 400 "Wrong input value").

## Listing & search (`POST /entities/search`)
- **List by type:** `GET /entities?includeTypes=experiment`. ⚠️ `filter[type]=` is **silently ignored** (returns every type).
- `includeOptions=shared` always returns nothing. Use `mine` / `other`, or check `/entities/{eid}/shares`.
- ⚠️ `$match` **tokenizes** the value unless you send `"mode":"keyword"`. `"QC-2026-001"` also matches everything containing "2026". Always use keyword mode for names and IDs.
- `$prefix` needs `"mode":"keyword"` for multi-word prefixes (otherwise it matches token prefixes).
- ⚠️ The wrong `source` returns **0 with no error**: notebook = `SN` (default), inventory containers/locations = `IVT`, also `CHEMICALS`, `CONNECTED` (archive).
- Tag fields need `"in":"tags"` + `"as"`. **Numeric tags need `"as":"double"`**, and the wrong `as` returns 0 with no error. Discover the indexed types with **`POST /entities/search/tags`** and a scoping query (GET → 404; an empty body → 504).
- `$not` takes an **array**. `$simple` = full text (a trailing `*` works). `$semantic` = vector search. `$child` / `$parent` = traverse.
- **Structure search:** `{"$chemsearch":{"molecule":"<smiles>","mime":"chemical/x-daylight-smiles"}}` = **substructure**. Add `"options":"full=true"` for exact. (`"options":"substructure"` → 400. There's no `/chemistry/search`.)
- Paging: `page[limit]` ≤ 100, `page[offset]` ≤ 5000 (both hard 400). To go beyond, **keyset-page** on `createdAt` (`$gt`, sorted ascending).
- For incremental sync, use `$gt modifiedAt` or `GET /entities?includeOptions=nontemplate&start=<ISO>`. Modification times cascade from children.
- **Tag fields** (e.g. `materials.Chemical Name`, `fields.Barcode`): `{"$match":{"field":"materials.Chemical Name","value":"Toluene","in":"tags","as":"text","mode":"keyword"}}`. `"as":"string"` → 400. A material's `name` is its **material ID** (`Reagents-005`), not the chemical name.
- `source=IVT` results also include the location and container **types** (`isTemplate: true`). Add `{"$match":{"field":"isTemplate","value":false}}`.

## Chemistry & materials
- Structure of a notebook element: `GET /entities/{eid}/export?format=smiles|svg|mol|mol-v3000|cdxml|inchi`. Of a registered material: `GET /materials/{id}/drawing?format=...`. Stoichiometry: `GET /stoichiometry/{eid}`.
- Materials search: `$match type = asset` (materials) or `batch`. Libraries: `GET /materials/libraries`.
- `POST /materials/{lib}/assets` accepts SMILES / InChI / CDXML / HELM, **not molfile** (400). For MOL V3000, use a bulkImport ZIP with an SDF, or upload the `.mol` to an experiment and export it as CDXML.
- `bulkImport`: no record-count cap, 300 MiB body limit. `bulkExport`: 25,000 assets / 100 MB per file (continue via `nextExport`).
- **Build a reaction with a stoichiometry table:** upload a blank CDXML as a child (`chemical/x-cdxml`) → `POST /chemicaldrawings/{eid}/reaction/reactants` (and `/products`) with `{"data":{"attributes":{"dataType":"smiles","data":"<smiles>"}}}` → `PATCH /stoichiometry/{eid}/{row_id}` with `{"data":{"attributes":{"values":{"eq":"1.2"}}}}` or `{"values":{"sm":"1.82 g","limit":{"value":true}}}` (moles and the other masses are calculated) → `POST /stoichiometry/{eid}/solvents` with `{"values":{"solvent":"Toluene","volume":"40 mL"}}`. An uploaded `.rxn` file becomes a drawing whose stoichiometry table is **empty** and can't be updated (403).
- Inventory write endpoints take the bare UUID (`location:<uuid>:ivt` from search → `<uuid>`). Locations have no DELETE; containers can only be disposed.

## Bulk export & async jobs
- `POST /entities/export/bulk?eid=...&depth=0|1|-1` (**`depth` is required**) → 202 job → poll `GET …/{jobId}` → `GET …/{jobId}/contents` (multipart/mixed). **The download is one-shot**: it's purged seconds after the first GET.
- Part 1 is a JSON "table of content". Resolve parts by `content.part`, and don't construct part names yourself.
- 429 = no free export worker. Retry after a short backoff, and keep roughly 4–8 jobs in flight.

## External integrations
- **External Actions** open **your URL in the user's browser** (dialog or new window) with `?__eid=<eid>` (GET, default parameter name) or the entity object in a POST body. Your page calls the API, then closes with `window.parent.postMessage(["closeAndContinue",[]], "https://<tenant>")` (also `close`, `closeAndAbort`, `setTitle`, `setWidth`). They're not server webhooks, so `localhost` works for them.
- **External Data / Chemical Sources** are called **server-to-server** by Signals, so they need a public HTTPS URL (Codespaces public port or a Cloudflare tunnel). The URL placeholders are `{id}`, `{username}`, `{user_alias}` (not for Lists).
- Data Sources accept **nested JSON**: leaves are flattened to paths like `a.b[0].c`. Types are strict: Number strips leading zeros (map IDs as Text), Checkbox needs a real boolean, Date/Time needs a time component.
- External Lists: `GET → {"data":[...]}`. The refresh schedule (Hourly/Daily/Never) is set on the **List attribute**.
- **Notifications (polling):** `GET /notifications?status=dismissed,notdismissed` (new events can arrive already dismissed). Material create fires `create` on both asset and batch. A signed close is `close`, an unsigned one `close_without_signing`.

## Data Factory (SDF) API (`/datafactory/api/v1|v2`)
- A bad or missing `x-api-key` → **401 as plain HTML** (not JSON).
- `filters.attributes` is exact-match. Non-indexed keys → 400. On 2.0 projects filter `Row ID` with the **suffixed** value (`…-m1-v0`).
- The search endpoints use cursor paging: follow `links.next`, but **re-append `publication-from/to-date`** on each page.
- Writes are async: `202 {publicationId}` → poll `GET /api/v2/projects/publication/status/{id}`. A row PUT body must include the identity columns.
- CSV upload has no row limit, but a ~30 s total request limit. SD files aren't supported (load structures via an entity map + `format`).
