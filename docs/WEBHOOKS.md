# Webhook Module

The Webhook Module provides comprehensive support for downstream event notifications with async event emission, retry logic, exponential backoff, and signed payloads for verification.

## Overview

The webhook module enables the AltWallet Checkout Agent to send real-time notifications to external systems about important events such as:

- **Authentication Results**: Transaction decisions and scoring outcomes
- **Settlements**: Payment settlement status and details
- **Chargebacks**: Chargeback notifications and reasons
- **Loyalty Events**: Points changes and tier updates

## Key Features

### ✅ **Async Event Emission**
- Non-blocking event delivery using asyncio
- High-performance HTTP client with aiohttp
- Configurable timeouts and connection pooling

### ✅ **Retry Logic with Exponential Backoff**
- Automatic retry on delivery failures
- Configurable retry attempts and delays
- Exponential backoff with maximum delay caps
- Smart retry scheduling

### ✅ **Signed Payloads**
- HMAC-SHA256 signature verification
- Webhook secret-based authentication
- Tamper-proof payload integrity
- Standard webhook signature headers

### ✅ **Event Type Filtering**
- Per-webhook event type configuration
- Support for all events or specific types
- Flexible webhook endpoint management

## Architecture

### Core Components

1. **WebhookManager**: Manages webhook configurations and delivery
2. **WebhookEventEmitter**: High-level API for emitting events
3. **WebhookConfig**: Configuration for individual webhook endpoints
4. **WebhookPayload**: Standardized event payload structure
5. **WebhookDelivery**: Delivery attempt tracking and history

### Event Flow

```
Event Source → WebhookEventEmitter → WebhookManager → HTTP Delivery → Retry Logic
     ↓              ↓                    ↓              ↓            ↓
  Business      Event Creation      Configuration    HTTP POST    Exponential
   Logic         & Routing         & Filtering      with Headers   Backoff
```

## Supported Event Types

### `auth_result`
Authentication and authorization results from transaction processing.

**Payload Structure:**
```json
{
  "event_type": "auth_result",
  "event_id": "uuid-12345",
  "timestamp": 1640995200.0,
  "data": {
    "transaction_id": "txn_12345",
    "decision": "APPROVE",
    "score": 85.0
  },
  "metadata": {
    "merchant_id": "merchant_123",
    "customer_id": "customer_456"
  }
}
```

### `settlement`
Payment settlement status and details.

**Payload Structure:**
```json
{
  "event_type": "settlement",
  "event_id": "uuid-67890",
  "timestamp": 1640995200.0,
  "data": {
    "transaction_id": "txn_12345",
    "amount": 150.00,
    "currency": "USD",
    "status": "completed"
  },
  "metadata": {
    "settlement_id": "settlement_789",
    "processing_time_ms": 1250
  }
}
```

### `chargeback`
Chargeback notifications and reasons.

**Payload Structure:**
```json
{
  "event_type": "chargeback",
  "event_id": "uuid-11111",
  "timestamp": 1640995200.0,
  "data": {
    "transaction_id": "txn_12345",
    "chargeback_id": "cb_12345",
    "reason": "fraud_suspected",
    "amount": 150.00
  },
  "metadata": {
    "chargeback_date": "2025-01-15",
    "reason_code": "10.1"
  }
}
```

### `loyalty_event`
Loyalty program events and point changes.

**Payload Structure:**
```json
{
  "event_type": "loyalty_event",
  "event_id": "uuid-22222",
  "timestamp": 1640995200.0,
  "data": {
    "customer_id": "customer_456",
    "event_type": "points_earned",
    "points_change": 15
  },
  "metadata": {
    "transaction_amount": 150.00,
    "points_rate": 0.1,
    "tier": "SILVER"
  }
}
```

## Configuration

### Webhook Configuration

```python
from altwallet_agent.webhooks import WebhookConfig, WebhookEventType

# Auth-only webhook
auth_webhook = WebhookConfig(
    url="https://your-domain.com/webhooks/auth",
    secret="your_webhook_secret_here",
    event_types=[WebhookEventType.AUTH_RESULT],
    timeout=30,
    max_retries=3,
    retry_delay_base=1.0,
    retry_delay_max=60.0,
    enabled=True
)

# General webhook for all events
general_webhook = WebhookConfig(
    url="https://your-domain.com/webhooks/general",
    secret="your_general_secret_here",
    event_types=[],  # Empty list = all event types
    timeout=45,
    max_retries=5,
    retry_delay_base=2.0,
    retry_delay_max=120.0
)
```

### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | str | Required | Webhook endpoint URL |
| `secret` | str | Required | Secret for payload signing |
| `event_types` | List[WebhookEventType] | [] | Event types to receive (empty = all) |
| `timeout` | int | 30 | HTTP request timeout in seconds |
| `max_retries` | int | 3 | Maximum retry attempts |
| `retry_delay_base` | float | 1.0 | Base delay for exponential backoff |
| `retry_delay_max` | float | 60.0 | Maximum retry delay in seconds |
| `enabled` | bool | True | Whether webhook is active |

## Usage

### Basic Setup

```python
import asyncio
from altwallet_agent.webhooks import (
    get_webhook_manager,
    get_webhook_emitter,
    WebhookConfig,
    WebhookEventType
)

async def setup_webhooks():
    # Get webhook manager
    webhook_manager = await get_webhook_manager()
    
    # Add webhook configuration
    config = WebhookConfig(
        url="https://your-domain.com/webhook",
        secret="your_secret_here"
    )
    await webhook_manager.add_webhook("my_webhook", config)
    
    # Get event emitter
    emitter = await get_webhook_emitter()
    
    return emitter

# Usage
emitter = await setup_webhooks()
```

### Emitting Events

```python
# Emit authentication result
await emitter.emit_auth_result(
    transaction_id="txn_12345",
    decision="APPROVE",
    score=85.0,
    metadata={
        "merchant_id": "merchant_123",
        "customer_id": "customer_456"
    }
)

# Emit settlement event
await emitter.emit_settlement(
    transaction_id="txn_12345",
    amount=150.00,
    currency="USD",
    status="completed",
    metadata={
        "settlement_id": "settlement_789"
    }
)

# Emit chargeback event
await emitter.emit_chargeback(
    transaction_id="txn_12345",
    chargeback_id="cb_12345",
    reason="fraud_suspected",
    amount=150.00
)

# Emit loyalty event
await emitter.emit_loyalty_event(
    customer_id="customer_456",
    event_type="points_earned",
    points_change=15
)
```

### Webhook Management

```python
# List all webhooks
webhooks = await webhook_manager.list_webhooks()
for webhook in webhooks:
    print(f"ID: {webhook['webhook_id']}")
    print(f"URL: {webhook['url']}")
    print(f"Event Types: {webhook['event_types']}")

# Get specific webhook
config = await webhook_manager.get_webhook("webhook_id")
if config:
    print(f"Webhook URL: {config.url}")

# Remove webhook
await webhook_manager.remove_webhook("webhook_id")

# Check delivery history
deliveries = await webhook_manager.get_delivery_history(
    webhook_id="webhook_id",
    limit=100
)

# Clear old history
removed = await webhook_manager.clear_delivery_history(older_than_days=30)
print(f"Removed {removed} old delivery records")
```

## Security

### Payload Signing

All webhook payloads are signed using HMAC-SHA256 with the configured webhook secret.

**Signature Header:**
```
X-Webhook-Signature: sha256=<hex_signature>
```

**Verification (Python):**
```python
import hmac
import hashlib

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    received = signature.replace('sha256=', '')
    return hmac.compare_digest(expected, received)

# Usage
is_valid = verify_signature(
    request.body,
    request.headers['X-Webhook-Signature'],
    'your_webhook_secret'
)
```

**Verification (Node.js):**
```javascript
const crypto = require('crypto');

function verifySignature(payload, signature, secret) {
    const expected = crypto
        .createHmac('sha256', secret)
        .update(payload)
        .digest('hex');
    
    const received = signature.replace('sha256=', '');
    return crypto.timingSafeEqual(
        Buffer.from(expected, 'hex'),
        Buffer.from(received, 'hex')
    );
}
```

### Additional Headers

Each webhook request includes these headers for verification:

```
Content-Type: application/json
X-Webhook-Signature: sha256=<signature>
X-Webhook-Event-Type: <event_type>
X-Webhook-Event-ID: <event_id>
User-Agent: AltWallet-Checkout-Agent/1.0
```

## Retry Logic

### Exponential Backoff

The webhook module implements exponential backoff for failed deliveries:

- **Attempt 1**: Base delay (e.g., 1 second)
- **Attempt 2**: Base delay × 2¹ = 2 seconds
- **Attempt 3**: Base delay × 2² = 4 seconds
- **Attempt 4**: Base delay × 2³ = 8 seconds
- **Maximum**: Capped at `retry_delay_max`

### Retry Conditions

Webhooks are retried when:
- HTTP status code is not 2xx
- Request times out
- Network errors occur
- Server errors (5xx) are returned

### Retry Limits

- **Default**: 3 retry attempts
- **Configurable**: Per webhook via `max_retries`
- **Final State**: After max retries, status becomes `FAILED`

## Delivery Tracking

### Delivery Status

| Status | Description |
|--------|-------------|
| `PENDING` | Delivery attempt in progress |
| `SENT` | Successfully delivered |
| `FAILED` | Delivery failed (no more retries) |
| `RETRYING` | Scheduled for retry |

### Delivery History

```python
# Get all deliveries
all_deliveries = await webhook_manager.get_delivery_history()

# Filter by webhook
webhook_deliveries = await webhook_manager.get_delivery_history(
    webhook_id="webhook_123"
)

# Filter by status
failed_deliveries = await webhook_manager.get_delivery_history(
    status=WebhookStatus.FAILED
)

# Filter by event
event_deliveries = await webhook_manager.get_delivery_history(
    event_id="event_456"
)
```

### Delivery Record Fields

```python
{
    "webhook_id": "webhook_123",
    "event_id": "event_456",
    "url": "https://example.com/webhook",
    "status": "sent",
    "attempt": 1,
    "sent_at": 1640995200.0,
    "response_code": 200,
    "response_body": "OK",
    "error_message": null,
    "retry_after": null
}
```

## Integration Examples

### FastAPI Integration

```python
from fastapi import FastAPI, BackgroundTasks
from altwallet_agent.webhooks import get_webhook_emitter

app = FastAPI()

@app.post("/webhook/setup")
async def setup_webhook(webhook_url: str, secret: str):
    webhook_manager = await get_webhook_manager()
    
    config = WebhookConfig(
        url=webhook_url,
        secret=secret,
        event_types=[WebhookEventType.AUTH_RESULT]
    )
    
    await webhook_manager.add_webhook("api_webhook", config)
    return {"status": "webhook configured"}

@app.post("/transaction/process")
async def process_transaction(
    transaction_data: dict,
    background_tasks: BackgroundTasks
):
    # Process transaction
    decision = "APPROVE"
    score = 85.0
    
    # Emit webhook in background
    background_tasks.add_task(
        emit_auth_result,
        transaction_data["id"],
        decision,
        score
    )
    
    return {"decision": decision, "score": score}

async def emit_auth_result(transaction_id: str, decision: str, score: float):
    emitter = await get_webhook_emitter()
    await emitter.emit_auth_result(transaction_id, decision, score)
```

### Django Integration

```python
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import asyncio
from altwallet_agent.webhooks import get_webhook_emitter

@method_decorator(csrf_exempt, name='dispatch')
class WebhookSetupView(View):
    async def post(self, request):
        data = json.loads(request.body)
        
        webhook_manager = await get_webhook_manager()
        config = WebhookConfig(
            url=data['url'],
            secret=data['secret']
        )
        
        await webhook_manager.add_webhook("django_webhook", config)
        return JsonResponse({"status": "configured"})

class TransactionView(View):
    async def post(self, request):
        # Process transaction
        transaction_id = "txn_123"
        decision = "APPROVE"
        score = 85.0
        
        # Emit webhook
        emitter = await get_webhook_emitter()
        await emitter.emit_auth_result(transaction_id, decision, score)
        
        return JsonResponse({
            "transaction_id": transaction_id,
            "decision": decision,
            "score": score
        })
```

## Testing

### Unit Tests

```bash
# Run webhook tests
pytest tests/test_webhooks.py -v

# Run with coverage
pytest tests/test_webhooks.py --cov=src/altwallet_agent/webhooks
```

### Integration Testing

```python
# Test webhook delivery
async def test_webhook_delivery():
    # Mock webhook endpoint
    mock_server = MockWebhookServer()
    
    # Configure webhook
    webhook_manager = await get_webhook_manager()
    config = WebhookConfig(
        url=mock_server.url,
        secret="test_secret"
    )
    await webhook_manager.add_webhook("test_webhook", config)
    
    # Emit event
    emitter = await get_webhook_emitter()
    deliveries = await emitter.emit_auth_result(
        "txn_test", "APPROVE", 85.0
    )
    
    # Verify delivery
    assert len(deliveries) == 1
    assert deliveries[0].status == WebhookStatus.SENT
    assert mock_server.received_events == 1
```

## Performance Considerations

### Async Operations
- All webhook operations are asynchronous
- Non-blocking event emission
- Concurrent webhook delivery

### Connection Pooling
- HTTP connection reuse via aiohttp
- Configurable connection limits
- Automatic connection cleanup

### Memory Management
- Delivery history with configurable retention
- Automatic cleanup of old records
- Efficient payload serialization

## Monitoring and Debugging

### Logging
The webhook module integrates with the structured logging system:

```python
# Webhook events are logged with structured data
logger.info(
    "Webhook sent successfully",
    webhook_id="webhook_123",
    event_id="event_456",
    response_code=200
)
```

### Metrics
Track webhook performance with delivery status:

```python
# Get delivery statistics
all_deliveries = await webhook_manager.get_delivery_history()
successful = len([d for d in all_deliveries if d.is_successful])
total = len(all_deliveries)
success_rate = successful / total if total > 0 else 0

print(f"Webhook success rate: {success_rate:.2%}")
```

### Error Handling
```python
try:
    await emitter.emit_auth_result("txn_123", "APPROVE", 85.0)
except Exception as e:
    logger.error("Failed to emit webhook", error=str(e))
    # Handle error appropriately
```

## Best Practices

### Security
1. **Use strong secrets**: Generate cryptographically secure webhook secrets
2. **Verify signatures**: Always verify webhook signatures on the receiving end
3. **HTTPS only**: Use HTTPS for all webhook endpoints
4. **Secret rotation**: Regularly rotate webhook secrets

### Reliability
1. **Idempotency**: Design webhook handlers to be idempotent
2. **Timeout handling**: Set appropriate timeouts for your use case
3. **Retry configuration**: Configure retry attempts based on business requirements
4. **Monitoring**: Monitor webhook delivery success rates

### Performance
1. **Async processing**: Process webhooks asynchronously when possible
2. **Connection pooling**: Reuse HTTP connections for multiple webhooks
3. **Batch processing**: Consider batching multiple events when appropriate
4. **Rate limiting**: Implement rate limiting on webhook endpoints

## Troubleshooting

### Common Issues

**Webhook not receiving events:**
- Check webhook URL and secret configuration
- Verify webhook is enabled
- Check event type filtering
- Review delivery history for errors

**High failure rates:**
- Check webhook endpoint availability
- Verify signature verification
- Review timeout and retry settings
- Check network connectivity

**Performance issues:**
- Monitor connection pool usage
- Review timeout configurations
- Check webhook endpoint response times
- Consider webhook endpoint scaling

### Debug Commands

```python
# Check webhook status
webhooks = await webhook_manager.list_webhooks()
print(f"Active webhooks: {len(webhooks)}")

# Check delivery history
recent_deliveries = await webhook_manager.get_delivery_history(limit=10)
for delivery in recent_deliveries:
    print(f"Status: {delivery.status}, URL: {delivery.url}")

# Test webhook configuration
config = await webhook_manager.get_webhook("webhook_id")
if config:
    print(f"URL: {config.url}")
    print(f"Enabled: {config.enabled}")
    print(f"Max retries: {config.max_retries}")
```
