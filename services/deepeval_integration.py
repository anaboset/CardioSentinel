"""DeepEval integration for RAG evaluation and quality metrics.

Provides metrics for evaluating retrieval quality, answer relevance,
and clinical guideline coherence.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("clinical_mcp_server.evaluation")

try:
    from deepeval.metrics import AnswerRelevanceMetric, ContextualRelevanceMetric, FaithfulnessMetric
    from deepeval.test_case import LLMTestCase

    DEEPEVAL_AVAILABLE = True
except ImportError:  # pragma: no cover
    DEEPEVAL_AVAILABLE = False


class RAGEvaluator:
    """Evaluate RAG retrieval quality and answer generation."""

    def __init__(self, enabled: bool = DEEPEVAL_AVAILABLE):
        self.enabled = enabled and DEEPEVAL_AVAILABLE
        if self.enabled:
            logger.info("DeepEval evaluation enabled")

    def evaluate_retrieval_quality(
        self, query: str, retrieved_documents: List[str], expected_sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Evaluate retrieval quality for a given query.

        Args:
            query: Clinical query that was executed.
            retrieved_documents: List of retrieved guideline texts.
            expected_sources: Optional list of expected source documents.

        Returns:
            Dictionary with evaluation metrics.
        """
        if not retrieved_documents:
            return {
                "retrieval_quality": "poor",
                "retrieved_count": 0,
                "metrics": {},
                "recommendation": "No documents retrieved",
            }

        metrics = {
            "retrieval_count": len(retrieved_documents),
            "avg_document_length": sum(len(doc) for doc in retrieved_documents) / len(retrieved_documents),
            "total_content_length": sum(len(doc) for doc in retrieved_documents),
        }

        if DEEPEVAL_AVAILABLE:
            try:
                context_str = " ".join(retrieved_documents[:3])

                context_metric = ContextualRelevanceMetric(
                    threshold=0.5, model="gpt-4", expected_output=f"Relevant to: {query}"
                )
                test_case = LLMTestCase(input=query, actual_output=context_str, expected_output=f"Relevant to: {query}")
                score = context_metric.measure(test_case)
                metrics["contextual_relevance"] = score

            except Exception as e:  # pragma: no cover
                logger.warning("DeepEval contextual relevance check failed: %s", e)

        quality_score = (
            min(100, len(retrieved_documents) * 30 + metrics.get("contextual_relevance", 0.5) * 70) / 100
        )

        return {
            "retrieval_quality": "good" if quality_score > 0.7 else "fair" if quality_score > 0.4 else "poor",
            "quality_score": round(quality_score, 3),
            "retrieved_count": len(retrieved_documents),
            "metrics": metrics,
            "expected_sources": expected_sources,
            "recommendation": (
                "Good retrieval quality; results are relevant" if quality_score > 0.7 else "Consider refining query"
            ),
        }

    def evaluate_answer_relevance(self, query: str, answer: str) -> Dict[str, Any]:
        """Evaluate answer relevance to the original query.

        Args:
            query: Original clinical query.
            answer: Generated answer or evidence.

        Returns:
            Dictionary with relevance metrics.
        """
        if not answer:
            return {"relevance": "not_applicable", "score": 0, "reason": "Empty answer"}

        metrics: Dict[str, Any] = {
            "answer_length": len(answer),
            "query_length": len(query),
            "ratio": len(answer) / max(1, len(query)),
        }

        query_terms = set(query.lower().split())
        answer_terms = set(answer.lower().split())
        overlap = len(query_terms & answer_terms)
        metrics["term_overlap"] = overlap / max(1, len(query_terms))

        try:
            if DEEPEVAL_AVAILABLE:
                relevance_metric = AnswerRelevanceMetric(threshold=0.5, model="gpt-4")
                test_case = LLMTestCase(input=query, actual_output=answer)
                score = relevance_metric.measure(test_case)
                metrics["deepeval_relevance_score"] = score
        except Exception as e:  # pragma: no cover
            logger.warning("DeepEval answer relevance check failed: %s", e)

        relevance_score = metrics.get("deepeval_relevance_score", metrics.get("term_overlap", 0))

        return {
            "relevance": "high" if relevance_score > 0.7 else "moderate" if relevance_score > 0.4 else "low",
            "score": round(relevance_score, 3),
            "metrics": metrics,
        }

    def evaluate_clinical_coherence(self, guideline_text: str) -> Dict[str, Any]:
        """Evaluate coherence and medical appropriateness of guideline text.

        Args:
            guideline_text: Guideline or evidence text to evaluate.

        Returns:
            Dictionary with coherence metrics.
        """
        if not guideline_text:
            return {"coherence": "invalid", "score": 0, "issues": ["Empty text"]}

        issues: List[str] = []
        metrics: Dict[str, Any] = {"text_length": len(guideline_text)}

        sentences = [s.strip() for s in guideline_text.split(".") if s.strip()]
        metrics["sentence_count"] = len(sentences)

        keywords = {
            "clinical": ["patient", "treatment", "therapy", "diagnosis", "condition", "drug", "medication"],
            "evidence": ["study", "guideline", "trial", "recommendation", "evidence", "based"],
            "safety": ["contraindication", "adverse", "warning", "precaution", "risk", "toxicity"],
        }

        for category, keyword_list in keywords.items():
            found = sum(1 for kw in keyword_list if kw.lower() in guideline_text.lower())
            metrics[f"{category}_keywords"] = found

        if metrics["sentence_count"] == 0:
            issues.append("No complete sentences found")

        if metrics["clinical_keywords"] == 0:
            issues.append("No clinical terminology detected")

        if metrics["evidence_keywords"] == 0:
            issues.append("No evidence-based language detected")

        coherence_score = (
            min(100, metrics.get("sentence_count", 1) * 5 + metrics.get("evidence_keywords", 0) * 10) / 100
        )

        return {
            "coherence": "good" if coherence_score > 0.7 else "fair" if coherence_score > 0.4 else "poor",
            "score": round(coherence_score, 3),
            "metrics": metrics,
            "issues": issues,
        }


def evaluate_guideline_response(
    query: str, retrieved_evidence: List[Dict[str, Any]], sources: List[str]
) -> Dict[str, Any]:
    """Comprehensive evaluation of guideline retrieval response.

    Args:
        query: Clinical query.
        retrieved_evidence: List of retrieved evidence dictionaries.
        sources: List of evidence sources.

    Returns:
        Comprehensive evaluation report.
    """
    evaluator = RAGEvaluator()

    evidence_texts = [item.get("text", "") for item in retrieved_evidence]
    retrieval_eval = evaluator.evaluate_retrieval_quality(query, evidence_texts, sources)

    evidence_samples = [item.get("text", "")[:500] for item in retrieved_evidence[:2]]
    coherence_evals = [evaluator.evaluate_clinical_coherence(text) for text in evidence_samples]

    return {
        "query": query,
        "retrieval_evaluation": retrieval_eval,
        "coherence_evaluations": coherence_evals,
        "overall_quality": (
            "excellent"
            if retrieval_eval.get("quality_score", 0) > 0.8
            else "good"
            if retrieval_eval.get("quality_score", 0) > 0.6
            else "fair"
            if retrieval_eval.get("quality_score", 0) > 0.4
            else "poor"
        ),
        "source_count": len(sources),
        "recommendations": [
            "Retrieved evidence is comprehensive and relevant" if retrieval_eval.get("quality_score", 0) > 0.7 else "",
            "Consider additional sources for comprehensive coverage" if len(sources) < 2 else "",
            "Evidence is well-structured and coherent" if all(c.get("score", 0) > 0.6 for c in coherence_evals) else "",
        ],
    }
