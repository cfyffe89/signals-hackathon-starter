# REST API

Almost everything a user can do in the Signals interface, your code can do through the REST API. It's the core of most integrations — a versioned, JSON:API-based library of endpoints, fully documented in an interactive Swagger UI specific to your tenant.

**1** Overview & API docs **2** Conventions **3** Authentication **4** Rate and size limits **5** Understanding responses **6** Pagination & shaping **7** Error handling **8** Concurrent editing & digests **9** Search **10** Code snippets

## 1 · Overview & API documentation

The majority of actions users take in the Signals GUI are available in the public API. All endpoints follow the **JSON:API** standard for document structure, headers, and response codes; user and group provisioning supports **SCIM 2.0** as an optional standard integration mechanism.

Every endpoint available to you is documented in an interactive **Swagger UI** generated for your tenant. It updates in real time as new endpoints are released, and all APIs are versioned so existing integrations keep working.

Resource| Where  
---|---  
API base URL| https://<your-tenant>/api/rest/v1.0  
Interactive docs (Swagger)| https://<your-tenant>/docs/extapi/swagger/index.html  
Raw OpenAPI spec| https://<your-tenant>/docs/extapi/apidoc/v1/index.yaml  
  
The Swagger UI for a Signals tenant. Reach it via System Configuration → System Settings → API Key → "Open External API Document."

You can also open the Swagger UI from _System Configuration → System Settings → API Key → "Open External API Document."_

**Why JSON:API helps** Because responses follow a predictable structure — a primary `data` resource, its `relationships`, and an `included` array of related resources — you can reuse existing client libraries (see [jsonapi.org/implementations](https://jsonapi.org/implementations/)) and fetch related data in a single call instead of many.

## 2 · Conventions

A quick orientation that applies across every endpoint.

Convention| Detail  
---|---  
**Methods**| `GET` read · `POST` create · `PUT`/`PATCH` update · `DELETE` remove · `HEAD` (used, e.g., to poll async PDF generation).  
**Media type**|  Send and accept `application/vnd.api+json`.  
**Versioning**|  The version is in the path (`/v1.0`). Pin to a version to avoid surprises.  
**Long-running work**|  Bulk imports/exports and PDF generation run as async jobs: submit, then poll a status/`HEAD` endpoint, then fetch the result.  
  
## 3 · Authentication

Two mechanisms are supported: API keys and OAuth bearer tokens. In both cases, **the request runs with the permissions of the user the credential belongs to** — the API grants no more access than that user has in the app.

### API keys

Include the key in an `x-api-key` header. Keys are created by system administrators for a specific user, from _System Configuration → System Settings → API Key_ (select the user's email, then **Generate API Key** ; **Delete API Key** removes it). A tenant may issue up to **100** API keys.
    
    
    x-api-key: <your-api-key>

### OAuth bearer tokens

For user-attributed access your application obtains an OAuth 2.0 bearer token for the signed-in user, then sends it on every call:
    
    
    Authorization: Bearer <your_access_token>

Two flows are supported. They differ in how the token reaches your application, so choose the one that matches your architecture and security requirements.

Flow| How the token arrives| Suited to  
---|---|---  
**Implicit Grant**  
RFC 6749 §4.2 | Returned directly to your redirect URI as a URL fragment. | Simpler integrations where the token can be handled safely in the browser.  
**Authorization Code + PKCE**  
RFC 7636 | A short-lived code is returned, which your application exchanges for a token using a cryptographic proof. | Applications needing a higher security posture, or token refresh without re-authenticating the user. Recommended for public clients such as single-page and mobile applications.  
  
**Token lifetime (both flows)** A bearer token stays valid as long as it is used at least once every **30 days**. After 30 days of inactivity it is invalidated and the user must authenticate again — account for this in how your application stores and renews credentials.

#### Prerequisites for both flows

You need a **Client ID** issued by Signals. Contact Signals support to request one, providing:

  * **Application name** — the name of the application that will access Signals; any reasonably short string.
  * **Redirect URI(s)** — where your application is sent after authentication. These must match _exactly_ , so register every environment you intend to use.

Your Client ID, along with the required `response_type` and `scope` values, is supplied once registration completes.

#### Implicit Grant flow

  1. **Initiate the authorization request.** Redirect the user to `<your-tenant>/auth/oauth/authorize`, including the `response_type`, `client_id`, `scope`, and `redirect_uri` parameters.
  2. **User authentication and consent.** The user authenticates — through your identity provider if one is configured — and authorises your application.
  3. **Receive the token.** The user is redirected to your `redirect_uri` with the token appended as a URL fragment: 
         
         <redirect_uri>#access_token=<token_value>

  4. **Extract and cache it.** Parse the token from the fragment and store it securely for subsequent API calls.

#### Authorization Code + PKCE flow

PKCE extends the Authorization Code flow with a one-time cryptographic challenge tied to each request, which prevents an intercepted authorization code from being exchanged by anyone else.

  1. **Generate a code verifier.** A cryptographically random string of **43 to 128 characters**. Hold it in memory for the duration of the flow and never expose it.
  2. **Derive a code challenge.** Hash the verifier with SHA-256, then Base64URL-encode the result **without padding**. The transformation is one-way, so the challenge is safe to send over the network.
  3. **Send the authorization request** to `<your-tenant>/auth/oauth/authorize` with these parameters: 

Parameter| Value  
---|---  
response_type| `code`  
client_id| Your Client ID  
redirect_uri| Your registered redirect URI  
code_challenge| The Base64URL-encoded SHA-256 hash from step 2  
code_challenge_method| `S256`  
scope| Provided by Signals with your Client ID  
  
  4. **User authentication and consent** , as in the Implicit flow.
  5. **Handle the callback.** The user returns to your `redirect_uri` with a short-lived `code` query parameter.
  6. **Exchange the code for a token.** `POST` to the token endpoint with: 

Parameter| Value  
---|---  
grant_type| `authorization_code`  
client_id| Your Client ID  
redirect_uri| The same redirect URI used in step 3  
code| The authorization code from step 5  
code_verifier| The original random string from step 1  
  
The server confirms that the verifier hashes to the stored challenge and, if it matches, returns an access token.
  7. **Use the token** in the `Authorization` header on all subsequent requests.

**Common mistakes** **Reusing a code verifier** — generate a fresh one for every authorization request. **Using`plain` as the challenge method** — always use `S256`. **Mismatched redirect URIs** — the URI must match the registered value exactly, including trailing slashes.

### Which to use?

Use…| When| Examples  
---|---|---  
**API key**|  Server-to-server integrations with no end-user in the loop. Typically tied to a dedicated system/API user.| Automated archival, compliance dashboards, external data syncs.  
**Bearer token**|  Actions taken by a real user — especially anything that leaves an audit-trail imprint.| Sample registration from your web app, user-driven data retrieval.  
  
**Audit trail** Actions appear in the audit log as the user who owns the credential. For user-attributed changes, prefer bearer tokens so the record reflects the real person.

## 4 · Rate and size limits

### Request rate

Rate limits are enforced per tenant: up to **1,000 requests per minute** across all API keys and bearer tokens combined. (Limits may change to keep the API responsive.)

When request thresholds are exceeded, the API responds with HTTP status `429 Too Many Requests`:
    
    
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
    
    
    { "errors": [ { "status": "429", "code": "TooManyRequests", "title": "Rate limit exceeded" } ] }

**Handling rate limits** Throttle proactively on the client side, and retry on `429` using **exponential backoff with jitter**. For large jobs, prefer the bulk and asynchronous endpoints over many individual calls.

### Request and job size limits

Rate limiting caps how _often_ you may call. These limits cap how much a single call may carry — and they differ per endpoint family, so the figure that applies to searching is not the figure that applies to importing.

Operation| Limit  
---|---  
Bulk material import  
POST /materials/{library}/bulkImport | **No cap on the number of records** in one call. The constraint is the request body: **300 MiB**. Records are validated individually and the import then runs as an asynchronous job.  
Bulk material export  
POST /materials/{library}/bulkExport | **25,000 assets** or **100 MB** per job, whichever is reached first. Continue beyond that with the `nextExport` link returned in the report.  
Entity content export  
POST /entities/export/bulk| Asynchronous; the result is held for **2 hours** and may be downloaded **once**. Submissions return `429` when no export worker is free. See _Example Concepts → Bulk-exporting an experiment's contents_.  
Search result paging  
POST /entities/search | `page[limit]` up to **100** per page; `page[offset]` up to **5,000**. To retrieve more than 5,000 records, page by an immutable key instead of deep-paging — see the Search page.  
  
**The 5,000 limit applies to search paging, not to importing** `page[offset]` stops at 5,000, and that ceiling is often assumed to cap bulk imports as well. It does not: a single `bulkImport` call may carry far more than 5,000 records, bounded only by the 300 MiB body size.

## 5 · Understanding responses

A JSON:API response has three top-level parts. Fetching an experiment with `GET /entities/{eid}` returns:
    
    
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

Part| What it holds  
---|---  
data| The primary resource. Its `type`, `id`, and `attributes` describe the entity itself.  
relationships| Links and lightweight references (type + id) to related resources — creator, children, owner, a convenience `pdf` link.  
included| The full related resources referenced above, so you can resolve them without extra calls. Match a relationship's `type`+`id` to an entry here.  
  
The full response for a real experiment is large — it lists every child and the users involved — but it always follows this shape. See the next section for returning only the fields you need.

## 6 · Pagination & shaping responses

### Relationships and the `include` parameter

JSON:API relationship endpoints (such as `GET /entities`, `GET /entities/{eid}`, and `GET /users`) return relationship links pointing to parent or related resources (e.g. `ancestors`, `roles`, `members`).

  * **Default Inclusion Behavior:** When the `include` parameter is omitted, Signals automatically populates related resources in the top-level `included` array.
  * **Selective Relationships:** Passing `include=ancestors` or `include=roles` explicitly restricts the `included` section to only those requested relationship types, reducing response payload size.
  * **Endpoint Scope:** The `include` parameter is supported on standard JSON:API relationship endpoints. Search endpoints (`POST /entities/search`) do not use `include`; they return entity attributes and metadata directly within `data[].attributes`.

#### Pagination

List and search endpoints page with two query parameters:
    
    
    ?page[offset]=0&page[limit]=20     // limit max 100, default 20; offset up to 5000

Drive paging from `meta.total` in the response (the full match count), advancing `offset` until you've read `total` items. Where provided, follow the `links.next` cursor. For pulling very large sets efficiently, see the extraction pattern on the Search page.

#### Return only what you need

Use sparse fieldsets to trim response size, and `include` to pull related resources into `included` on entity fetches:
    
    
    ?fields[entity]=name,description   // only these attributes
    ?include=owner                     // add related owner to "included"

**curl & the square brackets** `[` and `]` in `page[limit]` / `fields[entity]` are wildcard characters to curl. Pass `-g` (`--globoff`) or URL-encode them, or the request silently returns nothing.

## 7 · Error handling

Signals uses standard HTTP status codes — `2xx` success, `4xx` client error, `5xx` server error. Most errors return a JSON:API `errors` array; **authentication errors return a bare object.** Handle both:
    
    
    // most errors
    { "errors": [ { "status": "404", "code": "NotFound", "title": "The requested resource was not found." } ] }
    
    // authentication errors (no "errors" wrapper)
    { "status": "401", "code": "Unauthorized", "title": "User is unauthorized",
      "detail": "No x-api-key is found in request header or the value of x-api-key is invalid." }

#### Codes you'll encounter

Status| code| When  
---|---|---  
400| BadRequest| Malformed body or query — the `detail` names the problem (missing property, unknown operator…).  
401| Unauthorized| Missing or invalid credential (bare-object shape above).  
403| PreconditionFailed| Action forbidden — e.g. editing a trashed entity, even with `force=true`.  
404| NotFound · MethodNotFound| No such entity, or the method isn't supported on that path.  
428| DigestNotMatch| Concurrent-edit conflict — see the next section.  
429| TooManyRequests| Tenant rate limit exceeded — back off and retry.  
  
## 8 · Concurrent editing & digests

Most entity responses include a `digest` — a value that changes every time the entity changes. It's how Signals detects concurrent edits and protects data integrity.

When you modify an entity via the API, include its current `digest` as a URL parameter along with your change. The server recomputes the digest for the entity's current state:

  * **Match** → you were working from the latest version; the change is applied.
  * **Mismatch** → someone else edited it since you read it; the server rejects the change with `428`:

    
    
    { "errors": [ {
        "status": "428",
        "code":   "DigestNotMatch",
        "title":  "Digest is mismatch.",
        "detail": "Failed to update entity experiment:… Precondition Required: …"
    } ] }

On a `428`, re-fetch the entity to get the latest `digest` (and current data), then re-apply your change.

Passing `force=true` in the query string bypasses standard optimistic locking digest verification for administrative force-deletions or override updates.

**Note on Race Conditions** Even when `force=true` is supplied, requests can still fail with status `428 DigestNotMatch` if a concurrent race condition occurs during multi-step parent entity mutations (for example, when parent notebook digests are recalculated simultaneously by concurrent child creation calls).

**A related mechanism for samples** Samples and compliance use a pair of hash digests — `digests.self` (the current state in Signals) and `digests.external` (the state your system last acknowledged) — to track whether an external registration is up to date. See _Example Concepts & Workflows_ and the chemistry tutorial.

## 9 · Search

The `POST /entities/search` endpoint is how you find and extract exactly the data you need — from one experiment to a full incremental sync. It takes a JSON `query` tree and returns matching entities.
    
    
    POST /api/rest/v1.0/entities/search
    { "query": { "$and": [
        { "$match": { "field": "type", "value": "experiment", "mode": "keyword" } },
        { "$match": { "field": "isTemplate", "value": false } }
    ] } }

Search has its own page covering the query language, the field/tag model, relationship traversal, full-text search, and large-scale extraction. **→ SeeSearch.**

## 10 · Code snippets

An authenticated call to fetch the most recently modified experiments.

#### Python (requests)
    
    
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

#### JavaScript (fetch)
    
    
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

**Tip** The Swagger UI (§1) can generate example requests, and the raw OpenAPI spec can be imported into Postman or used to generate a typed client.
