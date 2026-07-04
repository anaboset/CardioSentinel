"""openFDA API client for drug interaction lookups."""

import logging
import os
from typing import List, Optional
from urllib.parse import quote

import httpx

from data.drug_knowledge import DRUG_ALIASES, INTERACTION_DB
from utils.resilience import retry_with_backoff

logger = logging.getLogger(__name__)

OPENFDA_BASE = "https://api.fda.gov/drug/label.json"
OPENFDA_ENABLED = os.getenv("OPENFDA_ENABLED", "false").lower() == "true"


def normalize_drug_name(drug: str) -> str:
    """Normalize drug name using aliases."""
    key = drug.lower().strip().replace(" ", "_").replace("-", "_")
    return DRUG_ALIASES.get(key, key)


class OpenFDAClient:
    """Client for openFDA drug label API with local fallback."""

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    def _query_fda_interactions(self, drug_a: str, drug_b: str) -> Optional[str]:
        """Query openFDA for interaction warnings between two drugs."""

        def _fetch() -> Optional[str]:
            search_term = f'"{drug_a}" AND "{drug_b}"'
            url = f"{OPENFDA_BASE}?search=drug_interactions:{quote(search_term)}&limit=1"
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url)
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                data = response.json()
                results = data.get("results", [])
                if not results:
                    return None
                interactions = results[0].get("drug_interactions", [])
                if interactions:
                    text = interactions[0][:300]
                    return f"{drug_a} + {drug_b}: {text} (source: openFDA)"
                return None

        try:
            return retry_with_backoff(_fetch, operation_name=f"openFDA({drug_a},{drug_b})")
        except Exception as exc:
            logger.warning("openFDA lookup failed for %s + %s: %s", drug_a, drug_b, exc)
            return None

    def check_interactions(self, medications: List[str]) -> dict:
        """
        Check drug-drug interactions using openFDA API with local DB fallback.
        """
        meds = [normalize_drug_name(m) for m in medications]
        warnings: List[str] = []

        for i, drug_a in enumerate(meds):
            for drug_b in meds[i + 1:]:
                pair = (drug_a, drug_b)
                pair_rev = (drug_b, drug_a)

                if pair in INTERACTION_DB:
                    warnings.append(f"{drug_a} + {drug_b}: {INTERACTION_DB[pair]}")
                    continue
                if pair_rev in INTERACTION_DB:
                    warnings.append(f"{drug_b} + {drug_a}: {INTERACTION_DB[pair_rev]}")
                    continue

                if OPENFDA_ENABLED:
                    fda_result = self._query_fda_interactions(drug_a, drug_b)
                    if fda_result:
                        warnings.append(fda_result)

        return {
            "interactions_found": len(warnings) > 0,
            "warnings": warnings,
            "source": "openFDA+local" if warnings else "none",
        }
