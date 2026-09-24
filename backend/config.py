"""Environment loading for the starter.

Order of precedence (first wins): real environment variables (e.g. Codespaces secrets) > .env file.
Optional: a single Codespaces secret named HACKATHON holding several KEY=VALUE lines (or JSON),
so a team pastes one secret instead of four.
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / ".env"
PLACEHOLDER_MARKERS = ("your-", "your_", "<")


def _parse_bundle(raw: str) -> dict:
    raw = raw.strip().replace("\\n", "\n")
    if raw.startswith("{"):
        try:
            return {k: str(v) for k, v in json.loads(raw).items()}
        except Exception:
            return {}
    out = {}
    for line in raw.replace(";", "\n").splitlines():
        line = line.strip().removeprefix("export ").strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip("'\"")
    return out


def is_placeholder(value: str) -> bool:
    return not value or any(m in value for m in PLACEHOLDER_MARKERS)


def load_env() -> None:
    """Load .env and the optional HACKATHON bundle without overriding real environment variables."""
    values = {}
    if ENV_FILE.exists():
        try:
            from dotenv import dotenv_values
            values.update({k: v for k, v in dotenv_values(ENV_FILE).items() if v})
        except ImportError:
            values.update(_parse_bundle(ENV_FILE.read_text(encoding="utf-8")))
    if os.getenv("HACKATHON"):
        values.update(_parse_bundle(os.environ["HACKATHON"]))
    for k, v in values.items():
        if is_placeholder(os.environ.get(k, "")) and not is_placeholder(v):
            os.environ[k] = v


load_env()
