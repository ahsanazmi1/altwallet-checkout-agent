"""Main client for the AltWallet Python SDK."""

import asyncio
import logging
import time
import uuid
from typing import Any

import httpx
import structlog

from .exceptions import (
    AltWalletError,
    APIError,
    AuthenticationError,
    ConfigurationError,
    NetworkError,
    RateLimitError,
    ValidationError,
)
from .models import (
    DecisionRequest,
    DecisionResponse,
    QuoteRequest,
    QuoteResponse,
    SDKConfig,
)


class AltWalletClient:
    """Client for interacting with the AltWallet Checkout Agent API."""

    def __init__(self, config: SDKConfig | dict[str, Any] | None = None):
        """Initialize the AltWallet client.

        Args:
            config: SDK configuration object or dictionary
        """
        if isinstance(config, dict):
            config = SDKConfig(**config)
        elif config is None:
            config = SDKConfig()

        self.config = config
        self._client: httpx.AsyncClient | None = None
        self._initialized = False

        # Setup logging
        self._setup_logging()
        self.logger = structlog.get_logger(__name__)

        # Performance tracking
        self._request_count = 0
        self._total_latency_ms = 0.0
        self._error_count = 0

        self.logger.info(
            "AltWallet client initialized",
            api_endpoint=self.config.api_endpoint,
            timeout=self.config.timeout,
        )

    def _setup_logging(self) -> None:
        """Setup structured logging for the SDK."""
        if not self.config.enable_logging:
            logging.getLogger("altwallet_sdk").setLevel(logging.CRITICAL)
            return

        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        # Set log level
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        logging.getLogger("altwallet_sdk").setLevel(log_level)

    async def initialize(self) -> None:
        """Initialize the HTTP client and validate configuration."""
        if self._initialized:
            return

        try:
            # Validate configuration
            self._validate_config()

            # Create HTTP client
            limits = httpx.Limits(
                max_keepalive_connections=self.config.connection_pool_size,
                max_connections=self.config.connection_pool_size * 2,
            )

            timeout = httpx.Timeout(self.config.timeout)

            self._client = httpx.AsyncClient(
                base_url=self.config.api_endpoint,
                timeout=timeout,
                limits=limits,
                headers=self._get_headers(),
            )

            # Test connection
            await self._test_connection()

            self._initialized = True
            self.logger.info("AltWallet client initialized successfully")

        except Exception as e:
            self.logger.error("Failed to initialize AltWallet client", error=str(e))
            raise ConfigurationError(f"Failed to initialize client: {e}")

    def _validate_config(self) -> None:
        """Validate client configuration."""
        if not self.config.api_endpoint:
            raise ConfigurationError("API endpoint is required")

        if not self.config.api_endpoint.startswith(("http://", "https://")):
            raise ConfigurationError("API endpoint must be a valid HTTP/HTTPS URL")

        if self.config.timeout <= 0:
            raise ConfigurationError("Timeout must be positive")

        if self.config.retry_attempts < 0:
            raise ConfigurationError("Retry attempts must be non-negative")

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers for requests."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "altwallet-python-sdk/1.0.0",
            "Accept": "application/json",
        }

        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        return headers

    async def _test_connection(self) -> None:
        """Test connection to the API."""
        try:
            response = await self._client.get("/health")
            if response.status_code != 200:
                raise NetworkError(
                    f"Health check failed with status {response.status_code}"
                )
        except httpx.RequestError as e:
            raise NetworkError(f"Failed to connect to API: {e}")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Make HTTP request with retry logic."""
        if not self._initialized:
            await self.initialize()

        if request_id is None:
            request_id = str(uuid.uuid4())

        start_time = time.time()
        last_exception = None

        for attempt in range(self.config.retry_attempts + 1):
            try:
                self.logger.info(
                    "Making API request",
                    method=method,
                    endpoint=endpoint,
                    attempt=attempt + 1,
                    request_id=request_id,
                )

                if method.upper() == "GET":
                    response = await self._client.get(endpoint)
                elif method.upper() == "POST":
                    response = await self._client.post(endpoint, json=data)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Update performance metrics
                latency_ms = (time.time() - start_time) * 1000
                self._request_count += 1
                self._total_latency_ms += latency_ms

                # Handle response
                if response.status_code == 200:
                    self.logger.info(
                        "API request successful",
                        status_code=response.status_code,
                        latency_ms=latency_ms,
                        request_id=request_id,
                    )
                    return response.json()

                elif response.status_code == 401:
                    self._error_count += 1
                    raise AuthenticationError("Authentication failed")

                elif response.status_code == 422:
                    self._error_count += 1
                    error_data = response.json()
                    raise ValidationError(
                        error_data.get("error_message", "Validation failed"),
                        error_code=error_data.get("error_code"),
                        request_id=request_id,
                        details=error_data.get("details"),
                    )

                elif response.status_code == 429:
                    self._error_count += 1
                    raise RateLimitError("Rate limit exceeded")

                else:
                    self._error_count += 1
                    error_data = response.json() if response.content else {}
                    raise APIError(
                        error_data.get(
                            "error_message", f"API error: {response.status_code}"
                        ),
                        status_code=response.status_code,
                        error_code=error_data.get("error_code"),
                        request_id=request_id,
                        details=error_data.get("details"),
                    )

            except (AuthenticationError, ValidationError, RateLimitError):
                # Don't retry these errors
                raise

            except Exception as e:
                last_exception = e
                if attempt < self.config.retry_attempts:
                    delay = self.config.retry_delay * (
                        2**attempt
                    )  # Exponential backoff
                    self.logger.warning(
                        "Request failed, retrying",
                        attempt=attempt + 1,
                        delay=delay,
                        error=str(e),
                        request_id=request_id,
                    )
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(
                        "All request attempts failed",
                        attempts=self.config.retry_attempts + 1,
                        error=str(e),
                        request_id=request_id,
                    )

        # If we get here, all retries failed
        if isinstance(last_exception, httpx.RequestError):
            raise NetworkError(f"Network error: {last_exception}")
        else:
            raise AltWalletError(f"Request failed: {last_exception}")

    async def quote(
        self,
        cart: dict[str, Any] | Any,
        customer: dict[str, Any] | Any,
        context: dict[str, Any] | Any,
        request_id: str | None = None,
    ) -> QuoteResponse:
        """Get card recommendations for a transaction.

        Args:
            cart: Shopping cart information
            customer: Customer information
            context: Transaction context
            request_id: Optional request identifier

        Returns:
            QuoteResponse with card recommendations

        Raises:
            ValidationError: If request data is invalid
            NetworkError: If network communication fails
            APIError: If API returns an error
        """
        try:
            # Create request object
            quote_request = QuoteRequest(
                cart=cart, customer=customer, context=context, request_id=request_id
            )

            # Make API request
            response_data = await self._make_request(
                "POST",
                "/v1/quote",
                data=quote_request.dict(),
                request_id=request_id or quote_request.request_id,
            )

            # Parse response
            return QuoteResponse(**response_data)

        except Exception as e:
            if isinstance(e, (ValidationError, NetworkError, APIError)):
                raise
            else:
                raise AltWalletError(f"Quote request failed: {e}")

    async def decision(self, request_id: str) -> DecisionResponse:
        """Get decision details for a previous request.

        Args:
            request_id: Request identifier to look up

        Returns:
            DecisionResponse with decision details

        Raises:
            ValidationError: If request_id is invalid
            NetworkError: If network communication fails
            APIError: If API returns an error
        """
        try:
            # Create request object
            DecisionRequest(request_id=request_id)

            # Make API request
            response_data = await self._make_request(
                "GET", f"/v1/decision/{request_id}", request_id=request_id
            )

            # Parse response
            return DecisionResponse(**response_data)

        except Exception as e:
            if isinstance(e, (ValidationError, NetworkError, APIError)):
                raise
            else:
                raise AltWalletError(f"Decision request failed: {e}")

    async def health_check(self) -> dict[str, Any]:
        """Check API health status.

        Returns:
            Health status information
        """
        try:
            response_data = await self._make_request("GET", "/health")
            return response_data
        except Exception as e:
            return {"status": "unhealthy", "error": str(e), "timestamp": time.time()}

    def get_metrics(self) -> dict[str, Any]:
        """Get client performance metrics.

        Returns:
            Performance metrics
        """
        return {
            "request_count": self._request_count,
            "error_count": self._error_count,
            "error_rate": (
                self._error_count / self._request_count
                if self._request_count > 0
                else 0
            ),
            "average_latency_ms": (
                self._total_latency_ms / self._request_count
                if self._request_count > 0
                else 0
            ),
            "initialized": self._initialized,
        }

    async def cleanup(self) -> None:
        """Cleanup client resources."""
        if self._client:
            await self._client.aclose()
            self._client = None

        self._initialized = False
        self.logger.info("AltWallet client cleaned up")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()


# Convenience functions for easy usage
async def create_client(
    config: SDKConfig | dict[str, Any] | None = None,
) -> AltWalletClient:
    """Create and initialize an AltWallet client.

    Args:
        config: SDK configuration

    Returns:
        Initialized AltWallet client
    """
    client = AltWalletClient(config)
    await client.initialize()
    return client


async def quote(
    cart: dict[str, Any] | Any,
    customer: dict[str, Any] | Any,
    context: dict[str, Any] | Any,
    config: SDKConfig | dict[str, Any] | None = None,
) -> QuoteResponse:
    """Convenience function for getting quotes.

    Args:
        cart: Shopping cart information
        customer: Customer information
        context: Transaction context
        config: Optional SDK configuration

    Returns:
        QuoteResponse with card recommendations
    """
    async with AltWalletClient(config) as client:
        return await client.quote(cart, customer, context)


async def decision(
    request_id: str, config: SDKConfig | dict[str, Any] | None = None
) -> DecisionResponse:
    """Convenience function for getting decisions.

    Args:
        request_id: Request identifier
        config: Optional SDK configuration

    Returns:
        DecisionResponse with decision details
    """
    async with AltWalletClient(config) as client:
        return await client.decision(request_id)
