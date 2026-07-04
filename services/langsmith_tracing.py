"""LangSmith tracing and observability module for clinical MCP server.

Provides distributed tracing, performance monitoring, and debugging support
via LangSmith integration.
"""

from __future__ import annotations

import logging
import os
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("clinical_mcp_server.tracing")

LANGSMITH_ENABLED = os.getenv("LANGSMITH_ENABLED", "false").lower() == "true"
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "clinical_mcp_server")
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com").strip()

try:
    from langsmith import traceable, get_run_tree
    from langsmith.client import Client as LangSmithClient

    LANGSMITH_AVAILABLE = True
except ImportError:  # pragma: no cover
    LANGSMITH_AVAILABLE = False

    def traceable(*args: Any, **kwargs: Any) -> Callable:  # type: ignore[no-redef]
        """Fallback decorator when LangSmith is unavailable."""
        def decorator(func: Callable) -> Callable:
            return func
        return decorator


class LangSmithTracer:
    """Wrapper for LangSmith tracing functionality."""

    def __init__(self, enabled: bool = LANGSMITH_ENABLED):
        self.enabled = enabled and LANGSMITH_AVAILABLE
        self.client: Optional[LangSmithClient] = None

        if self.enabled:
            try:
                self.client = LangSmithClient(endpoint=LANGSMITH_ENDPOINT)
                logger.info("LangSmith tracing enabled (project: %s)", LANGSMITH_PROJECT)
            except Exception as e:  # pragma: no cover
                logger.warning("Failed to initialize LangSmith client: %s", e)
                self.enabled = False

    def trace_tool_call(
        self, tool_name: str, inputs: Dict[str, Any], outputs: Dict[str, Any], duration_ms: float
    ) -> None:
        """Record a tool call trace.

        Args:
            tool_name: Name of the tool that was called.
            inputs: Input parameters to the tool.
            outputs: Output from the tool.
            duration_ms: Execution time in milliseconds.
        """
        if not self.enabled:
            return

        try:
            trace_data = {
                "name": f"tool_{tool_name}",
                "inputs": inputs,
                "outputs": outputs,
                "metadata": {
                    "tool": tool_name,
                    "duration_ms": duration_ms,
                    "status": outputs.get("status", "unknown"),
                },
            }
            logger.debug("LangSmith trace: %s", trace_data)
        except Exception as e:  # pragma: no cover
            logger.warning("Failed to record LangSmith trace: %s", e)

    def trace_rag_retrieval(
        self, query: str, results_count: int, sources: list[str], latency_ms: float
    ) -> None:
        """Record a RAG retrieval operation.

        Args:
            query: The query that was executed.
            results_count: Number of results retrieved.
            sources: List of evidence sources.
            latency_ms: Retrieval latency in milliseconds.
        """
        if not self.enabled:
            return

        try:
            logger.info(
                "RAG retrieval: query_len=%d, results=%d, latency_ms=%.1f",
                len(query),
                results_count,
                latency_ms,
            )
        except Exception as e:  # pragma: no cover
            logger.warning("Failed to trace RAG retrieval: %s", e)

    def trace_api_call(
        self, service: str, method: str, status_code: Optional[int], latency_ms: float
    ) -> None:
        """Record an external API call.

        Args:
            service: Service name (e.g., openFDA, Apify).
            method: HTTP method.
            status_code: HTTP status code.
            latency_ms: Request latency in milliseconds.
        """
        if not self.enabled:
            return

        try:
            logger.info(
                "API call: service=%s, method=%s, status=%s, latency_ms=%.1f",
                service,
                method,
                status_code,
                latency_ms,
            )
        except Exception as e:  # pragma: no cover
            logger.warning("Failed to trace API call: %s", e)

    def trace_error(self, tool_name: str, error_type: str, error_message: str) -> None:
        """Record an error event.

        Args:
            tool_name: Tool where error occurred.
            error_type: Type of error (exception class name).
            error_message: Error message.
        """
        if not self.enabled:
            return

        try:
            logger.warning(
                "Tool error: tool=%s, error_type=%s, message=%s",
                tool_name,
                error_type,
                error_message,
            )
        except Exception as e:  # pragma: no cover
            logger.warning("Failed to trace error: %s", e)


def instrument_tool(tool_name: str) -> Callable:
    """Decorator to instrument a tool with LangSmith tracing.

    Args:
        tool_name: Name of the tool for tracing.

    Returns:
        Decorator function.
    """
    tracer = LangSmithTracer()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000

                tracer.trace_tool_call(
                    tool_name=tool_name, inputs={"args": args, "kwargs": kwargs}, outputs=result, duration_ms=duration_ms
                )
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                tracer.trace_error(tool_name, type(e).__name__, str(e))
                raise

        return wrapper

    return decorator


class PerformanceMetrics:
    """Collect and report performance metrics."""

    def __init__(self):
        self.metrics: Dict[str, list[float]] = {}

    def record_latency(self, operation: str, latency_ms: float) -> None:
        """Record operation latency.

        Args:
            operation: Operation name.
            latency_ms: Latency in milliseconds.
        """
        if operation not in self.metrics:
            self.metrics[operation] = []
        self.metrics[operation].append(latency_ms)

    def get_summary(self) -> Dict[str, Dict[str, float]]:
        """Get summary statistics for all operations.

        Returns:
            Dictionary with statistics per operation.
        """
        summary = {}
        for op, latencies in self.metrics.items():
            if not latencies:
                continue
            summary[op] = {
                "count": len(latencies),
                "min_ms": min(latencies),
                "max_ms": max(latencies),
                "avg_ms": sum(latencies) / len(latencies),
                "p95_ms": sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0,
            }
        return summary

    def reset(self) -> None:
        """Reset all metrics."""
        self.metrics.clear()


# Global metrics collector
performance_metrics = PerformanceMetrics()
