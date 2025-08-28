# AltWallet Checkout Agent

AltWallet Checkout Agent is a production-minded Python scaffold for intelligent checkout processing and card recommendations. It provides a robust foundation for processing transactions, scoring, and providing intelligent card recommendations with a clean API and CLI interface.

## What's New in Phase 2

Phase 2 introduces intelligent decision-making capabilities that build upon the solid foundation established in Phase 1:

### 🧠 Core Intelligence Engine
- **Main Orchestrator**: `IntelligenceEngine` class coordinates all intelligence components
- **Multi-factor Processing**: Risk assessment, transaction scoring, and smart recommendations
- **Performance Optimization**: Processing time tracking and optimization strategies
- **Error Handling**: Graceful fallback to basic processing on intelligence failures

### 📊 Comprehensive Data Layer
- **Card Database**: 7 major credit cards with detailed rewards structures
- **Category System**: Merchant categorization with 7 major categories
- **Risk Patterns**: Known risk patterns for fraud detection
- **Reward Calculations**: Dynamic reward rate calculations based on merchant categories

### 🏪 Smart Merchant Analysis
- **Category Detection**: Automatic merchant categorization based on merchant IDs
- **Risk Assessment**: Multi-level risk scoring (low, medium, high)
- **Behavior Patterns**: Detection of online-only, subscription, marketplace patterns
- **Optimal Card Matching**: Context-aware card recommendations

### 🎯 Enhanced Processing Logic
- **Risk Scoring**: Weighted risk factors based on amount, merchant, and currency
- **Transaction Scoring**: Multi-factor scoring with amount bonuses and merchant bonuses
- **Intelligent Recommendations**: Context-aware card suggestions with reasoning
- **Confidence Scoring**: Confidence levels for all recommendations

## Features

- **Core Engine**: Transaction processing and scoring with structured logging
- **Intelligence Layer**: Smart risk assessment and card recommendations
- **Approval Scoring**: Two-stage approval-odds system (rules → calibrator)
- **Composite Utility**: Multi-factor utility computation for optimal card ranking
- **Explainability**: Detailed feature attributions and audit trails
- **FastAPI Integration**: RESTful API with automatic OpenAPI schema generation
- **CLI Interface**: Rich, user-friendly command-line interface with Typer
- **Data Validation**: Pydantic models for request/response validation
- **Structured Logging**: JSON logs with request/trace IDs via structlog
- **Testing**: Comprehensive test suite with pytest and golden tests
- **Docker Support**: Multi-stage build for production deployment
- **Development Tools**: Ruff (linting), Black (formatting), MyPy (typing)

## How Approval Odds Work

The approval system uses a two-stage approach:

### 1. Rules Layer
Combines deterministic signals into a raw log-odds score:
- **MCC-based weights**: Different merchant categories have different risk profiles
- **Amount-based weights**: Higher amounts generally increase risk
- **Velocity patterns**: Transaction frequency analysis
- **Location factors**: Cross-border and device location mismatch
- **Customer factors**: Loyalty tier and chargeback history

### 2. Calibration Layer
Maps raw scores to probabilities using configurable calibration methods:
- **Logistic (Platt) Calibration**: Default method using `p_approval = 1 / (1 + exp(-(scale * raw_score + bias)))`
- **Isotonic Calibration**: Placeholder for future learned calibration
- **Probability Clamping**: Configurable bounds (default: 0.01 to 0.99)

### Example Configuration
```yaml
rules_layer:
  mcc_weights:
    "7995": -2.5  # Gambling (high risk)
    "5411": 0.2   # Grocery stores (low risk)
  amount_weights:
    "0-10": 0.3
    "100-500": -0.2
    "5000+": -2.0

calibration_layer:
  method: "logistic"
  logistic:
    bias: 0.0
    scale: 1.0
```

## How Utility is Computed

The composite utility formula combines four key components:

```
utility = p_approval × expected_rewards × preference_weight × merchant_penalty
```

### Components

1. **p_approval**: Probability of card approval (0.0 to 1.0)
2. **expected_rewards**: Expected rewards multiplier (e.g., 0.05 = 5% rewards)
3. **preference_weight**: User preference weight (0.5 to 1.5)
4. **merchant_penalty**: Merchant-specific penalty (0.8 to 1.0)

### Expected Rewards Calculation
- Base cashback/points rate
- Category bonuses (MCC-based multipliers)
- Signup bonuses (if eligible)
- Capped at 10% maximum

### Preference Weight
- User preference adjustments (cashback vs points, issuer affinity)
- Loyalty tier multipliers
- Category boost effects
- Seasonal promotions

### Merchant Penalty
- Merchant-specific penalties
- MCC family fallbacks
- Network preference penalties
- Fuzzy merchant matching

## How Explainability Works

The system provides comprehensive explainability through:

### Feature Attributions
- **Baseline**: Base score contribution from configuration
- **Contributions**: List of all feature contributions to the score
- **Top Drivers**: Top 3 positive and negative feature drivers
- **Calibration Info**: Method and parameters used for probability calculation

### Audit Information
- **Config Versions**: Version indicators for configuration files
- **Code Version**: Git SHA of deployed code
- **Request ID**: Unique UUID for request tracing
- **Latency**: Processing time in milliseconds

### Example Explainability Output
```json
{
  "explainability": {
    "baseline": 0.0,
    "contributions": [
      {
        "feature": "loyalty_tier",
        "value": 0.5,
        "impact": "positive"
      },
      {
        "feature": "cross_border",
        "value": -1.0,
        "impact": "negative"
      }
    ],
    "top_drivers": {
      "positive": [
        {
          "feature": "loyalty_tier",
          "value": 0.5,
          "magnitude": 0.5
        }
      ],
      "negative": [
        {
          "feature": "cross_border",
          "value": -1.0,
          "magnitude": 1.0
        }
      ]
    }
  }
}
```

## Quickstart

### CLI Quickstart

```bash
# Install the package
pip install -e .

# Basic checkout processing
altwallet_agent checkout --merchant-id "amazon" --amount 150.00

# Score a transaction from file
altwallet_agent score --input examples/context_basic.json

# Show help
altwallet_agent --help
```

### API Quickstart

```bash
# Start the API server
uvicorn src.altwallet_agent.api:app --host 0.0.0.0 --port 8000 --reload

# Health check
curl http://localhost:8000/health

# Process checkout
curl -X POST http://localhost:8000/checkout \
  -H "Content-Type: application/json" \
  -d '{"merchant_id": "amazon", "amount": 150.00, "currency": "USD"}'

# Interactive API docs
open http://localhost:8000/docs
```

### Installation

```bash
# Install in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

### Windows Setup

For Windows users, use the provided PowerShell scripts:

```powershell
# Complete setup (creates virtual environment, installs dependencies, runs tests)
.\setup.ps1

# Common development tasks
.\tasks.ps1 help          # Show available commands
.\tasks.ps1 install       # Install dependencies
.\tasks.ps1 test          # Run all tests
.\tasks.ps1 run           # Start API server
```

### Unix/Linux Setup

For Unix/Linux users, use the Makefile:

```bash
# Show available commands
make help

# Install dependencies
make install

# Run tests
make test

# Start API server
make run

# Build Docker image
make build-docker

# Run with Docker Compose
docker-compose up -d
```

## Example Contexts and Expected Outputs

### Example 1: Basic Grocery Transaction

**Input Context** (`examples/context_basic.json`):
```json
{
    "cart": {
        "items": [
            {
                "item": "Grocery Items",
                "unit_price": "45.99",
                "qty": 1,
                "mcc": "5411",
                "merchant_category": "Grocery Stores"
            }
        ],
        "currency": "USD"
    },
    "merchant": {
        "name": "Local Grocery Store",
        "mcc": "5411",
        "network_preferences": [],
        "location": {
            "city": "New York",
            "country": "US"
        }
    },
    "customer": {
        "id": "customer_12345",
        "loyalty_tier": "SILVER",
        "historical_velocity_24h": 3,
        "chargebacks_12m": 0
    },
    "device": {
        "ip": "192.168.1.100",
        "device_id": "device_abc123",
        "ip_distance_km": 0.5,
        "location": {
            "city": "New York",
            "country": "US"
        }
    },
    "geo": {
        "city": "New York",
        "region": "NY",
        "country": "US",
        "lat": 40.7128,
        "lon": -74.0060
    }
}
```

**Expected Output** (abridged):
```json
{
    "transaction_id": "uuid-1234-5678",
    "score": 0.85,
    "status": "completed",
    "recommendations": [
        {
            "card_id": "amex_gold",
            "card_name": "American Express Gold",
            "rank": 1,
            "p_approval": 0.92,
            "expected_rewards": 0.04,
            "utility": 0.88,
            "explainability": {
                "baseline": 0.0,
                "contributions": [
                    {"feature": "mcc", "value": 0.2, "impact": "positive"},
                    {"feature": "amount", "value": 0.1, "impact": "positive"}
                ],
                "top_drivers": {
                    "positive": [
                        {"feature": "mcc", "value": 0.2, "magnitude": 0.2}
                    ],
                    "negative": []
                }
            },
            "audit": {
                "request_id": "uuid-1234-5678",
                "code_version": "a1b2c3d4",
                "latency_ms": 45
            }
        }
    ]
}
```

### Example 2: Risky Electronics Transaction

**Input Context** (`examples/context_risky.json`):
```json
{
    "cart": {
        "items": [
            {
                "item": "High-End Electronics",
                "unit_price": "899.99",
                "qty": 1,
                "mcc": "5732",
                "merchant_category": "Electronics Stores"
            }
        ],
        "currency": "USD"
    },
    "merchant": {
        "name": "Electronics Store",
        "mcc": "5732",
        "network_preferences": [],
        "location": {
            "city": "Los Angeles",
            "country": "US"
        }
    },
    "customer": {
        "id": "customer_67890",
        "loyalty_tier": "NONE",
        "historical_velocity_24h": 15,
        "chargebacks_12m": 2
    },
    "device": {
        "ip": "192.168.1.200",
        "device_id": "device_def456",
        "ip_distance_km": 3500.0,
        "location": {
            "city": "New York",
            "country": "US"
        }
    },
    "geo": {
        "city": "Los Angeles",
        "region": "CA",
        "country": "US",
        "lat": 34.0522,
        "lon": -118.2437
    }
}
```

**Expected Output** (abridged):
```json
{
    "transaction_id": "uuid-5678-9abc",
    "score": 0.35,
    "status": "completed",
    "recommendations": [
        {
            "card_id": "chase_freedom_unlimited",
            "card_name": "Chase Freedom Unlimited",
            "rank": 1,
            "p_approval": 0.45,
            "expected_rewards": 0.015,
            "utility": 0.32,
            "explainability": {
                "baseline": 0.0,
                "contributions": [
                    {"feature": "amount", "value": -0.5, "impact": "negative"},
                    {"feature": "location_mismatch_distance", "value": -1.0, "impact": "negative"},
                    {"feature": "chargebacks_12m", "value": -0.3, "impact": "negative"}
                ],
                "top_drivers": {
                    "positive": [],
                    "negative": [
                        {"feature": "location_mismatch_distance", "value": -1.0, "magnitude": 1.0},
                        {"feature": "amount", "value": -0.5, "magnitude": 0.5}
                    ]
                }
            },
            "audit": {
                "request_id": "uuid-5678-9abc",
                "code_version": "a1b2c3d4",
                "latency_ms": 52
            }
        }
    ]
}
```

## Running the Regression Suite

The golden regression test suite ensures scoring consistency across changes:

### Run All Regression Tests
```bash
# Run all golden regression tests
python -m pytest tests/test_golden.py -v

# Run specific fixture test
python -m pytest tests/test_golden.py::test_01_grocery_small_ticket -v
```

### Update Golden Snapshots
When scoring logic changes and you want to update expected outputs:
```bash
# Set environment variable to update snapshots
export UPDATE_GOLDEN=1
python -m pytest tests/test_golden.py

# Or run the test file directly
UPDATE_GOLDEN=1 python tests/test_golden.py
```

### Fast Unit Tests
```bash
# Run fast unit tests for core components
python -m pytest tests/test_fast_unit.py -v
```

### Smoke Tests
```bash
# Run basic smoke tests
python -m pytest tests/smoke_tests.py::test_agent_initialization -v
python -m pytest tests/smoke_tests.py::test_checkout_processing -v
python -m pytest tests/smoke_tests.py::test_transaction_scoring -v

# Test CLI functionality
python -m pytest tests/smoke_tests.py::test_cli_with_context_basic -v

# Test API endpoints
python -m pytest tests/smoke_tests.py::test_api_health_check -v

# Run all smoke tests at once
python -m pytest tests/smoke_tests.py -v
```

## API Documentation

### Interactive API Docs
Once the server is running, you can access:
- **Interactive API docs**: http://localhost:8000/docs
- **ReDoc documentation**: http://localhost:8000/redoc
- **OpenAPI schema**: http://localhost:8000/openapi.json

### OpenAPI Specification
The complete OpenAPI 3.0.3 specification is available at:
- **Specification**: [openapi/openapi.yaml](openapi/openapi.yaml)
- **Documentation**: [openapi/README.md](openapi/README.md)

### Key Endpoints
- **POST /v1/score**: Process checkout and return card recommendations
- **POST /v1/explain**: Get detailed feature attributions
- **GET /v1/healthz**: Health check endpoint
- **GET /v1/version**: Version information

## Usage

### CLI Commands

The AltWallet Checkout Agent provides a rich CLI interface:

```bash
# Show help
altwallet_agent --help

# Process a checkout request
altwallet_agent checkout --merchant-id "amazon" --amount 150.00

# Score a transaction from file
altwallet_agent score --file tests/data/sample_transaction.json

# Show version information
altwallet_agent version
```

### API Endpoints

The FastAPI application provides RESTful endpoints:

```bash
# Start the API server
uvicorn altwallet_agent.api:app --host 0.0.0.0 --port 8000 --reload

# Health check
curl http://localhost:8000/health

# Process checkout
curl -X POST http://localhost:8000/checkout \
  -H "Content-Type: application/json" \
  -d '{"merchant_id": "amazon", "amount": 150.00, "currency": "USD"}'

# Score transaction
curl -X POST http://localhost:8000/score \
  -H "Content-Type: application/json" \
  -d '{"transaction_data": {"amount": 150, "merchant": "amazon"}}'

# Get OpenAPI schema
curl http://localhost:8000/openapi.json
```

## Development

### Project Structure

```
altwallet_agent/
├── src/altwallet_agent/          # Main package
│   ├── __init__.py              # Package exports
│   ├── api.py                   # FastAPI application
│   ├── cli.py                   # CLI interface with Typer
│   ├── core.py                  # Core CheckoutAgent logic
│   ├── intelligence/            # Phase 2 intelligence layer
│   │   ├── engine.py           # Main intelligence orchestrator
│   │   └── processing/         # Processing components
│   ├── approval_scorer.py      # Two-stage approval scoring
│   ├── composite_utility.py    # Multi-factor utility computation
│   ├── preference_weighting.py # User preference weighting
│   ├── merchant_penalty.py     # Merchant penalty calculations
│   └── models.py               # Pydantic data models
├── tests/                       # Test suite
│   ├── smoke_tests.py          # Basic functionality tests
│   ├── golden/                 # Golden tests for regression
│   └── data/                   # Test data files
├── config/                      # Configuration files
│   ├── approval.yaml           # Approval scoring config
│   ├── preferences.yaml        # Preference weighting config
│   └── merchant_penalties.yaml # Merchant penalty config
├── examples/                    # Example contexts and demos
├── pyproject.toml              # Project configuration
├── Makefile                    # Unix/Linux development tasks
├── tasks.ps1                   # Windows PowerShell tasks
├── setup.ps1                   # Windows setup script
└── Dockerfile                  # Multi-stage Docker build
```

### Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run smoke tests only
python -m pytest tests/smoke_tests.py -v

# Run with coverage
python -m pytest tests/ --cov=src/altwallet_agent --cov-report=html
```

**Smoke Test Checklist:**
- [ ] Agent initializes correctly
- [ ] Checkout processing works
- [ ] Transaction scoring works
- [ ] CLI commands execute successfully
- [ ] API endpoints respond correctly

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

## Docker

### Quick Start

```bash
# Build the Docker image
make build-docker

# Run with Docker Compose (recommended)
docker-compose up -d

# Or run directly
docker run -p 8080:8080 altwallet/checkout-agent:0.1.0
```

### Docker Usage

**Build and run the API server:**
```bash
# Build image
docker build -t altwallet/checkout-agent:latest .

# Run API server
docker run -p 8000:8000 altwallet/checkout-agent:latest

# Run with environment variables
docker run -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e LOG_LEVEL=INFO \
  altwallet/checkout-agent:latest
```

**Run CLI commands with Docker:**
```bash
# Score a transaction
docker run --rm \
  -v "$(pwd)/examples:/data:ro" \
  altwallet/checkout-agent:latest \
  altwallet_agent score --input /data/context_basic.json

# Process checkout
docker run --rm \
  altwallet/checkout-agent:latest \
  altwallet_agent checkout --merchant-id "amazon" --amount 150.00
```

**Development with Docker Compose:**
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### CLI Usage

```bash
# Run CLI commands with Docker
./scripts/docker-cli.sh

# Or manually
docker run --rm \
  -v "$(pwd)/data:/data:ro" \
  altwallet/checkout-agent:0.1.0 \
  python -m altwallet_agent score --input /data/context.json
```

### Multi-stage Build

The Dockerfile uses a multi-stage build to create a minimal runtime image:
- **Build stage**: Installs dependencies in a virtual environment
- **Runtime stage**: Creates a slim image with only runtime dependencies

### Features

- **OCI Labels**: Proper container labels with version information
- **Security**: Non-root user, minimal dependencies
- **Health Checks**: Built-in health monitoring
- **Volume Mounts**: Read-only data directory for input files

For detailed Docker usage, see [docs/DOCKER.md](docs/DOCKER.md).

## Configuration

The agent can be configured through environment variables or configuration files:

```bash
# Environment variables
export ENVIRONMENT=production
export LOG_LEVEL=INFO
export API_HOST=0.0.0.0
export API_PORT=8000
```

## Logging

The application uses structured logging with JSON format and includes:
- Request/trace IDs for correlation
- Timestamp in ISO format
- Log levels and context information
- Exception details with stack traces

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details.
