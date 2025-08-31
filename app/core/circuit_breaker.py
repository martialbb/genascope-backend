"""
Circuit Breaker Pattern Implementation

Implements the circuit breaker pattern to handle external service failures gracefully.
"""
import time
import asyncio
import logging
from enum import Enum
from typing import Callable, Any, Optional
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, requests fail immediately
    HALF_OPEN = "half_open"  # Testing if service has recovered


class CircuitBreakerOpenException(Exception):
    """Raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Circuit breaker implementation for handling service failures.
    
    The circuit breaker has three states:
    - CLOSED: Normal operation, all requests go through
    - OPEN: Service is down, requests fail immediately  
    - HALF_OPEN: Testing if service has recovered
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time in seconds before attempting recovery
            expected_exception: Exception type that triggers circuit breaker
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self._failure_count = 0
        self._last_failure_time = None
        self._state = CircuitState.CLOSED
        
    @property
    def state(self) -> CircuitState:
        """Get current circuit breaker state."""
        return self._state
    
    @property
    def failure_count(self) -> int:
        """Get current failure count."""
        return self._failure_count
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self._last_failure_time is None:
            return False
        return time.time() - self._last_failure_time >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful request."""
        self._failure_count = 0
        self._last_failure_time = None
        self._state = CircuitState.CLOSED
        logger.info("Circuit breaker reset to CLOSED state")
    
    def _on_failure(self):
        """Handle failed request."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker opened after {self._failure_count} failures"
            )
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenException: When circuit is open
            HTTPException: When service is unavailable
        """
        # Check if circuit should transition from OPEN to HALF_OPEN
        if self._state == CircuitState.OPEN and self._should_attempt_reset():
            self._state = CircuitState.HALF_OPEN
            logger.info("Circuit breaker transitioned to HALF_OPEN state")
        
        # Fail fast if circuit is open
        if self._state == CircuitState.OPEN:
            logger.warning("Circuit breaker is OPEN, failing fast")
            raise HTTPException(
                status_code=503,
                detail="Service temporarily unavailable. Please try again later."
            )
        
        try:
            # Attempt to call the function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Success - reset circuit breaker if it was half-open
            if self._state == CircuitState.HALF_OPEN:
                self._on_success()
            
            return result
            
        except self.expected_exception as e:
            logger.error(f"Circuit breaker caught expected exception: {e}")
            self._on_failure()
            
            # Re-raise the exception for the caller to handle
            raise e
        except Exception as e:
            # Unexpected exceptions don't trigger circuit breaker
            logger.error(f"Circuit breaker caught unexpected exception: {e}")
            raise e


class AIServiceCircuitBreaker(CircuitBreaker):
    """Specialized circuit breaker for AI services."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60
    ):
        # Common AI service exceptions that should trigger circuit breaker
        import openai
        expected_exceptions = (
            openai.error.ServiceUnavailableError,
            openai.error.APIError,
            openai.error.RateLimitError,
            ConnectionError,
            TimeoutError,
        )
        
        super().__init__(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exceptions
        )
