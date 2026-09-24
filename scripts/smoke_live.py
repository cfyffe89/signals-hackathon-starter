"""Live smoke test for backend/signals_client.py against a real Signals tenant.

    SIGNALS_BASE_URL=... SIGNALS_API_KEY=... SIGNALS_SAMPLE_TEMPLATE_EID=sample:... \
    python scripts/smoke_live.py [--write --notebook journal:...]

Read-only by default. With --write it creates one experiment (+ a sample, an HTML note and a plate container) in the
--notebook you name and moves it to the trash at the end. Never prints the API key.
"""
import os, sys, time, uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend import config  # noqa: E402,F401  (loads .env / Codespaces secrets)
from backend.signals_client import SignalsClient, SignalsError  # noqa: E402

WRITE = "--write" in sys.argv
sc = SignalsClient()
results = []


def step(name, fn):
    t = time.time()
    try:
        info = fn()
        results.append(("PASS", name, info))
    except Exception as e:  # noqa: BLE001
        results.append(("FAIL", name, f"{type(e).__name__}: {str(e)[:160]}"))
    print(f"{results[-1][0]:4} {name:34} {str(results[-1][2])[:110]}  ({time.time()-t:.1f}s)")


assert not sc.mock_mode, "Set SIGNALS_BASE_URL and SIGNALS_API_KEY (mock mode is on)"
step("check_connection", lambda: sc.check_connection()["status"])
step("get_current_user", lambda: sc.get_current_user().get("userId"))
step("get_version", lambda: sc.get_version())
step("list_notebooks", lambda: f"{len(sc.list_notebooks(5))} notebooks")
exps = []
step("list_experiments", lambda: (exps.extend(sc.list_experiments(5)), f"{len(exps)}: {exps[0]['name'][:40] if exps else ''}")[1])
if exps:
    step("get_entity", lambda: sc.get_entity(exps[0]["eid"])["attributes"]["type"])
    step("list_child_entities", lambda: f"{len(sc.list_child_entities(exps[0]['eid']))} children")
drawings = []
step("list_chemical_drawings", lambda: (drawings.extend(sc.list_chemical_drawings(3)), f"{len(drawings)}; smiles[0]={str(drawings[0]['smiles'])[:30] if drawings else None}")[1])
if drawings:
    d = drawings[0]["id"]
    step("export_entity svg", lambda: f"{len(sc.export_entity(d, 'svg'))} chars svg")
    step("export_entity mol", lambda: sc.export_entity(d, "mol").splitlines()[3][:30])
    step("get_stoichiometry", lambda: list(sc.get_stoichiometry(d).keys()))
step("chemistry_search substructure", lambda: f"{len(sc.chemistry_search('c1ccccc1', limit=5))} hits")
step("chemistry_search exact", lambda: f"{len(sc.chemistry_search('c1ccccc1', exact=True, limit=5))} hits")
step("search_materials", lambda: f"{len(sc.search_materials('', 5))} assets")
step("list_material_libraries", lambda: f"{len(sc.list_material_libraries())} libraries")
step("search_containers (IVT)", lambda: f"{len(sc.search_containers('', 5))} containers")
step("list_inventory_types", lambda: f"{len(sc.list_inventory_types())} container types")
cont = []
step("get_container", lambda: (cont.extend(sc.search_containers("", 1)), sc.get_container(cont[0]["id"])["barcode"] if cont else "no containers")[1])
if cont:
    step("find_containers_by_barcode", lambda: f"{len(sc.find_containers_by_barcode([sc.get_container(cont[0]['id'])['barcode'], 'NOPE-000']))} found")

if WRITE:
    nb = sys.argv[sys.argv.index("--notebook") + 1] if "--notebook" in sys.argv else ""
    assert nb.startswith("journal:"), "--write needs --notebook journal:... (a notebook you may write in)"
    tpl = os.getenv("SIGNALS_SAMPLE_TEMPLATE_EID", "")
    created = {}
    step("create_experiment", lambda: created.setdefault("exp", sc.create_experiment(f"ZZ smoke {uuid.uuid4().hex[:6]}", nb, "starter smoke test"))["id"])
    if created.get("exp"):
        eid = created["exp"]["id"]
        step("  ...is inside the notebook", lambda: [a["id"] for a in sc.get_entity(eid)["relationships"]["ancestors"]["data"]] and "ok")
        step("upload_child_attachment html", lambda: sc.upload_child_attachment(eid, "note.html", b"<p>smoke</p>", "text/html")["data"]["id"][:30])
        if tpl:
            step("create_sample (template)", lambda: sc.create_sample(eid, tpl)["id"][:30])
        pcs = []
        step("create_plate_container", lambda: pcs.append(sc.create_plate_container(eid, 8, 12, 1)) or pcs[0][:30])
        if pcs:
            step("set_plate_wells (umolar)", lambda: sc.set_plate_wells(pcs[0], "Concentration", {"A1": "10 umolar", "A2": "5 umolar"}) and "ok")
            step("export_plates_csv", lambda: sc.export_plates_csv(pcs[0]).splitlines()[1][:40])
        step("cleanup: trash experiment", lambda: sc._request("DELETE", f"/entities/{eid}", params={"force": "true"}).status_code)

fails = [r for r in results if r[0] == "FAIL"]
print(f"\n{len(results) - len(fails)} passed, {len(fails)} failed")
sys.exit(1 if fails else 0)
