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

# Run golden tests only
golden:
	pytest tests/golden/test_golden_scoring.py -v

# Run the API server
run:
	uvicorn altwallet_agent.api:app --host 0.0.0.0 --port 8080 --reload

# Read version from VERSION file
VERSION := $(shell cat VERSION 2>/dev/null || echo "0.1.0")

# Build Docker image
build-docker:
	docker build \
		--build-arg VERSION=$(VERSION) \
		-t altwallet/checkout-agent:$(VERSION) \
		-t altwallet/checkout-agent:latest \
		.

# Build Docker image (Windows PowerShell alternative)
build-docker-ps:
	powershell -ExecutionPolicy Bypass -File scripts/build-docker.ps1

# Generate OpenAPI schema
gen-openapi:
	python -c "import uvicorn; from altwallet_agent.api import app; import json; import os; os.makedirs('openapi', exist_ok=True); open('openapi/openapi.json', 'w').write(json.dumps(app.openapi(), indent=2))"

# Clean up generated files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -f .coverage
	rm -rf openapi/

# Development setup
dev-setup: install
	pre-commit install

# Run with specific config
run-dev:
	PYTHONPATH=src uvicorn altwallet_agent.api:app --host 0.0.0.0 --port 8080 --reload

# CLI commands
cli-checkout:
	PYTHONPATH=src altwallet-agent checkout --merchant-id test --amount 100.00

cli-score:
	PYTHONPATH=src altwallet-agent score --file tests/data/sample_transaction.json

# Docker run
docker-run:
	docker run -p 8000:8000 altwallet-agent:latest
