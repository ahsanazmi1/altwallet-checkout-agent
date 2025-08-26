# AltWallet Checkout Agent - PowerShell Tasks
# Usage: .\tasks.ps1 <command>

param(
    [Parameter(Position = 0)]
    [string]$Command = "help"
)

function Show-Help {
    Write-Host "AltWallet Checkout Agent - Available commands:" -ForegroundColor Cyan
    Write-Host "  install      - Install dependencies" -ForegroundColor White
    Write-Host "  lint         - Run linting (ruff, black, mypy)" -ForegroundColor White
    Write-Host "  format       - Format code" -ForegroundColor White
    Write-Host "  test         - Run all tests" -ForegroundColor White
    Write-Host "  smoke        - Run smoke tests only" -ForegroundColor White
    Write-Host "  run          - Run the API server" -ForegroundColor White
    Write-Host "  build-docker - Build Docker image" -ForegroundColor White
    Write-Host "  gen-openapi  - Generate OpenAPI schema" -ForegroundColor White
    Write-Host "  clean        - Clean up generated files" -ForegroundColor White
}

function Install-Dependencies {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -e .
    pip install -e ".[dev]"
    Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
}

function Invoke-Lint {
    Write-Host "Running linting..." -ForegroundColor Yellow
    ruff check src/ tests/
    if ($LASTEXITCODE -eq 0) {
        black --check src/ tests/
        if ($LASTEXITCODE -eq 0) {
            mypy src/
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Linting passed" -ForegroundColor Green
            }
            else {
                Write-Host "❌ MyPy failed" -ForegroundColor Red
                exit 1
            }
        }
        else {
            Write-Host "❌ Black check failed" -ForegroundColor Red
            exit 1
        }
    }
    else {
        Write-Host "❌ Ruff check failed" -ForegroundColor Red
        exit 1
    }
}

function Format-Code {
    Write-Host "Formatting code..." -ForegroundColor Yellow
    black src/ tests/
    ruff format src/ tests/
    Write-Host "✅ Code formatted successfully" -ForegroundColor Green
}

function Invoke-Tests {
    Write-Host "Running all tests..." -ForegroundColor Yellow
    python -m pytest tests/ -v --cov=src/altwallet_agent --cov-report=term-missing
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ All tests passed" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Tests failed" -ForegroundColor Red
        exit 1
    }
}

function Invoke-SmokeTests {
    Write-Host "Running smoke tests..." -ForegroundColor Yellow
    python -m pytest tests/smoke_tests.py -v
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Smoke tests passed" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Smoke tests failed" -ForegroundColor Red
        exit 1
    }
}

function Start-Server {
    Write-Host "Starting API server..." -ForegroundColor Yellow
    uvicorn altwallet_agent.api:app --host 0.0.0.0 --port 8080 --reload
}

function Build-Docker {
    Write-Host "Building Docker image..." -ForegroundColor Yellow
    docker build -t altwallet-agent:latest .
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker image built successfully" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Docker build failed" -ForegroundColor Red
        exit 1
    }
}

function Generate-OpenAPI {
    Write-Host "Generating OpenAPI schema..." -ForegroundColor Yellow
    python -c "import uvicorn; from altwallet_agent.api import app; import json; import os; os.makedirs('openapi', exist_ok=True); open('openapi/openapi.json', 'w').write(json.dumps(app.openapi(), indent=2))"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ OpenAPI schema generated successfully" -ForegroundColor Green
    }
    else {
        Write-Host "❌ OpenAPI generation failed" -ForegroundColor Red
        exit 1
    }
}

function Clean-Project {
    Write-Host "Cleaning up generated files..." -ForegroundColor Yellow
    Get-ChildItem -Recurse -Include "*.pyc" | Remove-Item -Force
    Get-ChildItem -Recurse -Include "__pycache__" -Directory | Remove-Item -Recurse -Force
    Get-ChildItem -Recurse -Include "*.egg-info" -Directory | Remove-Item -Recurse -Force
    if (Test-Path ".pytest_cache") { Remove-Item -Recurse -Force ".pytest_cache" }
    if (Test-Path "htmlcov") { Remove-Item -Recurse -Force "htmlcov" }
    if (Test-Path ".coverage") { Remove-Item -Force ".coverage" }
    if (Test-Path "openapi") { Remove-Item -Recurse -Force "openapi" }
    Write-Host "✅ Cleanup completed" -ForegroundColor Green
}

# Main command dispatcher
switch ($Command.ToLower()) {
    "help" { Show-Help }
    "install" { Install-Dependencies }
    "lint" { Invoke-Lint }
    "format" { Format-Code }
    "test" { Invoke-Tests }
    "smoke" { Invoke-SmokeTests }
    "run" { Start-Server }
    "build-docker" { Build-Docker }
    "gen-openapi" { Generate-OpenAPI }
    "clean" { Clean-Project }
    default {
        Write-Host "Unknown command: $Command" -ForegroundColor Red
        Show-Help
        exit 1
    }
}
