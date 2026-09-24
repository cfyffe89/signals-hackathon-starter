"""
SignalsClient: Revvity Signals Notebook REST API client for the EMEA Hackathon 2026.
Live calls are verified against a real tenant (scripts/smoke_live.py); offline sample data when no key is set.
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
        "mw": 180.16,
        "logp": 1.19,
        "tpsa": 63.60,
        "hbd": 1,
        "hba": 3,
        "rotb": 3,
        "modifiedAt": "2026-09-23T16:20:00Z",
        "author": "Dr. Sarah Chen",
        "notebook": "EXP-2026-081"
    },
    {
        "id": "chemicalDrawing:cd-002",
        "name": "EXP-081: Ibuprofen (NSAID candidate)",
        "smiles": "CC(C)Cc1ccc(C(C)C(=O)O)cc1",
        "formula": "C13H18O2",
        "mw": 206.28,
        "logp": 3.50,
        "tpsa": 37.30,
        "hbd": 1,
        "hba": 1,
        "rotb": 4,
        "modifiedAt": "2026-09-23T15:45:00Z",
        "author": "Dr. Sarah Chen",
        "notebook": "EXP-2026-081"
    },
    {
        "id": "chemicalDrawing:cd-003",
        "name": "EXP-094: Caffeine (CNS reference stimulant)",
        "smiles": "Cn1cnc2c1c(=O)n(c(=O)n2C)C",
        "formula": "C8H10N4O2",
        "mw": 194.19,
        "logp": -0.07,
        "tpsa": 58.44,
        "hbd": 0,
        "hba": 3,
        "rotb": 0,
        "modifiedAt": "2026-09-23T15:10:00Z",
        "author": "Marcus Weber",
        "notebook": "EXP-2026-094"
    },
    {
        "id": "chemicalDrawing:cd-004",
        "name": "EXP-094: Paracetamol (Acetaminophen)",
        "smiles": "CC(=O)Nc1ccc(O)cc1",
        "formula": "C8H9NO2",
        "mw": 151.16,
        "logp": 1.35,
        "tpsa": 49.33,
        "hbd": 2,
        "hba": 2,
        "rotb": 1,
        "modifiedAt": "2026-09-23T14:30:00Z",
        "author": "Marcus Weber",
        "notebook": "EXP-2026-094"
    },
    {
        "id": "chemicalDrawing:cd-005",
        "name": "EXP-081: 4-Cyanobiphenyl (Suzuki coupling product)",
        "smiles": "N#Cc1ccc(-c2ccccc2)cc1",
        "formula": "C13H9N",
        "mw": 179.22,
        "logp": 3.14,
        "tpsa": 23.79,
        "hbd": 0,
        "hba": 1,
        "rotb": 1,
        "modifiedAt": "2026-09-23T14:00:00Z",
        "author": "Dr. Sarah Chen",
        "notebook": "EXP-2026-081"
    },
    {
        "id": "chemicalDrawing:cd-006",
        "name": "EXP-081: Phenylboronic Acid (Suzuki reactant)",
        "smiles": "OB(O)c1ccccc1",
        "formula": "C6H7BO2",
        "mw": 121.93,
        "logp": 0.94,
        "tpsa": 40.46,
        "hbd": 2,
        "hba": 2,
        "rotb": 1,
        "modifiedAt": "2026-09-23T13:40:00Z",
        "author": "Dr. Sarah Chen",
        "notebook": "EXP-2026-081"
    },
    {
        "id": "chemicalDrawing:cd-007",
        "name": "EXP-081: 4-Bromobenzonitrile (Suzuki halide)",
        "smiles": "N#Cc1ccc(Br)cc1",
        "formula": "C7H4BrN",
        "mw": 182.02,
        "logp": 2.22,
        "tpsa": 23.79,
        "hbd": 0,
        "hba": 1,
        "rotb": 0,
        "modifiedAt": "2026-09-23T13:15:00Z",
        "author": "Dr. Sarah Chen",
        "notebook": "EXP-2026-081"
    },
    {
        "id": "chemicalDrawing:cd-008",
        "name": "EXP-102: Vanillin (Phenolic aldehyde)",
        "smiles": "O=Cc1ccc(O)c(OC)c1",
        "formula": "C8H8O3",
        "mw": 152.15,
        "logp": 1.17,
        "tpsa": 46.53,
        "hbd": 1,
        "hba": 3,
        "rotb": 2,
        "modifiedAt": "2026-09-23T12:50:00Z",
        "author": "Elena Rostova",
        "notebook": "EXP-2026-102"
    },
    {
        "id": "chemicalDrawing:cd-009",
        "name": "EXP-102: Dopamine (Catecholamine scaffold)",
        "smiles": "NCCc1ccc(O)c(O)c1",
        "formula": "C8H11NO2",
        "mw": 153.18,
        "logp": 0.44,
        "tpsa": 66.48,
        "hbd": 3,
        "hba": 3,
        "rotb": 2,
        "modifiedAt": "2026-09-23T12:20:00Z",
        "author": "Elena Rostova",
        "notebook": "EXP-2026-102"
    },
    {
        "id": "chemicalDrawing:cd-010",
        "name": "EXP-102: Serotonin (Indole ethylamine)",
        "smiles": "NCCc1c[nH]c2ccc(O)cc12",
        "formula": "C10H12N2O",
        "mw": 176.21,
        "logp": 0.81,
        "tpsa": 56.23,
        "hbd": 3,
        "hba": 2,
        "rotb": 2,
        "modifiedAt": "2026-09-23T11:55:00Z",
        "author": "Elena Rostova",
        "notebook": "EXP-2026-102"
    },
    {
        "id": "chemicalDrawing:cd-011",
        "name": "EXP-115: Nicotine (Pyridine alkaloid)",
        "smiles": "CN1CCC[C@H]1c2cccnc2",
        "formula": "C10H14N2",
        "mw": 162.23,
        "logp": 1.17,
        "tpsa": 16.13,
        "hbd": 0,
        "hba": 2,
        "rotb": 1,
        "modifiedAt": "2026-09-23T11:30:00Z",
        "author": "Marcus Weber",
        "notebook": "EXP-2026-115"
    },
    {
        "id": "chemicalDrawing:cd-012",
        "name": "EXP-115: Metformin (Biguanide derivative)",
        "smiles": "CN(C)C(=N)NC(=N)N",
        "formula": "C4H11N5",
        "mw": 129.16,
        "logp": -1.33,
        "tpsa": 88.99,
        "hbd": 4,
        "hba": 4,
        "rotb": 0,
        "modifiedAt": "2026-09-23T11:00:00Z",
        "author": "Marcus Weber",
        "notebook": "EXP-2026-115"
    },
    {
        "id": "chemicalDrawing:cd-013",
        "name": "EXP-081: Salicylic Acid (Aspirin metabolite)",
        "smiles": "Oc1ccccc1C(=O)O",
        "formula": "C7H6O3",
        "mw": 138.12,
        "logp": 1.34,
        "tpsa": 57.53,
        "hbd": 2,
        "hba": 2,
        "rotb": 1,
        "modifiedAt": "2026-09-23T10:30:00Z",
        "author": "Dr. Sarah Chen",
        "notebook": "EXP-2026-081"
    },
    {
        "id": "chemicalDrawing:cd-014",
        "name": "EXP-115: Benzocaine (Ester anesthetic)",
        "smiles": "CCOC(=O)c1ccc(N)cc1",
        "formula": "C9H11NO2",
        "mw": 165.19,
        "logp": 1.86,
        "tpsa": 52.32,
        "hbd": 1,
        "hba": 2,
        "rotb": 3,
        "modifiedAt": "2026-09-23T10:00:00Z",
        "author": "Marcus Weber",
        "notebook": "EXP-2026-115"
    },
    {
        "id": "chemicalDrawing:cd-015",
        "name": "EXP-102: Warfarin (Coumarin anticoagulant)",
        "smiles": "CC(=O)CC(c1ccccc1)c2c(O)c3ccccc3oc2=O",
        "formula": "C19H16O4",
        "mw": 308.33,
        "logp": 2.70,
        "tpsa": 67.51,
        "hbd": 1,
        "hba": 4,
        "rotb": 3,
        "modifiedAt": "2026-09-23T09:40:00Z",
        "author": "Elena Rostova",
        "notebook": "EXP-2026-102"
    },
    {
        "id": "chemicalDrawing:cd-016",
        "name": "EXP-115: Ciprofloxacin (Broad-spectrum antibacterial)",
        "smiles": "O=C(O)c1cn(C2CC2)c3cc(N4CCNCC4)c(F)cc3c1=O",
        "formula": "C17H18FN3O3",
        "mw": 331.34,
        "logp": 0.40,
        "tpsa": 74.57,
        "hbd": 2,
        "hba": 5,
        "rotb": 3,
        "modifiedAt": "2026-09-23T09:15:00Z",
        "author": "Dr. Sarah Chen",
        "notebook": "EXP-2026-115"
    },
    {
        "id": "chemicalDrawing:cd-017",
        "name": "EXP-102: Omeprazole (Sulfinyl benzimidazole)",
        "smiles": "COc1ccc2[nH]c(S(=O)Cc3ncc(C)c(OC)c3C)nc2c1",
        "formula": "C17H19N3O3S",
        "mw": 345.42,
        "logp": 2.23,
        "tpsa": 85.50,
        "hbd": 1,
        "hba": 6,
        "rotb": 4,
        "modifiedAt": "2026-09-23T08:50:00Z",
        "author": "Elena Rostova",
        "notebook": "EXP-2026-102"
    },
    {
        "id": "chemicalDrawing:cd-018",
        "name": "EXP-094: Amoxicillin (Penicillin class antibiotic)",
        "smiles": "CC1(C)S[C@@H]2[C@H](NC(=O)[C@H](N)c3ccc(O)cc3)C(=O)N2[C@H]1C(=O)O",
        "formula": "C16H19N3O5S",
        "mw": 365.40,
        "logp": 0.87,
        "tpsa": 128.84,
        "hbd": 4,
        "hba": 6,
        "rotb": 4,
        "modifiedAt": "2026-09-23T08:20:00Z",
        "author": "Marcus Weber",
        "notebook": "EXP-2026-094"
    },
    {
        "id": "chemicalDrawing:cd-019",
        "name": "EXP-115: Atorvastatin Diol Core (Statin intermediate)",
        "smiles": "CC(C)c1c(C(=O)Nc2ccccc2)c(-c2ccccc2)c(-c2ccc(F)cc2)n1CC[C@@H](O)C[C@@H](O)CC(=O)O",
        "formula": "C33H35FN2O5",
        "mw": 558.64,
        "logp": 5.70,
        "tpsa": 111.79,
        "hbd": 3,
        "hba": 5,
        "rotb": 12,
        "modifiedAt": "2026-09-23T07:45:00Z",
        "author": "Dr. Sarah Chen",
        "notebook": "EXP-2026-115"
    },
    {
        "id": "chemicalDrawing:cd-020",
        "name": "EXP-102: Sildenafil Pyrazolopyrimidinone Scaffold",
        "smiles": "CCCC1=NN(C)C2=C1N=C(NC2=O)C3=C(OCC)C=CC(=C3)S(=O)(=O)N4CCN(C)CC4",
        "formula": "C22H30N6O4S",
        "mw": 474.58,
        "logp": 1.50,
        "tpsa": 111.45,
        "hbd": 1,
        "hba": 8,
        "rotb": 7,
        "modifiedAt": "2026-09-23T07:15:00Z",
        "author": "Elena Rostova",
        "notebook": "EXP-2026-102"
    }
]

class SignalsError(RuntimeError):
    """Raised with the Signals error detail (status + JSON:API errors[].detail) instead of a bare HTTPError."""


class SignalsClient:
    """
    Revvity Signals Notebook REST API client (JSON:API).

    Every live call in this class has been exercised against a real tenant (see scripts/smoke_live.py).
    Configuration comes from the environment (or .env):
        SIGNALS_BASE_URL     e.g. https://<your-tenant>/api/rest/v1.0
        SIGNALS_API_KEY      your API key (sent as x-api-key)
    There is no default notebook: pick one with list_notebooks() and pass its eid to the write methods
    (the Streamlit app has a notebook picker in the sidebar).
    With no key (or MOCK_MODE=true) every method returns offline sample data.
    """

    JSONAPI = "application/vnd.api+json"

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self._base_url = base_url
        self._api_key = api_key

    # ---------------------------------------------------------------- config
    @property
    def base_url(self) -> str:
        return (self._base_url or os.getenv("SIGNALS_BASE_URL", "")).rstrip("/")

    @property
    def api_key(self) -> str:
        return self._api_key or os.getenv("SIGNALS_API_KEY", "")

    @property
    def mock_mode(self) -> bool:
        key = self.api_key
        return (os.getenv("MOCK_MODE", "false").lower() == "true" or not key or "your-" in key
                or "your_" in key or not self.base_url or "<" in self.base_url)

    # ---------------------------------------------------------------- http
    def _headers(self, content_type: Optional[str] = None, accept: Optional[str] = None) -> Dict[str, str]:
        # Signals is strict: GET with Accept: application/json -> 406; POST /entities with
        # Content-Type: application/json -> 415. Use the JSON:API media type.
        h = {"x-api-key": self.api_key, "Accept": accept or self.JSONAPI}
        if content_type:
            h["Content-Type"] = content_type
        return h

    def _request(self, method: str, path: str, *, params=None, json_body=None, data=None,
                 content_type: Optional[str] = None, accept: Optional[str] = None, timeout: int = 30):
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        if json_body is not None:
            data = json.dumps(json_body)
            content_type = content_type or self.JSONAPI
        res = requests.request(method, url, headers=self._headers(content_type, accept),
                               params=params, data=data, timeout=timeout)
        if res.status_code >= 400:
            detail = res.text[:300]
            try:
                errs = res.json().get("errors", [])
                detail = "; ".join(f"{e.get('title','')} {e.get('detail','')}".strip() for e in errs) or detail
            except Exception:
                pass
            raise SignalsError(f"{method} {path} -> {res.status_code}: {detail}")
        return res

    def get_digest(self, eid: str) -> str:
        """Current digest of an entity. Edits and child creation need the PARENT's digest (?digest=)."""
        return self._request("GET", f"/entities/{eid}").json()["data"]["attributes"]["digest"]

    # ---------------------------------------------------------------- 1. connectivity
    def check_connection(self) -> Dict[str, Any]:
        """Validates the API key and that the tenant is reachable."""
        if self.mock_mode:
            return {"status": "mock_connected", "tenant": self.base_url or "(not set)",
                    "message": "Offline mock mode (MOCK_MODE=true or SIGNALS_BASE_URL/SIGNALS_API_KEY not set)"}
        try:
            res = self._request("GET", "/entities", params={"includeTypes": "journal", "page[limit]": 1}, timeout=15)
            return {"status": "connected", "statusCode": res.status_code, "tenant": self.base_url,
                    "message": "Authenticated with the Signals tenant."}
        except Exception as e:
            logger.warning(f"Signals connectivity check failed: {e}")
            return {"status": "error", "tenant": self.base_url, "error": str(e)}

    # ---------------------------------------------------------------- 2. search & discovery
    def search_entities(self, query: Dict[str, Any], options: Optional[Dict[str, Any]] = None,
                        limit: int = 20, source: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        POST /entities/search  body {"query": ..., "options": ...}
        - page[limit] max 100, page[offset] max 5000 (use keyset paging on createdAt beyond that)
        - ALWAYS use "mode": "keyword" when matching names/ids, otherwise the value is tokenized
          (e.g. "QC-2026-001" also matches everything containing "2026").
        - source: SN (notebook, default) | IVT (inventory containers/locations) | CHEMICALS | CONNECTED.
          The wrong source silently returns 0 results.
        """
        if self.mock_mode:
            return self._mock_search(query, limit)
        params: Dict[str, Any] = {"page[limit]": min(limit, 100)}
        if source:
            params["source"] = source
        body: Dict[str, Any] = {"query": query}
        if options:
            body["options"] = options
        return self._request("POST", "/entities/search", params=params, json_body=body,
                             content_type="application/json").json().get("data", [])

    def list_notebooks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Notebooks (type 'journal') you can see: GET /entities?includeTypes=journal."""
        if self.mock_mode:
            return [{"eid": "journal:00000000-0000-0000-0000-000000000001", "name": "Hackathon Team Notebook (mock)"}]
        data = self._request("GET", "/entities", params={"includeTypes": "journal", "page[limit]": min(limit, 100)}).json().get("data", [])
        return [{"eid": d["id"], "name": d.get("attributes", {}).get("name")} for d in data]

    def list_notebook_experiments(self, notebook_eid: str) -> List[Dict[str, Any]]:
        """Experiments in one notebook: GET /entities/{notebook}/children, experiments only."""
        if self.mock_mode:
            return [{"eid": f"experiment:{uuid.uuid4()}", "name": "Mock experiment in notebook",
                     "modifiedAt": "2026-09-23T14:30:00Z", "description": ""}]
        data = self._request("GET", f"/entities/{notebook_eid}/children", params={"page[limit]": 100}).json().get("data", [])
        return [{"eid": d["id"], "name": d["attributes"].get("name", ""), "modifiedAt": d["attributes"].get("modifiedAt") or d["attributes"].get("editedAt", ""),
                 "description": d["attributes"].get("description", "")}
                for d in data if d.get("attributes", {}).get("type") == "experiment"]

    def list_experiments(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Most recently modified, non-template experiments (Search API, sorted by modifiedAt desc)."""
        query = {"$and": [{"$match": {"field": "type", "value": "experiment", "mode": "keyword"}},
                          {"$match": {"field": "isTemplate", "value": False}}]}
        items = self.search_entities(query, options={"sort": {"modifiedAt": "desc"}}, limit=limit)
        return [{"eid": it.get("id") or it.get("attributes", {}).get("eid"),
                 "name": it.get("attributes", {}).get("name", "Untitled Experiment"),
                 "modifiedAt": it.get("attributes", {}).get("modifiedAt", ""),
                 "description": it.get("attributes", {}).get("description", "")} for it in items]

    def get_entity(self, eid: str) -> Dict[str, Any]:
        """GET /entities/{eid}: attributes (name, digest, flags, ...) and relationships (ancestors, owner, ...)."""
        if self.mock_mode:
            return {"id": eid, "type": "entity", "attributes": {
                "eid": eid, "type": eid.split(":")[0] if ":" in eid else "experiment", "name": f"Mock Entity ({eid})",
                "createdAt": "2026-09-23T12:00:00Z", "modifiedAt": "2026-09-23T14:30:00Z", "digest": "00000000"}}
        return self._request("GET", f"/entities/{eid}").json().get("data", {})

    def list_child_entities(self, parent_eid: str) -> List[Dict[str, Any]]:
        """GET /entities/{eid}/children: the elements inside an experiment (drawings, text, tables, files...)."""
        if self.mock_mode:
            return [{"id": f"chemicalDrawing:{uuid.uuid4()}", "type": "entity", "attributes": {"type": "chemicalDrawing", "name": "Reaction Scheme 1"}},
                    {"id": f"text:{uuid.uuid4()}", "type": "entity", "attributes": {"type": "text", "name": "Procedure & Observations"}},
                    {"id": f"imageResource:{uuid.uuid4()}", "type": "entity", "attributes": {"type": "imageResource", "name": "TLC Plate Stain"}}]
        return self._request("GET", f"/entities/{parent_eid}/children").json().get("data", [])

    # ---------------------------------------------------------------- 3. create / write
    def create_experiment(self, name: str, notebook_eid: str, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Create an experiment INSIDE a notebook: POST /entities?digest=<notebook digest>
        with relationships.ancestors = the notebook. (Without ancestors Signals creates an orphan
        experiment that sits in no notebook, so this method refuses to do that.)
        Names must be unique per notebook (409 otherwise). notebook_eid: a journal:... eid from list_notebooks().
        """
        nb = notebook_eid
        if self.mock_mode:
            return {"id": f"experiment:{uuid.uuid4()}", "type": "entity",
                    "attributes": {"type": "experiment", "name": name, "description": description or ""}}
        if not nb:
            raise SignalsError("Pass notebook_eid (a journal:... eid from list_notebooks()) so the experiment is created inside a notebook.")
        body = {"data": {"type": "experiment",
                         "attributes": {"name": name, **({"description": description} if description else {})},
                         "relationships": {"ancestors": {"data": [{"type": "journal", "id": nb}]}}}}
        return self._request("POST", "/entities", params={"digest": self.get_digest(nb)}, json_body=body).json().get("data", {})

    def create_sample(self, experiment_eid: str, template_eid: str,
                      fields: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a sample in an experiment from a sample TEMPLATE (sample:... eid of the template).
        Signals auto-creates the experiment's samples table the first time.
        `fields` = {field_id: value}, using the template's field IDs (read them from
        GET /entities/{template_eid} -> attributes.fields). Sent as [{"id", "content": {"value"}}].
        """
        if self.mock_mode:
            return {"id": f"sample:{uuid.uuid4()}", "type": "entity", "attributes": {"type": "sample", "name": "Sample-001 (mock)"}}
        field_list = [{"id": str(k), "content": {"value": v}} for k, v in (fields or {}).items()]
        body = {"data": {"type": "sample", "attributes": {"fields": field_list},
                         "relationships": {"ancestors": {"data": [{"type": "experiment", "id": experiment_eid}]},
                                           "template": {"data": {"type": "sample", "id": template_eid}}}}}
        return self._request("POST", "/entities", params={"digest": self.get_digest(experiment_eid)},
                             json_body=body).json().get("data", {})

    def upload_child_attachment(self, parent_eid: str, filename: str, content_bytes: bytes,
                                content_type: str = "application/octet-stream", force: bool = False) -> Dict[str, Any]:
        """
        Upload a file as a child element: POST /entities/{eid}/children/{filename}?digest=<parent digest>
        Send the file's own MIME type (text/html makes an editable Text element; image/png an image, ...).
        force=True skips the concurrency check instead of sending the digest (also allows duplicate names).
        """
        if self.mock_mode:
            return {"status": "mock_success", "id": f"uploadedResource:{filename}-mock", "filename": filename,
                    "parentEid": parent_eid, "sizeBytes": len(content_bytes), "contentType": content_type}
        params = {"force": "true"} if force else {"digest": self.get_digest(parent_eid)}
        return self._request("POST", f"/entities/{parent_eid}/children/{filename}", params=params,
                             data=content_bytes, content_type=content_type, timeout=90).json()

    # ---------------------------------------------------------------- 4. chemistry
    def list_chemical_drawings(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Most recent chemicalDrawing elements (Search API). SMILES are fetched via export_entity()."""
        query = {"$and": [{"$match": {"field": "type", "value": "chemicalDrawing", "mode": "keyword"}},
                          {"$match": {"field": "isTemplate", "value": False}}]}
        items = self.search_entities(query, options={"sort": {"modifiedAt": "desc"}}, limit=limit)
        out = []
        for it in items:
            a = it.get("attributes", {})
            eid = it.get("id") or a.get("eid")
            smiles = a.get("smiles")
            if not smiles and not self.mock_mode:
                try:
                    smiles = self.export_entity(eid, format="smiles").strip() or None
                except Exception as e:  # never invent a structure in live mode
                    logger.info(f"No SMILES for {eid}: {e}")
                    smiles = None
            out.append({"id": eid, "name": a.get("name", "Untitled Chemical Drawing"), "smiles": smiles,
                        "formula": a.get("formula", ""), "mw": a.get("mw"), "logp": a.get("logp"), "tpsa": a.get("tpsa"),
                        "hbd": a.get("hbd"), "hba": a.get("hba"), "rotb": a.get("rotb"),
                        "modifiedAt": a.get("modifiedAt", ""), "author": a.get("author", ""), "notebook": a.get("notebook", "")})
        return out

    EXPORT_ACCEPT = {"smiles": "chemical/x-daylight-smiles", "svg": "image/svg+xml", "mol": "chemical/x-mdl-molfile",
                     "mol-v3000": "chemical/x-mdl-molfile-v3000", "cdxml": "chemical/x-cdxml", "inchi": "chemical/x-inchi"}

    def export_entity(self, eid: str, format: str = "smiles") -> str:
        """
        GET /entities/{eid}/export: a chemicalDrawing with format=smiles|svg|mol|mol-v3000|cdxml|inchi;
        with format="" a text element comes back as HTML and a table (grid/materialsTable/samplesContainer) as CSV.
        """
        fmt = (format or "").lower().strip()
        if self.mock_mode:
            return self._mock_export(eid, fmt)
        return self._request("GET", f"/entities/{eid}/export", params={"format": fmt} if fmt else None,
                             accept=f"{self.EXPORT_ACCEPT.get(fmt, '*/*')}, */*").text

    def get_chemical_drawing(self, id_or_eid: str, format: str = "smiles") -> str:
        """
        Structure of a notebook element (chemicalDrawing:..., sample:...) -> GET /entities/{eid}/export
        or of a registered material (asset/batch id)                   -> GET /materials/{id}/drawing
        """
        if ":" in id_or_eid and not id_or_eid.startswith(("asset:", "batch:")):
            return self.export_entity(id_or_eid, format=format)
        fmt = format.lower().strip()
        if self.mock_mode:
            return self._mock_export(id_or_eid, fmt)
        return self._request("GET", f"/materials/{id_or_eid}/drawing", params={"format": fmt},
                             accept=f"{self.EXPORT_ACCEPT.get(fmt, '*/*')}, */*").text

    def get_stoichiometry(self, drawing_eid: str) -> Dict[str, Any]:
        """GET /stoichiometry/{eid}: reactants, products, solvents, conditions of an experiment or chemicalDrawing."""
        if self.mock_mode:
            fx = FIXTURES_DIR / "suzuki_stoichiometry.json"
            if fx.exists():
                return json.loads(fx.read_text(encoding="utf-8"))
            return {"data": {"id": drawing_eid, "attributes": {"reactants": [], "products": []}}}
        return self._request("GET", f"/stoichiometry/{drawing_eid}").json()

    def chemistry_search(self, smiles: str, exact: bool = False, limit: int = 20,
                         source: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Structure search via the Search API ($chemsearch). Default = SUBSTRUCTURE; exact=True -> exact match.
        (There is no /chemistry/search endpoint.)
        """
        q: Dict[str, Any] = {"$chemsearch": {"molecule": smiles, "mime": "chemical/x-daylight-smiles"}}
        if exact:
            q["$chemsearch"]["options"] = "full=true"
        return self.search_entities(q, limit=limit, source=source)

    # ---------------------------------------------------------------- 5. materials & inventory
    def search_materials(self, query: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Registered materials (type 'asset') via the Search API, optionally full-text filtered.
        For libraries: GET /materials/libraries; one asset: GET /materials/{lib}/assets/id/{id}.
        """
        if self.mock_mode:
            reagents = [
                {"id": "asset:m-001", "name": "Phenylboronic acid", "cas": "98-80-6", "formula": "C6H7BO2", "smiles": "OB(O)c1ccccc1"},
                {"id": "asset:m-002", "name": "4-Bromobenzonitrile", "cas": "623-00-7", "formula": "C7H4BrN", "smiles": "N#Cc1ccc(Br)cc1"},
                {"id": "asset:m-003", "name": "Sodium Hydroxide 1.0M", "cas": "1310-73-2", "formula": "NaOH", "smiles": "[Na+].[OH-]"},
                {"id": "asset:m-004", "name": "Aspirin (Acetylsalicylic Acid)", "cas": "50-78-2", "formula": "C9H8O4", "smiles": "CC(=O)Oc1ccccc1C(=O)O"},
                {"id": "asset:m-005", "name": "Caffeine Pure", "cas": "58-08-2", "formula": "C8H10N4O2", "smiles": "Cn1cnc2c1c(=O)n(c(=O)n2C)C"}]
            ql = query.lower()
            return [m for m in reagents if not ql or ql in m["name"].lower() or ql in m["formula"].lower() or ql in m["cas"]][:limit]
        clauses: List[Dict[str, Any]] = [{"$match": {"field": "type", "value": "asset", "mode": "keyword"}}]
        if query:
            clauses.append({"$simple": {"query": query, "operator": "and"}})
        return self.search_entities({"$and": clauses}, limit=limit)

    def list_material_libraries(self) -> List[Dict[str, Any]]:
        """GET /materials/libraries: active material libraries."""
        if self.mock_mode:
            return [{"id": "Compounds", "attributes": {"name": "Compounds"}}, {"id": "Reagents", "attributes": {"name": "Reagents"}}]
        return self._request("GET", "/materials/libraries").json().get("data", [])

    def search_containers(self, query: str = "", limit: int = 20) -> List[Dict[str, Any]]:
        """Inventory containers live in the IVT index: search with source=IVT (SN returns 0)."""
        if self.mock_mode:
            return [{"id": "container:mock-1", "attributes": {"type": "container", "name": "Vial FZ7-001 (mock)"}}]
        clauses: List[Dict[str, Any]] = [{"$match": {"field": "type", "value": "container", "mode": "keyword"}}]
        if query:
            clauses.append({"$simple": {"query": query, "operator": "and"}})
        return self.search_entities({"$and": clauses}, limit=limit, source="IVT")

    # ---------------------------------------------------------------- mock helpers
    def _mock_search(self, query: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        entity_type = ""
        for clause in (query.get("$and", []) if isinstance(query, dict) else []):
            m = clause.get("$match", {})
            if m.get("field") == "type":
                entity_type = m.get("value", "")
        if entity_type == "chemicalDrawing" or "$chemsearch" in query:
            return [{"type": "entity", "id": d["id"], "attributes": {**{k: v for k, v in d.items() if k != "id"}, "eid": d["id"], "type": "chemicalDrawing"}}
                    for d in MOCK_CHEMICAL_DRAWINGS[:limit]]
        fx = FIXTURES_DIR / "experiments_sample.json"
        if fx.exists():
            try:
                return [{"type": "entity", "id": e.get("eid"), "attributes": {"eid": e.get("eid"), "type": "experiment",
                         "name": e.get("name"), "modifiedAt": e.get("modifiedAt")}}
                        for e in json.loads(fx.read_text(encoding="utf-8"))[:limit]]
            except Exception:
                pass
        return []

    def _mock_export(self, eid: str, fmt: str) -> str:
        d = next((x for x in MOCK_CHEMICAL_DRAWINGS if x["id"] == eid), None)
        smiles = d["smiles"] if d else "CC(=O)Oc1ccccc1C(=O)O"
        if fmt == "svg":
            try:
                from rdkit import Chem
                from rdkit.Chem import Draw
                mol = Chem.MolFromSmiles(smiles)
                drawer = Draw.rdMolDraw2D.MolDraw2DSVG(420, 280)
                drawer.DrawMolecule(mol)
                drawer.FinishDrawing()
                return drawer.GetDrawingText()
            except Exception:
                svg = FIXTURES_DIR / "caffeine.svg"
                return svg.read_text(encoding="utf-8") if svg.exists() else "<svg xmlns='http://www.w3.org/2000/svg'/>"
        if fmt in ("mol", "mol-v3000"):
            try:
                from rdkit import Chem
                return Chem.MolToMolBlock(Chem.MolFromSmiles(smiles))
            except Exception:
                return f"\n  mock\n\n  0  0  0  0  0  0            999 V2000\nM  END\n"
        return smiles
