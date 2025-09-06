# AltWallet SDKs

This directory contains SDK packages for integrating with the AltWallet Checkout Agent. Choose the SDK that matches your development environment.

## Available SDKs

### 🐍 Python SDK
- **Location**: `python/`
- **Language**: Python 3.8+
- **Features**: Async/await support, Pydantic models, comprehensive error handling
- **Installation**: `pip install altwallet-sdk`

### 🟢 Node.js SDK  
- **Location**: `nodejs/`
- **Language**: Node.js 16.0+ / TypeScript
- **Features**: Async/await support, TypeScript definitions, Express.js integration
- **Installation**: `npm install altwallet-sdk`

## Common API Interface

Both SDKs provide the same core interface for consistency:

### Core Methods

#### `initialize(config)`
Initialize the SDK client with configuration.

```python
# Python
await client.initialize()
```

```javascript
// Node.js
await client.initialize();
```

#### `quote(cart, customer, context)`
Get card recommendations for a transaction.

```python
# Python
response = await client.quote(cart, customer, context)
```

```javascript
// Node.js
const response = await client.quote(cart, customer, context);
```

#### `decision(request_id)`
Get decision details for a previous request.

```python
# Python
decision = await client.decision(request_id)
```

```javascript
// Node.js
const decision = await client.decision(requestId);
```

### Consistent Response Schema

Both SDKs return responses that match the OpenAPI specification:

#### QuoteResponse
```json
{
  "request_id": "req_12345",
  "transaction_id": "txn_67890", 
  "score": 0.85,
  "status": "completed",
  "recommendations": [
    {
      "card_id": "amex_gold",
      "card_name": "American Express Gold",
      "issuer": "American Express",
      "rank": 1,
      "approval_probability": 0.92,
      "expected_rewards": 0.04,
      "utility_score": 0.88,
      "reasoning": "High rewards for grocery purchases"
    }
  ],
  "processing_time_ms": 45,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### DecisionResponse
```json
{
  "request_id": "req_12345",
  "transaction_id": "txn_67890",
  "decision": "approve", 
  "confidence": 0.92,
  "reasoning": "Low risk transaction with good customer profile",
  "risk_factors": [],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Quick Start Examples

### Python Quick Start

```python
import asyncio
from altwallet_sdk import AltWalletClient

async def main():
    client = AltWalletClient({
        "api_endpoint": "http://localhost:8000"
    })
    await client.initialize()
    
    response = await client.quote(
        cart={"items": [{"item_id": "item_1", "name": "Product", "unit_price": 100, "quantity": 1}]},
        customer={"customer_id": "cust_123"},
        context={"merchant_id": "merchant_456"}
    )
    
    print(f"Best card: {response.recommendations[0].card_name}")
    await client.cleanup()

asyncio.run(main())
```

### Node.js Quick Start

```javascript
const { AltWalletClient } = require('altwallet-sdk');

async function main() {
    const client = new AltWalletClient({
        apiEndpoint: 'http://localhost:8000'
    });
    await client.initialize();
    
    const response = await client.quote(
        { items: [{ itemId: 'item_1', name: 'Product', unitPrice: 100, quantity: 1 }] },
        { customerId: 'cust_123' },
        { merchantId: 'merchant_456' }
    );
    
    console.log(`Best card: ${response.recommendations[0].cardName}`);
    await client.cleanup();
}

main().catch(console.error);
```

## Configuration

Both SDKs support similar configuration options:

### Common Configuration Options

| Option | Python | Node.js | Description |
|--------|--------|---------|-------------|
| API Endpoint | `api_endpoint` | `apiEndpoint` | AltWallet API URL |
| API Key | `api_key` | `apiKey` | Authentication key |
| Timeout | `timeout` | `timeout` | Request timeout (seconds) |
| Retry Attempts | `retry_attempts` | `retryAttempts` | Number of retries |
| Retry Delay | `retry_delay` | `retryDelay` | Delay between retries |
| Log Level | `log_level` | `logLevel` | Logging level |
| Connection Pool | `connection_pool_size` | `connectionPoolSize` | HTTP connection pool size |

### Environment Variables

Both SDKs support configuration via environment variables:

```bash
export ALTWALLET_API_ENDPOINT="http://localhost:8000"
export ALTWALLET_API_KEY="your-api-key"
export ALTWALLET_TIMEOUT="30"
export ALTWALLET_LOG_LEVEL="INFO"
```

## Error Handling

Both SDKs provide consistent error handling:

### Error Types

- **ConfigurationError**: Invalid SDK configuration
- **NetworkError**: Network communication failures
- **AuthenticationError**: Authentication failures
- **ValidationError**: Request validation errors
- **RateLimitError**: Rate limit exceeded
- **APIError**: API-specific errors

### Error Handling Example

```python
# Python
try:
    response = await client.quote(cart, customer, context)
except ValidationError as e:
    print(f"Validation error: {e.message}")
except NetworkError as e:
    print(f"Network error: {e.message}")
```

```javascript
// Node.js
try {
    const response = await client.quote(cart, customer, context);
} catch (error) {
    if (error instanceof ValidationError) {
        console.log(`Validation error: ${error.message}`);
    } else if (error instanceof NetworkError) {
        console.log(`Network error: ${error.message}`);
    }
}
```

## Performance Features

Both SDKs include performance monitoring and optimization:

### Metrics
- Request count and error rate
- Average latency tracking
- Connection pool management
- Automatic retry with exponential backoff

### Logging
- Structured JSON logging
- Configurable log levels
- Request/response tracing
- Performance metrics logging

## Integration Examples

### Web Application Integration

#### Python (FastAPI)
```python
from fastapi import FastAPI
from altwallet_sdk import AltWalletClient

app = FastAPI()
client = AltWalletClient({"api_endpoint": "http://localhost:8000"})

@app.on_event("startup")
async def startup():
    await client.initialize()

@app.post("/checkout")
async def checkout(request: CheckoutRequest):
    response = await client.quote(request.cart, request.customer, request.context)
    return response
```

#### Node.js (Express)
```javascript
const express = require('express');
const { AltWalletClient } = require('altwallet-sdk');

const app = express();
const client = new AltWalletClient({ apiEndpoint: 'http://localhost:8000' });

app.use(express.json());

app.post('/checkout', async (req, res) => {
    try {
        const response = await client.quote(req.body.cart, req.body.customer, req.body.context);
        res.json(response);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});
```

## Testing

Both SDKs include comprehensive test suites:

### Python Testing
```bash
cd python/
pip install -e ".[dev]"
pytest
```

### Node.js Testing
```bash
cd nodejs/
npm install
npm test
```

## Documentation

- **Python SDK**: [python/README.md](python/README.md)
- **Node.js SDK**: [nodejs/README.md](nodejs/README.md)
- **API Reference**: [OpenAPI Specification](../../openapi/)

## Support

- **Issues**: [GitHub Issues](https://github.com/altwallet/checkout-agent/issues)
- **Documentation**: [GitHub Repository](https://github.com/altwallet/checkout-agent)
- **Email**: team@altwallet.com

## License

MIT License - see LICENSE file for details.
