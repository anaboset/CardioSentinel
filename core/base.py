"""Base classes for agents and tools with error handling."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable
import time

from config import MAX_RETRIES, RETRY_BACKOFF

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """Abstract base class for all tools."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"tool.{name}")
    
    @abstractmethod
    def run(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool. Must be implemented by subclasses."""
        pass
    
    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with exponential backoff retry logic."""
        last_error = None
        
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                self.logger.info(f"[{self.name}] Attempt {attempt}/{MAX_RETRIES}")
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES:
                    wait_time = RETRY_BACKOFF ** (attempt - 1)
                    self.logger.warning(
                        f"[{self.name}] Attempt {attempt} failed: {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"[{self.name}] All {MAX_RETRIES} attempts failed")
        
        raise last_error
    
    def execute_with_fallback(
        self, 
        primary: Callable, 
        fallback: Callable,
        *args, 
        **kwargs
    ) -> Any:
        """Try primary function, fall back to secondary on failure."""
        try:
            self.logger.info(f"[{self.name}] Trying primary execution")
            return primary(*args, **kwargs)
        except Exception as e:
            self.logger.warning(f"[{self.name}] Primary failed: {e}. Using fallback.")
            try:
                return fallback(*args, **kwargs)
            except Exception as e2:
                self.logger.error(f"[{self.name}] Fallback also failed: {e2}")
                raise


class BaseAgent(ABC):
    """Abstract base class for all agents."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"agent.{name}")
    
    @abstractmethod
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent logic. Must be implemented by subclasses."""
        pass
    
    def log_execution(self, message: str):
        """Consistent logging format."""
        self.logger.info(f"[{self.name}] {message}")
    
    def log_error(self, error: Exception):
        """Log error with context."""
        self.logger.error(f"[{self.name}] Error: {str(error)}", exc_info=True)


class ToolRegistry:
    """Registry for managing tools with lifecycle."""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self.logger = logging.getLogger("tool_registry")
    
    def register(self, name: str, tool: BaseTool) -> None:
        """Register a tool."""
        self._tools[name] = tool
        self.logger.info(f"Registered tool: {name}")
    
    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self) -> list:
        """List all registered tools."""
        return list(self._tools.keys())