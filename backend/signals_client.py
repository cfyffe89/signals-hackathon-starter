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

MOCK_CHEMICAL_DRAWINGS = [
    {
        "id": "chemicalDrawing:cd-001",
        "name": "EXP-081: Aspirin (Acetylsalicylic acid)",
        "smiles": "CC(=O)Oc1ccccc1C(=O)O",
        "formula": "C9H8O4",
        "modifiedAt": "2026-09-23T16:20:00Z",
        "author": "Dr. Sarah Chen",
        "notebook": "EXP-2026-081"
    },
    {
        "id": "chemicalDrawing:cd-002",
        "name": "EXP-081: Ibuprofen (NSAID candidate)",
        "smiles": "CC(C)Cc1ccc(C(C)C(=O)O)cc1",
        "formula": "C13H18O2",
        "modifiedAt": "2026-09-23T15:45:00Z",
        "author": "Dr. Sarah Chen",
        "notebook": "EXP-2026-081"
    },
    {
        "id": "chemicalDrawing:cd-003",
        "name": "EXP-094: Caffeine (CNS reference stimulant)",
        "smiles": "Cn1cnc2c1c(=O)n(c(=O)n2C)C",
        "formula": "C8H10N4O2",
        "modifiedAt": "2026-09-23T15:10:00Z",
        "author": "Marcus Weber",
        "notebook": "EXP-2026-094"
    },
    {
        "id": "chemicalDrawing:cd-004",
        "name": "EXP-094: Paracetamol (Acetaminophen)",
        "smiles": "CC(=O)Nc1ccc(O)cc1",
        "formula": "C8H9NO2",
        "modifiedAt": "2026-09-23T14:30:00Z",
        "author": "Marcus Weber",
        "notebook": "EXP-2026-094"
    },
    {
        "id": "chemicalDrawing:cd-005",
        "name": "EXP-081: 4-Cyanobiphenyl (Suzuki coupling product)",
        "smiles": "N#Cc1ccc(-c2ccccc2)cc1",
        "formula": "C13H9N",
        "modifiedAt": "2026-09-23T14:00:00Z",
        "author": "Dr. Sarah Chen",
        "notebook": "EXP-2026-081"
    },
    {
        "id": "chemicalDrawing:cd-006",
        "name": "EXP-081: Phenylboronic Acid (Suzuki reactant)",
        "smiles": "OB(O)c1ccccc1",
        "formula": "C6H7BO2",
        "modifiedAt": "2026-09-23T13:40:00Z",
        "author": "Dr. Sarah Chen",
        "notebook": "EXP-2026-081"
    },
    {
        "id": "chemicalDrawing:cd-007",
        "name": "EXP-081: 4-Bromobenzonitrile (Suzuki halide)",
        "smiles": "N#Cc1ccc(Br)cc1",
        "formula": "C7H4BrN",
        "modifiedAt": "2026-09-23T13:15:00Z",
        "author": "Dr. Sarah Chen",
        "notebook": "EXP-2026-081"
    },
    {
        "id": "chemicalDrawing:cd-008",
        "name": "EXP-102: Vanillin (Phenolic aldehyde)",
        "smiles": "O=Cc1ccc(O)c(OC)c1",
        "formula": "C8H8O3",
        "modifiedAt": "2026-09-23T12:50:00Z",
        "author": "Elena Rostova",
        "notebook": "EXP-2026-102"
    },
    {
        "id": "chemicalDrawing:cd-009",
        "name": "EXP-102: Dopamine (Catecholamine scaffold)",
        "smiles": "NCCc1ccc(O)c(O)c1",
        "formula": "C8H11NO2",
        "modifiedAt": "2026-09-23T12:20:00Z",
        "author": "Elena Rostova",
        "notebook": "EXP-2026-102"
    },
    {
        "id": "chemicalDrawing:cd-010",
        "name": "EXP-102: Serotonin (Indole ethylamine)",
        "smiles": "NCCc1c[nH]c2ccc(O)cc12",
        "formula": "C10H12N2O",
        "modifiedAt": "2026-09-23T11:55:00Z",
        "author": "Elena Rostova",
        "notebook": "EXP-2026-102"
    },
    {
        "id": "chemicalDrawing:cd-011",
        "name": "EXP-115: Nicotine (Pyridine alkaloid)",
        "smiles": "CN1CCC[C@H]1c2cccnc2",
        "formula": "C10H14N2",
        "modifiedAt": "2026-09-23T11:30:00Z",
        "author": "Marcus Weber",
        "notebook": "EXP-2026-115"
    },
    {
        "id": "chemicalDrawing:cd-012",
        "name": "EXP-115: Metformin (Biguanide derivative)",
        "smiles": "CN(C)C(=N)NC(=N)N",
        "formula": "C4H11N5",
        "modifiedAt": "2026-09-23T11:00:00Z",
        "author": "Marcus Weber",
        "notebook": "EXP-2026-115"
    },
    {
        "id": "chemicalDrawing:cd-013",
        "name": "EXP-081: Salicylic Acid (Aspirin metabolite)",
        "smiles": "Oc1ccccc1C(=O)O",
        "formula": "C7H6O3",
        "modifiedAt": "2026-09-23T10:30:00Z",
        "author": "Dr. Sarah Chen",
        "notebook": "EXP-2026-081"
    },
    {
        "id": "chemicalDrawing:cd-014",
        "name": "EXP-115: Benzocaine (Ester anesthetic)",
        "smiles": "CCOC(=O)c1ccc(N)cc1",
        "formula": "C9H11NO2",
        "modifiedAt": "2026-09-23T10:00:00Z",
        "author": "Marcus Weber",
        "notebook": "EXP-2026-115"
    },
    {
        "id": "chemicalDrawing:cd-015",
        "name": "EXP-102: Warfarin (Coumarin anticoagulant)",
        "smiles": "CC(=O)CC(c1ccccc1)c2c(O)c3ccccc3oc2=O",
        "formula": "C19H16O4",
        "modifiedAt": "2026-09-23T09:40:00Z",
        "author": "Elena Rostova",
        "notebook": "EXP-2026-102"
    },
    {
        "id": "chemicalDrawing:cd-016",
        "name": "EXP-115: Ciprofloxacin (Broad-spectrum antibacterial)",
        "smiles": "O=C(O)c1cn(C2CC2)c3cc(N4CCNCC4)c(F)cc3c1=O",
        "formula": "C17H18FN3O3",
        "modifiedAt": "2026-09-23T09:15:00Z",
        "author": "Dr. Sarah Chen",
        "notebook": "EXP-2026-115"
    },
    {
        "id": "chemicalDrawing:cd-017",
        "name": "EXP-102: Omeprazole (Sulfinyl benzimidazole)",
        "smiles": "COc1ccc2[nH]c(S(=O)Cc3ncc(C)c(OC)c3C)nc2c1",
        "formula": "C17H19N3O3S",
        "modifiedAt": "2026-09-23T08:50:00Z",
        "author": "Elena Rostova",
        "notebook": "EXP-2026-102"
    },
    {
        "id": "chemicalDrawing:cd-018",
        "name": "EXP-094: Amoxicillin (Penicillin class antibiotic)",
        "smiles": "CC1(C)S[C@@H]2[C@H](NC(=O)[C@H](N)c3ccc(O)cc3)C(=O)N2[C@H]1C(=O)O",
        "formula": "C16H19N3O5S",
        "modifiedAt": "2026-09-23T08:20:00Z",
        "author": "Marcus Weber",
        "notebook": "EXP-2026-094"
    },
    {
        "id": "chemicalDrawing:cd-019",
        "name": "EXP-115: Atorvastatin Diol Core (Statin intermediate)",
        "smiles": "CC(C)c1c(C(=O)Nc2ccccc2)c(-c2ccccc2)c(-c2ccc(F)cc2)n1CC[C@@H](O)C[C@@H](O)CC(=O)O",
        "formula": "C33H35FN2O5",
        "modifiedAt": "2026-09-23T07:45:00Z",
        "author": "Dr. Sarah Chen",
        "notebook": "EXP-2026-115"
    },
    {
        "id": "chemicalDrawing:cd-020",
        "name": "EXP-102: Sildenafil Pyrazolopyrimidinone Scaffold",
        "smiles": "CCCC1=NN(C)C2=C1N=C(NC2=O)C3=C(OCC)C=CC(=C3)S(=O)(=O)N4CCN(C)CC4",
        "formula": "C22H30N6O4S",
        "modifiedAt": "2026-09-23T07:15:00Z",
        "author": "Elena Rostova",
        "notebook": "EXP-2026-102"
    }
]

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
    # 2. Search & Entity Discovery
    # ---------------------------------------------------------
    def search_entities(
        self,
        query: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Executes a structured search query against Signals Notebook Search API:
        POST /entities/search?page[limit]={limit}
        Payload: { "query": query, "options": options }
        """
        if self.mock_mode:
            entity_type = ""
            try:
                and_clauses = query.get("$and", []) if isinstance(query, dict) else []
                for clause in and_clauses:
                    match = clause.get("$match", {})
                    if match.get("field") == "type":
                        entity_type = match.get("value", "")
            except Exception:
                pass

            if entity_type == "chemicalDrawing":
                return [
                    {
                        "type": "entity",
                        "id": d["id"],
                        "attributes": {
                            "eid": d["id"],
                            "name": d["name"],
                            "formula": d["formula"],
                            "smiles": d["smiles"],
                            "modifiedAt": d["modifiedAt"],
                            "author": d["author"],
                            "notebook": d["notebook"]
                        }
                    }
                    for d in MOCK_CHEMICAL_DRAWINGS[:limit]
                ]
            else:
                fx_file = FIXTURES_DIR / "experiments_sample.json"
                if fx_file.exists():
                    try:
                        exps = json.loads(fx_file.read_text(encoding="utf-8"))[:limit]
                        return [
                            {
                                "type": "entity",
                                "id": e.get("eid"),
                                "attributes": {
                                    "eid": e.get("eid"),
                                    "name": e.get("name"),
                                    "modifiedAt": e.get("modifiedAt")
                                }
                            }
                            for e in exps
                        ]
                    except Exception:
                        pass
                return [
                    {
                        "type": "entity",
                        "id": "experiment:e323ff17-15c4-4706-9bf3-7f2e12a40001",
                        "attributes": {
                            "eid": "experiment:e323ff17-15c4-4706-9bf3-7f2e12a40001",
                            "name": "EXP-2026-081: Suzuki-Miyaura Catalyst Screening",
                            "modifiedAt": "2026-09-23T10:30:00Z"
                        }
                    },
                    {
                        "type": "entity",
                        "id": "experiment:e323ff17-15c4-4706-9bf3-7f2e12a40002",
                        "attributes": {
                            "eid": "experiment:e323ff17-15c4-4706-9bf3-7f2e12a40002",
                            "name": "EXP-2026-094: Formulation Batch 4B Viscosity Stability",
                            "modifiedAt": "2026-09-23T11:15:00Z"
                        }
                    },
                    {
                        "type": "entity",
                        "id": "experiment:e323ff17-15c4-4706-9bf3-7f2e12a40003",
                        "attributes": {
                            "eid": "experiment:e323ff17-15c4-4706-9bf3-7f2e12a40003",
                            "name": "EXP-2026-102: HTRF Kinase Dose-Response Assay Plate 3",
                            "modifiedAt": "2026-09-23T11:45:00Z"
                        }
                    }
                ][:limit]

        url = f"{self.base_url}/entities/search"
        params = {"page[limit]": limit}
        payload: Dict[str, Any] = {"query": query}
        if options:
            payload["options"] = options
        try:
            res = requests.post(url, headers=self._headers(), params=params, json=payload, timeout=20)
            res.raise_for_status()
            return res.json().get("data", [])
        except Exception as e:
            logger.error(f"Signals Search API error: {e}")
            raise

    def list_experiments(self, limit: int = 15) -> List[Dict[str, Any]]:
        """
        Fetch accessible experiment notebooks using the Signals Search API:
        POST /entities/search?page[limit]={limit}
        Query: type == 'experiment' and isTemplate == false, sorted by modifiedAt desc
        """
        query = {
            "$and": [
                {
                    "$match": {
                        "field": "type",
                        "value": "experiment",
                        "mode": "keyword"
                    }
                },
                {
                    "$match": {
                        "field": "isTemplate",
                        "value": False
                    }
                }
            ]
        }
        options = {
            "sort": {
                "modifiedAt": "desc"
            }
        }
        items = self.search_entities(query=query, options=options, limit=limit)
        experiments = []
        for item in items:
            attr = item.get("attributes", {})
            eid = item.get("id") or attr.get("eid")
            experiments.append({
                "eid": eid,
                "name": attr.get("name", "Untitled Experiment"),
                "modifiedAt": attr.get("modifiedAt", "N/A"),
                "description": attr.get("description", "")
            })
        return experiments

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
    def list_chemical_drawings(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Fetch the most recent chemical drawings across notebooks using the Signals Search API:
        POST /entities/search?page[limit]={limit}
        Query: type == 'chemicalDrawing' and isTemplate == false, sorted by modifiedAt desc
        """
        query = {
            "$and": [
                {
                    "$match": {
                        "field": "type",
                        "value": "chemicalDrawing",
                        "mode": "keyword"
                    }
                },
                {
                    "$match": {
                        "field": "isTemplate",
                        "value": False
                    }
                }
            ]
        }
        options = {
            "sort": {
                "modifiedAt": "desc"
            }
        }
        items = self.search_entities(query=query, options=options, limit=limit)
        drawings = []
        for item in items:
            attr = item.get("attributes", {})
            eid = item.get("id") or attr.get("eid")
            # Extract SMILES if directly present in attributes or fields
            smiles = attr.get("smiles") or attr.get("structure")
            if not smiles and attr.get("fields"):
                for f_k, f_v in attr.get("fields", {}).items():
                    if "structure" in f_k.lower() or "smiles" in f_k.lower():
                        smiles = f_v.get("value")
            if not smiles and eid and not self.mock_mode:
                try:
                    smiles = self.export_entity(eid, format="smiles")
                except Exception:
                    smiles = "CC(=O)Oc1ccccc1C(=O)O"
            elif not smiles:
                smiles = "CC(=O)Oc1ccccc1C(=O)O"

            drawings.append({
                "id": eid,
                "name": attr.get("name", "Untitled Chemical Drawing"),
                "smiles": smiles,
                "formula": attr.get("formula", ""),
                "modifiedAt": attr.get("modifiedAt", ""),
                "author": attr.get("author", "Scientist"),
                "notebook": attr.get("notebook", "General")
            })
        return drawings


    # ---------------------------------------------------------
    # Chemical Structure Retrieval & Export Endpoints
    # ---------------------------------------------------------
    def export_entity(self, eid: str, format: str = "smiles") -> str:
        """
        Fetch/export content of an entity by EID using GET /entities/{eid}/export.
        
        This is the official Signals Notebook endpoint for exporting notebook entities
        such as chemicalDrawing, sample, grid, text, etc.
        
        Supported formats for chemical structures:
          - 'smiles': Daylight SMILES string
          - 'mol': MDL V2000 molfile
          - 'mol-v3000': MDL V3000 molfile
          - 'svg': SVG vector image
          - 'cdxml': ChemDraw XML
          - 'inchi': InChI string
          - 'rxn' / 'rxn-v3000': Reaction files
        """
        fmt = format.lower().strip()
        if self.mock_mode:
            if fmt == "svg":
                svg_file = FIXTURES_DIR / "caffeine.svg"
                if svg_file.exists():
                    return svg_file.read_text(encoding="utf-8")
                return "<svg viewBox='0 0 100 100'><circle cx='50' cy='50' r='40' fill='#00707d'/></svg>"
            elif fmt in ("mol", "mol-v3000"):
                return f"  Mock Molfile V2000\n  Signals EMEA Hackathon 2026\n  Entity: {eid}\n"
            else:
                aspirin = (FIXTURES_DIR / "aspirin.smiles")
                if aspirin.exists():
                    return aspirin.read_text(encoding="utf-8").strip()
                return "CC(=O)Oc1ccccc1C(=O)O"

        url = f"{self.base_url}/entities/{eid}/export"
        params = {"format": fmt}
        headers = {"x-api-key": self.api_key}
        if fmt == "svg":
            headers["Accept"] = "image/svg+xml"
        elif fmt in ("mol", "mol-v3000"):
            headers["Accept"] = "chemical/x-mdl-molfile"
        elif fmt == "smiles":
            headers["Accept"] = "chemical/x-daylight-smiles, text/plain, */*"
        elif fmt == "cdxml":
            headers["Accept"] = "chemical/x-cdxml"
        elif fmt == "inchi":
            headers["Accept"] = "chemical/x-inchi"
        else:
            headers["Accept"] = "*/*"

        res = requests.get(url, headers=headers, params=params, timeout=15)
        res.raise_for_status()
        return res.text

    def get_chemical_drawing(self, id_or_eid: str, format: str = "smiles") -> str:
        """
        Fetch a 2D chemical drawing for an entity or material.
        
        Routing:
        - If id_or_eid represents an entity (e.g., 'chemicalDrawing:...', 'sample:...'):
          calls GET /entities/{eid}/export?format={format}
        - If id_or_eid represents an inventory material/batch (e.g., 'material:...', 'asset:...', 'batch:...'):
          calls GET /materials/{assetBatchId}/drawing?format={format}
        """
        # If it's an entity EID (starts with chemicalDrawing or contains standard entity prefixes)
        if any(id_or_eid.startswith(prefix) for prefix in ("chemicalDrawing:", "sample:", "entity:", "draw:")):
            return self.export_entity(id_or_eid, format=format)

        format = format.lower().strip()
        if self.mock_mode:
            if format == "svg":
                svg_file = FIXTURES_DIR / "caffeine.svg"
                if svg_file.exists():
                    return svg_file.read_text(encoding="utf-8")
                return "<svg viewBox='0 0 100 100'><circle cx='50' cy='50' r='40' fill='#00707d'/></svg>"
            elif format == "mol":
                return f"  Mock Molfile V2000\n  Signals EMEA Hackathon 2026\n  Material: {id_or_eid}\n"
            else:
                # Default to SMILES
                aspirin = (FIXTURES_DIR / "aspirin.smiles")
                if aspirin.exists():
                    return aspirin.read_text(encoding="utf-8").strip()
                return "CC(=O)Oc1ccccc1C(=O)O"

        url = f"{self.base_url}/materials/{id_or_eid}/drawing"
        params = {"format": format}
        headers = {"x-api-key": self.api_key}
        if format == "svg":
            headers["Accept"] = "image/svg+xml"
        elif format in ("mol", "mol-v3000"):
            headers["Accept"] = "chemical/x-mdl-molfile"
        elif format == "smiles":
            headers["Accept"] = "chemical/x-daylight-smiles, text/plain, */*"
        else:
            headers["Accept"] = "*/*"

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
