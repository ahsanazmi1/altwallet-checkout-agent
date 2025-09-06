# AltWallet Python SDK

A Python SDK for integrating with the AltWallet Checkout Agent to get intelligent card recommendations and transaction scoring.

## Installation

```bash
pip install altwallet-sdk
```

## Quick Start

```python
import asyncio
from altwallet_sdk import AltWalletClient, SDKConfig, Cart, Customer, Context

async def main():
    # Configure the SDK
    config = SDKConfig(
        api_endpoint="http://localhost:8000",
        api_key="your-api-key-here",  # Optional
        timeout=30,
        retry_attempts=3,
        log_level="INFO",
    )

    # Create client
    client = AltWalletClient(config)

    # Initialize the client
    await client.initialize()

    # Prepare request data
    cart = Cart(
        items=[
            {
                "item_id": "item_123",
                "name": "Premium Headphones",
                "price": 299.99,
                "quantity": 1,
                "category": "electronics"
            }
        ],
        total_amount=299.99,
        currency="USD"
    )

    customer = Customer(
        customer_id="cust_456",
        email="customer@example.com",
        risk_score=0.2
    )

    context = Context(
        merchant_id="merchant_789",
        transaction_id="txn_101",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0..."
    )

    # Get quote
    quote_response = await client.quote(cart, customer, context)
    print(f"Recommendations: {quote_response.recommendations}")

    # Get decision
    decision_response = await client.decision(quote_response.request_id)
    print(f"Decision: {decision_response.decision}")

if __name__ == "__main__":
    asyncio.run(main())
```

## API Reference

### AltWalletClient

The main client class for interacting with the AltWallet Checkout Agent.

#### Methods

- `initialize()` - Initialize the client
- `quote(cart, customer, context)` - Get card recommendations
- `decision(request_id)` - Get decision for a specific request
- `health_check()` - Check client health status

### Data Models

- `SDKConfig` - Configuration for the SDK
- `Cart` - Shopping cart information
- `Customer` - Customer information
- `Context` - Transaction context
- `QuoteResponse` - Response from quote request
- `DecisionResponse` - Response from decision request

## Examples

See the `examples/` directory for more detailed usage examples:

- `basic_usage.py` - Basic integration example
- `advanced_usage.py` - Advanced usage with error handling and retries

## Error Handling

The SDK provides custom exceptions for different error scenarios:

- `AltWalletError` - Base exception class
- `ConfigurationError` - Configuration-related errors
- `NetworkError` - Network connectivity issues
- `AuthenticationError` - Authentication failures
- `ValidationError` - Input validation errors
- `RateLimitError` - Rate limiting errors
- `APIError` - General API errors

## Configuration

The SDK can be configured using environment variables or the `SDKConfig` class:

```python
config = SDKConfig(
    api_endpoint=os.getenv("ALTWALLET_API_ENDPOINT", "http://localhost:8000"),
    api_key=os.getenv("ALTWALLET_API_KEY"),
    timeout=int(os.getenv("ALTWALLET_TIMEOUT", "30")),
    retry_attempts=int(os.getenv("ALTWALLET_RETRY_ATTEMPTS", "3")),
    log_level=os.getenv("ALTWALLET_LOG_LEVEL", "INFO"),
)
```

## Logging

The SDK uses structured logging with trace IDs. Set `LOG_SILENT=1` to suppress logs during testing.

## License

MIT License