# AltWallet Python SDK

The AltWallet Python SDK provides a simple and powerful way to integrate with the AltWallet Checkout Agent to get intelligent card recommendations and transaction scoring.

## Features

- 🚀 **Easy Integration**: Simple API for getting card recommendations
- 🔄 **Async Support**: Full async/await support for high-performance applications
- 🛡️ **Error Handling**: Comprehensive error handling with custom exceptions
- 📊 **Metrics**: Built-in performance metrics and monitoring
- 🔧 **Configurable**: Flexible configuration options for different environments
- 📝 **Type Safety**: Full type hints and Pydantic models for data validation
- 🔍 **Logging**: Structured logging with configurable levels

## Installation

```bash
pip install altwallet-sdk
```

## Quick Start

### Basic Usage

```python
import asyncio
from altwallet_sdk import AltWalletClient, SDKConfig

async def main():
    # Configure the SDK
    config = SDKConfig(
        api_endpoint="http://localhost:8000",
        api_key="your-api-key-here",  # Optional
        timeout=30
    )
    
    # Create and initialize client
    client = AltWalletClient(config)
    await client.initialize()
    
    # Prepare request data
    cart = {
        "items": [
            {
                "item_id": "item_123",
                "name": "Grocery Items",
                "unit_price": 45.99,
                "quantity": 1,
                "category": "groceries",
                "mcc": "5411"
            }
        ],
        "currency": "USD",
        "total_amount": 45.99
    }
    
    customer = {
        "customer_id": "cust_12345",
        "loyalty_tier": "SILVER",
        "preferred_cards": ["amex_gold", "chase_freedom"]
    }
    
    context = {
        "merchant_id": "grocery_store_123",
        "merchant_name": "Local Grocery Store",
        "device_type": "mobile",
        "ip_address": "192.168.1.100"
    }
    
    # Get card recommendations
    response = await client.quote(cart, customer, context)
    
    print(f"Received {len(response.recommendations)} recommendations")
    print(f"Transaction Score: {response.score:.2f}")
    
    # Display top recommendations
    for i, rec in enumerate(response.recommendations[:3], 1):
        print(f"{i}. {rec.card_name} ({rec.issuer})")
        print(f"   Approval: {rec.approval_probability:.1%}")
        print(f"   Rewards: {rec.expected_rewards:.1%}")
    
    # Get decision details
    decision = await client.decision(response.request_id)
    print(f"Decision: {decision.decision} (Confidence: {decision.confidence:.1%})")
    
    # Cleanup
    await client.cleanup()

# Run the example
asyncio.run(main())
```

### Convenience Functions

```python
from altwallet_sdk import quote, decision

# Simple quote request
response = await quote(cart, customer, context)

# Get decision details
decision = await decision(response.request_id)
```

### Context Manager

```python
from altwallet_sdk import AltWalletClient

async with AltWalletClient(config) as client:
    response = await client.quote(cart, customer, context)
    decision = await client.decision(response.request_id)
```

## API Reference

### AltWalletClient

The main client class for interacting with the AltWallet API.

#### Constructor

```python
client = AltWalletClient(config: SDKConfig)
```

#### Methods

##### `initialize() -> None`

Initialize the client and test the connection to the API.

```python
await client.initialize()
```

##### `quote(cart, customer, context, request_id=None) -> QuoteResponse`

Get card recommendations for a transaction.

**Parameters:**
- `cart`: Shopping cart information
- `customer`: Customer information  
- `context`: Transaction context
- `request_id`: Optional request identifier

**Returns:** `QuoteResponse` with card recommendations

##### `decision(request_id) -> DecisionResponse`

Get decision details for a previous request.

**Parameters:**
- `request_id`: Request identifier to look up

**Returns:** `DecisionResponse` with decision details

##### `health_check() -> Dict[str, Any]`

Check API health status.

**Returns:** Health status information

##### `get_metrics() -> Dict[str, Any]`

Get client performance metrics.

**Returns:** Performance metrics including request count, error rate, and latency

##### `cleanup() -> None`

Cleanup client resources.

```python
await client.cleanup()
```

### Data Models

#### Cart

```python
{
    "items": [
        {
            "item_id": "string",
            "name": "string", 
            "unit_price": 0.0,
            "quantity": 1,
            "category": "string",  # Optional
            "mcc": "string"        # Optional
        }
    ],
    "currency": "USD",
    "total_amount": 0.0,      # Optional
    "tax_amount": 0.0,        # Optional
    "shipping_amount": 0.0    # Optional
}
```

#### Customer

```python
{
    "customer_id": "string",
    "loyalty_tier": "string",           # Optional
    "preferred_cards": ["string"],      # Optional
    "risk_profile": "string",           # Optional
    "location": {                       # Optional
        "city": "string",
        "state": "string", 
        "country": "string"
    }
}
```

#### Context

```python
{
    "merchant_id": "string",
    "merchant_name": "string",          # Optional
    "device_type": "string",            # Optional
    "user_agent": "string",             # Optional
    "ip_address": "string",             # Optional
    "session_id": "string",             # Optional
    "referrer": "string",               # Optional
    "campaign_id": "string"             # Optional
}
```

#### QuoteResponse

```python
{
    "request_id": "string",
    "transaction_id": "string",
    "score": 0.0,
    "status": "string",
    "recommendations": [
        {
            "card_id": "string",
            "card_name": "string",
            "issuer": "string",
            "rank": 1,
            "approval_probability": 0.0,
            "expected_rewards": 0.0,
            "utility_score": 0.0,
            "reasoning": "string",      # Optional
            "features": {}              # Optional
        }
    ],
    "processing_time_ms": 0,
    "timestamp": "2024-01-15T10:30:00Z",
    "metadata": {}                      # Optional
}
```

#### DecisionResponse

```python
{
    "request_id": "string",
    "transaction_id": "string", 
    "decision": "string",
    "confidence": 0.0,
    "reasoning": "string",
    "risk_factors": ["string"],         # Optional
    "timestamp": "2024-01-15T10:30:00Z",
    "metadata": {}                      # Optional
}
```

### Configuration

#### SDKConfig

```python
config = SDKConfig(
    api_endpoint="http://localhost:8000",    # Required
    api_key="your-api-key",                  # Optional
    timeout=30,                              # Optional
    retry_attempts=3,                        # Optional
    retry_delay=1.0,                         # Optional
    connection_pool_size=10,                 # Optional
    keep_alive=True,                         # Optional
    log_level="INFO",                        # Optional
    enable_logging=True                      # Optional
)
```

### Error Handling

The SDK provides custom exceptions for different error types:

```python
from altwallet_sdk.exceptions import (
    AltWalletError,
    ConfigurationError,
    NetworkError,
    AuthenticationError,
    ValidationError,
    RateLimitError,
    APIError
)

try:
    response = await client.quote(cart, customer, context)
except ValidationError as e:
    print(f"Validation error: {e.message}")
    print(f"Details: {e.details}")
except NetworkError as e:
    print(f"Network error: {e.message}")
except APIError as e:
    print(f"API error: {e.message} (Status: {e.status_code})")
except AltWalletError as e:
    print(f"AltWallet error: {e.message}")
```

## Advanced Usage

### Batch Processing

```python
import asyncio

async def process_multiple_requests():
    client = AltWalletClient(config)
    await client.initialize()
    
    try:
        # Create multiple requests
        requests = [
            (cart1, customer1, context1),
            (cart2, customer2, context2),
            (cart3, customer3, context3)
        ]
        
        # Process concurrently
        tasks = [
            client.quote(cart, customer, context)
            for cart, customer, context in requests
        ]
        
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                print(f"Request {i} failed: {response}")
            else:
                print(f"Request {i} success: {response.score}")
                
    finally:
        await client.cleanup()
```

### Custom Retry Logic

```python
config = SDKConfig(
    retry_attempts=5,
    retry_delay=2.0,  # Exponential backoff starts at 2 seconds
    timeout=60
)
```

### Logging Configuration

```python
config = SDKConfig(
    log_level="DEBUG",      # DEBUG, INFO, WARN, ERROR
    enable_logging=True
)
```

### Performance Monitoring

```python
# Get metrics after processing requests
metrics = client.get_metrics()
print(f"Requests: {metrics['request_count']}")
print(f"Error Rate: {metrics['error_rate']:.1%}")
print(f"Avg Latency: {metrics['average_latency_ms']:.1f}ms")
```

## Examples

See the `examples/` directory for complete working examples:

- `basic_usage.py` - Simple integration example
- `advanced_usage.py` - Advanced features and error handling

## Requirements

- Python 3.8+
- httpx >= 0.25.0
- pydantic >= 2.0.0
- structlog >= 23.0.0

## License

MIT License - see LICENSE file for details.

## Support

- Documentation: [GitHub Repository](https://github.com/altwallet/checkout-agent)
- Issues: [GitHub Issues](https://github.com/altwallet/checkout-agent/issues)
- Email: team@altwallet.com
