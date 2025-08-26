#!/bin/bash
# Bash script to build Docker image for AltWallet Checkout Agent

set -e

# Get version from VERSION file or use default
VERSION=${1:-$(cat VERSION 2>/dev/null || echo "0.1.0")}

echo "Building Docker image with version: $VERSION"

# Build the Docker image
docker build \
    --build-arg VERSION="$VERSION" \
    -t altwallet/checkout-agent:"$VERSION" \
    -t altwallet/checkout-agent:latest \
    .

echo "Docker image built successfully!"
echo "Tags: altwallet/checkout-agent:$VERSION, altwallet/checkout-agent:latest"
