"""AI client for the starter: Google Gemini (native REST) or any OpenAI-compatible gateway (e.g. LiteLLM).

Env:  GEMINI_API_KEY  (Gemini)          or  AI_GATEWAY_URL + AI_GATEWAY_KEY  (OpenAI-compatible)
      AI_MODEL        (default gemini-3.5-flash)
No key -> mock mode: returns an honest placeholder that shows the context it would have sent.
"""
import os
import logging
from typing import Any, Dict, List, Optional

import requests

from .config import is_placeholder

logger = logging.getLogger("ai_client")

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
        return self._model or os.getenv("AI_MODEL", "gemini-3.5-flash")

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
                      max_tokens: int = 2048) -> Dict[str, Any]:
        if self.mock_mode:
            return {"source": "mock", "text": (
                "**AI is not configured** (set `GEMINI_API_KEY`, or `AI_GATEWAY_URL` + `AI_GATEWAY_KEY`, in `.env`).\n\n"
                f"This is the prompt that would be sent ({len(prompt):,} characters):\n\n```\n{prompt[:1500]}\n```")}
        try:
            if self.gemini_key:
                r = requests.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
                    headers={"x-goog-api-key": self.gemini_key},
                    json={"system_instruction": {"parts": [{"text": system_instruction}]},
                          "contents": [{"parts": [{"text": prompt}]}],
                          "generationConfig": {"temperature": 0.2, "maxOutputTokens": max_tokens}},
                    timeout=90)
                r.raise_for_status()
                parts = r.json()["candidates"][0]["content"]["parts"]
                return {"source": f"{self.model} (gemini)", "text": "".join(p.get("text", "") for p in parts).strip()}
            url, key = self.gateway
            r = requests.post(f"{url.rstrip('/')}/chat/completions", headers={"Authorization": f"Bearer {key}"},
                              json={"model": self.model, "temperature": 0.2, "max_tokens": max_tokens,
                                    "messages": [{"role": "system", "content": system_instruction},
                                                 {"role": "user", "content": prompt}]}, timeout=90)
            r.raise_for_status()
            return {"source": f"{self.model} (gateway)", "text": r.json()["choices"][0]["message"]["content"].strip()}
        except Exception as e:
            logger.warning(f"AI call failed: {e}")
            return {"source": "error", "text": f"AI call failed: {str(e)[:300]}"}

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
