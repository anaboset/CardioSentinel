"""Drug interaction checking via openFDA API with local fallback."""

import logging

from core.base import BaseTool
from services.openfda_client import OpenFDAClient
from services.redis_cache import MEDICATION_CACHE_TTL_SECONDS

logger = logging.getLogger(__name__)


class DrugInteractionTool(BaseTool):
    """Checks drug-drug interactions using openFDA and curated knowledge base."""

    def __init__(self, client=None, cache=None):
        super().__init__("drug_interaction")
        self._client = client or OpenFDAClient()
        self._cache = cache

    def run(self, medications: list) -> dict:
        logger.info("[DrugInteractionTool] Checking: %s", medications)

        cache_key = {"medications": sorted(medications)}
        if self._cache is not None:
            cached = self._cache.get("drug_interactions", cache_key)
            if cached is not None:
                return cached

        def _check():
            return self._client.check_interactions(medications)

        try:
            result = self.execute_with_retry(_check)
            if self._cache is not None:
                self._cache.set("drug_interactions", cache_key, result, ttl_seconds=MEDICATION_CACHE_TTL_SECONDS)
            return result
        except Exception as exc:
            logger.error("[DrugInteractionTool] Failed: %s", exc)
            return {"interactions_found": False, "warnings": [], "error": str(exc)}
