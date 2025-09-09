# Multi-stage Dockerfile for Orca Checkout Agent
# Stage 1: Build stage with pinned dependencies
FROM python:3.11-slim as build

# Build arguments
ARG VERSION=0.1.0

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.11-slim as runtime

# Build arguments
ARG VERSION=0.1.0

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Copy virtual environment from build stage
COPY --from=build /opt/venv /opt/venv

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create app directory
WORKDIR /app

# Copy application code
COPY src/ ./src/
COPY pyproject.toml .

# Install the application in development mode
RUN pip install -e .

# Create data directory for input files
RUN mkdir -p /data && chown -R appuser:appuser /data

# Switch to non-root user
USER appuser

# Expose port for API
EXPOSE 8080

# Add labels
LABEL org.opencontainers.image.version="${VERSION}" \
    org.opencontainers.image.title="orca-checkout" \
    org.opencontainers.image.description="Orca Checkout Agent - Intelligent payment processing and card recommendations" \
    org.opencontainers.image.vendor="Orca" \
    org.opencontainers.image.source="https://github.com/orca/checkout-agent" \
    org.opencontainers.image.url="https://github.com/orca/checkout-agent" \
    org.opencontainers.image.documentation="https://github.com/orca/checkout-agent/blob/main/README.md" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.created="${BUILD_DATE}" \
    org.opencontainers.image.revision="${GIT_COMMIT}" \
    com.orca.service="checkout-agent" \
    com.orca.version="${VERSION}" \
    com.orca.component="api"

# Default command (can be overridden)
CMD ["uvicorn", "altwallet_agent.api:app", "--host", "0.0.0.0", "--port", "8080"]
