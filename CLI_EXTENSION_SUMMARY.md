# CLI Extension Summary

## Overview

The CLI has been successfully extended to provide comprehensive card recommendations with machine-readable JSON output. The extension adds the `--json` and `-vv` flags to the existing `score` command.

## New Features

### 1. `--json` Flag
When the `--json` flag is used, the CLI outputs a comprehensive JSON document that includes:

- **Basic scoring information**: `trace_id`, `risk_score`, `loyalty_boost`, `final_score`, `routing_hint`, `signals`
- **Card recommendations**: An array of candidate cards with detailed information

### 2. Card Recommendation Structure
Each card recommendation includes:

```json
{
  "card_id": "amex_gold",
  "card_name": "American Express Gold",
  "p_approval": 0.95,
  "expected_rewards": 0.1,
  "utility": 0.094354,
  "top_drivers": [
    {
      "feature": "loyalty_tier_boost",
      "value": 10,
      "impact": "positive"
    }
  ],
  "audit": {
    "scoring_audit": { ... },
    "utility_audit": { ... },
    "transaction_context": { ... }
  }
}
```

### 3. `-vv` Flag (Verbose Logging)
- **Default behavior**: Quiet mode - minimal logging output
- **With `-vv`**: Verbose mode - detailed JSON logs to stdout
- JSON logs are only output when `-vv` is set

## Usage Examples

### Basic Scoring (Original Behavior)
```bash
echo '{"customer": {...}}' | python -m src.altwallet_agent.cli score
```

### JSON Output with Card Recommendations
```bash
echo '{"customer": {...}}' | python -m src.altwallet_agent.cli score --json
```

### Pretty-printed JSON Output
```bash
echo '{"customer": {...}}' | python -m src.altwallet_agent.cli score --json --pretty
```

### Verbose Logging
```bash
echo '{"customer": {...}}' | python -m src.altwallet_agent.cli score --json -vv
```

## Implementation Details

### Key Components Added

1. **Sample Card Database**: Built-in sample cards for demonstration
   - Chase Sapphire Preferred
   - American Express Gold
   - Citi Double Cash
   - Chase Freedom Unlimited

2. **Top Drivers Extraction**: Identifies the most significant factors affecting the score
   - Positive drivers (e.g., loyalty tier boost)
   - Negative drivers (e.g., location mismatch, high velocity)

3. **Audit Block**: Comprehensive audit information including:
   - Scoring audit (risk score, loyalty boost, final score, routing hint, signals)
   - Utility audit (components breakdown, score result, context info)
   - Transaction context (merchant, cart, customer details)

4. **Logging Control**: Proper verbosity control
   - Quiet mode by default
   - Verbose mode with `-vv` flag

### Integration Points

- **Composite Utility Module**: Used for calculating card utility scores
- **Scoring Module**: Provides base scoring and signals
- **Preference Weighting**: Considers user preferences and loyalty tiers
- **Merchant Penalty**: Applies merchant-specific adjustments

## Output Structure

The JSON output follows this structure:

```json
{
  "trace_id": "uuid",
  "risk_score": 0,
  "loyalty_boost": 10,
  "final_score": 110,
  "routing_hint": "prefer_visa",
  "signals": { ... },
  "card_recommendations": [
    {
      "card_id": "string",
      "card_name": "string",
      "p_approval": 0.95,
      "expected_rewards": 0.1,
      "utility": 0.094354,
      "top_drivers": [
        {
          "feature": "string",
          "value": 10,
          "impact": "positive|negative"
        }
      ],
      "audit": {
        "scoring_audit": { ... },
        "utility_audit": { ... },
        "transaction_context": { ... }
      }
    }
  ]
}
```

## Testing

The implementation has been tested with:
- Basic scoring functionality (without `--json`)
- JSON output with card recommendations
- Pretty-printed output
- Verbose logging control

All core functionality works as expected, providing a comprehensive card recommendation system that integrates with the existing scoring infrastructure.

## Backward Compatibility

The extension maintains full backward compatibility:
- Existing `score` command behavior unchanged
- All existing flags (`--input`, `--trace-id`, `--pretty`) continue to work
- New flags are optional and additive
