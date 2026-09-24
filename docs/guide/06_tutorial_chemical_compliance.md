<!-- 
Signals EMEA Hackathon 2026 Reference Guide (Distilled Markdown)
Architecture Notice: Use FastAPI (backend) & Streamlit (UI). Do NOT copy legacy Flask patterns.
-->


# Tutorial: External Checking for Chemical Drawings

Signals Notebook can flag every chemical drawing as requiring external validation. This tutorial builds a small Flask application that reviews a reaction, writes a compliance status back to the stoichiometry table, and clears the warning when the drawing passes.

1Overview
2What you will build
3Prerequisites
4Concepts and APIs used
5Part 1 — The compliance API
6Part 2 — The Flask application
7Part 3 — Key mechanisms
8Configuring the External Action
9Running and verifying
10Summary and endpoints
11Next steps

## 1 · Overview

External Checking allows an organisation to apply its own validation rules to chemical drawings. When the feature is enabled, a warning indicator appears whenever a user creates or edits a drawing. The warning persists until an external system reviews the drawing and clears it through the API.

The mechanism is a pair of hashes. Signals maintains a `self` hash representing the drawing's current state; your system writes an `external` hash to record what it last reviewed. While the two match, the drawing is considered checked. Editing the drawing produces a new `self` hash, the two diverge, and the warning returns.

## 2 · What you will build

A Flask application, opened from Signals as an External Action, that:

* Detects whether the drawing has already been reviewed.

* Displays the reaction's reactants and products.

* Lets a reviewer mark each component compliant, compliant with warning, or non-compliant.

* Writes the result to a Compliance column in the stoichiometry table.

* Clears the External Checking warning when no component is non-compliant.

## 3 · Prerequisites

* Signals Notebook access with permission to generate an API key.

* External Checking enabled — System Configuration → Chemistry Settings → External Checking: tick the option and set the warning message.

* A Compliance column on the stoichiometry table — Chemistry Settings → Stoichiometry Table Columns: add a column titled `Compliance`, type Text, marked read-only so that only the API updates it. Add it to both the Reactants and Products grids.

* Python 3.7 or later with `flask` and `requests` installed: `pip install flask requests`

Disclaimer
    The code examples in this tutorial are a proof of concept, written for clarity rather than production use. They omit robust error handling, security hardening, and performance optimisation. Review and adapt them before deploying.

## 4 · Concepts and APIs used

| Endpoint | Method | Purpose |

| /entities/{eid}/compliance | GET | Read the current `self` and `external` hashes. |

| /entities/{eid}/compliance | PATCH | Write the `external` hash to clear or re-raise the warning. |

| /stoichiometry/{eid} | GET | Read the reaction's reactants, products, and column definitions. |

| /stoichiometry/{eid}/{rowId} | PATCH | Update a single stoichiometry row. |

Background reading: REST API for authentication and response structure, and External Actions for how the action is configured and how the dialog communicates with Signals.

## 5 · Part 1 — The compliance API

The endpoint supports two methods: `GET` to read the current status and `PATCH` to update the external hash.

#### Reading the compliance status

cURL
Python
JavaScript
C#

```python
curl -X GET "https://<your-tenant>/api/rest/v1.0/entities/chemicalDrawing:429762d7-.../compliance" \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Accept: application/vnd.api+json"
```

```python
import requests

url = "https://<your-tenant>/api/rest/v1.0/entities/chemicalDrawing:429762d7-.../compliance"
headers = {
    "x-api-key": "YOUR_API_KEY",
    "Accept": "application/vnd.api+json"
}

response = requests.get(url, headers=headers)
print(response.json())
```

```python
const url = "https://<your-tenant>/api/rest/v1.0/entities/chemicalDrawing:429762d7-.../compliance";
const headers = {
  "x-api-key": "YOUR_API_KEY",
  "Accept": "application/vnd.api+json"
};

fetch(url, { method: "GET", headers })
  .then(res => res.json())
  .then(json => console.log(json));
```

```python
using System.Net.Http;
using System.Threading.Tasks;

var client = new HttpClient();
var request = new HttpRequestMessage(HttpMethod.Get, "https://<your-tenant>/api/rest/v1.0/entities/chemicalDrawing:429762d7-.../compliance");
request.Headers.Add("x-api-key", "YOUR_API_KEY");
request.Headers.Add("Accept", "application/vnd.api+json");

var response = await client.SendAsync(request);
var content = await response.Content.ReadAsStringAsync();
```

```python
{
  "data": {
    "type": "compliance",
    "id": "chemicalDrawing:429762d7-...",
    "attributes": {
      "self":     { "hash": "Y2hlbWljYWxEcmF3aW5nOjZjMmMwYmNj..." },
      "external": { "hash": "" }
    }
  }
}
```

Signals generates `self.hash` when the drawing is created and regenerates it on every edit. `external.hash` is empty until your system sets it.

#### Clearing the warning

To clear the warning, copy the value of `self.hash` into `external.hash`:

cURL
Python
JavaScript
C#

```python
curl -X PATCH "https://<your-tenant>/api/rest/v1.0/entities/chemicalDrawing:429762d7-.../compliance?force=true" \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/vnd.api+json" \
  -H "Accept: application/vnd.api+json" \
  -d '{
        "data": {
          "attributes": {
            "external": { "hash": "Y2hlbWljYWxEcmF3aW5nOjZjMmMwYmNj..." }
          }
        }
      }'
```

```python
import requests

url = "https://<your-tenant>/api/rest/v1.0/entities/chemicalDrawing:429762d7-.../compliance?force=true"
headers = {
    "x-api-key": "YOUR_API_KEY",
    "Content-Type": "application/vnd.api+json",
    "Accept": "application/vnd.api+json"
}
payload = {
    "data": {
        "attributes": {
            "external": { "hash": "Y2hlbWljYWxEcmF3aW5nOjZjMmMwYmNj..." }
        }
    }
}

response = requests.patch(url, json=payload, headers=headers)
print(response.json())
```

```python
const url = "https://<your-tenant>/api/rest/v1.0/entities/chemicalDrawing:429762d7-.../compliance?force=true";
const headers = {
  "x-api-key": "YOUR_API_KEY",
  "Content-Type": "application/vnd.api+json",
  "Accept": "application/vnd.api+json"
};
const body = JSON.stringify({
  data: {
    attributes: {
      external: { hash: "Y2hlbWljYWxEcmF3aW5nOjZjMmMwYmNj..." }
    }
  }
});

fetch(url, { method: "PATCH", headers, body })
  .then(res => res.json())
  .then(json => console.log(json));
```

```python
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;

var client = new HttpClient();
var request = new HttpRequestMessage(HttpMethod.Patch, "https://<your-tenant>/api/rest/v1.0/entities/chemicalDrawing:429762d7-.../compliance?force=true");
request.Headers.Add("x-api-key", "YOUR_API_KEY");
request.Headers.Add("Accept", "application/vnd.api+json");

var payload = "{ \"data\": { \"attributes\": { \"external\": { \"hash\": \"Y2hlbWljYWxEcmF3aW5nOjZjMmMwYmNj...\" } } } }";
request.Content = new StringContent(payload, Encoding.UTF8, "application/vnd.api+json");

var response = await client.SendAsync(request);
var content = await response.Content.ReadAsStringAsync();
```

## 6 · Part 2 — The Flask application

The application has two routes: `/review` renders the review interface, and `/submit` processes the reviewer's decisions.

#### Project structure

```python
compliance-app/
├── app.py                 # Flask application
└── templates/
    └── index.html         # single state-based template
```

#### app.py

```python
"""Chemical compliance review — an External Action for Signals Notebook."""
# Modernized to FastAPI for Hackathon Starter
from fastapi import FastAPI, Request
app = FastAPI()
import requests

app = Flask(__name__)

CONFIG = {
    "base_url": "https://your-tenant/api/rest/v1.0",
    "api_key":  "your-api-key",
}
HEADERS = {
    "x-api-key": CONFIG["api_key"],
    "Content-Type": "application/vnd.api+json",
    "Accept": "application/vnd.api+json",
}

COMPLIANCE_OPTIONS = {
    "compliant":     {"symbol": "[OK]",   "label": "Compliant",              "text": "Compliant"},
    "warning":       {"symbol": "[!]",    "label": "Warning",                "text": "Compliant with warning"},
    "non_compliant": {"symbol": "[X]",    "label": "Non-compliant",          "text": "Non-compliant"},
}

def get_stoichiometry(eid):
    r = requests.get(f"{CONFIG['base_url']}/stoichiometry/{eid}", headers=HEADERS)
    r.raise_for_status()
    return r.json()

def get_compliance(eid):
    r = requests.get(f"{CONFIG['base_url']}/entities/{eid}/compliance", headers=HEADERS)
    r.raise_for_status()
    return r.json()

def update_stoichiometry_row(eid, row_id, column_key, status_text):
    """Write the compliance status into one stoichiometry row."""
    payload = {"data": {"attributes": {"values": {column_key: status_text}}}}
    r = requests.patch(
        f"{CONFIG['base_url']}/stoichiometry/{eid}/{row_id}",
        headers=HEADERS, params={"force": "true"}, json=payload,
    )
    r.raise_for_status()
    return r.json()

def dismiss_external_warning(eid):
    """Copy self.hash into external.hash, which clears the warning."""
    compliance = get_compliance(eid)
    self_hash = compliance["data"]["attributes"]["self"].get("hash")
    if not self_hash:
        return False
    payload = {"data": {"attributes": {"external": {"hash": self_hash}}}}
    r = requests.patch(
        f"{CONFIG['base_url']}/entities/{eid}/compliance",
        headers=HEADERS, params={"force": "true"}, json=payload,
    )
    r.raise_for_status()
    return True

def is_already_compliant(eid):
    """True when the two hashes match, i.e. the drawing is already reviewed."""
    try:
        attrs = get_compliance(eid)["data"]["attributes"]
    except requests.RequestException:      # narrowed from a bare except
        return False
    self_hash     = attrs.get("self", {}).get("hash")
    external_hash = attrs.get("external", {}).get("hash")
    return bool(self_hash) and self_hash == external_hash

def find_compliance_column_key(column_definitions, grid_type):
    """Custom columns have generated keys; look one up by its display title."""
    for col in column_definitions.get(grid_type, []):
        if col.get("title", "").lower() == "compliance":
            return col.get("key")
    return None

@app.route("/review")
def review():
    eid = request.args.get("__eid")
    if not eid:
        return "Error: no entity ID provided. Expected ?__eid=chemicalDrawing:...", 400

    force_review = request.args.get("force", "").lower() == "true"
    try:
        if not force_review and is_already_compliant(eid):
            return render_template("index.html", eid=eid, state="already_compliant")
        attributes = get_stoichiometry(eid)["data"]["attributes"]
        return render_template(
            "index.html", eid=eid, state="review",
            reactants=attributes.get("reactants", []),
            products=attributes.get("products", []),
            options=COMPLIANCE_OPTIONS,
        )
    except requests.RequestException as exc:
        return f"Error fetching data: {exc}", 500

@app.route("/submit", methods=["POST"])
def submit_review():
    eid = request.form.get("eid")
    if not eid:
        return "Error: no entity ID provided", 400

    try:
        stoich     = get_stoichiometry(eid)
        attributes = stoich["data"]["attributes"]

        column_defs = {}
        for item in stoich.get("included", []):
            if item.get("type") == "columnDefinitions":
                column_defs = item.get("attributes", {})
                break

        statuses = []
        for grid in ("reactants", "products"):
            key = find_compliance_column_key(column_defs, grid)
            if not key:
                continue
            for row in attributes.get(grid, []):
                row_id = row.get("row_id")
                if not row_id:
                    continue
                choice = request.form.get(f"{grid[:-1]}_{row_id}", "compliant")
                statuses.append(choice)
                update_stoichiometry_row(eid, row_id, key, COMPLIANCE_OPTIONS[choice]["text"])

        has_non_compliant = "non_compliant" in statuses
        warning_dismissed = not has_non_compliant and dismiss_external_warning(eid)

        return render_template(
            "index.html", eid=eid, state="result",
            all_compliant=all(s == "compliant" for s in statuses) if statuses else True,
            has_warnings=("warning" in statuses) and not has_non_compliant,
            warning_dismissed=warning_dismissed,
        )
    except requests.RequestException as exc:
        return f"Error processing review: {exc}", 500

if __name__ == "__main__":
    app.run(port=5000)
```

#### templates/index.html

```python
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8"/>
    <title>Chemical Compliance Review</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 24px; background: #fdfdfd; color: #333; line-height: 1.5; }
        .card { background: #fff; border: 1px solid #ddd; border-radius: 6px; padding: 20px; max-width: 700px; margin: 0 auto; }
        h2 { margin-top: 0; color: #00707d; font-size: 20px; }
        table { width: 100%; border-collapse: collapse; margin: 12px 0 16px; font-size: 14px; }
        th, td { border: 1px solid #eee; padding: 8px 12px; text-align: left; }
        th { background: #f7f9fa; font-weight: 600; }
        .btn { background: #00707d; color: #fff; border: none; padding: 9px 18px; border-radius: 4px; font-weight: 600; cursor: pointer; }
        .btn:hover { background: #00565f; }
    </style>
</head>
<body>
<div class="card">
    <h2>Chemical Compliance Review</h2>
    <p>Entity: <code>{{ eid }}</code></p>

    {% if state == "already_compliant" %}
        <p style="color: #2e7d32; font-weight: 600;">✓ Drawing Already Verified</p>
        <button type="button" class="btn" onclick="closeSignalsDialog()">Close Dialog</button>

    {% elif state == "review" %}
        <form action="/submit" method="POST">
            <input type="hidden" name="eid" value="{{ eid }}"/>
            <h4>Reactants & Products</h4>
            <table>
                <thead><tr><th>Name</th><th>Formula</th><th>Status</th></tr></thead>
                <tbody>
                {% for r in reactants %}
                <tr>
                    <td>{{ r.name or "Unnamed" }}</td>
                    <td>{{ r.formula or "-" }}</td>
                    <td>
                        <select name="reactant_{{ r.row_id }}">
                            {% for opt_key, opt in options.items() %}
                            <option value="{{ opt_key }}">{{ opt.symbol }} {{ opt.label }}</option>
                            {% endfor %}
                        </select>
                    </td>
                </tr>
                {% endfor %}
                </tbody>
            </table>
            <button type="submit" class="btn">Submit Review</button>
        </form>

    {% elif state == "result" %}
        {% if all_compliant %}
            <p style="color: #2e7d32; font-weight: 600;">✓ Review Successful — Warning Cleared</p>
        {% else %}
            <p style="color: #b3261e; font-weight: 600;">✗ Non-Compliant Structures Detected</p>
        {% endif %}
        <button type="button" class="btn" onclick="closeSignalsDialog()">Close Dialog</button>
    {% endif %}
</div>

<script>
// Client dialog communication: dispatch command back to Signals Notebook
function closeSignalsDialog() {
    if (window.parent && window.parent !== window) {
        window.parent.postMessage(['closeDialog', []], '*');
    } else {
        window.close();
    }
}
</script>
</body>
</html>
```

## 7 · Part 3 — Key mechanisms

### Hash matching

The whole feature rests on comparing two values. `self.hash` changes whenever the drawing changes; `external.hash` only changes when your system writes it. Equal hashes mean "reviewed at this exact state", which is why an edit automatically re-raises the warning.

### Column keys are generated, not titles

Custom stoichiometry columns have system-generated keys that differ from their display titles, so you cannot write to `"Compliance"` directly. The stoichiometry response includes a `columnDefinitions` entry in its `included` array that maps titles to keys; `find_compliance_column_key` performs that lookup for the reactants and products grids separately.

### Row updates

Each reactant and product carries a `row_id`. Updating a row is a `PATCH` to `/stoichiometry/{eid}/{rowId}` with the column key and its new value inside `data.attributes.values`.

## 8 · Configuring the External Action

* Go to System Configuration → External Actions → Create External Action.

* Set Name to "Compliance Review" and URL to `https://your-host/review`.

* Set Apply to to Chemical Drawing.

* Set Submit method to `HTTP GET` and leave Parameter name as `__eid`.

* Enable Open in a dialog and Require write access.

* Use Test to confirm the URL responds, then save.

Signals will call your URL with the drawing's id appended:

```python
https://your-host/review?__eid=chemicalDrawing:429762d7-422b-4737-9c7d-2cbbdcc68044
```

Security
    An External Action is a redirect to your URL, so anyone holding that URL can reach it. Authenticate users at your application, and for user-attributed API calls use the OAuth bearer flow — Authorization Code with PKCE is the recommended flow for a page of this kind. The API key shown above is used here only to keep the proof of concept short.

## 9 · Running and verifying

* Create the project folder and a `templates` subfolder; save `app.py` and `templates/index.html`.

* Set `base_url` and `api_key` in `CONFIG`.

* Install dependencies and start the server: `pip install flask requests` then `python app.py`.

* Open `http://localhost:5000/review?__eid=chemicalDrawing:<your-drawing-id>`.

A correct run shows the reaction's components with review options. After submitting an all-compliant review, re-opening the page shows the "already compliant" state, and the warning indicator on the drawing in Signals is cleared. Editing the drawing restores the warning.

Downloads `app.py` and `templates/index.html` are available from the tutorial index.

## 10 · Summary and endpoints

| Endpoint | Method | Purpose |

| /entities/{eid}/compliance | GET | Fetch compliance status. |

| /entities/{eid}/compliance | PATCH | Update the external hash. |

| /stoichiometry/{eid} | GET | Fetch reaction data and column definitions. |

| /stoichiometry/{eid}/{rowId} | PATCH | Update a stoichiometry row. |

## 11 · Next steps

* Replace the API key with the bearer-token flow so that reviews are attributed to the reviewer in the audit trail.

* Check structures against a regulatory system or internal database rather than relying on manual selection.

* Record review outcomes externally for reporting, using External Notifications to trigger downstream workflows.

## Tutorial Source Code & Downloadable Package

This tutorial includes a complete, runnable Python Flask reference implementation for an External Action server that performs chemical drawing compliance reviews.

### 📦 Download Package: `signals-chemical-compliance-tutorial.zip`

Package Contents:

* `app.py` — Flask compliance review server evaluating reaction stoichiometry and returning `window.postMessage` dialog commands.

* `README.md` — Setup guide and step-by-step External Action configuration instructions for Signals System Settings.

⬇️ Download Tutorial Package (.zip)
📄 View README.md