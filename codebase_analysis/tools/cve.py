"""Utility for CVE lookup using NVD API with graceful fallback."""
from __future__ import annotations

import logging
import os
from typing import Dict, List

import requests

LOGGER = logging.getLogger(__name__)
NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"


class CVEChecker:
    """Checks code packages or libraries against NVD vulnerabilities."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("NVD_API_KEY")

    def search(self, keyword: str, max_results: int = 10) -> List[Dict[str, str]]:
        """Search NVD for CVEs containing the given keyword."""
        if not self.api_key:
            if os.getenv("ALLOW_STUB", "0") in {"1", "true", "yes"}:
                LOGGER.warning(
                    "NVD_API_KEY not set, but ALLOW_STUB enabled; returning empty CVE list."
                )
                return []
            raise RuntimeError(
                "NVD_API_KEY not set. Provide a valid NVD API key to enable CVE lookups or set ALLOW_STUB=1."
            )

        params = {
            "keywordSearch": keyword,
            "resultsPerPage": max_results,
            "apiKey": self.api_key,
        }
        try:
            r = requests.get(NVD_API_URL, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
        except Exception as exc:  # pragma: no cover
            if os.getenv("ALLOW_STUB", "0") in {"1", "true", "yes"}:
                LOGGER.warning("CVE API request failed but ALLOW_STUB enabled: %s", exc)
                return []
            raise RuntimeError(f"CVE API request failed: {exc}")

        results: List[Dict[str, str]] = []
        for item in data.get("vulnerabilities", []):
            cve = item.get("cve")
            if not cve:
                continue
            results.append({
                "id": cve.get("id"),
                "summary": cve.get("descriptions", [{}])[0].get("value", ""),
            })
        return results 