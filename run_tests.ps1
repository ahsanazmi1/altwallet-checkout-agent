# AltWallet Merchant Agent - Test Runner Script
# Run this script in Cursor's terminal on Windows PowerShell

Write-Host "🧪 AltWallet Merchant Agent - Test Runner" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan

# Check if we're in the right directory
if (-not (Test-Path "pyproject.toml")) {
    Write-Host "❌ Error: pyproject.toml not found. Please run this script from the project root directory." -ForegroundColor Red
    exit 1
}

# Install dependencies if needed
Write-Host "📦 Installing development dependencies..." -ForegroundColor Yellow
pip install -e ".[dev]" --quiet

# Run all tests
Write-Host "`n🚀 Running all tests..." -ForegroundColor Green
python -m pytest tests/test_demo.py -v

# Run demo command tests specifically
Write-Host "`n🎯 Running demo command tests..." -ForegroundColor Green
python -m pytest tests/test_demo.py::TestDemoCommand -v

# Run the specific context creation test
Write-Host "`n🔍 Running context creation test..." -ForegroundColor Green
python -m pytest tests/test_demo.py::TestDemoCommand::test_demo_context_creation -v

# Run deterministic scores test
Write-Host "`n🎲 Running deterministic scores test..." -ForegroundColor Green
python -m pytest tests/test_demo.py::TestDemoCommand::test_deterministic_scores -v

Write-Host "`n✅ All tests completed!" -ForegroundColor Green
Write-Host "`n💡 Tip: Use 'python -m pytest tests/test_demo.py -v' to run all tests with verbose output" -ForegroundColor Cyan
