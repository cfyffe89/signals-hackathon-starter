<!-- 
Signals EMEA Hackathon 2026 Reference Guide (Distilled Markdown)
Architecture Notice: Use FastAPI (backend) & Streamlit (UI). Do NOT copy legacy Flask patterns.
-->


# Overview

Welcome. Signals is an electronic data-capture and management application built on a resilient, scalable cloud architecture. This guide shows you how to extend it — reading and writing data, reacting to events, and connecting your own systems.

## Introduction

Signals is delivered as a SaaS application and updated frequently with minimal disruption to end-users. This documentation walks through the principles, concepts, and components you'll use to build integrations — from a one-off script to a fully automated data pipeline.

If you're here to do something specific, the table below points you straight to the right component and page. If you're new to Signals, read on through Core Concepts first.

## What you can build

Signals offers four integration surfaces. Most real solutions combine several — but you can start with just one.

| I want to… | Use | Learn more |

| Read or write Signals data from my own application | REST API | REST API |

| Find or extract specific entities (and keep an external copy in sync) | Search | Search |

| Add a button in Signals that opens my web app for a custom workflow | External Actions | External Actions |

| React automatically when users sign, create, or export records | External Notifications | External Notifications |

| Populate dropdowns or table rows from my systems of record | External Lists & Data Sources | External Data Sources & Lists |

## Before you start

A few facts that get you to a first successful call. Full details live on the REST API page.

| What | Value |

| API base URL | https://<your-tenant>/api/rest/v1.0 |

| Interactive API docs | Swagger UI at `https://<your-tenant-url>/docs/extapi/swagger/index.html` — test endpoints live in your browser. Reach it via System Configuration → System Settings → API Key → "Open External API Document." |

| OpenAPI Specification | Download the complete OpenAPI 3.0 specification file (`openapi.yaml`) directly from Signals Notebook under System Configuration → System Settings → API Key → "Open External API Document" by clicking the Download button next to it. |

| Authentication | An API key in the `x-api-key` header (server-to-server), or an OAuth bearer token (user-attributed actions). Keys are generated in System Settings → API Key. |

| Versioning | APIs are versioned (`v1.0`); new endpoints appear in the Swagger UI as they're released, so existing integrations keep working. |

Verifying your credentials To confirm a key is working, call `GET /api/rest/v1.0/version`, which returns the release, or `GET /api/rest/v1.0/profiles/me`, which returns the user the key belongs to.

## General Principles

These principles guide how the integration surfaces are designed — and how we suggest you approach building on them.

Simple should be simple. Common use cases built on well-defined APIs should be straightforward to implement.
Supportability. Integrations, however complex, should never impede the supportability of the application.
Don't mess with what isn't broken. Existing systems shouldn't need major changes to serve a specific integration.
Future vision. Integration is central to a transformative future — automatic data capture, data pipelining, and more.
Adherence to standards. Experienced developers should find the technology familiar, lowering the barrier to implementation.

## Core Concepts · Entities

In Signals Notebook, nearly everything you interact with is an Entity — from top-level Notebooks and Experiments down to an individual text element or table. Every entity has a unique identifier, referred to as its Entity ID, eid, or simply id. You'll use these constantly to address specific entities through the API.

An Entity ID is a `type:uuid` string. For example, an experiment:

```python
experiment:03ae2d17-e94d-466a-ba83-94d89a3cea2f
```

### Common entities and their internal types

The `type` prefix in an eid — and the `type` you filter on in Search — uses these internal names:

| Area | Entity | Internal type |

| Notebook & experiment | Notebook | journal |

| Experiment | experiment |

| Text element | text |

| Worksheet | worksheet |

| Tables | Admin Defined Table | grid |

| Materials Table | materialsTable |

| Variations Table | variationsGrid |

| Hierarchical Table | hierarchicalGrid |

| Chemistry | Chemical Drawing | chemicalDrawing |

| Samples & inventory | Sample | sample |

| Samples container (in an experiment) | samplesContainer |

| Inventory container | container |

| Inventory asset / batch / material library | asset · batch · assetType |

| Plates | Plate | plate |

| Plate map | plateMap |

| Biopolymers | Monomer | monomer |

| Monomer library | monomerLibrary |

| Tasks | Task | task |

| Task container | taskContainer |

| Files & analysis | Image | imageResource |

| Uploaded file | uploadedResource |

| Spotfire for Signals | signals_spotfiredxp |

This is the common set, and your tenant may hold others. To list the types that actually exist in your tenant, ask the Search API for the distinct values of the `type` field. The `/entities/search/terms` endpoint returns each value with a count rather than returning the entities themselves:

```python
POST /api/rest/v1.0/entities/search/terms

{
  "query": { "$match": { "field": "isTemplate", "value": false } },
  "field": "type"
}
```

```python
// each entry is a type present in your tenant, with how many exist
{ "data": [
    { "attributes": { "term": "monomer",         "count": 1256 } },
    { "attributes": { "term": "sample",          "count": 270  } },
    { "attributes": { "term": "chemicalDrawing", "count": 253  } },
    { "attributes": { "term": "experiment",      "count": 111  } }
] }
```

The same endpoint works on any field, so it is also the way to discover the values in use for a custom field. See the Search page for the full query language.

### Finding an Entity's ID

You can get an eid three ways:

* From an API response — most calls return entities with their `id` in the `data` object. See the REST API page for how responses are structured.

* From the app — open the entity in Signals; its eid appears in the browser URL.

* By searching — `POST /entities/search` returns matching entities and their ids. See the Search page.

## Key terms

A few terms recur throughout the guide — worth knowing up front.

Entity / eidAny addressable object in Signals, and its unique `type:uuid` identifier.
digestA version stamp on an entity. Send it back on an update so the server can detect if someone else changed the entity in the meantime.
templateA reusable blueprint an entity was created from. Real content has `isTemplate: false` — most queries filter templates out.
stateAn entity's workflow status, e.g. `open` or `closed`.
fields / tagsAn entity's named data values. In search responses these are exposed as searchable tags.

## System Configuration

Administrators configure a tenant — including every integration point in this guide — from the System Configuration area, reached at your tenant's URL. Setting up External Actions, Notifications, and Data Sources requires administrator access.

Step-by-step setup for those features lives in the System Configuration Guide, opened from the drop-down menu within System Configuration. This developer guide focuses on what your code does; the configuration guide covers the admin screens.

## External Servers & architecture

Most integrations run through an external server you host — a bridge between Signals' APIs and your own systems. It's where you handle authentication, transform data between formats, and orchestrate multi-step workflows, keeping that complexity out of Signals itself.

An external server typically lets you:

* Exchange data with Signals via the REST API and push it downstream into your digital lab.

* Receive events from External Notifications and trigger automated workflows.

* Serve data to Signals as External Lists and Data Sources, in the shape Signals expects.

* Authenticate and authorize access, so only permitted users and applications reach sensitive data.

### How it fits together

Signals
SaaS cloud

Your External
Server

LIMS

Registry

Data lake / BI

REST API

External Actions

Notifications

Lists & Data Sources

Signals reaches your external server through four channels; your server bridges to your own systems of record.

A fuller solution uses several channels together. For example: an External List keeps project codes current in Signals; an External Data Source pulls instrument metadata into a table by barcode; an External Action registers a sample in your LIMS; and a Notification handler archives an experiment automatically when it's signed and closed.

## Where to go next

REST API →Authentication, responses, digests, error handling.
Search →Find and extract exactly the data you need.
External Actions →Launch your app from a button in Signals.
External Notifications →React automatically to Signals events.
External Data Sources & Lists →Feed dropdowns and tables from your systems.
Tutorials →End-to-end, hands-on walkthroughs.

---

# REST API

Almost everything a user can do in the Signals interface, your code can do through the REST API. It's the core of most integrations — a versioned, JSON:API-based library of endpoints, fully documented in an interactive Swagger UI specific to your tenant.

1Overview & API docs
2Conventions
3Authentication
4Rate and size limits
5Understanding responses
6Pagination & shaping
7Error handling
8Concurrent editing & digests
9Search
10Code snippets

## 1 · Overview & API documentation

The majority of actions users take in the Signals GUI are available in the public API. All endpoints follow the JSON:API standard for document structure, headers, and response codes; user and group provisioning supports SCIM 2.0 as an optional standard integration mechanism.

Every endpoint available to you is documented in an interactive Swagger UI generated for your tenant. It updates in real time as new endpoints are released, and all APIs are versioned so existing integrations keep working.

| Resource | Where |

| API base URL | https://<your-tenant>/api/rest/v1.0 |

| Interactive docs (Swagger) | https://<your-tenant>/docs/extapi/swagger/index.html |

| Raw OpenAPI spec | https://<your-tenant>/docs/extapi/apidoc/v1/index.yaml |

The Swagger UI for a Signals tenant. Reach it via System Configuration → System Settings → API Key → "Open External API Document."

You can also open the Swagger UI from System Configuration → System Settings → API Key → "Open External API Document."

Why JSON:API helps Because responses follow a predictable structure — a primary `data` resource, its `relationships`, and an `included` array of related resources — you can reuse existing client libraries (see jsonapi.org/implementations) and fetch related data in a single call instead of many.

## 2 · Conventions

A quick orientation that applies across every endpoint.

| Convention | Detail |

| Methods | `GET` read · `POST` create · `PUT`/`PATCH` update · `DELETE` remove · `HEAD` (used, e.g., to poll async PDF generation). |

| Media type | Send and accept `application/vnd.api+json`. |

| Versioning | The version is in the path (`/v1.0`). Pin to a version to avoid surprises. |

| Long-running work | Bulk imports/exports and PDF generation run as async jobs: submit, then poll a status/`HEAD` endpoint, then fetch the result. |

## 3 · Authentication

Two mechanisms are supported: API keys and OAuth bearer tokens. In both cases, the request runs with the permissions of the user the credential belongs to — the API grants no more access than that user has in the app.

### API keys

Include the key in an `x-api-key` header. Keys are created by system administrators for a specific user, from System Configuration → System Settings → API Key (select the user's email, then Generate API Key; Delete API Key removes it). A tenant may issue up to 100 API keys.

```python
x-api-key: 85DP8xx5hg0uvYNOghhkFGmSCWmBbc4neLs9fD3Iy7lW…
```

### OAuth bearer tokens

For user-attributed access your application obtains an OAuth 2.0 bearer token for the signed-in user, then sends it on every call:

```python
Authorization: Bearer <your_access_token>
```

Two flows are supported. They differ in how the token reaches your application, so choose the one that matches your architecture and security requirements.

| Flow | How the token arrives | Suited to |

| Implicit GrantRFC 6749 §4.2 | Returned directly to your redirect URI as a URL fragment. | Simpler integrations where the token can be handled safely in the browser. |

| Authorization Code + PKCERFC 7636 | A short-lived code is returned, which your application exchanges for a token using a cryptographic proof. | Applications needing a higher security posture, or token refresh without re-authenticating the user. Recommended for public clients such as single-page and mobile applications. |

Token lifetime (both flows)
    A bearer token stays valid as long as it is used at least once every 30 days. After 30 days of inactivity it is invalidated and the user must authenticate again — account for this in how your application stores and renews credentials.

#### Prerequisites for both flows

You need a Client ID issued by Signals. Contact Signals support to request one, providing:

* Application name — the name of the application that will access Signals; any reasonably short string.

* Redirect URI(s) — where your application is sent after authentication. These must match exactly, so register every environment you intend to use.

Your Client ID, along with the required `response_type` and `scope` values, is supplied once registration completes.

#### Implicit Grant flow

* Initiate the authorization request. Redirect the user to `<your-tenant>/auth/oauth/authorize`, including the `response_type`, `client_id`, `scope`, and `redirect_uri` parameters.

* User authentication and consent. The user authenticates — through your identity provider if one is configured — and authorises your application.

* Receive the token. The user is redirected to your `redirect_uri` with the token appended as a URL fragment:
        
```python
<redirect_uri>#access_token=<token_value>
```

* Extract and cache it. Parse the token from the fragment and store it securely for subsequent API calls.

#### Authorization Code + PKCE flow

PKCE extends the Authorization Code flow with a one-time cryptographic challenge tied to each request, which prevents an intercepted authorization code from being exchanged by anyone else.

* Generate a code verifier. A cryptographically random string of 43 to 128 characters. Hold it in memory for the duration of the flow and never expose it.

* Derive a code challenge. Hash the verifier with SHA-256, then Base64URL-encode the result without padding. The transformation is one-way, so the challenge is safe to send over the network.

* Send the authorization request to `<your-tenant>/auth/oauth/authorize` with these parameters:
        
ParameterValue

response_type`code`
client_idYour Client ID
redirect_uriYour registered redirect URI
code_challengeThe Base64URL-encoded SHA-256 hash from step 2
code_challenge_method`S256`
scopeProvided by Signals with your Client ID

* User authentication and consent, as in the Implicit flow.

* Handle the callback. The user returns to your `redirect_uri` with a short-lived `code` query parameter.

* Exchange the code for a token. `POST` to the token endpoint with:
        
ParameterValue

grant_type`authorization_code`
client_idYour Client ID
redirect_uriThe same redirect URI used in step 3
codeThe authorization code from step 5
code_verifierThe original random string from step 1

        The server confirms that the verifier hashes to the stored challenge and, if it matches, returns an access token.

* Use the token in the `Authorization` header on all subsequent requests.

Common mistakes
Reusing a code verifier — generate a fresh one for every authorization request.
    Using `plain` as the challenge method — always use `S256`.
    Mismatched redirect URIs — the URI must match the registered value exactly, including trailing slashes.

### Which to use?

| Use… | When | Examples |

| API key | Server-to-server integrations with no end-user in the loop. Typically tied to a dedicated system/API user. | Automated archival, compliance dashboards, external data syncs. |

| Bearer token | Actions taken by a real user — especially anything that leaves an audit-trail imprint. | Sample registration from your web app, user-driven data retrieval. |

Audit trail Actions appear in the audit log as the user who owns the credential. For user-attributed changes, prefer bearer tokens so the record reflects the real person.

## 4 · Rate and size limits

### Request rate

Rate limits are enforced per tenant: up to 1,000 requests per minute across all API keys and bearer tokens combined. (Limits may change to keep the API responsive.)

When request thresholds are exceeded, the API responds with HTTP status `429 Too Many Requests`:

```python
{
  "errors": [
    {
      "status": "429",
      "code": "TooManyRequests",
      "title": "Too Many Requests",
      "detail": "Rate limit exceeded. Please retry after waiting."
    }
  ]
}
```

```python
{ "errors": [ { "status": "429", "code": "TooManyRequests", "title": "Rate limit exceeded" } ] }
```

Handling rate limits Throttle proactively on the client side, and retry on `429` using exponential backoff with jitter. For large jobs, prefer the bulk and asynchronous endpoints over many individual calls.

### Request and job size limits

Rate limiting caps how often you may call. These limits cap how much a single call may carry — and they differ per endpoint family, so the figure that applies to searching is not the figure that applies to importing.

| Operation | Limit |

| Bulk material importPOST /materials/{library}/bulkImport | No cap on the number of records in one call. The constraint is the request body: 300 MiB. Records are validated individually and the import then runs as an asynchronous job. |

| Bulk material exportPOST /materials/{library}/bulkExport | 25,000 assets or 100 MB per job, whichever is reached first. Continue beyond that with the `nextExport` link returned in the report. |

| Entity content exportPOST /entities/export/bulk | Asynchronous; the result is held for 2 hours and may be downloaded once. Submissions return `429` when no export worker is free. See Example Concepts → Bulk-exporting an experiment's contents. |

| Search result pagingPOST /entities/search | `page[limit]` up to 100 per page; `page[offset]` up to 5,000. To retrieve more than 5,000 records, page by an immutable key instead of deep-paging — see the Search page. |

The 5,000 limit applies to search paging, not to importing
`page[offset]` stops at 5,000, and that ceiling is often assumed to cap bulk imports as well. It does not: a single `bulkImport` call may carry far more than 5,000 records, bounded only by the 300 MiB body size.

## 5 · Understanding responses

A JSON:API response has three top-level parts. Fetching an experiment with `GET /entities/{eid}` returns:

```python
{
  "links": { "self": "…/entities/experiment:966a7304-…" },
  "data": {
    "type": "entity",
    "id": "experiment:966a7304-4436-4f84-b56b-053c2ba2e439",
    "attributes": {
      "name": "My First Signals Experiment",
      "type": "experiment", "state": "open", "digest": "72378008",
      "createdAt": "2024-01-22T21:17:12.334Z", "editedAt": "…",
      "fields": { "Name": { "value": "My First Signals Experiment" } }
    },
    "relationships": {
      "createdBy": { "data": { "type": "user", "id": "100" } },
      "children":  { "data": [ { "type": "entity", "id": "text:1884…" }, … ] }
    },
  },
  "included": [ { "type": "user", "id": "100", "attributes": { "email": "…" } }, … ]
}
```

| Part | What it holds |

| data | The primary resource. Its `type`, `id`, and `attributes` describe the entity itself. |

| relationships | Links and lightweight references (type + id) to related resources — creator, children, owner, a convenience `pdf` link. |

| included | The full related resources referenced above, so you can resolve them without extra calls. Match a relationship's `type`+`id` to an entry here. |

The full response for a real experiment is large — it lists every child and the users involved — but it always follows this shape. See the next section for returning only the fields you need.

## 6 · Pagination & shaping responses

### Relationships and the `include` parameter

JSON:API relationship endpoints (such as `GET /entities`, `GET /entities/{eid}`, and `GET /users`) return relationship links pointing to parent or related resources (e.g. `ancestors`, `roles`, `members`).

* Default Inclusion Behavior: When the `include` parameter is omitted, Signals automatically populates related resources in the top-level `included` array.

* Selective Relationships: Passing `include=ancestors` or `include=roles` explicitly restricts the `included` section to only those requested relationship types, reducing response payload size.

* Endpoint Scope: The `include` parameter is supported on standard JSON:API relationship endpoints. Search endpoints (`POST /entities/search`) do not use `include`; they return entity attributes and metadata directly within `data[].attributes`.

#### Pagination

List and search endpoints page with two query parameters:

```python
?page[offset]=0&page[limit]=20     // limit max 100, default 20; offset up to 5000
```

Drive paging from `meta.total` in the response (the full match count), advancing `offset` until you've read `total` items. Where provided, follow the `links.next` cursor. For pulling very large sets efficiently, see the extraction pattern on the Search page.

#### Return only what you need

Use sparse fieldsets to trim response size, and `include` to pull related resources into `included` on entity fetches:

```python
?fields[entity]=name,description   // only these attributes
?include=owner                     // add related owner to "included"
```

curl & the square brackets `[` and `]` in `page[limit]` / `fields[entity]` are wildcard characters to curl. Pass `-g` (`--globoff`) or URL-encode them, or the request silently returns nothing.

## 7 · Error handling

Signals uses standard HTTP status codes — `2xx` success, `4xx` client error, `5xx` server error. Most errors return a JSON:API `errors` array; authentication errors return a bare object. Handle both:

```python
// most errors
{ "errors": [ { "status": "404", "code": "NotFound", "title": "The requested resource was not found." } ] }

// authentication errors (no "errors" wrapper)
{ "status": "401", "code": "Unauthorized", "title": "User is unauthorized",
  "detail": "No x-api-key is found in request header or the value of x-api-key is invalid." }
```

#### Codes you'll encounter

| Status | code | When |

| 400 | BadRequest | Malformed body or query — the `detail` names the problem (missing property, unknown operator…). |

| 401 | Unauthorized | Missing or invalid credential (bare-object shape above). |

| 403 | PreconditionFailed | Action forbidden — e.g. editing a trashed entity, even with `force=true`. |

| 404 | NotFound · MethodNotFound | No such entity, or the method isn't supported on that path. |

| 428 | DigestNotMatch | Concurrent-edit conflict — see the next section. |

| 429 | TooManyRequests | Tenant rate limit exceeded — back off and retry. |

## 8 · Concurrent editing & digests

Most entity responses include a `digest` — a value that changes every time the entity changes. It's how Signals detects concurrent edits and protects data integrity.

When you modify an entity via the API, include its current `digest` as a URL parameter along with your change. The server recomputes the digest for the entity's current state:

* Match → you were working from the latest version; the change is applied.

* Mismatch → someone else edited it since you read it; the server rejects the change with `428`:

```python
{ "errors": [ {
    "status": "428",
    "code":   "DigestNotMatch",
    "title":  "Digest is mismatch.",
    "detail": "Failed to update entity experiment:… Precondition Required: …"
} ] }
```

On a `428`, re-fetch the entity to get the latest `digest` (and current data), then re-apply your change.

Passing `force=true` in the query string bypasses standard optimistic locking digest verification for administrative force-deletions or override updates.

Note on Race Conditions
    Even when `force=true` is supplied, requests can still fail with status `428 DigestNotMatch` if a concurrent race condition occurs during multi-step parent entity mutations (for example, when parent notebook digests are recalculated simultaneously by concurrent child creation calls).
A related mechanism for samples Samples and compliance use a pair of hash digests — `digests.self` (the current state in Signals) and `digests.external` (the state your system last acknowledged) — to track whether an external registration is up to date. See Example Concepts & Workflows and the chemistry tutorial.

## 9 · Search

The `POST /entities/search` endpoint is how you find and extract exactly the data you need — from one experiment to a full incremental sync. It takes a JSON `query` tree and returns matching entities.

```python
POST /api/rest/v1.0/entities/search
{ "query": { "$and": [
    { "$match": { "field": "type", "value": "experiment", "mode": "keyword" } },
    { "$match": { "field": "isTemplate", "value": false } }
] } }
```

Search has its own page covering the query language, the field/tag model, relationship traversal, full-text search, and large-scale extraction. → See Search.

## 10 · Code snippets

An authenticated call to fetch the most recently modified experiments.

#### Python (requests)

```python
import requests

BASE = "https://your-tenant/api/rest/v1.0"
HEADERS = {"x-api-key": "YOUR_KEY", "Content-Type": "application/vnd.api+json"}

r = requests.post(
    f"{BASE}/entities/search",
    headers=HEADERS,
    params={"page[limit]": 20},
    json={"query": {"$match": {"field": "type", "value": "experiment", "mode": "keyword"}},
          "options": {"sort": {"modifiedAt": "desc"}}},
)
r.raise_for_status()
for e in r.json()["data"]:
    print(e["id"], e["attributes"]["name"])
```

#### JavaScript (fetch)

```python
const BASE = "https://your-tenant/api/rest/v1.0";
const res = await fetch(`${BASE}/entities/search?page[limit]=20`, {
  method: "POST",
  headers: { "x-api-key": "YOUR_KEY", "Content-Type": "application/vnd.api+json" },
  body: JSON.stringify({
    query: { $match: { field: "type", value: "experiment", mode: "keyword" } },
    options: { sort: { modifiedAt: "desc" } },
  }),
});
const { data } = await res.json();
data.forEach(e => console.log(e.id, e.attributes.name));
```

Tip The Swagger UI (§1) can generate example requests, and the raw OpenAPI spec can be imported into Postman or used to generate a typed client.