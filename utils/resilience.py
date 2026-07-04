"""Retry, timeout, and circuit-breaker utilities for resilient tool/LLM calls."""

import logging
import signal
import time
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from config import MAX_RETRIES, RETRY_BACKOFF, TIMEOUT_SECONDS, MAX_LOOP_ITERATIONS

logger = logging.getLogger(__name__)

T = TypeVar("T")


class TimeoutError(Exception):
    """Raised when an operation exceeds its time limit."""


class LoopLimitExceeded(Exception):
    """Raised when iteration cap is reached."""


def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = MAX_RETRIES,
    backoff: float = RETRY_BACKOFF,
    operation_name: str = "operation",
) -> T:
    """Execute *func* with exponential backoff on failure."""
    last_error: Optional[Exception] = None

    for attempt in range(1, max_retries + 1):
        try:
            logger.info("[%s] Attempt %d/%d", operation_name, attempt, max_retries)
            return func()
        except Exception as exc:
            last_error = exc
            if attempt < max_retries:
                wait = backoff ** (attempt - 1)
                logger.warning(
                    "[%s] Attempt %d failed: %s. Retrying in %.1fs...",
                    operation_name,
                    attempt,
                    exc,
                    wait,
                )
                time.sleep(wait)
            else:
                logger.error("[%s] All %d attempts failed", operation_name, max_retries)

    raise last_error  # type: ignore[misc]


def with_timeout(seconds: int = TIMEOUT_SECONDS):
    """Decorator that raises TimeoutError if the wrapped function runs too long."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            def _handler(signum: int, frame: Any) -> None:
                raise TimeoutError(
                    f"{func.__name__} exceeded {seconds}s timeout"
                )

            old_handler = signal.signal(signal.SIGALRM, _handler)
            signal.alarm(seconds)
            try:
                return func(*args, **kwargs)
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)

        return wrapper

    return decorator


def check_loop_limit(counter: int, label: str = "loop") -> None:
    """Raise if *counter* exceeds MAX_LOOP_ITERATIONS."""
    if counter >= MAX_LOOP_ITERATIONS:
        raise LoopLimitExceeded(
            f"{label} exceeded maximum iterations ({MAX_LOOP_ITERATIONS})"
        )
