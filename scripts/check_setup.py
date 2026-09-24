"""Check the starter works:  python scripts/check_setup.py
Runs in whatever mode your .env gives (mock if keys are missing). Exercises the knowledge pack,
the Signals client, the AI client and every FastAPI route. Exit code 1 if anything fails.

    python scripts/check_setup.py --demo    # also: a real AI round trip, the Continue config, running apps, Codespace URLs
"""
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
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
nbs = []
check("list_notebooks", lambda: (nbs.extend(sc.list_notebooks(100)), f"{len(nbs)} notebooks")[1])
check("list_experiments", lambda: len(sc.list_experiments(3)))
if nbs:
    check("list_notebook_experiments", lambda: len(sc.list_notebook_experiments(nbs[0]["eid"])))
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
check("GET /api/notebooks", lambda: len(client.get("/api/notebooks").json()))
exps = client.get("/api/experiments?limit=3").json()
check("GET /api/experiments", lambda: len(exps))
check("GET /api/knowledge", lambda: len(client.get("/api/knowledge", params={"q": "search keyword mode"}).json()["chunks"]))
check("POST /api/ask", lambda: client.post("/api/ask", json={"question": "How do I list experiments?"}).json()["source"])
if exps and isinstance(exps, list):
    check("GET /action", lambda: client.get("/action", params={"__eid": exps[0]["eid"]}).status_code)


def ai_round_trip():
    r = ai.generate_text("Reply with the single word OK.", max_tokens=1024)  # thinking models need headroom
    if r["source"] in ("mock", "error"):
        raise RuntimeError(r["text"][:150])
    return f"{r['source']}: {r['text'][:20]}"


def continue_config():
    path = Path.home() / ".continue" / "config.yaml"
    if not path.exists():
        raise FileNotFoundError("run: python scripts/setup_continue.py, then Developer: Reload Window")
    text = path.read_text(encoding="utf-8")
    models = text.split("\nmodels:", 1)[1].split("\ncontext:", 1)[0] if "\nmodels:" in text else ""
    return f"{models.count('- name:')} model(s)"   # count models only, not the context providers


if "--demo" in sys.argv:
    import requests
    from backend.config import is_placeholder
    print("\n6. Demo readiness")
    names = ["SIGNALS_BASE_URL", "SIGNALS_API_KEY", "GEMINI_API_KEY", "AI_GATEWAY_URL", "AI_GATEWAY_KEY", "AI_MODEL"]
    found = [n for n in names if not is_placeholder(os.getenv(n, ""))]
    src = "HACKATHON secret" if os.getenv("HACKATHON") else ("Codespaces secrets/env" if os.getenv("CODESPACES") else ".env/env")
    print(f"  info  settings found via {src}: {', '.join(found) or 'none'} (values are never printed)")
    check("AI round trip", ai_round_trip)
    check("Continue config", continue_config)
    check("Continue slash prompts", lambda: sorted(p.stem for p in (ROOT / ".continue" / "prompts").glob("*.md")))
    for port, path in ((8000, "/api/health"), (8501, "/")):
        check(f"app running on port {port}", lambda port=port, path=path: requests.get(f"http://localhost:{port}{path}", timeout=5).status_code)
    if not results[-1] or not results[-2]:
        print("  hint  start the apps: ./scripts/start.sh   (logs: /tmp/api.log, /tmp/ui.log)")
    if os.getenv("CODESPACE_NAME"):
        dom = os.getenv("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "app.github.dev")
        print(f"  info  Streamlit:    https://{os.environ['CODESPACE_NAME']}-8501.{dom}")
        print(f"  info  FastAPI docs: https://{os.environ['CODESPACE_NAME']}-8000.{dom}/docs")

print(f"\n{sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
