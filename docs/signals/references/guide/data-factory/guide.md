# SDF Public API — Guide

A practical guide to the **Signals Data Factory (SDF) Public API**: what it
models, how to authenticate, and how to run the common workflows (discover →
search/export → write → track). Pairs with `sdf-openapi.yaml` (the machine-
readable spec). Endpoint-by-endpoint request/response shapes live in the spec;
this guide is the narrative and the gotchas.

---

## 1. The mental model

SDF stores assay/screening data as **result rows** attached to **entities**,
grouped into **projects**:

```
Project ──┬── Entity rows      (Compound → Batch → …, a hierarchy)
          └── Result rows      (each typed by one Measurement Type)

Measurement Type ── Attributes  (the typed, filterable columns of a result)
Map ── mappings: attributeId → column   (required for any write)
```

- **Project** — the container. v2 project ids are GUIDs
  (`e087599a-ef53-4da7-bfc8-c97544c3a018`); v1 project ids are small numbers.
- **Measurement type (mtype)** — a *result schema*: a named set of typed
  attributes. Its id is 24 hex chars (`68b1b8036675f6817860970d`). The same id
  is called `mtypeId` in v1 and `resultSchemaId` in v2 row URLs — **they are the
  same value** (verified live).
- **Entity** — the subject a result hangs off. Core hierarchy is **Compound**
  (level 2) → **Batch** (level 3) → **Result**. `entityName` is a *type name*
  string (`"Compound"`), not an id.
- **Map** — how incoming columns fill entity/result attributes. Required for
  every write.
- **Writes are asynchronous** — they return `202` + a `publicationId`; the data
  lands when the publication finishes.

---

## 2. Authentication & base URL

Every request needs the `x-api-key` header:

```bash
curl https://your-tenant.revvitycloud.com/datafactory/api/v2/projects \
  -H "x-api-key: $SDF_API_KEY"
```

- **Base URL** is per-tenant and ends in `/datafactory`.
- **No key / bad key → `401 Authorization Required` returned as plain HTML**
  (from the gateway, before the app) — *not* the JSON error envelope. Don't try
  to `JSON.parse` an auth failure. (The JSON `403` schemas are for
  authenticated-but-unpermitted requests, a different case.)
- Keep the key server-side. Never put it in a URL or query string.

---

## 3. Discovering what's there

| Goal | Call |
|---|---|
| Projects (GUIDs) | `GET /api/v2/projects` |
| Projects (v1, numeric) | `GET /api/v1/projects` |
| Measurement types → `mtypeId` | `GET /api/v1/info-design/measurement-types` |
| An mtype's **filterable attributes** | `GET /api/v1/info-design/measurement-types/{mtypeId}/attributes` |
| Data maps → `mapId` | `GET /api/v2/maps` |

There is **no endpoint for "which measurement types does this project have data
for."** Either read the `Type ID` column from a sample of results, or probe each
mtype with a project-scoped search (one request per type — definitive).

---

## 4. Searching & exporting (read-only)

Four endpoints, all `POST`/`GET` reads (the POSTs carry a filter body but change
nothing):

| Call | Scope |
|---|---|
| `POST /api/v1/projects/{projectId}/results` | all results in a project |
| `POST /api/v1/projects/{projectId}/results/{mtypeId}` | one mtype in a project |
| `POST /api/v1/data/search/measurements/{mtypeId}` | one mtype, optional `{ projectId }` body |
| `GET /api/v1/projects/{projectId}/{entityName}/{entityId}/results` | one entity record |

**Request body** (the two project-results endpoints):

```jsonc
{
  "filters": {
    "entity": "Compound",                          // entity type name
    "attributes": { "Assay Date": "2025-01-01" },  // exact match; see §5 for valid keys
    "tags": ["<mtypeTag>"],                         // only mtypes with these tags
    "options": { "Assay Date": { "format": "yyyy-MM-dd" } }
  },
  "fields": ["Compound ID", "IC50"]                 // any result column
}
```

Send `{}` for an unfiltered scan. Example:

```bash
curl -X POST \
  "$BASE/api/v1/projects/$PROJECT/results?page-size=100" \
  -H "x-api-key: $SDF_API_KEY" -H "content-type: application/json" \
  -d '{"filters":{"attributes":{"Compound ID":"10000015"}},"fields":["Compound ID","Row ID"]}'
```

**Response** (`SearchDataByMtypeAndProjectResponse`):

```jsonc
{
  "links": { "next": "/api/v1/projects/<id>/results?page-size=2&search-id=<sid>&last-doc-id=<lastId>" },
  "meta":  { "count": 334148574, "search-id": "<guid>", "last-doc-id": "<id>" },
  "data":  [ { "type": "results", "id": "<composite>", "attributes": { … } } ]
}
```

### Pagination — cursor, not offset

The search endpoints use a **cursor**, not `limit`/`offset`:

1. First request returns `meta.search-id`, `meta.last-doc-id`, and
   `links.next` — a URL that already carries both.
2. **Follow `links.next`** until a page comes back with **no rows**. Don't wait
   for `links.next` to disappear — SDF keeps returning one past the last page.

Paging problems (verified 2026-09-15):

- **Filters are not remembered between pages; `search-id` does not store them.**
  Each page is filtered only by what that request carries. Hand-built page URLs
  (from `meta.search-id` / `meta.last-doc-id`) and `links.next` behave the same:
  - date params on page 1 only → 1,043 rows instead of 20; on every page → 20/20
  - body filter on page 1 only (later pages `{}`) → 757 rows instead of 83;
    resent every page → 83/83
  - changing the date param on page 2 applies the *new* date
  - `meta.count` keeps reporting page 1's count, so it won't flag the leak

  **Rule: send the identical body and date params on every page**, adding only
  `search-id` + `last-doc-id`. `links.next` omits the date params, so re-append
  them if you follow it. Omitting `search-id` still returned the right rows (its
  documented role is point-in-time consistency, not filtering).
- **Paging can silently lose rows.** On one sandbox project (80 rows, 78 sharing a
  microsecond-precision `timeStamp`), some page sizes dropped rows for good:
  size 1 → 74, size 3 → 78, sizes 5/7/9/79 → 79. Sizes 2/4/6/8/10/20/40 returned
  all 80. Following `links.next` past empty pages never recovered them. Two other
  projects (1,047 and 3,770 rows) paged correctly at every size tried. **Compare
  the rows you collect against `meta.count`.** If you're short, re-run with a
  `page-size` at least `meta.count` (max 10,000), or split the export into
  publication-date windows that each fit in one page.

The `search-id` pins a point in time so rows indexed mid-scan don't shift your
window. `page-size` defaults to **10000** (max 10000). *(The by-mtype
`.../data/search/measurements/{mtypeId}` endpoint calls the same parameter
`limit`, not `page-size`.)*

> The two plain list endpoints (`GET /api/v1/projects`,
> `GET /api/v1/info-design/measurement-types`) use classic `limit`/`offset`
> instead. Only the four search endpoints are cursor-based.

---

## 5. Which columns you can filter on

`filters.attributes` matches **exact values**. A result row's columns fall into
three groups:

| Kind | Examples | Filter with it? | Use in `fields`? |
|---|---|---|---|
| Measurement-type attributes | `Assay Date`, `IC50`, `Method` | ✅ yes | ✅ yes |
| Id columns | `Compound ID`, `Batch ID`, `Row ID`, `Project ID`, `Set ID` | ✅ yes | ✅ yes |
| Non-indexed columns | `Type ID`, `timeStamp` (and the envelope `id`) | ❌ **`400`** | ✅ yes |

Verified live (2026-09-15, read-only tenant; a 334M-row 2.0 project and a
legacy v1 project):

- `{"attributes":{"Compound ID":"10000015"}}` → 45 rows.
- `{"attributes":{"Method":"ChemCharts"}}` → 176,732,220 rows.
- `{"attributes":{"Type ID":"…"}}`, `timeStamp`, `id`, or a misspelled name →
  **`400 "The following attributes are not part of any measurement type: <name>"`**.
  Invalid keys fail loudly.
- A **valid key with a non-matching value** returns `200` with 0 rows and no
  error. That's the one that looks like "not found".

**The `Row ID` trap (2.0 projects).** The `Row ID` shown in 2.0 results is the
short form (`10000015-C-r565459`), but the filter matches the **indexed form
with the measurement/version suffix**: the last segment of the row's `id`
(`10000015-C-r565459-m1-v0`). Filtering on the displayed value returns 0 rows;
filtering on the suffixed form returns exactly 1. On legacy v1 projects the
displayed `Row ID` already includes the suffix (`d1-f1-m1-r2-v0`), so it
matches as shown.

Rule of thumb: anything you can't filter on, you can still **return** via
`fields`.

### Dates, operators, and case

Verified 2026-09-15 on two tenants:

- **No operators or ranges.** `{"gt": …}`, `{"$gt": …}`, `{"from","to"}`,
  `{"min","max"}`, and lists return **500**. `">2001-01-01"` and
  `"a..b"` / `"[a TO b]"` return **400**. Numbers are no different:
  `{"gt": 50}` → 400 "search query is malformed". Every filter is an exact match.
- **Date attributes need a format**, or you get `400 "Date format is required for:
  <attr>"`: `"options": { "Assay Date": { "format": "yyyy-MM-dd" } }`. Accepted
  formats: `yyyy-MM-dd`, `yyyy/MM/dd`, `dd-MM-yyyy`, `dd/MM/yyyy`, `MM-dd-yyyy`,
  `MM/dd/yyyy`, `dd.MM.yyyy`. Datetime *formats* are rejected.
- **The format controls how the filter value is parsed.** `12/03/2004` matches
  12 March under `dd/MM/yyyy` but 3 December under `MM/dd/yyyy`. A value that
  doesn't fit the format returns `400 Invalid date/time`. `yyyy-MM-dd` is the only
  format that also accepts ISO date-times (`2000-01-01T00:00:00Z`,
  `2000-01-01T00:00`, even `2000-1-1`); every other format rejects them. Use
  `yyyy-MM-dd` unless you need another input layout.
- **A date filter matches an exact instant.** A date-only value (`2016-04-21`)
  means midnight UTC. Keep `format: yyyy-MM-dd`, but pass a **full UTC timestamp
  as the value** to match anything else, e.g. `"Assay Date": "2016-04-21T01:00:00Z"`.
  Milliseconds and a missing `Z` are accepted; an offset (`+01:00`) returns 400.
  The same day at a different hour returns 0 rows. Data loaded with a time-zone
  shift (stored at `T01:00:00Z`) therefore matches only its exact timestamp.
  Read the stored value from a result first. For "after/before a date", filter
  on other attributes and compare dates client-side.
- **Text matching is case-insensitive** (`"bob"` matches `Bob`), but whole-value
  only: no partial match or `*` wildcard.
- **`options` does nothing beyond `format`.** Unknown keys (`operator`, `op`,
  `range`, `match`, `from`/`to`, `exact`, time-zone keys) are silently ignored, as
  is `format` on non-date attributes or with no matching filter. `format` also
  doesn't change how dates are returned (always ISO UTC).
- `publication-from-date` / `publication-to-date` are the only range filters.
  They return `400 "Search criteria is not compatible with legacy projects"` on
  legacy projects. See the next section.

### Publication date ranges (2.0 projects)

The query params `publication-from-date` and `publication-to-date` filter rows by
their **`timeStamp`** (publication time). Verified 2026-09-15 against full
ground truth on six 2.0 projects (sandbox and read-only tenant, 12–3,770 rows):

| Want | Params | Matches |
|---|---|---|
| After (on or after) X | `publication-from-date=X` | `timeStamp >= X` |
| Before (on or before) X | `publication-to-date=X` | `timeStamp <= X` |
| Between X and Y | both | `X <= timeStamp <= Y` (both ends inclusive) |
| Exactly one instant | `from=T&to=T` | `timeStamp == T` |

- **A date-only value is midnight UTC.** `to=2026-03-26` excludes rows published
  later that day; `from=2026-03-26&to=2026-03-26` returns nothing. For a whole
  day use `from=2026-03-26&to=2026-03-26T23:59:59.999Z` (or `to` = next day,
  which also includes rows at exactly midnight).
- **Compared at millisecond precision.** Stored stamps can carry microseconds
  (`…21.459819Z`); `from=…21.459Z` includes them.
- **ISO 8601 only.** `2026-03-20`, `…T00:00:00Z`, `…T00:00:00` (read as UTC), and
  offsets like `+01:00` all work; offsets are applied correctly. `2026/03/20`,
  `20-03-2026`, and `20/03/2026` return `400 "publication-from-date" must be in iso
  format`.
- A reversed range (`from` > `to`) returns 0 rows, not an error.
- Works on `POST …/results`, `POST …/results/{mtypeId}`, and
  `POST /api/v1/data/search/measurements/{mtypeId}` (matched ground truth on each).
  The entity endpoint `GET …/{entityName}/{entityId}/results` returned 0 rows for
  a 2.0 compound even with no date params, so it couldn't be tested.
- **Paging drops these params from `links.next`**; re-append them (see §4).

---

## 6. Row identity, and retrieving one row by id

There is **no GET-by-id endpoint** for a single result row (only `PUT`/`DELETE`
take a `{rowId}`). Row identity, from live data:

- Each row's `id` is composite, and its shape depends on the data:
  - 2.0, no batches: `{projectId}||{compoundId}||{RowID}-m{n}-v{n}`
  - 2.0, with batches: `{projectId}||{compoundId}||{batchId}||{RowID}-m{n}-v{n}`
  - legacy v1: `{typeName}||{projectName}||{compoundId}||{rowId}||{n}`
- **That composite `id` identifies exactly one row.**
- On 2.0 projects the displayed `Row ID` attribute is **not** unique: it's
  shared across a compound's measurement/version rows (45 rows for one compound
  spanned 7 distinct values).

**To fetch one row from `projectId` + its `id`:** filter `Row ID` on the id's
row segment, the one carrying the `-m{n}-v{n}` suffix:

```bash
curl -X POST "$BASE/api/v1/projects/$PROJECT/results?page-size=1" \
  -H "x-api-key: $SDF_API_KEY" -H "content-type: application/json" \
  -d '{"filters":{"attributes":{"Row ID":"10000015-C-r565459-m1-v0"}}}'
# -> meta.count 1
```

If you know the measurement type, the same filter works on the narrower
`.../results/{mtypeId}` endpoint.

For the row-write endpoints (`PUT`/`DELETE .../rows/{rowId}`), `rowId` is the
**short** form shown in results (e.g. `R1`), not the suffixed filter form.

---

## 7. Writing data (v2, asynchronous)

All writes need a **map** and go through v2. They return `202` + `publicationId`.

### a. Create a map (`POST /api/v2/maps`)

Needs `targetType` (`result`|`entity`), `targetId` (the `mtypeId` for a result
map), the id-column names, and `mappings` of `attributeId → column`. The map
also names the **unique-result-id column** (e.g. `Result ID`).

### b. Update one row (`PUT /api/v2/projects/{projectId}/results/{resultSchemaId}/rows/{rowId}`)

`resultSchemaId` = the `mtypeId`. Body is `{ mapId, data }` — and **`data` must
include the identity columns**, not just the mapped attributes:

```bash
curl -X PUT \
  "$BASE/api/v2/projects/$PROJECT/results/$MTYPE/rows/R1" \
  -H "x-api-key: $SDF_API_KEY" -H "content-type: application/json" \
  -d '{"mapId":"<mapId>","data":{
        "Compound ID":"CMPD-001","Batch ID":"CMPD-001-01","Result ID":"R1",
        "Max":"42.0","Min":"31.0"}}'
# -> 202 {"publicationId":"b7fd24db-..."}
```

Omit `Compound ID` and you get `400 "Missing required column \"Compound ID\",
required for Asset ID"`. Include: the entity ids, the map's unique-result-id
column, and the attribute columns you're changing.

### c. Other writes

- `DELETE .../results/{resultSchemaId}/rows/{rowId}` — delete a result row.
- `PUT`/`DELETE .../entities/{entityName}/rows/{rowId}` — entity rows.
- `POST /api/v2/projects/{projectId}/files` — CSV upload (`multipart/form-data`,
  needs `mapId` + column list + file). Size limits below.

### d. CSV upload limits (verified 2026-09-18, dev tenant)

- **No row limit found up to 1,000,000 rows.** 1k, 10k, 100k, 500k and 1M-row
  files (a 5-column map) each completed with every row processed, 0 errors, and
  every row searchable afterwards.
- **No fixed file-size cap found up to 75 MB.** The real limit is a **~30 s
  timeout on the whole upload request**: a 5 MB file sent slowly over 45 s was
  cut off at 30.2 s, and a 100 MB file failed only because it couldn't be sent
  in 30 s. The connection is closed with **no HTTP response** (no `413`). Long
  pauses mid-upload (several seconds) also drop it. So the practical size limit
  depends on your upload speed: here, about 3 MB/s allowed ~75 MB.
- The upload returns `202 {"data":{"publicationId"}}` once the file is received
  (0.3 s for 1k rows, 15 s for 1M / 43 MB). The import then runs asynchronously:

  | Rows | File | Upload → `COMPLETED` | Processing (report `startTime`→`endTime`) |
  |---|---|---|---|
  | 1,000 | 0.04 MB | 204 s | 89 s |
  | 10,000 | 0.4 MB | 205 s | 94 s |
  | 100,000 | 4.3 MB | 245 s | 146 s |
  | 500,000 | 21 MB | 386 s | 272 s |
  | 1,000,000 | 43 MB | 412 s | 347 s |

  Each import has ~3 minutes of fixed overhead (queue + ~90 s processing
  minimum), so even a tiny file takes minutes to appear. Many small files are
  much slower than one large one.
- The report (`reportUrl`) gives `rowsProcessed`, `rowsErrored`, `warnings`,
  `startTime` and `endTime`.
- **Recommendation:** split very large loads into files that upload in well
  under 30 s (e.g. ≤ 1M rows / ~40 MB on a typical connection), and check each
  report's `rowsProcessed` against the file's row count. The Explorer's proxy
  adds its own 60 MB / 30 s cap, so upload bigger files directly.
- `POST /api/v2/projects/{projectId}/results/{resultSchemaId}/rows` — **deprecated**;
  use `PUT` instead.

### e. Measurement types & attributes (verified 2026-09-23, dev tenant)

**You can create a measurement type by API, but you cannot give it attributes,
which makes it useless for loading data.** Define mtypes and their attributes in
the Signals UI; use the API for maps and data.

- `POST /api/v1/info-design/measurement-types` → `201`. **`linkedEntity` is
  required** even though the spec marks only `name` as required, and its value is
  **not validated** (`"NoSuchEntity"` was accepted).
- An `attributes` array is rejected on create and on `PATCH`:
  `400 "attributes" is not allowed`. `PATCH` only accepts `description`, `tags`,
  `detailsMtype`.
- The new mtype's attributes are `{"data": []}`, and **no route adds any**:
  `POST`/`PUT`/`PATCH .../measurement-types/{id}/attributes`,
  `/info-design/attributes`, `/info-design/attribute-templates` and
  `POST /info-design/entities/{entity}/attributes` all return a **bare empty
  404** (unknown route — a genuine "not found" returns a JSON message).
- Consequence: a map needs ≥1 mapping with an existing `attributeId`
  (`mappings: []` → 400), so an API-created mtype can never receive a file.
- There is **no DELETE** for measurement types, so test mtypes are permanent.
- The spec defines an `AttributeCreation` schema that **no endpoint references** —
  presumably internal or planned.

### f. Structures: SD files, SMILES and molfiles (verified 2026-09-23)

**SDF does not ingest `.sdf` (SD) files** — note the acronym clash: SDF = Signals
Data Factory; an SD file is a chemistry format.

- `POST /api/v2/projects/{projectId}/files` is delimited-text only (`delimiter`,
  `quotecharacter`, `escapecharacter`, `multiline`). It doesn't check file type:
  a real `.sdf` returned `202`, then the import **failed** with
  `Missing expected column 'Batch ID' … in file probe.sdf` (0 rows processed).
- Legacy v1 datasources accept only `delimited`, `sql`, `sas7bdat`, `xlsx`.
- **Structures do load from a delimited file**, as an *entity* attribute:
  1. `Chemical Structure` is a **Compound entity** attribute (never a result
     attribute — confirmed across three tenants).
  2. Create an entity map: `{"targetType":"entity","targetId":"Compound",
     "assetId":"Compound ID","mappings":[{"attributeId":"<structure attr id>",
     "column":"Structure"}]}`. (On create, `assetId` and `assetMapping` are
     mutually exclusive, and `type` is not accepted.)
  3. Declare the column's format in the upload's `options`, or you get
     `400 No chemical structure format specified for "<column>"`. Allowed:
     **`chemical/smiles`, `chemical/x-cdxml`, `chemical/x-cdx`,
     `chemical/x-mdl-molfile`, `protein`, `nucleotide`** (alongside the date
     formats).
  Verified: a CSV of `Compound ID,Structure` with `c1ccccc1` and
  `options={"Structure":{"format":"chemical/smiles"}}` → `COMPLETED`,
  `targetType: ENTITY`, 1 row, 0 errors, creating the compound.
  So converting SD files to SMILES (or to a quoted molfile column with
  `multiline: true`) is a working route.
- **You can't read structures back through SDF**: the search endpoints return
  result attributes only. Requesting `Chemical Structure`, `Molecular Weight` or
  `Chemical Name` in `fields` returns just `Compound ID`, on every tenant, and
  there's no GET for an entity row.
- **The Materials Library is not the only way in.** SDF creates its own
  Compound/Batch entities from an upload, and dev's `CMPD-001` exists in **no**
  material library (18 checked). For real `.sdf` files, use the **core Signals
  API**: `POST /api/rest/v1.0/materials/{libraryName}/bulkImport` takes a ZIP
  containing an SD or CSV file (async job, max 300 MiB; CSV structure columns are
  auto-detected by name: SMILES → InChI → HELM; SDF field names may not contain
  `- . < > = %` or spaces). Whether a tenant syncs a material library into SDF is
  tenant configuration — neither API exposes a sync endpoint.

---

## 8. Tracking async jobs

```bash
curl "$BASE/api/v2/projects/publication/status/$PUBLICATION_ID" \
  -H "x-api-key: $SDF_API_KEY"
```

```jsonc
{
  "publicationId": "b7fd24db-…", "projectId": "e087599a-…",
  "targetType": "RESULT", "targetId": "68b1b803…",
  "status": "COMPLETED",                         // PENDING | COMPLETED | WARNING | ERROR
  "reportUrl": "https://…/reports/<id>/final_report.json?<presigned>"
}
```

Poll until `status` is terminal. A small single-row update reaches `COMPLETED`
in seconds. `reportUrl` is a **presigned S3 URL (≈1-hour expiry)** — fetch it
for row-level detail, especially on `WARNING`/`ERROR`. Re-run a search to
confirm the change landed.

---

## 9. Errors

Most errors share the JSON envelope `{ statusCode, error, message }`:

| Code | Meaning |
|---|---|
| `400` | Bad request — malformed body, missing required column, bad filter shape |
| `403` | Authenticated but not permitted (`Forbidden` / `NotAuthorized`) |
| `404` | Project / mtype / map / row not found |
| `409` | Conflict (e.g. duplicate map/dataset) |
| `422` | Unprocessable — e.g. a map references an entity that doesn't exist |
| `500/501/502/503/504` | Server / gateway errors |

**Exception:** a missing or invalid `x-api-key` returns **`401` as plain HTML**
from the gateway, not this JSON shape (see §2). Also, a filter on a valid key
whose value doesn't match returns **`200` with 0 rows**, not an error (see §5).

---

## 10. Endpoint quick reference

**Discover:** `GET /api/v2/projects` · `GET /api/v1/projects` ·
`GET /api/v1/info-design/measurement-types` ·
`GET /api/v1/info-design/measurement-types/{mtypeId}/attributes` ·
`GET /api/v2/maps`

**Search (read-only):** `POST /api/v1/projects/{projectId}/results` ·
`POST /api/v1/projects/{projectId}/results/{mtypeId}` ·
`POST /api/v1/data/search/measurements/{mtypeId}` ·
`GET /api/v1/projects/{projectId}/{entityName}/{entityId}/results`

**Write (v2):** `POST /api/v2/maps` ·
`POST /api/v2/projects/{projectId}/files` ·
`PUT|DELETE /api/v2/projects/{projectId}/results/{resultSchemaId}/rows/{rowId}` ·
`PUT|DELETE /api/v2/projects/{projectId}/entities/{entityName}/rows/{rowId}`

**Track:** `GET /api/v2/projects/publication/status/{publicationId}`

See `sdf-openapi.yaml` for the full list (44 operations incl. datasets,
datasources, and v1/v2 maps) with parameters, bodies, and schemas.

---

## Appendix — safety when testing against live tenants

- **Writes are irreversible-ish and hit a real tenant.** Only run
  create/update/delete against a **non-production** tenant you own.
- Read (`GET`, and the search `POST`s) is always safe.
- Never commit API keys; keep them in env vars / a gitignored file and reference
  them as `$SDF_API_KEY`.
