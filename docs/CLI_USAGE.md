# AltWallet Agent CLI Usage

## Overview

The AltWallet Agent provides a command-line interface for scoring transactions using the deterministic scoring system.

## Installation

The CLI is available as a Python module. Make sure you have the required dependencies installed:

```bash
pip install typer rich
```

## Basic Usage

### Score Command

The main command is `score`, which processes transaction data and returns scoring results.

```bash
python -m altwallet_agent score [OPTIONS]
```

### Options

- `--input, -i`: Path to JSON input file (optional - reads from stdin if not provided)
- `--trace-id, -t`: Trace ID for tracking (generates UUID v4 if omitted)
- `--pretty, -p`: Pretty-print JSON output (default: compact JSON)
- `--help, -h`: Show help message

## Examples

### 1. Score from File

```bash
python -m altwallet_agent score --input examples/context_basic.json
```

Output:
```json
{"trace_id":"550e8400-e29b-41d4-a716-446655440000","risk_score":0,"loyalty_boost":5,"final_score":105,"routing_hint":"prefer_mc","signals":{...}}
```

### 2. Score with Custom Trace ID

```bash
python -m altwallet_agent score --input examples/context_risky.json --trace-id "my-trace-123"
```

### 3. Pretty-Printed Output

```bash
python -m altwallet_agent score --input examples/context_basic.json --pretty
```

Output:
```json
{
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "risk_score": 0,
  "loyalty_boost": 5,
  "final_score": 105,
  "routing_hint": "prefer_mc",
  "signals": {
    "location_mismatch": false,
    "velocity_flag": false,
    "chargebacks_present": false,
    "high_ticket": false,
    "risk_factors": [],
    "cart_total": 45.99,
    "customer_velocity_24h": 3,
    "customer_chargebacks_12m": 0,
    "loyalty_tier": "SILVER",
    "merchant_mcc": "5411",
    "merchant_network_preferences": [],
    "routing_hint": "prefer_mc",
    "loyalty_boost": 5,
    "final_score": 105
  }
}
```

### 4. Read from Stdin

```bash
cat examples/context_basic.json | python -m altwallet_agent score
```

### 5. Pipeline Usage

```bash
echo '{"cart": {...}}' | python -m altwallet_agent score --trace-id "pipeline-123"
```

## Input Format

The CLI expects JSON input that can be parsed into a `Context` object. The JSON should contain:

- `cart`: Shopping cart information
- `merchant`: Merchant details
- `customer`: Customer information
- `device`: Device information
- `geo`: Geographic location

### Example Input Structure

```json
{
  "cart": {
    "items": [
      {
        "item": "Product Name",
        "unit_price": "100.00",
        "qty": 1,
        "mcc": "5411"
      }
    ],
    "currency": "USD"
  },
  "merchant": {
    "name": "Merchant Name",
    "mcc": "5411",
    "network_preferences": [],
    "location": {
      "city": "New York",
      "country": "US"
    }
  },
  "customer": {
    "id": "customer_123",
    "loyalty_tier": "SILVER",
    "historical_velocity_24h": 5,
    "chargebacks_12m": 0
  },
  "device": {
    "ip": "192.168.1.1",
    "device_id": "device_123",
    "location": {
      "city": "New York",
      "country": "US"
    }
  },
  "geo": {
    "city": "New York",
    "country": "US"
  }
}
```

## Output Format

The CLI outputs a single JSON object with the following structure:

```json
{
  "trace_id": "string",
  "risk_score": 0,
  "loyalty_boost": 5,
  "final_score": 105,
  "routing_hint": "prefer_mc",
  "signals": {
    "location_mismatch": false,
    "velocity_flag": false,
    "chargebacks_present": false,
    "high_ticket": false,
    "risk_factors": [],
    "cart_total": 100.0,
    "customer_velocity_24h": 5,
    "customer_chargebacks_12m": 0,
    "loyalty_tier": "SILVER",
    "merchant_mcc": "5411",
    "merchant_network_preferences": [],
    "routing_hint": "prefer_mc",
    "loyalty_boost": 5,
    "final_score": 105
  }
}
```

### Output Fields

- `trace_id`: Unique identifier for the scoring request
- `risk_score`: Calculated risk score (0-100)
- `loyalty_boost`: Loyalty tier boost points
- `final_score`: Final score after risk and loyalty adjustments (0-120)
- `routing_hint`: Payment network preference
- `signals`: Detailed scoring signals and components

## Error Handling

The CLI returns appropriate exit codes:

- `0`: Success
- `1`: Error (validation, runtime, or file not found)

### Common Errors

1. **File not found**:
   ```
   Error: File examples/missing.json not found
   ```

2. **Invalid JSON**:
   ```
   Error: Invalid JSON input: Expecting ',' delimiter
   ```

3. **Validation error**:
   ```
   Error: 1 validation error for Context
   ```

## Testing

Run the CLI tests to verify functionality:

```bash
python tests/test_cli_scoring.py
```

## Integration Examples

### Shell Script Integration

```bash
#!/bin/bash
# score_transaction.sh

INPUT_FILE="$1"
TRACE_ID="$2"

if [ -z "$INPUT_FILE" ]; then
    echo "Usage: $0 <input_file> [trace_id]"
    exit 1
fi

if [ -z "$TRACE_ID" ]; then
    python -m altwallet_agent score --input "$INPUT_FILE"
else
    python -m altwallet_agent score --input "$INPUT_FILE" --trace-id "$TRACE_ID"
fi
```

### Python Integration

```python
import subprocess
import json

def score_transaction(input_file, trace_id=None):
    """Score a transaction using the CLI."""
    cmd = ["python", "-m", "altwallet_agent", "score", "--input", input_file]
    
    if trace_id:
        cmd.extend(["--trace-id", trace_id])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        return json.loads(result.stdout.strip())
    else:
        raise RuntimeError(f"Scoring failed: {result.stderr}")

# Usage
result = score_transaction("examples/context_basic.json", "my-trace-123")
print(f"Final Score: {result['final_score']}")
```

## Performance

The CLI is designed for fast, stateless processing:

- Typical response time: < 100ms
- Memory usage: < 50MB
- No external dependencies during scoring
- Deterministic results for same input

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure you're running from the project root directory
2. **JSON parsing errors**: Validate your input JSON format
3. **Missing dependencies**: Install required packages with `pip install typer rich`

### Debug Mode

For debugging, you can run with verbose output:

```bash
python -m altwallet_agent score --input examples/context_basic.json --pretty
```

This will show the full scoring signals and help identify issues.
