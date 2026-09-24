"""FastAPI app: the "API" half of the starter (port 8000).

Run:  uvicorn backend.app:app --reload --port 8000        (docs at /docs)
Shows: reading Signals (experiments, drawings, materials), grounded AI answers (/api/ask),
the knowledge pack (/api/knowledge), and an External Action page (/action?__eid=...).
"""
import html
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response
from pydantic import BaseModel

from . import config  # noqa: F401  (loads .env / Codespaces secrets)
from .ai_client import AIClient
from .context import experiment_context, structure_context
from .knowledge import find_endpoints, knowledge_block, search_knowledge
from .signals_client import SignalsClient, SignalsError

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="Signals Hackathon Starter API",
              description="Signals REST API + grounded AI examples. Edit backend/app.py to add your own routes.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
sc, ai = SignalsClient(), AIClient()
FRONTEND = Path(__file__).resolve().parents[1] / "frontend"


def _signals(fn, *a, **kw):
    try:
        return fn(*a, **kw)
    except SignalsError as e:
        raise HTTPException(502, str(e))


# ------------------------------------------------------------------ status
@app.get("/api/health")
def health():
    return {"signals": sc.check_connection(), "ai": ai.check_status()}


# ------------------------------------------------------------------ Signals reads
@app.get("/api/experiments")
def experiments(limit: int = 15):
    return _signals(sc.list_experiments, limit)


@app.get("/api/experiments/{eid}/context")
def experiment_text(eid: str):
    """The text the AI sees for an experiment: its fields plus every text/table/drawing child."""
    return _signals(experiment_context, sc, eid)


@app.get("/api/drawings")
def drawings(limit: int = 10):
    return _signals(sc.list_chemical_drawings, limit)


@app.get("/api/structure/{eid}")
def structure(eid: str, format: str = "svg"):
    body = _signals(sc.get_chemical_drawing, eid, format)
    return Response(body, media_type="image/svg+xml" if format == "svg" else "text/plain")


@app.get("/api/materials")
def materials(q: str = "", limit: int = 10):
    return _signals(sc.search_materials, q, limit)


# ------------------------------------------------------------------ knowledge + AI
@app.get("/api/knowledge")
def knowledge(q: str, k: int = 4):
    """Search the Signals knowledge pack (docs/signals) and the endpoint index."""
    return {"chunks": search_knowledge(q, k), "endpoints": find_endpoints(q)}


class AskRequest(BaseModel):
    question: str
    eid: Optional[str] = None          # ground in this experiment / entity
    smiles: Optional[str] = None       # ground in this structure
    use_knowledge: bool = True         # add API / integration docs


@app.post("/api/ask")
def ask(req: AskRequest):
    """Grounded AI: optional Signals record context + optional knowledge-pack context."""
    records, sources = "", []
    if req.eid:
        ctx = _signals(experiment_context, sc, req.eid)
        records, sources = ctx["text"], ctx["sources"]
    if req.smiles:
        records += "\n\n" + structure_context(req.smiles)
    know = knowledge_block(req.question, k=4) if req.use_knowledge else ""
    out = ai.ask(req.question, records=records, knowledge=know)
    return {**out, "sources": sources, "knowledge_used": bool(know)}


# ------------------------------------------------------------------ External Action demo
@app.get("/action", response_class=HTMLResponse)
def external_action(eid: str = Query(alias="__eid")):
    """
    Register in Signals Configuration › External Actions with URL https://<your-codespace>-8000.app.github.dev/action
    (GET, parameter __eid, open in dialog). Signals opens this page in the user's browser.
    """
    ent = _signals(sc.get_entity, eid)
    name = html.escape(ent.get("attributes", {}).get("name", eid))
    summary = ai.ask("Summarise this experiment in 3 bullet points and flag anything that looks incomplete.",
                     records=_signals(experiment_context, sc, eid)["text"], knowledge="")
    body = html.escape(summary["text"]).replace("\n", "<br>")
    return f"""<!doctype html><meta charset="utf-8"><title>AI summary</title>
<body style="font-family:system-ui;margin:1.5rem;max-width:760px">
<h3>{name}</h3><div>{body}</div><p style="color:#666;font-size:.85em">{html.escape(summary['source'])}</p>
<button onclick="window.parent.postMessage(['closeAndContinue',[]],'*')">Close</button>
</body>"""


# ------------------------------------------------------------------ frontend
@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")
