"""Check the starter works:  python scripts/check_setup.py
Runs in whatever mode your .env gives (mock if keys are missing). Exercises the knowledge pack,
the Signals client, the AI client and every FastAPI route. Exit code 1 if anything fails.
"""
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
results = []


def check(name, fn):
    try:
        info = fn()
        results.append(True)
        print(f"  OK    {name}: {str(info)[:100]}")
    except Exception as e:  # noqa: BLE001
        results.append(False)
        print(f"  FAIL  {name}: {type(e).__name__}: {str(e)[:160]}")
        if "-v" in sys.argv:
            traceback.print_exc()


print("1. Packages")
for mod in ["fastapi", "streamlit", "requests", "dotenv", "rdkit"]:
    check(mod, lambda m=mod: __import__(m).__name__)

from backend.signals_client import SignalsClient  # noqa: E402
from backend.ai_client import AIClient  # noqa: E402
from backend.knowledge import search_knowledge, find_endpoints  # noqa: E402

sc, ai = SignalsClient(), AIClient()
print(f"\n2. Signals client ({'MOCK' if sc.mock_mode else 'LIVE: ' + sc.base_url})")
check("connection", lambda: sc.check_connection()["status"])
check("list_experiments", lambda: len(sc.list_experiments(3)))
check("list_chemical_drawings", lambda: len(sc.list_chemical_drawings(2)))
check("search_materials", lambda: len(sc.search_materials("", 3)))
print(f"\n3. AI client ({ai.check_status()})")
print("\n4. Knowledge pack")
check("search_knowledge", lambda: [c["source"] for c in search_knowledge("create a sample from a template", 2)])
check("find_endpoints", lambda: find_endpoints("materials libraries")[0][:60])
print("\n5. FastAPI routes")
from fastapi.testclient import TestClient  # noqa: E402
from backend.app import app  # noqa: E402

client = TestClient(app)
check("GET /api/health", lambda: client.get("/api/health").json()["signals"]["status"])
exps = client.get("/api/experiments?limit=3").json()
check("GET /api/experiments", lambda: len(exps))
check("GET /api/knowledge", lambda: len(client.get("/api/knowledge", params={"q": "search keyword mode"}).json()["chunks"]))
check("POST /api/ask", lambda: client.post("/api/ask", json={"question": "How do I list experiments?"}).json()["source"])
if exps and isinstance(exps, list):
    check("GET /action", lambda: client.get("/action", params={"__eid": exps[0]["eid"]}).status_code)

print(f"\n{sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
