# AltWallet Merchant Agent - Complete Setup Script
# Run this script in Cursor's terminal on Windows PowerShell

Write-Host "🚀 AltWallet Merchant Agent - Complete Setup" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# Check if we're in the right directory
if (-not (Test-Path "pyproject.toml")) {
    Write-Host "❌ Error: pyproject.toml not found. Please run this script from the project root directory." -ForegroundColor Red
    exit 1
}

# Step 1: Create virtual environment
Write-Host "`n📦 Step 1: Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    Write-Host "   Virtual environment already exists. Removing old one..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force ".venv"
}

python -m venv .venv
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to create virtual environment" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ Virtual environment created successfully" -ForegroundColor Green

# Step 2: Activate virtual environment
Write-Host "`n🔧 Step 2: Activating virtual environment..." -ForegroundColor Yellow
& ".\.venv\Scripts\Activate.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to activate virtual environment" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ Virtual environment activated" -ForegroundColor Green

# Step 3: Upgrade pip
Write-Host "`n⬆️  Step 3: Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to upgrade pip" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ Pip upgraded successfully" -ForegroundColor Green

# Step 4: Install project in editable mode with dev dependencies
Write-Host "`n📥 Step 4: Installing project in editable mode..." -ForegroundColor Yellow
pip install -e ".[dev]"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install project" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ Project installed successfully" -ForegroundColor Green

# Step 5: Test CLI help
Write-Host "`n❓ Step 5: Testing CLI help..." -ForegroundColor Yellow
altwallet-merchant-agent --help
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ CLI help test failed" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ CLI help works correctly" -ForegroundColor Green

# Step 6: Test demo command
Write-Host "`n🎯 Step 6: Testing demo command..." -ForegroundColor Yellow
altwallet-merchant-agent demo -m "Whole Foods" -a 180 --json
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Demo command test failed" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ Demo command works correctly" -ForegroundColor Green

# Step 7: Run tests
Write-Host "`n🧪 Step 7: Running tests..." -ForegroundColor Yellow
python -m pytest tests/test_demo.py -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Tests failed" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ All tests passed" -ForegroundColor Green

Write-Host "`n🎉 Setup completed successfully!" -ForegroundColor Green
Write-Host "`n💡 Next steps:" -ForegroundColor Cyan
Write-Host "   - Activate the virtual environment: .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "   - Run the CLI: altwallet-merchant-agent --help" -ForegroundColor White
Write-Host "   - Run tests: python -m pytest tests/test_demo.py -v" -ForegroundColor White
Write-Host "`n⚠️  Note: Remember to activate the virtual environment in new terminal sessions!" -ForegroundColor Yellow
