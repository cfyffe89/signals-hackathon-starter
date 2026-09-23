import os
import logging
import requests
from typing import List, Dict, Any, Optional

logger = logging.getLogger("signals_client")

class SignalsClient:
    """
    Standard Revvity Signals Notebook REST API client.
    Includes mock fallback for offline hackathon development.
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

    def list_experiments(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Fetch accessible experiment notebooks."""
        if self.mock_mode:
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
        try:
            res = requests.post(url, headers=headers, data=content_bytes, timeout=30)
            res.raise_for_status()
            return res.json()
        except Exception as e:
            logger.error(f"Failed to upload {filename} to Signals: {e}")
            raise
