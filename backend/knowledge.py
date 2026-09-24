"""Tiny retrieval over the Signals knowledge pack (docs/signals) so the apps' AI can answer
API / integration / developer-guide questions from verified material. Standard library only.

    from backend.knowledge import search_knowledge, find_endpoints
    search_knowledge("how do I create a sample from a template", k=4)
"""
import math
import re
from functools import lru_cache
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / "docs" / "signals"
SOURCES = ["GOTCHAS.md", "CHEAT_SHEET.md", "references/guide/core/*.md", "references/guide/data-factory/*.md"]
# GOTCHAS are live-verified: rank them slightly higher than the narrative guide
BOOST = {"GOTCHAS.md": 1.5, "CHEAT_SHEET.md": 1.3}
WORD = re.compile(r"[a-z0-9$_/{}.\-]+")
STOP = set("the a an and or of to in on for is are be with by as at it this that from how do i can what which when my your use using".split())


def _tokens(text: str):
    return [w.strip(".-") for w in WORD.findall(text.lower()) if w.strip(".-") and w not in STOP]


@lru_cache(maxsize=1)
def _chunks():
    chunks = []
    for pattern in SOURCES:
        for path in sorted(DOCS.glob(pattern)):
            rel = path.relative_to(DOCS).as_posix()
            text = path.read_text(encoding="utf-8", errors="replace")
            # split on markdown headings (##/###) keeping the heading with its body
            parts = re.split(r"(?m)^(?=#{2,3} )", text)
            for part in parts:
                part = part.strip()
                if len(part) < 40:
                    continue
                for i in range(0, len(part), 2400):     # keep chunks prompt-sized
                    body = part[i:i + 2400]
                    heading = body.splitlines()[0].lstrip("# ").strip()
                    chunks.append({"source": rel, "heading": heading, "text": body, "tokens": _tokens(body)})
    df = {}
    for c in chunks:
        for t in set(c["tokens"]):
            df[t] = df.get(t, 0) + 1
    return chunks, df


def search_knowledge(query: str, k: int = 4):
    """Return the k most relevant knowledge chunks: [{source, heading, text, score}]."""
    chunks, df = _chunks()
    q = set(_tokens(query))
    n = len(chunks) or 1
    scored = []
    for c in chunks:
        if not c["tokens"]:
            continue
        tf = {}
        for t in c["tokens"]:
            if t in q:
                tf[t] = tf.get(t, 0) + 1
        if not tf:
            continue
        score = sum((1 + math.log(f)) * math.log(1 + n / df[t]) for t, f in tf.items())
        score = score / math.sqrt(len(c["tokens"])) * BOOST.get(c["source"], 1.0)
        scored.append((score, c))
    scored.sort(key=lambda x: -x[0])
    return [{"source": c["source"], "heading": c["heading"], "text": c["text"], "score": round(s, 3)} for s, c in scored[:k]]


def find_endpoints(query: str, limit: int = 12, system: str = "core"):
    """Grep the endpoint index for rows matching every query word (e.g. 'materials libraries')."""
    idx = DOCS / "references" / f"endpoint-index-{system}.md"
    words = [w for w in _tokens(query) if len(w) > 2]
    rows = [l.strip() for l in idx.read_text(encoding="utf-8").splitlines() if l.startswith("| ") and "`/" in l]
    hits = [r for r in rows if all(w in r.lower() for w in words)] or [r for r in rows if any(w in r.lower() for w in words)]
    return hits[:limit]


def knowledge_block(query: str, k: int = 4, with_endpoints: bool = True) -> str:
    """Formatted context for an LLM prompt: top knowledge chunks (+ matching endpoint rows)."""
    parts = [f"[{c['source']} › {c['heading']}]\n{c['text']}" for c in search_knowledge(query, k)]
    if with_endpoints:
        eps = find_endpoints(query, 10)
        if eps:
            parts.append("[Endpoint index matches: | file | method | path | operationId | tags | summary |]\n" + "\n".join(eps))
    return "\n\n---\n\n".join(parts)
