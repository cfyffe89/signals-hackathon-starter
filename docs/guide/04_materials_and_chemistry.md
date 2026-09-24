<!-- 
Signals EMEA Hackathon 2026 Reference Guide (Distilled Markdown)
Architecture Notice: Use FastAPI (backend) & Streamlit (UI). Do NOT copy legacy Flask patterns.
-->


# External Data Sources, Lists & Chemical Sources

Signals can pull data from systems you host directly into the notebook — as dropdown values, as live table rows, and as chemical structures in a reaction. All three are configured under one Data Sources area and share the same basic model.

1Overview
2How they work
3External Lists
4External Data Sources
5External Chemical Sources
6Limits
7Next steps

## 1 · Overview

There are three external source types. They differ in what they return and where the data lands in Signals:

| Type | Returns | Lands in | Direction |

| External List | A list of values | An attribute's dropdown / picklist | read |

| External Data Source | A record, by key | Rows of an Admin-Defined Table | read write |

| External Chemical Source | A structure + properties, by key | Reactants / Products in Stoichiometry | read |

System Configuration → Data Sources. All three source types are created from here.

Choose a List to keep a field's options in sync with a system of record; a Data Source to fill (or push back) a whole table row from a key such as a barcode; and a Chemical Source to let chemists pull a registered compound's structure into a reaction.

## 2 · How they work

All three source types share a common model:

* You host a RESTful URL. Signals calls it and expects JSON in response. A static file is sufficient for a read-only List; a dynamic service is required for keyed lookups and writes.

* Header authentication. Each configuration supports one or more HTTP headers (name + value) — for example an API key — which Signals sends on every request so your server can authenticate the call. Use Add HTTP Header to define as many as your endpoint requires.

* Fetch Example Data & field mapping. A button pulls a sample response so you can map external fields to Signals — choosing the key, descriptions, data types, and which fields to include. A Test control exercises the endpoint before you save.

* Response-time budgets. To protect the UI, Signals gives up if your server is slow — Lists at 30 seconds, Data & Chemical Sources at 20 seconds.

All three are created under System Configuration → Data Sources → Create Data Source. Every configuration field is documented in the sections below; the System Configuration Guide covers the administrative procedure and the permissions needed to reach these screens.

Proxy mode
      Where the Use Preconfigured Proxy feature is enabled for the tenant, a source can route through a
      preconfigured proxy instead of calling your URL directly. Source then becomes a dropdown of available
      proxy URLs, Destination URL is populated from the chosen proxy, and a Context field
      supplies the trailing path segments of the destination. The data contract your endpoint must satisfy is unchanged.
Two further source types, out of scope here
Create Data Source also offers Internal Data Source (drawing on data already inside
      Signals) and External Ontology Source. Neither requires you to build an endpoint, so neither is
      covered on this page; both are described in the System Configuration Guide.

## 3 · External Lists

An External List populates an attribute's dropdown from your server. It is read-only, and Signals holds a cached copy that is refreshed on a schedule.

Refresh is configured on the attribute, not on the source
      The source defines where the values come from; refreshing is set where they are consumed. In Attributes → Create Attribute → List, select External List and choose the source. That attribute page then offers Schedule a Refresh Now for an immediate pull, a Refresh Frequency of Hourly, Daily, or Never, and a Last Refreshed timestamp.
A new list attribute is empty until its first refresh
      Creating the attribute does not populate it. Run Schedule a Refresh Now once, or users will see an empty dropdown and conclude the integration is broken.

#### Data format

A `GET` returns a top-level `data` array of objects. Objects may carry several fields; you pick which one is the list's key (the stored value) and, optionally, a description field.

```python
GET https://your-server/list  →
{ "data": [
    { "code": "BIO-100", "project": "Oncology Screen" },
    { "code": "CHM-204", "project": "Lead Optimization" }
] }
```

#### Configuration

| Field | What it does |

| Source Name · Description | Identify the list. |

| Destination URL | The endpoint Signals calls. |

| HTTP Headers | Optional authentication headers sent with the request. Add as many as required. |

| Fetch Example Data | Pull a sample response to map fields. |

| Field mapping | For each external field: an Internal Field Name, and flags Key (the stored value — required, exactly one), Desc. (shown with the option), and Include. Add Manual Field covers values not present in the sample. |

Attach the list to a list-type attribute (Configuration → Attributes); any field or table using that attribute then shows your live options.

## 4 · External Data Sources

A Data Source fills an Admin-Defined-Table row when a user enters a key, and can push rows back to your system.

#### The URL carries the lookup value

The Destination URL is a template. Signals substitutes the key the user enters as `{id}`, and can also send `{username}` and `{user_alias}`:

```python
https://your-server/flasks/{id}
e.g. https://abc.com?id={id}&un={username}&alias={user_alias}
```

#### Operations

```python
GET  /flasks/88             → { "id":"88", "name":"Flask A", "amount":250 }   // fetch by key
POST /flasks  { … }         → creates & echoes the row
PUT  /flasks/89 { … }       → updates & echoes the row
```

#### Nested responses are flattened automatically

A response does not have to be flat. Signals walks the JSON it receives and offers every leaf value as a mappable field, naming each one by its path. Nested objects and arrays therefore require no flattening on your server.

| In your response | Offered as a field |

| Nested object, to any depth | `address.city`, `a.b.c.d` |

| Array of values | `tags[0]`, `tags[1]`, `tags[2]` |

| Array of objects | `variants[0].ratio`, `variants[1].ratio` |

| Array inside an array | `matrix[0][1]` |

| Object inside a mixed array | `items[4].detail` |

| Key that itself contains a dot | `["field.with.dots"]` — bracket-escaped, so it is not read as a path |

Keys containing spaces, hyphens, or mixed case are preserved exactly as sent, and `null` values map normally, arriving as empty cells.

Empty objects and arrays cannot be mapped
      An `{}` or `[]` is listed as a field but holds no value to convert, so it fails validation against every data type. Leave such fields unmapped — which does not prevent saving — or return a scalar value instead of an empty container.
The mapping follows your example record
      The field list is derived from the record fetched for the Example ID. If your endpoint later returns leaves that record did not contain, they have no mapping until you run Fetch Example Data again. Where a response shape varies between records, choose an example that contains every field you intend to map.

#### Data types and conversion

Each mapped field is assigned one of six data types:

TextNumberIntegerCheckboxDate/TimeExternal Hyperlink

Conversion is deliberately strict. A value that cannot be represented in the chosen type is reported by Test Mapping rather than being silently altered:

| Value sent | Mapped to | Result |

| `3.14159` | Integer | Rejected Fractional values are never truncated to fit. |

| `"red"` | Number | Rejected Text that is not numeric is not coerced. |

| `"true"` | Checkbox | Rejected Checkbox requires a real JSON boolean, not the string. |

| `"2026-07-28"` | Date/Time | Rejected A time component is required, as in `2026-07-28T14:30:00Z`. |

| `"42"` | Number | Accepted Numeric strings are parsed. |

| `true` | Checkbox | Accepted |

Map identifiers to Text, not Number
      A numeric-looking string is accepted as a Number, and its leading zeros are lost: the postcode `"02101"` becomes `2101`. Postcodes, part numbers, and similar identifiers must be mapped to Text to survive intact.

#### Configuration

| Field | What it does |

| Source Name · Description · URL | Identify the source and its endpoint template. |

| HTTP Headers | Optional authentication headers, up to 20 per source. Use Add HTTP Header to add each one. |

| Example ID | A sample key so Fetch Example Data has something to look up. |

| Available operations | Tick GET to fetch, POST to create, PUT to update. GET-only = read-only lookup. |

| Field mapping | Map each external field to a Signals Data Type and mark exactly one as the Key. Nested responses are flattened for you — see above. |

Use the source from an Admin-Defined Table: entering a key in a row triggers the `GET` and fills the mapped columns. With POST/PUT enabled, edited rows sync back to your server.

## 5 · External Chemical Sources

A Chemical Source is the chemistry-aware relative of a Data Source. For a key — a compound name or id — it returns a chemical structure plus properties, and drops them straight into a reaction's Reactants or Products grids through the ChemDraw plugin's Quick Add.

Enable Stoichiometry Configuration With this toggle on, the source is connected to the Reactants and Products tables in Stoichiometry, so end-users can add its products and reactants via Quick Add. This is what makes a Chemical Source more than a generic table lookup.
The External Chemical Source configuration panel showing Destination URL, Quick Add hint text, and stoichiometry column mapping.

#### The data contract

Like a Data Source, but the record includes a structure field (SMILES, MOL, …) alongside properties:

```python
GET https://your-server/chem/{id} // same {id}/{username}/{user_alias} placeholders

GET /chem/benzene →
{ "id": "benzene", "name": "Benzene", "CAS": "71-43-2",
  "MW": 78.11, "MF": "C6H6", "smiles": "c1ccccc1" }
```

#### Configuration

| Field | What it does |

| Enable Stoichiometry Configuration | Connects the source to Reactants/Products for Quick Add (see above). |

| Source Name · Description · URL · HTTP Headers · Example ID | As for a Data Source. |

| Quick Add Hint Text | The prompt shown in the Quick Add box for this source. |

| Chemical structure field + Structure Format | Which response field holds the structure, and its format (e.g. SMILES). Tick Base64 Encoded or Chemical Structure is Link if the structure is encoded or referenced by URL rather than inline. |

| Record Field → column mapping | Map your response fields to Stoichiometry columns (see below). |

Mapping the structure field and format, then each record field to a Stoichiometry column.

#### Mappable stoichiometry columns

Beyond the structure, a Chemical Source can populate any of these reaction columns:

| Group | Columns |

| Identity | Product/Reactant Name · CAS Number · Reg ID · HELM · Supplier · Lot Number · Barcode |

| Structure-derived | MF · FM · MW · EM |

| Quantities | Load · Molarity · d (density) · % Wt · Purity · Conversion |

Use Test Mapping to confirm the fields resolve, then save. In a Chemical Drawing's stoichiometry grid, a user picks Quick Add and types a key (`benzene`); Signals fetches the record, renders the structure into the reaction, and fills the mapped columns.

## 6 · Limits

| Limit | Detail |

| List size | Up to 20,000 items per External List. |

| Lists per tenant | Up to 200. |

| List response time | 30 seconds before timing out. |

| Data & Chemical Source response time | 20 seconds before timing out. |

Response time These budgets are firm, and keyed sources are called during user interaction. Cache upstream lookups and pre-shape responses so that a request resolves quickly rather than triggering a live cross-system query.

## 7 · Next steps

For a hands-on walkthrough — including a single reference server that implements all three contracts (a list, a keyed data source with GET/POST/PUT, and a chemical source returning a structure) — see the tutorial External Lists, Data Sources & Chemical Sources. To read or write the entities these sources feed, see the REST API and Search pages.

---

# Example Concepts & Workflows

Five worked recipes that combine the integration surfaces into real solutions. Each shows the components, the endpoints, and the steps — ready to adapt.

## Before you begin

Every recipe below assumes the API base URL `https://<your-tenant>/api/rest/v1.0` and an authenticated request — an `x-api-key` header for server-to-server flows, or a bearer token for user-driven ones (see REST API → Authentication). Remember that create and update calls appear in the audit log as the user the credential belongs to.

### The recipes at a glance

| Recipe | Components | Key endpoints |

| User management | REST API | GET/POST /users |

| Create & update an experiment | REST API | POST /entities?digest=<parent> · PATCH /entities/{eid}/properties |

| Sample registration | External Action · REST API | GET/PATCH /samples/{id}/properties |

| Automated archival | Notifications · REST API | PUT/HEAD/GET /entities/export/pdf |

| Signing compliance | External Action · REST API | GET /entities/{eid}/children |

| Bulk-export an experiment | REST API · async job | POST /entities/export/bulk |

## 1 · User management

REST APIGET /usersPOST /users

List users, create one, and confirm. Roles come back as relationships; grab the role `id` you need from `GET /roles` (or a prior `GET /users`).

#### List users

```python
GET /users?enabled=true&page[offset]=0&page[limit]=20

// trimmed — each user has attributes + a "roles" relationship
{ "data": [ { "type": "user", "id": "100",
    "attributes": { "email": "ross.geller@example.com", "firstName": "Ross", "isEnabled": true },
    "relationships": { "roles": { "data": [ { "type": "role", "id": "3" } ] } } } ] }
```

#### Create a standard user

```python
POST /users
{ "data": { "attributes": {
    "firstName": "Rachel", "lastName": "Green",
    "emailAddress": "rachel.green@example.com",
    "country": "USA", "organization": "example",
    "roles": [ { "id": "3", "name": "Standard User" } ]
} } }   // 201 → the new user, id 101
```

Re-run `GET /users` to confirm; the full response lists every user with their roles resolved in `included`.

## 2 · Create an experiment & update its properties

REST APIPOST /entitiesPATCH /entities/{eid}/properties

Create an experiment inside a notebook, then set a property — capturing the `digest` from the create response so the update is safe against concurrent edits.

If creating the experiment inside a notebook, the request needs two things beyond the name: the parent in `relationships.ancestors`, and the parent's digest as a query parameter. (Note: if the "Require Experiment to be in a Notebook" configuration is disabled in the entity settings, Experiment in our example, these parent parameters can be omitted).

```python
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
```

Two digests, two different entities
      The digest on the create is the parent notebook's; the digest on the update is the
      new experiment's, returned in the create response. Using the wrong one is a common cause of an unexplained
      `400` or `428`. Note also that creating a child changes the parent's digest, so a script creating several
      experiments in a row must re-read the notebook between calls.
Names must be unique within the notebook
      A second experiment with the same name under the same parent is refused with `409 Conflict` —
      “cannot have the same name as an existing item of same type in same location”. The same name in a
      different notebook is allowed, so a name identifies an experiment only together with its parent.
Digests If the experiment changed between the two calls, the saved `digest` is stale and the update returns `428`. Re-fetch with `GET /entities/{eid}` for the latest digest, then retry. See REST API → Concurrent editing.

## 3 · Sample registration flow

External ActionREST APIGET /samples/{id}/propertiesPATCH …/digests.external

An External Action on a Sample opens your page (with the sample id in `sampleId`); your page reads the sample, registers it in your LIMS, and records that it did — so Signals can warn when a registered sample later drifts out of date.

Two properties drive this:

| Property | Meaning |

| digests.self | The sample's current state in Signals. Any change updates it. |

| digests.external | The state your system last acknowledged. Initially empty. |

* Read the sample: `GET /samples/{sampleId}/properties` — you'll find `digests.self`, `digests.external`, and the fields you need (ID, Chemical Name, …).

* Register the sample in your external system.

* Record it: `PATCH /samples/{sampleId}/properties/digests.external` with the current `digests.self` value as the content.

```python
PATCH /samples/{sampleId}/properties/digests.external
{ "data": { "attributes": { "content": { "value": "48ac6e46…" } } } }
```

Now the two digests match. If the sample is edited later, `digests.self` changes, the two diverge, and Signals can flag that the sample needs re-registering. See External Actions for configuring the action.

## 4 · Automated archival of closed experiments

NotificationsREST APIasync PDF

Subscribe to Sign and Close notifications; when one fires, generate a PDF of the experiment and store it. PDF generation is asynchronous — the recommended pattern for large experiments.

Sign and Close
notification

Your handler
reads entity id

PUT export/pdf
returns fileId

HEAD poll
until length > 0

GET / archive
save the PDF

The archival pipeline: submit the export, poll until it is ready, then download and store the PDF.

* Handle the push notification and read the experiment id from `data.relationships.entity.data.id` (the `type` will be `close`).

* Start the export: `PUT /entities/export/pdf?eid={eid}&attachments=true` → returns a `fileId`.

* Poll `HEAD /entities/export/pdf/{fileId}` until `content-length > 0` (wait a few seconds between checks).

* Download: `GET /entities/export/pdf/{fileId}` → `content-type: application/pdf`. Save it.

```python
PUT /entities/export/pdf?eid=experiment:d5dc8e92-…&attachments=true
// → { "data": { "attributes": { "fileId": "aa5fa03a-…", "fileName": "Images Experiment.pdf" } } }
HEAD /entities/export/pdf/aa5fa03a-…    // content-length: 0  → not ready
HEAD /entities/export/pdf/aa5fa03a-…    // content-length: 78526 → ready
GET  /entities/export/pdf/aa5fa03a-…    // application/pdf
```

A reusable pattern Submit → poll → download is how Signals handles all long-running work (PDF/ZIP export, bulk import/update). Once recognised, it applies to any asynchronous endpoint. To ensure no Sign and Close event is missed, pair push delivery with pull notifications.

## 5 · Additional signing compliance

External ActionSigning EventGET /entities/{eid}/childrenpostMessage

Enforce an organization-specific rule at sign time. Configure an External Action on the Sign and Close signing event that opens your page in a dialog; your page checks the experiment and either allows the sign to proceed or blocks it. Here: require an Excel attachment named "Safety Sheet."

* Your page receives the experiment id from the action URL.

* Fetch its children: `GET /entities/{eid}` (or `/entities/{eid}/children`) and look through the `children` relationship for an `excel` entity; use the `included` array to read its name.

* If a child named "Safety Sheet" exists, allow the sign; otherwise block it and tell the user.

```python
// found it → let signing complete
window.parent.postMessage(['closeAndContinue', []], 'https://<your-tenant>/')

// missing → abort the sign, leaving the experiment open
window.parent.postMessage(['closeAndAbort', []], 'https://<your-tenant>/')
```

Complete implementation The tutorial External Checking for Chemical Drawings is a complete, runnable version of this pattern (a Flask app validating chemistry at sign time). For the dialog commands, see External Actions → Dialog messages.

## 6 · Bulk-exporting an experiment's contents

REST APIasync jobPOST /entities/export/bulkmultipart/mixed

PDF export (recipe 4) produces a document for people to read. Bulk export produces the underlying content for a machine to consume: every child of an experiment, each in its native format — HTML for text, CSV for tables, CDXML for structures, PNG for images, JSON for grids — returned together in a single `multipart/mixed` response with a manifest describing what is inside. Use it to archive an experiment, migrate it, or feed its contents into a pipeline.

Supported roots: `experiment`, `request`, `sample`, `parallel experiment`, `subexperiment`, and custom admin-defined objects.

### The three calls

The pattern is the familiar submit → poll → download, with one difference that matters: the download may be performed only once.

```python
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
```

How long a job takes depends on how much content the entity holds and how busy the export workers are, so poll rather than assuming a duration.

### Parameters

| Parameter | Effect |

| eid | The entity to export. Required. |

| depth | `0` the entity alone · `1` its immediate children · `-1` every descendant. Send it explicitly — see the warning below. |

| types | Comma-separated entity types to include; everything else is skipped — for example `types=chemicalDrawing`. |

| structureFormat | Format for `chemicalDrawing` and `sample` structures: `cdxml` (default), `inchi`, `mol`, `mol-v3000`, `smiles`, `svg`. |

| stoichiometry | Default `true`. Exports each stoichiometry row as its own pair of parts; set it `false` to omit them entirely. |

| stoichiometryStructureFormat | Format for reactant and product structures, independently of `structureFormat`. Same list plus `helm`. Default `cdxml`. |

Technical Illustration
      Comparative evaluation of export options on a representative sample entity.
      and are not limits or guarantees — they are here only to show the direction each parameter moves things.
      

| Parameters | Parts returned |

| depth=0 | 1 — the manifest alone |

| depth=1 | 18 |

| depth=-1 | 30 |

| depth=-1&types=chemicalDrawing | 11 |

| …&stoichiometry=false | 2 |

### Reading the response

The first part is always a manifest, named `table of content`. It mirrors the entity hierarchy and tells you which part holds each entity's content, so nothing has to be inferred from the ordering:

```python
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
```

Each `content.part` is the exact `name` of the multipart part carrying the bytes, and each part is named `part_` followed by the entity's UUID — the eid without its `type:` prefix. Children nest, so a Samples Table contains its sample rows and a Worksheet contains its tables.

Each part carries the content type appropriate to its entity, so a consumer can dispatch on it directly. Text elements arrive as `text/html`, tables as `text/csv`, grids and worksheets as `application/json`, drawings as `chemical/x-cdxml` (or whichever `structureFormat` was requested), images as `image/png`, and uploaded documents in their own type.

#### Stoichiometry

A `chemicalDrawing` child gains a `stoichiometry` block listing `reactants` and `products`. Every row carries its own `structure` and `properties` parts, keyed by row id, alongside the row's `name`:

```python
"stoichiometry": { "reactants": [
  { "rowId": "39", "name": "(2Z,4E)-hexa-2,4-diene",
    "structure":  { "content": { "type": "chemical/x-cdxml",
                                "part": "part_eec00078-…_r_39_structure" } },
    "properties": { "content": { "type": "application/json",
                                "part": "part_eec00078-…_r_39_properties" } } } ] }
```

The block has six keys: `reactants`, `products`, `solvents` and `conditions` are lists of rows, `summary` is a single object describing the table as a whole, and `fields` holds the table's own values. Part names follow a readable convention (`_r_` reactant, `_p_` product, `_summary_properties`), but treat that as incidental — always take the part name from `content.part` rather than assembling it yourself. A consumer that walks only `reactants` and `products` will silently leave the summary, solvents and conditions behind.

### Unpacking the download

What arrives is one byte stream containing every file, separated by a boundary string that the `Content-Type`
    header names. Each section carries its own headers and then its payload:

```python
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
```

The `name` in each `Content-Disposition` is the identifier the manifest uses. That is the only
    thing tying a payload to an entity — order is not meaningful, so index the sections by name and then
    resolve each entity through the manifest.

Do not split on the boundary by hand
      The declared boundary already ends in dashes, and the delimiter in the body is that string with `--` prefixed,
      which makes naive string-splitting error-prone. Payloads are binary in places, so the stream must be handled as bytes
      throughout. Use a MIME parser: Python's built-in `email` package does this correctly once you feed it the
      `Content-Type` header along with the body.

#### Step 1 — index the sections by name

```python
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
```

#### Step 2 — choose a file extension from the content type

Every section states its own type, so the extension follows from it rather than from any guesswork about the entity:

| Content type | Produced by | Save as |

| text/html | Text elements | .html |

| text/csv | Materials, samples and other tables | .csv |

| application/json | Grids, worksheets, tasks, stoichiometry properties | .json |

| chemical/x-cdxml | `structureFormat=cdxml` (default) | .cdxml |

| chemical/x-mdl-molfile | `structureFormat=mol` | .mol |

| chemical/x-mdl-molfile-v3000 | `structureFormat=mol-v3000` | .mol |

| chemical/x-daylight-smiles | `structureFormat=smiles` | .smi |

| chemical/x-inchi | `structureFormat=inchi` | .inchi |

| image/svg+xml | `structureFormat=svg` | .svg |

| image/png | Image elements | .png |

| application/vnd.openxmlformats-officedocument.wordprocessingml.document | Uploaded Word documents | .docx |

Keep a small lookup and fall back to `.bin` for anything unrecognised, so an unfamiliar attachment type is
    still written out rather than dropped.

#### Step 3 — walk the manifest and write the files

Because the manifest nests, the same walk that resolves the parts can reproduce the experiment's structure on disk.
    This writes one folder per entity, the entity's own content inside it, and its header values alongside:

```python
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
```

Run against an experiment containing text, tasks, tables, samples, a drawing with stoichiometry, an image and an
    attachment, that produces a tree of the shape:

```python
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
```

Check that nothing was left behind
      After walking the manifest, compare the part names you resolved against the names you indexed. Anything in the payload
      that the walk did not reach means a branch of the manifest is not being handled — the stoichiometry
      `summary` is the usual culprit. One line catches it:
      
```python
leftover = set(parts) - resolved - {"table of content"}
assert not leftover, leftover
```

### Practical notes

The download works exactly once
      The server deletes the content as soon as it has been sent. A second `GET …/contents` returns `404`, and so does a status check on the same job — the job record disappears with it. Write the bytes to durable storage before doing anything else; if the transfer fails part-way, the export has to be repeated from the beginning. Content that is never downloaded is discarded after two hours.
Send `depth` explicitly
      The specification gives `depth` a default of `0`, but omitting it is rejected with `400 — "Depth(null) is not a valid integer."` Treat the parameter as required. Note also that `depth=0` returns the manifest alone: an experiment's own content lives in its children.
Two structure formats, not one
`structureFormat` governs only the drawing itself. Reactant and product structures follow `stoichiometryStructureFormat`, and both default to `cdxml`. Setting just the first converts the drawing and silently leaves every stoichiometry structure as CDXML. If you want SMILES throughout, for instance, both parameters have to say so.
Capacity is shared
      Exports run on a pool of workers. When none is free the submit returns `429`; this is a queueing signal rather than the tenant rate limit, so retry the submission after a short pause.