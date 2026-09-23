import os
import json
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger("ai_client")

class AIClient:
    """
    Unified AI Client supporting:
    1. Google Gemini Native REST (gemini-3.5-flash)
    2. Hackathon LiteLLM / OpenAI Gateways
    3. Intelligent Mock Fallback
    """
    def __init__(self):
        self._default_gateway_url = "https://signals-ai.revvity-hackathon.com/v1"

    @property
    def gateway_url(self) -> str:
        return os.getenv("AI_GATEWAY_URL", self._default_gateway_url)

    @property
    def api_key(self) -> str:
        return os.getenv("GEMINI_API_KEY", "") or os.getenv("AI_GATEWAY_KEY", "")

    @property
    def model(self) -> str:
        return os.getenv("AI_MODEL", "gemini-3.5-flash")

    @property
    def mock_mode(self) -> bool:
        key = self.api_key
        return (
            os.getenv("MOCK_MODE", "false").lower() == "true"
            or not key
            or "your-" in key
            or "your_" in key
            or ("sk-team" in key and "revvity-hackathon.com" in self.gateway_url)
        )

    @property
    def is_gemini_key(self) -> bool:
        key = self.api_key
        return (
            key.startswith("AQ.")
            or key.startswith("AIza")
            or "generativelanguage.googleapis.com" in self.gateway_url
        )

    def check_status(self) -> Dict[str, Any]:
        """Returns the active AI configuration and model provider."""
        return {
            "mockMode": self.mock_mode,
            "provider": "Google Gemini Native" if self.is_gemini_key else "OpenAI/LiteLLM Gateway",
            "model": self.model,
            "keyConfigured": bool(self.api_key and not self.mock_mode)
        }

    def generate_text(self, prompt: str, system_instruction: str = "You are an expert scientific lab copilot.") -> Dict[str, Any]:
        """Generates a text completion."""
        if self.mock_mode:
            return {
                "source": "mock_simulator",
                "text": f"[MOCK AI RESPONSE] Synthesized scientific analysis for prompt: '{prompt[:60]}...'. All parameters verified compliant with standard lab protocol."
            }

        # 1. Native Gemini
        if self.is_gemini_key:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            payload = {
                "system_instruction": {"parts": [{"text": system_instruction}]},
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 2048}
            }
            try:
                res = requests.post(url, json=payload, timeout=30)
                if res.status_code == 200:
                    text_out = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    return {"source": f"{self.model} (native)", "text": text_out}
                else:
                    logger.warning(f"Native Gemini returned {res.status_code}: {res.text[:150]}")
            except Exception as e:
                logger.warning(f"Native Gemini failed: {e}")

        # 2. OpenAI / LiteLLM Gateway
        try:
            from openai import OpenAI
            client = OpenAI(base_url=self.gateway_url, api_key=self.api_key, timeout=25.0)
            res = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            return {"source": f"{self.model} (gateway)", "text": res.choices[0].message.content}
        except Exception as e:
            logger.error(f"Gateway failed: {e}. Falling back to mock simulation.")
            return {
                "source": "fallback_mock",
                "text": f"[FALLBACK SIMULATOR] AI analysis generated for: '{prompt[:60]}...'. Note: upstream gateway returned: {str(e)[:80]}."
            }
