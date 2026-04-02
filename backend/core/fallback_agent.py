"""
Intelligent Fallback Agent — Automatic Error Recovery System

This module implements a smart retry and fallback system that:
1. Detects failures (502, 503, timeouts, rate limits)
2. Applies exponential backoff with jitter
3. Switches to alternative strategies on persistent failures
4. Implements circuit breaker to avoid overloading failing services

Usage:
    from core.fallback_agent import FallbackAgent, FallbackStrategy
    
    agent = FallbackAgent(max_retries=3, base_delay=2)
    result = await agent.execute_with_fallback(
        primary_func=generate_with_gemini,
        fallback_func=generate_with_simple_prompt,
        context={"character": "Abraão"}
    )
"""

import asyncio
import time
import random
from typing import Callable, Any, Dict, List, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
from core.deps import logger


class ErrorType(Enum):
    """Classification of errors for intelligent retry decisions"""
    RATE_LIMIT = "rate_limit"  # 429, rate limit errors
    SERVER_ERROR = "server_error"  # 500, 502, 503, 504
    TIMEOUT = "timeout"  # Connection timeout
    AUTHENTICATION = "auth"  # 401, 403
    NOT_FOUND = "not_found"  # 404
    BAD_REQUEST = "bad_request"  # 400
    UNKNOWN = "unknown"


@dataclass
class FallbackStrategy:
    """Defines a fallback strategy with its parameters"""
    name: str
    func: Callable
    max_retries: int = 3
    base_delay: float = 2.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True


class CircuitBreaker:
    """Circuit breaker to avoid overwhelming failing services"""
    def __init__(self, failure_threshold: int = 5, timeout_duration: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout_duration = timeout_duration
        self.failures = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
    
    def record_success(self):
        """Reset circuit breaker on success"""
        self.failures = 0
        self.state = "closed"
        logger.info("CircuitBreaker: Reset to CLOSED (success)")
    
    def record_failure(self):
        """Record a failure and potentially open circuit"""
        self.failures += 1
        self.last_failure_time = datetime.now()
        
        if self.failures >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"CircuitBreaker: OPENED after {self.failures} failures")
    
    def can_attempt(self) -> bool:
        """Check if we can attempt the operation"""
        if self.state == "closed":
            return True
        
        if self.state == "open":
            # Check if timeout has passed
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.timeout_duration:
                    self.state = "half_open"
                    logger.info("CircuitBreaker: Transitioning to HALF_OPEN (timeout passed)")
                    return True
            return False
        
        # half_open state — allow one attempt
        return True


class FallbackAgent:
    """Intelligent agent that manages retries, backoff, and fallback strategies"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 2.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        circuit_breaker: Optional[CircuitBreaker] = None
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
    
    def classify_error(self, error: Exception) -> ErrorType:
        """Classify error type for intelligent retry decisions"""
        error_str = str(error).lower()
        
        if "429" in error_str or "rate limit" in error_str or "quota" in error_str:
            return ErrorType.RATE_LIMIT
        
        if any(code in error_str for code in ["500", "502", "503", "504", "gateway"]):
            return ErrorType.SERVER_ERROR
        
        if "timeout" in error_str or "timed out" in error_str:
            return ErrorType.TIMEOUT
        
        if "401" in error_str or "403" in error_str or "unauthorized" in error_str:
            return ErrorType.AUTHENTICATION
        
        if "404" in error_str:
            return ErrorType.NOT_FOUND
        
        if "400" in error_str or "bad request" in error_str:
            return ErrorType.BAD_REQUEST
        
        return ErrorType.UNKNOWN
    
    def is_retryable(self, error_type: ErrorType) -> bool:
        """Determine if error type is retryable"""
        retryable = {
            ErrorType.RATE_LIMIT,
            ErrorType.SERVER_ERROR,
            ErrorType.TIMEOUT,
            ErrorType.UNKNOWN
        }
        return error_type in retryable
    
    def calculate_delay(self, attempt: int, error_type: ErrorType) -> float:
        """Calculate delay with exponential backoff and jitter"""
        # Base exponential backoff
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        
        # Adjust based on error type
        if error_type == ErrorType.RATE_LIMIT:
            delay *= 2  # Longer wait for rate limits
        elif error_type == ErrorType.SERVER_ERROR:
            delay *= 1.5  # Moderate wait for server errors
        
        # Add jitter (randomization to avoid thundering herd)
        jitter = random.uniform(0, delay * 0.3)
        final_delay = delay + jitter
        
        return min(final_delay, self.max_delay)
    
    async def execute_with_retry(
        self,
        func: Callable,
        context: Dict[str, Any],
        strategy_name: str = "primary"
    ) -> Any:
        """Execute function with intelligent retry logic"""
        
        for attempt in range(self.max_retries):
            # Check circuit breaker
            if not self.circuit_breaker.can_attempt():
                raise Exception(
                    f"CircuitBreaker OPEN for {strategy_name} — service temporarily unavailable"
                )
            
            try:
                logger.info(
                    f"FallbackAgent: {strategy_name} attempt {attempt + 1}/{self.max_retries}"
                )
                
                # Execute function
                if asyncio.iscoroutinefunction(func):
                    result = await func(**context)
                else:
                    result = func(**context)
                
                # Success!
                self.circuit_breaker.record_success()
                logger.info(f"FallbackAgent: {strategy_name} SUCCESS on attempt {attempt + 1}")
                return result
            
            except Exception as e:
                error_type = self.classify_error(e)
                logger.warning(
                    f"FallbackAgent: {strategy_name} FAILED attempt {attempt + 1} "
                    f"(type: {error_type.value}): {str(e)[:200]}"
                )
                
                # Record failure in circuit breaker
                self.circuit_breaker.record_failure()
                
                # Check if retryable
                if not self.is_retryable(error_type):
                    logger.error(
                        f"FallbackAgent: {strategy_name} FATAL error (non-retryable: {error_type.value})"
                    )
                    raise
                
                # Last attempt?
                if attempt == self.max_retries - 1:
                    logger.error(
                        f"FallbackAgent: {strategy_name} EXHAUSTED all {self.max_retries} retries"
                    )
                    raise
                
                # Calculate delay and wait
                delay = self.calculate_delay(attempt, error_type)
                logger.info(
                    f"FallbackAgent: Waiting {delay:.1f}s before retry "
                    f"(error_type: {error_type.value})"
                )
                await asyncio.sleep(delay)
    
    async def execute_with_fallback(
        self,
        strategies: List[FallbackStrategy],
        context: Dict[str, Any]
    ) -> Any:
        """
        Execute with multiple fallback strategies.
        Tries each strategy in order until one succeeds.
        
        Args:
            strategies: List of FallbackStrategy objects (ordered by priority)
            context: Context dict passed to all strategy functions
        
        Returns:
            Result from the first successful strategy
        
        Raises:
            Exception if all strategies fail
        """
        errors = []
        
        for i, strategy in enumerate(strategies):
            try:
                logger.info(
                    f"FallbackAgent: Trying strategy {i + 1}/{len(strategies)}: {strategy.name}"
                )
                
                # Temporarily adjust retry params for this strategy
                original_retries = self.max_retries
                original_delay = self.base_delay
                original_max_delay = self.max_delay
                
                self.max_retries = strategy.max_retries
                self.base_delay = strategy.base_delay
                self.max_delay = strategy.max_delay
                
                try:
                    result = await self.execute_with_retry(
                        func=strategy.func,
                        context=context,
                        strategy_name=strategy.name
                    )
                    
                    logger.info(
                        f"FallbackAgent: Strategy '{strategy.name}' SUCCEEDED ✅"
                    )
                    return result
                
                finally:
                    # Restore original params
                    self.max_retries = original_retries
                    self.base_delay = original_delay
                    self.max_delay = original_max_delay
            
            except Exception as e:
                error_msg = f"Strategy '{strategy.name}' failed: {str(e)[:200]}"
                errors.append(error_msg)
                logger.warning(f"FallbackAgent: {error_msg}")
                
                # If this is the last strategy, raise
                if i == len(strategies) - 1:
                    logger.error(
                        f"FallbackAgent: ALL {len(strategies)} strategies FAILED ❌"
                    )
                    combined_error = "\n".join(errors)
                    raise Exception(f"All fallback strategies failed:\n{combined_error}")
                
                # Otherwise, continue to next strategy
                logger.info(
                    f"FallbackAgent: Falling back to next strategy ({i + 2}/{len(strategies)})"
                )


# ── Pre-configured fallback agents for common use cases ──

def create_image_generation_agent() -> FallbackAgent:
    """Create agent optimized for image generation (Gemini, DALL-E, etc.)"""
    return FallbackAgent(
        max_retries=3,
        base_delay=3.0,  # Longer initial delay for image gen
        max_delay=120.0,  # Up to 2 minutes for rate limits
        exponential_base=2.5,
        circuit_breaker=CircuitBreaker(failure_threshold=3, timeout_duration=180)
    )


def create_llm_agent() -> FallbackAgent:
    """Create agent optimized for LLM calls (Claude, GPT, etc.)"""
    return FallbackAgent(
        max_retries=3,
        base_delay=2.0,
        max_delay=60.0,
        exponential_base=2.0,
        circuit_breaker=CircuitBreaker(failure_threshold=5, timeout_duration=120)
    )


def create_api_agent() -> FallbackAgent:
    """Create agent optimized for general API calls"""
    return FallbackAgent(
        max_retries=3,
        base_delay=1.0,
        max_delay=30.0,
        exponential_base=2.0,
        circuit_breaker=CircuitBreaker(failure_threshold=5, timeout_duration=60)
    )
