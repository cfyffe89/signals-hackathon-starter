<!-- 
Signals EMEA Hackathon 2026 Reference Guide (Distilled Markdown)
Architecture Notice: Use FastAPI (backend) & Streamlit (UI). Do NOT copy legacy Flask patterns.
-->


# External Actions

External Actions add a button to Signals that opens your web application, passing along the entity the user is working on. They're how you extend Signals with custom, user-driven workflows — sample registration, compliance checks, external lookups — without leaving the notebook.

1Overview
2Where actions appear
3Passing data: GET vs POST
4Configuration
5Triggers & availability
6Authentication & security
7Dialog messages
8Example & next steps

## 1 · Overview

An administrator configures an External Action for a given entity type and sets a URL. Signals adds a button (with an icon you choose) to that entity's interface. When a user clicks it, Signals opens your URL — in a dialog or a new window — passing an identifier for the entity in play. Your page then does the work and, if it needs to, calls back into Signals via the REST API.

A typical sample-registration flow:

* The user clicks a Register button on a Sample.

* Your page opens with the Sample's entity id.

* Your page calls the Signals API to read the sample's details.

* Your page registers the sample in your external system, then writes the result back to Signals.

## 2 · Where actions appear

External Actions can be attached to a wide range of entity types — each configured action becomes a button on that entity. The supported types are:

Chemical DrawingCollectionDesigns TableExcelExperimentFormulation ExperimentHierarchical TableMaterials TableNotebookParallel ExperimentPDFPlatesPowerPointRequestSampleSample SummarySamples TableSubexperimentSubexperiment SummarySynergy ExperimentTableTaskVariations TableWordWork OrderWorksheetFolders

In System Configuration, actions are grouped by entity type and each can be activated, given an icon, and ordered relative to other actions on the same entity.

## 3 · Passing data: GET vs POST

You choose how the entity's information reaches your page. During setup you also choose the parameter name that carries the id — the default is `__eid`.

|  | GET | POST |

| How data arrives | Entity id in a URL query parameter. | Full entity object in the request body. |

| Best for | Simple, view-style actions where the id is enough. | Actions needing the entity's attributes/ancestors up front, or multi-entity (folder) actions. |

| Example | …/?__eid=experiment:03ae2d17-… | JSON body (below) |

#### GET

```python
https://yourapplication.com/?__eid=experiment:03ae2d17-e94d-466a-ba83-94d89a3cea2f
```

#### POST body (an Admin Defined Table)

```python
{ "data": {
    "id": "grid:8a9b9331-…", "type": "grid",
    "attributes": { "name": "Data Table", "digest": "76541692", … },
    "relationships": { "ancestors": [
        { "data": { "id": "journal:b3f1335e-…", "type": "journal" } },
        { "data": { "id": "experiment:9247c379-…", "type": "experiment" } }
    ] }
} }
```

Folders An action on a Folder receives an array of these objects — one per selected entity — and therefore must use POST.

## 4 · Configuration

Administrators create actions in System Configuration → External Actions → Create External Action. The form:

| Field | What it does |

| Name · Description | Label for the button/action (required) and optional notes. |

| URL | The endpoint Signals opens (required). |

| Submit method | `HTTP GET` or `HTTP POST` (see §3). |

| Parameter name | The query-parameter name that carries the entity id — default `__eid`. |

| Apply to | The entity type this action attaches to (see §2). |

| Apply to all templates | For template-based entities, make it available on every template or specific ones. |

| Trigger | `User Action` and, where supported, `Signing Event` (see §5). |

| Open in a dialog | On: opens in an in-app modal (enables dialog messages, §7). Off: opens a new browser window. |

| Require write access | Only users with write access to the entity can use the action. |

System Configuration → External Actions → Create External Action.
Validating the configuration The form's Test control exercises the configured URL before you save. Every field above is documented on this page; the System Configuration Guide covers the administrative procedure and the permissions needed to reach these screens.

## 5 · Triggers & availability

By default, actions are triggered by a User Action (the button click). Some entities support more:

| Entity kind | Extra availability control |

| Signable entities (Experiments, Parallel Experiments, Admin Defined Objects) | Signing Event trigger — fire the action on one or more signing events (e.g. Sign and Close). Enables signing flow control (§7). |

| Template-based entities (Tables, Worksheets) | Apply to all templates, or only chosen templates. |

| Samples | Make the action available only for chosen sample statuses. |

| Folders | Restrict to specific folders (and remember: POST only). |

## 6 · Authentication & security

An External Action is just a redirect to your URL — anyone who has that URL has the same access, and Signals can't see who follows it. Secure your own site accordingly, and authenticate users before doing anything sensitive.

The recommended pattern gives your page authenticated access to the Signals API as the acting user:

* Authenticate at your app — via your own credentials, VPN, or intranet. Skippable if the user is already behind your firewall.

* Bearer token exchange — redirect the user through the Signals OAuth flow; on success they return to your `redirect_url` with a bearer token (SSO governs whether they re-enter credentials). Use Authorization Code with PKCE for new integrations, since an External Action page is a public client.

* Call the API — your page now holds a token scoped to that user's permissions and can read/write Signals on their behalf.

Notes Signals is secured via IP whitelisting, so API access is controlled regardless of where the user is. See the REST API page for bearer-token setup (client id + redirect URIs are requested through Signals support).

## 7 · Dialog messages

When an action opens in a dialog, Signals listens for commands from your page sent via `window.postMessage`. Use them to resize or title the dialog, refresh the entity, and — during signing events — control whether the sign proceeds.

Each command is an array of `[commandName, [args]]`, posted to the modal's parent window at the Signals origin:

```python
window.parent.postMessage(
  ['closeAndContinue', []],
  'https://<your-tenant>/' // the Signals origin — targets the command precisely
)
```

#### Supported commands

| Command | Format | What it does |

| close | ['close', [status]] | Closes the dialog. `status` (boolean, optional, default `true`): when `true`, Signals continues its current flow — refreshing the entity the action was triggered from, and proceeding with a signing transition. When `false`, the entity is not refreshed and the signing transition is aborted. |

| closeAndContinue | ['closeAndContinue', []] | Closes the dialog as if `close` had been issued with `true`. |

| closeAndAbort | ['closeAndAbort', []] | Closes the dialog as if `close` had been issued with `false`. |

| setTitle | ['setTitle', [newTitle]] | Sets the dialog title, which otherwise defaults to the name of the action. `newTitle` (string) — HTML is escaped. |

| setWidth | ['setWidth', [newWidth]] | Sets the dialog width as a percentage of the parent window; the height adjusts automatically to maintain the aspect ratio. `newWidth` accepts multiples of ten (10, 20, 30…), thirds (33 and 67, with 66 accepted as an alias for 67), quarters (25, 50, 75), or the string `'phi'`, which sets the width to 61.8% — the golden section of the parent window. |

Two things to note
    A command that takes no arguments must still be given an empty array. And refreshing the entity is not a separate command — it is what `close` does when `status` is `true`, which is also why `closeAndContinue` refreshes and `closeAndAbort` does not.
Example use On a Sign-and-Close signing event, your page can call the API to verify required content, then post `closeAndContinue` if it's present or `closeAndAbort` (with a message to the user) if it isn't — enforcing a compliance check at signing time.

## 8 · Example & next steps

Signals
entity + action button

Your web
application

Your systems
LIMS / registry
1 - opens URL (__eid)

3 - REST API (bearer)

4 - postMessage result

2 - your logic

A user-triggered External Action: Signals opens your application with the entity id; your application calls back through the REST API and returns control with a dialog message.

A minimal dialog action reads the entity id, does its work, and hands control back:

```python
// 1. read the entity id Signals passed in
const eid = new URLSearchParams(location.search).get("__eid");

// 2. …call the Signals REST API with the user's bearer token, do the work…
// 3. hand control back to Signals
window.parent.postMessage(["closeAndContinue", []], "https://your-tenant/");
```

For a complete, runnable walkthrough — a Flask app that validates chemistry at signing time — see the tutorial External Checking for Chemical Drawings. To read or write entity data from your page, see the REST API and Search pages.

---

# External Notifications

Notifications let your systems react to what happens in Signals — an experiment signed, an entity created, a record exported — without anyone clicking a thing. Subscribe to events, and your workflows kick off automatically.

1Overview: push & pull
2Setup
3Triggers & types
4The notification object
5Push notifications
6Pull notifications
7Limits
8Reliability

## 1 · Overview: push and pull

An administrator configures which events publish notifications. There are two ways to consume them:

|  | Push | Pull |

| How | Signals sends each notification to a URL you host, as it happens. | You fetch notifications from the Signals REST API on your schedule. |

| Best for | Real-time reactions. | Catching up on anything you missed, and reconciliation. |

The two are complementary. Consider an archival integration: it's subscribed via push, so when a user signs and closes an experiment it immediately fetches a PDF and archives it. If that service was offline for a while, it uses pull to retrieve everything it missed and mark those handled. We recommend using both — see §8.

## 2 · Setup

An administrator enables External Notifications and selects which events to publish. During setup:

* Push URL & auth — configure the single URL that receives pushes, plus an HTTP header name and value (e.g. an API key) that Signals will send on every request so your endpoint can verify the call is genuine.

* Auto-dismissal — optionally, a notification delivered by push is marked dismissed automatically once your server returns any `2XX`. This sets the `isDismissed` flag to `true` (it doesn't delete anything — dismissed notifications remain queryable).

The fields you configure are described above. The System Configuration Guide covers the administrative procedure and the permissions needed to reach these screens.

## 3 · Triggers & notification types

Three trigger families can be enabled. Each notification's `type` attribute tells you exactly what happened:

| Trigger | Event | type |

| Top-level entity creation | Entity created (Notebook, Experiment, Request, Parallel/Sub Experiment, Admin Defined Object, Sample, Task, Material) | create |

| Export to PDF/ZIP | Print / ZIP export | print |

| All signing events | Sign and Close | close |

| Sign and Keep Open | sign |

| Close Without Signing | close_without_signing |

| Reopen | reopen |

| Request Reviewer | review_request_for_reviewer |

| Request Two-Stage Review | two_stage_review_request_for_reviewer |

| Reviewer Request Accepted / Rejected | review_accepted_for_owner · review_rejected_for_owner |

| First Review Accepted / Rejected | first_review_accepted_for_owner · first_review_rejected_for_owner |

| Second Review Accepted / Rejected | second_review_accepted_for_owner · second_review_rejected_for_owner |

| Archive | archive |

| Return From Archive | unarchive |

| Void | void |

| (review variants fire for the relevant reviewer/owner role) |

## 4 · The notification object

Notifications follow the same JSON:API shape as other responses. The `relationships` and `included` give you the user and entity involved; the key details are in `attributes`:

```python
{ "data": {
    "type": "notification", "id": "519",
    "attributes": {
      "id": "519", "type": "close", "createdAt": "2023-12-13T20:42:50.427Z",
      "isDismissed": true, "isRead": false, "isFlagged": false,
      "comment": "This experiment was a success"
    },
    "relationships": {
      "createdBy": { "data": { "type": "user", "id": "100" } },
      "entity":    { "data": { "type": "entity", "id": "experiment:d5dc8e92-…" } }
    }
  }
}
```

| Attribute | Meaning |

| id | Notification id — use it to fetch or update this notification. |

| type | Which event occurred (see §3). |

| createdAt | When the triggering event happened. |

| isDismissed | Handled? Set by auto-dismissal on push, or via the API. |

| isRead · isFlagged | Your own bookkeeping flags, set via the API. |

| comment | The signing comment for signing events; `null` where not applicable (e.g. creation, export). |

#### Endpoints

| Method | Path | Purpose |

| GET | /notifications | List, with filters (see §6). |

| GET | /notifications/{id} | Fetch one. |

| PATCH | /notifications/{id} | Set `isRead` / `isDismissed` / `isFlagged`. |

## 5 · Push notifications

When an enabled event fires, Signals `POST`s the notification object (§4) to your configured URL. This is your real-time trigger — verify the request, then kick off your workflow (fetch a PDF, update a dashboard, start an archive).

Verifying push requests Signals sends the header name and value configured at setup on every request. Your handler should validate it and reject any request that does not match; because the endpoint is publicly reachable, this is how you confirm the call originated from Signals.
Using auto-dismissal With auto-dismissal enabled, returning `2XX` marks the notification dismissed. A non-2XX response or a timeout leaves it undismissed, so the pull job (§6) will retrieve it later. Make your handler idempotent so that re-delivery is harmless.

## 6 · Pull notifications

Pull is how you catch up — on startup, on a schedule, or after downtime. Fetch notifications with the REST API and filter to what you still need to handle:

| Parameter | Use |

| status | `notdismissed` or `dismissed` — get only the outstanding ones. |

| from · to | Limit to a date range (ISO-8601), e.g. since your last successful run. |

| page[offset] · page[limit] | Page through results. |

#### Catch-up recipe

```python
# 1. fetch everything still outstanding since the last run
GET /api/rest/v1.0/notifications?status=notdismissed&from=2026-07-16T00:00:00.000Z

# 2. handle each notification (fetch the entity, archive, etc.)
# 3. mark each one handled so it won't come back
PATCH /api/rest/v1.0/notifications/519
{ "data": [ { "attributes": { "name": "isDismissed", "value": "true" } } ] }
```

The same `PATCH` sets `isRead` or `isFlagged` — pass one object per flag in the `data` array.

## 7 · Limits

| Limit | Detail |

| Push destination | A single URL per tenant. |

| Pull retention | Notifications are available to pull for 180 days, then expire — so reconcile at least that often. |

## 8 · Reliability & which to use

Use both. Auto-dismissed push notifications give you real-time reactions; a pull job that runs on a schedule — and whenever your handler restarts — verifies nothing slipped through. Anything a push missed is still `notdismissed`, so the pull sweep catches it.

Signals
events

Push handler

Database

Worker
from queue

Archive
dashboards
push

store

queue

process

pull - scheduled catch-up

Push delivers events in real time; the handler stores them and a worker processes them asynchronously. A scheduled pull reconciles anything a push did not deliver.

#### Store before processing

For volume and resilience, don't process inside the push request. Have the push handler write the notification to a database and return `2XX` quickly; a separate worker reads from a queue and does the real work asynchronously. This decouples delivery from processing and gives you fault tolerance, retries, and prioritization.

Pair with Search for a complete picture Notifications tell you an event happened. When you need the full set of what changed — to keep an external database in step — combine notification triggers with the incremental-sync pattern on the Search page: notifications for immediacy, a periodic `modifiedAt` delta as the guaranteed backstop.