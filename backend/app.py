import os
import sys
import logging
import json
from pathlib import Path
from dotenv import dotenv_values

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hackathon_starter")

dotenv_path = Path(__file__).parent.parent / ".env"
dotenv_example_path = Path(__file__).parent.parent / ".env.example"

import re
import base64

def parse_secret_bundle(raw_str: str) -> dict:
    """Robustly parses multi-line, JSON, escaped newlines, or semicolon-delimited secret bundles."""
    if not raw_str or not isinstance(raw_str, str):
        return {}
    raw = raw_str.strip()

    # Check if base64 encoded
    try:
        decoded = base64.b64decode(raw).decode("utf-8")
        if ("SIGNALS_" in decoded or "GEMINI_" in decoded) and ("=" in decoded or "{" in decoded):
            raw = decoded.strip()
    except Exception:
        pass

    # Unescape literal \n or \r\n if present
    raw = raw.replace("\\r\\n", "\n").replace("\\n", "\n")

    # Check if JSON or Python dict
    if raw.startswith("{") and raw.endswith("}"):
        try:
            return json.loads(raw)
        except Exception:
            try:
                import ast
                val = ast.literal_eval(raw)
                if isinstance(val, dict):
                    return val
            except Exception:
                pass

    res = {}
    lines = re.split(r"[\r\n;]+", raw)
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip("'\"")
        if k and v:
            res[k] = v
    return res

def get_bundle_secret() -> str:
    """Checks for single bundled secret in common environment variables or auto-detects any variable containing the keys."""
    # 1. Direct check for HACKATHON first!
    val = os.getenv("HACKATHON")
    if val and val.strip():
        return val

    # 2. Common conventional names
    for name in ["ENV_FILE", "APP_ENV", "HACKATHON_ENV", "CODESPACE_ENV", "SECRETS", "ENV", "HACKATHON_SECRETS", "KEYS", "DOTENV"]:
        val = os.getenv(name)
        if val and val.strip():
            return val

    # 3. Dynamic auto-detection: scan all env vars for any string containing Signals or Gemini keys
    for k, v in os.environ.items():
        if not v or not isinstance(v, str) or k in ("PATH", "LS_COLORS", "PROMPT"):
            continue
        if ("SIGNALS_" in v or "GEMINI_" in v or "AI_GATEWAY_" in v) and ("=" in v or "{" in v):
            return v
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

app = FastAPI(
    title="Revvity Signals EMEA Hackathon 2026 Starter",
    description="Universal template for rapid prototyping with Signals Notebook REST APIs & AI",
    version="1.0.0"
)

def sync_continue_config():
    """Automatically populates Continue.dev config (schema v1) in user home with API key from .env."""
    try:
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        gateway_key = os.getenv("AI_GATEWAY_KEY", "")
        if not (gemini_key or gateway_key):
            return

        is_valid_gemini = bool(gemini_key and "your-" not in gemini_key and "your_" not in gemini_key)
        is_valid_gateway = bool(gateway_key and "your-" not in gateway_key and "your_" not in gateway_key)
        active_key = gemini_key if is_valid_gemini else ""

        # Remove any conflicting/legacy workspace config.yaml that causes merge flickering
        ws_yaml = Path(__file__).parent.parent / ".continue" / "config.yaml"
        if ws_yaml.exists():
            try:
                ws_yaml.unlink()
            except Exception:
                pass

        # 1. Modern Continue config.yaml (schema v1 with explicit roles)
        home_continue = Path.home() / ".continue"
        home_continue.mkdir(parents=True, exist_ok=True)
        yaml_path = home_continue / "config.yaml"

        system_msg = (
            "You are an expert pair-programmer for the Revvity Signals EMEA Hackathon 2026.\n"
            "Reference documentation in docs/ (including docs/Full-Guide-Redraft-v3.html, docs/SIGNALS_DEVELOPER_CHEAT_SHEET.md, and docs/signals-api/) "
            "provides architecture, API schemas, and JSON:API 1.0 patterns.\n"
            "CRITICAL ARCHITECTURE RULES:\n"
            "1. docs/Full-Guide-Redraft-v3.html is strictly for architectural reference and payload structures.\n"
            "2. The guide contains illustrative examples written in Flask. NEVER use or generate Flask code for this project.\n"
            "3. The project standardizes on FastAPI (backend/app.py) and Streamlit (app_streamlit.py on port 8501) with RDKit and Google GenAI.\n"
            "4. Always adapt any reference workflows from the guide into FastAPI endpoints or Streamlit components."
        )

        yaml_content = f"""name: Signals Hackathon Copilot
version: 1.0.0
schema: v1

systemMessage: |
  You are an expert pair-programmer for the Revvity Signals EMEA Hackathon 2026.
  
  STRICT SIGNALS API GROUNDING (NEVER GUESS ENDPOINTS):
  1. Revvity Signals Notebook uses a proprietary JSON:API 1.0 specification. NEVER guess, invent, or extrapolate endpoints (e.g. do NOT generate /api/experiments, /drawings, or /reactions).
  2. ONLY use exact endpoints found in docs/API_CATALOG.md and docs/signals-api/*.yaml.
  3. ALWAYS check backend/signals_client.py first — pre-tested, verified helper methods already exist for get_chemical_drawing, get_stoichiometry, create_experiment, search_materials, and upload_child_attachment.
  4. Standard entity/material operations require strict JSON:API envelopes: {{"data": {{"type": "<type>", "attributes": {{...}}}}}}.
  5. Child element uploads MUST include ?force=true on the URL.
  
  ARCHITECTURE CONSTRAINTS:
  1. Standardize on FastAPI (backend/app.py) and Streamlit (app_streamlit.py on port 8501). NEVER generate Flask code.

models:
  - name: Gemini 3.6 Flash
    provider: gemini
    model: gemini-3.6-flash
    apiKey: "{active_key}"
    roles:
      - chat
      - edit
      - apply
  - name: Gemini 1.5 Flash
    provider: gemini
    model: gemini-1.5-flash
    apiKey: "{active_key}"
    roles:
      - chat
      - edit
      - apply
"""

        if not yaml_path.exists() or yaml_path.read_text(encoding="utf-8").strip() != yaml_content.strip():
            yaml_path.write_text(yaml_content, encoding="utf-8")
            logger.info(f"Synced Continue YAML config into {yaml_path}")

        # 2. Write config.json for backward compatibility
        json_path = home_continue / "config.json"
        json_data = {
            "systemMessage": "You are an expert pair-programmer for Revvity Signals Hackathon 2026. Consult docs/ for API schemas. docs/Full-Guide-Redraft-v3.html is for reference only (its examples use Flask). NEVER use or generate Flask code; always use FastAPI and Streamlit.",
            "models": [
                {
                    "title": "Gemini 3.6 Flash",
                    "provider": "gemini",
                    "model": "gemini-3.6-flash",
                    "apiKey": active_key
                },
                {
                    "title": "Gemini 1.5 Flash",
                    "provider": "gemini",
                    "model": "gemini-1.5-flash",
                    "apiKey": active_key
                }
            ]
        }
        json_text = json.dumps(json_data, indent=2) + "\n"
        if not json_path.exists() or json_path.read_text(encoding="utf-8").strip() != json_text.strip():
            json_path.write_text(json_text, encoding="utf-8")
            logger.info(f"Synced Continue JSON config into {json_path}")

        # 3. Sync ~/.continue/prompts/*.prompt for slash commands (/signals, /signals-drawing, /signals-action)
        home_prompts = home_continue / "prompts"
        home_prompts.mkdir(parents=True, exist_ok=True)
        ws_prompts_dir = Path(__file__).parent.parent / ".continue" / "prompts"
        if ws_prompts_dir.exists():
            for p_file in ws_prompts_dir.glob("*.prompt"):
                (home_prompts / p_file.name).write_text(p_file.read_text(encoding="utf-8"), encoding="utf-8")
            logger.info(f"Synced slash prompts into {home_prompts}")

        # 4. Auto-approve terminal/bash execution so Continue doesn't block on every command
        permissions_path = home_continue / "permissions.yaml"
        perm_yaml = """allow:
  - Bash
  - "Bash(*)"
  - Read
  - "Read(*)"
  - Write
  - "Write(*)"
  - Edit
  - "Edit(*)"
ask: []
exclude: []
"""
        if not permissions_path.exists() or permissions_path.read_text(encoding="utf-8").strip() != perm_yaml.strip():
            permissions_path.write_text(perm_yaml, encoding="utf-8")
            logger.info(f"Synced Continue permissions.yaml into {permissions_path}")

    except Exception as e:
        logger.warning(f"Continue config sync note: {e}")

sync_continue_config()

_last_env_mtime = 0.0

# Auto-reload .env only when the file is actually modified on disk
@app.middleware("http")
async def auto_reload_env(request: Request, call_next):
    global _last_env_mtime
    if dotenv_path.exists():
        try:
            mtime = dotenv_path.stat().st_mtime
            if mtime > _last_env_mtime:
                _last_env_mtime = mtime
                smart_load_env(dotenv_path)
                sync_continue_config()
        except Exception:
            pass
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
    prompt: str = "Summarize the active Signals Notebook experiments retrieved from the API, identify key research themes, and recommend next scientific priorities."
    include_experiments: bool = True

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
    """
    Executes an AI synthesis prompt against Gemini / Hackathon Gateway.
    By default, incorporates live Signals Notebook experiment data retrieved via API as grounding context.
    """
    try:
        prompt_to_send = req.prompt
        if req.include_experiments:
            try:
                exps = signals_client.list_experiments(limit=10)
                exp_lines = []
                for e in exps:
                    exp_lines.append(f"- Experiment [{e.get('eid', 'N/A')}]: '{e.get('name', 'Untitled')}' (Modified: {e.get('modifiedAt', 'N/A')})")
                context_str = "\n".join(exp_lines)
                prompt_to_send = (
                    f"{req.prompt}\n\n"
                    f"### Ground-Truth Signals Notebook API Experiment Data (GET /entities):\n"
                    f"{context_str}\n\n"
                    f"Please synthesize these active lab experiments into an executive overview highlighting project focus areas and actionable next steps."
                )
            except Exception as ex_err:
                logger.warning(f"Could not load experiments context for AI: {ex_err}")

        res = ai_client.generate_text(
            prompt=prompt_to_send,
            system_instruction=(
                "You are an expert scientific lab informatics copilot for Revvity Signals Notebook. "
                "Analyze experimental data accurately, highlighting key findings, active chemistry/biology workflows, and actionable next steps."
            )
        )
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
