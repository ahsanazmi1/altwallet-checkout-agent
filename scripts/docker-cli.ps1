# PowerShell script to run AltWallet Checkout Agent CLI in Docker

param(
    [string]$InputFile = "/data/context.json"
)

# Get version from VERSION file or use default
$VERSION = if (Test-Path "VERSION") { Get-Content "VERSION" } else { "0.1.0" }

Write-Host "Running AltWallet Checkout Agent CLI (version: $VERSION)"
Write-Host "Input file: $InputFile"

# Run CLI command
docker run --rm `
    -v "${PWD}/data:/data:ro" `
    altwallet/checkout-agent:${VERSION} `
    python -m altwallet_agent score --input "$InputFile"
