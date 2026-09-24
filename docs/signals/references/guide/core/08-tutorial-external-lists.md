# Tutorial: External Lists, Data Sources & Chemical Sources

Three ways to pull data from _outside_ Signals directly into the notebook — dropdown lists, live table rows, and chemical structures. This tutorial builds one small server that powers all three, and walks the exact configuration for each, verified against a live tenant.

**00** The three source types **01** What they share **02** The reference server **03** External List **04** External Data Source **05** External Chemical Source **06** Technical Considerations & production notes **07** Summary

**Proof of concept** The code here is intentionally minimal — no authentication hardening, error handling, or persistence — so the integration mechanics stay visible. It is not production-ready. Signals reaches your server over the internet, so for real use it must be publicly resolvable and properly secured.

## 1 · The three source types, and when to use each

All three live under **System Configuration → Data Sources** , but they feed different parts of Signals.

Type| Feeds…| Direction| Use it when…  
---|---|---|---  
**External List**|  Dropdown / picklist values on an _attribute_|  read| you want a field's options to come from a system of record — project codes, sites, instruments.  
**External Data Source**|  Rows of an _Admin-Defined Table_|  read write| a user types a key (a barcode, a sample id) and you fill — or push back — a whole row of data.  
**External Chemical Source**|  Reactants / Products in the _Stoichiometry_ table, via ChemDraw Quick Add| read| chemists should pull a structure + its properties (CAS, MW…) from a compound registry by name or id.  
  
The first two are introduced in the guide's _External Data Sources and Lists_ page. The third — **Chemical Sources** — is the chemistry-aware cousin: same plumbing, but the payload is a molecule and it lands in the stoichiometry grid.

## 2 · What all three share

System Configuration → Data Sources. All three source types are created from here.

These principles apply to all three source types; each type is a variation on the same model.

  * **A RESTful URL you host** Signals calls a URL you provide and expects JSON in response. A static file is sufficient for a read-only List; a dynamic service is required for key lookups and writes.
  * **HTTP header authentication** Each configuration supports one or more **HTTP headers (name + value)** — for example `x-api-key: …` — which Signals sends on every request. Use **Add HTTP Header** to define as many as your endpoint requires.
  * **Nested JSON needs no flattening** Signals walks the response and offers every leaf as a mappable field, named by its path — `address.city`, `variants[0].ratio`, `matrix[0][1]`. Keys containing a literal dot are bracket-escaped as `["field.with.dots"]`. Two things to know: an empty `{}` or `[]` is listed but cannot be mapped to any type, and the field list comes from the record fetched for your **Example ID** — new leaves appearing later need another **Fetch Example Data**. Conversion is strict, so map identifiers such as `"02101"` to **Text** ; as a Number they lose leading zeros.
  * **"Fetch Example Data" + field mapping** A button pulls a sample response so you can **map external fields to Signals** — choosing which field is the _key_ , which is the description, which columns to include, and their data types.
  * **Response-time budgets** To protect the UI, Signals gives up if your server is slow: **External Lists time out at 30s** , **Data and Chemical Sources at 20 seconds**.

## 3 · The reference server

One Flask app exposing an endpoint for each source type. Run it, and the three configs below point at it. tested
    
    
    """Reference external server for Signals Lists, Data Sources, and Chemical Sources.
    Proof-of-concept: no auth, no persistence. pip install flask ; python server.py"""
    from flask import Flask, request, jsonify, abort
    app = Flask(__name__)
    
    PROJECT_CODES = [
        {"code": "BIO-100", "project": "Oncology Screen",   "active": True},
        {"code": "CHM-204", "project": "Lead Optimization", "active": True},
        {"code": "TOX-311", "project": "Safety / Tox",      "active": False},
    ]
    FLASKS = {
        "88": {"id": "88", "name": "Flask A", "amount": 250, "type": "round-bottom"},
        "89": {"id": "89", "name": "Flask B", "amount": 500, "type": "erlenmeyer"},
    }
    CHEMICALS = {
        "benzene": {"id":"benzene","name":"Benzene","CAS":"71-43-2","MW":78.11,"MF":"C6H6","smiles":"c1ccccc1"},
        "aspirin": {"id":"aspirin","name":"Aspirin","CAS":"50-78-2","MW":180.16,"MF":"C9H8O4","smiles":"CC(=O)Oc1ccccc1C(=O)O"},
    }
    
    # 1. LIST — GET returns {"data": [ ...objects... ]}
    @app.route("/list", methods=["GET"])
    def list_source():
        return jsonify({"data": PROJECT_CODES})
    
    # 2. DATA SOURCE — GET by key, POST create, PUT update
    @app.route("/flasks/<key>", methods=["GET"])
    def get_flask(key):
        return jsonify(FLASKS.get(key) or abort(404))
    
    @app.route("/flasks", methods=["POST"])
    def create_flask():
        body = request.get_json(force=True)
        body["id"] = str(max(int(k) for k in FLASKS) + 1)
        FLASKS[body["id"]] = body
        return jsonify(body), 201
    @app.route("/flasks/<key>", methods=["PUT"])
    def update_flask(key):
        body = request.get_json(force=True); body["id"] = key
        FLASKS[key] = body
        return jsonify(body)
    
    # 3. CHEMICAL SOURCE — GET by key returns structure + properties
    @app.route("/chem/<key>", methods=["GET"])
    def get_chem(key):
        return jsonify(CHEMICALS.get(key.lower()) or abort(404))
    
    if __name__ == "__main__":
        app.run(port=5005)

**Expected responses** With the server running, the three endpoints return the shapes Signals expects: 
    
    
    GET /list        → {"data":[{"code":"BIO-100","project":"Oncology Screen","active":true}, …]}
    GET /flasks/88   → {"id":"88","name":"Flask A","amount":250,"type":"round-bottom"}
    POST /flasks     → {"name":"Flask C","amount":100,"type":"vial","id":"90"}
    GET /chem/aspirin→ {"id":"aspirin","name":"Aspirin","CAS":"50-78-2","MW":180.16,"MF":"C9H8O4","smiles":"CC(=O)Oc1ccccc1C(=O)O"}

If you do not have a server available, free mock hosts can serve a GitHub repository's `db.json` in the same way — a raw file URL for a List, and `my-json-server.typicode.com/<user>/<repo>/data/{id}` for a keyed Data or Chemical Source.

## 4 · External List — dropdown values from a system of record

Populate an attribute's picklist from your server. Read-only; refreshed on a schedule.

#### The data contract

A single `GET` returns a top-level `data` array of objects. Objects can carry many fields — you pick which one is the list's **key** (what users pick) and, optionally, a description.
    
    
    GET /list  →
    { "data": [
        { "code": "BIO-100", "project": "Oncology Screen",   "active": true },
        { "code": "CHM-204", "project": "Lead Optimization", "active": true }
    ] }

#### Configure it

  1. Go to **System Configuration → Data Sources → Create Data Source → External List Source**.
  2. Set a **Source Name** (e.g. "Project Codes") and the **Destination URL** (`https://your-server/list`).
  3. Optionally use **Add HTTP Header** to define one or more authentication headers (name + value), for example `x-api-key`.
  4. Click **Fetch Example Data**. Signals calls the URL and lists the fields it found.
  5. In the mapping grid, for each external field set the **Internal Field Name** and choose: **Key** (the value stored — required, exactly one), **Desc.** (shown alongside), and **Include**. Here, `code` = Key, `project` = Desc. Use **Add Manual Field** for values not present in the sample.
  6. **Save.** Then attach it: **Configuration → Attributes →** a list-type attribute → choose this External List as its source. Any table or field using that attribute now shows your live options.

**Limits** An External List can hold up to **20,000 items** , and a tenant can define up to **200 lists**. The fetch must return within **30 seconds**.

## 5 · External Data Source — live table rows by key

A user enters a key in an Admin-Defined Table row; Signals fetches the matching record and fills the row. Optionally push rows back out.

#### The data contract

The URL carries the lookup value via a placeholder. Signals substitutes **`{id}`** (the key the user typed), and can also send **`{username}`** and **`{user_alias}`** :
    
    
    Destination URL:  https://your-server/flasks/{id}
                      (e.g. https://abc.com?id={id}&un={username}&alias={user_alias})
    
    GET  /flasks/88             → { "id":"88", "name":"Flask A", "amount":250, "type":"round-bottom" }
    POST /flasks  {name,amount} → creates & echoes the row (with new id)
    PUT  /flasks/89 {…}         → updates & echoes the row

#### Configure it

  1. **Create Data Source → External Data Source.** Name it, set the **Destination URL** with a `{id}` placeholder.
  2. Add authentication **HTTP headers** if required. Enter an **Example ID** (for example `88`) so Fetch Example Data has a key to look up.
  3. Tick the **available operations** : GET to fetch, POST to create, PUT to update. GET-only makes it read-only lookup.
  4. **Fetch Example Data** , then map each external field to a Signals **Data Type** (Text, Number, …) and mark exactly one as the **Key** (here `id`).
  5. **Save.** Use it from an **Admin-Defined Table** : add the data source to the table, and entering a key in a row triggers the `GET` and populates the mapped columns. With POST/PUT enabled, edited rows sync back to your server.

**Limit** A Data Source fetch must return within **20 seconds**. Because it fires on user interaction, keep it snappy.

## 6 · External Chemical Source — structures into stoichiometry

The chemistry-aware source: a chemist types a compound key, and its structure plus properties drop into the Reactants/Products grids through ChemDraw's **Quick Add**.

#### The data contract

Like a Data Source, but the record includes a **chemical structure** field (SMILES, MOL, …) alongside properties:
    
    
    Destination URL:  https://your-server/chem/{id}
    
    GET /chem/benzene →
    { "id": "benzene", "name": "Benzene", "CAS": "71-43-2",
      "MW": 78.11, "MF": "C6H6", "smiles": "c1ccccc1" }

#### Configure it

  1. **Create Data Source → External Chemical Source.** Name it and set the **Destination URL** with `{id}`; add authentication headers if required; enter an **Example ID** (for example `benzene`).
  2. Leave **Enable Stoichiometry Configuration** on — this is what wires the source into the Reactants and Products tables so chemists can pull from it via the ChemDraw plugin's Quick Add. Set the **Quick Add hint text** shown in that box.
  3. **Fetch Example Data.** Choose the **Chemical structure field** (`smiles`) and its **Structure Format** (SMILES). Tick **Base64 Encoded** or **Chemical Structure is Link** if your structure is encoded or referenced by URL rather than inline.
  4. Map the remaining record fields to Stoichiometry columns — **Product/Reactant Name** , **CAS Number** , **MF** , **MW** , **FM** — from your response fields.
  5. **Save.** In a Chemical Drawing's stoichiometry grid, use **Quick Add** and type a key (`benzene`); Signals fetches the record, renders the structure, and fills the mapped property columns.

**How this differs from a Data Source** A plain Data Source fills generic table cells. A Chemical Source understands chemistry: it parses the structure field into a real molecule, places it in the reaction, and aligns the rest to the stoichiometry model — so a registry lookup becomes a drawn, calculable reactant in one Quick Add.

## 7 · Technical Considerations & production notes

  * **Format is exact** Lists must return `{"data":[…]}`; a bare array won't map. Data/Chemical sources return a single object for a keyed GET. Wrong shape → nothing to map.
  * **Reachability & CORS**Signals calls your server cloud-to-server, so it must be publicly reachable (a static file host, or a mock like `my-json-server.typicode.com`, works for demos). A localhost URL only works where the fetch happens in your own browser.
  * **Stale configs fail silently-ish** If the backing URL later 404s (a repo renamed, a page removed), the source simply returns nothing. Keep the endpoint and its data under version control alongside the config.
  * **Secure the header** The HTTP header value is your only auth to the server — treat it like a secret, scope the token to read-only where the source is read-only, and prefer per-source tokens.
  * **Response time** The 20-second and 30-second budgets are firm. Cache upstream lookups and pre-shape responses so that a keyed GET resolves from memory rather than triggering a live cross-system query.

## 8 · Summary

Three sources, one pattern: host a URL, map its fields, let Signals pull.

Source| Endpoint shape| Lands in| Ops| Timeout  
---|---|---|---|---  
**List**|  GET /list → {data:[…]}| Attribute dropdown| GET| 30s  
**Data Source**|  GET/POST/PUT /x/{id}| Admin-Defined Table row| GET·POST·PUT| 20s  
**Chemical Source**|  GET /chem/{id} + structure| Stoichiometry (Quick Add)| GET| 20s  
  
### Next steps

  * ›Swap the in-memory dicts for a query against your real LIMS / registry / project system.
  * ›Add auth: require the configured header on every request and reject anything else.
  * ›For the Data Source, make POST/PUT actually persist so edits in Signals write back to your system.
  * ›Pair with **External Actions** and the **Search API** for round-trip workflows — look up a code here, then search Signals for everything using it.

## Tutorial Source Code & Downloadable Package

This tutorial includes a complete, runnable Python Flask reference implementation that provides endpoints for External Lists, External Data Sources, and External Chemical Sources.

### 📦 Download Package: `signals-data-sources-tutorial.zip`

**Package Contents:**

  * `app.py` — Full Flask reference server implementing `GET /api/lists/project-codes`, `GET/POST/PUT /api/data/records/{id}`, and `GET /api/chemical/lookup/{id}`.
  * `README.md` — Quick-start setup instructions, dependency requirements, and endpoint configuration guides.

[⬇️ Download Tutorial Package (.zip)](tutorials/signals-data-sources-tutorial.zip) [📄 View README.md](tutorials/01-external-lists-data-sources/README.md)
