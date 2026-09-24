<!-- 
Signals EMEA Hackathon 2026 Reference Guide (Distilled Markdown)
Architecture Notice: Use FastAPI (backend) & Streamlit (UI). Do NOT copy legacy Flask patterns.
-->


# Tutorial: Building a Metrics Dashboard

A staged tutorial that builds a reporting tool for Signals administrators: user activity, license consumption, and entity creation — first as a command-line tool, then as a small web dashboard.

1Overview
2What you will build
3Prerequisites
4APIs used
5Part 1 — Users
6Part 2 — Licenses
7Part 3 — Entity creation
8Part 4 — Web dashboard
9Summary and endpoints
10Next steps

## 1 · Overview

Signals administrators frequently need a view of how a tenant is being used: who is active, how licenses are consumed, and how much work is being created. This tutorial builds that view in four stages, each adding one capability to a single Python script, and finishes by presenting the same data as a web dashboard.

## 2 · What you will build

* Retrieve all users and categorise them by login activity — never logged in, inactive for 30 days or more, and active.

* Report license totals, consumption, and remaining capacity by license type.

* Summarise entity creation over the past 30 days for experiments, samples, and tasks.

* Present all of it in a browser as a simple dashboard.

## 3 · Prerequisites

* A Signals API key. The key's user must have permission to read users and licenses (typically a System Admin).

* Python 3.9 or later.

* Libraries: `pip install requests tabulate flask`

* Familiarity with the JSON:API response structure — see REST API.

The base URL must include the version path and a trailing slash
    URLs in this tutorial are built by concatenation, so `BASE_API_URL` must be the full API root ending in a slash:
    
```python
BASE_API_URL = "https://your-tenant/api/rest/v1.0/" # note the trailing slash
```

Disclaimer
    The code examples in this tutorial are a proof of concept, written for clarity rather than production use. They omit robust error handling, security hardening, and performance optimisation. Review and adapt them before deploying.

## 4 · APIs used

| Endpoint | Method | Purpose |

| /users | GET | All users, with roles resolved in `included`. Paginated. |

| /users/licenses | GET | License totals and consumption. |

| /entities/search/terms | POST | Counts of distinct values of a field, for a given query. |

## 5 · Part 1 — Fetching and categorising users

Retrieve every user and group them by last login. `GET /users` is paginated and returns a `links.next` cursor while further pages remain, so the fetch loop follows that link until it is absent.

#### metrics_app.py

```python
import datetime
import requests
from tabulate import tabulate

BASE_API_URL = "https://your-tenant/api/rest/v1.0/"   # trailing slash required
HEADERS = {
    "accept": "application/vnd.api+json",
    "x-api-key": "YOUR_API_KEY",
}
PAGE_LIMIT = 100

def fetch_all_users():
    """Fetch every user, following the links.next cursor."""
    users, included = [], []
    url = f"{BASE_API_URL}users?enabled=true&page[offset]=0&page[limit]={PAGE_LIMIT}"
    while url:
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            print("Error fetching users:", response.status_code)
            return None
        data = response.json()
        users.extend(data.get("data", []))
        included.extend(data.get("included", []))
        url = data.get("links", {}).get("next")      # None on the last page
    return {"data": users, "included": included}

def parse_users(payload):
    """Flatten the JSON:API response into rows, resolving roles from `included`."""
    roles_by_id = {
        r["id"]: r["attributes"]["name"]
        for r in payload.get("included", []) if r.get("type") == "role"
    }
    now = datetime.datetime.now(datetime.timezone.utc)   # timezone-aware
    rows = []
    for user in payload["data"]:
        attrs = user["attributes"]
        raw_login = attrs.get("lastLoginAt")
        last_login = (
            datetime.datetime.fromisoformat(raw_login.replace("Z", "+00:00"))
            if raw_login else None
        )
        days = (now - last_login).days if last_login else None
        role_refs = user.get("relationships", {}).get("roles", {}).get("data", [])
        rows.append({
            "User ID": attrs.get("userId"),
            "First Name": attrs.get("firstName"),
            "Last Name": attrs.get("lastName"),
            "Email": attrs.get("email"),
            "Last Login": last_login.strftime("%Y-%m-%d") if last_login else "Never",
            "Days Since Login": days if last_login else "Never",
            "Licenses": ", ".join(l["name"] for l in attrs.get("licenses", [])),
            "Roles": ", ".join(roles_by_id.get(r["id"], "Unknown") for r in role_refs),
        })
    return rows

def categorize_users(users):
    never  = [u for u in users if u["Last Login"] == "Never"]
    stale  = [u for u in users if isinstance(u["Days Since Login"], int) and u["Days Since Login"] > 30]
    active = [u for u in users if isinstance(u["Days Since Login"], int) and u["Days Since Login"] <= 30]
    return never, stale, active

def display_summary(never, stale, active):
    print("\nUser summary")
    print(f"Total users: {len(never) + len(stale) + len(active)}")
    print(f"Never logged in: {len(never)}")
    print(f"Inactive 30+ days: {len(stale)}")
    print(f"Active within 30 days: {len(active)}")

def display_users(users, category):
    print(f"\n{category} users:")
    print(tabulate(users, headers="keys", tablefmt="pretty"))
```

Run it with `python metrics_app.py`. Commands were tested on Windows; exact invocation varies by operating system and Python installation.

## 6 · Part 2 — License usage

`GET /users/licenses` returns a single `data` object whose `attributes.licenses` array holds one entry per license type, each with `totalLicense` and `totalLicenseConsumed`.

```python
def fetch_license_usage():
    response = requests.get(f"{BASE_API_URL}users/licenses", headers=HEADERS)
    if response.status_code != 200:
        print("Error fetching licenses:", response.status_code)
        return None
    licenses = response.json().get("data", {}).get("attributes", {}).get("licenses", [])
    return [{
        "License":   lic["name"],
        "Total":     lic["totalLicense"],
        "Used":      lic["totalLicenseConsumed"],
        "Remaining": lic["totalLicense"] - lic["totalLicenseConsumed"],
    } for lic in licenses]

def display_license_summary(summary):
    print("\nLicense usage")
    print(tabulate(summary, headers="keys", tablefmt="pretty"))
```

## 7 · Part 3 — Entity creation over 30 days

This part uses `POST /entities/search/terms`. Unlike `/entities/search`, which returns matching entities, the terms endpoint returns the distinct values of a named field together with a count — exactly what a summary needs. The request body carries both the `query` and the `field` to aggregate.

```python
def fetch_entity_creation_total():
    """Count experiments, samples, and tasks created in the past 30 days."""
    now = datetime.datetime.now(datetime.timezone.utc)
    start = now - datetime.timedelta(days=30)
    payload = {
        "query": {"$and": [
            {"$in": {"field": "type", "values": ["experiment", "sample", "task"]}},
            {"$range": {"field": "createdAt", "as": "date",
                        "from": start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                        "to":   now.strftime("%Y-%m-%dT%H:%M:%S.000Z")}},
            {"$match": {"field": "isTemplate", "value": False}},
        ]},
        "field": "type",
    }
    response = requests.post(
        f"{BASE_API_URL}entities/search/terms?source=SN", headers=HEADERS, json=payload
    )
    if response.status_code != 200:
        print("Error fetching entity counts:", response.status_code)
        return None
    return [
        {"Entity Type": e["attributes"]["term"], "Created": e["attributes"]["count"]}
        for e in response.json()["data"]
    ]

def display_entity_summary(summary):
    """Previously referenced but not shown; included here for completeness."""
    print("\nEntities created in the past 30 days")
    print(tabulate(summary, headers="keys", tablefmt="pretty"))
```

Reading the response
    You will get one entry per entity type that had matches in the window, each with its count — for example `experiment` and `sample`. Types with no matches are absent entirely rather than returned with a zero, so do not assume every type you asked about will appear; read the keys that come back rather than indexing into ones you expect.

#### Bringing the command-line tool together

```python
def main():
    payload = fetch_all_users()
    if not payload:
        return
    users = parse_users(payload)
    never, stale, active = categorize_users(users)

    display_summary(never, stale, active)
    licenses = fetch_license_usage()
    if licenses:
        display_license_summary(licenses)
    entities = fetch_entity_creation_total()
    if entities:
        display_entity_summary(entities)

    choices = {"1": (active, "Active"), "2": (stale, "Inactive (30+ days)"), "3": (never, "Never logged in")}
    while True:
        choice = input("\nView: (1) Active, (2) Inactive, (3) Never logged in, (q) Quit: ").lower()
        if choice == "q":
            break
        if choice in choices:
            display_users(*choices[choice])
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main()
```

## 8 · Part 4 — The web dashboard

The final stage presents the same data through Flask. The data-gathering functions are unchanged; only the presentation layer is new.

```python
# dashboard.py
# Modernized to FastAPI for Hackathon Starter
from fastapi import FastAPI, Request
app = FastAPI()
# reuse fetch_all_users, parse_users, categorize_users,
# fetch_license_usage, fetch_entity_creation_total from metrics_app.py

app = Flask(__name__)

def get_data():
    """Return five values on every path, so unpacking is always safe."""
    payload = fetch_all_users()
    if not payload:
        return None, None, None, None, None       # five, matching the caller
    users = parse_users(payload)
    never, stale, active = categorize_users(users)
    return never, stale, active, fetch_license_usage(), fetch_entity_creation_total()

@app.route("/")
def index():
    never, stale, active, licenses, entities = get_data()
    if never is None:
        return "Unable to retrieve data from the Signals API.", 503

    summary = {
        "Total Users": len(never) + len(stale) + len(active),
        "Active (within 30 days)": len(active),
        "Inactive (30+ days)": len(stale),
        "Never Logged In": len(never),
    }
    return render_template(
        "dashboard.html",                      # template name used consistently
        summary=summary, license_summary=licenses, entity_creation_summary=entities,
        never_logged_in=never, inactive=stale, active=active,
    )

if __name__ == "__main__":
    app.run(debug=True)
```

#### Project structure and running it

```python
metrics-dashboard/
├── metrics_app.py          # parts 1-3, the CLI tool
├── dashboard.py            # part 4, the Flask app
└── templates/
    └── dashboard.html      # the dashboard template
```

* Install dependencies: `pip install requests tabulate flask`

* Set `BASE_API_URL` and the API key.

* Run `python dashboard.py` and open `http://localhost:5000`.

Binding to another host or port
    Flask binds to `127.0.0.1:5000` by default. To expose it elsewhere, pass the host and port explicitly: `app.run(host="192.168.1.100", port=8000)`.

#### templates/dashboard.html

```python
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8"/>
    <title>Signals Executive Metrics Dashboard</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 30px; background: #f4f6f8; color: #333; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; }
        .card { background: #fff; border-radius: 8px; padding: 20px; box-shadow: 0 2px 6px rgba(0,0,0,0.06); border-top: 4px solid #00707d; }
        .metric { font-size: 32px; font-weight: 700; color: #111; margin-top: 8px; }
        .section { background: #fff; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 6px rgba(0,0,0,0.06); }
        table { width: 100%; border-collapse: collapse; font-size: 14px; margin-top: 10px; }
        th, td { border: 1px solid #eee; padding: 9px 12px; text-align: left; }
        th { background: #f8fafc; font-weight: 600; }
    </style>
</head>
<body>
<h1 style="color: #00707d;">Signals Executive Metrics Dashboard</h1>

<div class="grid">
    <div class="card"><div>Total Users</div><div class="metric">{{ summary["Total Users"] }}</div></div>
    <div class="card"><div>Active (30 Days)</div><div class="metric" style="color: #2e7d32;">{{ summary["Active (within 30 days)"] }}</div></div>
    <div class="card"><div>Inactive (30+ Days)</div><div class="metric" style="color: #8a6100;">{{ summary["Inactive (30+ days)"] }}</div></div>
    <div class="card"><div>Never Logged In</div><div class="metric" style="color: #b3261e;">{{ summary["Never Logged In"] }}</div></div>
</div>

<div class="section">
    <h3>License Utilization</h3>
    <table>
        <thead><tr><th>License</th><th>Total</th><th>Used</th><th>Remaining</th></tr></thead>
        <tbody>
        {% for lic in license_summary %}
        <tr><td>{{ lic["License"] }}</td><td>{{ lic["Total"] }}</td><td>{{ lic["Used"] }}</td><td><strong>{{ lic["Remaining"] }}</strong></td></tr>
        {% endfor %}
        </tbody>
    </table>
</div>

<div class="section">
    <h3>30-Day Velocity by Type</h3>
    <table>
        <thead><tr><th>Type</th><th>Created Count</th></tr></thead>
        <tbody>
        {% for ent in entity_creation_summary %}
        <tr><td><code>{{ ent["Entity Type"] }}</code></td><td><strong>{{ ent["Created"] }}</strong></td></tr>
        {% endfor %}
        </tbody>
    </table>
</div>
</body>
</html>
```

## 9 · Summary and endpoints

| Endpoint | Method | Used for |

| /users | GET | User list and roles; paginated via `links.next`. |

| /users/licenses | GET | License totals and consumption. |

| /entities/search/terms | POST | Entity creation counts by type. |

## 10 · Next steps

* Extend the entity summary with other types, or filter by notebook using the query language described on the Search page.

* Integrate a charting library like Chart.js or Plotly to visualize the license utilization data over time directly on the dashboard.

## Tutorial Source Code & Downloadable Package

This tutorial includes a complete, runnable Python Flask application that connects to the Signals REST API to build a real-time executive analytics dashboard.

### 📦 Download Package: `signals-metrics-dashboard-tutorial.zip`

Package Contents:

* `app.py` — Flask web application connecting to the Signals REST API to monitor active users, license utilization, and 30-day entity velocity.

* `README.md` — API key configuration, dependency installation, and local dashboard launch instructions.

⬇️ Download Tutorial Package (.zip)
📄 View README.md