@echo off
REM AltWallet Merchant Agent - Complete Setup Script (Batch)
REM Run this script in Cursor's terminal on Windows

echo 🚀 AltWallet Merchant Agent - Complete Setup
echo =============================================

REM Check if we're in the right directory
if not exist "pyproject.toml" (
    echo ❌ Error: pyproject.toml not found. Please run this script from the project root directory.
    exit /b 1
)

REM Step 1: Create virtual environment
echo.
echo 📦 Step 1: Creating virtual environment...
if exist ".venv" (
    echo    Virtual environment already exists. Removing old one...
    rmdir /s /q ".venv"
)

python -m venv .venv
if errorlevel 1 (
    echo ❌ Failed to create virtual environment
    exit /b 1
)
echo    ✅ Virtual environment created successfully

REM Step 2: Activate virtual environment
echo.
echo 🔧 Step 2: Activating virtual environment...
call .\.venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    exit /b 1
)
echo    ✅ Virtual environment activated

REM Step 3: Upgrade pip
echo.
echo ⬆️  Step 3: Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo ❌ Failed to upgrade pip
    exit /b 1
)
echo    ✅ Pip upgraded successfully

REM Step 4: Install project in editable mode with dev dependencies
echo.
echo 📥 Step 4: Installing project in editable mode...
pip install -e ".[dev]"
if errorlevel 1 (
    echo ❌ Failed to install project
    exit /b 1
)
echo    ✅ Project installed successfully

REM Step 5: Test CLI help
echo.
echo ❓ Step 5: Testing CLI help...
altwallet-merchant-agent --help
if errorlevel 1 (
    echo ❌ CLI help test failed
    exit /b 1
)
echo    ✅ CLI help works correctly

REM Step 6: Test demo command
echo.
echo 🎯 Step 6: Testing demo command...
altwallet-merchant-agent demo -m "Whole Foods" -a 180 --json
if errorlevel 1 (
    echo ❌ Demo command test failed
    exit /b 1
)
echo    ✅ Demo command works correctly

REM Step 7: Run tests
echo.
echo 🧪 Step 7: Running tests...
python -m pytest tests/test_demo.py -v
if errorlevel 1 (
    echo ❌ Tests failed
    exit /b 1
)
echo    ✅ All tests passed

echo.
echo 🎉 Setup completed successfully!
echo.
echo 💡 Next steps:
echo    - Activate the virtual environment: .\.venv\Scripts\activate.bat
echo    - Run the CLI: altwallet-merchant-agent --help
echo    - Run tests: python -m pytest tests/test_demo.py -v
echo.
echo ⚠️  Note: Remember to activate the virtual environment in new terminal sessions!
pause
