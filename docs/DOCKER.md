# Docker Usage

This document describes how to use the AltWallet Checkout Agent with Docker.

## Quick Start

### Build the Docker Image

```bash
# Build with version from VERSION file
make build-docker

# Or build with specific version
VERSION=0.1.0 make build-docker
```

### Run the API Server

```bash
# Using docker-compose (recommended)
docker-compose up -d

# Or using docker run
docker run -p 8080:8080 altwallet/checkout-agent:0.1.0
```

The API will be available at `http://localhost:8080`

### Run CLI Commands

```bash
# Using the provided script (Linux/Mac)
./scripts/docker-cli.sh

# Using PowerShell (Windows)
.\scripts\docker-cli.ps1

# Or manually with docker run
docker run --rm \
  -v "$(pwd)/data:/data:ro" \
  altwallet/checkout-agent:0.1.0 \
  python -m altwallet_agent score --input /data/context.json
```

## Docker Compose

The `docker-compose.yml` file provides a complete setup for the API service:

```yaml
services:
  altwallet-agent-api:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        VERSION: ${VERSION:-0.1.0}
    image: altwallet/checkout-agent:${VERSION:-0.1.0}
    ports:
      - "8080:8080"
    volumes:
      - ./data:/data:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Commands

```bash
# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down

# Rebuild and start
docker-compose up --build -d
```

## Multi-Stage Build

The Dockerfile uses a multi-stage build approach:

1. **Build Stage**: Installs all dependencies in a virtual environment
2. **Runtime Stage**: Creates a slim runtime image with only the necessary components

This approach results in a smaller final image and better security.

## Image Labels

The Docker image includes Open Container Initiative (OCI) labels:

- `org.opencontainers.image.version`: Version from VERSION file
- `org.opencontainers.image.title`: "AltWallet Checkout Agent"
- `org.opencontainers.image.description`: Description of the application
- `org.opencontainers.image.vendor`: "AltWallet"
- `org.opencontainers.image.source`: GitHub repository URL

## Security Features

- Non-root user (`appuser`)
- Minimal runtime dependencies
- Read-only data volume mounts
- Health checks
- Proper signal handling

## Data Directory

The container expects input files to be mounted at `/data`. Create a `data` directory in your project root:

```bash
mkdir -p data
# Place your context.json files in the data directory
```

## Environment Variables

- `PYTHONPATH`: Set to `/app/src` for proper module resolution
- `PYTHONUNBUFFERED`: Set to `1` for immediate log output
- `PYTHONDONTWRITEBYTECODE`: Set to `1` to avoid writing .pyc files

## Troubleshooting

### Health Check Failures

If the health check fails, check if the API is responding:

```bash
curl http://localhost:8080/health
```

### Permission Issues

If you encounter permission issues with mounted volumes, ensure the data directory has proper permissions:

```bash
chmod 755 data/
```

### Build Issues

If the build fails, try cleaning up Docker cache:

```bash
docker system prune -a
make build-docker
```
