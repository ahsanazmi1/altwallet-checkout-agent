# Multi-stage build for AltWallet Checkout Agent v0.2.0
FROM python:3.11-slim as builder

# Set build arguments
ARG VERSION=0.2.0
ARG GIT_SHA
ARG BUILD_DATE

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY pyproject.toml .
COPY VERSION .

# Install the package
RUN pip install -e .

# Runtime stage
FROM python:3.11-slim as runtime

# Set build arguments for labels
ARG VERSION=0.2.0
ARG GIT_SHA
ARG BUILD_DATE

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy configuration files
COPY config/ ./config/
COPY openapi/ ./openapi/

# Copy source code for runtime
COPY src/ ./src/

# Set ownership
RUN chown -R app:app /app

# Switch to non-root user
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Set labels
LABEL org.opencontainers.image.title="AltWallet Checkout Agent"
LABEL org.opencontainers.image.description="Intelligent checkout processing and card recommendations engine"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.revision="${GIT_SHA}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.source="https://github.com/altwallet/checkout-agent"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.vendor="AltWallet"

# Default command
CMD ["python", "-m", "altwallet_agent.api"]
