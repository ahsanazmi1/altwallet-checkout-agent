"""Inline deployment module for direct integration into merchant applications."""

import asyncio
import time
from typing import Any, Dict, Optional, Union
from contextlib import asynccontextmanager

import structlog
from pydantic import BaseModel

from ..config import DeploymentConfig, InlineConfig, is_inline_mode
from src.altwallet_agent.core import CheckoutAgent
from src.altwallet_agent.models import CheckoutRequest, CheckoutResponse, Context


class InlineCheckoutClient:
    """Inline checkout client for direct integration into merchant applications.
    
    This client provides a lightweight interface for integrating the AltWallet
    Checkout Agent directly into merchant applications without requiring
    separate service deployment.
    """
    
    def __init__(self, config: Optional[InlineConfig] = None):
        """Initialize the inline checkout client.
        
        Args:
            config: Inline-specific configuration
        """
        self.config = config or InlineConfig()
        self.logger = structlog.get_logger(__name__)
        self._agent: Optional[CheckoutAgent] = None
        self._initialized = False
        
        # Performance tracking
        self._request_count = 0
        self._total_latency_ms = 0.0
        self._error_count = 0
        
        # Circuit breaker state
        self._circuit_breaker_failures = 0
        self._circuit_breaker_last_failure = 0.0
        self._circuit_breaker_state = "closed"  # closed, open, half-open
        
        self.logger.info(
            "Inline checkout client initialized",
            integration_method=self.config.integration_method,
            cache_enabled=self.config.cache_enabled,
            circuit_breaker_enabled=self.config.circuit_breaker_enabled
        )
    
    async def initialize(self) -> None:
        """Initialize the checkout agent."""
        if self._initialized:
            return
        
        try:
            self._agent = CheckoutAgent()
            self._initialized = True
            self.logger.info("Checkout agent initialized successfully")
        except Exception as e:
            self.logger.error("Failed to initialize checkout agent", error=str(e))
            raise
    
    async def process_checkout(
        self,
        request: Union[CheckoutRequest, Dict[str, Any]],
        context: Optional[Context] = None
    ) -> CheckoutResponse:
        """Process a checkout request.
        
        Args:
            request: Checkout request data
            context: Optional transaction context
            
        Returns:
            CheckoutResponse with recommendations
            
        Raises:
            RuntimeError: If agent is not initialized
            CircuitBreakerOpenError: If circuit breaker is open
        """
        if not self._initialized:
            await self.initialize()
        
        # Check circuit breaker
        if self._is_circuit_breaker_open():
            raise CircuitBreakerOpenError("Circuit breaker is open")
        
        start_time = time.time()
        self._request_count += 1
        
        try:
            # Convert dict to CheckoutRequest if needed
            if isinstance(request, dict):
                request = CheckoutRequest(**request)
            
            # Process the checkout
            response = await self._process_with_retry(request, context)
            
            # Update performance metrics
            latency_ms = (time.time() - start_time) * 1000
            self._total_latency_ms += latency_ms
            
            # Reset circuit breaker on success
            if self._circuit_breaker_state == "half-open":
                self._circuit_breaker_state = "closed"
                self._circuit_breaker_failures = 0
            
            self.logger.info(
                "Checkout processed successfully",
                request_id=response.transaction_id,
                latency_ms=latency_ms,
                recommendations_count=len(response.recommendations)
            )
            
            return response
            
        except Exception as e:
            self._error_count += 1
            self._handle_circuit_breaker_failure()
            
            self.logger.error(
                "Checkout processing failed",
                error=str(e),
                latency_ms=(time.time() - start_time) * 1000
            )
            raise
    
    async def _process_with_retry(
        self,
        request: CheckoutRequest,
        context: Optional[Context] = None
    ) -> CheckoutResponse:
        """Process checkout with retry logic."""
        last_exception = None
        
        for attempt in range(self.config.retry_attempts + 1):
            try:
                if context:
                    # Use context-based processing
                    return await self._agent.process_with_context(context)
                else:
                    # Use direct request processing
                    return await self._agent.process_checkout(request)
                    
            except Exception as e:
                last_exception = e
                if attempt < self.config.retry_attempts:
                    delay = self.config.retry_delay * (2 ** attempt)  # Exponential backoff
                    self.logger.warning(
                        "Checkout attempt failed, retrying",
                        attempt=attempt + 1,
                        delay=delay,
                        error=str(e)
                    )
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(
                        "All checkout attempts failed",
                        attempts=self.config.retry_attempts + 1,
                        error=str(e)
                    )
        
        raise last_exception
    
    def _is_circuit_breaker_open(self) -> bool:
        """Check if circuit breaker is open."""
        if not self.config.circuit_breaker_enabled:
            return False
        
        if self._circuit_breaker_state == "open":
            # Check if we should transition to half-open
            if time.time() - self._circuit_breaker_last_failure > 60:  # 1 minute timeout
                self._circuit_breaker_state = "half-open"
                self.logger.info("Circuit breaker transitioning to half-open")
                return False
            return True
        
        return False
    
    def _handle_circuit_breaker_failure(self) -> None:
        """Handle circuit breaker failure."""
        if not self.config.circuit_breaker_enabled:
            return
        
        self._circuit_breaker_failures += 1
        self._circuit_breaker_last_failure = time.time()
        
        if self._circuit_breaker_failures >= self.config.circuit_breaker_threshold:
            self._circuit_breaker_state = "open"
            self.logger.warning(
                "Circuit breaker opened",
                failures=self._circuit_breaker_failures,
                threshold=self.config.circuit_breaker_threshold
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        try:
            if not self._initialized:
                await self.initialize()
            
            # Basic health check
            health_status = {
                "status": "healthy",
                "initialized": self._initialized,
                "request_count": self._request_count,
                "error_count": self._error_count,
                "circuit_breaker_state": self._circuit_breaker_state,
                "average_latency_ms": (
                    self._total_latency_ms / self._request_count
                    if self._request_count > 0 else 0
                )
            }
            
            return health_status
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "initialized": self._initialized
            }
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        self._agent = None
        self._initialized = False
        self.logger.info("Inline checkout client cleaned up")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return {
            "request_count": self._request_count,
            "error_count": self._error_count,
            "error_rate": (
                self._error_count / self._request_count
                if self._request_count > 0 else 0
            ),
            "average_latency_ms": (
                self._total_latency_ms / self._request_count
                if self._request_count > 0 else 0
            ),
            "circuit_breaker_state": self._circuit_breaker_state,
            "circuit_breaker_failures": self._circuit_breaker_failures
        }


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


# Global client instance for easy access
_inline_client: Optional[InlineCheckoutClient] = None


async def get_inline_client() -> InlineCheckoutClient:
    """Get or create the global inline client instance."""
    global _inline_client
    
    if _inline_client is None:
        _inline_client = InlineCheckoutClient()
        await _inline_client.initialize()
    
    return _inline_client


async def process_checkout_inline(
    request: Union[CheckoutRequest, Dict[str, Any]],
    context: Optional[Context] = None
) -> CheckoutResponse:
    """Convenience function for processing checkout inline.
    
    Args:
        request: Checkout request data
        context: Optional transaction context
        
    Returns:
        CheckoutResponse with recommendations
    """
    client = await get_inline_client()
    return await client.process_checkout(request, context)


@asynccontextmanager
async def inline_checkout_client(config: Optional[InlineConfig] = None):
    """Context manager for inline checkout client."""
    client = InlineCheckoutClient(config)
    try:
        await client.initialize()
        yield client
    finally:
        await client.cleanup()


# Synchronous wrapper for non-async environments
class SyncInlineCheckoutClient:
    """Synchronous wrapper for inline checkout client."""
    
    def __init__(self, config: Optional[InlineConfig] = None):
        self._client = InlineCheckoutClient(config)
        self._loop = None
    
    def _get_loop(self):
        """Get or create event loop."""
        if self._loop is None:
            try:
                self._loop = asyncio.get_event_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        return self._loop
    
    def initialize(self) -> None:
        """Initialize the client synchronously."""
        loop = self._get_loop()
        loop.run_until_complete(self._client.initialize())
    
    def process_checkout(
        self,
        request: Union[CheckoutRequest, Dict[str, Any]],
        context: Optional[Context] = None
    ) -> CheckoutResponse:
        """Process checkout synchronously."""
        loop = self._get_loop()
        return loop.run_until_complete(
            self._client.process_checkout(request, context)
        )
    
    def health_check(self) -> Dict[str, Any]:
        """Health check synchronously."""
        loop = self._get_loop()
        return loop.run_until_complete(self._client.health_check())
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics synchronously."""
        return self._client.get_metrics()
    
    def cleanup(self) -> None:
        """Cleanup synchronously."""
        loop = self._get_loop()
        loop.run_until_complete(self._client.cleanup())
