#!/bin/bash
# Script to run AltWallet Checkout Agent CLI in Docker

set -e

# Default values
VERSION=${VERSION:-$(cat VERSION 2>/dev/null || echo "0.1.0")}
INPUT_FILE=${1:-/data/context.json}

echo "Running AltWallet Checkout Agent CLI (version: $VERSION)"
echo "Input file: $INPUT_FILE"

# Run CLI command
docker run --rm \
  -v "$(pwd)/data:/data:ro" \
  altwallet/checkout-agent:${VERSION} \
  python -m altwallet_agent score --input "$INPUT_FILE"
