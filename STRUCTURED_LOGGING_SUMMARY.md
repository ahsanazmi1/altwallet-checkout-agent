# Structured Logging Implementation Summary

## Overview

The logging system has been enhanced to emit structured JSON logs with the requested fields: `ts`, `level`, `component`, `request_id`, and `latency_ms`. The implementation also includes PII removal and a silent mode for tests and golden runs.

## New Features

### 1. Structured JSON Log Format

All log entries now include the following structured fields:

```json
{
  "ts": "2025-08-28T00:09:21.483918Z",
  "level": "info",
  "component": "cli",
  "request_id": "90aa2f31-ad56-4f92-a6ab-75a214b20d63",
  "latency_ms": 22,
  "event": "Context parsed successfully"
}
```

**Field Descriptions:**
- **`ts`**: ISO8601 timestamp
- **`level`**: Lowercase log level (debug, info, warning, error, critical)
- **`component`**: Extracted from logger name (e.g., "src.altwallet_agent.cli" → "cli")
- **`request_id`**: Request identifier (from trace_id)
- **`latency_ms`**: Request latency in milliseconds

### 2. PII Removal

The logging system automatically removes PII fields from log entries:

**Removed Fields:**
- `customer_id`, `user_id`, `merchant_id`, `device_id`
- `ip`, `email`, `phone`, `name`, `address`
- `city`, `country`, `postal_code`, `ssn`
- `card_number`, `account_number`, `password`
- `token`, `secret`, `key`

**Implementation:**
- Exact field name matches
- Partial field name matches (case-insensitive)
- Applied to all log entries automatically

### 3. Silent Mode

Silent mode is controlled via the `LOG_SILENT` environment variable:

```bash
# Enable silent mode (no logs output)
export LOG_SILENT=1
python -m src.altwallet_agent.cli score --json

# Disable silent mode (normal logging)
export LOG_SILENT=0
python -m src.altwallet_agent.cli score --json
```

**Supported Values:**
- `1`, `true`, `yes`, `on` → Silent mode enabled
- `0`, `false`, `no`, `off` → Silent mode disabled (default)

### 4. Latency Tracking

Request latency is automatically tracked and included in log entries:

```python
from src.altwallet_agent.logger import set_request_start_time, set_trace_id

# Set up request context
set_trace_id("request-123")
set_request_start_time()

# All subsequent logs will include latency_ms
logger.info("Processing started")  # latency_ms: 0
time.sleep(0.1)
logger.info("Processing completed")  # latency_ms: 100
```

## Implementation Details

### Enhanced Logger Configuration

The logger now includes:

1. **Structured Field Processing**: Automatically adds required fields to all log entries
2. **PII Filtering**: Removes sensitive information before output
3. **Silent Mode Support**: Configurable via environment variable
4. **Latency Calculation**: Tracks request duration

### Integration Points

- **CLI Commands**: Both `checkout` and `score` commands use the enhanced logging
- **Request Context**: Trace ID and start time are set at the beginning of each request
- **Component Extraction**: Logger names are automatically converted to component names

## Usage Examples

### Normal Logging
```bash
# Structured logs with all fields
python -m src.altwallet_agent.cli score --json -vv
```

### Silent Mode for Tests
```bash
# No log output
LOG_SILENT=1 python -m src.altwallet_agent.cli score --json
```

### Golden Runs
```bash
# Silent mode for automated testing
LOG_SILENT=1 python -m src.altwallet_agent.cli score --json --pretty > output.json
```

## Log Output Examples

### Info Level Log
```json
{
  "ts": "2025-08-28T00:09:21.483918Z",
  "level": "info",
  "component": "cli",
  "request_id": "90aa2f31-ad56-4f92-a6ab-75a214b20d63",
  "latency_ms": 0,
  "event": "Context parsed successfully",
  "context_keys": ["cart", "merchant", "customer", "device", "geo", "flags"]
}
```

### Error Level Log
```json
{
  "ts": "2025-08-28T00:09:21.506844Z",
  "level": "error",
  "component": "scoring",
  "request_id": "90aa2f31-ad56-4f92-a6ab-75a214b20d63",
  "latency_ms": 22,
  "event": "Scoring failed",
  "error": "Invalid input data"
}
```

## Backward Compatibility

The enhanced logging maintains full backward compatibility:

- Existing log calls continue to work
- No changes required to existing code
- All existing environment variables still supported
- CLI behavior unchanged

## Testing

The implementation has been tested with:

- ✅ Structured field generation
- ✅ PII removal functionality
- ✅ Silent mode operation
- ✅ Latency tracking
- ✅ Component name extraction
- ✅ Request ID propagation

All features work as expected and integrate seamlessly with the existing codebase.
