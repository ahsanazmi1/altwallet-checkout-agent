# AltWallet Checkout Agent

AltWallet Checkout Agent is a production-minded Python scaffold for Phase 1 (Core Engine MVP) of the checkout processing system. It provides a robust foundation for processing transactions, scoring, and providing card recommendations with a clean API and CLI interface.

## Features

- **Core Engine**: Transaction processing and scoring with structured logging
- **FastAPI Integration**: RESTful API with automatic OpenAPI schema generation
- **CLI Interface**: Rich, user-friendly command-line interface with Typer
- **Data Validation**: Pydantic models for request/response validation
- **Structured Logging**: JSON logs with request/trace IDs via structlog
- **Testing**: Comprehensive test suite with pytest and golden tests
- **Docker Support**: Multi-stage build for production deployment
- **Development Tools**: Ruff (linting), Black (formatting), MyPy (typing)

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
│   └── models.py                # Pydantic data models
├── tests/                       # Test suite
│   ├── smoke_tests.py           # Basic functionality tests
│   ├── golden/                  # Golden tests for regression
│   └── data/                    # Test data files
├── pyproject.toml               # Project configuration
├── Makefile                     # Unix/Linux development tasks
├── tasks.ps1                    # Windows PowerShell tasks
├── setup.ps1                    # Windows setup script
└── Dockerfile                   # Multi-stage Docker build
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

### Smoke Tests

Quick verification that the core functionality works:

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

## Phase 1 TODOs

The following items are marked as TODOs for Phase 1 implementation:

### Core Engine
- [ ] Implement actual checkout processing logic in `CheckoutAgent.process_checkout()`
- [ ] Implement actual scoring logic in `CheckoutAgent.score_transaction()`
- [ ] Add card recommendation algorithms
- [ ] Integrate with external payment processors

### API Enhancements
- [ ] Add authentication and authorization
- [ ] Implement rate limiting
- [ ] Add request/response middleware
- [ ] Add metrics and monitoring endpoints

### Data Models
- [ ] Add more comprehensive transaction models
- [ ] Implement card database integration
- [ ] Add user preference models
- [ ] Add merchant category models

### Testing
- [ ] Add integration tests
- [ ] Add performance tests
- [ ] Add security tests
- [ ] Expand golden test coverage

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details.
