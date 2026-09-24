"""Seed a Signals tenant for the EMEA Hackathon 2026 (organisers only).

    python scripts/seed_tenant.py                        # DRY RUN (default): read-only, prints the plan
    python scripts/seed_tenant.py --apply                # create notebooks + experiments
    python scripts/seed_tenant.py --apply --global       # ...and materials + inventory (tenant-wide)
    python scripts/seed_tenant.py --prefix HACK26-TEST --teams 1 --parts notebooks,experiments

What it creates (content: seed/seed_data.json, fixtures: seed/fixtures/):
  notebooks    "<P> Reference Data" + "<P> Team NN" (one per team) with a "Team NN bench notes" experiment
  experiments  one example experiment per use case in the Reference Data notebook (texts, samples,
               reactions with stoichiometry, tasks with Required By dates, PDF/CSV attachments)
  materials    reagents in one materials library (tenant-wide, NOT in a notebook)
  inventory    a location tree (site > stability lab > chambers; stockroom > shelf) and one container per
               reagent with expiry dates around the event date (tenant-wide, NOT in a notebook)

Idempotent: everything is looked up by name first (containers by barcode) and only missing items are
created, so re-running after a partial failure is safe. Tenant-specific IDs (templates, inventory types,
field ids) are resolved by NAME from seed_data.json "tenant", so the same file works on any tenant.

Safety: dry run unless --apply. Materials and inventory can't be removed through the API (locations have
no DELETE; containers can only be disposed), so writing them also needs --global. Refuses to write to
read-only tenants. Never prints the API key. Uses SIGNALS_BASE_URL / SIGNALS_API_KEY from .env.
"""
import argparse
import json
import re
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend import config  # noqa: E402,F401  (loads .env)
from backend.signals_client import SignalsClient, SignalsError  # noqa: E402

SEED = ROOT / "seed"
READ_ONLY_HOSTS = ("sartraining", "demo.signalsresearch")
BLANK_CDXML = (b'<?xml version="1.0" encoding="UTF-8" ?><!DOCTYPE CDXML SYSTEM '
               b'"http://www.cambridgesoft.com/xml/cdxml.dtd" ><CDXML><page id="1"></page></CDXML>')


class Seeder:
    def __init__(self, sc, data, args):
        self.sc, self.d, self.a = sc, data, args
        self.apply = args.apply
        self.log_rows, self.missing, self.out = [], [], {"teams": {}, "experiments": {}, "materials": {}, "locations": {}}
        self.event = date.fromisoformat(args.event_date)

    # ------------------------------------------------------------------ plumbing
    def req(self, method, path, **kw):
        return self.sc._request(method, path, **kw)

    def log(self, status, what, detail=""):
        self.log_rows.append((status, what, detail))
        print(f"  {status:12} {what}{'  ' + detail if detail else ''}")

    def need(self, what, fix):
        self.missing.append((what, fix))
        self.log("MISSING", what, fix)

    def p(self, s, nn=None):
        s = s.replace("{P}", self.a.prefix)
        return s.replace("{NN}", f"{nn:02d}") if nn is not None else s

    def search(self, clauses, source=None, limit=100):
        return self.sc.search_entities({"$and": clauses}, limit=limit, source=source)

    def kw(self, field, value):
        return {"$match": {"field": field, "value": value, "mode": "keyword"}}

    def tag(self, field, value):
        # tag fields (materials.*, fields.*) need "in":"tags" + "as":"text" ("as":"string" -> 400)
        return {"$match": {"field": field, "value": value, "in": "tags", "as": "text", "mode": "keyword"}}

    NOT_TEMPLATE = {"$match": {"field": "isTemplate", "value": False}}  # IVT search also returns the location/container TYPES

    def children(self, eid):
        if not eid or eid.startswith("DRY:"):
            return []
        return self.req("GET", f"/entities/{eid}/children", params={"page[limit]": 100}).json().get("data", [])

    def child(self, eid, name, typ=None):
        for c in self.children(eid):
            at = c.get("attributes", {})
            if at.get("name") == name and (typ is None or at.get("type") == typ) and not at.get("flags", {}).get("isTrashed"):
                return c["id"]
        return None

    def create_entity(self, parent, body):
        params = {"digest": self.sc.get_digest(parent)} if parent else None
        return self.req("POST", "/entities", params=params, json_body=body).json()["data"]["id"]

    # ------------------------------------------------------------------ resolve tenant config (read-only)
    def resolve(self):
        t = self.d["tenant"]
        print("\n== Resolve tenant configuration (read-only)")
        self.tpl = {}
        for kind, name in (("sample", t["sample_template"]), ("task", t["task_template"]), ("experiment", t.get("experiment_template"))):
            if not name:
                continue
            rows = self.req("GET", "/entities", params={"includeTypes": kind, "includeOptions": "template", "page[limit]": 100}).json()["data"]
            hit = next((r["id"] for r in rows if r["attributes"].get("name") == name), None)
            if hit:
                self.tpl[kind] = hit
                self.log("OK", f"{kind} template '{name}'", hit)
            else:
                self.need(f"{kind} template '{name}'", f"Create it in Signals Configuration (or change tenant.{kind}_template)")
        self.sfield = self._fields("sample", "/samples/{}/properties", t["sample_fields"])
        self.tfield = self._fields("task", "/tasks/{}/properties", t["task_fields"])
        if "materials" in self.a.parts or "inventory" in self.a.parts:
            self._resolve_library(t["materials_library"])
        if "inventory" in self.a.parts:
            self._resolve_inventory(t)

    def _fields(self, kind, path, wanted):
        out = {}
        if kind not in self.tpl:
            return out
        props = self.req("GET", path.format(self.tpl[kind])).json()["data"]
        by_name = {p["attributes"].get("name"): p["id"] for p in props}
        for key, name in wanted.items():
            if key.startswith("_"):
                continue
            if name in by_name:
                out[key] = by_name[name]
            else:
                self.need(f"{kind} template field '{name}'", f"Add it to the {kind} template in Signals Configuration")
        self.log("OK", f"{kind} fields", json.dumps(out))
        return out

    def _resolve_library(self, name):
        libs = self.req("GET", "/materials/libraries", params={"name": name}).json()["data"]
        if not libs:
            self.lib = None
            return self.need(f"materials library '{name}'", "Enable/create it in Signals Configuration or change tenant.materials_library")
        a = libs[0]["attributes"]
        self.lib = {"name": a["name"], "fields": a["assets"]["fields"], "name_field": a["assets"].get("assetNameFieldId"),
                    "batch_fields": (a.get("batches") or {}).get("fields", [])}
        f = self.lib["fields"]
        self.lib["name_label"] = next((x["name"] for x in f if x["id"] == self.lib["name_field"]), None)
        self.lib["structure"] = next((x["id"] for x in f if x.get("dataType") == "CHEMICAL_DRAWING"), None)
        self.lib["cas"] = next((x["id"] for x in f if re.search(r"\bCAS\b", x.get("name", ""), re.I)), None)
        defaults = self.d["tenant"].get("material_field_defaults", {})
        self.lib["defaults"] = [{"id": x["id"], "value": defaults[x["name"]]} for x in f + self.lib["batch_fields"]
                                if defaults.get(x["name"]) is not None]
        mapped = {self.lib["name_field"], self.lib["structure"], self.lib["cas"]} | {x["id"] for x in self.lib["defaults"]}
        unmapped = [x["name"] for x in f + self.lib["batch_fields"] if x.get("mandatory") and x["id"] not in mapped]
        self.log("OK", f"materials library '{a['name']}'",
                 f"name={bool(self.lib['name_field'])} structure={bool(self.lib['structure'])} cas={bool(self.lib['cas'])}")
        if unmapped:
            self.need(f"mandatory library fields {unmapped}", "Give values in tenant.material_field_defaults (format per field type) or make them optional")

    def _resolve_inventory(self, t):
        self.itype = {}
        for et in ("location", "container"):
            rows = self.req("GET", "/inventory/types", params={"entityType": et, "page[limit]": 100}).json()["data"]
            for r in rows:
                self.itype[(et, r["attributes"]["name"])] = r["attributes"]
        for key, name in t["location_types"].items():
            if ("location", name) not in self.itype:
                self.need(f"location type '{name}' ({key})", "Create it in Signals Configuration > Inventory, or change tenant.location_types")
        ctype = self.itype.get(("container", t["container_type"]))
        if not ctype:
            return self.need(f"container type '{t['container_type']}'", "Create it or change tenant.container_type")
        self.cfields = {f["definition"]["title"]: f for f in ctype["fields"]}
        req = [n for n, f in self.cfields.items() if f["definition"].get("isRequired")]
        covered = {"Barcode", "Amount", "Status"} | {k for k, v in t["container_defaults"].items()}
        self.log("OK", f"container type '{t['container_type']}'", f"required fields: {req}")
        for n in req:
            if n not in covered:
                self.need(f"container field '{n}' is required", "Add a value in tenant.container_defaults")
        self.container_defaults = dict(t["container_defaults"])
        sec = self.cfields.get("Inventory Security")
        if sec and not self.container_defaults.get("Inventory Security"):
            opts = self.req("GET", f"/attributes/{sec['definition']['attributeListEid']}").json()["data"]["attributes"].get("options", [])
            self.container_defaults["Inventory Security"] = opts[0] if opts else None
            self.log("OK", "Inventory Security default", str(self.container_defaults["Inventory Security"]))

    # ------------------------------------------------------------------ notebooks
    def notebook(self, name, description):
        hits = [h for h in self.search([self.kw("type", "journal"), self.kw("name", name)])
                if h.get("attributes", {}).get("name") == name and not h["attributes"].get("flags", {}).get("isTrashed")]
        if hits:
            self.log("EXISTS", f"notebook '{name}'", hits[0]["id"])
            return hits[0]["id"]
        if not self.apply:
            self.log("WOULD CREATE", f"notebook '{name}'")
            return f"DRY:{name}"
        eid = self.create_entity(None, {"data": {"type": "journal", "attributes": {"name": name, "description": description}}})
        self.log("CREATED", f"notebook '{name}'", eid)
        return eid

    def experiment(self, nb, name, description):
        hit = self.child(nb, name, "experiment")
        if hit:
            self.log("EXISTS", f"  experiment '{name}'", hit)
            return hit
        if not self.apply:
            self.log("WOULD CREATE", f"  experiment '{name}'")
            return f"DRY:{name}"
        body = {"data": {"type": "experiment", "attributes": {"name": name, "description": description},
                         "relationships": {"ancestors": {"data": [{"type": "journal", "id": nb}]}}}}
        if "experiment" in self.tpl:
            body["data"]["relationships"]["template"] = {"data": {"type": "experiment", "id": self.tpl["experiment"]}}
        eid = self.create_entity(nb, body)
        self.log("CREATED", f"  experiment '{name}'", eid)
        return eid

    def seed_notebooks(self):
        nbs = self.d["notebooks"]
        print("\n== Notebooks")
        self.ref_nb = self.notebook(self.p(nbs["reference"]["name"]), self.p(nbs["reference"]["description"]))
        for nn in range(1, self.a.teams + 1):
            nb = self.notebook(self.p(nbs["team"]["name"], nn), self.p(nbs["team"]["description"], nn))
            exp = self.experiment(nb, self.p(nbs["team_experiment"]["name"], nn), self.p(nbs["team_experiment"]["description"], nn))
            self.out["teams"][f"{nn:02d}"] = {"notebook": nb, "experiment": exp}

    # ------------------------------------------------------------------ experiment content
    def seed_experiments(self):
        print("\n== Reference experiments")
        if not hasattr(self, "ref_nb"):
            self.ref_nb = self.notebook(self.p(self.d["notebooks"]["reference"]["name"]), "")
        exps = {}
        for x in self.d["experiments"]:  # pass 1: all experiments exist before links between them
            exps[x["key"]] = self.experiment(self.ref_nb, x["name"], x["description"])
        self.out["experiments"] = {k: v for k, v in exps.items()}
        for x in self.d["experiments"]:
            eid = exps[x["key"]]
            print(f"  -- {x['name']}  [{'; '.join(x['use_cases'])}]")
            for t in x.get("texts", []):
                self.text(eid, t["name"], t["html"])
            if x.get("reaction"):
                self.reaction(eid, x["reaction"])
            for att in x.get("attachments", []):
                self.attachment(eid, att["file"], att["mime"])
            if x.get("samples"):
                self.samples(eid, x["samples"])
            if x.get("tasks"):
                self.tasks(eid, x["tasks"], exps)

    def _create_child(self, eid, name, typ, fn):
        if self.child(eid, name, typ):
            return self.log("EXISTS", f"    {typ} '{name}'")
        if not self.apply:
            return self.log("WOULD CREATE", f"    {typ} '{name}'")
        for attempt in (1, 2, 3):
            try:
                fn()
                return self.log("CREATED", f"    {typ} '{name}'")
            except SignalsError as e:
                # the dev tenant sometimes answers 502/503/504 on uploads; a 504 can still have succeeded
                if attempt < 3 and re.search(r"-> 50[234]", str(e)):
                    time.sleep(5 * attempt)
                    if self.child(eid, name, typ):
                        return self.log("CREATED", f"    {typ} '{name}'", f"(after {str(e)[str(e).find('->'):][:8]})")
                    continue
                return self.log("ERROR", f"    {typ} '{name}'", str(e)[:200])

    def text(self, eid, name, html):
        # text/html upload = an editable Text element; the filename (no extension) becomes its name
        self._create_child(eid, name, "text", lambda: self.sc.upload_child_attachment(
            eid, name, f"<div>{html}</div>".encode(), "text/html"))

    def attachment(self, eid, rel, mime):
        path = SEED / rel
        name = path.name
        typ = "pdf" if mime == "application/pdf" else "uploadedResource"
        self._create_child(eid, name, typ, lambda: self.sc.upload_child_attachment(eid, name, path.read_bytes(), mime))

    def reaction(self, eid, r):
        # Verified route to a drawing WITH a stoichiometry table: upload a blank CDXML, append structures by
        # SMILES, then set the limiting reagent mass (Signals calculates moles and the other masses).
        # (Uploading an .rxn file gives a drawing with an EMPTY stoichiometry table that can't be updated.)
        def build():
            d = self.sc.upload_child_attachment(eid, r["name"], BLANK_CDXML, "chemical/x-cdxml")["data"]["id"]
            for pos in ("reactants", "products"):
                for smi in r[pos]:
                    self.req("POST", f"/chemicaldrawings/{d}/reaction/{pos}", params={"digest": self.sc.get_digest(d)},
                             json_body={"data": {"attributes": {"dataType": "smiles", "data": smi}}})
            st = self.req("GET", f"/stoichiometry/{d}").json()["data"]["attributes"]
            def row_for(smi):
                return next((x for x in st.get("reactants", []) if _canon(_v(x.get("smiles"))) == _canon(smi)), None)

            def patch(row, values):
                self.req("PATCH", f"/stoichiometry/{d}/{row['row_id']}", params={"digest": self.sc.get_digest(d)},
                         json_body={"data": {"attributes": {"values": values}}})
            # equivalents first, then the limiting mass: Signals recalculates the other masses from both
            for smi, eq in r.get("equivalents", {}).items():
                if row_for(smi):
                    patch(row_for(smi), {"eq": str(eq)})
            lim = r.get("limiting")
            if lim and row_for(lim["smiles"]):
                patch(row_for(lim["smiles"]), {"sm": lim["sm"], "limit": {"value": True}})
            for s in r.get("solvents", []):
                self.req("POST", f"/stoichiometry/{d}/solvents", params={"digest": self.sc.get_digest(d)},
                         json_body={"data": {"attributes": {"values": s}}})
        self._create_child(eid, r["name"], "chemicalDrawing", build)

    def _existing_rows(self, eid, container_type):
        cont = next((c["id"] for c in self.children(eid) if c["attributes"].get("type") == container_type), None)
        return len(self.children(cont)) if cont else 0

    def samples(self, eid, rows):
        if "sample" not in self.tpl:
            return self.log("SKIP", "    samples", "no sample template")
        have = self._existing_rows(eid, "samplesContainer")
        todo = rows[have:]
        if not todo:
            return self.log("EXISTS", f"    {len(rows)} samples")
        if not self.apply:
            return self.log("WOULD CREATE", f"    {len(todo)} samples", f"template {self.tpl['sample']}")
        for s in todo:
            fields = {self.sfield[k]: v for k, v in s.items() if k in self.sfield and not k.startswith("_")}
            try:
                self.sc.create_sample(eid, self.tpl["sample"], fields)
                self.log("CREATED", "    sample", s.get("description", ""))
            except SignalsError as e:
                if "amount" in s and self.sfield.get("amount") in fields:  # unit strings vary per tenant: retry without
                    fields.pop(self.sfield["amount"])
                    self.sc.create_sample(eid, self.tpl["sample"], fields)
                    self.log("CREATED", "    sample (no amount)", f"{s.get('description', '')}; amount rejected: {str(e)[:80]}")
                else:
                    self.log("ERROR", "    sample", str(e)[:200])

    def tasks(self, eid, rows, exps):
        if "task" not in self.tpl:
            return self.log("SKIP", "    tasks", "no task template")
        have = self._existing_rows(eid, "taskContainer")
        todo = rows[have:]
        if not todo:
            return self.log("EXISTS", f"    {len(rows)} tasks")
        if not self.apply:
            return self.log("WOULD CREATE", f"    {len(todo)} tasks", "with Required By dates")
        for t in todo:
            due = datetime.combine(self.event + timedelta(days=t["required_by_days"]), datetime.min.time(), timezone.utc) + timedelta(hours=9)
            fields = [{"id": self.tfield["required_by"], "content": {"value": due.strftime("%Y-%m-%dT%H:%M:%S.000Z")}}]
            if "requestor_comment" in self.tfield:
                fields.append({"id": self.tfield["requestor_comment"], "content": {"value": t["requestor_comment"]}})
            link = exps.get(t.get("link_to", ""))
            if link and "reference" in self.tfield:
                # "Experiment Link" is system-managed (400 "not editable"); "Reference ID" takes a values list
                fields.append({"id": self.tfield["reference"], "content": {"values": [{"eid": link}]}})
            body = {"data": {"type": "task", "attributes": {"fields": fields},
                             "relationships": {"ancestors": {"data": [{"type": "experiment", "id": eid}]},
                                               "template": {"data": {"type": "task", "id": self.tpl["task"]}}}}}
            try:
                self.create_entity(eid, body)
                self.log("CREATED", "    task", f"{t['requestor_comment']} (due {due.date()})")
            except SignalsError as e:
                if link:  # link fields are the least certain part: retry without
                    body["data"]["attributes"]["fields"] = fields[:-1]
                    self.create_entity(eid, body)
                    self.log("CREATED", "    task (no link)", f"{t['requestor_comment']}; link rejected: {str(e)[:80]}")
                else:
                    self.log("ERROR", "    task", str(e)[:200])

    # ------------------------------------------------------------------ materials (tenant-wide)
    def seed_materials(self):
        print("\n== Materials")
        if not getattr(self, "lib", None):
            return self.log("SKIP", "materials", "library not resolved")
        for m in self.d["materials"]:
            hits = self.search([self.kw("type", "asset"), self.tag(f"materials.{self.lib['name_label']}", m["name"])])
            hits = [h for h in hits if not h["attributes"].get("flags", {}).get("isTrashed")]
            if hits:
                self.out["materials"][m["name"]] = hits[0]["id"]
                self.log("EXISTS", f"material '{m['name']}'", hits[0]["id"])
                continue
            if not (self.apply and self.a.glob):
                self.log("WOULD CREATE", f"material '{m['name']}'", f"{self.lib['name']}, CAS {m['cas']}")
                continue
            fields = list(self.lib["defaults"])
            if self.lib["name_field"]:
                fields.append({"id": self.lib["name_field"], "value": m["name"]})
            if self.lib["structure"]:
                fields.append({"id": self.lib["structure"], "value": {"data": m["smiles"], "contentType": "chemical/x-daylight-smiles"}})
            if self.lib["cas"]:
                fields.append({"id": self.lib["cas"], "value": m["cas"]})
            try:
                res = self.req("POST", f"/materials/{self.lib['name']}/assets",
                               json_body={"data": {"type": "asset", "attributes": {"fields": fields}}}).json()["data"]
                self.out["materials"][m["name"]] = res["id"]
                self.log("CREATED", f"material '{m['name']}'", res["id"])
            except SignalsError as e:
                self.log("ERROR", f"material '{m['name']}'", str(e)[:200])

    # ------------------------------------------------------------------ inventory (tenant-wide)
    def seed_inventory(self):
        print("\n== Inventory")
        inv, t = self.d["inventory"], self.d["tenant"]
        ids = {}
        for loc in inv["locations"]:
            name, tname = self.p(loc["name"]), t["location_types"][loc["type"]]
            hits = [h for h in self.search([self.kw("type", "location"), self.kw("name", name), self.NOT_TEMPLATE], source="IVT")
                    if h.get("attributes", {}).get("name") == name]
            if hits:
                ids[loc["key"]] = hits[0]["id"]
                self.log("EXISTS", f"location '{name}'", hits[0]["id"])
                continue
            ltype = self.itype.get(("location", tname))
            if not (self.apply and self.a.glob) or not ltype:
                ids[loc["key"]] = f"DRY:{name}"
                self.log("WOULD CREATE", f"location '{name}'", f"type {tname}" + ("" if ltype else " (TYPE MISSING)"))
                continue
            attrs = {"name": name, "typeId": ltype["id"]}
            parent = ids.get(loc.get("parent", ""))
            if parent:
                attrs["ancestors"] = [{"id": _ivt_id(parent)}]
            try:
                res = self.req("POST", "/inventory/locations", json_body={"data": {"type": "inventoryLocation", "attributes": attrs}}).json()["data"]
                ids[loc["key"]] = res["id"]
                self.log("CREATED", f"location '{name}'", res["id"])
            except SignalsError as e:
                self.log("ERROR", f"location '{name}'", str(e)[:200])
        self.out["locations"] = ids
        shelf = ids.get("shelf_a", "")
        ctype = self.itype.get(("container", t["container_type"]))
        for i, c in enumerate(inv["containers"], 1):
            barcode = f"{self.a.prefix}-C{i:03d}"
            expiry = self.event + timedelta(days=c["expiry_days"])
            hits = self.search([self.kw("type", "container"), self.tag("fields.Barcode", barcode), self.NOT_TEMPLATE], source="IVT")
            if hits:
                self.log("EXISTS", f"container {barcode}", c["material"])
                continue
            asset = self.out["materials"].get(c["material"])
            if not (self.apply and self.a.glob) or not ctype or not asset or shelf.startswith("DRY:"):
                self.log("WOULD CREATE", f"container {barcode}", f"{c['material']} {c['amount']} {c['unit']}, expires {expiry}")
                continue
            try:
                batch = self._first_batch(asset)
                fields = [{"id": self.cfields["Expiration Date"]["id"], "content": {"value": f"{expiry}T00:00:00.000Z"}}] if "Expiration Date" in self.cfields else []
                for k, v in self.container_defaults.items():
                    if k not in ("Status",) and k in self.cfields and v is not None:
                        fields.append({"id": self.cfields[k]["id"], "content": {"value": v}})
                attrs = {"typeId": ctype["id"], "barcode": barcode, "amount": c["amount"], "unit": c["unit"],
                         "status": self.container_defaults.get("Status"), "location": {"id": _ivt_id(shelf)},
                         "description": f"{c['material']} (hackathon seed)", "fields": fields}
                if batch:
                    attrs["contents"] = [{"entityId": batch}]
                self.req("POST", "/inventory/containers", json_body={"data": {"type": "inventoryContainer", "attributes": attrs}})
                self.log("CREATED", f"container {barcode}", f"{c['material']}, expires {expiry}")
            except SignalsError as e:
                self.log("ERROR", f"container {barcode}", str(e)[:200])

    def _first_batch(self, asset_eid):
        try:
            a = self.req("GET", f"/materials/{asset_eid}").json()["data"]
            rel = a.get("relationships", {}).get("batches", {}).get("data") or []
            return rel[0]["id"] if rel else None
        except SignalsError:
            return None

    # ------------------------------------------------------------------ report
    def report(self):
        counts = {}
        for s, *_ in self.log_rows:
            counts[s] = counts.get(s, 0) + 1
        print("\n== Summary:", ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
        if self.missing:
            print("\n== Prerequisites missing on this tenant (do these in the UI, then re-run):")
            for what, fix in self.missing:
                print(f"  - {what}: {fix}")
        host = self.sc.base_url.split("//")[-1].split("/")[0]
        outdir = SEED / "output"
        outdir.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        rep = {"host": host, "prefix": self.a.prefix, "mode": "apply" if self.apply else "dry-run", "parts": self.a.parts,
               "at": stamp, "counts": counts, "missing": self.missing, "ids": self.out,
               "log": [{"status": s, "what": w, "detail": d} for s, w, d in self.log_rows]}
        path = outdir / f"seed_report_{host.split('.')[0]}_{rep['mode']}_{stamp}.json"
        path.write_text(json.dumps(rep, indent=2), encoding="utf-8")
        if self.apply and self.out["teams"]:
            lines = ["| Team | Notebook | Bench-notes experiment |", "|---|---|---|"]
            lines += [f"| {k} | `{v['notebook']}` | `{v['experiment']}` |" for k, v in self.out["teams"].items()]
            (outdir / f"team_sheet_{host.split('.')[0]}.md").write_text(
                f"# Team table sheet ({host}, prefix {self.a.prefix})\n\nSIGNALS_BASE_URL=https://{host}/api/rest/v1.0\n\n" + "\n".join(lines) + "\n",
                encoding="utf-8")
        print(f"\nReport: {path.relative_to(ROOT)}")


def _ivt_id(eid):
    """Inventory write endpoints take the bare UUID; search returns 'location:<uuid>:ivt'."""
    parts = eid.split(":")
    return parts[1] if len(parts) > 1 else eid


def _v(x):
    return x.get("value") if isinstance(x, dict) else x


def _canon(smi):
    """Order-insensitive atom-letter signature: matches our input SMILES to Signals' re-written SMILES without RDKit."""
    return "".join(sorted(re.sub(r"[^A-Za-z]", "", smi or "").upper()))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="write to the tenant (default: dry run)")
    ap.add_argument("--global", dest="glob", action="store_true", help="also write tenant-wide materials + inventory")
    ap.add_argument("--prefix", default="HACK26", help="name prefix for everything created (default HACK26)")
    ap.add_argument("--teams", type=int, default=6, help="number of team notebooks (default 6)")
    ap.add_argument("--parts", default="notebooks,experiments,materials,inventory")
    ap.add_argument("--event-date", default="2026-10-21", help="anchor for task due dates and container expiry dates")
    ap.add_argument("--data", default=str(SEED / "seed_data.json"))
    a = ap.parse_args()
    a.parts = [p.strip() for p in a.parts.split(",") if p.strip()]

    sc = SignalsClient()
    if sc.mock_mode:
        sys.exit("Set SIGNALS_BASE_URL and SIGNALS_API_KEY (.env) first: the seed script has no mock mode.")
    host = sc.base_url.split("//")[-1].split("/")[0]
    if a.apply and any(h in host for h in READ_ONLY_HOSTS):
        sys.exit(f"{host} is a read-only tenant. Refusing to write.")
    if a.apply and a.glob is False and {"materials", "inventory"} & set(a.parts):
        print("NOTE: materials/inventory are tenant-wide and can't be removed via the API; they stay dry-run without --global.")
    print(f"Tenant {host} | prefix {a.prefix} | teams {a.teams} | parts {','.join(a.parts)} | "
          f"{'APPLY' + (' + GLOBAL' if a.glob else '') if a.apply else 'DRY RUN (read-only)'}")

    s = Seeder(sc, json.loads(Path(a.data).read_text(encoding="utf-8")), a)
    t0 = time.time()
    s.resolve()
    if "notebooks" in a.parts:
        s.seed_notebooks()
    if "experiments" in a.parts:
        s.seed_experiments()
    if "materials" in a.parts:
        s.seed_materials()
    if "inventory" in a.parts:
        s.seed_inventory()
    s.report()
    print(f"Done in {time.time() - t0:.0f}s.")


if __name__ == "__main__":
    main()
