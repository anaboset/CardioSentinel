"""Redis-backed caching layer for clinical MCP server.

Provides distributed caching for guideline retrieval, drug interactions,
and contraindication lookups with TTL and invalidation support.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Any, Optional

logger = logging.getLogger("clinical_mcp_server.caching")

REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
GUIDELINE_CACHE_TTL_SECONDS = int(os.getenv("GUIDELINE_CACHE_TTL_SECONDS", "1800"))
MEDICATION_CACHE_TTL_SECONDS = int(os.getenv("MEDICATION_CACHE_TTL_SECONDS", "900"))

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:  # pragma: no cover
    REDIS_AVAILABLE = False


class RedisCache:
    """Redis-backed cache with TTL support."""

    def __init__(self, enabled: bool = REDIS_ENABLED):
        self.enabled = enabled and REDIS_AVAILABLE
        self.client: Optional[redis.Redis] = None

        if self.enabled:
            try:
                self.client = redis.Redis(
                    host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True, socket_connect_timeout=5
                )
                self.client.ping()
                logger.info("Redis cache initialized (host=%s, port=%d, db=%d)", REDIS_HOST, REDIS_PORT, REDIS_DB)
            except Exception as e:  # pragma: no cover
                logger.warning("Failed to connect to Redis: %s", e)
                self.enabled = False
                self.client = None

    def _make_key(self, prefix: str, query_or_params: str | dict) -> str:
        """Generate a cache key from query or parameters.

        Args:
            prefix: Cache key prefix (e.g., "guideline", "interaction").
            query_or_params: Query string or parameter dictionary.

        Returns:
            Cache key suitable for Redis.
        """
        if isinstance(query_or_params, dict):
            content = json.dumps(query_or_params, sort_keys=True)
        else:
            content = str(query_or_params).lower().strip()

        digest = hashlib.md5(content.encode()).hexdigest()
        return f"cache:{prefix}:{digest}"

    def get(self, prefix: str, query_or_params: str | dict) -> Optional[Any]:
        """Retrieve a cached value.

        Args:
            prefix: Cache key prefix.
            query_or_params: Query string or parameter dictionary.

        Returns:
            Cached value (deserialized JSON) or None if not found.
        """
        if not self.enabled or self.client is None:
            return None

        try:
            key = self._make_key(prefix, query_or_params)
            value = self.client.get(key)
            if value:
                logger.debug("Cache hit: %s", key)
                return json.loads(value)
            logger.debug("Cache miss: %s", key)
            return None
        except Exception as e:  # pragma: no cover
            logger.warning("Cache get failed: %s", e)
            return None

    def set(self, prefix: str, query_or_params: str | dict, value: Any, ttl_seconds: int = CACHE_TTL_SECONDS) -> bool:
        """Store a value in cache.

        Args:
            prefix: Cache key prefix.
            query_or_params: Query string or parameter dictionary.
            value: Value to cache (will be JSON serialized).
            ttl_seconds: Time-to-live in seconds.

        Returns:
            True if set succeeded, False otherwise.
        """
        if not self.enabled or self.client is None:
            return False

        try:
            key = self._make_key(prefix, query_or_params)
            serialized = json.dumps(value)
            self.client.setex(key, ttl_seconds, serialized)
            logger.debug("Cache set: %s (ttl=%ds)", key, ttl_seconds)
            return True
        except Exception as e:  # pragma: no cover
            logger.warning("Cache set failed: %s", e)
            return False

    def delete(self, prefix: str, query_or_params: str | dict) -> bool:
        """Delete a cached value.

        Args:
            prefix: Cache key prefix.
            query_or_params: Query string or parameter dictionary.

        Returns:
            True if deleted, False otherwise.
        """
        if not self.enabled or self.client is None:
            return False

        try:
            key = self._make_key(prefix, query_or_params)
            deleted = self.client.delete(key)
            if deleted:
                logger.debug("Cache deleted: %s", key)
            return bool(deleted)
        except Exception as e:  # pragma: no cover
            logger.warning("Cache delete failed: %s", e)
            return False

    def invalidate(self, prefix: str, query_or_params: str | dict) -> bool:
        """Invalidate a single cached entry."""
        return self.delete(prefix, query_or_params)

    def clear_by_prefix(self, prefix: str) -> int:
        """Clear all cache entries with a given prefix.

        Args:
            prefix: Cache key prefix to clear.

        Returns:
            Number of keys deleted.
        """
        if not self.enabled or self.client is None:
            return 0

        try:
            pattern = f"cache:{prefix}:*"
            cursor = 0
            deleted_count = 0

            while True:
                cursor, keys = self.client.scan(cursor, match=pattern, count=100)
                if keys:
                    deleted_count += self.client.delete(*keys)
                if cursor == 0:
                    break

            logger.info("Cleared %d cache entries with prefix: %s", deleted_count, prefix)
            return deleted_count
        except Exception as e:  # pragma: no cover
            logger.warning("Cache clear failed: %s", e)
            return 0

    def stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics.
        """
        if not self.enabled or self.client is None:
            return {"enabled": False, "stats": None}

        try:
            info = self.client.info()
            return {
                "enabled": True,
                "connected": True,
                "used_memory_mb": info.get("used_memory", 0) / (1024 * 1024),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
            }
        except Exception as e:  # pragma: no cover
            logger.warning("Failed to get cache stats: %s", e)
            return {"enabled": True, "connected": False, "error": str(e)}


# Global cache instance
_cache_instance: Optional[RedisCache] = None


def get_cache() -> RedisCache:
    """Get the global cache instance.

    Returns:
        RedisCache instance.
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache()
    return _cache_instance


def cached(prefix: str, ttl_seconds: int = CACHE_TTL_SECONDS):
    """Decorator to cache function results.

    Args:
        prefix: Cache key prefix.
        ttl_seconds: Cache TTL in seconds.

    Returns:
        Decorator function.
    """
    def decorator(func):
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            cache = get_cache()
            cache_key = {"args": args, "kwargs": kwargs}
            cached_value = cache.get(prefix, cache_key)
            if cached_value is not None:
                logger.debug("Returning cached result for %s", prefix)
                return cached_value

            result = func(*args, **kwargs)
            cache.set(prefix, cache_key, result, ttl_seconds)
            return result

        return wrapper

    return decorator
