"""Centralized logging and LangSmith observability configuration."""

import logging
import os
import sys

from config import LOG_FORMAT, LOG_LEVEL


def setup_logging() -> None:
    """Configure root logger with consistent format."""
    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def setup_langsmith() -> bool:
    """
    Enable LangSmith tracing when LANGCHAIN_TRACING_V2=true.
    Returns True if tracing was enabled.
    """
    tracing = os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true"
    if not tracing:
        return False

    api_key = os.getenv("LANGCHAIN_API_KEY")
    project = os.getenv("LANGCHAIN_PROJECT", "cardiosentinel")

    if not api_key:
        logging.getLogger(__name__).warning(
            "LANGCHAIN_TRACING_V2 is enabled but LANGCHAIN_API_KEY is missing"
        )
        return False

    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_PROJECT", project)
    logging.getLogger(__name__).info(
        "LangSmith tracing enabled for project: %s", project
    )
    return True


def init_app_environment() -> None:
    """Load dotenv, configure logging, and optionally enable LangSmith."""
    from dotenv import load_dotenv

    load_dotenv()
    setup_logging()
    setup_langsmith()
