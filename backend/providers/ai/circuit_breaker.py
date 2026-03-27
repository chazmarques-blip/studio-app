"""Circuit Breaker — Automatic failover between AI providers.
If primary provider fails N times, switches to fallback automatically.
Periodically tests if primary recovered.
"""
import time
import asyncio
import logging

logger = logging.getLogger(__name__)

CLOSED = "closed"
OPEN = "open"
HALF_OPEN = "half_open"


class CircuitBreaker:
    """Wraps a primary + fallback provider pair with automatic failover."""

    def __init__(self, primary, fallback, name: str = "",
                 failure_threshold: int = 3, recovery_timeout: int = 60):
        self.primary = primary
        self.fallback = fallback
        self.name = name or primary.__class__.__name__
        self.state = CLOSED
        self.failures = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure_time = 0

    def _should_attempt_recovery(self) -> bool:
        return time.time() - self.last_failure_time > self.recovery_timeout

    def _on_success(self):
        if self.state == HALF_OPEN:
            logger.info(f"CircuitBreaker [{self.name}]: Primary recovered! Closing circuit.")
        self.state = CLOSED
        self.failures = 0

    def _on_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = OPEN
            logger.warning(f"CircuitBreaker [{self.name}]: OPEN — switching to fallback ({self.fallback.__class__.__name__})")

    async def call(self, method: str, *args, **kwargs):
        """Call a method on the provider with circuit breaker logic."""
        if self.state == OPEN:
            if self._should_attempt_recovery():
                self.state = HALF_OPEN
                logger.info(f"CircuitBreaker [{self.name}]: Testing primary recovery...")
            else:
                return await self._call_provider(self.fallback, method, *args, **kwargs)

        try:
            result = await self._call_provider(self.primary, method, *args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            logger.warning(f"CircuitBreaker [{self.name}]: Primary failed ({e}), using fallback")
            return await self._call_provider(self.fallback, method, *args, **kwargs)

    def call_sync(self, method: str, *args, **kwargs):
        """Synchronous version for thread pool usage."""
        if self.state == OPEN:
            if self._should_attempt_recovery():
                self.state = HALF_OPEN
            else:
                return self._call_provider_sync(self.fallback, method, *args, **kwargs)

        try:
            result = self._call_provider_sync(self.primary, method, *args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            logger.warning(f"CircuitBreaker [{self.name}]: Primary failed ({e}), using fallback")
            return self._call_provider_sync(self.fallback, method, *args, **kwargs)

    async def _call_provider(self, provider, method, *args, **kwargs):
        fn = getattr(provider, method)
        if asyncio.iscoroutinefunction(fn):
            return await fn(*args, **kwargs)
        return fn(*args, **kwargs)

    def _call_provider_sync(self, provider, method, *args, **kwargs):
        fn = getattr(provider, method)
        return fn(*args, **kwargs)

    @property
    def status(self) -> dict:
        return {
            "name": self.name,
            "state": self.state,
            "failures": self.failures,
            "primary": self.primary.__class__.__name__,
            "fallback": self.fallback.__class__.__name__,
        }
