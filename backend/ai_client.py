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
        return os.getenv("AI_MODEL", "gemini-3.6-flash")

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
            prompt_lower = prompt.lower()
            if any(k in prompt_lower for k in ["drawing", "smiles", "chemical", "medicinal", "lipinski", "pharmacophore"]):
                return {
                    "source": "mock_simulator (medicinal chemistry)",
                    "text": (
                        "### [AI Analysis] Medicinal Chemistry Assessment (Simulated Flash Model)\n\n"
                        "**1. Chemical Classification & Pharmacophore Architecture**\n"
                        "- **Scaffold Core**: Functionalized aromatic/heterocyclic framework containing defined polar recognition elements.\n"
                        "- **Key Motifs**: Hydrogen-bond donor/acceptor pairs positioned for complementary active site engagement.\n"
                        "- **Class Affinity**: Structural topology resembles biologically validated small-molecule therapeutic chemical space.\n\n"
                        "**2. Drug-Likeness & Lipinski Rule of 5 Evaluation**\n"
                        "- **Molecular Weight**: Favorable (< 500 Da), supporting oral formulation.\n"
                        "- **Calculated LogP**: Balanced lipophilicity (optimal range 1.0 - 3.5), suggesting clean partition kinetics.\n"
                        "- **Polar Surface Area (TPSA)**: Within ideal window (40 - 110 A^2), predicting favorable cell permeability without rapid P-gp efflux.\n"
                        "- **Rule of 5 Compliance**: 0 violations (Rule of 5 and Veber guidelines satisfied).\n\n"
                        "**3. ADMET & Liability Assessment**\n"
                        "- **Metabolic Clearance**: Benzylic and ester handles subject to Phase I/II metabolism; monitor microsomal stability.\n"
                        "- **Toxicity Alerts**: Structure is clear of reactive electrophiles, quinone precursors, or promiscuous PAINS alerts.\n"
                        "- **Solubility**: Estimated aqueous solubility is adequate for primary in vitro biochemical and phenotypic assays.\n\n"
                        "**4. Discovery & Lead Optimization Recommendations**\n"
                        "- *SAR Expansion*: Introduce fluorine or small lipophilic substituents at ortho/para aryl positions to tune metabolic half-life.\n"
                        "- *Bioisosterism*: Screen oxadiazole or heterocyclic bioisosteres if carboxylate/ester hydrolytic stability is an issue.\n"
                        "- *Selectivity*: Rigidify linkers to lock in bound bioactive conformation and increase target selectivity."
                    )
                }
            elif any(k in prompt_lower for k in ["summarize", "experiment", "portfolio", "signals notebook", "lab"]):
                return {
                    "source": "mock_simulator (lab portfolio)",
                    "text": (
                        "### [AI Summary] Signals Notebook Experiment Portfolio Summary (Simulated Flash Model)\n\n"
                        "**Executive Summary**\n"
                        "The accessible experiment portfolio reflects an active multidisciplinary drug discovery and formulation pipeline spanning catalyst optimization, phenotypic cytotoxicity screening, and high-throughput reaction screening.\n\n"
                        "**Active Research Tracks Identified:**\n"
                        "1. **Suzuki-Miyaura Cross-Coupling Screening (EXP-2026-081)**\n"
                        "   - *Objective*: Optimize catalyst/ligand combinations for biaryl coupling of functionalized 4-bromobenzonitriles.\n"
                        "   - *Status*: High activity; multiple chemical drawings and stoichiometry sheets linked.\n"
                        "2. **Cell Viability & IC50 Profiling (EXP-2026-102)**\n"
                        "   - *Objective*: Evaluate compound library efficacy across cancer cell lines using automated microplate readouts.\n"
                        "   - *Status*: Data collection complete; pending cross-referencing with compound registry.\n"
                        "3. **Controlled-Release Polymer Formulation (EXP-2026-115)**\n"
                        "   - *Objective*: Screen biodegradable excipients for sustained small-molecule dissolution kinetics.\n"
                        "   - *Status*: Formulation batches characterized; stability testing underway.\n\n"
                        "**Recommended Next Priorities:**\n"
                        "- **Automate Chemical Drawing Extraction**: Directly sync verified reaction products into the centralized inventory register.\n"
                        "- **Integrate In Silico ADMET**: Run pre-synthesis property calculations on proposed targets prior to wet-lab catalyst trials."
                    )
                }
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
