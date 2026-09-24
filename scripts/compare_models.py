"""Compare LLMs on hackathon-style prompts: answer quality (rough checks + full answers), speed, tokens, cost.

    python scripts/compare_models.py                                   # AI_MODEL, AI_FALLBACK_MODEL, gemini-3.8-flash
    python scripts/compare_models.py gemini-3.6-flash gemini-3.5-flash-lite

Each prompt is grounded the same way the apps and Continue are (the knowledge pack in docs/signals + AGENTS.md
rules). Every model gets the same prompts, with no fallback between models (busy models are retried).
The checks are keyword hints, not a grade: read the answers in the report (model-compare/report_<time>.md).
Prices are USD per 1M tokens from https://ai.google.dev/gemini-api/docs/pricing (checked 2026-09-24).
"""
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend import config  # noqa: E402,F401  (loads .env / Codespaces secrets)
import os  # noqa: E402
from backend.ai_client import AIClient, TransientAIError, SIGNALS_EXPERT  # noqa: E402
from backend.knowledge import knowledge_block  # noqa: E402

PRICES = {  # (input, output) USD per 1M tokens; thinking tokens are billed as output
    "gemini-3.8-flash": (0.75, 3.75), "gemini-3.7-flash": (0.75, 3.75), "gemini-3.6-flash": (0.75, 3.75),
    "gemini-3.5-flash": (1.50, 9.00), "gemini-3.5-flash-lite": (0.30, 2.50), "gemini-3.1-flash-lite": (0.25, 1.50),
}

AGENTS = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
PROMPTS = [
    {"name": "Docs: task with due date + link",
     "q": "How do I create a task with a due date in an experiment and link it to another experiment? Show the request.",
     "expect": ["POST /entities", "ancestors", "Required By", "Reference ID"], "avoid": ["Experiment Link\": {\"value"]},
    {"name": "Docs: search returns too many",
     "q": "A search for experiment 'QC-2026-001' returns 40 results. Why, and what's the fix?",
     "expect": ["keyword"], "avoid": []},
    {"name": "Docs: list only experiments",
     "q": "How do I list only experiments via the REST API?",
     "expect": ["includeTypes"], "avoid": ["filter[type]=experiment\n"]},
    {"name": "Docs: inventory search",
     "q": "Why does my search for containers return 0 results, and how do I find a container by barcode?",
     "expect": ["IVT", "fields.Barcode"], "avoid": []},
    {"name": "Code: tasks in a notebook",
     "q": ("Write a Python function for this repo that lists every task in a notebook with its 'Required By' date. "
           "Use SignalsClient where it has a method, otherwise sc._request. Code only, with short comments."),
     "expect": ["def ", "/tasks/", "properties", "Required By"], "avoid": ["filter[type]"], "code": True},
]


def run(model: str, p: dict) -> dict:
    ai = AIClient(model)
    kb = knowledge_block(p["q"], k=5)
    system = SIGNALS_EXPERT + ("\n\nRepository rules (AGENTS.md):\n" + AGENTS if p.get("code") else "")
    prompt = f"KNOWLEDGE (verified Signals API / integration docs):\n{kb}\n\nQUESTION: {p['q']}"
    t0 = time.time()
    for wait in (0, 3, 8):
        time.sleep(wait)
        try:
            r = ai._call(model, prompt, system, 4096)
            break
        except TransientAIError as e:
            r = {"text": f"(busy: {e})", "usage": {}}
        except Exception as e:  # noqa: BLE001
            r = {"text": f"(error: {e})", "usage": {}}
            break
    secs = time.time() - t0
    u = r.get("usage", {})
    pin, pout = PRICES.get(model, (0, 0))
    cost = (u.get("input", 0) * pin + (u.get("output", 0) + u.get("thinking", 0)) * pout) / 1e6
    text = r["text"]
    hits = [e for e in p["expect"] if e.lower() in text.lower()]
    bad = [a for a in p["avoid"] if a in text]
    return {"text": text, "secs": secs, "usage": u, "cost": cost, "hits": hits, "bad": bad}


def main():
    models = sys.argv[1:] or [m for m in [os.getenv("AI_MODEL", "gemini-3.6-flash"),
                                          *os.getenv("AI_FALLBACK_MODEL", "").split(","), "gemini-3.8-flash"] if m.strip()]
    models = list(dict.fromkeys(m.strip() for m in models))
    if AIClient().mock_mode:
        sys.exit("No AI key (GEMINI_API_KEY or AI_GATEWAY_URL/AI_GATEWAY_KEY): nothing to compare.")
    print(f"Models: {', '.join(models)} | {len(PROMPTS)} prompts\n")
    results = {m: [] for m in models}
    for p in PROMPTS:
        for m in models:
            res = run(m, p)
            results[m].append(res)
            print(f"  {m:24} {p['name']:34} {res['secs']:5.1f}s  checks {len(res['hits'])}/{len(p['expect'])}"
                  f"{'  AVOID:' + str(res['bad']) if res['bad'] else ''}  ${res['cost']:.4f}")
    lines = [f"# Model comparison {datetime.now():%Y-%m-%d %H:%M}", "",
             "| Model | Checks | Avg time | Tokens in / out (+thinking) | Cost for these prompts | Est. per team-day (300 req) |",
             "|---|---|---|---|---|---|"]
    for m, rs in results.items():
        hits = sum(len(r["hits"]) for r in rs)
        total = sum(len(p["expect"]) for p in PROMPTS)
        tin = sum(r["usage"].get("input", 0) for r in rs)
        tout = sum(r["usage"].get("output", 0) for r in rs)
        tthink = sum(r["usage"].get("thinking", 0) for r in rs)
        cost = sum(r["cost"] for r in rs)
        lines.append(f"| {m} | {hits}/{total} | {sum(r['secs'] for r in rs) / len(rs):.1f}s | {tin:,} / {tout:,} (+{tthink:,}) "
                     f"| ${cost:.4f} | ${cost / len(rs) * 300:.2f} |")
    lines += ["", "Checks = expected facts found in the answer (a hint only). Read the answers below.", ""]
    for i, p in enumerate(PROMPTS):
        lines += [f"## {p['name']}", f"> {p['q']}", ""]
        for m in models:
            r = results[m][i]
            lines += [f"### {m} ({r['secs']:.1f}s, checks {', '.join(r['hits']) or 'none'})", "", r["text"], ""]
    out = ROOT / "model-compare"
    out.mkdir(exist_ok=True)
    path = out / f"report_{datetime.now():%Y%m%d-%H%M%S}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print("\n" + "\n".join(lines[2:4 + len(models)]))  # header + separator + one row per model
    print(f"\nFull answers: {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
