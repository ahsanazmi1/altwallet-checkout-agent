# Structured Logging

The AltWallet Checkout Agent uses structured logging with `structlog` to provide comprehensive, machine-readable logs for monitoring and debugging.

## Features

- **JSON Format**: All logs are emitted in JSON format for easy parsing
- **ISO8601 Timestamps**: Precise timestamps in ISO8601 format
- **Trace ID Correlation**: Each request gets a unique trace ID for correlation
- **Structured Events**: Log events include structured data fields
- **Environment-based Configuration**: Log level controlled via `LOG_LEVEL` environment variable

## Configuration

### Log Level

Set the log level using the `LOG_LEVEL` environment variable:

```bash
export LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

Default: `INFO`

### Environment Variables

- `LOG_LEVEL`: Controls log verbosity (default: `INFO`)

## Usage

### Basic Logging

```python
from altwallet_agent.logger import get_logger, set_trace_id

# Set trace ID for correlation
set_trace_id("request-123")

# Get logger
logger = get_logger(__name__)

# Log structured events
logger.info("Processing transaction",
            merchant_id="merchant_123",
            amount=100.50,
            currency="USD")
```

### CLI Integration

The CLI automatically sets trace IDs and logs key events:

- **Checkout Command**: Generates trace ID and logs processing steps
- **Score Command**: Uses provided or generated trace ID and logs scoring events

### Key Log Events

#### Checkout Processing
- `Starting checkout processing`: When checkout begins
- `Configuration loaded from file`: When config file is loaded
- `Processing checkout request`: When agent processes request
- `Checkout processing completed`: When checkout finishes

#### Transaction Scoring
- `Context parsed successfully`: When JSON context is parsed
- `Starting transaction scoring`: When scoring begins
- `Scoring completed`: When scoring finishes (includes final_score, routing_hint)

#### Scoring Details (DEBUG level)
- `Risk score calculated`: Risk score calculation
- `Loyalty boost calculated`: Loyalty boost calculation
- `Final score calculated`: Final score calculation
- `Routing hint determined`: Routing hint determination

## Log Format

Each log entry includes:

```json
{
  "timestamp": "2024-01-15T10:30:45.123456Z",
  "level": "info",
  "logger": "altwallet_agent.cli",
  "event": "Scoring completed",
  "trace_id": "request-123",
  "final_score": 85,
  "routing_hint": "visa",
  "risk_score": 15,
  "loyalty_boost": 10
}
```

## Testing

Run the logging demo to see structured logs in action:

```bash
python examples/logging_demo.py
```

## Integration

The logging system is automatically configured when the `altwallet_agent.logger` module is imported. No additional setup is required for CLI commands.

For custom applications, import and configure:

```python
from altwallet_agent.logger import configure_logging, get_logger, set_trace_id

# Configure (optional, done automatically on import)
configure_logging()

# Use logging
set_trace_id("my-trace-id")
logger = get_logger("my_app")
logger.info("My event", data="value")
```
