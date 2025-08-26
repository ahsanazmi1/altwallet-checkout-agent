# AltWallet Checkout Agent

AltWallet Checkout Agent is a production-ready Python application for Phase 1 (Core Engine MVP) of the checkout processing system. It provides a robust foundation for processing transactions, scoring, and providing card recommendations with a clean API and CLI interface.

**Current Version**: v0.1.0 — Core Engine (MVP)

## Features

- **Core Engine**: Transaction processing and scoring with structured logging
- **Deterministic Scoring v1**: Pure functions for risk assessment and loyalty boosts
- **FastAPI Integration**: RESTful API with automatic OpenAPI schema generation
- **CLI Interface**: Rich, user-friendly command-line interface with Typer
- **Data Validation**: Pydantic models for request/response validation
- **Structured Logging**: JSON logs with request/trace IDs via structlog
- **Testing**: Comprehensive test suite with pytest and golden tests
- **Docker Support**: Multi-stage build for production deployment
- **Development Tools**: Ruff (linting), Black (formatting), MyPy (typing)

## Quickstart

### Prerequisites

- Python 3.11+
- Git
- Docker (optional, for containerized deployment)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd altwallet-checkout-agent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate

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
```

## Usage

### CLI Commands

The AltWallet Checkout Agent provides a rich CLI interface:

```bash
# Show help
python -m altwallet_agent --help

# Show version information
python -m altwallet_agent version

# Score a transaction from file
python -m altwallet_agent score --file examples/context_basic.json

# Score with pretty output
python -m altwallet_agent score --file examples/context_basic.json --pretty

# Score with trace ID
python -m altwallet_agent score --file examples/context_basic.json --trace-id "trace_123"

# Process a checkout request
python -m altwallet_agent checkout --merchant-id "amazon" --amount 150.00
```

### API Endpoints

The FastAPI application provides RESTful endpoints:

```bash
# Start the API server (recommended method)
python scripts/start_api.py

# Alternative: Start with uvicorn directly (from project root)
python -m uvicorn altwallet_agent.api:app --host 0.0.0.0 --port 8000 --reload

# Health check
curl http://localhost:8000/health

# Score transaction
curl -X POST http://localhost:8000/score \
  -H "Content-Type: application/json" \
  -d @examples/context_basic.json

# Process checkout
curl -X POST http://localhost:8000/checkout \
  -H "Content-Type: application/json" \
  -d '{"merchant_id": "amazon", "amount": 150.00, "currency": "USD"}'

# Get OpenAPI schema
curl http://localhost:8000/openapi.json
```

### API Documentation

Once the server is running, you can access:
- **Interactive API docs**: http://localhost:8000/docs
- **ReDoc documentation**: http://localhost:8000/redoc
- **OpenAPI schema**: http://localhost:8000/openapi.json

## Development

### Project Structure

```
altwallet_agent/
├── src/altwallet_agent/          # Main package
│   ├── __init__.py              # Package exports
│   ├── api.py                   # FastAPI application
│   ├── cli.py                   # CLI interface with Typer
│   ├── core.py                  # Core CheckoutAgent logic
│   ├── models.py                # Pydantic data models
│   ├── scoring.py               # Deterministic scoring functions
│   ├── policy.py                # Risk weights and policy constants
│   └── __main__.py              # Module entry point
├── examples/                    # Example context files
│   ├── context_basic.json       # Basic transaction context
│   └── context_risky.json       # Risky transaction context
├── tests/                       # Test suite
│   ├── smoke_tests.py           # Basic functionality tests
│   ├── golden/                  # Golden tests for regression
│   │   ├── inputs/              # Test input files
│   │   ├── outputs/             # Expected output files
│   │   └── test_golden.py       # Golden test runner
│   └── data/                    # Test data files
├── docs/                        # Documentation
│   └── phase1_acceptance.md     # Phase 1 acceptance criteria
├── scripts/                     # Utility scripts
│   └── verify_phase1.py         # Phase 1 verification script
├── pyproject.toml               # Project configuration
├── Makefile                     # Unix/Linux development tasks
├── tasks.ps1                    # Windows PowerShell tasks
├── setup.ps1                    # Windows setup script
├── docker-compose.yml           # Docker Compose configuration
└── Dockerfile                   # Multi-stage Docker build
```

### Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run smoke tests only
python -m pytest tests/smoke_tests.py -v

# Run golden tests
python -m pytest tests/golden/test_golden.py -v

# Run with coverage
python -m pytest tests/ --cov=src/altwallet_agent --cov-report=html
```

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

### Build and Run

```bash
# Build the Docker image
docker build -t altwallet-agent:v0.1.0 .

# Run the container
docker run -p 8000:8000 altwallet-agent:v0.1.0

# Run with docker-compose
docker compose up --build
```

### Multi-stage Build

The Dockerfile uses a multi-stage build to create a minimal runtime image:
- **Builder stage**: Installs dependencies and builds the application
- **Runtime stage**: Creates a minimal image with only runtime dependencies

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

## Scoring System

The deterministic scoring system includes:

### Risk Factors
- **Location Mismatch**: Device location vs transaction location
- **High Velocity**: Multiple transactions in 24 hours
- **Chargebacks**: Historical chargeback count
- **High Value**: Transactions above threshold

### Loyalty Boosts
- **NONE**: 0.0 boost
- **SILVER**: 0.1 boost
- **GOLD**: 0.2 boost
- **PLATINUM**: 0.3 boost

### Routing Hints
- Merchant network preferences
- MCC-based routing
- Default to "any" network

## Phase 1 Status

✅ **COMPLETED** - Core Engine MVP (v0.1.0)

### Implemented Features
- ✅ Context ingestion with Pydantic models
- ✅ Deterministic scoring v1 with policy constants
- ✅ CLI with JSON output and trace-id support
- ✅ Structured logging with structlog
- ✅ Golden tests and smoke tests
- ✅ FastAPI application with OpenAPI
- ✅ Docker multi-stage build with docker-compose
- ✅ CI/CD with GitHub Actions
- ✅ Comprehensive documentation

### Next Phase (Phase 2)
- 🔄 Advanced scoring algorithms
- 🔄 Machine learning integration
- 🔄 Real-time processing
- 🔄 Enhanced monitoring and observability

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

MIT License - see LICENSE file for details.

## Troubleshooting

### Common Issues

**API Server Won't Start**
```bash
# Make sure you're in the project root directory
cd /path/to/altwallet-checkout-agent

# Ensure the package is installed
pip install -e .

# Try the startup script
python scripts/start_api.py
```

**Module Not Found Errors**
```bash
# Check if the package is properly installed
python -c "import altwallet_agent; print('OK')"

# Reinstall if needed
pip uninstall altwallet_agent
pip install -e .
```

**CLI Commands Not Working**
```bash
# Use the module syntax
python -m altwallet_agent version

# Instead of
altwallet_agent version  # This may not work
```

### Getting Help

For support and questions:
- Create an issue in the GitHub repository
- Check the [documentation](docs/phase1_acceptance.md)
- Review the [API documentation](http://localhost:8000/docs) when running locally
- Run the verification script: `python scripts/verify_phase1.py`
