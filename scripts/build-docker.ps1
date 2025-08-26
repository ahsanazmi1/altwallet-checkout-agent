# PowerShell script to build Docker image for AltWallet Checkout Agent

param(
    [string]$Version = ""
)

# Get version from VERSION file if not provided
if (-not $Version) {
    if (Test-Path "VERSION") {
        $Version = Get-Content "VERSION" -Raw
        $Version = $Version.Trim()
    } else {
        $Version = "0.1.0"
    }
}

Write-Host "Building Docker image with version: $Version"

# Build the Docker image
docker build `
    --build-arg VERSION=$Version `
    -t altwallet/checkout-agent:$Version `
    -t altwallet/checkout-agent:latest `
    .

if ($LASTEXITCODE -eq 0) {
    Write-Host "Docker image built successfully!"
    Write-Host "Tags: altwallet/checkout-agent:$Version, altwallet/checkout-agent:latest"
} else {
    Write-Host "Docker build failed with exit code: $LASTEXITCODE"
    exit $LASTEXITCODE
}
