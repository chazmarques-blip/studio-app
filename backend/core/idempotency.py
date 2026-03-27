"""Idempotency Guard — Prevents duplicate expensive operations."""
import asyncio
import time
import logging
from typing import Any

logger = logging.getLogger(__name__)

_active_operations: dict = {}
_LOCK = asyncio.Lock()


async def idempotent_execute(key: str, operation_fn, ttl: int = 3600) -> Any:
    """Execute operation only if not already running/cached for this key.

    Args:
        key: Unique operation key (e.g. "production:project_id:hash")
        operation_fn: Async callable to execute
        ttl: Seconds to cache result
    """
    async with _LOCK:
        if key in _active_operations:
            entry = _active_operations[key]
            if entry["status"] == "running":
                logger.info(f"Idempotency: Operation '{key}' already running, skipping duplicate")
                return {"status": "already_running", "message": "This operation is already in progress"}
            if entry["status"] == "done" and time.time() - entry["ts"] < ttl:
                logger.info(f"Idempotency: Returning cached result for '{key}'")
                return entry["result"]

        _active_operations[key] = {"status": "running", "ts": time.time()}

    try:
        result = await operation_fn()
        _active_operations[key] = {"status": "done", "result": result, "ts": time.time()}

        # Schedule cleanup
        async def _cleanup():
            await asyncio.sleep(ttl)
            _active_operations.pop(key, None)

        asyncio.create_task(_cleanup())
        return result
    except Exception as e:
        _active_operations.pop(key, None)
        raise
