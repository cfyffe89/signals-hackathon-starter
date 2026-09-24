# External Actions

External Actions add a button to Signals that opens your web application, passing along the entity the user is working on. They're how you extend Signals with custom, user-driven workflows — sample registration, compliance checks, external lookups — without leaving the notebook.

**1** Overview **2** Where actions appear **3** Passing data: GET vs POST **4** Configuration **5** Triggers & availability **6** Authentication & security **7** Dialog messages **8** Example & next steps

## 1 · Overview

An administrator configures an External Action for a given entity type and sets a URL. Signals adds a button (with an icon you choose) to that entity's interface. When a user clicks it, Signals opens your URL — in a dialog or a new window — passing an identifier for the entity in play. Your page then does the work and, if it needs to, calls back into Signals via the REST API.

A typical sample-registration flow:

  1. The user clicks a **Register** button on a Sample.
  2. Your page opens with the Sample's entity id.
  3. Your page calls the Signals API to read the sample's details.
  4. Your page registers the sample in your external system, then writes the result back to Signals.

## 2 · Where actions appear

External Actions can be attached to a wide range of entity types — each configured action becomes a button on that entity. The supported types are:

Chemical DrawingCollectionDesigns TableExcelExperimentFormulation ExperimentHierarchical TableMaterials TableNotebookParallel ExperimentPDFPlatesPowerPointRequestSampleSample SummarySamples TableSubexperimentSubexperiment SummarySynergy ExperimentTableTaskVariations TableWordWork OrderWorksheetFolders

In System Configuration, actions are grouped by entity type and each can be activated, given an icon, and ordered relative to other actions on the same entity.

## 3 · Passing data: GET vs POST

You choose how the entity's information reaches your page. During setup you also choose the **parameter name** that carries the id — the default is `__eid`.

| GET| POST  
---|---|---  
**How data arrives**|  Entity id in a URL query parameter.| Full entity object in the request body.  
**Best for**|  Simple, view-style actions where the id is enough.| Actions needing the entity's attributes/ancestors up front, or multi-entity (folder) actions.  
**Example**|  …/?__eid=experiment:03ae2d17-…| JSON body (below)  
  
#### GET
    
    
    https://yourapplication.com/?__eid=experiment:03ae2d17-e94d-466a-ba83-94d89a3cea2f

#### POST body (an Admin Defined Table)
    
    
    { "data": {
        "id": "grid:8a9b9331-…", "type": "grid",
        "attributes": { "name": "Data Table", "digest": "76541692", … },
        "relationships": { "ancestors": [
            { "data": { "id": "journal:b3f1335e-…", "type": "journal" } },
            { "data": { "id": "experiment:9247c379-…", "type": "experiment" } }
        ] }
    } }

**Folders** An action on a Folder receives an **array** of these objects — one per selected entity — and therefore **must use POST**.

## 4 · Configuration

Administrators create actions in _System Configuration → External Actions → Create External Action_. The form:

Field| What it does  
---|---  
**Name** · Description| Label for the button/action (required) and optional notes.  
**URL**|  The endpoint Signals opens (required).  
**Submit method**| `HTTP GET` or `HTTP POST` (see §3).  
**Parameter name**|  The query-parameter name that carries the entity id — default `__eid`.  
**Apply to**|  The entity type this action attaches to (see §2).  
**Apply to all templates**|  For template-based entities, make it available on every template or specific ones.  
**Trigger**| `User Action` and, where supported, `Signing Event` (see §5).  
**Open in a dialog**|  On: opens in an in-app modal (enables dialog messages, §7). Off: opens a new browser window.  
**Require write access**|  Only users with write access to the entity can use the action.  
  
System Configuration → External Actions → Create External Action.

**Validating the configuration** The form's **Test** control exercises the configured URL before you save. Every field above is documented on this page; the System Configuration Guide covers the administrative procedure and the permissions needed to reach these screens.

## 5 · Triggers & availability

By default, actions are triggered by a **User Action** (the button click). Some entities support more:

Entity kind| Extra availability control  
---|---  
Signable entities (Experiments, Parallel Experiments, Admin Defined Objects)| **Signing Event** trigger — fire the action on one or more signing events (e.g. Sign and Close). Enables signing flow control (§7).  
Template-based entities (Tables, Worksheets)| Apply to all templates, or only chosen templates.  
Samples| Make the action available only for chosen sample statuses.  
Folders| Restrict to specific folders (and remember: POST only).  
  
## 6 · Authentication & security

An External Action is just a redirect to your URL — **anyone who has that URL has the same access** , and Signals can't see who follows it. Secure your own site accordingly, and authenticate users before doing anything sensitive.

The recommended pattern gives your page authenticated access to the Signals API _as the acting user_ :

  1. **Authenticate at your app** — via your own credentials, VPN, or intranet. Skippable if the user is already behind your firewall.
  2. **Bearer token exchange** — redirect the user through the Signals OAuth flow; on success they return to your `redirect_url` with a bearer token (SSO governs whether they re-enter credentials). Use **Authorization Code with PKCE** for new integrations, since an External Action page is a public client.
  3. **Call the API** — your page now holds a token scoped to that user's permissions and can read/write Signals on their behalf.

**Notes** Signals is secured via IP whitelisting, so API access is controlled regardless of where the user is. See the REST API page for bearer-token setup (client id + redirect URIs are requested through Signals support).

## 7 · Dialog messages

When an action opens **in a dialog** , Signals listens for commands from your page sent via `window.postMessage`. Use them to resize or title the dialog, refresh the entity, and — during signing events — control whether the sign proceeds.

Each command is an array of `[commandName, [args]]`, posted to the modal's parent window at the Signals origin:
    
    
    window.parent.postMessage(
      ['closeAndContinue', []],
      'https://<your-tenant>/' // the Signals origin — targets the command precisely
    )

#### Supported commands

Command| Format| What it does  
---|---|---  
close| ['close', [status]] | Closes the dialog. `status` (boolean, optional, default `true`): when `true`, Signals continues its current flow — refreshing the entity the action was triggered from, and proceeding with a signing transition. When `false`, the entity is not refreshed and the signing transition is aborted.  
closeAndContinue| ['closeAndContinue', []] | Closes the dialog as if `close` had been issued with `true`.  
closeAndAbort| ['closeAndAbort', []] | Closes the dialog as if `close` had been issued with `false`.  
setTitle| ['setTitle', [newTitle]] | Sets the dialog title, which otherwise defaults to the name of the action. `newTitle` (string) — HTML is escaped.  
setWidth| ['setWidth', [newWidth]] | Sets the dialog width as a percentage of the parent window; the height adjusts automatically to maintain the aspect ratio. `newWidth` accepts multiples of ten (10, 20, 30…), thirds (33 and 67, with 66 accepted as an alias for 67), quarters (25, 50, 75), or the string `'phi'`, which sets the width to 61.8% — the golden section of the parent window.  
  
**Two things to note** A command that takes no arguments must still be given an empty array. And refreshing the entity is not a separate command — it is what `close` does when `status` is `true`, which is also why `closeAndContinue` refreshes and `closeAndAbort` does not.

**Example use** On a Sign-and-Close signing event, your page can call the API to verify required content, then post `closeAndContinue` if it's present or `closeAndAbort` (with a message to the user) if it isn't — enforcing a compliance check at signing time.

## 8 · Example & next steps

Signals entity + action button Your web application Your systems LIMS / registry 1 - opens URL (__eid) 3 - REST API (bearer) 4 - postMessage result 2 - your logic

A user-triggered External Action: Signals opens your application with the entity id; your application calls back through the REST API and returns control with a dialog message.

A minimal dialog action reads the entity id, does its work, and hands control back:
    
    
    // 1. read the entity id Signals passed in
    const eid = new URLSearchParams(location.search).get("__eid");
    
    // 2. …call the Signals REST API with the user's bearer token, do the work…
    // 3. hand control back to Signals
    window.parent.postMessage(["closeAndContinue", []], "https://your-tenant/");

For a complete, runnable walkthrough — a Flask app that validates chemistry at signing time — see the tutorial **External Checking for Chemical Drawings**. To read or write entity data from your page, see the REST API and Search pages.
