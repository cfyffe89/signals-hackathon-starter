"""
SignalsClient: Standard Revvity Signals Notebook REST API client.
Enriched with 1-line convenience methods and offline fixtures for the EMEA Hackathon 2026.
"""
import os
import json
import logging
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests

logger = logging.getLogger("signals_client")
FIXTURES_DIR = Path(__file__).parent / "fixtures"

class SignalsClient:
    """
    Standard Revvity Signals Notebook REST API client.
    Includes comprehensive mock fallbacks for offline hackathon development.
    """
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self._default_base_url = (base_url or "https://hackathon.signalsnotebook.revvitycloud.com/api/rest/v1.0").rstrip("/")
        self._default_api_key = api_key or ""

    @property
    def base_url(self) -> str:
        return (os.getenv("SIGNALS_BASE_URL", self._default_base_url) or self._default_base_url).rstrip("/")

    @property
    def api_key(self) -> str:
        return os.getenv("SIGNALS_API_KEY", self._default_api_key) or self._default_api_key

    @property
    def mock_mode(self) -> bool:
        key = self.api_key
        return (
            os.getenv("MOCK_MODE", "false").lower() == "true" 
            or not key 
            or "your-" in key
            or "your_" in key
        )

    def _headers(self, content_type: str = "application/vnd.api+json") -> Dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "Content-Type": content_type,
            "Accept": "application/vnd.api+json"
        }

    # ---------------------------------------------------------
    # 1. Connectivity & Health Check
    # ---------------------------------------------------------
    def check_connection(self) -> Dict[str, Any]:
        """Validates API key and tenant reachability."""
        if self.mock_mode:
            return {
                "status": "mock_connected",
                "message": "Running in offline Mock Mode (MOCK_MODE=true or API key not set)",
                "tenant": self.base_url
            }

        url = f"{self.base_url}/entities"
        params = {"page[limit]": 1}
        try:
            res = requests.get(url, headers=self._headers(), params=params, timeout=10)
            res.raise_for_status()
            return {
                "status": "connected",
                "statusCode": res.status_code,
                "tenant": self.base_url,
                "message": "Successfully authenticated with Signals Notebook tenant!"
            }
        except Exception as e:
            logger.warning(f"Signals connectivity check failed: {e}")
            return {
                "status": "error",
                "tenant": self.base_url,
                "error": str(e)
            }

    # ---------------------------------------------------------
    # 2. Experiments & Notebook Entities
    # ---------------------------------------------------------
    def list_experiments(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Fetch accessible experiment notebooks."""
        if self.mock_mode:
            fx_file = FIXTURES_DIR / "experiments_sample.json"
            if fx_file.exists():
                try:
                    return json.loads(fx_file.read_text(encoding="utf-8"))[:limit]
                except Exception:
                    pass
            return [
                {
                    "eid": "experiment:e323ff17-15c4-4706-9bf3-7f2e12a40001",
                    "name": "EXP-2026-081: Suzuki-Miyaura Catalyst Screening",
                    "modifiedAt": "2026-09-23T10:30:00Z"
                },
                {
                    "eid": "experiment:e323ff17-15c4-4706-9bf3-7f2e12a40002",
                    "name": "EXP-2026-094: Formulation Batch 4B Viscosity Stability",
                    "modifiedAt": "2026-09-23T11:15:00Z"
                },
                {
                    "eid": "experiment:e323ff17-15c4-4706-9bf3-7f2e12a40003",
                    "name": "EXP-2026-102: HTRF Kinase Dose-Response Assay Plate 3",
                    "modifiedAt": "2026-09-23T11:45:00Z"
                }
            ]

        url = f"{self.base_url}/entities"
        params = {"filter[type]": "experiment", "page[limit]": limit}
        try:
            res = requests.get(url, headers=self._headers(), params=params, timeout=12)
            res.raise_for_status()
            data = res.json().get("data", [])
            experiments = []
            for item in data:
                attr = item.get("attributes", {})
                experiments.append({
                    "eid": item.get("id"),
                    "name": attr.get("name", "Untitled Experiment"),
                    "modifiedAt": attr.get("modifiedAt")
                })
            return experiments
        except Exception as e:
            logger.error(f"Error listing experiments: {e}")
            raise

    def get_entity(self, eid: str) -> Dict[str, Any]:
        """Fetch metadata, attributes, and relationships for any entity ID."""
        if self.mock_mode:
            return {
                "id": eid,
                "type": eid.split(":")[0] if ":" in eid else "experiment",
                "attributes": {
                    "name": f"Mock Entity ({eid})",
                    "createdAt": "2026-09-23T12:00:00Z",
                    "modifiedAt": "2026-09-23T14:30:00Z",
                    "description": "Mock entity data generated for offline hackathon development."
                }
            }

        url = f"{self.base_url}/entities/{eid}"
        res = requests.get(url, headers=self._headers(), timeout=12)
        res.raise_for_status()
        return res.json().get("data", {})

    def create_experiment(self, name: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Create a new top-level experiment notebook."""
        if self.mock_mode:
            new_id = f"experiment:{uuid.uuid4()}"
            logger.info(f"[MOCK] Created experiment {new_id}: {name}")
            return {
                "id": new_id,
                "type": "experiment",
                "attributes": {
                    "name": name,
                    "description": description or "",
                    "createdAt": "2026-09-23T16:00:00Z"
                }
            }

        url = f"{self.base_url}/entities"
        payload = {
            "data": {
                "type": "experiment",
                "attributes": {
                    "name": name,
                    "description": description or ""
                }
            }
        }
        res = requests.post(url, headers=self._headers(), json=payload, timeout=15)
        res.raise_for_status()
        return res.json().get("data", {})

    def list_child_entities(self, parent_eid: str) -> List[Dict[str, Any]]:
        """List all child elements (drawings, text notes, images) inside an experiment."""
        if self.mock_mode:
            return [
                {
                    "id": f"chemicalDrawing:{uuid.uuid4()}",
                    "type": "chemicalDrawing",
                    "attributes": {"name": "Reaction Scheme 1", "modifiedAt": "2026-09-23T10:00:00Z"}
                },
                {
                    "id": f"text:{uuid.uuid4()}",
                    "type": "text",
                    "attributes": {"name": "Procedure & Observations", "modifiedAt": "2026-09-23T10:30:00Z"}
                },
                {
                    "id": f"image:{uuid.uuid4()}",
                    "type": "image",
                    "attributes": {"name": "TLC Plate Stain", "modifiedAt": "2026-09-23T11:00:00Z"}
                }
            ]

        url = f"{self.base_url}/entities/{parent_eid}/children"
        res = requests.get(url, headers=self._headers(), timeout=12)
        res.raise_for_status()
        return res.json().get("data", [])

    def upload_child_attachment(
        self,
        parent_eid: str,
        filename: str,
        content_bytes: bytes,
        content_type: str = "application/octet-stream"
    ) -> Dict[str, Any]:
        """
        Uploads an image, HTML note, or file directly as a child entity.
        Always uses ?force=true to avoid 409 conflict errors.
        """
        if self.mock_mode:
            logger.info(f"[MOCK] Uploading {filename} ({len(content_bytes)} bytes) to {parent_eid}")
            return {
                "status": "mock_success",
                "id": f"attachment:{filename}-mock-eid",
                "filename": filename,
                "parentEid": parent_eid,
                "sizeBytes": len(content_bytes),
                "contentType": content_type
            }

        url = f"{self.base_url}/entities/{parent_eid}/children/{filename}?force=true"
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": content_type
        }
        res = requests.post(url, headers=headers, data=content_bytes, timeout=30)
        res.raise_for_status()
        return res.json()

    # ---------------------------------------------------------
    # 3. Chemistry & Chemical Drawings
    # ---------------------------------------------------------
    def get_chemical_drawing(self, asset_batch_id: str, format: str = "smiles") -> str:
        """
        Fetch a 2D chemical drawing for a material/batch.
        Supported formats: 'smiles', 'mol', 'mol-v3000', 'svg', 'cdxml', 'inchi'.
        """
        format = format.lower().strip()
        if self.mock_mode:
            if format == "svg":
                svg_file = FIXTURES_DIR / "caffeine.svg"
                if svg_file.exists():
                    return svg_file.read_text(encoding="utf-8")
                return "<svg viewBox='0 0 100 100'><circle cx='50' cy='50' r='40' fill='#00707d'/></svg>"
            elif format == "mol":
                return "  Mock Molfile V2000\n  Signals EMEA Hackathon 2026\n"
            else:
                # Default to SMILES
                aspirin = (FIXTURES_DIR / "aspirin.smiles")
                if aspirin.exists():
                    return aspirin.read_text(encoding="utf-8").strip()
                return "CC(=O)Oc1ccccc1C(=O)O"

        url = f"{self.base_url}/materials/{asset_batch_id}/drawing"
        params = {"format": format}
        headers = {"x-api-key": self.api_key}
        if format == "svg":
            headers["Accept"] = "image/svg+xml"
        elif format in ("mol", "mol-v3000"):
            headers["Accept"] = "chemical/x-mdl-molfile"
        else:
            headers["Accept"] = "text/plain"

        res = requests.get(url, headers=headers, params=params, timeout=15)
        res.raise_for_status()
        return res.text

    def get_stoichiometry(self, drawing_eid: str) -> Dict[str, Any]:
        """
        Fetch stoichiometry reactants, products, and conditions for a reaction drawing.
        """
        if self.mock_mode:
            fx_file = FIXTURES_DIR / "suzuki_stoichiometry.json"
            if fx_file.exists():
                try:
                    return json.loads(fx_file.read_text(encoding="utf-8"))
                except Exception:
                    pass
            return {
                "data": {
                    "id": drawing_eid,
                    "attributes": {
                        "name": "Mock Reaction",
                        "reactants": [{"name": "Reactant A", "smiles": "c1ccccc1Br", "formula": "C6H5Br"}],
                        "products": [{"name": "Product C", "smiles": "c1ccccc1-c1ccccc1", "formula": "C12H10"}]
                    }
                }
            }

        url = f"{self.base_url}/stoichiometry/{drawing_eid}"
        res = requests.get(url, headers=self._headers(), timeout=15)
        res.raise_for_status()
        return res.json()

    # ---------------------------------------------------------
    # 4. Materials & Inventory Search
    # ---------------------------------------------------------
    def search_materials(self, query: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """Search chemical materials, reagents, and inventory containers."""
        if self.mock_mode:
            mock_reagents = [
                {"id": "material:m-001", "name": "Phenylboronic acid", "cas": "98-80-6", "formula": "C6H7BO2", "smiles": "OB(O)c1ccccc1"},
                {"id": "material:m-002", "name": "4-Bromobenzonitrile", "cas": "623-00-7", "formula": "C7H4BrN", "smiles": "N#Cc1ccc(Br)cc1"},
                {"id": "material:m-003", "name": "Sodium Hydroxide 1.0M", "cas": "1310-73-2", "formula": "NaOH", "smiles": "[Na+].[OH-]"},
                {"id": "material:m-004", "name": "Aspirin (Acetylsalicylic Acid)", "cas": "50-78-2", "formula": "C9H8O4", "smiles": "CC(=O)Oc1ccccc1C(=O)O"},
                {"id": "material:m-005", "name": "Caffeine Pure", "cas": "58-08-2", "formula": "C8H10N4O2", "smiles": "Cn1cnc2c1c(=O)n(c(=O)n2C)C"}
            ]
            if query:
                q_lower = query.lower()
                return [m for m in mock_reagents if q_lower in m["name"].lower() or q_lower in m["formula"].lower() or q_lower in m["cas"]][:limit]
            return mock_reagents[:limit]

        url = f"{self.base_url}/materials/bulk"
        params = {"filter[query]": query, "page[limit]": limit}
        res = requests.get(url, headers=self._headers(), params=params, timeout=12)
        res.raise_for_status()
        return res.json().get("data", [])
