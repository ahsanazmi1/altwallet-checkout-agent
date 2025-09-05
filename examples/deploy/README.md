# Deployment Examples

This directory contains example configurations and integration code for deploying the AltWallet Checkout Agent in different modes.

## Deployment Modes

### 1. Sidecar Mode
Runs the agent as a containerized service alongside your merchant application.

**Files:**
- `sidecar_config.json` - Configuration for sidecar deployment
- `sidecar_docker_compose.yml` - Docker Compose setup for sidecar mode

**Features:**
- Containerized service
- HTTP API access
- Health checks and monitoring
- Resource limits and scaling
- Integration with monitoring stack (Prometheus, Grafana)

### 2. Inline Mode
Embeds the agent directly into your merchant application.

**Files:**
- `inline_config.json` - Configuration for inline deployment
- `inline_integration_example.py` - Complete integration examples

**Features:**
- Direct function calls
- Optimized performance
- Circuit breaker pattern
- Caching and retry logic
- Both async and sync interfaces

## Quick Start

### Sidecar Deployment

1. **Using Docker Compose:**
```bash
# Copy the example configuration
cp examples/deploy/sidecar_docker_compose.yml docker-compose.yml

# Start the services
docker-compose up -d

# Check health
curl http://localhost:8000/health
```

2. **Using Kubernetes:**
```bash
# Apply the Kubernetes manifests
kubectl apply -f deployment/sidecar/kubernetes.yaml

# Check deployment status
kubectl get pods -n altwallet
```

### Inline Deployment

1. **Install the package:**
```bash
pip install altwallet-checkout-agent
```

2. **Basic integration:**
```python
from deployment import process_checkout_inline, CheckoutRequest

# Process a checkout
request = CheckoutRequest(
    merchant_id="your-merchant",
    amount=100.0,
    currency="USD"
)

response = await process_checkout_inline(request)
print(f"Best card: {response.recommendations[0].card_name}")
```

3. **Advanced integration:**
```python
from deployment import InlineCheckoutClient, InlineConfig

# Configure the client
config = InlineConfig(
    merchant_app_name="my-app",
    cache_enabled=True,
    circuit_breaker_enabled=True
)

# Create and use client
client = InlineCheckoutClient(config)
await client.initialize()

response = await client.process_checkout(request)
```

## Configuration

### Environment Variables

Both deployment modes support configuration via environment variables:

```bash
# Deployment mode selection
export DEPLOYMENT_MODE=sidecar  # or 'inline'

# Common configuration
export ENVIRONMENT=production
export LOG_LEVEL=INFO
export API_HOST=0.0.0.0
export API_PORT=8000
export MAX_WORKERS=4
export REQUEST_TIMEOUT=30
export METRICS_ENABLED=true
export TRACING_ENABLED=true
```

### Configuration Files

You can also use JSON configuration files:

```python
from deployment import load_deployment_config

# Load from file
config = load_deployment_config("examples/deploy/sidecar_config.json")
```

## Integration Examples

### Async Integration

```python
import asyncio
from deployment import InlineCheckoutClient, CheckoutRequest

async def main():
    client = InlineCheckoutClient()
    await client.initialize()
    
    request = CheckoutRequest(
        merchant_id="grocery-store",
        amount=45.99,
        currency="USD"
    )
    
    response = await client.process_checkout(request)
    print(f"Recommendations: {len(response.recommendations)}")
    
    await client.cleanup()

asyncio.run(main())
```

### Sync Integration

```python
from deployment import SyncInlineCheckoutClient, CheckoutRequest

client = SyncInlineCheckoutClient()
client.initialize()

request = CheckoutRequest(
    merchant_id="electronics-store",
    amount=299.99,
    currency="USD"
)

response = client.process_checkout(request)
print(f"Best card: {response.recommendations[0].card_name}")

client.cleanup()
```

### Context Manager

```python
from deployment import inline_checkout_client, CheckoutRequest

async def main():
    async with inline_checkout_client() as client:
        request = CheckoutRequest(
            merchant_id="gas-station",
            amount=25.00,
            currency="USD"
        )
        
        response = await client.process_checkout(request)
        print(f"Transaction ID: {response.transaction_id}")

asyncio.run(main())
```

### Convenience Function

```python
from deployment import process_checkout_inline, CheckoutRequest

async def main():
    request = CheckoutRequest(
        merchant_id="restaurant",
        amount=75.50,
        currency="USD"
    )
    
    response = await process_checkout_inline(request)
    print(f"Score: {response.score}")

asyncio.run(main())
```

## Monitoring and Health Checks

### Health Check Endpoints

**Sidecar Mode:**
```bash
# Basic health check
curl http://localhost:8000/health

# Detailed health check
curl http://localhost:8000/health/detailed
```

**Inline Mode:**
```python
# Health check
health = await client.health_check()
print(f"Status: {health['status']}")
```

### Metrics

**Sidecar Mode:**
```bash
# Prometheus metrics
curl http://localhost:8000/metrics
```

**Inline Mode:**
```python
# Get metrics
metrics = client.get_metrics()
print(f"Request count: {metrics['request_count']}")
print(f"Error rate: {metrics['error_rate']:.2%}")
```

## Performance Tuning

### Sidecar Mode

- **Resource Limits:** Adjust memory and CPU limits in Docker Compose or Kubernetes
- **Scaling:** Use Kubernetes HPA or Docker Swarm scaling
- **Caching:** Enable Redis for response caching

### Inline Mode

- **Connection Pool:** Configure `connection_pool_size` for HTTP clients
- **Caching:** Enable and tune `cache_ttl` for response caching
- **Circuit Breaker:** Configure failure thresholds and timeouts
- **Retry Logic:** Adjust retry attempts and delays

## Security Considerations

### Sidecar Mode

- Use non-root containers
- Enable security contexts in Kubernetes
- Configure network policies
- Use secrets for sensitive data

### Inline Mode

- Validate all input data
- Use secure coding practices
- Implement proper error handling
- Monitor for security issues

## Troubleshooting

### Common Issues

1. **Connection Refused (Sidecar)**
   - Check if the service is running
   - Verify port configuration
   - Check firewall settings

2. **Import Errors (Inline)**
   - Ensure the package is installed
   - Check Python path
   - Verify dependencies

3. **Performance Issues**
   - Check resource limits
   - Monitor metrics
   - Tune configuration parameters

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
```

### Logs

**Sidecar Mode:**
```bash
# Docker logs
docker logs altwallet-checkout-agent

# Kubernetes logs
kubectl logs -n altwallet deployment/altwallet-checkout-agent
```

**Inline Mode:**
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Support

For more information and support:

- Check the main documentation in `/docs`
- Review the test examples in `/tests`
- See the API documentation in `/openapi`
- Contact the development team for assistance
