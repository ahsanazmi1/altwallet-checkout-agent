# Webhook Emitter Documentation

## Overview

The AltWallet Checkout Agent webhook emitter provides a robust, asynchronous event delivery system for downstream integrations. It supports configurable webhook endpoints with retry logic, payload signing, and comprehensive delivery tracking.

## Architecture

### Core Components

- **WebhookEventEmitter**: Main event emission engine
- **WebhookManager**: Webhook configuration and lifecycle management
- **WebhookConfig**: Individual webhook endpoint configuration
- **WebhookPayload**: Event payload with HMAC-SHA256 signature
- **WebhookDelivery**: Delivery tracking and status management

### Event Flow

```
Transaction Event → WebhookEventEmitter → WebhookManager → HTTP Delivery → Retry Logic → Status Tracking
```

## Supported Event Types

| Event Type | Description | Typical Use Case |
|------------|-------------|------------------|
| `auth_result` | Authentication/authorization result | Payment gateway integration |
| `settlement` | Transaction settlement notification | Accounting systems |
| `chargeback` | Chargeback/dispute notification | Risk management |
| `loyalty_event` | Loyalty program events | Customer engagement |

## Configuration

### Webhook Configuration

```python
from altwallet_agent.webhooks import WebhookConfig, WebhookEventType

config = WebhookConfig(
    url="https://api.example.com/webhooks",
    event_types=[WebhookEventType.AUTH_RESULT, WebhookEventType.SETTLEMENT],
    secret_key="your-secret-key-here",
    max_retries=3,
    timeout_seconds=30,
    is_active=True
)
```

### Configuration Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | string | Yes | - | Webhook endpoint URL |
| `event_types` | array | Yes | - | List of event types to receive |
| `secret_key` | string | Yes | - | Secret for payload signing |
| `max_retries` | integer | No | 3 | Maximum retry attempts |
| `timeout_seconds` | integer | No | 30 | HTTP timeout in seconds |
| `is_active` | boolean | No | true | Whether webhook is active |

## Usage Examples

### Basic Event Emission

```python
from altwallet_agent.webhooks import get_webhook_emitter, WebhookEventType

emitter = get_webhook_emitter()

# Emit an auth result event
await emitter.emit_auth_result(
    event_id="evt_123",
    data={
        "transaction_id": "txn_456",
        "status": "approved",
        "amount": 100.00
    }
)
```

### Custom Event Data

```python
# Emit a settlement event with custom data
await emitter.emit_settlement(
    event_id="evt_789",
    data={
        "transaction_id": "txn_456",
        "settlement_amount": 99.50,
        "fees": 0.50,
        "settlement_date": "2024-01-15T10:30:00Z"
    }
)
```

### Loyalty Event with Metadata

```python
await emitter.emit_loyalty_event(
    event_id="evt_101",
    data={
        "customer_id": "cust_123",
        "points_earned": 150,
        "tier_upgrade": True,
        "campaign": "winter_bonus"
    }
)
```

## Security Features

### Payload Signing

All webhook payloads are signed using HMAC-SHA256 with the configured secret key:

```python
# Signature calculation
import hmac
import hashlib

signature = hmac.new(
    secret_key.encode('utf-8'),
    json_payload.encode('utf-8'),
    hashlib.sha256
).hexdigest()
```

### Verification on Receiver Side

```python
# Example verification in webhook receiver
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret_key):
    expected_signature = hmac.new(
        secret_key.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)
```

## Retry Logic

### Exponential Backoff

The webhook emitter implements exponential backoff for failed deliveries:

- **Attempt 1**: Immediate retry
- **Attempt 2**: 1 second delay
- **Attempt 3**: 2 seconds delay
- **Attempt 4**: 4 seconds delay
- **Attempt 5**: 8 seconds delay

### Retry Conditions

Webhooks are retried when:
- HTTP status code is 4xx or 5xx
- Network timeout occurs
- Connection errors happen
- Maximum retries not exceeded

## Delivery Tracking

### Webhook Delivery Status

| Status | Description |
|--------|-------------|
| `pending` | Initial delivery attempt |
| `sent` | Successfully delivered |
| `failed` | All retries exhausted |
| `retrying` | Currently retrying |

### Delivery History

```python
from altwallet_agent.webhooks import get_webhook_manager

manager = get_webhook_manager()
history = await manager.get_webhook_history("webhook_123")

for delivery in history:
    print(f"Status: {delivery.status}")
    print(f"Attempts: {delivery.attempt}")
    print(f"Response: {delivery.response_code}")
    print(f"Delivered: {delivery.delivered_at}")
```

## Error Handling

### Common Error Scenarios

1. **Network Timeouts**: Automatically retried with exponential backoff
2. **HTTP Errors**: 4xx/5xx responses trigger retries
3. **Invalid URLs**: Validation prevents malformed webhook configurations
4. **Authentication Failures**: Logged and tracked for debugging

### Error Monitoring

```python
# Check failed webhooks
failed_webhooks = [
    w for w in manager.list_webhooks() 
    if w.webhook_id in [d.webhook_id for d in history if d.status == "failed"]
]
```

## Performance Considerations

### Async Processing

- All webhook deliveries are asynchronous
- Non-blocking event emission
- Configurable timeout limits
- Connection pooling for HTTP clients

### Scalability

- Webhook manager supports unlimited webhook configurations
- Event emission is stateless and horizontally scalable
- Delivery tracking is lightweight and efficient

## Monitoring and Debugging

### Logging

Webhook events are logged using structured logging:

```json
{
  "event": "webhook_delivery",
  "webhook_id": "webhook_123",
  "event_type": "auth_result",
  "status": "sent",
  "response_code": 200,
  "latency_ms": 150
}
```

### Metrics

Key metrics to monitor:
- Delivery success rate
- Average delivery latency
- Retry frequency
- Failed webhook count

## Best Practices

### Webhook Configuration

1. **Use HTTPS**: Always use secure endpoints
2. **Unique Secret Keys**: Use different secrets for each webhook
3. **Reasonable Timeouts**: Set appropriate timeout values
4. **Event Type Filtering**: Only subscribe to needed events

### Error Handling

1. **Implement Idempotency**: Handle duplicate webhook deliveries
2. **Validate Signatures**: Always verify webhook authenticity
3. **Log Failures**: Track and monitor delivery issues
4. **Graceful Degradation**: Handle webhook failures gracefully

### Security

1. **Secret Rotation**: Regularly rotate webhook secrets
2. **IP Whitelisting**: Restrict webhook sources if possible
3. **Rate Limiting**: Implement rate limiting on webhook endpoints
4. **Input Validation**: Validate all webhook payload data

## Integration Examples

### Payment Gateway Integration

```python
# Configure webhook for payment gateway
payment_webhook = WebhookConfig(
    url="https://payment-gateway.com/webhooks",
    event_types=[WebhookEventType.AUTH_RESULT, WebhookEventType.SETTLEMENT],
    secret_key="pg-secret-123",
    max_retries=5,
    timeout_seconds=45
)

manager.add_webhook(payment_webhook)
```

### CRM System Integration

```python
# Configure webhook for CRM updates
crm_webhook = WebhookConfig(
    url="https://crm.example.com/webhooks",
    event_types=[WebhookEventType.LOYALTY_EVENT],
    secret_key="crm-secret-456",
    max_retries=3,
    timeout_seconds=30
)

manager.add_webhook(crm_webhook)
```

## Troubleshooting

### Common Issues

1. **Webhook Not Receiving Events**
   - Check webhook is active
   - Verify event types are subscribed
   - Check network connectivity

2. **Signature Verification Failures**
   - Verify secret key matches
   - Check payload format
   - Ensure proper encoding

3. **High Retry Rates**
   - Check endpoint availability
   - Verify timeout settings
   - Review network conditions

### Debug Commands

```python
# List all webhooks
webhooks = manager.list_webhooks()
for webhook in webhooks:
    print(f"ID: {webhook.webhook_id}, URL: {webhook.url}, Active: {webhook.is_active}")

# Check delivery history
history = await manager.get_webhook_history("webhook_123")
for delivery in history:
    print(f"Status: {delivery.status}, Attempts: {delivery.attempt}")
```

## API Reference

### WebhookEventEmitter Methods

- `emit_auth_result(event_id: str, data: dict) -> None`
- `emit_settlement(event_id: str, data: dict) -> None`
- `emit_chargeback(event_id: str, data: dict) -> None`
- `emit_loyalty_event(event_id: str, data: dict) -> None`
- `emit_custom_event(event_type: str, event_id: str, data: dict) -> None`

### WebhookManager Methods

- `add_webhook(config: WebhookConfig) -> str`
- `remove_webhook(webhook_id: str) -> bool`
- `list_webhooks() -> List[WebhookConfig]`
- `get_webhook_history(webhook_id: str) -> List[WebhookDelivery]`
- `shutdown() -> None`

### Global Functions

- `get_webhook_manager() -> WebhookManager`
- `get_webhook_emitter() -> WebhookEventEmitter`
- `shutdown_webhooks() -> None`

## Version History

- **v0.3.0**: Initial webhook emitter implementation
  - Async event emission
  - Retry logic with exponential backoff
  - HMAC-SHA256 payload signing
  - Comprehensive delivery tracking
  - Configurable webhook management
