"""Contraindication checking against curated clinical knowledge base."""

import logging

from core.base import BaseTool
from data.drug_knowledge import CONTRAINDICATION_DB
from services.redis_cache import MEDICATION_CACHE_TTL_SECONDS
from utils.normalization import normalize_conditions, normalize_medication

logger = logging.getLogger(__name__)


def _normalize_med(med: str) -> str:
    return normalize_medication(med)


class ContraindicationChecker(BaseTool):
    """Flags medications contraindicated given patient conditions."""

    def __init__(self, cache=None):
        super().__init__("contraindication_checker")
        self._cache = cache

    def run(self, conditions: list, proposed_medications: list) -> dict:
        logger.info(
            "[ContraindicationChecker] Conditions: %s, Meds: %s",
            conditions,
            proposed_medications,
        )
        cache_key = {"conditions": sorted(conditions or []), "medications": sorted(proposed_medications or [])}
        if self._cache is not None:
            cached = self._cache.get("contraindications", cache_key)
            if cached is not None:
                return cached

        conditions_clean = normalize_conditions(conditions)
        meds_clean = [_normalize_med(m) for m in proposed_medications]
        flags = []

        for condition in conditions_clean:
            if condition in CONTRAINDICATION_DB:
                blocked = CONTRAINDICATION_DB[condition]
                for med in meds_clean:
                    if med in blocked:
                        flags.append(
                            f"CONTRAINDICATED: {med} is contraindicated in {condition}."
                        )

        result = {
            "contraindications_found": len(flags) > 0,
            "flags": flags,
        }
        if self._cache is not None:
            self._cache.set("contraindications", cache_key, result, ttl_seconds=MEDICATION_CACHE_TTL_SECONDS)
        return result
