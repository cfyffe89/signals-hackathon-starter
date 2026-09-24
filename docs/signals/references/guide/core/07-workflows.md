# Example Concepts & Workflows

Five worked recipes that combine the integration surfaces into real solutions. Each shows the components, the endpoints, and the steps — ready to adapt.

## Before you begin

Every recipe below assumes the API base URL `https://<your-tenant>/api/rest/v1.0` and an authenticated request — an `x-api-key` header for server-to-server flows, or a bearer token for user-driven ones (see REST API → Authentication). Remember that create and update calls appear in the audit log as the user the credential belongs to.

### The recipes at a glance

Recipe| Components| Key endpoints  
---|---|---  
User management| REST API| GET/POST /users  
Create & update an experiment| REST API| POST /entities?digest=<parent> · PATCH /entities/{eid}/properties  
Sample registration| External Action · REST API| GET/PATCH /samples/{id}/properties  
Automated archival| Notifications · REST API| PUT/HEAD/GET /entities/export/pdf  
Signing compliance| External Action · REST API| GET /entities/{eid}/children  
Bulk-export an experiment| REST API · async job| POST /entities/export/bulk  
  
## 1 · User management

REST APIGET /usersPOST /users

List users, create one, and confirm. Roles come back as relationships; grab the role `id` you need from `GET /roles` (or a prior `GET /users`).

#### List users
    
    
    GET /users?enabled=true&page[offset]=0&page[limit]=20
    
    // trimmed — each user has attributes + a "roles" relationship
    { "data": [ { "type": "user", "id": "100",
        "attributes": { "email": "ross.geller@example.com", "firstName": "Ross", "isEnabled": true },
        "relationships": { "roles": { "data": [ { "type": "role", "id": "3" } ] } } } ] }

#### Create a standard user
    
    
    POST /users
    { "data": { "attributes": {
        "firstName": "Rachel", "lastName": "Green",
        "emailAddress": "rachel.green@example.com",
        "country": "USA", "organization": "example",
        "roles": [ { "id": "3", "name": "Standard User" } ]
    } } }   // 201 → the new user, id 101

Re-run `GET /users` to confirm; the full response lists every user with their roles resolved in `included`.

## 2 · Create an experiment & update its properties

REST APIPOST /entitiesPATCH /entities/{eid}/properties

Create an experiment inside a notebook, then set a property — capturing the `digest` from the create response so the update is safe against concurrent edits.

If creating the experiment inside a notebook, the request needs two things beyond the name: the parent in `relationships.ancestors`, and the **parent's** digest as a query parameter. (Note: if the "Require Experiment to be in a Notebook" configuration is disabled in the entity settings, Experiment in our example, these parent parameters can be omitted).
    
    
    GET /entities/journal:e323ff17-…
    // → data.attributes.digest = "94013033"   ← the NOTEBOOK's digest
    POST /entities?digest=94013033
    {
      "data": {
        "type": "experiment",
        "attributes": { "name": "My New Experiment" },
        "relationships": {
          "ancestors": { "data": [ { "type": "journal", "id": "journal:e323ff17-…" } ] }
        }
      }
    }
    // → 201 Created; data.id = "experiment:0f7c02d1-…"
    //   data.attributes.digest is the NEW EXPERIMENT's digest — use it below
    PATCH /entities/experiment:0f7c02d1-…/properties?digest=60367023
    { "data": [ { "attributes": { "name": "Description", "value": "This is our new experiment" } } ] }

**Two digests, two different entities** The digest on the **create** is the _parent notebook's_ ; the digest on the **update** is the _new experiment's_ , returned in the create response. Using the wrong one is a common cause of an unexplained `400` or `428`. Note also that creating a child changes the parent's digest, so a script creating several experiments in a row must re-read the notebook between calls.

**Names must be unique within the notebook** A second experiment with the same name under the same parent is refused with `409 Conflict` — _“cannot have the same name as an existing item of same type in same location”_. The same name in a _different_ notebook is allowed, so a name identifies an experiment only together with its parent.

**Digests** If the experiment changed between the two calls, the saved `digest` is stale and the update returns `428`. Re-fetch with `GET /entities/{eid}` for the latest digest, then retry. See REST API → Concurrent editing.

## 3 · Sample registration flow

External ActionREST APIGET /samples/{id}/propertiesPATCH …/digests.external

An External Action on a Sample opens your page (with the sample id in `sampleId`); your page reads the sample, registers it in your LIMS, and records that it did — so Signals can warn when a registered sample later drifts out of date.

Two properties drive this:

Property| Meaning  
---|---  
digests.self| The sample's current state in Signals. Any change updates it.  
digests.external| The state your system last acknowledged. Initially empty.  
  
  1. Read the sample: `GET /samples/{sampleId}/properties` — you'll find `digests.self`, `digests.external`, and the fields you need (ID, Chemical Name, …).
  2. Register the sample in your external system.
  3. Record it: `PATCH /samples/{sampleId}/properties/digests.external` with the current `digests.self` value as the content.

    
    
    PATCH /samples/{sampleId}/properties/digests.external
    { "data": { "attributes": { "content": { "value": "48ac6e46…" } } } }

Now the two digests match. If the sample is edited later, `digests.self` changes, the two diverge, and Signals can flag that the sample needs re-registering. See External Actions for configuring the action.

## 4 · Automated archival of closed experiments

NotificationsREST APIasync PDF

Subscribe to **Sign and Close** notifications; when one fires, generate a PDF of the experiment and store it. PDF generation is asynchronous — the recommended pattern for large experiments.

Sign and Close notification Your handler reads entity id PUT export/pdf returns fileId HEAD poll until length > 0 GET / archive save the PDF

The archival pipeline: submit the export, poll until it is ready, then download and store the PDF.

  1. Handle the push notification and read the experiment id from `data.relationships.entity.data.id` (the `type` will be `close`).
  2. Start the export: `PUT /entities/export/pdf?eid={eid}&attachments=true` → returns a `fileId`.
  3. Poll `HEAD /entities/export/pdf/{fileId}` until `content-length > 0` (wait a few seconds between checks).
  4. Download: `GET /entities/export/pdf/{fileId}` → `content-type: application/pdf`. Save it.

    
    
    PUT /entities/export/pdf?eid=experiment:d5dc8e92-…&attachments=true
    // → { "data": { "attributes": { "fileId": "aa5fa03a-…", "fileName": "Images Experiment.pdf" } } }
    HEAD /entities/export/pdf/aa5fa03a-…    // content-length: 0  → not ready
    HEAD /entities/export/pdf/aa5fa03a-…    // content-length: 78526 → ready
    GET  /entities/export/pdf/aa5fa03a-…    // application/pdf

**A reusable pattern** **Submit → poll → download** is how Signals handles all long-running work (PDF/ZIP export, bulk import/update). Once recognised, it applies to any asynchronous endpoint. To ensure no Sign and Close event is missed, pair push delivery with pull notifications.

## 5 · Additional signing compliance

External ActionSigning EventGET /entities/{eid}/childrenpostMessage

Enforce an organization-specific rule at sign time. Configure an External Action on the **Sign and Close** signing event that opens your page in a dialog; your page checks the experiment and either allows the sign to proceed or blocks it. Here: require an Excel attachment named "Safety Sheet."

  1. Your page receives the experiment id from the action URL.
  2. Fetch its children: `GET /entities/{eid}` (or `/entities/{eid}/children`) and look through the `children` relationship for an `excel` entity; use the `included` array to read its name.
  3. If a child named "Safety Sheet" exists, allow the sign; otherwise block it and tell the user.

    
    
    // found it → let signing complete
    window.parent.postMessage(['closeAndContinue', []], 'https://<your-tenant>/')
    
    // missing → abort the sign, leaving the experiment open
    window.parent.postMessage(['closeAndAbort', []], 'https://<your-tenant>/')

**Complete implementation** The tutorial _External Checking for Chemical Drawings_ is a complete, runnable version of this pattern (a Flask app validating chemistry at sign time). For the dialog commands, see External Actions → Dialog messages.

## 6 · Bulk-exporting an experiment's contents

REST APIasync jobPOST /entities/export/bulkmultipart/mixed

PDF export (recipe 4) produces a document for people to read. **Bulk export** produces the underlying content for a machine to consume: every child of an experiment, each in its native format — HTML for text, CSV for tables, CDXML for structures, PNG for images, JSON for grids — returned together in a single `multipart/mixed` response with a manifest describing what is inside. Use it to archive an experiment, migrate it, or feed its contents into a pipeline.

Supported roots: `experiment`, `request`, `sample`, `parallel experiment`, `subexperiment`, and custom admin-defined objects.

### The three calls

The pattern is the familiar **submit → poll → download** , with one difference that matters: the download may be performed only once.
    
    
    // 1 — submit. Returns 202 and a jobId; depth is REQUIRED (see below).
    POST /entities/export/bulk?eid=experiment:2495f484-…&depth=-1
    
    { "data": { "type": "bulkExport",
               "id": "a299c3a8-f82c-4aca-b8b9-0b59d7f820ed",
               "attributes": { "jobId": "a299c3a8-…",
                                "entityEid": "experiment:2495f484-…",
                                "status": "IN_PROGRESS" } } }
    
    // 2 — poll every 2 seconds until the status changes
    GET /entities/export/bulk/a299c3a8-…
    //   IN_PROGRESS -> wait and repeat   COMPLETED -> download   FAILED -> read the error
    // 3 — download once. Content-Type: multipart/mixed
    GET /entities/export/bulk/a299c3a8-…/contents

How long a job takes depends on how much content the entity holds and how busy the export workers are, so poll rather than assuming a duration.

### Parameters

Parameter| Effect  
---|---  
eid| The entity to export. Required.  
depth| `0` the entity alone · `1` its immediate children · `-1` every descendant. **Send it explicitly** — see the warning below.  
types| Comma-separated entity types to include; everything else is skipped — for example `types=chemicalDrawing`.  
structureFormat| Format for `chemicalDrawing` and `sample` structures: `cdxml` (default), `inchi`, `mol`, `mol-v3000`, `smiles`, `svg`.  
stoichiometry| Default `true`. Exports each stoichiometry row as its own pair of parts; set it `false` to omit them entirely.  
stoichiometryStructureFormat| Format for reactant and product structures, _independently_ of `structureFormat`. Same list plus `helm`. Default `cdxml`.  
  
**Technical Illustration** Comparative evaluation of export options on a representative sample entity. and are not limits or guarantees — they are here only to show the direction each parameter moves things. 

Parameters| Parts returned  
---|---  
depth=0| 1 — the manifest alone  
depth=1| 18  
depth=-1| 30  
depth=-1&types=chemicalDrawing| 11  
…&stoichiometry=false| 2  
  
### Reading the response

The first part is always a manifest, named `table of content`. It mirrors the entity hierarchy and tells you which part holds each entity's content, so nothing has to be inferred from the ordering:
    
    
    // part 1 — Content-Disposition: form-data; name="table of content"
    { "root": {
        "eid": "experiment:2495f484-…",
        "name": "API Experiment 00001",
        "fields": { "Animal Subject": "Dog", "Description": "" },
        "children": [
          { "eid": "text:1d34af02-…", "name": "Text", "fields": { … },
            "content": { "type": "text/html",
                         "part": "part_1d34af02-…" } },
          …
        ] } }

Each `content.part` is the exact `name` of the multipart part carrying the bytes, and each part is named `part_` followed by the entity's UUID — the eid without its `type:` prefix. Children nest, so a Samples Table contains its sample rows and a Worksheet contains its tables.

Each part carries the content type appropriate to its entity, so a consumer can dispatch on it directly. Text elements arrive as `text/html`, tables as `text/csv`, grids and worksheets as `application/json`, drawings as `chemical/x-cdxml` (or whichever `structureFormat` was requested), images as `image/png`, and uploaded documents in their own type.

#### Stoichiometry

A `chemicalDrawing` child gains a `stoichiometry` block listing `reactants` and `products`. Every row carries its own `structure` and `properties` parts, keyed by row id, alongside the row's `name`:
    
    
    "stoichiometry": { "reactants": [
      { "rowId": "39", "name": "(2Z,4E)-hexa-2,4-diene",
        "structure":  { "content": { "type": "chemical/x-cdxml",
                                    "part": "part_eec00078-…_r_39_structure" } },
        "properties": { "content": { "type": "application/json",
                                    "part": "part_eec00078-…_r_39_properties" } } } ] }

The block has six keys: `reactants`, `products`, `solvents` and `conditions` are lists of rows, `summary` is a single object describing the table as a whole, and `fields` holds the table's own values. Part names follow a readable convention (`_r_` reactant, `_p_` product, `_summary_properties`), but treat that as incidental — **always take the part name from`content.part` rather than assembling it yourself**. A consumer that walks only `reactants` and `products` will silently leave the summary, solvents and conditions behind.

### Unpacking the download

What arrives is one byte stream containing every file, separated by a boundary string that the `Content-Type` header names. Each section carries its own headers and then its payload:
    
    
    Content-Type: multipart/mixed; boundary=---bulk-export-content-boundary-eb…---
    
    -----bulk-export-content-boundary-eb…---
    Content-Type: application/json
    Content-Disposition: form-data; name="table of content"
    content-length: 6557
    
    {"root":{"eid":"experiment:2495f484-…", … }}
    -----bulk-export-content-boundary-eb…---
    Content-Type: text/html
    Content-Disposition: form-data; name="part_1d34af02-…"
    content-length: 19
    
    <p>This is text</p>
    -----bulk-export-content-boundary-eb…---
    … one section per file …

The `name` in each `Content-Disposition` is the identifier the manifest uses. That is the only thing tying a payload to an entity — **order is not meaningful** , so index the sections by name and then resolve each entity through the manifest.

**Do not split on the boundary by hand** The declared boundary already ends in dashes, and the delimiter in the body is that string with `--` prefixed, which makes naive string-splitting error-prone. Payloads are binary in places, so the stream must be handled as bytes throughout. Use a MIME parser: Python's built-in `email` package does this correctly once you feed it the `Content-Type` header along with the body.

#### Step 1 — index the sections by name
    
    
    import json, re, requests
    from email import message_from_bytes
    
    resp = requests.get(f"{BASE}/entities/export/bulk/{job}/contents", headers=HDRS)
    
    # the parser needs the Content-Type header, so put it back in front of the body
    msg = message_from_bytes(b"Content-Type: " + resp.headers["Content-Type"].encode()
                             + b"\r\n\r\n" + resp.content)
    
    parts = {}
    for part in msg.get_payload():
        name = re.search(r'name="([^"]+)"', part.get("Content-Disposition", ""))
        if name:
            # decode=True returns bytes and handles any transfer encoding
            parts[name.group(1)] = (part.get_content_type(), part.get_payload(decode=True))
    
    manifest = json.loads(parts["table of content"][1])

#### Step 2 — choose a file extension from the content type

Every section states its own type, so the extension follows from it rather than from any guesswork about the entity:

Content type| Produced by| Save as  
---|---|---  
text/html| Text elements| .html  
text/csv| Materials, samples and other tables| .csv  
application/json| Grids, worksheets, tasks, stoichiometry properties| .json  
chemical/x-cdxml| `structureFormat=cdxml` (default)| .cdxml  
chemical/x-mdl-molfile| `structureFormat=mol`| .mol  
chemical/x-mdl-molfile-v3000| `structureFormat=mol-v3000`| .mol  
chemical/x-daylight-smiles| `structureFormat=smiles`| .smi  
chemical/x-inchi| `structureFormat=inchi`| .inchi  
image/svg+xml| `structureFormat=svg`| .svg  
image/png| Image elements| .png  
application/vnd.openxmlformats-officedocument.wordprocessingml.document| Uploaded Word documents| .docx  
  
Keep a small lookup and fall back to `.bin` for anything unrecognised, so an unfamiliar attachment type is still written out rather than dropped.

#### Step 3 — walk the manifest and write the files

Because the manifest nests, the same walk that resolves the parts can reproduce the experiment's structure on disk. This writes one folder per entity, the entity's own content inside it, and its header values alongside:
    
    
    import json, os, re
    
    EXT = { "text/html": ".html", "text/csv": ".csv", "application/json": ".json",
            "chemical/x-cdxml": ".cdxml", "chemical/x-inchi": ".inchi",
            "chemical/x-mdl-molfile": ".mol", "chemical/x-mdl-molfile-v3000": ".mol",
            "chemical/x-daylight-smiles": ".smi",
            "image/png": ".png", "image/svg+xml": ".svg",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx" }
    
    def safe(name):
        # entity names are free text; strip anything a filesystem will reject
        return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", str(name)).strip(" .") or "unnamed"
    
    def write(part_name, folder, stem):
        if part_name not in parts:
            return
        content_type, blob = parts[part_name]
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, safe(stem) + EXT.get(content_type, ".bin"))
        with open(path, "wb") as fh:          # binary — never text mode
            fh.write(blob or b"")
    
    def unpack(node, folder):
        os.makedirs(folder, exist_ok=True)
    
        # the entity's header fields travel in the manifest, not as a part
        with open(os.path.join(folder, "_fields.json"), "w", encoding="utf-8") as fh:
            json.dump(node.get("fields", {}), fh, indent=1)
    
        if node.get("content"):
            write(node["content"]["part"], folder, node.get("name", "content"))
    
        stoich = node.get("stoichiometry") or {}
        for role in ("reactants", "products", "solvents", "conditions"):
            for row in stoich.get(role, []):
                sub = os.path.join(folder, "stoichiometry", role)
                label = f"{row.get('rowId')}_{row.get('name','')}"
                for key in ("structure", "properties"):
                    blk = (row.get(key) or {}).get("content")
                    if blk:
                        write(blk["part"], sub, f"{label}_{key}")
    
        if stoich.get("summary"):                      # easily missed
            blk = (stoich["summary"].get("properties") or {}).get("content")
            if blk:
                write(blk["part"], os.path.join(folder, "stoichiometry"), "summary")
    
        for child in node.get("children", []):
            unpack(child, os.path.join(folder, safe(child.get("name", "child"))))
    
    root = manifest["root"]
    unpack(root, os.path.join("export", safe(root["name"])))

Run against an experiment containing text, tasks, tables, samples, a drawing with stoichiometry, an image and an attachment, that produces a tree of the shape:
    
    
    export/API Experiment 00001/
    ├── _fields.json
    ├── Text/Text.html
    ├── Tasks/Tasks.json
    │   ├── Task-1/Task-1.json
    │   └── Task-2/Task-2.json
    ├── Materials Table/Materials Table.csv
    ├── Samples Table/
    │   ├── Samples Table.csv
    │   └── Sample-57/Sample-57.cdxml
    ├── ChemDraw Document/
    │   ├── ChemDraw Document.cdxml
    │   └── stoichiometry/
    │       ├── reactants/39_(2Z,4E)-hexa-2,4-diene_structure.cdxml
    │       ├── reactants/39_(2Z,4E)-hexa-2,4-diene_properties.json
    │       ├── products/23_cyclohexene_structure.cdxml
    │       └── summary.json
    ├── exampleImage.png
    └── My Word Doc.docx

**Check that nothing was left behind** After walking the manifest, compare the part names you resolved against the names you indexed. Anything in the payload that the walk did not reach means a branch of the manifest is not being handled — the stoichiometry `summary` is the usual culprit. One line catches it: 
    
    
    leftover = set(parts) - resolved - {"table of content"}
    assert not leftover, leftover

### Practical notes

**The download works exactly once** The server deletes the content as soon as it has been sent. A second `GET …/contents` returns `404`, and so does a status check on the same job — the job record disappears with it. Write the bytes to durable storage before doing anything else; if the transfer fails part-way, the export has to be repeated from the beginning. Content that is never downloaded is discarded after **two hours**.

**Send`depth` explicitly** The specification gives `depth` a default of `0`, but omitting it is rejected with `400 — "Depth(null) is not a valid integer."` Treat the parameter as required. Note also that `depth=0` returns the manifest alone: an experiment's own content lives in its children.

**Two structure formats, not one** `structureFormat` governs only the drawing itself. Reactant and product structures follow `stoichiometryStructureFormat`, and both default to `cdxml`. Setting just the first converts the drawing and silently leaves every stoichiometry structure as CDXML. If you want SMILES throughout, for instance, both parameters have to say so.

**Capacity is shared** Exports run on a pool of workers. When none is free the submit returns `429`; this is a queueing signal rather than the tenant rate limit, so retry the submission after a short pause.
