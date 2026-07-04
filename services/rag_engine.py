"""Semantic RAG engine for cardiovascular guideline retrieval."""

import logging
import math
import re
from typing import Dict, List, Tuple

from services.redis_cache import GUIDELINE_CACHE_TTL_SECONDS, get_cache

from data.guidelines_corpus import GUIDELINE_CORPUS

logger = logging.getLogger(__name__)


def _tokenize(text: str) -> set:
    """Simple tokenizer for TF-based similarity."""
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _tfidf_similarity(query_tokens: set, doc_tokens: set, corpus_size: int, doc_freq: int) -> float:
    """Compute TF-IDF cosine similarity between query and document."""
    if not query_tokens or not doc_tokens:
        return 0.0
    intersection = query_tokens & doc_tokens
    if not intersection:
        return 0.0
    tf = len(intersection) / len(doc_tokens)
    idf = math.log((corpus_size + 1) / (doc_freq + 1)) + 1
    return tf * idf


class RAGEngine:
    """
    Semantic guideline retrieval engine.
    Uses TF-IDF similarity over curated ACC/AHA/ESC guideline corpus.
    """

    def __init__(self, cache=None):
        self._corpus = GUIDELINE_CORPUS
        self._cache = cache or get_cache()
        self._build_index()

    def _build_index(self) -> None:
        """Pre-compute token sets for each document."""
        self._doc_tokens = [_tokenize(doc["text"] + " " + doc["topic"]) for doc in self._corpus]
        self._condition_index: Dict[str, List[int]] = {}
        for i, doc in enumerate(self._corpus):
            self._condition_index.setdefault(doc["condition"], []).append(i)

    def search(
        self,
        clinical_question: str,
        conditions: List[str],
        top_k: int = 5,
        min_score: float = 0.05,
    ) -> List[Tuple[dict, float]]:
        """
        Retrieve top-k guideline chunks matching query and patient conditions.
        Returns list of (document, score) tuples.
        """
        query_tokens = _tokenize(clinical_question)
        for cond in conditions:
            query_tokens |= _tokenize(cond)

        candidates: set = set()
        for cond in conditions:
            for idx in self._condition_index.get(cond, []):
                candidates.add(idx)

        if not candidates:
            candidates = set(range(len(self._corpus)))

        scored: List[Tuple[dict, float]] = []
        for idx in candidates:
            doc = self._corpus[idx]
            doc_tokens = self._doc_tokens[idx]
            doc_freq = sum(1 for tokens in self._doc_tokens if doc_tokens & tokens)
            score = _tfidf_similarity(query_tokens, doc_tokens, len(self._corpus), doc_freq)

            if cond_match := any(c == doc["condition"] for c in conditions):
                score += 0.3

            if score >= min_score:
                scored.append((doc, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        results = scored[:top_k]
        logger.info(
            "RAG search: query='%s', conditions=%s, results=%d",
            clinical_question[:50],
            conditions,
            len(results),
        )
        return results

    def retrieve(
        self,
        patient_summary: dict,
        clinical_question: str,
    ) -> dict:
        """High-level retrieval matching GuidelineRetrieverTool interface."""
        from utils.normalization import normalize_conditions

        cache_key = {"query": clinical_question, "conditions": sorted(patient_summary.get("conditions", []))}
        cached = self._cache.get("guideline_search", cache_key)
        if cached is not None:
            return cached

        conditions = normalize_conditions(patient_summary.get("conditions", []))
        ldl = patient_summary.get("ldl", 0)
        if ldl and ldl > 130 and "dyslipidemia" not in conditions:
            conditions = conditions + ["dyslipidemia"]

        results = self.search(clinical_question, conditions)

        if not results:
            return {
                "status": "insufficient_evidence",
                "recommendations": [],
                "sources": [],
            }

        recommendations = [doc["text"] for doc, _ in results]
        sources = list(dict.fromkeys(doc["source"] for doc, _ in results))
        avg_score = sum(s for _, s in results) / len(results)
        confidence = "high" if avg_score > 0.4 else "moderate" if avg_score > 0.2 else "low"

        result = {
            "status": "ok",
            "recommendations": recommendations,
            "sources": sources,
            "confidence": confidence,
            "chunks_retrieved": len(results),
        }
        self._cache.set("guideline_search", cache_key, result, ttl_seconds=GUIDELINE_CACHE_TTL_SECONDS)
        return result
