# Golden Regression Test Suite

This directory contains the golden regression test suite for the AltWallet Checkout Agent, designed to ensure scoring consistency across changes and validate core functionality.

## Structure

```
tests/golden/
├── fixtures/           # Input test data (10 JSON contexts)
├── snapshots/          # Expected outputs for each fixture
└── README.md          # This file
```

## Fixtures

The suite includes 10 comprehensive test fixtures covering various transaction scenarios:

1. **01_grocery_small_ticket.json** - Small grocery transaction with low risk
2. **02_travel_high_value.json** - High-value travel transaction with premium characteristics
3. **03_cross_border.json** - Cross-border transaction with international characteristics
4. **04_device_mismatch_high_velocity.json** - Device location mismatch with high velocity patterns
5. **05_loyalty_gold_with_promo.json** - GOLD loyalty tier with promotional offers
6. **06_merchant_prefers_debit.json** - Transaction where merchant prefers debit cards
7. **07_high_risk_mcc.json** - Transaction with high-risk merchant category code
8. **08_missing_fields.json** - Transaction with missing or incomplete data fields
9. **09_issuer_affinity.json** - Transaction with strong issuer affinity patterns
10. **10_mixed_cart_large_amount.json** - Mixed cart with large total amount

## Snapshots

Each fixture has a corresponding snapshot file containing expected outputs:

- **p_approval** - Approval probability (0.0 to 1.0)
- **top_card** - Recommended card ID
- **utility** - Utility score for the top card
- **top_feature_drivers** - Top 4 feature contributions with descriptions
- **raw_score** - Raw scoring system score
- **calibration_method** - Calibration method used
- **risk_signals** - Boolean risk indicators

## Usage

### Running Tests

```bash
# Run all golden regression tests
python -m pytest tests/test_golden.py -v

# Run specific fixture test
python -m pytest tests/test_golden.py::test_01_grocery_small_ticket -v
```

### Updating Golden Snapshots

When the scoring logic changes and you want to update the expected outputs:

```bash
# Set environment variable to update snapshots
export UPDATE_GOLDEN=1
python -m pytest tests/test_golden.py

# Or run the test file directly
UPDATE_GOLDEN=1 python tests/test_golden.py
```

### Running Fast Unit Tests

```bash
# Run fast unit tests for core components
python -m pytest tests/test_fast_unit.py -v
```

## Test Categories

### Golden Regression Tests (`test_golden.py`)

- **Comprehensive Coverage**: Tests all major transaction types and edge cases
- **Deterministic**: Same inputs always produce same outputs
- **Snapshot-based**: Compares against expected outputs for regression detection
- **Updateable**: Can regenerate snapshots when logic changes

### Fast Unit Tests (`test_fast_unit.py`)

- **Calibration Monotonicity**: Ensures higher scores give higher probabilities
- **Preference Weights**: Validates loyalty tier and issuer affinity effects
- **Merchant Penalties**: Tests network preference and MCC penalty logic
- **Attribution Additivity**: Verifies feature contributions sum to total score

## Adding New Fixtures

To add a new test fixture:

1. Create a new JSON file in `fixtures/` with the naming pattern `XX_description.json`
2. Create a corresponding snapshot file in `snapshots/` with expected outputs
3. Add a test function in `test_golden.py` following the existing pattern
4. Update the main test runner if needed

## Validation Rules

The golden regression suite validates:

- **Approval Probability**: Must be between 0.0 and 1.0
- **Utility Scores**: Must be positive and reasonable
- **Feature Drivers**: Must sum to raw score (additivity)
- **Consistency**: Same inputs must produce same outputs
- **Monotonicity**: Higher scores must give higher probabilities
- **Bounds**: All values must stay within expected ranges

## Integration

The golden regression suite integrates with:

- **CI/CD Pipeline**: Automated testing on code changes
- **Development Workflow**: Local validation before commits
- **Release Process**: Final validation before deployments
- **Performance Monitoring**: Baseline for regression detection

## Troubleshooting

### Common Issues

1. **Snapshot Mismatches**: Run with `UPDATE_GOLDEN=1` to regenerate
2. **Import Errors**: Ensure all dependencies are installed
3. **Configuration Issues**: Check config files are present and valid
4. **Performance Issues**: Fast unit tests should complete in < 1 second

### Debugging

```bash
# Run with verbose output
python -m pytest tests/test_golden.py -v -s

# Run specific test with debug info
python -m pytest tests/test_golden.py::test_01_grocery_small_ticket -v -s --tb=short
```

## Contributing

When contributing to the golden regression suite:

1. **Add Tests**: Include tests for new functionality
2. **Update Snapshots**: Regenerate snapshots when logic changes
3. **Document Changes**: Update this README for new fixtures
4. **Validate**: Ensure all tests pass before submitting
