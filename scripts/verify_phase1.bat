@echo off
REM Phase 1 Verification Script for Windows
REM Run this to verify all Phase 1 requirements are met

echo Running AltWallet Checkout Agent Phase 1 Verification...
python scripts\verify_phase1.py

REM Check the exit code
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ All Phase 1 requirements PASSED
    exit /b 0
) else (
    echo.
    echo ❌ Some Phase 1 requirements FAILED
    exit /b 1
)
