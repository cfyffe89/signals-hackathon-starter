# External Notifications

Notifications let your systems react to what happens in Signals — an experiment signed, an entity created, a record exported — without anyone clicking a thing. Subscribe to events, and your workflows kick off automatically.

**1** Overview: push & pull **2** Setup **3** Triggers & types **4** The notification object **5** Push notifications **6** Pull notifications **7** Limits **8** Reliability

## 1 · Overview: push and pull

An administrator configures which events publish notifications. There are two ways to consume them:

| Push| Pull  
---|---|---  
**How**|  Signals sends each notification to a URL you host, as it happens.| You fetch notifications from the Signals REST API on your schedule.  
**Best for**|  Real-time reactions.| Catching up on anything you missed, and reconciliation.  
  
The two are complementary. Consider an archival integration: it's subscribed via **push** , so when a user signs and closes an experiment it immediately fetches a PDF and archives it. If that service was offline for a while, it uses **pull** to retrieve everything it missed and mark those handled. We recommend using both — see §8.

## 2 · Setup

An administrator enables External Notifications and selects which events to publish. During setup:

  * **Push URL & auth** — configure the single URL that receives pushes, plus an **HTTP header name and value** (e.g. an API key) that Signals will send on every request so your endpoint can verify the call is genuine.
  * **Auto-dismissal** — optionally, a notification delivered by push is marked dismissed automatically once your server returns any `2XX`. This sets the `isDismissed` flag to `true` (it doesn't delete anything — dismissed notifications remain queryable).

The fields you configure are described above. The System Configuration Guide covers the administrative procedure and the permissions needed to reach these screens.

## 3 · Triggers & notification types

Three trigger families can be enabled. Each notification's `type` attribute tells you exactly what happened:

Trigger| Event| type  
---|---|---  
Top-level entity creation| Entity created (Notebook, Experiment, Request, Parallel/Sub Experiment, Admin Defined Object, Sample, Task, Material)| create  
Export to PDF/ZIP| Print / ZIP export| print  
All signing events| Sign and Close| close  
Sign and Keep Open| sign  
Close Without Signing| close_without_signing  
Reopen| reopen  
Request Reviewer| review_request_for_reviewer  
Request Two-Stage Review| two_stage_review_request_for_reviewer  
Reviewer Request Accepted / Rejected| review_accepted_for_owner · review_rejected_for_owner  
First Review Accepted / Rejected| first_review_accepted_for_owner · first_review_rejected_for_owner  
Second Review Accepted / Rejected| second_review_accepted_for_owner · second_review_rejected_for_owner  
Archive| archive  
Return From Archive| unarchive  
Void| void  
(review variants fire for the relevant reviewer/owner role)  
  
## 4 · The notification object

Notifications follow the same JSON:API shape as other responses. The `relationships` and `included` give you the user and entity involved; the key details are in `attributes`:
    
    
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

Attribute| Meaning  
---|---  
id| Notification id — use it to fetch or update this notification.  
type| Which event occurred (see §3).  
createdAt| When the triggering event happened.  
isDismissed| Handled? Set by auto-dismissal on push, or via the API.  
isRead · isFlagged| Your own bookkeeping flags, set via the API.  
comment| The signing comment for signing events; `null` where not applicable (e.g. creation, export).  
  
#### Endpoints

Method| Path| Purpose  
---|---|---  
GET| /notifications| List, with filters (see §6).  
GET| /notifications/{id}| Fetch one.  
PATCH| /notifications/{id}| Set `isRead` / `isDismissed` / `isFlagged`.  
  
## 5 · Push notifications

When an enabled event fires, Signals `POST`s the notification object (§4) to your configured URL. This is your real-time trigger — verify the request, then kick off your workflow (fetch a PDF, update a dashboard, start an archive).

**Verifying push requests** Signals sends the header name and value configured at setup on every request. Your handler should validate it and reject any request that does not match; because the endpoint is publicly reachable, this is how you confirm the call originated from Signals.

**Using auto-dismissal** With auto-dismissal enabled, returning `2XX` marks the notification dismissed. A non-2XX response or a timeout leaves it undismissed, so the pull job (§6) will retrieve it later. Make your handler idempotent so that re-delivery is harmless.

## 6 · Pull notifications

Pull is how you catch up — on startup, on a schedule, or after downtime. Fetch notifications with the REST API and filter to what you still need to handle:

Parameter| Use  
---|---  
status| `notdismissed` or `dismissed` — get only the outstanding ones.  
from · to| Limit to a date range (ISO-8601), e.g. since your last successful run.  
page[offset] · page[limit]| Page through results.  
  
#### Catch-up recipe
    
    
    # 1. fetch everything still outstanding since the last run
    GET /api/rest/v1.0/notifications?status=notdismissed&from=2026-07-16T00:00:00.000Z
    
    # 2. handle each notification (fetch the entity, archive, etc.)
    # 3. mark each one handled so it won't come back
    PATCH /api/rest/v1.0/notifications/519
    { "data": [ { "attributes": { "name": "isDismissed", "value": "true" } } ] }

The same `PATCH` sets `isRead` or `isFlagged` — pass one object per flag in the `data` array.

## 7 · Limits

Limit| Detail  
---|---  
Push destination| A single URL per tenant.  
Pull retention| Notifications are available to pull for **180 days** , then expire — so reconcile at least that often.  
  
## 8 · Reliability & which to use

Use **both**. Auto-dismissed push notifications give you real-time reactions; a pull job that runs on a schedule — and whenever your handler restarts — verifies nothing slipped through. Anything a push missed is still `notdismissed`, so the pull sweep catches it.

Signals events Push handler Database Worker from queue Archive dashboards push store queue process pull - scheduled catch-up

Push delivers events in real time; the handler stores them and a worker processes them asynchronously. A scheduled pull reconciles anything a push did not deliver.

#### Store before processing

For volume and resilience, don't process inside the push request. Have the push handler **write the notification to a database** and return `2XX` quickly; a separate worker reads from a **queue** and does the real work asynchronously. This decouples delivery from processing and gives you fault tolerance, retries, and prioritization.

**Pair with Search for a complete picture** Notifications tell you _an event happened_. When you need the full set of _what changed_ — to keep an external database in step — combine notification triggers with the incremental-sync pattern on the Search page: notifications for immediacy, a periodic `modifiedAt` delta as the guaranteed backstop.
