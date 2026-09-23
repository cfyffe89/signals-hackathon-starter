import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load .env
dotenv_path = Path(__file__).parent.parent / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)
else:
    load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .signals_client import SignalsClient
from .ai_client import AIClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hackathon_starter")

app = FastAPI(
    title="Revvity Signals EMEA Hackathon 2026 Starter",
    description="Universal template for rapid prototyping with Signals Notebook REST APIs & AI",
    version="1.0.0"
)

# Auto-reload .env whenever a request arrives so editing .env in VS Code takes effect immediately
@app.middleware("http")
async def auto_reload_env(request: Request, call_next):
    if dotenv_path.exists():
        load_dotenv(dotenv_path, override=True)
    return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

signals_client = SignalsClient()
ai_client = AIClient()

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
DOCS_DIR = Path(__file__).parent.parent / "docs"

class AIPromptRequest(BaseModel):
    prompt: str = "Explain the significance of the force=true parameter when uploading child entities to Signals Notebook."

@app.get("/api/health")
def health():
    # Count installed packages
    import importlib.util
    core_pkgs = ["fastapi", "streamlit", "rdkit", "Bio", "pandas", "numpy", "openai", "google.genai", "PIL"]
    available_pkgs = [p for p in core_pkgs if importlib.util.find_spec(p.split('.')[0]) is not None]

    return {
        "status": "online",
        "pythonVersion": sys.version.split()[0],
        "installedPackages": available_pkgs,
        "signals": {
            "tenant": signals_client.base_url,
            "mockMode": signals_client.mock_mode
        },
        "ai": ai_client.check_status()
    }

@app.get("/api/test-signals")
def test_signals():
    """Validates Signals Notebook connection and fetches experiment list."""
    try:
        conn = signals_client.check_connection()
        experiments = signals_client.list_experiments(limit=5)
        return {
            "status": "success",
            "connection": conn,
            "experiments": experiments
        }
    except Exception as e:
        logger.error(f"Signals test failed: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

@app.post("/api/test-ai")
def test_ai(req: AIPromptRequest):
    """Executes a test prompt against Gemini / Hackathon Gateway."""
    try:
        res = ai_client.generate_text(req.prompt)
        return {"status": "success", "result": res}
    except Exception as e:
        logger.error(f"AI test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/docs-list")
def list_docs():
    """Lists available OpenAPI specs in docs/signals-api/."""
    yaml_dir = DOCS_DIR / "signals-api"
    specs = []
    if yaml_dir.exists():
        for f in yaml_dir.glob("*.yaml"):
            specs.append({
                "filename": f.name,
                "name": f.stem.capitalize(),
                "sizeKb": round(f.stat().st_size / 1024, 1)
            })
    return {"specs": sorted(specs, key=lambda x: x["filename"])}

@app.get("/api/docs/spec/{filename}")
def get_spec(filename: str):
    """Returns raw OpenAPI YAML spec for viewing in browser."""
    spec_path = DOCS_DIR / "signals-api" / filename
    if not spec_path.exists():
        raise HTTPException(status_code=404, detail="Spec not found")
    return FileResponse(spec_path, media_type="text/plain")

@app.get("/api/docs/cheat-sheet")
def get_cheat_sheet():
    """Returns the Signals Developer Cheat Sheet markdown."""
    sheet_path = DOCS_DIR / "SIGNALS_DEVELOPER_CHEAT_SHEET.md"
    if not sheet_path.exists():
        raise HTTPException(status_code=404, detail="Cheat sheet not found")
    return FileResponse(sheet_path, media_type="text/plain")

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    def index():
        return FileResponse(FRONTEND_DIR / "index.html")
