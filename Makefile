# AltWallet Checkout Agent Makefile

.PHONY: help install lint test smoke run build-docker gen-openapi clean

# Default target
help:
	@echo "AltWallet Checkout Agent - Available commands:"
	@echo "  install      - Install dependencies"
	@echo "  lint         - Run linting (ruff, black, mypy)"
	@echo "  test         - Run all tests"
	@echo "  smoke        - Run smoke tests only"
	@echo "  run          - Run the API server"
	@echo "  build-docker - Build Docker image"
	@echo "  gen-openapi  - Generate OpenAPI schema"
	@echo "  clean        - Clean up generated files"

# Install dependencies
install:
	pip install -e .
	pip install -e ".[dev]"

# Run linting
lint:
	ruff check src/ tests/
	black --check src/ tests/
	mypy src/

# Format code
format:
	black src/ tests/
	ruff format src/ tests/

# Run all tests
test:
	pytest tests/ -v --cov=src/altwallet_agent --cov-report=term-missing

# Run smoke tests only
smoke:
	pytest tests/smoke_tests.py -v

# Run the API server
run:
	uvicorn altwallet_agent.api:app --host 0.0.0.0 --port 8000 --reload

# Build Docker image
build-docker:
	docker build -t altwallet-agent:latest .

# Generate OpenAPI schema
gen-openapi:
	python -c "import uvicorn; from altwallet_agent.api import app; import json; open('openapi.json', 'w').write(json.dumps(app.openapi(), indent=2))"

# Clean up generated files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -f .coverage
	rm -f openapi.json

# Development setup
dev-setup: install
	pre-commit install

# Run with specific config
run-dev:
	PYTHONPATH=src uvicorn altwallet_agent.api:app --host 0.0.0.0 --port 8000 --reload

# CLI commands
cli-checkout:
	PYTHONPATH=src altwallet-agent checkout --merchant-id test --amount 100.00

cli-score:
	PYTHONPATH=src altwallet-agent score --file tests/data/sample_transaction.json

# Docker run
docker-run:
	docker run -p 8000:8000 altwallet-agent:latest
