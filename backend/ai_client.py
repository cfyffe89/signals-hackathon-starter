"""AI client for the starter: Google Gemini (native REST) or any OpenAI-compatible gateway (e.g. LiteLLM).

Env:  GEMINI_API_KEY  (Gemini)          or  AI_GATEWAY_URL + AI_GATEWAY_KEY  (OpenAI-compatible)
      AI_MODEL        (default gemini-3.6-flash)
      AI_FALLBACK_MODEL  optional, comma-separated: used when AI_MODEL stays busy (429/500/503) after 3 tries
No key -> mock mode: returns an honest placeholder that shows the context it would have sent.
"""
import os
import time
import logging
from typing import Any, Dict, List, Optional

import requests

from .config import is_placeholder

logger = logging.getLogger("ai_client")


class TransientAIError(RuntimeError):
    """The model service is busy or briefly unavailable (429 / 500 / 503): worth retrying."""


def _raise_for_status(r: requests.Response) -> None:
    """Raise with the provider's own error message (e.g. Gemini's "The model is overloaded")."""
    if r.status_code < 400:
        return
    try:
        err = r.json().get("error", {})
        msg = err.get("message") if isinstance(err, dict) else str(err)
    except ValueError:
        msg = r.text[:200]
    text = f"{r.status_code} {msg or r.reason}"
    raise (TransientAIError if r.status_code in (429, 500, 503) else RuntimeError)(text)

SIGNALS_EXPERT = (
    "You are a Revvity Signals expert helping a scientist or integration developer.\n"
    "Answer ONLY from the SIGNALS RECORDS and KNOWLEDGE provided. If they don't contain the answer, say so and "
    "suggest what to look up. Never invent endpoints, parameters, record contents or numbers.\n"
    "When you use a record or a knowledge section, cite it in [brackets] (record name or knowledge source).\n"
    "For API answers: name the exact method + path, show a minimal request, and mention any gotcha from the knowledge.\n"
    "Be concise and practical."
)


class AIClient:
    def __init__(self, model: Optional[str] = None):
        self._model = model

    @property
    def model(self) -> str:
        return self._model or os.getenv("AI_MODEL", "gemini-3.6-flash")

    @property
    def gemini_key(self) -> str:
        k = os.getenv("GEMINI_API_KEY", "")
        return "" if is_placeholder(k) else k

    @property
    def gateway(self) -> tuple:
        url, key = os.getenv("AI_GATEWAY_URL", ""), os.getenv("AI_GATEWAY_KEY", "")
        return (url, key) if url and not is_placeholder(key) else ("", "")

    @property
    def mock_mode(self) -> bool:
        return os.getenv("MOCK_MODE", "false").lower() == "true" or not (self.gemini_key or self.gateway[0])

    def check_status(self) -> Dict[str, Any]:
        provider = "mock" if self.mock_mode else ("gemini" if self.gemini_key else "gateway")
        return {"mockMode": self.mock_mode, "provider": provider, "model": self.model}

    def generate_text(self, prompt: str, system_instruction: str = SIGNALS_EXPERT,
                      max_tokens: int = 4096) -> Dict[str, Any]:  # thinking models spend part of this budget
        if self.mock_mode:
            return {"source": "mock", "text": (
                "**AI is not configured** (set `GEMINI_API_KEY`, or `AI_GATEWAY_URL` + `AI_GATEWAY_KEY`, in `.env`).\n\n"
                f"This is the prompt that would be sent ({len(prompt):,} characters):\n\n```\n{prompt[:1500]}\n```")}
        # Busy/overloaded (429/500/503) is common on shared models: retry with backoff, then try AI_FALLBACK_MODEL.
        models = [self.model] + [m.strip() for m in os.getenv("AI_FALLBACK_MODEL", "").split(",") if m.strip()]
        last = ""
        for model in models:
            for wait in (0, 2, 5):
                time.sleep(wait)
                try:
                    return self._call(model, prompt, system_instruction, max_tokens)
                except TransientAIError as e:
                    last = str(e)
                    logger.warning(f"AI busy ({model}), retrying: {last}")
                except Exception as e:  # noqa: BLE001
                    logger.warning(f"AI call failed: {e}")
                    return {"source": "error", "text": f"AI call failed ({model}): {str(e)[:300]}"}
        return {"source": "error", "text": f"AI call failed after retries ({', '.join(models)}): {last[:300].rstrip('.')}. "
                                           "The model service is busy; try again, or set AI_FALLBACK_MODEL."}

    def _call(self, model: str, prompt: str, system_instruction: str, max_tokens: int) -> Dict[str, Any]:
        if self.gemini_key:
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                headers={"x-goog-api-key": self.gemini_key},
                json={"system_instruction": {"parts": [{"text": system_instruction}]},
                      "contents": [{"parts": [{"text": prompt}]}],
                      "generationConfig": {"temperature": 0.2, "maxOutputTokens": max_tokens}},
                timeout=90)
            _raise_for_status(r)
            body = r.json()
            cand = (body.get("candidates") or [{}])[0]
            text = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", [])).strip()
            if not text:
                # e.g. finishReason MAX_TOKENS: thinking models can spend the whole output budget before answering
                raise RuntimeError(f"no text returned (finishReason={cand.get('finishReason')}, "
                                   f"promptFeedback={body.get('promptFeedback')}); try a larger max_tokens")
            u = body.get("usageMetadata", {})
            usage = {"input": u.get("promptTokenCount", 0), "output": u.get("candidatesTokenCount", 0),
                     "thinking": u.get("thoughtsTokenCount", 0)}  # thinking tokens are billed as output
            return {"source": f"{model} (gemini)", "text": text, "usage": usage}
        url, key = self.gateway
        r = requests.post(f"{url.rstrip('/')}/chat/completions", headers={"Authorization": f"Bearer {key}"},
                          json={"model": model, "temperature": 0.2, "max_tokens": max_tokens,
                                "messages": [{"role": "system", "content": system_instruction},
                                             {"role": "user", "content": prompt}]}, timeout=90)
        _raise_for_status(r)
        body = r.json()
        u = body.get("usage", {})
        return {"source": f"{model} (gateway)", "text": body["choices"][0]["message"]["content"].strip(),
                "usage": {"input": u.get("prompt_tokens", 0), "output": u.get("completion_tokens", 0), "thinking": 0}}

    def ask(self, question: str, records: str = "", knowledge: str = "",
            extra_instruction: str = "") -> Dict[str, Any]:
        """Grounded answer: question + Signals records (context.py) + knowledge chunks (knowledge.py)."""
        prompt = ""
        if records:
            prompt += f"SIGNALS RECORDS (live data the user can access):\n{records}\n\n"
        if knowledge:
            prompt += f"KNOWLEDGE (verified Signals API / integration docs):\n{knowledge}\n\n"
        prompt += f"QUESTION: {question}"
        return self.generate_text(prompt, SIGNALS_EXPERT + ("\n" + extra_instruction if extra_instruction else ""))
