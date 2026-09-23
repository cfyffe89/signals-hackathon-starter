import os
import sys
import logging
import json
from pathlib import Path
from dotenv import dotenv_values

dotenv_path = Path(__file__).parent.parent / ".env"
dotenv_example_path = Path(__file__).parent.parent / ".env.example"

def parse_secret_bundle(raw_str: str) -> dict:
    """Parses a multi-line KEY=VAL string or JSON object into a dict."""
    raw = (raw_str or "").strip()
    if not raw:
        return {}
    if raw.startswith("{") and raw.endswith("}"):
        try:
            return json.loads(raw)
        except Exception:
            pass
    res = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        res[k.strip()] = v.strip().strip("'\"")
    return res

def get_bundle_secret() -> str:
    """Checks for single bundled secret in common environment variables."""
    for name in ["ENV_FILE", "APP_ENV", "HACKATHON_ENV", "CODESPACE_ENV", "SECRETS"]:
        val = os.getenv(name)
        if val and val.strip():
            return val
    return ""

def init_env_file():
    """Seeds .env from single secret bundle (ENV_FILE) or .env.example with individual secrets."""
    try:
        # 1. Single-secret bundle support
        bundle = get_bundle_secret()
        if bundle:
            parsed = parse_secret_bundle(bundle)
            if parsed:
                lines = [f"{k}={v}" for k, v in parsed.items()]
                dotenv_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                for k, v in parsed.items():
                    os.environ[k] = str(v)
                logger.info("Initialized .env from single secret bundle.")
                return

        # 2. Individual secrets from .env.example
        if not dotenv_path.exists() and dotenv_example_path.exists():
            content = dotenv_example_path.read_text(encoding="utf-8")
            for var in ["SIGNALS_BASE_URL", "SIGNALS_API_KEY", "GEMINI_API_KEY", "AI_GATEWAY_URL", "AI_GATEWAY_KEY"]:
                val = os.getenv(var)
                if val and "your-" not in val:
                    lines = content.splitlines()
                    new_lines = []
                    for line in lines:
                        if line.startswith(f"{var}="):
                            new_lines.append(f"{var}={val}")
                        else:
                            new_lines.append(line)
                    content = "\n".join(new_lines) + "\n"
            dotenv_path.write_text(content, encoding="utf-8")
    except Exception as e:
        logger.warning(f"Note creating .env: {e}")

def smart_load_env(path: Path):
    """
    Intelligently merges .env and secret bundles with the system environment:
    - Never overwrites real system environment variables with placeholder dummy values ('your-...').
    - Allows user edits in .env (real non-dummy values) to update the environment.
    """
    bundle = get_bundle_secret()
    if bundle:
        parsed = parse_secret_bundle(bundle)
        for k, v in parsed.items():
            if v and "your-" not in str(v):
                os.environ[k] = str(v)

    if not path.exists():
        return
    values = dotenv_values(path)
    for k, v in values.items():
        if v is None:
            continue
        v_str = str(v).strip().strip("'\"")
        current = os.environ.get(k)
        if current and "your-" not in current and ("your-" in v_str or not v_str):
            continue
        os.environ[k] = v_str

init_env_file()
smart_load_env(dotenv_path)

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

def sync_continue_config():
    """Automatically populates Continue.dev config in both workspace and user home with API key from .env."""
    try:
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        gateway_key = os.getenv("AI_GATEWAY_KEY", "")
        if not (gemini_key or gateway_key):
            return

        targets = [
            Path(__file__).parent.parent / ".continue" / "config.json",
            Path.home() / ".continue" / "config.json"
        ]

        for target in targets:
            data = {}
            if target.exists():
                try:
                    with open(target, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    data = {}
            else:
                target.parent.mkdir(parents=True, exist_ok=True)

            models = data.get("models", [])
            if not models:
                models = [
                    {
                        "title": "Gemini 3.5 Flash (Signals Copilot)",
                        "provider": "gemini",
                        "model": "gemini-3.5-flash",
                        "apiKey": gemini_key if "your-" not in gemini_key else ""
                    }
                ]
                data["models"] = models
            else:
                for m in models:
                    if m.get("provider") == "gemini" and gemini_key and "your-" not in gemini_key:
                        m["apiKey"] = gemini_key
                    elif m.get("provider") == "openai" and gateway_key and "your-" not in gateway_key:
                        m["apiKey"] = gateway_key

            with open(target, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Synced AI credentials into {target}")
    except Exception as e:
        logger.warning(f"Continue config sync note: {e}")

sync_continue_config()

# Auto-reload .env whenever a request arrives so editing .env in VS Code takes effect immediately
@app.middleware("http")
async def auto_reload_env(request: Request, call_next):
    if dotenv_path.exists():
        smart_load_env(dotenv_path)
        sync_continue_config()
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
