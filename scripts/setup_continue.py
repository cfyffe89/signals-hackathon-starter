"""Write ~/.continue/config.yaml for the Continue extension from .env (run automatically on Codespace create).

Uses GEMINI_API_KEY (Gemini) or AI_GATEWAY_URL + AI_GATEWAY_KEY (OpenAI-compatible gateway).
Re-run after changing keys:  python scripts/setup_continue.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend import config  # noqa: E402,F401  (loads .env)
import os  # noqa: E402

model = os.getenv("AI_MODEL", "gemini-3.6-flash")
gemini = os.getenv("GEMINI_API_KEY", "")
gw_url, gw_key = os.getenv("AI_GATEWAY_URL", ""), os.getenv("AI_GATEWAY_KEY", "")

models = []
fallbacks = [m.strip() for m in os.getenv("AI_FALLBACK_MODEL", "").split(",") if m.strip()]
if gemini and not config.is_placeholder(gemini):
    for m in [model] + fallbacks:   # fallbacks appear in Continue's model dropdown for when the first is busy
        models.append(f"""  - name: {m} (Gemini)
    provider: gemini
    model: {m}
    apiKey: "{gemini}"
    roles: [chat, edit, apply]""")
if gw_url and gw_key and not config.is_placeholder(gw_key):
    models.append(f"""  - name: {model} (hackathon gateway)
    provider: openai
    model: {model}
    apiBase: "{gw_url}"
    apiKey: "{gw_key}"
    roles: [chat, edit, apply]""")

if not models:
    print("No AI key in .env yet (GEMINI_API_KEY or AI_GATEWAY_URL/AI_GATEWAY_KEY). Skipping Continue setup.")
    sys.exit(0)

cfg = f"""name: Signals Hackathon Copilot
version: 1.0.0
schema: v1
rules:
  - Follow AGENTS.md in the workspace root. Signals API facts come from docs/signals (GOTCHAS.md, CHEAT_SHEET.md, the lookup script). Never invent endpoints.
models:
{chr(10).join(models)}
context:
  - provider: code
  - provider: currentFile
  - provider: file
  - provider: diff
  - provider: terminal
  - provider: problems
  - provider: repo-map
"""
path = Path.home() / ".continue" / "config.yaml"
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(cfg, encoding="utf-8")
print(f"Wrote {path} ({len(models)} model(s)). Workspace prompts: .continue/prompts (/signals, /signals-endpoint, ...)")
